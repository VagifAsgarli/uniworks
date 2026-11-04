# rp_common.jl - host-side helpers shared by the research-project scripts (the Project 2 harness): kernel
# timing, correctness checks, device information and the Markdown results
# tables.  No assessed GPU kernel lives here.
#
# The timing harness is the one from Project 1 (warm-up launch, then
# CUDA.@elapsed around every launch); the resident-block wording of the
# Project 1 comments is corrected here (grid size and residency are different
# things, see `resident_blocks_per_sm`).

using CUDA, Printf

const PROJECT_ROOT = normpath(joinpath(@__DIR__, ".."))
const RESULTS_DIR  = joinpath(PROJECT_ROOT, "results")
const DATA_DIR     = joinpath(PROJECT_ROOT, "data")
const BENCH_FILE   = joinpath(RESULTS_DIR, "benchmarks.md")
const README_FILE  = joinpath(PROJECT_ROOT, "README.md")

# Launches per timing (the brief uses 100).  RP_REPS=<n> overrides it,
# RP_QUICK=1 runs only the correctness checks (used by test/runtests.jl), and
# RP_SIZES="125000,250000" restricts the corpus sizes.
const REPS  = parse(Int, get(ENV, "RP_REPS", "100"))
const QUICK = get(ENV, "RP_QUICK", "0") == "1"

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
    time_stats(launch; reps = REPS, reset = nothing) -> (; mean, min, max) seconds

`launch` is a zero-argument function that performs one GPU operation (a
kernel launch, an array operation, or a whole pipeline).  It runs once as a
warm-up, which also compiles the kernels, followed by `CUDA.synchronize()`,
so neither compilation nor earlier queued work is measured.  Then `reps`
launches are each timed with their own `CUDA.@elapsed` (CUDA events on the
stream: GPU time).  `reset()`, if given, restores the inputs before every
launch, outside the timed interval (for kernels that accumulate into their
output).  The minimum and maximum show the variation between samples.
"""
function time_stats(launch::Function; reps::Integer = REPS, reset = nothing)
    reset === nothing || reset()
    launch()                                   # warm-up (and compilation)
    CUDA.synchronize()
    samples = zeros(reps)
    for r in 1:reps
        if reset !== nothing
            reset()
            CUDA.synchronize()
        end
        samples[r] = CUDA.@elapsed launch()
    end
    return (mean = sum(samples) / reps, min = minimum(samples), max = maximum(samples))
end

"Mean GPU time per launch, see `time_stats`."
time_kernel(launch::Function; kwargs...) = time_stats(launch; kwargs...).mean

"""
    time_cpu(f; reps = 3) -> (; mean, min, max) seconds

Wall-clock time of a CPU function (`@elapsed` is correct for CPU code; it is
never used around a GPU launch).  One warm-up call, then `reps` timed calls.
"""
function time_cpu(f::Function; reps::Integer = 3)
    f()
    samples = [(@elapsed f()) for _ in 1:reps]
    return (mean = sum(samples) / reps, min = minimum(samples), max = maximum(samples))
end

"Bandwidth in GB/s (1 GB = 10^9 bytes) for `bytes` moved in `t` seconds."
gbps(bytes, t) = bytes / t / 1e9

"Throughput in MB/s (1 MB = 10^6 bytes) for `bytes` processed in `t` seconds."
mbps(bytes, t) = bytes / t / 1e6

f0(x) = @sprintf("%.0f", x)
f1(x) = @sprintf("%.1f", x)
f2(x) = @sprintf("%.2f", x)
f3(x) = @sprintf("%.3f", x)
us(t) = f2(t * 1e6)                 # seconds -> µs, 2 decimals
ms(t) = f3(t * 1e3)                 # seconds -> ms, 3 decimals
"Thousands separator for integers: 1234567 -> 1,234,567."
function commas(n::Integer)
    s = string(abs(n))
    out = IOBuffer()
    for (k, c) in enumerate(s)
        k > 1 && (length(s) - k + 1) % 3 == 0 && print(out, ',')
        print(out, c)
    end
    return (n < 0 ? "-" : "") * String(take!(out))
end

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

const SM_COUNT = Ref(0)
"Number of streaming multiprocessors (queried once; falls back to 32 if unknown)."
function sm_count()
    SM_COUNT[] == 0 && (SM_COUNT[] = something(device_attr(:MULTIPROCESSOR_COUNT), 32))
    return SM_COUNT[]
end

"Maximum threads resident on one SM (falls back to 1024 if unknown)."
max_threads_per_sm() = something(device_attr(:MAX_THREADS_PER_MULTIPROCESSOR), 1024)

"""
Blocks of `threads` threads that can be resident on one SM at the same time,
from the thread limit alone (registers and shared memory can lower it; the
compiled kernel's `CUDA.active_blocks` gives the exact figure).  This is not
the grid size: a grid may hold many more blocks, which then wait in a queue.
"""
resident_blocks_per_sm(threads) = max_threads_per_sm() ÷ threads

"Theoretical DRAM bandwidth in GB/s from memory clock and bus width, or `nothing`."
function theoretical_bandwidth()
    clk = device_attr(:MEMORY_CLOCK_RATE)          # kHz
    bus = device_attr(:GLOBAL_MEMORY_BUS_WIDTH)    # bits
    (clk === nothing || bus === nothing || clk == 0 || bus == 0) && return nothing
    return 2 * clk * 1e3 * (bus / 8) / 1e9         # double data rate
end

"""
Theoretical integer (INT32) throughput in operations/s: CUDA cores × clock.
Each CUDA core issues one 32-bit integer add/logic operation per cycle; on
Turing (7.5) the INT32 units are separate from the FP32 units and the count
equals the FP32 lane count (64 per SM).  Used for the integer "roofline" of
the match kernel.
"""
function theoretical_int_ops()
    cc    = CUDA.capability(CUDA.device())
    lanes = get(INT32_LANES_PER_SM, (Int(cc.major), Int(cc.minor)), nothing)
    sms   = device_attr(:MULTIPROCESSOR_COUNT)
    clk   = device_attr(:CLOCK_RATE)                # kHz
    (lanes === nothing || sms === nothing || clk === nothing || clk == 0) && return nothing
    return lanes * sms * clk * 1e3
end

# INT32 lanes per SM by compute capability (CUDA C Programming Guide,
# "Arithmetic Instructions" throughput table: 32-bit integer add/logical).
const INT32_LANES_PER_SM = Dict(
    (5, 0) => 128, (5, 2) => 128, (5, 3) => 128,
    (6, 0) => 64,  (6, 1) => 128, (6, 2) => 128,
    (7, 0) => 64,  (7, 2) => 64,  (7, 5) => 64,
    (8, 0) => 64,  (8, 6) => 64,  (8, 7) => 64,  (8, 9) => 64,
    (9, 0) => 64,  (10, 0) => 64, (10, 1) => 64, (10, 3) => 64,
    (11, 0) => 64, (12, 0) => 64, (12, 1) => 64,
)

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
    sms === nothing || push!(lines, "- Streaming multiprocessors: $sms, up to $(max_threads_per_sm()) resident threads each")
    try
        push!(lines, "- Device memory: $(f2(CUDA.totalmem(dev) / 2^30)) GiB")
    catch
    end
    bw = theoretical_bandwidth()
    bw === nothing || push!(lines, "- Theoretical DRAM bandwidth: $(f1(bw)) GB/s")
    io = theoretical_int_ops()
    io === nothing || push!(lines, "- Theoretical INT32 throughput: $(f2(io / 1e12)) × 10¹² ops/s")
    for (label, getter) in (("CUDA driver", CUDA.driver_version),
                            ("CUDA runtime", CUDA.runtime_version))
        try
            push!(lines, "- $label: $(getter())")
        catch
        end
    end
    push!(lines, "- Julia: $(VERSION), CUDA.jl: $(pkgversion(CUDA))")
    push!(lines, "- Host CPU: $(strip(Sys.cpu_info()[1].model)) ($(Sys.CPU_THREADS) threads); Julia threads: $(Threads.nthreads())")
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
run refreshes only its own part of a shared results file.
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
    Student: $STUDENT_NAME ($STUDENT_CARD), research project, topic 10 (log indicator matching); generator seed $SEED.
    Device: $(CUDA.name(CUDA.device())) (compute capability $(CUDA.capability(CUDA.device()))).
    Timing: one warm-up launch + `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
    (CUDA events, GPU time) over $REPS launches; tables give the mean, and min–max where the
    variation matters.  Every step is timed directly; no figure is a difference of two timings.
    CPU times are wall-clock `@elapsed` of CPU code, best of 3 after a warm-up.
    """
end

"Record the device block in README.md (every run does this, so it stays current)."
record_device_info() = update_section!(README_FILE, "device", device_info_md())
