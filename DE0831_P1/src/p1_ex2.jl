const STUDENT_CARD = "251ADM047"                               # <- your student card number
const STUDENT_ID   = parse(Int, filter(isdigit, STUDENT_CARD))  # 251047: its digits, for N and SEED
const STUDENT_NAME = "Vagif Asgarli"

const N_BASE = 1024
const N      = N_BASE + (STUDENT_ID % 37) * 64      # unique array size
const SEED   = STUDENT_ID % 100_000                 # unique RNG seed

using CUDA, Random
Random.seed!(SEED)

println("Student: $STUDENT_NAME, ID: $STUDENT_CARD (digits $STUDENT_ID used for N and SEED)")
println("Device: ", CUDA.name(CUDA.device()))
println("Compute capability: ", CUDA.capability(CUDA.device()))
println("Problem size N = $N, seed = $SEED")

# Project 1, exercise 2: N×N Float32 matrix transpose, naive and tiled.
include("p1_common.jl")

# ---------------------------------------------------------------------------
# Kernels
# ---------------------------------------------------------------------------
# Julia arrays are column-major: A[i, j] and A[i+1, j] are neighbours in
# memory.  threadIdx().x is the fastest-varying thread index inside a warp, so
# it is always mapped to the FIRST array index of the access that should be
# coalesced.

# Naive: one thread per element, B[j, i] = A[i, j].  threadIdx().x runs along
# i, so the read of A walks down a column and is coalesced, but the write to
# B[j, i] jumps by a whole column (N floats) between neighbouring threads, so
# every thread of a warp writes to a different memory segment.  It is the
# simplest correct version and the baseline the tiled kernel must beat.
function transpose_naive!(B, A)
    i = (blockIdx().x - 1) * blockDim().x + threadIdx().x     # row of A
    j = (blockIdx().y - 1) * blockDim().y + threadIdx().y     # column of A
    if i <= size(A, 1) && j <= size(A, 2)
        @inbounds B[j, i] = A[i, j]
    end
    return nothing
end

# Tiled: a TILE×TILE block of threads copies one tile of A into shared memory
# with coalesced reads, waits at a barrier, and then writes the tile to B with
# threadIdx().x running along B's first index, so the writes are coalesced
# too; the transposition happens in shared memory, where strided access is
# cheap.  The shared array is (TILE+1)×TILE: the extra row shifts each column
# of the tile to a different shared-memory bank, so reading a row of the tile
# (stride TILE+1 words) does not serialise on one bank.  TILE is a type
# parameter so the shared-memory size is a compile-time constant.
function transpose_tiled!(B, A, ::Val{TILE}) where {TILE}
    tile = CuStaticSharedArray(Float32, (TILE + 1, TILE))
    tx, ty = threadIdx().x, threadIdx().y
    i0 = (blockIdx().x - 1) * TILE                            # tile origin: row of A
    j0 = (blockIdx().y - 1) * TILE                            # tile origin: column of A

    # Load: thread (tx, ty) reads A[i0+tx, j0+ty]; tx runs down a column of A.
    i, j = i0 + tx, j0 + ty
    if i <= size(A, 1) && j <= size(A, 2)
        @inbounds tile[tx, ty] = A[i, j]
    end
    sync_threads()

    # Store: thread (tx, ty) writes B[j0+tx, i0+ty] = A[i0+ty, j0+tx] = tile[ty, tx];
    # tx runs down a column of B.
    bi, bj = j0 + tx, i0 + ty
    if bi <= size(B, 1) && bj <= size(B, 2)
        @inbounds B[bi, bj] = tile[ty, tx]
    end
    return nothing
end

# For comparison only (not an assessed kernel): the same tiled kernel without
# the padding row, used to measure what the padding buys.
function transpose_tiled_nopad!(B, A, ::Val{TILE}) where {TILE}
    tile = CuStaticSharedArray(Float32, (TILE, TILE))
    tx, ty = threadIdx().x, threadIdx().y
    i0 = (blockIdx().x - 1) * TILE
    j0 = (blockIdx().y - 1) * TILE
    i, j = i0 + tx, j0 + ty
    if i <= size(A, 1) && j <= size(A, 2)
        @inbounds tile[tx, ty] = A[i, j]
    end
    sync_threads()
    bi, bj = j0 + tx, i0 + ty
    if bi <= size(B, 1) && bj <= size(B, 2)
        @inbounds B[bi, bj] = tile[ty, tx]
    end
    return nothing
end

# Reference for the bandwidth tables (not an assessed kernel): a plain copy
# with both accesses coalesced, i.e. the best a transpose could hope for.
function copy2d!(B, A)
    i = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    j = (blockIdx().y - 1) * blockDim().y + threadIdx().y
    if i <= size(A, 1) && j <= size(A, 2)
        @inbounds B[i, j] = A[i, j]
    end
    return nothing
end

# ---------------------------------------------------------------------------
# Host code
# ---------------------------------------------------------------------------

const TILES = (8, 16, 32)

# One launcher per kernel: a TILE×TILE thread block per TILE×TILE tile of A
# (A is n×m, B is m×n).
launch_naive(B, A, tile) =
    @cuda threads=(tile, tile) blocks=(cld(size(A, 1), tile), cld(size(A, 2), tile)) transpose_naive!(B, A)
launch_tiled(B, A, tile) =
    @cuda threads=(tile, tile) blocks=(cld(size(A, 1), tile), cld(size(A, 2), tile)) transpose_tiled!(B, A, Val(tile))
launch_nopad(B, A, tile) =
    @cuda threads=(tile, tile) blocks=(cld(size(A, 1), tile), cld(size(A, 2), tile)) transpose_tiled_nopad!(B, A, Val(tile))
launch_copy(B, A, tile) =
    @cuda threads=(tile, tile) blocks=(cld(size(A, 1), tile), cld(size(A, 2), tile)) copy2d!(B, A)

const TRANSPOSES = (("naive", launch_naive), ("tiled", launch_tiled), ("tiled, no padding", launch_nopad))

# Known-answer example from the step-by-step guide: [1 2 3; 4 5 6] -> [1 4; 2 5; 3 6].
A_small = CuArray(Float32[1 2 3; 4 5 6])
for tile in TILES, (name, launch) in TRANSPOSES
    B = CUDA.fill(NaN32, 3, 2)
    launch(B, A_small, tile)
    CUDA.synchronize()
    require(Array(B) == Float32[1 4; 2 5; 3 6], "known-answer transpose ($name), TILE=$tile")
end

# Verify every transpose kernel against Array(A)' for every TILE: at N×N, at
# sizes that are not multiples of any TILE (partial tiles at the edges), and
# on rectangular matrices (catches swapped row/column indices).
for (n, m) in ((N, N), (1, 1), (33, 33), (257, 257), (37, 70), (70, 37))
    A = CuArray(rand(Float32, n, m))
    A_ref = Array(A)'
    for tile in TILES, (name, launch) in TRANSPOSES
        B = CUDA.fill(NaN32, m, n)          # NaN marks any element never written
        launch(B, A, tile)
        CUDA.synchronize()
        require(Array(B) == A_ref, "transpose ($name) with TILE=$tile on a $n×$m matrix")
    end
end
println("Naive and tiled transposes match Array(A)' for TILE ∈ $(TILES), including ragged and rectangular sizes")
println("Correct!")

# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

if !QUICK
    record_device_info()
    A = CuArray(rand(Float32, N, N))
    B = CUDA.zeros(Float32, N, N)
    bytes = 2 * N * N * sizeof(Float32)                 # read A once, write B once

    rows = Any[]
    for tile in TILES
        t_copy  = time_kernel(() -> launch_copy(B, A, tile))
        t_naive = time_kernel(() -> launch_naive(B, A, tile))
        t_tiled = time_kernel(() -> launch_tiled(B, A, tile))
        t_nopad = time_kernel(() -> launch_nopad(B, A, tile))
        push!(rows, (tile, tile * tile,
                     us(t_naive), f1(gbps(bytes, t_naive)),
                     us(t_tiled), f1(gbps(bytes, t_tiled)),
                     f1(gbps(bytes, t_nopad)), f1(gbps(bytes, t_copy)),
                     f2(t_naive / t_tiled)))
        println("  TILE = $tile: naive $(f1(gbps(bytes, t_naive))) GB/s, tiled $(f1(gbps(bytes, t_tiled))) GB/s, " *
                "no padding $(f1(gbps(bytes, t_nopad))) GB/s, copy $(f1(gbps(bytes, t_copy))) GB/s")
    end

    header = ["TILE", "threads per block", "naive (µs)", "naive (GB/s)", "tiled (µs)",
              "tiled (GB/s)", "tiled, no padding (GB/s)", "copy reference (GB/s)",
              "speedup tiled / naive"]
    section = """
    ## Exercise 2: matrix transpose

    $(run_info_md())
    Matrix: $N × $N Float32 ($(f1(N * N * 4 / 1e6)) MB).  Thread block = TILE × TILE for every kernel.
    Bytes per launch = 2 · N² · 4 B (each element read once and written once);
    bandwidth = bytes / time / 10⁹.  "Tiled, no padding" and "copy reference" are
    extra kernels for comparison: the copy is a transpose-free 2D copy with both accesses coalesced.

    $(md_table(header, rows))
    **Why padding reduces bank conflicts.** Shared memory is split into 32 banks of 4-byte
    words and threads of a warp that hit different words of the same bank are serialised; in
    the store phase a warp reads one row of the column-major tile, whose elements in an
    unpadded 32 × 32 tile are 32 words apart and so all sit in the same bank (a 32-way conflict).
    Padding the leading dimension to TILE + 1 = 33 words puts consecutive row elements 33 words
    apart, so they fall into 32 different banks and the warp is served in one shared-memory
    access instead of 32.
    """
    update_section!(BENCH_FILE, "ex2", section)
    println("Results written to $BENCH_FILE")
end
