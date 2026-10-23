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

# Project 1, exercise 4: sliding-window Shannon entropy scanner.
# Both accepted routes are implemented: the basic route (per-window histogram
# kernel + GPU array operations) and the fused route (histogram + tree
# reduction of -p log2 p inside one kernel).
include("p1_common.jl")

ENV["GKSwstype"] = "100"          # headless GR backend for Plots
using Plots

const W          = 4096           # window size in bytes
const NBINS      = 256            # one thread per bin
const PER_THREAD = W ÷ NBINS      # every thread counts 16 bytes of its window

# Windows do not overlap: window j covers bytes (j-1)·W+1 … j·W.  If the input
# length is not a multiple of W, the last window is partial and its
# probabilities are normalised by its real length.

# ---------------------------------------------------------------------------
# Kernels
# ---------------------------------------------------------------------------

# Basic route.  One block of 256 threads per window builds the window's
# 256-bin histogram in shared memory and writes it to column j of the
# 256 × windows count matrix.  In step k thread t reads byte k·256 + t of the
# window, so each step is one coalesced 256-byte row; shared-memory atomics are
# needed because several threads can see the same byte value.  Each thread then
# copies out the bin it owns, which also makes the write coalesced.
function window_hist!(counts, data)
    j    = blockIdx().x                       # window index
    t    = threadIdx().x                      # bin owned by this thread (byte value t-1)
    hist = CuStaticSharedArray(UInt32, NBINS)
    @inbounds hist[t] = UInt32(0)
    sync_threads()

    base = (j - 1) * W                        # bytes before this window
    n    = length(data)
    for k in 0:(PER_THREAD - 1)
        idx = base + k * NBINS + t
        if idx <= n                           # the last window may be partial
            @inbounds b = data[idx]
            CUDA.@atomic hist[b + 1] += UInt32(1)
        end
    end
    sync_threads()

    @inbounds counts[t, j] = hist[t]
    return nothing
end

# Fused route.  The same per-window histogram, then thread t turns its own bin
# into -p log2 p (0 for an empty bin) and the block sums the 256 terms with a
# shared-memory tree reduction (128, 64, …, 1 active threads, a barrier after
# each level), so the count matrix never goes to global memory and only one
# Float32 per window is written.  Thread 1 writes H_j.
function entropy_fused!(H, data)
    j    = blockIdx().x
    t    = threadIdx().x
    hist = CuStaticSharedArray(UInt32, NBINS)
    term = CuStaticSharedArray(Float32, NBINS)
    @inbounds hist[t] = UInt32(0)
    sync_threads()

    base = (j - 1) * W
    n    = length(data)
    for k in 0:(PER_THREAD - 1)
        idx = base + k * NBINS + t
        if idx <= n
            @inbounds b = data[idx]
            CUDA.@atomic hist[b + 1] += UInt32(1)
        end
    end
    sync_threads()

    wlen = min(W, n - base)                   # bytes in this window
    @inbounds c = hist[t]
    p = Float32(c) / Float32(wlen)
    @inbounds term[t] = c > 0 ? -p * log2(p) : 0.0f0
    sync_threads()

    s = NBINS ÷ 2
    while s > 0
        if t <= s
            @inbounds term[t] += term[t + s]
        end
        sync_threads()
        s ÷= 2
    end

    if t == 1
        @inbounds H[j] = term[1]
    end
    return nothing
end

# ---------------------------------------------------------------------------
# Host code
# ---------------------------------------------------------------------------

nwindows(n) = cld(n, W)
window_lengths(n) = Float32[min(W, n - (j - 1) * W) for j in 1:nwindows(n)]

"""
Basic route, entropy step: p = c / window length, then -p log2 p with empty bins
set to 0, then a column sum, all as GPU array operations on the count matrix.
"""
function entropy_from_counts(counts, wlens)
    P = Float32.(counts) ./ reshape(wlens, 1, :)
    T = @. ifelse(P > 0.0f0, -P * log2(P), 0.0f0)
    return vec(sum(T; dims = 1))
end

"Basic route: returns (H, counts) for a CuVector{UInt8}."
function scan_basic(data_d)
    nwin   = nwindows(length(data_d))
    counts = CUDA.zeros(UInt32, NBINS, nwin)
    nwin == 0 && return CUDA.zeros(Float32, 0), counts
    @cuda threads=NBINS blocks=nwin window_hist!(counts, data_d)
    return entropy_from_counts(counts, CuArray(window_lengths(length(data_d)))), counts
end

"Fused route: returns H for a CuVector{UInt8}."
function scan_fused(data_d)
    nwin = nwindows(length(data_d))
    H    = CUDA.zeros(Float32, nwin)
    nwin == 0 && return H
    @cuda threads=NBINS blocks=nwin entropy_fused!(H, data_d)
    return H
end

"CPU reference: 256 × windows count matrix."
function counts_cpu(data)
    n = length(data)
    C = zeros(UInt32, NBINS, nwindows(n))
    @inbounds for i in 1:n
        C[data[i] + 1, (i - 1) ÷ W + 1] += 1
    end
    return C
end

"CPU reference entropy (Float64), one value per window."
function entropy_cpu(data)
    n = length(data)
    H = zeros(Float64, nwindows(n))
    c = zeros(Int, NBINS)
    for j in eachindex(H)
        lo, hi = (j - 1) * W + 1, min(j * W, n)
        fill!(c, 0)
        @inbounds for i in lo:hi
            c[data[i] + 1] += 1
        end
        len = hi - lo + 1
        h = 0.0
        for k in 1:NBINS
            if c[k] > 0
                p = c[k] / len
                h -= p * log2(p)
            end
        end
        H[j] = h
    end
    return H
end

"Run both routes on `data` and compare with the CPU; returns the fused H on the host."
function check_scanner(data, label)
    data_d = CuArray(data)
    H_ref  = entropy_cpu(data)
    H_basic, counts = scan_basic(data_d)
    H_fused = scan_fused(data_d)
    CUDA.synchronize()
    require(Array(counts) == counts_cpu(data), "basic route counts, $label")
    require(allclose(Array(H_basic), H_ref; rtol = 0, atol = 1e-4), "basic route entropy, $label")
    require(allclose(Array(H_fused), H_ref; rtol = 0, atol = 1e-4), "fused route entropy, $label")
    return Array(H_fused)
end

# --- Test file with a known high-entropy section (from the brief) ----------
Random.seed!(SEED)
low  = rand(UInt8('a'):UInt8('z'), 512 * 1024)        # ~4.7 bits/byte
high = rand(UInt8, 256 * 1024)                        # ~8.0 bits/byte
mid  = rand(UInt8('a'):UInt8('z'), 512 * 1024)
const TESTFILE = joinpath(PROJECT_ROOT, "testfile.bin")
write(TESTFILE, vcat(low, high, mid))

testdata = read(TESTFILE)                             # the scanner reads the file back
const HIGH_WINDOWS = (length(low) ÷ W + 1):((length(low) + length(high)) ÷ W)   # ground truth
const THRESHOLD    = 6.5                              # bits/byte, between 4.7 and 8.0
println("testfile.bin: $(length(testdata)) bytes, $(nwindows(length(testdata))) windows, " *
        "high-entropy windows $(first(HIGH_WINDOWS))-$(last(HIGH_WINDOWS))")

H = check_scanner(testdata, "testfile.bin")
detected = findall(>(THRESHOLD), H)
require(detected == collect(HIGH_WINDOWS),
        "high-entropy windows detected = $(isempty(detected) ? "none" : extrema(detected)), expected $HIGH_WINDOWS")
mean_of(r) = sum(H[r]) / length(r)
println("  mean H: low $(f3(mean_of(1:first(HIGH_WINDOWS)-1))), " *
        "high $(f3(mean_of(HIGH_WINDOWS))), mid $(f3(mean_of(last(HIGH_WINDOWS)+1:length(H)))) bits/byte")
println("  windows above $THRESHOLD bits/byte: $(first(detected))-$(last(detected)) (matches the known section)")

# --- Known-answer windows from the step-by-step guide (exact values) -------
for (bytes, h) in ((UInt8[0, 0, 0, 0], 0.0), (UInt8[0, 1, 0, 1], 1.0),
                   (collect(0x00:0xff), 8.0), (zeros(UInt8, 5), 0.0))
    H_known = check_scanner(bytes, "known answer, $(length(bytes)) bytes")
    require(abs(H_known[1] - h) <= 1e-4, "known-answer entropy: got $(H_known[1]), expected $h")
end
println("Known-answer windows passed: H = 0, 1, 8 bits/byte")

# --- Boundary tests ---------------------------------------------------------
# N is read both as a number of windows (N·W bytes) and as a number of bytes
# (one partial window), so the bounds check in the counting loop is exercised.
const BOUNDARY_N = (1, 31, 32, 33, 255, 256, 257)
for n in BOUNDARY_N
    check_scanner(rand(UInt8, n * W), "$n windows")
    check_scanner(rand(UInt8, n), "$n bytes")
end
check_scanner(rand(UInt8, 3W + 5), "3 windows + 5 bytes")
check_scanner(zeros(UInt8, 2W), "constant bytes (H = 0)")
println("Boundary tests passed: N ∈ $(BOUNDARY_N) as windows and as bytes")
println("Correct!")

# --- Plot ---------------------------------------------------------------------
mkpath(RESULTS_DIR)
const PLOT_FILE = joinpath(RESULTS_DIR, "entropy_plot.png")
let j = 1:length(H)
    plt = plot(j, H; label = "H_j, GPU (fused kernel)", lw = 1.5, marker = :circle, ms = 2,
               xlabel = "window index j (W = 4096 bytes)", ylabel = "H_j (bits per byte)",
               ylims = (0, 8.6), legend = :bottomright, size = (1000, 480), dpi = 120,
               title = "Shannon entropy of testfile.bin: $STUDENT_NAME ($STUDENT_CARD)",
               titlefontsize = 11, left_margin = 5 * Plots.mm, bottom_margin = 5 * Plots.mm)
    vspan!(plt, [first(HIGH_WINDOWS) - 0.5, last(HIGH_WINDOWS) + 0.5]; alpha = 0.15, color = :red,
           label = "known high-entropy section (bytes 512 KiB - 768 KiB)")
    hline!(plt, [8.0]; ls = :dash, color = :gray, label = "8 bits/byte (uniform random bytes)")
    hline!(plt, [log2(26)]; ls = :dot, color = :gray, label = "log2(26) = 4.70 (letters a-z)")
    hline!(plt, [THRESHOLD]; ls = :dashdot, color = :black, lw = 0.8, label = "detection threshold $THRESHOLD")
    savefig(plt, PLOT_FILE)
end
println("Plot written to $PLOT_FILE")

# ---------------------------------------------------------------------------
# Benchmark and performance analysis
# ---------------------------------------------------------------------------

# Operation count per window in the fused kernel: per bin one division and one
# multiply (the sign is free), then 255 additions in the reduction.  The 256
# log2 evaluations are counted separately: a log2 is a multi-instruction
# special-function evaluation, not one FLOP.
const FLOPS_PER_WINDOW = 2 * NBINS + (NBINS - 1)
const LOG2_PER_WINDOW  = NBINS
# DRAM bytes per window in the fused kernel: the window is read once, H_j written once.
const BYTES_PER_WINDOW = W + sizeof(Float32)

"Timings of both routes on `data_d` (a CuVector{UInt8} whose length is a multiple of W)."
function bench_routes(data_d)
    n      = length(data_d)
    nwin   = nwindows(n)
    counts = CUDA.zeros(UInt32, NBINS, nwin)
    Hd     = CUDA.zeros(Float32, nwin)
    wlens  = CuArray(window_lengths(n))
    t_hist  = time_kernel(() -> @cuda threads=NBINS blocks=nwin window_hist!(counts, data_d))
    t_basic = time_kernel(() -> begin
        @cuda threads=NBINS blocks=nwin window_hist!(counts, data_d)
        entropy_from_counts(counts, wlens)
    end)
    t_fused = time_kernel(() -> @cuda threads=NBINS blocks=nwin entropy_fused!(Hd, data_d))
    return (; n, nwin, t_hist, t_basic, t_fused)
end

"Registers, memory use and occupancy of a compiled kernel (missing entries are skipped)."
function kernel_resources(kernel)
    r = Dict{Symbol,Any}()
    try r[:registers] = CUDA.registers(kernel) catch end
    try
        mem = CUDA.memory(kernel)
        r[:shared] = mem.shared
        r[:local]  = mem[:local]
    catch
    end
    try r[:occupancy] = CUDA.occupancy(kernel.fun, NBINS) catch end
    try r[:blocks_per_sm] = CUDA.active_blocks(kernel.fun, NBINS) catch end
    return r
end

fmt_opt(x, f = f1) = x === nothing ? "n/a" : f(x)
pct(x) = @sprintf("%.0f %%", 100x)

function write_analysis(m)
    bw_ref, bw_ref_name = m.theo_bw === nothing ? (m.copy_bw, "measured copy bandwidth") :
                                                   (m.theo_bw, "theoretical DRAM bandwidth")
    ridge      = m.peak_gflops === nothing ? nothing : m.peak_gflops / bw_ref
    attainable = m.peak_gflops === nothing ? m.oi * bw_ref : min(m.peak_gflops, m.oi * bw_ref)
    frac_copy  = m.bw_fused / m.copy_bw
    occ        = get(m.res_fused, :occupancy, nothing)
    regs       = get(m.res_fused, :registers, nothing)
    shmem      = get(m.res_fused, :shared, nothing)
    lmem       = get(m.res_fused, :local, nothing)
    bps        = get(m.res_fused, :blocks_per_sm, nothing)
    r_zero     = m.t_zero / m.t_uniform
    r_letters  = m.t_letters / m.t_uniform
    amdahl(f, s) = 1 / ((1 - f) + f / s)
    f_cont     = max(0.0, 1 - m.t_uniform / m.t_fused_big)   # contended share of the mix run time
    f_zero     = max(0.0, 1 - m.t_uniform / m.t_zero)

    ridge_txt = ridge === nothing ? "not available (the FP32 peak of this device is unknown)" :
        "**$(f1(ridge)) FLOP/byte** ($(f1(m.peak_gflops)) GFLOP/s FP32 peak / $(f1(bw_ref)) GB/s $(bw_ref_name))"
    left_txt  = ridge === nothing ? "far" : "about $(round(Int, ridge / m.oi))×"
    theo_txt  = m.theo_bw === nothing ? "" :
        " and $(pct(m.bw_fused / m.theo_bw)) of the theoretical $(f1(m.theo_bw)) GB/s"
    roofline = """
    Operation-count convention: per window the fused kernel performs 256 divisions, 256
    multiplications and 255 additions, i.e. $(FLOPS_PER_WINDOW) FLOPs, plus $(LOG2_PER_WINDOW) base-2
    logarithms counted separately (a logarithm costs far more than an addition).  Byte convention:
    useful global bytes, not measured DRAM traffic: each 4096-byte window is read once and one
    Float32 is written, $(BYTES_PER_WINDOW) bytes per window.  The operational intensity is therefore
    **$(f3(m.oi)) FLOP/byte** (plus $(f3(LOG2_PER_WINDOW / BYTES_PER_WINDOW)) log2/byte).  The basic route does the
    same arithmetic but also writes the 256 × windows count matrix (1 KB per 4 KB window) and reads it
    back in the array operations, so its intensity is lower still.  On this GPU the ridge point is
    $ridge_txt, so the scanner sits $left_txt to the left of
    the ridge, deep in the **memory-bound** region: the roofline caps it at
    $(f3(m.oi)) FLOP/B × $(f1(bw_ref)) GB/s = $(f1(attainable)) GFLOP/s, i.e. at streaming the input at
    full DRAM bandwidth.  Measured: on the $(f1(m.big_bytes / 1e6)) MB input the fused kernel takes
    $(ms(m.t_fused_big)) ms, which is $(f1(m.bw_fused)) GB/s of DRAM traffic and $(f1(m.gflops_fused)) GFLOP/s,
    i.e. **$(pct(frac_copy)) of the measured device-to-device copy bandwidth ($(f1(m.copy_bw)) GB/s)**$theo_txt.
    The roofline does not model atomic contention or special-function (log2) throughput, so it is
    an upper bound here, not a prediction.
    """

    count_matrix_cost = m.t_basic_big - m.t_hist_big
    evidence = """
    Observed on this GPU (Nsight Compute counters were not collected, so the limiter named above is
    an inference from these observations, not a profiler measurement):
    - `CUDA.registers`: $(fmt_opt(regs, string)) registers per thread (fused), $(fmt_opt(get(m.res_basic, :registers, nothing), string)) (basic kernel);
      shared memory $(fmt_opt(shmem, string)) bytes per block, local memory (spills) $(fmt_opt(lmem, string)) bytes.
    - Occupancy (`CUDA.occupancy`, 256 threads per block): $(occ === nothing ? "n/a" : pct(occ))$(bps === nothing ? "" : ", $(bps) resident blocks per SM").
    - Achieved bandwidth: $(f1(m.bw_fused)) GB/s = $(pct(frac_copy)) of copy bandwidth.
    - Generated code (`CUDA.@device_code_ptx`): the counting loop is fully unrolled into 16
      single-byte global loads and 16 `atom.acq_rel.gpu.shared.add.u32` per thread, i.e. one
      shared-memory atomic per input byte, and CUDA.jl's `@atomic` always uses acquire-release
      ordering (CUDA C's `atomicAdd` is relaxed).
    - Content dependence (fused kernel, same $(f1(m.big_bytes / 1e6)) MB size): all-0x00 bytes $(ms(m.t_zero)) ms,
      letters a-z $(ms(m.t_letters)) ms, uniform random bytes $(ms(m.t_uniform)) ms, test-file mix $(ms(m.t_fused_big)) ms;
      all-0x00 is $(f2(r_zero))× and letters $(f2(r_letters))× the uniform time.
    - Basic route on the same input: counting kernel alone $(ms(m.t_hist_big)) ms, whole scan (kernel +
      array step) $(ms(m.t_basic_big)) ms, so writing the count matrix and reading it back costs
      $(ms(count_matrix_cost)) ms ($(pct(count_matrix_cost / m.t_basic_big)) of the basic scan); the fused kernel, which
      removes that step, takes $(ms(m.t_fused_big)) ms.
    - Divergence is ruled out as the limiter: the only data-dependent branches are the bounds
      check (false only in a partial last window), the `c > 0` test on one value per thread and
      the reduction's `t <= s`, which is warp-uniform for s ≥ 32; the work per thread is identical.
    """

    if frac_copy >= 0.7
        limiter = """
        **The limiter is memory access, i.e. DRAM bandwidth, and the access pattern is already
        efficient.**  The kernel reaches $(pct(frac_copy)) of what a pure copy achieves on the
        test-file mix and its loads are fully coalesced (each warp reads 32 consecutive bytes per
        step), so neither the shared-memory atomics nor the arithmetic are what bounds it there.
        $(r_zero >= 1.3 ? "Only on degenerate input does contention take over: on all-0x00 bytes, where all 256 threads of a block update one bin, it is $(f2(r_zero))× slower than on uniform bytes." :
                          "The time also changes only by a factor $(f2(r_zero)) between the most and least contended inputs (all-0x00 against uniform bytes).")
        """
        optimisation = """
        **Overlap the host-to-device transfer with the scan (CUDA streams, pinned memory).**  The
        kernel already runs near the bandwidth roof, so the remaining cost in a real scan is the
        PCIe copy: measured pageable `copyto!` runs at $(f1(m.h2d_bw)) GB/s, so for this input the copy
        takes $(ms(m.t_h2d)) ms against $(ms(m.t_fused_big)) ms of kernel time.  Splitting the input into
        chunks on several streams lets chunk k+1 transfer while chunk k is scanned, so the end-to-end
        time drops from t_copy + t_kernel = $(ms(m.t_h2d + m.t_fused_big)) ms towards
        max(t_copy, t_kernel) = $(ms(max(m.t_h2d, m.t_fused_big))) ms, an expected **$(f2((m.t_h2d + m.t_fused_big) / max(m.t_h2d, m.t_fused_big)))×**
        end-to-end speedup (more if pinned memory also raises the copy rate).  The estimate is based
        on the two measured times above.
        """
    elseif r_zero >= 1.3
        limiter = """
        **The limiter is instruction throughput of the shared-memory atomics, serialised on
        contended bins.**  The kernel reaches only $(pct(frac_copy)) of copy bandwidth although its
        loads are coalesced and its intensity puts it on the memory roof, and its run time depends
        on the *content* of the data, which a bandwidth-bound kernel's would not: when all 256
        threads of a block hit one bin (all-0x00 input) it is $(f2(r_zero))× slower than on uniform
        bytes, and with only 26 distinct values (letters) $(f2(r_letters))× slower.  Atomic updates of
        the same shared-memory word are executed one after another, so for low-entropy windows the
        atomic unit, not DRAM, sets the pace.  Occupancy ($(occ === nothing ? "n/a" : pct(occ))) is not the
        problem: there are enough resident warps, they are just waiting on each other's atomics.
        """
        optimisation = """
        **Per-warp sub-histograms.**  Give each of the 8 warps of a block its own 256-bin copy in
        shared memory (8 × 256 × 4 B = 8 KiB per block, still far below the shared-memory limit),
        and add the 8 copies together before computing -p log2 p.  A hot bin is then contended by
        32 threads instead of 256, and threads of different warps never collide.  Estimate: on the
        test-file mix the time in excess of the uncontended (uniform-data) time is attributed to
        contention, f = 1 − $(ms(m.t_uniform)) / $(ms(m.t_fused_big)) = $(f2(f_cont)) of the run time; if that
        part becomes s = 8 times faster (8× fewer threads per copy of a hot bin), the overall
        speedup is 1 / ((1 − f) + f / s) = **$(f2(amdahl(f_cont, 8)))×** on the mix, and
        $(f2(amdahl(f_zero, 8)))× on constant data (f = $(f2(f_zero))).  Both f values come from the measured
        content dependence above; the cost of zeroing and merging the copies (8 extra shared writes
        and 8 reads per thread against 16 atomics, uncontended and bank-conflict-free) is not
        included, so these are upper bounds.
        """
    else
        limiter = if occ !== nothing && occ < 0.5
            """
            **The limiter is occupancy.**  Only $(pct(occ)) of the SM's warp slots can be filled
            ($(fmt_opt(regs, string)) registers per thread, $(fmt_opt(shmem, string)) bytes of shared memory
            per block), so there are too few warps in flight to hide the DRAM latency: the kernel
            reaches only $(pct(frac_copy)) of copy bandwidth while its run time barely depends on the
            data ($(f2(r_zero))× between all-0x00 and uniform bytes), which excludes atomic contention.
            """
        else
            """
            **The limiter is instruction throughput / memory-level parallelism.**  The kernel reaches
            only $(pct(frac_copy)) of copy bandwidth, yet occupancy is adequate ($(occ === nothing ? "n/a" : pct(occ)))
            and the time barely depends on the data ($(f2(r_zero))× between all-0x00 and uniform
            bytes), which excludes atomic contention.  What remains is the instruction mix: every
            input byte costs one 1-byte load, one shared-memory atomic and the index arithmetic, and
            a warp's load fetches only 32 bytes, so the SMs issue many instructions per byte and keep
            few bytes in flight; each block also does only 16 loop iterations before it pays for
            barriers, the reduction and its own launch.
            """
        end
        optimisation = """
        **Vectorised loads: read 4 bytes per load (`UInt32`) and unpack them in registers.**  Each
        thread would issue 4 loads of 4 bytes instead of 16 loads of 1 byte, so a warp request moves
        128 bytes instead of 32 and the load instruction count drops 4×, with the same number of
        shared atomics.  Estimate: per input byte the kernel issues one load and one shared atomic, so
        assume loads are a fraction f = 0.5 of the issued work (an assumption: no profiler counter was
        collected); making that part s = 4 times cheaper gives 1 / ((1 − f) + f / s) =
        **$(f2(min(amdahl(0.5, 4), m.copy_bw / m.bw_fused)))×**, which may not exceed the measured headroom to a coalesced copy,
        $(f1(m.copy_bw)) / $(f1(m.bw_fused)) GB/s = $(f2(m.copy_bw / m.bw_fused))×.
        """
    end

    tb = 1e12
    duration(s) = s < 120 ? "$(f1(s)) s" : s < 7200 ? "$(f1(s / 60)) min" : "$(f1(s / 3600)) h"
    kernel_bps = m.big_bytes / m.t_fused_big
    e2e_bps    = m.big_bytes / (m.t_h2d + m.t_fused_big)
    h2d_bps    = m.h2d_bw * 1e9
    io_point = if kernel_bps > h2d_bps
        """
        - **The GPU is not the bottleneck; data movement is.**  The kernel ($(f1(kernel_bps / 1e9)) GB/s)
          is faster than the host-to-device copy ($(f1(m.h2d_bw)) GB/s) and than typical storage (a fast
          NVMe SSD reads a few GB/s, a network share or HDD far less), so a GPU entropy scan can run
          *inline* with acquisition or ingestion instead of as a separate pass, and the effort should
          go into overlapping transfer and compute rather than into the kernel.
        """
    else
        """
        - **On this GPU the kernel is the slowest stage.**  It scans at $(f1(kernel_bps / 1e9)) GB/s, below
          the host-to-device copy ($(f1(m.h2d_bw)) GB/s), so optimising the kernel (section 3) pays off
          directly in end-to-end triage time; it is still far faster than the CPU reference.
        """
    end
    batch_point = if m.mbps_tf < 0.5 * kernel_bps / 1e6
        """
        - **Batch small files.**  A single 1.25 MiB file (320 windows) takes $(us(m.t_fused_tf)) µs, only
          $(f1(m.mbps_tf)) MB/s ($(pct(m.mbps_tf / (kernel_bps / 1e6))) of the large-input rate), because 320
          blocks cannot fill the GPU and the fixed launch cost dominates.  Triaging a file system file
          by file would waste most of the GPU; files should be packed into large buffers and scanned
          with one launch.
        """
    else
        """
        - **Small files are cheap too.**  A single 1.25 MiB file (320 windows) takes $(us(m.t_fused_tf)) µs
          ($(f1(m.mbps_tf)) MB/s, $(pct(m.mbps_tf / (kernel_bps / 1e6))) of the large-input rate), so on this GPU
          even per-file launches keep most of the throughput.
        """
    end
    security = """
    The scanner is a triage tool, so what matters is how fast it can answer *where in this data
    is something encrypted, compressed or packed?*  Measured on this GPU, the fused kernel scans
    at **$(f1(kernel_bps / 1e6)) MB/s** on a $(f1(m.big_bytes / 1e6)) MB input, versus **$(f1(m.cpu_mbps)) MB/s**
    for the single-threaded CPU reference ($(f1(kernel_bps / 1e6 / m.cpu_mbps))× faster); including the
    pageable host-to-device copy ($(f1(m.h2d_bw)) GB/s) the end-to-end rate is $(f1(e2e_bps / 1e6)) MB/s.
    At these measured rates a 1 TB disk image would take approximately $(duration(tb / kernel_bps)) of kernel
    time, $(duration(tb / e2e_bps)) including the host-to-device copy, and $(duration(tb / (m.cpu_mbps * 1e6))) on one CPU
    core, in each case excluding reading the image from storage.  Consequences for practice:

    $(rstrip(io_point))
    $(rstrip(batch_point))
    - **Resolution and statistics.**  With W = 4096 (one page) the scanner localises a
      high-entropy region to 4 KiB, as the plot shows (windows $(first(HIGH_WINDOWS))-$(last(HIGH_WINDOWS))
      above $(THRESHOLD) bits/byte), but 4096 samples of 256 symbols bias the estimate down by
      about 0.05 bits, so random data reads ≈ 7.95 rather than 8.0 and thresholds must allow for it.
    - **The same scan checks encryption.**  Correct ciphertext is indistinguishable from random
      bytes, so every window of an encrypted volume or of the output of a GPU encryption kernel
      should read ≈ 7.95 bits/byte at W = 4096; a run of low-entropy windows inside it points to
      unencrypted sectors, padding, or a broken cipher mode (e.g. ECB on repetitive data), which
      is a vulnerability the scan finds without decrypting anything.
    - **Entropy is a signal, not a verdict.**  High entropy flags encrypted containers, ransomware
      output, packed or encrypted malware sections and exfiltration archives, but also every
      ordinary JPEG, ZIP or video, so it ranks data for deeper analysis rather than detecting
      malice; and an adversary can lower it deliberately (Base64 encoding caps it at 6
      bits/byte, padding with low-entropy bytes dilutes a window).  A high-entropy region still
      needs closer inspection: identifying its format (archive, media, encrypted container),
      trying to decompress it, signature or YARA scanning, or disassembly.  Fast scanning
      matters because it lets an analyst apply this cheap signal to *all* the data and reserve
      the expensive tools for the flagged regions.
    """

    resources_table = md_table(
        ["kernel", "registers / thread", "shared memory / block (B)", "local memory (B)", "occupancy", "resident blocks / SM"],
        [(name, fmt_opt(get(res, :registers, nothing), string), fmt_opt(get(res, :shared, nothing), string),
          fmt_opt(get(res, :local, nothing), string),
          get(res, :occupancy, nothing) === nothing ? "n/a" : pct(res[:occupancy]),
          fmt_opt(get(res, :blocks_per_sm, nothing), string))
         for (name, res) in (("window_hist! (basic)", m.res_basic), ("entropy_fused!", m.res_fused))])

    text = """
    # Exercise 4: performance analysis of the entropy scanner

    $(run_info_md())
    All numbers below are measured by `src/p1_ex4.jl` on this device and inserted when the script
    runs; the timing tables are in `benchmarks.md` (Exercise 4).

    ## 1. Roofline placement

    $roofline
    ## 2. The limiter

    $limiter
    $evidence
    $resources_table
    ## 3. One further optimisation (not implemented)

    $optimisation
    ## 4. Security relevance: what the throughput means for triage

    $security"""
    write(joinpath(RESULTS_DIR, "analysis.md"), text)
    return nothing
end

if !QUICK
    record_device_info()

    # Large input: the test file repeated N ÷ 16 times, so it has the same mix of
    # low- and high-entropy windows but enough blocks to fill the GPU.
    nrep    = max(1, N ÷ 16)
    big     = repeat(testdata, nrep)
    big_d   = CuArray(big)
    tf_d    = CuArray(testdata)
    println("\nBenchmark: testfile.bin ($(length(testdata)) B) and the test file repeated $nrep times ($(length(big)) B)")
    b_tf  = bench_routes(tf_d)
    b_big = bench_routes(big_d)

    # Same-size inputs with different contents: how much do shared-atomic collisions cost?
    tmp_d = similar(big_d)
    Hd    = CUDA.zeros(Float32, nwindows(length(big)))
    content_times = Dict{String,Float64}()
    for (name, gen) in (("all 0x00", n -> zeros(UInt8, n)),
                        ("letters a-z", n -> rand(UInt8('a'):UInt8('z'), n)),
                        ("uniform random", n -> rand(UInt8, n)))
        copyto!(tmp_d, gen(length(big)))
        content_times[name] = time_kernel(() -> @cuda threads=NBINS blocks=length(Hd) entropy_fused!(Hd, tmp_d))
        println("  fused kernel on $name: $(ms(content_times[name])) ms")
    end
    tmp_d = nothing

    # Host-to-device transfer of the large input (pageable host memory).
    t_h2d = time_kernel(() -> copyto!(big_d, big))

    # CPU reference throughput (single thread), best of 3 after a warm-up call.
    entropy_cpu(testdata)
    t_cpu = minimum(@elapsed(entropy_cpu(big)) for _ in 1:3)

    # Resources of the compiled kernels.
    res_basic = kernel_resources(@cuda launch=false window_hist!(CUDA.zeros(UInt32, NBINS, 1), tf_d))
    res_fused = kernel_resources(@cuda launch=false entropy_fused!(Hd, tf_d))

    copy_bw = measured_copy_bandwidth()
    theo_bw = theoretical_bandwidth()
    peak    = theoretical_fp32_gflops()

    rows = Any[]
    for (label, b) in (("testfile.bin", b_tf), ("test file × $nrep", b_big))
        push!(rows, (label, b.n, b.nwin,
                     us(b.t_hist), us(b.t_basic), f1(mbps(b.n, b.t_basic)),
                     us(b.t_fused), f1(mbps(b.n, b.t_fused)), f1(gbps(b.nwin * BYTES_PER_WINDOW, b.t_fused))))
        println("  $label: basic $(us(b.t_basic)) µs ($(f1(mbps(b.n, b.t_basic))) MB/s), " *
                "fused $(us(b.t_fused)) µs ($(f1(mbps(b.n, b.t_fused))) MB/s)")
    end
    header = ["input", "bytes", "windows", "basic: histogram kernel (µs)", "basic: kernel + array ops (µs)",
              "basic (MB/s)", "fused kernel (µs)", "fused (MB/s)", "fused DRAM bandwidth (GB/s)"]
    content_rows = [(name, ms(content_times[name]), f1(mbps(length(big), content_times[name])))
                    for name in ("all 0x00", "letters a-z", "uniform random")]
    push!(content_rows, ("test-file mix", ms(b_big.t_fused), f1(mbps(length(big), b_big.t_fused))))

    section = """
    ## Exercise 4: entropy scanner

    $(run_info_md())
    Window convention: width W = 4096 bytes, step W (adjacent, non-overlapping windows), a short
    final window is kept and normalised by its actual length m; the CPU reference uses the same
    convention.  One block of 256 threads per window, each thread counts 16 bytes.  Throughput =
    input bytes / time / 10⁶ (MB/s); every input byte is counted once (no dropped tail, no
    overlapping reads).  "Basic: kernel + array ops" is the whole basic route (count kernel, then
    `p = c / m`, `-p log2 p` and `sum(...; dims=1)` as GPU array operations) and gives the basic
    throughput; the counting kernel alone is listed too, the difference being the cost of writing
    and re-reading the count matrix (1 KB per 4 KB window).  The fused route is a single kernel.
    Inputs are already on the GPU; the host-to-device copy is listed separately.

    $(md_table(header, rows))
    **Content dependence** (fused kernel, $(length(big)) bytes, same size, different contents):

    $(md_table(["input content", "time (ms)", "throughput (MB/s)"], content_rows))
    Other measurements on the $(length(big))-byte input: host-to-device `copyto!` (pageable memory)
    $(ms(t_h2d)) ms = $(f1(gbps(length(big), t_h2d))) GB/s; single-threaded CPU reference
    $(f3(t_cpu)) s = $(f1(mbps(length(big), t_cpu))) MB/s (`@elapsed`, CPU code, best of 3).
    Device-to-device copy bandwidth: $(f1(copy_bw)) GB/s.
    """
    update_section!(BENCH_FILE, "ex4", section)

    big_bytes = length(big)
    write_analysis((;
        oi = FLOPS_PER_WINDOW / BYTES_PER_WINDOW,
        theo_bw, copy_bw, peak_gflops = peak,
        big_bytes,
        t_fused_big = b_big.t_fused, t_hist_big = b_big.t_hist, t_basic_big = b_big.t_basic,
        bw_fused = gbps(b_big.nwin * BYTES_PER_WINDOW, b_big.t_fused),
        gflops_fused = b_big.nwin * FLOPS_PER_WINDOW / b_big.t_fused / 1e9,
        t_fused_tf = b_tf.t_fused, mbps_tf = mbps(b_tf.n, b_tf.t_fused),
        t_zero = content_times["all 0x00"], t_letters = content_times["letters a-z"],
        t_uniform = content_times["uniform random"],
        t_h2d, h2d_bw = gbps(big_bytes, t_h2d),
        cpu_mbps = mbps(big_bytes, t_cpu),
        res_basic, res_fused,
    ))
    println("Results written to $BENCH_FILE and $(joinpath(RESULTS_DIR, "analysis.md"))")
end
