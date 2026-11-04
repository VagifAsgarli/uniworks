# p2_gpu.jl - the GPU implementation of track E (full route): the kernels
# K1-K8 of notes/design.md and the pipeline that runs them.
#
# Memory layout: the corpus is one flat UInt8 vector; thread i handles byte i,
# so a warp reads 32 consecutive bytes (coalesced).  Lines and tokens are
# found with the lecture-7 pattern: a 0/1 flag per byte, an inclusive scan
# (`accumulate(+, flags)`), and a scatter kernel that writes each flagged
# position to its scanned slot (stream compaction).  Matching is one kernel
# over all patterns at once; matched lines are compacted and gathered with
# the same scan-and-scatter pattern.

using CUDA

# ---------------------------------------------------------------------------
# Scan and compaction (lecture 7)
# ---------------------------------------------------------------------------

# K1: flags[i] = 1 where byte i is a newline.  Grid-stride loop; the read of
# corpus[i] by consecutive threads is coalesced, the write of a UInt32 flag
# per byte is coalesced too (4 B per thread, 128 B per warp).
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

# K2: stream compaction.  `pos` is the inclusive scan of `flags`, so a flagged
# element i has the 1-based output slot pos[i]; unflagged elements write
# nothing.  No two flagged elements share a slot, so there is no race.
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

"""
Grid size for a grid-stride kernel over n elements: enough blocks for the
elements, capped at 32 × the SM count (at least one block).  This is the
number of blocks launched; how many are resident at once per SM is the
occupancy question (`resident_blocks_per_sm`, `CUDA.active_blocks`).
"""
grid_for(n; threads = 256) = max(1, min(cld(n, threads), 32 * sm_count()))

"""
Positions (1-based) of the elements with flags[i] != 0, packed, via scan and
scatter.  Returns the device vector of positions and the count.
"""
function compact_positions(flags::CuVector{UInt32})
    isempty(flags) && return CuVector{Int32}(undef, 0), 0
    pos   = accumulate(+, flags)                          # inclusive scan (lecture 7)
    count = Int(CUDA.@allowscalar pos[end])
    out   = CuVector{Int32}(undef, count)
    count > 0 && @cuda threads=256 blocks=grid_for(length(flags)) scatter_positions!(out, flags, pos)
    CUDA.unsafe_free!(pos)
    return out, count
end

"""
Line-start table on the device, same definition as `cpu_line_starts`:
offsets of every line's first byte and a sentinel n + 2.  `flags` is a
caller-provided UInt32 scratch vector of the corpus length.
"""
function gpu_line_starts(corpus::CuVector{UInt8}, flags::CuVector{UInt32})
    n = length(corpus)
    @cuda threads=256 blocks=grid_for(n) newline_flags!(flags, corpus)
    line_end, nnl = compact_positions(flags)             # positions of '\n'
    trailing = n > 0 && (CUDA.@allowscalar corpus[n]) == UInt8('\n')
    nl = trailing ? nnl : nnl + 1                         # a last line without '\n' counts too
    line_start = CuVector{Int32}(undef, nl + 1)
    CUDA.@allowscalar line_start[1] = Int32(1)
    if nl > 1
        line_start[2:nl] .= line_end[1:nl - 1] .+ Int32(1)
    end
    CUDA.@allowscalar line_start[nl + 1] = Int32(n + 2)
    CUDA.unsafe_free!(line_end)
    return line_start
end

# ---------------------------------------------------------------------------
# K3: multi-pattern matching
# ---------------------------------------------------------------------------

const MATCH_THREADS = 256
const MATCH_TILE    = 1024        # bytes per block: 4 positions per thread

# Largest k with line_start[k] <= g (line_start[1] = 1 and the sentinel is
# larger than any byte position, so the search always terminates inside).
@inline function line_of_device(line_start, g)
    lo = 1
    hi = length(line_start)
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

# One block matches one tile of MATCH_TILE corpus bytes.  The block first
# copies the pattern table, the first-byte mask and the word-character table
# into shared memory (every thread later reads the same addresses: shared-
# memory broadcast), then loads the tile plus a halo of MAXPLEN bytes with
# coalesced global loads.  Each thread then handles 4 positions: the
# first-byte mask says which patterns can start at this byte (none for most
# bytes), the candidate patterns are compared against shared memory, and a
# whole-word match sets the pattern's bit in the line's mask with an atomic
# OR.  Hits are rare (0.09 % of lines), so the binary search for the line and
# the atomic cost nothing measurable; the halo makes patterns that cross a
# tile edge match in the tile where they start.
function match_tiled!(line_mask, corpus, pat, plen, first_mask, is_word, line_start)
    tile  = CuStaticSharedArray(UInt8, MATCH_TILE + MAXPLEN)
    spat  = CuStaticSharedArray(UInt8, MAXPLEN * MAXPAT)
    splen = CuStaticSharedArray(Int32, MAXPAT)
    sfm   = CuStaticSharedArray(UInt32, 256)
    sword = CuStaticSharedArray(UInt8, 256)
    tid  = threadIdx().x
    base = (blockIdx().x - 1) * MATCH_TILE               # bytes before this tile
    n    = length(corpus)

    k = tid                                               # 1. tables into shared memory
    while k <= MAXPLEN * MAXPAT
        @inbounds spat[k] = pat[k]
        k += MATCH_THREADS
    end
    if tid <= MAXPAT
        @inbounds splen[tid] = plen[tid]
    end
    @inbounds sfm[tid] = first_mask[tid]                  # 256 threads, 256 entries
    @inbounds sword[tid] = is_word[tid]
    k = tid                                               # 2. tile + halo (coalesced)
    while k <= MATCH_TILE + MAXPLEN
        g = base + k
        @inbounds tile[k] = g <= n ? corpus[g] : 0x00
        k += MATCH_THREADS
    end
    sync_threads()

    k = tid                                               # 3. match at 4 positions per thread
    while k <= MATCH_TILE
        g = base + k
        if g <= n
            @inbounds m = sfm[tile[k] + 1]
            while m != 0x00000000
                p = trailing_zeros(m) + 1
                m &= m - 0x00000001
                @inbounds L = splen[p]
                if g + L - 1 <= n
                    ok = true
                    j = 1
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
        k += MATCH_THREADS
    end
    return nothing
end

# Variant for the analysis: the same matching with every byte read directly
# from global memory (no shared-memory tile).  One position per thread,
# grid-stride.
function match_global!(line_mask, corpus, pat, plen, first_mask, is_word, line_start)
    spat  = CuStaticSharedArray(UInt8, MAXPLEN * MAXPAT)
    splen = CuStaticSharedArray(Int32, MAXPAT)
    sfm   = CuStaticSharedArray(UInt32, 256)
    sword = CuStaticSharedArray(UInt8, 256)
    tid = threadIdx().x
    k = tid
    while k <= MAXPLEN * MAXPAT
        @inbounds spat[k] = pat[k]
        k += blockDim().x
    end
    if tid <= MAXPAT
        @inbounds splen[tid] = plen[tid]
    end
    k = tid
    while k <= 256
        @inbounds sfm[k] = first_mask[k]
        @inbounds sword[k] = is_word[k]
        k += blockDim().x
    end
    sync_threads()

    n      = length(corpus)
    g      = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    stride = gridDim().x * blockDim().x
    while g <= n
        @inbounds m = sfm[corpus[g] + 1]
        while m != 0x00000000
            p = trailing_zeros(m) + 1
            m &= m - 0x00000001
            @inbounds L = splen[p]
            if g + L - 1 <= n
                ok = true
                j = 1
                while ok && j <= L
                    @inbounds ok = corpus[g + j - 1] == spat[(p - 1) * MAXPLEN + j]
                    j += 1
                end
                if ok
                    @inbounds before = g > 1 ? corpus[g - 1] : 0x00
                    @inbounds after  = g + L <= n ? corpus[g + L] : 0x00
                    @inbounds if sword[before + 1] == 0x00 && sword[after + 1] == 0x00
                        ln = line_of_device(line_start, g)
                        CUDA.@atomic line_mask[ln] |= UInt32(1) << (p - 1)
                    end
                end
            end
        end
        g += stride
    end
    return nothing
end

# Measurement-only kernel for the integer-operation count: how many positions
# pass the first-byte filter and how many byte comparisons the candidates
# cost.  Per-warp counts are reduced with shared-memory atomics first and
# added to the two global counters once per block (privatisation, as in the
# Project 1 histogram), so the counting itself does not distort the numbers.
function match_counts!(counters, corpus, pat, plen, first_mask)
    spat  = CuStaticSharedArray(UInt8, MAXPLEN * MAXPAT)
    splen = CuStaticSharedArray(Int32, MAXPAT)
    sfm   = CuStaticSharedArray(UInt32, 256)
    local_counts = CuStaticSharedArray(UInt32, 2)
    tid = threadIdx().x
    k = tid
    while k <= MAXPLEN * MAXPAT
        @inbounds spat[k] = pat[k]
        k += blockDim().x
    end
    if tid <= MAXPAT
        @inbounds splen[tid] = plen[tid]
    end
    k = tid
    while k <= 256
        @inbounds sfm[k] = first_mask[k]
        k += blockDim().x
    end
    if tid <= 2
        @inbounds local_counts[tid] = 0x00000000
    end
    sync_threads()

    n = length(corpus)
    g = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    stride = gridDim().x * blockDim().x
    candidates = 0x00000000
    compares   = 0x00000000
    while g <= n
        @inbounds m = sfm[corpus[g] + 1]
        m != 0x00000000 && (candidates += 0x00000001)
        while m != 0x00000000
            p = trailing_zeros(m) + 1
            m &= m - 0x00000001
            @inbounds L = splen[p]
            if g + L - 1 <= n
                ok = true
                j = 1
                while ok && j <= L
                    @inbounds ok = corpus[g + j - 1] == spat[(p - 1) * MAXPLEN + j]
                    j += 1
                    compares += 0x00000001
                end
            end
        end
        g += stride
    end
    CUDA.@atomic local_counts[1] += candidates
    CUDA.@atomic local_counts[2] += compares
    sync_threads()
    if tid == 1
        @inbounds CUDA.@atomic counters[1] += UInt64(local_counts[1])
        @inbounds CUDA.@atomic counters[2] += UInt64(local_counts[2])
    end
    return nothing
end

# ---------------------------------------------------------------------------
# K4-K5: matched lines, compacted and gathered
# ---------------------------------------------------------------------------

# K5: one block per matched line; the threads copy its bytes to the packed
# output buffer at the line's scanned offset (consecutive threads write
# consecutive bytes: coalesced on both sides).
function gather_lines!(out, corpus, line_start, matched, off, len)
    k = blockIdx().x
    @inbounds s = line_start[matched[k]]
    @inbounds L = len[k]
    @inbounds o = off[k]
    t = threadIdx().x
    while t <= L
        @inbounds out[o + t] = corpus[s + t - 1]
        t += blockDim().x
    end
    return nothing
end

"""
Line numbers of the lines with a non-zero mask (compaction) and their text
packed into one byte buffer with offsets and lengths (gather).
"""
function extract_matched_lines(corpus::CuVector{UInt8}, line_start::CuVector{Int32}, line_mask::CuVector{UInt32})
    mflags = map(m -> m != 0x00000000 ? UInt32(1) : UInt32(0), line_mask)
    matched, nm = compact_positions(mflags)               # line numbers, ascending
    CUDA.unsafe_free!(mflags)
    nm == 0 && return matched, CuVector{Int32}(undef, 0), CuVector{Int32}(undef, 0), CuVector{UInt8}(undef, 0)
    len = line_start[matched .+ 1] .- line_start[matched] .- Int32(1)     # without the newline
    off = accumulate(+, len) .- len                                        # exclusive scan
    total = Int(CUDA.@allowscalar off[end] + len[end])
    out = CuVector{UInt8}(undef, total)
    @cuda threads=128 blocks=nm gather_lines!(out, corpus, line_start, matched, off, len)
    return matched, off, len, out
end

"Split a packed line buffer (host copies) into strings."
function unpack_lines(out::Vector{UInt8}, off::Vector{Int32}, len::Vector{Int32})
    return [String(out[off[k] + 1:off[k] + len[k]]) for k in eachindex(len)]
end

# ---------------------------------------------------------------------------
# K6-K8: tokens and entropy (the Project 1 scanner adapted to tokens)
# ---------------------------------------------------------------------------

# K6: flags[i] = 1 where a token starts (a token byte not preceded by one).
function token_flags!(flags, corpus, is_tok)
    i      = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    stride = gridDim().x * blockDim().x
    n      = length(corpus)
    while i <= n
        @inbounds t = is_tok[corpus[i] + 1]
        @inbounds prev = i > 1 ? is_tok[corpus[i - 1] + 1] : 0x00
        @inbounds flags[i] = (t == 0x01 && prev == 0x00) ? UInt32(1) : UInt32(0)
        i += stride
    end
    return nothing
end

const ENT_THREADS = 256

# K7: one thread per token.  The thread walks its token (at most MAXTOK
# bytes), counting the 64 base64 symbols in a private shared-memory
# histogram (UInt8 counts, laid out so that the 32 threads of a warp touch
# consecutive bytes: no bank conflicts), then folds the counts into
# H = -sum p log2 p in bits per character, exactly the generator's formula.
# A private histogram per thread is the Project 1 privatisation idea taken to
# its limit: no atomics at all.
function token_entropy!(H, Ltok, corpus, token_start, is_tok, tok_symbol)
    counts = CuStaticSharedArray(UInt8, NSYM * ENT_THREADS)
    tid = threadIdx().x
    k   = (blockIdx().x - 1) * ENT_THREADS + tid           # token index
    k > length(token_start) && return nothing
    for s in 0:NSYM-1
        @inbounds counts[s * ENT_THREADS + tid] = 0x00
    end
    @inbounds i = token_start[k]
    n = length(corpus)
    L = 0
    @inbounds while i + L <= n && L < MAXTOK && is_tok[corpus[i + L] + 1] == 0x01
        sym = tok_symbol[corpus[i + L] + 1]
        counts[Int(sym) * ENT_THREADS + tid] += 0x01
        L += 1
    end
    h  = 0.0f0
    Lf = Float32(L)
    for s in 0:NSYM-1
        @inbounds c = counts[s * ENT_THREADS + tid]
        if c != 0x00
            p = Float32(c) / Lf
            h -= p * log2(p)
        end
    end
    @inbounds H[k] = h
    @inbounds Ltok[k] = Int32(L)
    return nothing
end

const HIST_BINS = 128       # entropy histogram: 0.05 bits per bin, 0 .. 6.4

# Histogram of the token entropies (the Project 1 privatised histogram):
# block-private bins in shared memory, merged once per block.
function entropy_hist!(hist, H)
    local_hist = CuStaticSharedArray(UInt32, HIST_BINS)
    tid = threadIdx().x
    k = tid
    while k <= HIST_BINS
        @inbounds local_hist[k] = 0x00000000
        k += blockDim().x
    end
    sync_threads()
    i      = (blockIdx().x - 1) * blockDim().x + tid
    stride = gridDim().x * blockDim().x
    n      = length(H)
    while i <= n
        @inbounds b = min(HIST_BINS, 1 + unsafe_trunc(Int32, H[i] * 20.0f0))     # 0.05-bit bins
        CUDA.@atomic local_hist[b] += 0x00000001
        i += stride
    end
    sync_threads()
    k = tid
    while k <= HIST_BINS
        @inbounds c = local_hist[k]
        if c != 0x00000000
            CUDA.@atomic hist[k] += c
        end
        k += blockDim().x
    end
    return nothing
end

# ---------------------------------------------------------------------------
# The pipeline
# ---------------------------------------------------------------------------

"Device copies of the pattern table and the character tables."
struct DevicePatterns
    pat::CuVector{UInt8}          # MAXPLEN * MAXPAT, column-major (pattern p at (p-1)*MAXPLEN + j)
    plen::CuVector{Int32}
    first_mask::CuVector{UInt32}
    is_word::CuVector{UInt8}
    is_tok::CuVector{UInt8}
    tok_symbol::CuVector{UInt8}
end
DevicePatterns(pt::PatternTable) = DevicePatterns(CuVector(vec(pt.pat)), CuVector(pt.plen), CuVector(pt.first_mask),
                                                  CuVector(IS_WORD), CuVector(IS_TOK), CuVector(TOK_SYMBOL))

"Launch the tiled match kernel over the whole corpus (line_mask must be zero)."
function launch_match!(line_mask, corpus, dp::DevicePatterns, line_start; tiled::Bool = true)
    n = length(corpus)
    if tiled
        @cuda threads=MATCH_THREADS blocks=max(1, cld(n, MATCH_TILE)) match_tiled!(line_mask, corpus, dp.pat, dp.plen, dp.first_mask, dp.is_word, line_start)
    else
        @cuda threads=256 blocks=grid_for(n) match_global!(line_mask, corpus, dp.pat, dp.plen, dp.first_mask, dp.is_word, line_start)
    end
    return nothing
end

"Token starts on the device via flags, scan and scatter (K6 + K2)."
function gpu_token_starts(corpus::CuVector{UInt8}, flags::CuVector{UInt32}, dp::DevicePatterns)
    @cuda threads=256 blocks=grid_for(length(corpus)) token_flags!(flags, corpus, dp.is_tok)
    starts, nt = compact_positions(flags)
    return starts
end

"Entropy and length of every token (K7)."
function gpu_token_entropies(corpus::CuVector{UInt8}, token_start::CuVector{Int32}, dp::DevicePatterns)
    nt = length(token_start)
    H = CuVector{Float32}(undef, nt)
    L = CuVector{Int32}(undef, nt)
    nt > 0 && @cuda threads=ENT_THREADS blocks=cld(nt, ENT_THREADS) token_entropy!(H, L, corpus, token_start, dp.is_tok, dp.tok_symbol)
    return H, L
end

"Histogram of entropies in HIST_BINS bins of 0.05 bits (host vector)."
function gpu_entropy_histogram(H::CuVector{Float32})
    hist = CUDA.zeros(UInt32, HIST_BINS)
    length(H) > 0 && @cuda threads=256 blocks=grid_for(length(H)) entropy_hist!(hist, H)
    return Array(hist)
end

"Indices (into the token table) of the tokens with H >= threshold (K8)."
function gpu_flagged_tokens(H::CuVector{Float32}, threshold)
    thr = Float32(threshold)
    fflags = map(h -> h >= thr ? UInt32(1) : UInt32(0), H)
    idx, nf = compact_positions(fflags)
    CUDA.unsafe_free!(fflags)
    return idx
end

"""
Choose the entropy threshold from the measured distribution: the midpoint of
the widest empty band of the histogram above the median token, i.e. the gap
that separates the main mass (the ordinary tokens) from the upper cluster.
Bands below the median are not candidates (the zero-entropy spike of
one-symbol tokens leaves an empty band just above 0 bits that is as wide as
the real gap); equal widths go to the higher band.  Returns the threshold and
the (lower, upper) bin edges of the band in bits.
"""
function choose_threshold(hist::Vector{UInt32})
    nonempty = findall(!=(0), hist)
    isempty(nonempty) && return 5.0, (0.0, 0.0)
    half = sum(hist) / 2
    median_bin = findfirst(>=(half), cumsum(hist))          # bin that holds the median token
    best = (0, 0, 0)                                      # (width, lo, hi) in bins
    prev = nonempty[1]
    for b in nonempty[2:end]
        gap = b - prev - 1
        prev >= median_bin && gap >= best[1] && gap > 0 && (best = (gap, prev, b))
        prev = b
    end
    best[1] == 0 && return 5.0, (0.0, 0.0)
    lo = best[2] * 0.05                                   # upper edge of the last full bin
    hi = (best[3] - 1) * 0.05                             # lower edge of the first bin after the gap
    return (lo + hi) / 2, (lo, hi)
end

"""
Run the whole track-E pipeline on a device corpus: line table, matching,
matched-line extraction, tokens, entropies, histogram, threshold, flagged
tokens.  Returns a named tuple with device results.  Used both for the
end-to-end timing and for validation.
"""
function gpu_pipeline(corpus::CuVector{UInt8}, dp::DevicePatterns; threshold = nothing, tiled::Bool = true)
    n = length(corpus)
    flags = CuVector{UInt32}(undef, n)
    line_start = gpu_line_starts(corpus, flags)
    line_mask  = CUDA.zeros(UInt32, length(line_start) - 1)
    launch_match!(line_mask, corpus, dp, line_start; tiled)
    matched, off, len, packed = extract_matched_lines(corpus, line_start, line_mask)
    token_start = gpu_token_starts(corpus, flags, dp)
    CUDA.unsafe_free!(flags)
    H, L = gpu_token_entropies(corpus, token_start, dp)
    hist = gpu_entropy_histogram(H)
    thr, band = threshold === nothing ? choose_threshold(hist) : (Float64(threshold), (0.0, 0.0))
    flagged = gpu_flagged_tokens(H, thr)
    return (; line_start, line_mask, matched, off, len, packed, token_start, H, L, hist, threshold = thr, band, flagged)
end

# The benchmark loops run the steps hundreds of times; freeing their outputs at
# once keeps the device pool small, so no garbage collection lands inside a
# timed launch.  (`unsafe_free!` only returns the block to the pool.)
"Free every device array among the arguments."
free_all!(xs...) = (foreach(x -> x isa CuArray && CUDA.unsafe_free!(x), xs); nothing)
"Free every device array in a `gpu_pipeline` result."
free_results!(r::NamedTuple) = free_all!(values(r)...)
