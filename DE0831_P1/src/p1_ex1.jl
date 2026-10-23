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

# Project 1, exercise 1: SAXPY (y <- αx + y, Float32) with a grid-stride loop.
include("p1_common.jl")

# ---------------------------------------------------------------------------
# Kernel
# ---------------------------------------------------------------------------

# A grid-stride loop: every thread starts at its global index and then jumps
# ahead by the number of threads in the whole grid, so the kernel covers all N
# elements whatever the launch configuration is, including blocks=1 and grids
# larger than N.  In each iteration neighbouring threads touch neighbouring
# elements, so the loads of x and y and the store of y stay coalesced.
function saxpy!(y, α, x)
    i      = (blockIdx().x - 1) * blockDim().x + threadIdx().x   # 1-based global index
    stride = gridDim().x * blockDim().x                          # threads in the grid
    n      = length(y)
    while i <= n                                                 # bounds check
        @inbounds y[i] = α * x[i] + y[i]
        i += stride
    end
    return nothing
end

# ---------------------------------------------------------------------------
# Host code
# ---------------------------------------------------------------------------

const α          = Float32(1 + STUDENT_ID % 7)
const THREADS    = 256
const BLOCKS     = (1, 16, 64, 256, 1024)
const BOUNDARY_N = (1, 31, 32, 33, 255, 256, 257)

println("α = $α")

"Run saxpy! once on fresh random vectors of length n and compare with the CPU."
function saxpy_matches_cpu(n, blocks; threads = THREADS)
    x = CuArray(rand(Float32, n))
    y = CuArray(rand(Float32, n))
    y_ref = Array(y) .+ α .* Array(x)
    @cuda threads=threads blocks=blocks saxpy!(y, α, x)
    CUDA.synchronize()
    return allclose(Array(y), y_ref)
end

# 0. Known-answer example from the step-by-step guide: α = 2, x = [1, 2, 3],
#    y = [10, 20, 30] must give [12, 24, 36], also with a single block.
y_small = CuArray(Float32[10, 20, 30])
@cuda threads=256 blocks=1 saxpy!(y_small, 2.0f0, CuArray(Float32[1, 2, 3]))
CUDA.synchronize()
require(Array(y_small) == Float32[12, 24, 36], "known-answer SAXPY example")

# 1. The configuration from the brief: a FIXED grid of 64 blocks, not cld(N, 256).
#    Inputs are generated on the CPU from the seeded RNG so every run is reproducible.
x = CuArray(rand(Float32, N))
y = CuArray(rand(Float32, N))
y_ref = Array(y) .+ α .* Array(x)
@cuda threads=256 blocks=64 saxpy!(y, α, x)
CUDA.synchronize()
require(allclose(Array(y), y_ref), "saxpy! with threads=256, blocks=64, N=$N")

# 2. Correct for any grid size: every benchmarked grid, odd block sizes, the
#    guide's 10 elements on 4 threads, and a grid with more threads than elements.
for b in BLOCKS
    require(saxpy_matches_cpu(N, b), "saxpy! with blocks=$b, N=$N")
end
require(saxpy_matches_cpu(10, 1; threads = 4), "saxpy! with 4 threads, N=10")
for (t, b) in ((32, 1), (100, 3), (1024, 1), (256, cld(N, 256) + 7))
    require(saxpy_matches_cpu(N, b; threads = t), "saxpy! with threads=$t, blocks=$b, N=$N")
end

# 3. Boundary sizes around the warp (32) and block (256) size, for every grid.
for n in BOUNDARY_N, b in BLOCKS
    require(saxpy_matches_cpu(n, b), "saxpy! with blocks=$b, N=$n")
end
println("Boundary tests passed: N ∈ $(BOUNDARY_N), blocks ∈ $(BLOCKS)")
println("Correct!")

# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

"""
Time saxpy! for each grid in `BLOCKS` at vector length n.  SAXPY overwrites y,
so y is restored from an unchanged copy (outside the timed interval) before
every timed launch, and the result after the last measured launch is checked.
"""
function bench_saxpy(n)
    x  = CuArray(rand(Float32, n))
    y0 = CuArray(rand(Float32, n))           # initial y, never modified
    y  = copy(y0)
    y_ref = Array(y0) .+ α .* Array(x)
    bytes = 3 * n * sizeof(Float32)          # 12n: read x, read y, write y
    rows = Any[]
    for b in BLOCKS
        launch  = () -> @cuda threads=THREADS blocks=b saxpy!(y, α, x)
        restore = () -> copyto!(y, y0)
        s = time_stats(launch; reset = restore)
        require(allclose(Array(y), y_ref), "saxpy! result after timing, blocks=$b, n=$n")
        bw = gbps(bytes, s.mean)
        push!(rows, (b, b * THREADS, cld(n, b * THREADS), us(s.mean), "$(us(s.min)) – $(us(s.max))", f1(bw)))
        println("  n = $n, blocks = $b: $(us(s.mean)) µs, $(f1(bw)) GB/s")
    end
    return rows
end

if !QUICK
    record_device_info()
    N_LARGE = 4096 * N
    println("\nBenchmark at N = $N")
    rows_n = bench_saxpy(N)
    println("Benchmark at N_large = $N_LARGE")
    rows_large = bench_saxpy(N_LARGE)
    copy_bw = measured_copy_bandwidth()
    theo_bw = theoretical_bandwidth()
    println("Device-to-device copy: $(f1(copy_bw)) GB/s")

    header = ["blocks", "threads in grid", "elements per thread", "mean time (µs)",
              "min – max (µs)", "bandwidth (GB/s)"]
    section = """
    ## Exercise 1: SAXPY with a grid-stride loop

    $(run_info_md())
    α = $α, 256 threads per block.  y is restored from an unchanged copy before every timed
    launch (outside the timed interval), so each of the $REPS samples is one `CUDA.@elapsed`
    around one launch; the result after the last sample is checked against the CPU.  Bytes per
    launch = 12 · n (read x, read y, write y, Float32); effective bandwidth = 12n / mean time / 10⁹.

    **Required size, n = N = $N** ($(f1(3 * N * 4 / 1e3)) kB per launch)

    $(md_table(header, rows_n))
    **Additional size, n = 4096 · N = $N_LARGE** ($(f1(3 * N_LARGE * 4 / 1e6)) MB per launch),
    large enough that the time is set by memory traffic rather than launch overhead

    $(md_table(header, rows_large))
    Reference points: device-to-device `copyto!` reaches $(f1(copy_bw)) GB/s
    (read + write)$(theo_bw === nothing ? "" : "; theoretical DRAM bandwidth is $(f1(theo_bw)) GB/s").
    """
    update_section!(BENCH_FILE, "ex1", section)
    println("Results written to $BENCH_FILE")
end
