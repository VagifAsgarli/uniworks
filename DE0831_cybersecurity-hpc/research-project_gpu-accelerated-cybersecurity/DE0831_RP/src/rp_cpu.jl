# rp_cpu.jl - the CPU side of the research project: the word alphabet, the
# FNV-1a hash and the open-addressing indicator table (shared with the GPU
# kernels), the tuned multithreaded CPU matcher (baseline C1), the library
# baseline (`occursin` per indicator, C2), and the line helpers.
#
# Matching semantics (the Project 2 rule): an indicator matches a line when it
# occurs as a whole token, i.e. the bytes before and after it are not word
# characters [A-Za-z0-9.-].  Every method here and on the GPU applies it.

# ---------------------------------------------------------------------------
# Word alphabet, hash, indicator table
# ---------------------------------------------------------------------------

"Word characters: the token alphabet for indicator matching."
const IS_WORD = let t = zeros(UInt8, 256)
    for c in vcat('0':'9', 'A':'Z', 'a':'z', ['.', '-'])
        t[UInt8(c) + 1] = 0x01
    end
    t
end

const MAXIND = 64           # bytes of a token that are hashed; longer tokens cannot be indicators

const FNV_OFFSET = 0x811c9dc5
const FNV_PRIME  = 0x01000193
"One FNV-1a step (32-bit): the same function on the CPU and in the kernels."
@inline fnv1a_step(h::UInt32, b::UInt8) = (h ⊻ UInt32(b)) * FNV_PRIME
"FNV-1a of a byte string, never 0 (0 marks an empty table slot)."
function fnv1a(bytes)
    h = FNV_OFFSET
    for b in bytes
        h = fnv1a_step(h, UInt8(b))
    end
    return h == 0x00000000 ? 0x00000001 : h
end
@inline nonzero(h::UInt32) = h == 0x00000000 ? 0x00000001 : h

"""
Open-addressing hash table of the indicators (linear probing, load <= 0.5):
slot s holds `keys[s]` (the FNV-1a hash, 0 = empty), `ind[s]` (the indicator's
1-based index in the list), `off[s]` and `len[s]` (its bytes in the packed
buffer `buf`).  Capacity is a power of two, `mask = capacity - 1`.
"""
struct IndicatorTable
    keys::Vector{UInt32}
    ind::Vector{Int32}
    off::Vector{Int32}
    len::Vector{Int32}
    buf::Vector{UInt8}
    mask::UInt32
    capacity::Int
    n::Int
end

function IndicatorTable(list::Vector{String})
    n = length(list)
    cap = nextpow(2, max(4, 2n))
    keys = zeros(UInt32, cap); ind = zeros(Int32, cap); off = zeros(Int32, cap); len = zeros(Int32, cap)
    buf = UInt8[]
    seen = Set{String}()
    for (p, s) in enumerate(list)
        b = Vector{UInt8}(codeunits(s))
        1 <= length(b) <= MAXIND || error("indicator $p has $(length(b)) bytes; 1..$MAXIND supported")
        s in seen && error("duplicate indicator: $s")
        push!(seen, s)
        all(c -> IS_WORD[c + 1] == 0x01, b) || error("indicator $p ($s) contains a non-word character")
        h = fnv1a(b)
        slot = h & UInt32(cap - 1)
        while keys[slot + 1] != 0x00000000
            slot = (slot + 0x00000001) & UInt32(cap - 1)
        end
        keys[slot + 1] = h; ind[slot + 1] = Int32(p); off[slot + 1] = Int32(length(buf)); len[slot + 1] = Int32(length(b))
        append!(buf, b)
    end
    return IndicatorTable(keys, ind, off, len, buf, UInt32(cap - 1), cap, n)
end

"Bytes of the table arrays (keys + ind + off + len) and of the packed pattern buffer."
table_bytes(t::IndicatorTable) = (t.capacity * 16, length(t.buf))

"""
Look up the token `corpus[i0:i0+L-1]` with hash `h`: the indicator's index, or
0.  Exactly the probe loop of the kernel.
"""
@inline function lookup(t::IndicatorTable, corpus, i0, L, h::UInt32)
    slot = h & t.mask
    @inbounds while true
        k = t.keys[slot + 1]
        k == 0x00000000 && return 0
        if k == h && t.len[slot + 1] == L
            o = t.off[slot + 1]; ok = true; j = 0
            while ok && j < L
                ok = t.buf[o + j + 1] == corpus[i0 + j]
                j += 1
            end
            ok && return Int(t.ind[slot + 1])
        end
        slot = (slot + 0x00000001) & t.mask
    end
end

# ---------------------------------------------------------------------------
# Lines
# ---------------------------------------------------------------------------

"""
Offsets of the first byte of every line plus a sentinel n + 2 (a final line
without a newline is included).  Same definition as the GPU version.
"""
function cpu_line_starts(corpus::AbstractVector{UInt8})
    n = length(corpus)
    starts = Int32[1]
    @inbounds for i in 1:n
        corpus[i] == UInt8('\n') && push!(starts, Int32(i + 1))
    end
    if n > 0 && corpus[n] == UInt8('\n')
        pop!(starts)
    end
    push!(starts, Int32(n + 2))
    return starts
end
nlines_of(line_start) = length(line_start) - 1
line_of(line_start, i) = searchsortedlast(line_start, Int32(i))
corpus_lines(corpus::AbstractVector{UInt8}, line_start) =
    [String(corpus[line_start[k]:line_start[k + 1] - 2]) for k in 1:nlines_of(line_start)]

# ---------------------------------------------------------------------------
# C1: the tuned CPU matcher (one pass, hash per token, Julia threads)
# ---------------------------------------------------------------------------

"""
Chunk boundaries for T chunks: each chunk starts at a line start, so no token
or line spans two chunks.  Returns T + 1 offsets; chunk t is bounds[t]:bounds[t+1]-1.
"""
function chunk_bounds(corpus::AbstractVector{UInt8}, T::Integer)
    n = length(corpus)
    bounds = Int[1]
    @inbounds for t in 1:T-1
        b = max(1, (n * t) ÷ T)
        while b <= n && corpus[b] != UInt8('\n')
            b += 1
        end
        push!(bounds, min(b + 1, n + 1))
    end
    push!(bounds, n + 1)
    return bounds
end

"""
Scan bytes a..b (a is a line start, line0 its line number): tokens are found
on the fly, hashed as they are read (FNV-1a, at most MAXIND bytes), and looked
up; hits are pushed as (line, indicator index).  No allocation per token.
"""
function scan_chunk!(hits::Vector{Tuple{Int32,Int32}}, corpus::AbstractVector{UInt8}, t::IndicatorTable, a::Int, b::Int, line0::Int)
    line = line0; h = FNV_OFFSET; L = 0; i0 = 0
    @inbounds for i in a:b
        c = corpus[i]
        if IS_WORD[c + 1] == 0x01
            L == 0 && (i0 = i; h = FNV_OFFSET)
            L += 1
            L <= MAXIND && (h = fnv1a_step(h, c))
        else
            if L > 0
                if L <= MAXIND
                    ind = lookup(t, corpus, i0, L, nonzero(h))
                    ind != 0 && push!(hits, (Int32(line), Int32(ind)))
                end
                L = 0
            end
            c == UInt8('\n') && (line += 1)
        end
    end
    if L > 0 && L <= MAXIND                       # a token that ends with the corpus
        ind = lookup(t, corpus, i0, L, nonzero(h))
        ind != 0 && push!(hits, (Int32(line), Int32(ind)))
    end
    return hits
end

"""
The tuned CPU matcher: the corpus is cut into `T` newline-aligned chunks, the
lines per chunk are counted in parallel (so each chunk knows its first line
number), then every chunk is scanned by one task (`Threads.@threads`; T tasks
run in parallel when Julia has at least T threads).  Returns the sorted
(line, indicator index) pairs.
"""
function cpu_hash_match(corpus::AbstractVector{UInt8}, t::IndicatorTable; T::Integer = Threads.nthreads())
    bounds = chunk_bounds(corpus, T)
    nl = zeros(Int, T)
    Threads.@threads for c in 1:T
        a, b = bounds[c], bounds[c + 1] - 1
        nl[c] = b >= a ? count(==(UInt8('\n')), view(corpus, a:b)) : 0
    end
    line0 = cumsum(vcat(1, nl[1:end-1]))
    parts = [Tuple{Int32,Int32}[] for _ in 1:T]
    Threads.@threads for c in 1:T
        a, b = bounds[c], bounds[c + 1] - 1
        b >= a && scan_chunk!(parts[c], corpus, t, a, b, line0[c])
    end
    hits = reduce(vcat, parts)
    sort!(hits)
    return hits
end

# ---------------------------------------------------------------------------
# C2: the library baseline (occursin per indicator over the lines)
# ---------------------------------------------------------------------------

"Library route: `occursin` of every indicator over every line (substring semantics)."
function cpu_match_occursin(lines::Vector{String}, list::Vector{String})
    hits = Tuple{Int32,Int32}[]
    for (p, ind) in enumerate(list)
        @inbounds for (k, l) in enumerate(lines)
            occursin(ind, l) && push!(hits, (Int32(k), Int32(p)))
        end
    end
    sort!(hits)
    return hits
end

"(line, indicator index) pairs as a set of (line, indicator string), for comparison with the truth."
pairs_to_set(hits, list::Vector{String}) = Set((Int(l), list[p]) for (l, p) in hits)
