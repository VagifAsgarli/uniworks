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

# Project 1, exercise 3: 256-bin byte histogram, naive and privatised.
include("p1_common.jl")

const NBINS = 256

# ---------------------------------------------------------------------------
# Kernels
# ---------------------------------------------------------------------------
# Both kernels use the same grid-stride loop over the input (coalesced byte
# reads, any grid size), so the only difference between them is where the
# atomic increments go.  Bin k+1 counts byte value k (Julia is 1-based).

# Naive: one atomic add on the global histogram per input byte.  It is the
# most direct correct parallel histogram, but every thread on the GPU competes
# for the same 256 counters in global memory, and atomics on the same address
# are serialised in the L2 cache, so a popular bin becomes a bottleneck.
function hist_naive!(hist, data)
    i      = (blockIdx().x - 1) * blockDim().x + threadIdx().x
    stride = gridDim().x * blockDim().x
    n      = length(data)
    while i <= n
        @inbounds b = data[i]
        CUDA.@atomic hist[b + 1] += UInt32(1)
        i += stride
    end
    return nothing
end

# Privatised: each block first counts into its own 256-bin copy in shared
# memory, where atomics are much cheaper and only the threads of one block
# compete, and then adds its partial counts to the global histogram once.
# Global atomic traffic drops from one per byte to at most 256 per block; the
# loops over k work for any block size, not only 256 threads.
function hist_privatised!(hist, data)
    local_hist = CuStaticSharedArray(UInt32, NBINS)
    tid = threadIdx().x

    k = tid                                           # 1. zero the private histogram
    while k <= NBINS
        @inbounds local_hist[k] = UInt32(0)
        k += blockDim().x
    end
    sync_threads()

    i      = (blockIdx().x - 1) * blockDim().x + tid  # 2. count into shared memory
    stride = gridDim().x * blockDim().x
    n      = length(data)
    while i <= n
        @inbounds b = data[i]
        CUDA.@atomic local_hist[b + 1] += UInt32(1)
        i += stride
    end
    sync_threads()

    k = tid                                           # 3. merge once per block
    while k <= NBINS
        @inbounds c = local_hist[k]
        if c != 0
            CUDA.@atomic hist[k] += c
        end
        k += blockDim().x
    end
    return nothing
end

# ---------------------------------------------------------------------------
# Host code
# ---------------------------------------------------------------------------

const LEN     = N * 10_000
const THREADS = 256
const BLOCKS  = 16 * sm_count()      # a few resident blocks per SM; same grid for both kernels

"CPU reference histogram."
function hist_cpu(data)
    h = zeros(UInt32, NBINS)
    @inbounds for b in data
        h[b + 1] += 1
    end
    return h
end

"Uniform random bytes."
uniform_bytes(n) = rand(UInt8, n)

"Skewed bytes: exactly 90 % (rounded) are 0x00, the rest are random non-zero bytes, shuffled with the seeded RNG."
function skewed_bytes(n)
    nzero = round(Int, 0.9 * n)
    return shuffle!(vcat(zeros(UInt8, nzero), rand(0x01:0xff, n - nzero)))
end

function run_hist(kernel, data_d; threads = THREADS, blocks = BLOCKS)
    hist = CUDA.zeros(UInt32, NBINS)
    @cuda threads=threads blocks=blocks kernel(hist, data_d)
    CUDA.synchronize()
    return Array(hist)
end

# Known-answer example from the step-by-step guide: UInt8[0, 0, 1, 255] gives
# bin 1 (byte 0) = 2, bin 2 (byte 1) = 1, bin 256 (byte 255) = 1, all others 0.
let expected = zeros(UInt32, NBINS), small_d = CuArray(UInt8[0, 0, 1, 255])
    expected[1], expected[2], expected[256] = 2, 1, 1
    require(run_hist(hist_naive!, small_d) == expected, "known-answer histogram (naive)")
    require(run_hist(hist_privatised!, small_d) == expected, "known-answer histogram (privatised)")
end

println("Input length = N · 10000 = $LEN bytes, grid = $BLOCKS × $THREADS threads")
datasets = (("uniform", uniform_bytes(LEN)), ("skewed (90 % 0x00)", skewed_bytes(LEN)))

# Verify both kernels on both datasets against the CPU (exact integer counts),
# plus small inputs and unusual launch shapes.
for (name, data) in datasets
    ref = hist_cpu(data)
    data_d = CuArray(data)
    require(run_hist(hist_naive!, data_d) == ref, "naive histogram, $name data")
    require(run_hist(hist_privatised!, data_d) == ref, "privatised histogram, $name data")
    println("  $name: 0x00 fraction = $(f3(ref[1] / LEN)), both kernels match the CPU")
end
for n in (1, 33, 257, 1000), (t, b) in ((256, 1), (64, 3), (512, 2), (1024, 40))
    data = rand(UInt8, n)
    ref = hist_cpu(data)
    data_d = CuArray(data)
    require(run_hist(hist_naive!, data_d; threads = t, blocks = b) == ref, "naive histogram, n=$n, threads=$t, blocks=$b")
    require(run_hist(hist_privatised!, data_d; threads = t, blocks = b) == ref, "privatised histogram, n=$n, threads=$t, blocks=$b")
end
println("Correct!")

# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

if !QUICK
    record_device_info()
    rows = Any[]
    speedups = Dict{String,Float64}()
    for (name, data) in datasets
        data_d = CuArray(data)
        hist = CUDA.zeros(UInt32, NBINS)
        # Both kernels accumulate into `hist`, so it is zeroed (untimed) before every launch.
        reset        = () -> fill!(hist, UInt32(0))
        launch_naive = () -> @cuda threads=THREADS blocks=BLOCKS hist_naive!(hist, data_d)
        launch_priv  = () -> @cuda threads=THREADS blocks=BLOCKS hist_privatised!(hist, data_d)
        t_naive = time_kernel(launch_naive; reset = reset)
        t_priv  = time_kernel(launch_priv; reset = reset)
        require(Array(hist) == hist_cpu(data), "histogram after benchmarking, $name data")
        speedups[name] = t_naive / t_priv
        push!(rows, (name, f3(count(==(0x00), data) / LEN),
                     ms(t_naive), f1(gbps(LEN, t_naive)),
                     ms(t_priv), f1(gbps(LEN, t_priv)),
                     f2(t_naive / t_priv)))
        println("  $name: naive $(ms(t_naive)) ms, privatised $(ms(t_priv)) ms, speedup $(f2(t_naive / t_priv))×")
    end

    header = ["dataset", "fraction 0x00", "naive (ms)", "naive (GB/s)",
              "privatised (ms)", "privatised (GB/s)", "speedup privatised / naive"]
    su_u = f2(speedups["uniform"])
    su_s = f2(speedups["skewed (90 % 0x00)"])
    conclusion = if speedups["skewed (90 % 0x00)"] > speedups["uniform"]
        "The skewed data still costs the privatised kernel some time (its shared `hist[1]` is " *
        "contended too), but much less than it costs the naive kernel, which is why the speedup " *
        "is larger on the skewed dataset ($(su_s)× against $(su_u)×)."
    else
        "**Note: on this device the measured speedup is not larger on the skewed data " *
        "($(su_s)× against $(su_u)×), which contradicts this contention model; check the " *
        "naive and privatised times per dataset before drawing conclusions.**"
    end
    # A speedup below 1 is reported as measured and explained.
    if speedups["uniform"] < 1
        conclusion *= "  On the uniform dataset the privatised kernel was slower ($(su_u)×): with bytes " *
            "spread over 256 bins the naive kernel's global atomics rarely hit the same address, so there " *
            "is little contention for privatisation to remove, while each block pays for zeroing and " *
            "merging its 256 shared bins and for two barriers."
    end
    if speedups["skewed (90 % 0x00)"] < 1
        conclusion *= "  On the skewed dataset the privatised kernel was slower ($(su_s)×): inside each " *
            "block 90 % of the shared-memory atomics hit the same word `local_hist[1]`, and on this GPU " *
            "serialising them per block cost more than the naive kernel's global atomics on `hist[1]`."
    end
    section = """
    ## Exercise 3: privatised histogram

    $(run_info_md())
    Input: N · 10000 = $LEN bytes (UInt8), 256 bins (UInt32).  Uniform: random bytes; skewed:
    exactly 90 % of the positions hold 0x00 and the rest random non-zero bytes, shuffled with the
    seeded RNG.  Both kernels see identical data.  Grid = $BLOCKS blocks × $THREADS
    threads (16 blocks per SM) for both kernels.  The histogram is zeroed before every launch
    outside the timed region (reset-aware timing, one `CUDA.@elapsed` per launch).  Bandwidth =
    input bytes / time / 10⁹; speedup = naive time / privatised time.

    $(md_table(header, rows))
    **Speedup of privatised over naive: $(su_u)× on uniform data, $(su_s)× on skewed data.**

    **Why the speedup depends on the data.** Atomic updates of the *same* address cannot proceed in
    parallel: the hardware serialises them.  With uniform bytes the naive kernel's global atomics
    are spread over 256 different addresses, so the L2 atomic units process many of them
    concurrently and the naive kernel is already reasonably fast.  With 90 % of the bytes equal to
    0x00, nine out of ten global atomics from every thread on the GPU target the single counter
    `hist[1]`, so they queue up behind each other in L2 and the naive kernel slows down sharply.
    The privatised kernel moves that contention into shared memory, where each block has its own
    copy of `hist[1]`: only the threads of one block compete, shared-memory atomics have far lower
    latency than L2 atomics, and the SMs work on their copies in parallel.  $conclusion
    """
    update_section!(BENCH_FILE, "ex3", section)
    println("Results written to $BENCH_FILE")
end
