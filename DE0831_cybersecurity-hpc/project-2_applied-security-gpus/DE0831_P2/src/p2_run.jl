const STUDENT_CARD = "251ADM047"                               # <- student card number
const STUDENT_NAME = "Vagif Asgarli"

# Project 2, track E (log mining), full route: header block, validation
# against the generator's ground truth, benchmarks over the corpus sizes,
# results/benchmarks.md, results/analysis.md and the plots.
#
#   julia --project=. src/p2_run.jl            # everything
#   P2_QUICK=1 julia --project=. src/p2_run.jl # validation only
#   P2_MAIN=<lines>  corpus used for validation and the breakdown (default 1,000,000)
#   P2_SIZES=a,b,c   corpus sizes for the scaling study
#   P2_NO_PLOTS=1    skip the CairoMakie plots

using CUDA, Printf
include("p2_common.jl")
include("p2_data.jl")
include("p2_cpu.jl")
include("p2_gpu.jl")

const SEED   = student_seed(STUDENT_CARD)                     # the generator's derived seed
const MAIN_N = parse(Int, get(ENV, "P2_MAIN", "1000000"))
const SIZES  = corpus_sizes()
const CPU_REPS = parse(Int, get(ENV, "P2_CPU_REPS", "3"))

println("Student: $STUDENT_NAME, ID: $STUDENT_CARD")
println("Track: E (log mining), full route: one multi-pattern kernel, scan and compaction")
println("Derived parameters: generator seed = $SEED (SHA-256 of the ID), validation corpus = $(commas(MAIN_N)) lines, sizes = $(join(commas.(SIZES), ", "))")
println("Device: ", CUDA.name(CUDA.device()))
println("Compute capability: ", CUDA.capability(CUDA.device()))

# ---------------------------------------------------------------------------
# Validation on the main corpus
# ---------------------------------------------------------------------------

ensure_corpus(MAIN_N)
corpus = load_corpus(MAIN_N)
inds   = load_indicators(MAIN_N)
truth  = load_truth(MAIN_N)
etruth = load_entropy_truth(MAIN_N)
pt     = PatternTable(inds)
dp     = DevicePatterns(pt)
println("Corpus: $(commas(length(corpus))) bytes, $(commas(MAIN_N)) lines; $(length(inds)) indicators; truth: $(length(truth)) indicator lines, $(length(etruth)) payload tokens")

# CPU reference results (also the baseline later)
ls_cpu   = cpu_line_starts(corpus)
mask_cpu = cpu_match(corpus, pt, ls_cpu)
ts_cpu   = cpu_token_starts(corpus)
H_cpu, L_cpu = cpu_token_entropies(corpus, ts_cpu)

corpus_d = CuVector(corpus)
r = gpu_pipeline(corpus_d, dp)

# 1. line table
ls_gpu = Array(r.line_start)
require(ls_gpu == ls_cpu, "line table: GPU has $(length(ls_gpu) - 1) lines, CPU $(length(ls_cpu) - 1)")
require(nlines_of(ls_gpu) == MAIN_N, "line count $(nlines_of(ls_gpu)) != $MAIN_N")

# 2. match set: GPU == CPU == ground truth, for both kernel variants
mask_gpu = Array(r.line_mask)
require(mask_gpu == mask_cpu, "line masks: GPU != CPU")
mset = match_set(mask_gpu, inds)
require(mset == truth, "match set != truth: $(length(mset)) found, $(length(truth)) expected, $(length(setdiff(truth, mset))) missing, $(length(setdiff(mset, truth))) extra")
let m2 = CUDA.zeros(UInt32, MAIN_N)
    launch_match!(m2, corpus_d, dp, r.line_start; tiled = false)
    require(Array(m2) == mask_cpu, "match_global! != CPU")
end
lines = corpus_lines(corpus, ls_cpu)
mask_lib = cpu_match_occursin(lines, inds)
require(match_set(mask_lib, inds) == truth, "occursin baseline != truth")

# 3. extracted lines
matched = Array(r.matched)
require(matched == findall(!=(0), mask_cpu), "matched line numbers")
got = unpack_lines(Array(r.packed), Array(r.off), Array(r.len))
require(got == lines[matched], "extracted line text")

# 4. tokens and entropies
ts_gpu = Array(r.token_start)
require(ts_gpu == ts_cpu, "token starts: GPU $(length(ts_gpu)), CPU $(length(ts_cpu))")
H_gpu = Array(r.H); L_gpu = Array(r.L)
require(L_gpu == L_cpu, "token lengths")
hdiff = maximum(abs.(H_gpu .- Float32.(H_cpu)))
require(hdiff < 1e-4, "token entropies GPU vs CPU, max difference $hdiff")
require(sum(r.hist) == length(ts_gpu), "entropy histogram total")

# 5. flagging at the data-chosen threshold == entropy truth, and the values
truthset = Set((l, t) for (l, t, _) in etruth)
flagged_set(idx) = Set((line_of(ls_cpu, ts_gpu[k]), String(corpus[ts_gpu[k]:ts_gpu[k] + L_gpu[k] - 1])) for k in idx)
fl = flagged_set(Array(r.flagged))
require(fl == truthset, "flagged tokens at threshold $(r.threshold): $(length(fl)) flagged, $(length(truthset)) in truth")
tokidx = Dict{Tuple{Int,String},Int}((line_of(ls_cpu, ts_gpu[k]), String(corpus[ts_gpu[k]:ts_gpu[k] + L_gpu[k] - 1])) => k for k in Array(r.flagged))
hmax = maximum(abs(H_gpu[tokidx[(l, t)]] - h) for (l, t, h) in etruth)
require(hmax < 1e-3, "entropy values vs truth, max difference $hmax")
# precision / recall over a range of thresholds (reported, not required to be perfect)
thr_rows = Any[]
for thr in (3.5, 4.0, r.threshold, 4.5, 5.0, 5.5)
    fs = flagged_set(Array(gpu_flagged_tokens(r.H, thr)))
    tp = length(intersect(fs, truthset)); fp = length(fs) - tp; fn = length(truthset) - tp
    prec = tp + fp == 0 ? 1.0 : tp / (tp + fp); rec = tp / length(truthset)
    push!(thr_rows, (thr == r.threshold ? "**$(f2(thr)) (chosen)**" : f2(thr), length(fs), tp, fp, fn, f3(prec), f3(rec)))
end
bulk_max = maximum(H_gpu[k] for k in eachindex(H_gpu) if L_gpu[k] < 32; init = 0.0f0)
long_min = minimum(H_gpu[k] for k in eachindex(H_gpu) if L_gpu[k] >= 32; init = Inf32)
println("Entropy: $(commas(length(ts_gpu))) tokens; max H of tokens shorter than 32 chars = $(f3(bulk_max)); min H of the $(count(>=(32), L_gpu)) tokens of 32+ chars = $(f3(long_min)); " *
        "threshold from the histogram's empty band $(f2(r.band[1]))–$(f2(r.band[2])) bits: $(f2(r.threshold))")

# 6. hand-made small cases: boundaries of lines, words, tiles and the corpus
const SMALL_CASES = Ref(0)
function small_case(text, patterns; expect)
    SMALL_CASES[] += 1
    c = Vector{UInt8}(codeunits(text)); pt2 = PatternTable(patterns); dp2 = DevicePatterns(pt2)
    r2 = gpu_pipeline(CuVector(c), dp2; threshold = 5.0)
    ls2 = cpu_line_starts(c)
    require(Array(r2.line_start) == ls2, "small case line table: $(repr(text[1:min(end, 40)]))")
    got2 = match_set(Array(r2.line_mask), patterns)
    require(got2 == Set(expect), "small case $(repr(text[1:min(end, 40)])): got $got2, expected $expect")
    require(Array(r2.line_mask) == cpu_match(c, pt2, ls2), "small case CPU != GPU: $(repr(text[1:min(end, 40)]))")
end
small_case("", ["abc"]; expect = [])
small_case("abc", ["abc"]; expect = [(1, "abc")])                                   # one line, no newline, pattern at byte 1
small_case("x abc\nabc y\n", ["abc"]; expect = [(1, "abc"), (2, "abc")])
small_case("abcd\nxabc\nab\n", ["abc"]; expect = [])                                # inside longer words: no match
small_case("a.b\n192.0.2.24 x\n192.0.2.248\n", ["192.0.2.24", "192.0.2.248"]; expect = [(2, "192.0.2.24"), (3, "192.0.2.248")])
small_case("one two\nthree one two\n", ["one", "two"]; expect = [(1, "one"), (1, "two"), (2, "one"), (2, "two")])
small_case("x"^(MATCH_TILE - 3) * " abcdef " * "y"^20 * "\n", ["abcdef"]; expect = [(1, "abcdef")])   # crosses the tile edge
small_case("y"^(MATCH_TILE - 1) * " abcdef\n", ["abcdef"]; expect = [(1, "abcdef")])                   # starts at the tile edge
small_case("y"^(MATCH_TILE - 7) * " abcdef\n", ["abcdef"]; expect = [(1, "abcdef")])                   # ends at the tile edge
small_case("abc\n" * "z"^MATCH_TILE * " abc", ["abc"]; expect = [(1, "abc"), (2, "abc")])             # last byte of the corpus
small_case("abc\n" * "z"^MATCH_TILE * "abc", ["abc"]; expect = [(1, "abc")])                           # glued to a word: no match
println("Validation passed: line table, match set (tiled and global kernels, CPU, occursin) == truth, extraction, $(commas(length(ts_gpu))) tokens, entropies, flagging, boundary cases")
println("Correct!")

# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------

"Run the whole CPU baseline (same computation as the GPU pipeline)."
function cpu_pipeline(corpus, pt, threshold)
    ls = cpu_line_starts(corpus)
    mask = cpu_match(corpus, pt, ls)
    matched = findall(!=(0), mask)
    out = [corpus[ls[k]:ls[k + 1] - 2] for k in matched]
    ts = cpu_token_starts(corpus)
    H, L = cpu_token_entropies(corpus, ts)
    fl = flagged_tokens(corpus, ts, H, L, ls, threshold)
    return length(matched), length(fl)
end

"Resources of a compiled kernel (missing entries skipped)."
function kernel_resources(kernel, threads)
    r = Dict{Symbol,Any}()
    try r[:registers] = CUDA.registers(kernel) catch end
    try
        mem = CUDA.memory(kernel)
        r[:shared] = mem.shared; r[:local] = mem[:local]
    catch
    end
    try r[:occupancy] = CUDA.occupancy(kernel.fun, threads) catch end
    try r[:blocks_per_sm] = CUDA.active_blocks(kernel.fun, threads) catch end
    return r
end
fmt_opt(x, f = string) = x === nothing ? "n/a" : f(x)
pct(x) = @sprintf("%.0f %%", 100x)

# PTX of a kernel, produced by this script (the evidence must be reproducible
# from the submission).  The fake-CUDA emulator has no compiler, so the dump is
# empty there.
if isdefined(CUDA, Symbol("@device_code_ptx"))
    @eval function dump_ptx(launcher::Function)
        io = IOBuffer()
        CUDA.@device_code_ptx io=io launcher()
        return String(take!(io))
    end
else
    dump_ptx(launcher::Function) = ""
end
"The body of the kernel's `.entry` function (the dump also holds CUDA.jl's exception-reporting helpers)."
function kernel_body(ptx::AbstractString)
    i = findfirst(".entry", ptx); i === nothing && return ptx
    j = findnext("\n}", ptx, last(i)); j === nothing && return ptx[first(i):end]
    return ptx[first(i):last(j)]
end
"Counts of the instruction classes that matter for the limiter discussion (kernel body only)."
function ptx_counts(ptx::AbstractString)
    ptx = kernel_body(ptx)
    c(pat) = count(_ -> true, eachmatch(pat, ptx))
    return (ld_global = c(r"ld\.global"), ld_shared = c(r"ld\.shared"), st_shared = c(r"st\.shared"),
            atom = c(r"\b(atom|red)\."), bar = c(r"bar\.sync"), bra = c(r"\bbra\b"), total = c(r"^\s+[a-z@][\w.@%]*\s"m))
end

if !QUICK
    record_device_info()
    mkpath(RESULTS_DIR)
    copy_bw = measured_copy_bandwidth()
    theo_bw = theoretical_bandwidth()
    int_ops = theoretical_int_ops()
    thr = r.threshold

    # ---- per-size timings ---------------------------------------------------
    rows = Any[]                       # markdown rows
    csv  = String["lines,bytes,read_s,h2d_s,h2d_pinned_s,line_table_s,match_tiled_s,match_global_s,extract_s,token_starts_s,entropy_s,hist_s,flag_s,pipeline_s,d2h_s,cpu_line_s,cpu_match_s,cpu_occursin_s,cpu_tokens_s,cpu_entropy_s,cpu_pipeline_s"]
    breakdown = Dict{Int,Any}()
    for nl in SIZES
        ensure_corpus(nl)
        path = corpus_path(nl)
        t_read = time_cpu(() -> read(path); reps = CPU_REPS).mean
        c = read(path); n = length(c)
        println("\n[$(commas(nl)) lines, $(f1(n / 1e6)) MB]")
        cd = CuVector{UInt8}(undef, n)
        t_h2d = time_stats(() -> copyto!(cd, c)).mean
        t_h2d_pin = try
            CUDA.pin(c)
            time_stats(() -> copyto!(cd, c)).mean
        catch
            NaN
        end
        flags = CuVector{UInt32}(undef, n)
        t_lt  = time_kernel(() -> gpu_line_starts(cd, flags))
        ls_d  = gpu_line_starts(cd, flags)
        nlines = length(ls_d) - 1
        mask_d = CUDA.zeros(UInt32, nlines)
        reset = () -> fill!(mask_d, UInt32(0))
        s_mt = time_stats(() -> launch_match!(mask_d, cd, dp, ls_d; tiled = true); reset = reset)
        s_mg = time_stats(() -> launch_match!(mask_d, cd, dp, ls_d; tiled = false); reset = reset)
        reset(); launch_match!(mask_d, cd, dp, ls_d)
        t_ex  = time_kernel(() -> extract_matched_lines(cd, ls_d, mask_d))
        t_ts  = time_kernel(() -> gpu_token_starts(cd, flags, dp))
        ts_d  = gpu_token_starts(cd, flags, dp)
        t_en  = time_kernel(() -> gpu_token_entropies(cd, ts_d, dp))
        H_d, L_d = gpu_token_entropies(cd, ts_d, dp)
        t_hi  = time_kernel(() -> gpu_entropy_histogram(H_d))
        t_fl  = time_kernel(() -> gpu_flagged_tokens(H_d, thr))
        s_pipe = time_stats(() -> gpu_pipeline(cd, dp; threshold = thr); reps = min(REPS, 20))
        res = gpu_pipeline(cd, dp; threshold = thr)
        t_d2h = time_stats(() -> (Array(res.packed); Array(res.off); Array(res.len); Array(res.flagged))).mean
        # CPU baseline, same computation
        t_cl  = time_cpu(() -> cpu_line_starts(c); reps = CPU_REPS).mean
        lsc   = cpu_line_starts(c)
        t_cm  = time_cpu(() -> cpu_match(c, pt, lsc); reps = CPU_REPS).mean
        lns   = corpus_lines(c, lsc)
        t_co  = time_cpu(() -> cpu_match_occursin(lns, inds); reps = CPU_REPS).mean
        t_ct  = time_cpu(() -> cpu_token_starts(c); reps = CPU_REPS).mean
        tsc   = cpu_token_starts(c)
        t_ce  = time_cpu(() -> cpu_token_entropies(c, tsc); reps = CPU_REPS).mean
        t_cp  = time_cpu(() -> cpu_pipeline(c, pt, thr); reps = CPU_REPS).mean
        CUDA.unsafe_free!(flags); CUDA.unsafe_free!(cd)
        push!(csv, join(string.([nl, n, t_read, t_h2d, t_h2d_pin, t_lt, s_mt.mean, s_mg.mean, t_ex, t_ts, t_en, t_hi, t_fl, s_pipe.mean, t_d2h, t_cl, t_cm, t_co, t_ct, t_ce, t_cp]), ","))
        push!(rows, (commas(nl), f1(n / 1e6),
                     f2(nl / s_mt.mean / 1e6), f1(mbps(n, s_mt.mean)),
                     f2(nl / s_pipe.mean / 1e6), f1(mbps(n, s_pipe.mean)),
                     f2(nl / (s_pipe.mean + t_h2d) / 1e6), f1(mbps(n, s_pipe.mean + t_h2d)),
                     f3(nl / t_cp / 1e6), f1(mbps(n, t_cp)), f1(t_cp / s_pipe.mean), f1(t_cp / (s_pipe.mean + t_h2d))))
        breakdown[nl] = (; n, t_read, t_h2d, t_h2d_pin, t_lt, s_mt, s_mg, t_ex, t_ts, t_en, t_hi, t_fl, s_pipe, t_d2h, t_cl, t_cm, t_co, t_ct, t_ce, t_cp, nlines)
        println("  match $(ms(s_mt.mean)) ms ($(f1(mbps(n, s_mt.mean))) MB/s), pipeline $(ms(s_pipe.mean)) ms, +H2D $(ms(s_pipe.mean + t_h2d)) ms; CPU pipeline $(f3(t_cp)) s")
    end
    write(joinpath(RESULTS_DIR, "timings.csv"), join(csv, "\n") * "\n")
    write(joinpath(RESULTS_DIR, "entropy_hist.csv"), "bin_lo_bits,count\n" * join(["$(f2((k - 1) * 0.05)),$(r.hist[k])" for k in 1:HIST_BINS], "\n") * "\n")
    write(joinpath(RESULTS_DIR, "threshold_table.csv"), "threshold,flagged,tp,fp,fn,precision,recall\n" *
          join([join(string.(replace.(string.(collect(row)), "**" => "", " (chosen)" => "")), ",") for row in thr_rows], "\n") * "\n")

    # ---- integer-operation count and kernel resources at the main size ------
    counters = CUDA.zeros(UInt64, 2)
    @cuda threads=256 blocks=grid_for(length(corpus_d)) match_counts!(counters, corpus_d, dp.pat, dp.plen, dp.first_mask)
    candidates, compares = Int.(Array(counters))
    nbytes = length(corpus)
    cand_frac = candidates / nbytes
    cmp_per_byte = compares / nbytes
    # integer operations per byte of the tiled kernel: the filter (index
    # arithmetic, shared load, mask test: ~6) plus, per candidate, the loop
    # over set bits and the byte compares (~5 per compare: loads, compare,
    # branch, counter)
    int_per_byte = 6 + cmp_per_byte * 5 + cand_frac * 8
    kt = @cuda launch=false match_tiled!(r.line_mask, corpus_d, dp.pat, dp.plen, dp.first_mask, dp.is_word, r.line_start)
    kg = @cuda launch=false match_global!(r.line_mask, corpus_d, dp.pat, dp.plen, dp.first_mask, dp.is_word, r.line_start)
    ke = @cuda launch=false token_entropy!(r.H, r.L, corpus_d, r.token_start, dp.is_tok, dp.tok_symbol)
    res_t = kernel_resources(kt, MATCH_THREADS); res_g = kernel_resources(kg, 256); res_e = kernel_resources(ke, ENT_THREADS)
    ptx = dump_ptx(() -> @cuda launch=false match_tiled!(r.line_mask, corpus_d, dp.pat, dp.plen, dp.first_mask, dp.is_word, r.line_start))
    isempty(ptx) || write(joinpath(RESULTS_DIR, "match_tiled.ptx"), ptx)
    pc = ptx_counts(ptx)

    b = breakdown[MAIN_N]
    bw_tiled  = gbps(nbytes, b.s_mt.mean)            # useful bytes: the corpus read once
    bw_global = gbps(nbytes, b.s_mg.mean)
    t_bw_bound  = nbytes / ((theo_bw === nothing ? copy_bw : theo_bw) * 1e9)
    t_int_bound = int_ops === nothing ? NaN : nbytes * int_per_byte / int_ops

    # ---- benchmarks.md -----------------------------------------------------
    header = ["lines", "MB", "match kernel (M lines/s)", "match (MB/s)", "GPU pipeline (M lines/s)", "pipeline (MB/s)",
              "pipeline + H2D (M lines/s)", "+ H2D (MB/s)", "CPU pipeline (M lines/s)", "CPU (MB/s)", "speed-up (GPU)", "speed-up (GPU + H2D)"]
    bd_rows = [
        ("file read from disk (pageable host memory)", ms(b.t_read), f1(mbps(b.n, b.t_read))),
        ("host → device copy, pageable", ms(b.t_h2d), f1(gbps(b.n, b.t_h2d))),
        ("host → device copy, pinned", isnan(b.t_h2d_pin) ? "n/a" : ms(b.t_h2d_pin), isnan(b.t_h2d_pin) ? "n/a" : f1(gbps(b.n, b.t_h2d_pin))),
        ("line table: newline flags, scan, scatter", ms(b.t_lt), f1(mbps(b.n, b.t_lt))),
        ("match kernel, tiled (shared memory)", ms(b.s_mt.mean) * " (min $(ms(b.s_mt.min)), max $(ms(b.s_mt.max)))", f1(mbps(b.n, b.s_mt.mean))),
        ("match kernel, global memory variant", ms(b.s_mg.mean), f1(mbps(b.n, b.s_mg.mean))),
        ("matched lines: compaction + gather", ms(b.t_ex), ""),
        ("token starts: flags, scan, scatter", ms(b.t_ts), f1(mbps(b.n, b.t_ts))),
        ("token entropy kernel", ms(b.t_en), f1(mbps(b.n, b.t_en))),
        ("entropy histogram", ms(b.t_hi), ""),
        ("flagged tokens: compaction", ms(b.t_fl), ""),
        ("**GPU pipeline end to end (one timing)**", ms(b.s_pipe.mean) * " (min $(ms(b.s_pipe.min)), max $(ms(b.s_pipe.max)))", f1(mbps(b.n, b.s_pipe.mean))),
        ("device → host copy of the results", ms(b.t_d2h), ""),
        ("CPU: line table", ms(b.t_cl), f1(mbps(b.n, b.t_cl))),
        ("CPU: match (same algorithm)", ms(b.t_cm), f1(mbps(b.n, b.t_cm))),
        ("CPU: `occursin` per indicator (library search)", ms(b.t_co), f1(mbps(b.n, b.t_co))),
        ("CPU: token starts", ms(b.t_ct), f1(mbps(b.n, b.t_ct))),
        ("CPU: token entropies", ms(b.t_ce), f1(mbps(b.n, b.t_ce))),
        ("**CPU pipeline end to end (one timing)**", ms(b.t_cp), f1(mbps(b.n, b.t_cp))),
    ]
    res_rows = [(name, fmt_opt(get(rr, :registers, nothing)), fmt_opt(get(rr, :shared, nothing)), fmt_opt(get(rr, :local, nothing)),
                 get(rr, :occupancy, nothing) === nothing ? "n/a" : pct(rr[:occupancy]), fmt_opt(get(rr, :blocks_per_sm, nothing)))
                for (name, rr) in (("match_tiled! (256 threads)", res_t), ("match_global! (256 threads)", res_g), ("token_entropy! (256 threads)", res_e))]
    section = """
    ## Track E: log mining (full route)

    $(run_info_md())
    Validation on the $(commas(MAIN_N))-line corpus: line table equal to the CPU's; the match set of
    the tiled kernel, of the global-memory kernel, of the CPU baseline and of the `occursin` baseline
    all equal `truth_$(STUDENT_CARD).csv` ($(length(truth)) lines); extracted line text equal to the
    corpus lines; $(commas(length(ts_gpu))) tokens with entropies equal to the CPU's (max difference
    $(@sprintf("%.1e", hdiff))) and to `entropy_truth` for the $(length(etruth)) payloads (max difference
    $(@sprintf("%.1e", hmax))); $(SMALL_CASES[]) hand-made boundary cases.

    ### Throughput across corpus sizes

    Lines/s and MB/s = lines or bytes of the corpus divided by the time.  "Match kernel" is the
    multi-pattern kernel alone (the corpus already on the device, line table built); "GPU pipeline"
    is one timing around line table + matching + extraction + tokens + entropies + histogram +
    flagging; "+ H2D" adds the pageable host-to-device copy of the corpus; "CPU pipeline" is the
    single-threaded baseline doing the same steps.

    $(md_table(header, rows))
    ### Breakdown at $(commas(MAIN_N)) lines ($(f1(b.n / 1e6)) MB), every step timed directly

    $(md_table(["step", "time (ms)", "rate (MB/s or GB/s for copies)"], bd_rows))
    ### Entropy threshold

    Token entropies of all $(commas(length(ts_gpu))) tokens were histogrammed on the GPU (0.05-bit
    bins, `results/entropy_hist.csv`).  The ordinary tokens end at $(f2(bulk_max)) bits (the highest
    entropy of any token shorter than 32 characters), the $(count(>=(32), L_gpu)) long tokens start at
    $(f2(long_min)) bits; the widest empty band of the histogram is $(f2(r.band[1]))–$(f2(r.band[2])) bits and
    its midpoint, **$(f2(thr)) bits/char**, is the threshold.  A token of *n* characters has at most
    log2(*n*) bits of entropy, so a threshold of $(f2(thr)) can only be exceeded by tokens of
    $(ceil(Int, 2^thr))+ characters, which is why ordinary log fields never reach it.

    $(md_table(["threshold (bits/char)", "flagged", "true positives", "false positives", "false negatives", "precision", "recall"], thr_rows))
    ### Match kernel: operation counts and resources ($(commas(MAIN_N)) lines)

    Measured with `match_counts!`: $(commas(candidates)) of $(commas(nbytes)) byte positions pass the
    first-byte filter ($(f2(100cand_frac)) %), costing $(commas(compares)) byte comparisons in total
    ($(f3(cmp_per_byte)) per corpus byte).  Estimated integer operations per corpus byte in the tiled
    kernel: $(f1(int_per_byte)).  Useful bytes moved per corpus byte: 1 (the corpus is read once;
    the pattern tables are read from shared memory).

    $(md_table(["kernel", "registers / thread", "shared memory / block (B)", "local memory (B)", "occupancy", "resident blocks / SM"], res_rows))
    PTX of `match_tiled!` written by this script to `results/match_tiled.ptx`: $(pc.total) instructions,
    $(pc.ld_global) global loads, $(pc.ld_shared) shared loads, $(pc.st_shared) shared stores, $(pc.atom) atomics,
    $(pc.bar) barriers, $(pc.bra) branches.

    Reference bandwidths: device-to-device copy $(f1(copy_bw)) GB/s (read + write)$(theo_bw === nothing ? "" : "; theoretical DRAM $(f1(theo_bw)) GB/s"); INT32 throughput $(int_ops === nothing ? "n/a" : f2(int_ops / 1e12) * " × 10¹² ops/s").
    """
    update_section!(BENCH_FILE, "trackE", section)

    # ---- analysis.md -------------------------------------------------------
    big = breakdown[maximum(SIZES)]
    R_cpu = big.n / big.t_cp                                   # bytes/s, single core, whole pipeline
    R_gpu = big.n / big.s_pipe.mean                            # bytes/s, GPU pipeline
    R_gpu_h2d = big.n / (big.s_pipe.mean + big.t_h2d)          # with the copy
    day = 86_400.0
    gb(x) = f1(x / 1e9)
    V_cpu_day = R_cpu * day; V_gpu_day = R_gpu_h2d * day
    example_V = 2e12                                           # 2 TB/day example site
    cores_needed = ceil(Int, example_V / V_cpu_day); gpus_needed = ceil(Int, example_V / V_gpu_day)
    limiter_txt = if bw_tiled / copy_bw >= 0.6
        "**memory bandwidth**: the tiled kernel streams the corpus at $(f1(bw_tiled)) GB/s, $(pct(bw_tiled / copy_bw)) of the device-to-device copy rate, so most of its time is the one read of the corpus; the first-byte filter keeps the compare work small ($(f3(cmp_per_byte)) compares per byte)."
    else
        "**instruction throughput, not bandwidth**: the tiled kernel reads the corpus at only $(f1(bw_tiled)) GB/s ($(pct(bw_tiled / copy_bw)) of the copy rate) although every byte is loaded exactly once and coalesced; with about $(f1(int_per_byte)) integer operations per byte the integer model predicts $(ms(t_int_bound)) ms against $(ms(t_bw_bound)) ms for the bandwidth model, i.e. the kernel is bound by the per-byte instruction work (table lookups, index arithmetic, the candidate loop with its data-dependent branches: $(pc.bra) branches in the PTX)."
    end
    tiled_vs_global = b.s_mg.mean > b.s_mt.mean ?
        "The shared-memory tile makes the kernel $(f2(b.s_mg.mean / b.s_mt.mean))× faster than the global-memory variant ($(ms(b.s_mg.mean)) vs $(ms(b.s_mt.mean)) ms): the global variant re-reads up to 32 bytes per candidate position from L1/L2, the tiled one from shared memory." :
        "The shared-memory tile does not beat the global-memory variant here ($(ms(b.s_mt.mean)) vs $(ms(b.s_mg.mean)) ms): the candidate re-reads are served by L1 anyway, so the tile only adds a barrier and the halo load; the limiter is not the memory path."
    analysis = """
    # Track E: performance analysis

    $(run_info_md())
    All numbers are measured by `src/p2_run.jl` on this device and inserted when it runs; the
    tables are in `benchmarks.md`.

    ## 1. The headline number

    On the largest corpus ($(commas(maximum(SIZES))) lines, $(f1(big.n / 1e6)) MB) the GPU pipeline
    processes **$(f2(maximum(SIZES) / big.s_pipe.mean / 1e6)) million lines/s ($(f1(mbps(big.n, big.s_pipe.mean))) MB/s)**
    with the corpus resident on the device, and **$(f2(maximum(SIZES) / (big.s_pipe.mean + big.t_h2d) / 1e6)) million lines/s
    ($(f1(mbps(big.n, big.s_pipe.mean + big.t_h2d))) MB/s)** including the pageable host-to-device copy; the match kernel alone
    runs at $(f1(mbps(big.n, big.s_mt.mean))) MB/s.  Converted to a day: **$(gb(V_cpu_day)) GB/day is where one CPU core
    stops keeping up** ($(f1(mbps(big.n, big.t_cp))) MB/s single-threaded, same algorithm), while one GPU keeps up to
    **$(gb(V_gpu_day)) GB/day** including the copy.  Assumptions: 20 indicators (12 addresses, 8 domains),
    lines of about $(f0(big.n / maximum(SIZES))) bytes, the corpus already in host memory (reading it from disk took
    $(ms(big.t_read)) ms = $(f1(mbps(big.n, big.t_read))) MB/s on this machine and is the next wall), batch processing of
    whole files, results small enough that the device-to-host copy is negligible ($(ms(big.t_d2h)) ms).

    ## 2. The limiter

    The dominant kernel is `match_tiled!` ($(pct(b.s_mt.mean / b.s_pipe.mean)) of the pipeline at $(commas(MAIN_N)) lines; the token
    entropy kernel is $(pct(b.t_en / b.s_pipe.mean)), the scans and scatters the rest).  Its operational intensity is low
    and integer: about $(f1(int_per_byte)) integer operations per byte against 1 byte moved, so on the integer roofline
    ($(int_ops === nothing ? "n/a" : f2(int_ops / 1e12)) × 10¹² ops/s against $(f1(theo_bw === nothing ? copy_bw : theo_bw)) GB/s) the balance point is
    $(int_ops === nothing ? "n/a" : f1(int_ops / ((theo_bw === nothing ? copy_bw : theo_bw) * 1e9))) ops/byte: the kernel sits $(int_per_byte > (int_ops === nothing ? 0 : int_ops / ((theo_bw === nothing ? copy_bw : theo_bw) * 1e9)) ? "to the right of it (compute side)" : "to the left of it (memory side)").
    The limiter is $limiter_txt
    $tiled_vs_global

    Evidence (all produced by the script): achieved bandwidth $(f1(bw_tiled)) GB/s vs copy $(f1(copy_bw)) GB/s;
    `CUDA.registers` $(fmt_opt(get(res_t, :registers, nothing))) per thread, $(fmt_opt(get(res_t, :shared, nothing))) B shared memory per block,
    occupancy $(get(res_t, :occupancy, nothing) === nothing ? "n/a" : pct(res_t[:occupancy])), $(fmt_opt(get(res_t, :blocks_per_sm, nothing))) resident blocks per SM;
    measured candidate fraction $(f2(100cand_frac)) % and $(f3(cmp_per_byte)) compares per byte; PTX (`results/match_tiled.ptx`)
    with $(pc.ld_global) global and $(pc.ld_shared) shared loads, $(pc.bra) branches, $(pc.atom) atomics.  Nsight Compute counters were
    not collected; the limiter is inferred from these measurements.

    ## 3. Scaling and the transfer wall

    $(md_table(["lines", "match kernel (MB/s)", "GPU pipeline (MB/s)", "H2D copy (ms)", "pipeline (ms)", "copy / pipeline", "file read (ms)"],
               [(commas(nl), f1(mbps(breakdown[nl].n, breakdown[nl].s_mt.mean)), f1(mbps(breakdown[nl].n, breakdown[nl].s_pipe.mean)),
                 ms(breakdown[nl].t_h2d), ms(breakdown[nl].s_pipe.mean), f2(breakdown[nl].t_h2d / breakdown[nl].s_pipe.mean), ms(breakdown[nl].t_read)) for nl in SIZES]))
    The rate rises with the corpus size until the launch and scan overheads are amortised
    (from $(f1(mbps(breakdown[SIZES[1]].n, breakdown[SIZES[1]].s_pipe.mean))) MB/s at $(commas(SIZES[1])) lines to
    $(f1(mbps(big.n, big.s_pipe.mean))) MB/s at $(commas(maximum(SIZES)))) and then stays flat: the kernels are streaming
    kernels whose time grows linearly with the bytes.  The host-to-device copy costs $(f2(big.t_h2d / big.s_pipe.mean))× the whole
    GPU pipeline at the largest size ($(f1(gbps(big.n, big.t_h2d))) GB/s pageable$(isnan(big.t_h2d_pin) ? "" : ", $(f1(gbps(big.n, big.t_h2d_pin))) GB/s pinned")):
    the transfer wall is $(big.t_h2d > big.s_pipe.mean ? "real: for one-shot scans the copy, not the kernel, sets the rate, and only overlapping copy and compute (streams, chunks) or keeping the logs on the device removes it" : "not reached: the pipeline is slower than the copy, so the GPU work still dominates end to end").
    Reading the file from disk ($(f1(mbps(big.n, big.t_read))) MB/s here) is slower than both.

    ## 4. CPU comparison

    Against the single-threaded baseline with the same algorithm, the GPU pipeline is **$(f1(big.t_cp / big.s_pipe.mean))×** faster
    on the device and **$(f1(big.t_cp / (big.s_pipe.mean + big.t_h2d)))×** including the copy (largest corpus).  Per step at
    $(commas(MAIN_N)) lines: matching $(f1(b.t_cm / b.s_mt.mean))× (the library `occursin` search is $(f1(b.t_co / b.s_mt.mean))× slower than the
    kernel), token entropies $(f1(b.t_ce / b.t_en))×, line table $(f1(b.t_cl / b.t_lt))×.  The CPU numbers are one core; a tuned
    multithreaded matcher would scale with the core count, which is the research project's question.

    ## 5. The defensive conclusion

    A SOC that must match $(length(inds)) indicators against its logs every day can size the job from these rates: one
    CPU core covers up to **$(gb(V_cpu_day)) GB/day**, one GPU (including the copy) up to **$(gb(V_gpu_day)) GB/day**.  For a site
    producing 2 TB/day that is **$(cores_needed) CPU core$(cores_needed > 1 ? "s" : "") or $(gpus_needed) GPU$(gpus_needed > 1 ? "s" : "")** (2 × 10¹² / (86,400 × $(f1(R_cpu / 1e6)) × 10⁶) and
    2 × 10¹² / (86,400 × $(f1(R_gpu_h2d / 1e6)) × 10⁶)); below $(gb(V_cpu_day)) GB/day a single core keeps up and a GPU is not needed.
    The crossover moves with the indicator count (the research project measures 10 to 10,000) and with the storage
    rate: at $(f1(mbps(big.n, big.t_read))) MB/s disk reads the GPU is starved, so the logs must be streamed to it as they arrive
    or kept in device memory.  Entropy flagging at $(f2(thr)) bits/char produced $(length(fl)) flags in $(commas(MAIN_N)) lines
    with precision $(thr_rows[3][6]) and recall $(thr_rows[3][7]) on the planted payloads, i.e. about
    $(f1(length(fl) / MAIN_N * 1e6)) flags per million lines for an analyst to look at: the threshold is chosen from the
    measured distribution, not from the generator's hint, because the payloads of this corpus start at $(f2(long_min)) bits.
    Limits: synthetic logs, 20 fixed-length indicators, no regular expressions, a single GPU session; nothing here
    processes real logs (course policy).
    """
    write(joinpath(RESULTS_DIR, "analysis.md"), analysis)
    println("\nResults written to $BENCH_FILE and $(joinpath(RESULTS_DIR, "analysis.md"))")

    if get(ENV, "P2_NO_PLOTS", "0") != "1"
        try
            include("p2_plots.jl")
            make_plots(RESULTS_DIR, thr)
            println("Plots written to $RESULTS_DIR")
        catch err
            println("Plots not drawn (", first(sprint(showerror, err), 200), "); the data is in results/*.csv")
        end
    end
end
