# p2_cpu.jl - the single-threaded CPU baseline for track E and the shared
# definitions (character classes, pattern table) that the GPU kernels use too.
#
# The baseline performs the same computation as the GPU pipeline with the
# same algorithm (first-byte filter, byte comparison, token boundaries, 64-bin
# entropy), so that the two can be compared per step.  A second, library-style
# baseline (`occursin` per indicator over the lines, the basic route of the
# brief) is kept for the comparison table.

# ---------------------------------------------------------------------------
# Character classes and the pattern table
# ---------------------------------------------------------------------------

const MAXPAT  = 32          # patterns per set (indicator files have 20)
const MAXPLEN = 32          # longest pattern in bytes (longest indicator: 27)

# Word characters for the match boundary: an indicator must not be preceded or
# followed by one of these, so "192.0.2.24" never matches inside "192.0.2.248"
# and "app3.invalid" never matches inside "xapp3.invalid".
const IS_WORD = let t = zeros(UInt8, 256)
    for c in vcat('0':'9', 'A':'Z', 'a':'z', ['.', '-'])
        t[UInt8(c) + 1] = 0x01
    end
    t
end

# Token characters for entropy flagging: the base64 alphabet (the planted
# payloads are base64 blobs after "/upload?d="; '?' and '=' end a token, so the
# blob is a token of its own, exactly the string the generator measured).
const IS_TOK = let t = zeros(UInt8, 256)
    for c in vcat('A':'Z', 'a':'z', '0':'9', ['+', '/'])
        t[UInt8(c) + 1] = 0x01
    end
    t
end

# Symbol index 0..63 of a token character (base64 order), used as the entropy
# histogram bin; non-token bytes map to 0xff and never occur inside a token.
const TOK_SYMBOL = let t = fill(0xff, 256)
    for (k, c) in enumerate(vcat('A':'Z', 'a':'z', '0':'9', ['+', '/']))
        t[UInt8(c) + 1] = UInt8(k - 1)
    end
    t
end

const NSYM = 64

const TRI_SLOTS = 4096      # three-byte prefix filter: a 12-bit hash of the first three bytes

"12-bit hash of three consecutive bytes (the same function on the host and in the kernel)."
@inline tri_hash(b0::UInt8, b1::UInt8, b2::UInt8) =
    ((UInt32(b0) << 7) ⊻ (UInt32(b1) << 3) ⊻ UInt32(b2)) & UInt32(TRI_SLOTS - 1)

"""
Pattern table in the layout the kernels use: `pat[j, p]` is byte j of pattern
p (zero-padded), `plen[p]` its length, `first_mask[b+1]` has bit p-1 set if
pattern p starts with byte value b (the first-byte filter), and `tri[h+1]` is
1 if some pattern's first three bytes hash to h (the three-byte filter of the
second tiled kernel; all ones if a pattern is shorter than three bytes, which
disables that filter without changing the result).
"""
struct PatternTable
    pat::Matrix{UInt8}            # MAXPLEN × MAXPAT
    plen::Vector{Int32}           # MAXPAT
    npat::Int
    first_mask::Vector{UInt32}    # 256
    tri::Vector{UInt8}            # TRI_SLOTS
end

function PatternTable(indicators::AbstractVector{<:AbstractString})
    n = length(indicators)
    n <= MAXPAT || error("at most $MAXPAT patterns are supported, got $n")
    pat  = zeros(UInt8, MAXPLEN, MAXPAT)
    plen = zeros(Int32, MAXPAT)
    fm   = zeros(UInt32, 256)
    tri  = zeros(UInt8, TRI_SLOTS)
    for (p, s) in enumerate(indicators)
        b = Vector{UInt8}(codeunits(s))
        1 <= length(b) <= MAXPLEN || error("pattern $p has length $(length(b)); 1..$MAXPLEN supported")
        pat[1:length(b), p] = b
        plen[p] = length(b)
        fm[b[1] + 1] |= UInt32(1) << (p - 1)
        if length(b) >= 3
            tri[tri_hash(b[1], b[2], b[3]) + 1] = 0x01
        else
            fill!(tri, 0x01)
        end
    end
    return PatternTable(pat, plen, n, fm, tri)
end

"""
Filter statistics for the analysis, computed on the CPU from the same tables
the kernels use: the fraction of byte positions that pass the first-byte
filter and the three-byte filter, and the fraction of warps (32 consecutive
positions, exactly the lanes of one warp in the tiled kernels) in which no
lane has a candidate, so the whole warp skips the candidate loop.
"""
function cpu_filter_stats(corpus::AbstractVector{UInt8}, pt::PatternTable)
    n = length(corpus); c1 = 0; c3 = 0; w1 = 0; w3 = 0; nw = 0
    any1 = false; any3 = false
    @inbounds for g in 1:n
        b0 = corpus[g]
        a1 = pt.first_mask[b0 + 1] != 0
        b1 = g + 1 <= n ? corpus[g + 1] : 0x00
        b2 = g + 2 <= n ? corpus[g + 2] : 0x00
        a3 = a1 && pt.tri[tri_hash(b0, b1, b2) + 1] != 0x00
        c1 += a1; c3 += a3; any1 |= a1; any3 |= a3
        if g % 32 == 0
            nw += 1; w1 += !any1; w3 += !any3; any1 = false; any3 = false
        end
    end
    nw = max(nw, 1)
    return (cand1 = c1 / n, cand3 = c3 / n, skip1 = w1 / nw, skip3 = w3 / nw)
end

# ---------------------------------------------------------------------------
# Line table
# ---------------------------------------------------------------------------

"""
Offsets of the first byte of every line, plus a sentinel one past the end of
the corpus (`line_start[k]:line_start[k+1]-2` is line k without its newline;
a final line without a trailing newline is included).  Same definition as the
GPU version.
"""
function cpu_line_starts(corpus::AbstractVector{UInt8})
    n = length(corpus)
    starts = Int32[1]
    @inbounds for i in 1:n
        corpus[i] == UInt8('\n') && push!(starts, Int32(i + 1))
    end
    # a trailing newline leaves an empty "line" after it: drop that start
    if n > 0 && corpus[n] == UInt8('\n')
        pop!(starts)
    end
    push!(starts, Int32(n + 2))                 # sentinel: as if a newline followed byte n+1
    return starts
end

"Number of lines described by a line-start table."
nlines_of(line_start) = length(line_start) - 1

"Line number containing byte position i (binary search, same as the kernel)."
line_of(line_start, i) = searchsortedlast(line_start, Int32(i))

# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

"""
Does pattern p of `pt` occur at position i of `corpus` as a whole word?  The
exact test the match kernel performs (byte compare, then the boundary bytes).
"""
@inline function match_at(corpus, i, pt::PatternTable, p)
    n = length(corpus)
    L = Int(pt.plen[p])
    i + L - 1 > n && return false
    @inbounds for j in 1:L
        corpus[i + j - 1] == pt.pat[j, p] || return false
    end
    @inbounds before = i > 1 ? IS_WORD[corpus[i - 1] + 1] : 0x00
    @inbounds after  = i + L <= n ? IS_WORD[corpus[i + L] + 1] : 0x00
    return before == 0x00 && after == 0x00
end

"""
CPU baseline of the match kernel: for every byte position, the first-byte
filter, then the candidate patterns; returns the per-line bit mask exactly as
the GPU produces it (bit p-1 set when pattern p occurs in the line).
"""
function cpu_match(corpus::AbstractVector{UInt8}, pt::PatternTable, line_start)
    mask = zeros(UInt32, nlines_of(line_start))
    n = length(corpus)
    @inbounds for i in 1:n
        m = pt.first_mask[corpus[i] + 1]
        m == 0 && continue
        while m != 0
            p = trailing_zeros(m) + 1
            m &= m - 1
            if match_at(corpus, i, pt, p)
                ln = line_of(line_start, i)
                mask[ln] |= UInt32(1) << (p - 1)
            end
        end
    end
    return mask
end

"""
Library-style baseline (the brief's basic route on the CPU): split the corpus
into lines, then `occursin` for every indicator over every line.  Substring
semantics (no word boundary), which is enough for the generated data.
"""
function cpu_match_occursin(lines::Vector{String}, indicators::Vector{String})
    mask = zeros(UInt32, length(lines))
    for (p, ind) in enumerate(indicators)
        bit = UInt32(1) << (p - 1)
        @inbounds for (k, l) in enumerate(lines)
            occursin(ind, l) && (mask[k] |= bit)
        end
    end
    return mask
end

"Split the corpus into lines (for the library-style baseline and for display)."
function corpus_lines(corpus::AbstractVector{UInt8}, line_start)
    return [String(corpus[line_start[k]:line_start[k + 1] - 2]) for k in 1:nlines_of(line_start)]
end

"The set of (line, indicator) pairs encoded by a line mask."
function match_set(mask::AbstractVector{UInt32}, indicators)
    s = Set{Tuple{Int,String}}()
    @inbounds for (k, m) in enumerate(mask)
        while m != 0
            p = trailing_zeros(m) + 1
            m &= m - 1
            push!(s, (k, indicators[p]))
        end
    end
    return s
end

# ---------------------------------------------------------------------------
# Tokens and entropy
# ---------------------------------------------------------------------------

"Start positions of all tokens: a token byte not preceded by a token byte."
function cpu_token_starts(corpus::AbstractVector{UInt8})
    starts = Int32[]
    prev = 0x00
    @inbounds for i in eachindex(corpus)
        t = IS_TOK[corpus[i] + 1]
        (t == 0x01 && prev == 0x00) && push!(starts, Int32(i))
        prev = t
    end
    return starts
end

const MAXTOK = 255          # tokens are cut at this length (payloads are ≤ 120)

"Length of the token starting at position i (at most MAXTOK)."
@inline function token_length(corpus, i)
    n = length(corpus); L = 0
    @inbounds while i + L <= n && L < MAXTOK && IS_TOK[corpus[i + L] + 1] == 0x01
        L += 1
    end
    return L
end

"""
Shannon entropy in bits per character of the token at position i, over its
own 64-symbol distribution (the generator's `shannon(blob)`), computed with
Float64 on the CPU; the kernel does the same in Float32.
"""
function token_entropy(corpus, i, counts = zeros(Int32, NSYM))
    fill!(counts, Int32(0))
    L = token_length(corpus, i)
    @inbounds for j in 0:L-1
        counts[TOK_SYMBOL[corpus[i + j] + 1] + 1] += 1
    end
    h = 0.0
    @inbounds for c in counts
        c == 0 && continue
        p = c / L
        h -= p * log2(p)
    end
    return h, L
end

"Entropies (Float64) and lengths of all tokens in `starts`."
function cpu_token_entropies(corpus, starts)
    H = zeros(Float64, length(starts)); L = zeros(Int32, length(starts))
    counts = zeros(Int32, NSYM)                  # one buffer, reused for every token
    @inbounds for (k, i) in enumerate(starts)
        H[k], L[k] = token_entropy(corpus, i, counts)
    end
    return H, L
end

"The tokens with entropy ≥ threshold as a vector of (line, token, entropy)."
function flagged_tokens(corpus, starts, H, L, line_start, threshold)
    out = Tuple{Int,String,Float64}[]
    @inbounds for k in eachindex(starts)
        H[k] >= threshold || continue
        i = starts[k]
        push!(out, (line_of(line_start, i), String(corpus[i:i + L[k] - 1]), Float64(H[k])))
    end
    return out
end
