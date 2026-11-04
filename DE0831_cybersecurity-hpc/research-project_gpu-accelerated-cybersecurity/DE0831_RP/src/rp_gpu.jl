# rp_gpu.jl - the GPU side of the research project.
#
# G2, the method: tokens are found with the lecture-7 pattern (flag per byte,
# inclusive scan, scatter = stream compaction); one thread per token hashes
# the token's bytes (FNV-1a, the function of rp_cpu.jl) and probes the
# open-addressing indicator table (global memory, or a shared-memory copy of
# the keys while it fits).  The cost is one pass over the corpus whatever the
# list size; the list size enters only through the table's footprint.
#
# G1, the per-indicator baseline: the Project 2 kernel `match_tiled_tri!`
# (shared-memory tile, three-byte prefix filter, one 32-bit mask bit per
# pattern), launched once per group of 32 indicators: its cost grows with the
# number of groups.
#
# Memory layout: the corpus is one flat UInt8 vector; thread i handles byte i
# (coalesced); tokens and hits are compacted with scan + scatter.

using CUDA

# ---------------------------------------------------------------------------
# Scan and compaction (Project 2 code)
# ---------------------------------------------------------------------------

function newline_flags!(flags, corpus)
    i      = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    stride = gridDim().x * blockDim().x
    n      = length(corpus)
    while i <= n
        @inbounds flags[i] = corpus[i] == UInt8('\n') ? UInt32(1) : UInt32(0)
        i += stride
    end
    return nothing
end

"flags[i] = 1 where a token starts: a word byte not preceded by one."
function word_flags!(flags, corpus, is_word)
    i      = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    stride = gridDim().x * blockDim().x
    n      = length(corpus)
    while i <= n
        @inbounds t = is_word[corpus[i] + 1]
        @inbounds prev = i > 1 ? is_word[corpus[i - 1] + 1] : 0x00
        @inbounds flags[i] = (t == 0x01 && prev == 0x00) ? UInt32(1) : UInt32(0)
        i += stride
    end
    return nothing
end

"Stream compaction: a flagged element i is written to its scanned slot pos[i]."
function scatter_positions!(out, flags, pos)
    i      = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    stride = gridDim().x * blockDim().x
    n      = length(flags)
    while i <= n
        @inbounds if flags[i] != 0
            out[pos[i]] = Int32(i)
        end
        i += stride
    end
    return nothing
end

const SM_COUNT = Ref(0)
function sm_count()
    SM_COUNT[] == 0 && (SM_COUNT[] = something(device_attr(:MULTIPROCESSOR_COUNT), 32))
    return SM_COUNT[]
end
"Blocks launched for a grid-stride kernel over n elements (capped at 32 per SM; at least one)."
grid_for(n; threads = 256) = max(1, min(cld(n, threads), 32 * sm_count()))

"Positions of the elements with flags[i] != 0, packed (scan + scatter), and their count."
function compact_positions(flags::CuVector{UInt32})
    isempty(flags) && return CuVector{Int32}(undef, 0), 0
    pos   = accumulate(+, flags)
    count = Int(CUDA.@allowscalar pos[end])
    out   = CuVector{Int32}(undef, count)
    count > 0 && @cuda threads=256 blocks=grid_for(length(flags)) scatter_positions!(out, flags, pos)
    CUDA.unsafe_free!(pos)
    return out, count
end

"Line-start table on the device (same definition as `cpu_line_starts`); `flags` is scratch of the corpus length."
function gpu_line_starts(corpus::CuVector{UInt8}, flags::CuVector{UInt32})
    n = length(corpus)
    @cuda threads=256 blocks=grid_for(n) newline_flags!(flags, corpus)
    line_end, nnl = compact_positions(flags)
    trailing = n > 0 && (CUDA.@allowscalar corpus[n]) == UInt8('\n')
    nl = trailing ? nnl : nnl + 1
    line_start = CuVector{Int32}(undef, nl + 1)
    CUDA.@allowscalar line_start[1] = Int32(1)
    if nl > 1
        line_start[2:nl] .= line_end[1:nl - 1] .+ Int32(1)
    end
    CUDA.@allowscalar line_start[nl + 1] = Int32(n + 2)
    CUDA.unsafe_free!(line_end)
    return line_start
end

"Token starts on the device via flags, scan and scatter; `flags` is scratch."
function gpu_token_starts(corpus::CuVector{UInt8}, flags::CuVector{UInt32}, is_word::CuVector{UInt8})
    @cuda threads=256 blocks=grid_for(length(corpus)) word_flags!(flags, corpus, is_word)
    starts, _ = compact_positions(flags)
    return starts
end

"Largest k with line_start[k] <= g (binary search)."
@inline function line_of_device(line_start, g)
    lo = 1; hi = length(line_start)
    while hi - lo > 1
        mid = (lo + hi) >> 1
        @inbounds if line_start[mid] <= g
            lo = mid
        else
            hi = mid
        end
    end
    return lo
end

free_all!(xs...) = (foreach(x -> x isa CuArray && CUDA.unsafe_free!(x), xs); nothing)

# ---------------------------------------------------------------------------
# G2: the token hash-set matcher
# ---------------------------------------------------------------------------

"Device copy of an IndicatorTable plus the word table."
struct DeviceTable
    keys::CuVector{UInt32}
    ind::CuVector{Int32}
    off::CuVector{Int32}
    len::CuVector{Int32}
    buf::CuVector{UInt8}
    mask::UInt32
    capacity::Int
    n::Int
    is_word::CuVector{UInt8}
end
DeviceTable(t::IndicatorTable) = DeviceTable(CuVector(t.keys), CuVector(t.ind), CuVector(t.off), CuVector(t.len),
                                             CuVector(t.buf), t.mask, t.capacity, t.n, CuVector(IS_WORD))

const HASH_THREADS = 256
const SHARED_CAP   = 4096     # table capacity up to which the keys are copied into shared memory (16 KB)

# One thread per token: walk the token (at most MAXIND bytes) computing the
# FNV-1a hash as the bytes are read, then probe the table; on a hash match the
# bytes are compared against the packed buffer.  hit[k] = indicator index or 0.
# A token longer than MAXIND bytes cannot be an indicator and is not looked up.
@inline function hash_probe(corpus, i0, L, h, keys, ind, off, len, buf, mask)
    slot = h & mask
    result = Int32(0)
    @inbounds while true
        k = keys[slot + 1]
        k == 0x00000000 && break
        if k == h && len[slot + 1] == L
            o = off[slot + 1]; ok = true; j = 0
            while ok && j < L
                ok = buf[o + j + 1] == corpus[i0 + j]
                j += 1
            end
            if ok
                result = ind[slot + 1]
                break
            end
        end
        slot = (slot + 0x00000001) & mask
    end
    return result
end

@inline function token_hash(corpus, i0, is_word)
    n = length(corpus)
    h = FNV_OFFSET; L = 0
    @inbounds while i0 + L <= n && L < MAXIND && is_word[corpus[i0 + L] + 1] == 0x01
        h = fnv1a_step(h, corpus[i0 + L])
        L += 1
    end
    toolong = i0 + L <= n && (@inbounds is_word[corpus[i0 + L] + 1]) == 0x01    # the token continues past MAXIND
    return nonzero(h), L, toolong
end

function hash_match!(hit, corpus, token_start, is_word, keys, ind, off, len, buf, mask)
    k = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    k > length(token_start) && return nothing
    @inbounds i0 = token_start[k]
    h, L, toolong = token_hash(corpus, i0, is_word)
    @inbounds hit[k] = toolong ? Int32(0) : hash_probe(corpus, i0, L, h, keys, ind, off, len, buf, mask)
    return nothing
end

# Variant with the keys in shared memory (capacity <= SHARED_CAP): the probe
# loop reads shared memory, global memory is touched only on a key match.
function hash_match_shared!(hit, corpus, token_start, is_word, keys, ind, off, len, buf, mask)
    skeys = CuStaticSharedArray(UInt32, SHARED_CAP)
    tid = threadIdx().x
    cap = Int(mask) + 1
    s = tid
    while s <= cap
        @inbounds skeys[s] = keys[s]
        s += blockDim().x
    end
    sync_threads()
    k = (blockIdx().x - 1) * blockDim().x + tid
    k > length(token_start) && return nothing
    @inbounds i0 = token_start[k]
    h, L, toolong = token_hash(corpus, i0, is_word)
    @inbounds hit[k] = toolong ? Int32(0) : hash_probe(corpus, i0, L, h, skeys, ind, off, len, buf, mask)
    return nothing
end

# Measurement-only kernel: probes per lookup and key-equal compares, reduced
# per block in shared memory (privatisation) and added to two global counters.
function probe_counts!(counters, corpus, token_start, is_word, keys, len, mask)
    local_counts = CuStaticSharedArray(UInt32, 2)
    tid = threadIdx().x
    tid <= 2 && (@inbounds local_counts[tid] = 0x00000000)
    sync_threads()
    k = (blockIdx().x - 1) * blockDim().x + tid
    probes = 0x00000000; equal = 0x00000000
    if k <= length(token_start)
        @inbounds i0 = token_start[k]
        h, L, toolong = token_hash(corpus, i0, is_word)
        if !toolong
            slot = h & mask
            @inbounds while true
                probes += 0x00000001
                kk = keys[slot + 1]
                kk == 0x00000000 && break
                kk == h && (equal += 0x00000001)
                slot = (slot + 0x00000001) & mask
            end
        end
    end
    CUDA.@atomic local_counts[1] += probes
    CUDA.@atomic local_counts[2] += equal
    sync_threads()
    if tid <= 2
        @inbounds CUDA.@atomic counters[tid] += UInt64(local_counts[tid])
    end
    return nothing
end

"Line numbers of the hit tokens (binary search over the line table) and their indicator indices."
function hit_pairs!(lines, inds, hit_tokens, hit, token_start, line_start)
    k = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    k > length(hit_tokens) && return nothing
    @inbounds t = hit_tokens[k]
    @inbounds lines[k] = Int32(line_of_device(line_start, token_start[t]))
    @inbounds inds[k]  = hit[t]
    return nothing
end

"Launch the hash-match kernel over all tokens (global table, or shared keys when they fit)."
function launch_hash_match!(hit, corpus, token_start, dt::DeviceTable; variant::Symbol = :global)
    nt = length(token_start)
    nt == 0 && return nothing
    if variant === :shared
        dt.capacity <= SHARED_CAP || error("table capacity $(dt.capacity) exceeds the shared-memory variant's $SHARED_CAP")
        @cuda threads=HASH_THREADS blocks=cld(nt, HASH_THREADS) hash_match_shared!(hit, corpus, token_start, dt.is_word, dt.keys, dt.ind, dt.off, dt.len, dt.buf, dt.mask)
    elseif variant === :global
        @cuda threads=HASH_THREADS blocks=cld(nt, HASH_THREADS) hash_match!(hit, corpus, token_start, dt.is_word, dt.keys, dt.ind, dt.off, dt.len, dt.buf, dt.mask)
    else
        error("unknown hash-match variant $variant")
    end
    return nothing
end

"Hits (token index → indicator index, 0 = none) compacted to (line, indicator) pairs on the device."
function gpu_extract_hits(hit::CuVector{Int32}, token_start::CuVector{Int32}, line_start::CuVector{Int32})
    hflags = map(h -> h != Int32(0) ? UInt32(1) : UInt32(0), hit)
    hit_tokens, nh = compact_positions(hflags)
    CUDA.unsafe_free!(hflags)
    lines = CuVector{Int32}(undef, nh); inds = CuVector{Int32}(undef, nh)
    nh > 0 && @cuda threads=256 blocks=cld(nh, 256) hit_pairs!(lines, inds, hit_tokens, hit, token_start, line_start)
    CUDA.unsafe_free!(hit_tokens)
    return lines, inds
end

"""
The whole G2 pipeline on a device corpus: line table, token starts, hash
match, extraction.  Returns device results (freed by the caller).
"""
function gpu_hash_pipeline(corpus::CuVector{UInt8}, dt::DeviceTable; variant::Symbol = :global)
    n = length(corpus)
    flags = CuVector{UInt32}(undef, n)
    line_start  = gpu_line_starts(corpus, flags)
    token_start = gpu_token_starts(corpus, flags, dt.is_word)
    CUDA.unsafe_free!(flags)
    hit = CuVector{Int32}(undef, length(token_start))
    launch_hash_match!(hit, corpus, token_start, dt; variant)
    lines, inds = gpu_extract_hits(hit, token_start, line_start)
    return (; line_start, token_start, hit, lines, inds)
end

"Sorted (line, indicator index) pairs of a pipeline result, on the host."
function host_pairs(r)
    l = Array(r.lines); p = Array(r.inds)
    return sort!(collect(zip(l, p)))
end

free_results!(r::NamedTuple) = free_all!(values(r)...)

# ---------------------------------------------------------------------------
# G1: the per-indicator baseline (Project 2 kernel, one launch per 32 patterns)
# ---------------------------------------------------------------------------

const MAXPAT  = 32
const MAXPLEN = 32
const TRI_SLOTS = 4096
@inline tri_hash(b0::UInt8, b1::UInt8, b2::UInt8) =
    ((UInt32(b0) << 7) ⊻ (UInt32(b1) << 3) ⊻ UInt32(b2)) & UInt32(TRI_SLOTS - 1)

"Pattern table of one group of at most 32 indicators (Project 2 layout, with the three-byte filter)."
struct PatternTable
    pat::Matrix{UInt8}
    plen::Vector{Int32}
    npat::Int
    first_mask::Vector{UInt32}
    tri::Vector{UInt8}
end
function PatternTable(indicators::AbstractVector{<:AbstractString})
    n = length(indicators)
    n <= MAXPAT || error("at most $MAXPAT patterns per group, got $n")
    pat = zeros(UInt8, MAXPLEN, MAXPAT); plen = zeros(Int32, MAXPAT); fm = zeros(UInt32, 256); tri = zeros(UInt8, TRI_SLOTS)
    for (p, s) in enumerate(indicators)
        b = Vector{UInt8}(codeunits(s))
        1 <= length(b) <= MAXPLEN || error("pattern $p has length $(length(b)); 1..$MAXPLEN supported")
        pat[1:length(b), p] = b; plen[p] = length(b)
        fm[b[1] + 1] |= UInt32(1) << (p - 1)
        length(b) >= 3 ? (tri[tri_hash(b[1], b[2], b[3]) + 1] = 0x01) : fill!(tri, 0x01)
    end
    return PatternTable(pat, plen, n, fm, tri)
end

struct DevicePatterns
    pat::CuVector{UInt8}
    plen::CuVector{Int32}
    first_mask::CuVector{UInt32}
    tri::CuVector{UInt8}
    is_word::CuVector{UInt8}
    npat::Int
end
DevicePatterns(pt::PatternTable) = DevicePatterns(CuVector(vec(pt.pat)), CuVector(pt.plen), CuVector(pt.first_mask),
                                                  CuVector(pt.tri), CuVector(IS_WORD), pt.npat)

const MATCH_THREADS  = 256
const MATCH_TILE_TRI = 4096

# The Project 2 kernel: one block per 4 KB tile (+ halo) in shared memory,
# the group's tables in shared memory, three-byte prefix filter, first-byte
# mask, byte compare, word boundaries, atomic OR of the pattern bit into the
# line's mask.
function match_tiled_tri!(line_mask, corpus, pat, plen, first_mask, is_word, tri, line_start)
    tile  = CuStaticSharedArray(UInt8, MATCH_TILE_TRI + MAXPLEN)
    spat  = CuStaticSharedArray(UInt8, MAXPLEN * MAXPAT)
    splen = CuStaticSharedArray(Int32, MAXPAT)
    sfm   = CuStaticSharedArray(UInt32, 256)
    sword = CuStaticSharedArray(UInt8, 256)
    stri  = CuStaticSharedArray(UInt8, TRI_SLOTS)
    tid  = threadIdx().x
    base = (blockIdx().x - 1) * MATCH_TILE_TRI
    n    = length(corpus)
    k = tid
    while k <= MAXPLEN * MAXPAT
        @inbounds spat[k] = pat[k]
        k += MATCH_THREADS
    end
    if tid <= MAXPAT
        @inbounds splen[tid] = plen[tid]
    end
    @inbounds sfm[tid] = first_mask[tid]
    @inbounds sword[tid] = is_word[tid]
    k = tid
    while k <= TRI_SLOTS
        @inbounds stri[k] = tri[k]
        k += MATCH_THREADS
    end
    k = tid
    while k <= MATCH_TILE_TRI + MAXPLEN
        g = base + k
        @inbounds tile[k] = g <= n ? corpus[g] : 0x00
        k += MATCH_THREADS
    end
    sync_threads()
    k = tid
    while k <= MATCH_TILE_TRI
        g = base + k
        if g <= n
            @inbounds b0 = tile[k]
            @inbounds h  = tri_hash(b0, tile[k + 1], tile[k + 2])
            @inbounds passes = stri[h + 1] != 0x00
            if passes
                @inbounds m = sfm[b0 + 1]
                while m != 0x00000000
                    p = trailing_zeros(m) + 1
                    m &= m - 0x00000001
                    @inbounds L = splen[p]
                    if g + L - 1 <= n
                        ok = true; j = 1
                        while ok && j <= L
                            @inbounds ok = tile[k + j - 1] == spat[(p - 1) * MAXPLEN + j]
                            j += 1
                        end
                        if ok
                            @inbounds before = k > 1 ? tile[k - 1] : (g > 1 ? corpus[g - 1] : 0x00)
                            @inbounds after  = g + L <= n ? tile[k + L] : 0x00
                            @inbounds if sword[before + 1] == 0x00 && sword[after + 1] == 0x00
                                ln = line_of_device(line_start, g)
                                CUDA.@atomic line_mask[ln] |= UInt32(1) << (p - 1)
                            end
                        end
                    end
                end
            end
        end
        k += MATCH_THREADS
    end
    return nothing
end

"Groups of at most 32 indicators, as device pattern tables (built once, outside the timed region)."
function device_groups(list::Vector{String})
    return [DevicePatterns(PatternTable(list[a:min(a + MAXPAT - 1, end)])) for a in 1:MAXPAT:length(list)]
end

"One launch per group over the whole corpus; masks[g] receives the group's per-line bits (zeroed by the caller)."
function launch_groups!(masks::Vector{<:CuVector{UInt32}}, corpus, groups::Vector{DevicePatterns}, line_start)
    n = length(corpus)
    for (g, dp) in enumerate(groups)
        @cuda threads=MATCH_THREADS blocks=max(1, cld(n, MATCH_TILE_TRI)) match_tiled_tri!(masks[g], corpus, dp.pat, dp.plen, dp.first_mask, dp.is_word, dp.tri, line_start)
    end
    return nothing
end

"(line, indicator index) pairs from the group masks, on the host."
function group_pairs(masks::Vector{<:CuVector{UInt32}})
    hits = Tuple{Int32,Int32}[]
    for (g, m) in enumerate(masks)
        mh = Array(m)
        @inbounds for (ln, v) in enumerate(mh)
            while v != 0
                p = trailing_zeros(v) + 1
                v &= v - 1
                push!(hits, (Int32(ln), Int32((g - 1) * MAXPAT + p)))
            end
        end
    end
    sort!(hits)
    return hits
end
