# p1_common.jl - host-side helpers shared by p1_ex1.jl ... p1_ex4.jl:
# kernel timing, correctness checks, device information and the Markdown
# results tables.  No assessed GPU kernel lives here; every kernel is in its
# own exercise file.
#
# Each exercise script runs the individualisation header first (STUDENT_ID,
# N, SEED, `using CUDA, Random`) and then includes this file.

using Printf

const PROJECT_ROOT = normpath(joinpath(@__DIR__, ".."))
const RESULTS_DIR  = joinpath(PROJECT_ROOT, "results")
const BENCH_FILE   = joinpath(RESULTS_DIR, "benchmarks.md")
const README_FILE  = joinpath(PROJECT_ROOT, "README.md")

# Launches per timing (the brief uses 100).  P1_REPS=<n> overrides it and
# P1_QUICK=1 runs only the correctness checks (used by test/runtests.jl).
const REPS  = parse(Int, get(ENV, "P1_REPS", "100"))
const QUICK = get(ENV, "P1_QUICK", "0") == "1"

# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------

"Throw an error with `msg` unless `cond` holds (unlike @assert, never disabled)."
require(cond::Bool, msg) = cond || error("CHECK FAILED: " * string(msg))

"Element-wise approximate equality of two arrays of the same shape."
allclose(a, b; rtol = 1e-5, atol = 1e-6) =
    size(a) == size(b) && all(isapprox.(a, b; rtol = rtol, atol = atol))

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

"""
    time_kernel(launch; reps = REPS, reset = nothing) -> seconds per launch

`launch` is a zero-argument function that performs one GPU operation
(normally one `@cuda` launch).  It is run once as a warm-up, which also
JIT-compiles the kernel, followed by `CUDA.synchronize()`, so neither
compilation nor earlier queued work ends up in the measurement.

* `reset === nothing` (kernels that are safe to repeat): `reps` back-to-back
  launches inside one `CUDA.@elapsed` block, i.e. GPU time measured with CUDA
  events, divided by `reps`.
* State-changing kernels (e.g. a histogram that accumulates into its output):
  `reset()` restores the state before every launch.  The reset runs outside
  the timed region; each launch gets its own `CUDA.@elapsed` and the mean is
  returned.
"""
function time_kernel(launch::Function; reps::Integer = REPS, reset = nothing)
    reset === nothing || return time_stats(launch; reps = reps, reset = reset).mean
    launch()                                   # warm-up (and compilation)
    CUDA.synchronize()
    elapsed = CUDA.@elapsed begin
        for _ in 1:reps
            launch()
        end
    end
    return Float64(elapsed) / reps
end

"""
    time_stats(launch; reps = REPS, reset = nothing) -> (; mean, min, max) seconds

Warm-up launch + `CUDA.synchronize()`, then `reps` launches each timed by its
own `CUDA.@elapsed`; `reset()` (if given) restores the inputs before every
launch, outside the timed interval.  The minimum and maximum show the variation
between samples, which matters for kernels that run for only a few µs.
"""
function time_stats(launch::Function; reps::Integer = REPS, reset = nothing)
    reset === nothing || reset()
    launch()                                   # warm-up (and compilation)
    CUDA.synchronize()
    samples = zeros(reps)
    for r in 1:reps
        reset === nothing || reset()
        CUDA.synchronize()
        samples[r] = CUDA.@elapsed launch()
    end
    return (mean = sum(samples) / reps, min = minimum(samples), max = maximum(samples))
end

"Bandwidth in GB/s (1 GB = 10^9 bytes) for `bytes` moved in `t` seconds."
gbps(bytes, t) = bytes / t / 1e9

"Throughput in MB/s (1 MB = 10^6 bytes) for `bytes` processed in `t` seconds."
mbps(bytes, t) = bytes / t / 1e6

f1(x) = @sprintf("%.1f", x)
f2(x) = @sprintf("%.2f", x)
f3(x) = @sprintf("%.3f", x)
us(t) = f2(t * 1e6)                 # seconds -> µs, 2 decimals
ms(t) = f3(t * 1e3)                 # seconds -> ms, 3 decimals

# ---------------------------------------------------------------------------
# Device information
# ---------------------------------------------------------------------------

"Device attribute by short name (e.g. :MULTIPROCESSOR_COUNT), or `nothing`."
function device_attr(name::Symbol)
    for prefix in ("DEVICE_ATTRIBUTE_", "CU_DEVICE_ATTRIBUTE_")
        sym = Symbol(prefix, name)
        isdefined(CUDA, sym) || continue
        try
            return Int(CUDA.attribute(CUDA.device(), getfield(CUDA, sym)))
        catch
        end
    end
    return nothing
end

"Number of streaming multiprocessors (falls back to 32 if unknown)."
sm_count() = something(device_attr(:MULTIPROCESSOR_COUNT), 32)

"Theoretical DRAM bandwidth in GB/s from memory clock and bus width, or `nothing`."
function theoretical_bandwidth()
    clk = device_attr(:MEMORY_CLOCK_RATE)          # kHz
    bus = device_attr(:GLOBAL_MEMORY_BUS_WIDTH)    # bits
    (clk === nothing || bus === nothing || clk == 0 || bus == 0) && return nothing
    return 2 * clk * 1e3 * (bus / 8) / 1e9         # double data rate
end

# FP32 lanes per SM, by compute capability (CUDA C Programming Guide).
const FP32_LANES_PER_SM = Dict(
    (5, 0) => 128, (5, 2) => 128, (5, 3) => 128,
    (6, 0) => 64,  (6, 1) => 128, (6, 2) => 128,
    (7, 0) => 64,  (7, 2) => 64,  (7, 5) => 64,
    (8, 0) => 64,  (8, 6) => 128, (8, 7) => 128, (8, 9) => 128,
    (9, 0) => 128, (10, 0) => 128, (10, 1) => 128, (10, 3) => 128,
    (11, 0) => 128, (12, 0) => 128, (12, 1) => 128,
)

"Theoretical FP32 peak in GFLOP/s (2 FLOP per FMA lane per cycle), or `nothing`."
function theoretical_fp32_gflops()
    cc    = CUDA.capability(CUDA.device())
    lanes = get(FP32_LANES_PER_SM, (Int(cc.major), Int(cc.minor)), nothing)
    sms   = device_attr(:MULTIPROCESSOR_COUNT)
    clk   = device_attr(:CLOCK_RATE)                # kHz
    (lanes === nothing || sms === nothing || clk === nothing || clk == 0) && return nothing
    return 2 * lanes * sms * clk * 1e3 / 1e9
end

"""
Measured device-to-device copy bandwidth in GB/s (read + write counted): a
practical upper bound for any streaming kernel on this GPU.
"""
function measured_copy_bandwidth(; nbytes = 256 * 2^20)
    src = CUDA.zeros(UInt8, nbytes)
    dst = CUDA.zeros(UInt8, nbytes)
    t = time_kernel(() -> copyto!(dst, src))
    return gbps(2 * nbytes, t)
end

"Markdown bullet list describing the GPU and the software stack."
function device_info_md()
    dev = CUDA.device()
    lines = String[
        "- GPU: $(CUDA.name(dev))",
        "- Compute capability: $(CUDA.capability(dev))",
    ]
    sms = device_attr(:MULTIPROCESSOR_COUNT)
    sms === nothing || push!(lines, "- Streaming multiprocessors: $sms")
    try
        push!(lines, "- Device memory: $(f2(CUDA.totalmem(dev) / 2^30)) GiB")
    catch
    end
    bw = theoretical_bandwidth()
    bw === nothing || push!(lines, "- Theoretical DRAM bandwidth: $(f1(bw)) GB/s")
    fl = theoretical_fp32_gflops()
    fl === nothing || push!(lines, "- Theoretical FP32 peak: $(f1(fl)) GFLOP/s")
    for (label, getter) in (("CUDA driver", CUDA.driver_version),
                            ("CUDA runtime", CUDA.runtime_version))
        try
            push!(lines, "- $label: $(getter())")
        catch
        end
    end
    push!(lines, "- Julia: $(VERSION), CUDA.jl: $(pkgversion(CUDA))")
    push!(lines, "- Host CPU: $(strip(Sys.cpu_info()[1].model)) ($(Sys.CPU_THREADS) threads)")
    return join(lines, "\n")
end

# ---------------------------------------------------------------------------
# Markdown results
# ---------------------------------------------------------------------------

"Render a Markdown table (all columns right-aligned)."
function md_table(header, rows)
    io = IOBuffer()
    println(io, "| ", join(header, " | "), " |")
    println(io, "|", join(fill("---:", length(header)), "|"), "|")
    for r in rows
        println(io, "| ", join(string.(r), " | "), " |")
    end
    return String(take!(io))
end

"""
    update_section!(file, tag, content)

Replace the text between `<!-- BEGIN tag -->` and `<!-- END tag -->` in
`file` with `content` (appending the block if it is not there yet), so each
script refreshes only its own part of a shared results file.
"""
function update_section!(file, tag, content)
    open_m  = "<!-- BEGIN $tag -->"
    close_m = "<!-- END $tag -->"
    text  = isfile(file) ? read(file, String) : ""
    block = string(open_m, "\n", strip(content), "\n", close_m)
    a = findfirst(open_m, text)
    b = findfirst(close_m, text)
    if a !== nothing && b !== nothing && first(b) > last(a)
        text = text[1:prevind(text, first(a))] * block * text[nextind(text, last(b)):end]
    else
        text = rstrip(text) * "\n\n" * block * "\n"
    end
    mkpath(dirname(file))
    write(file, text)
    return nothing
end

"Common preamble for a results section: who, where, and how it was measured."
function run_info_md()
    return """
    Student: $STUDENT_NAME ($STUDENT_CARD), N = $N, seed = $SEED.
    Device: $(CUDA.name(CUDA.device())) (compute capability $(CUDA.capability(CUDA.device()))).
    Timing: one warm-up launch + `CUDA.synchronize()`, then `CUDA.@elapsed` (CUDA events, GPU
    time) over $REPS launches; the tables report the mean time per launch.  Kernel times exclude
    host/device transfers, file I/O, plotting and CPU checks unless a row says otherwise.
    """
end

"Record the device block in README.md (every script does this, so it stays current)."
record_device_info() = update_section!(README_FILE, "device", device_info_md())
