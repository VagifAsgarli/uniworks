# rp_run.jl - the research project's run script (topic 10, log indicator
# matching): header block, validation of every method against the ground
# truth, the list-size sweep, the corpus-size sweep, the CPU-threads sweep,
# results/benchmarks.md, results/analysis.md, the CSVs, the PTX dump and the
# plots.
#
#   julia -t auto --project=. src/rp_run.jl
#
# Environment: RP_MAIN=<lines> corpus of the validation and the list sweep
# (default 1,000,000); RP_LISTS=10,30,... list sizes; RP_SIZES=... corpus
# sizes of the data-rate sweep; RP_THREADS=1,2,4 chunk counts of the CPU
# matcher (capped at Julia's thread count); RP_REPS, RP_CPU_REPS; RP_G1_MAX
# largest list for the per-indicator GPU baseline (default 3000); RP_C2_MAX
# largest list for the occursin baseline (default 300); RP_QUICK=1 validation
# only; RP_CPU_ONLY=1 CPU methods only (no GPU needed); RP_NO_PLOTS=1.

const STUDENT_CARD = "251ADM047"
const STUDENT_NAME = "Vagif Asgarli"

using Printf
include("rp_common.jl")
include("rp_data.jl")
include("rp_cpu.jl")
const CPU_ONLY = get(ENV, "RP_CPU_ONLY", "0") == "1"
CPU_ONLY || include("rp_gpu.jl")

const SEED        = student_seed(STUDENT_CARD)
const MAIN_N      = parse(Int, get(ENV, "RP_MAIN", "1000000"))
const SIZES       = corpus_sizes()
const LISTS       = list_sizes()
const CPU_REPS    = parse(Int, get(ENV, "RP_CPU_REPS", "3"))
const THREADS     = filter(t -> t <= Threads.nthreads(), parse.(Int, split(get(ENV, "RP_THREADS", "1,2,4"), ",")))
const G1_MAX      = parse(Int, get(ENV, "RP_G1_MAX", "3000"))
const C2_MAX      = parse(Int, get(ENV, "RP_C2_MAX", "300"))
const SIZE_LIST_N = parse(Int, get(ENV, "RP_SIZE_LIST", "1000"))    # list size of the corpus-size sweep
isempty(THREADS) && error("RP_THREADS has no value <= Threads.nthreads() = $(Threads.nthreads()); start Julia with -t")
1 in THREADS || error("RP_THREADS must include 1 (the single-task reference)")

# ---------------------------------------------------------------------------
# Header block
# ---------------------------------------------------------------------------
println("Student: $STUDENT_NAME, ID: $STUDENT_CARD")
println("Research project, topic 10: log lines per second as the indicator list grows from 10 to 10,000")
println("Derived parameters: generator seed = $SEED (SHA-256 of the ID), validation corpus = $(commas(MAIN_N)) lines, list sizes = $(join(commas.(LISTS), ", ")), corpus sizes = $(join(commas.(SIZES), ", "))")
println("Host: $(strip(Sys.cpu_info()[1].model)), $(Sys.CPU_THREADS) hardware threads; Julia threads: $(Threads.nthreads()); CPU chunk counts: $(join(THREADS, ", "))")
if CPU_ONLY
    println("Device: none (RP_CPU_ONLY=1)")
else
    println("Device: $(CUDA.name(CUDA.device()))")
    println("Compute capability: $(CUDA.capability(CUDA.device()))")
end

# ---------------------------------------------------------------------------
# Data and validation
# ---------------------------------------------------------------------------
corpus = load_corpus(MAIN_N)
base   = load_indicators(MAIN_N)
truth  = load_truth(MAIN_N)
ls_cpu = cpu_line_starts(corpus)
require(nlines_of(ls_cpu) == MAIN_N, "line count $(nlines_of(ls_cpu)) != $MAIN_N")
println("Corpus: $(commas(length(corpus))) bytes, $(commas(MAIN_N)) lines; $(length(base)) generator indicators; truth: $(length(truth)) (line, indicator) pairs")
lists = Dict(N => indicator_list(N, base) for N in LISTS)
for N in LISTS
    require(length(lists[N]) == N && allunique(lists[N]), "list $N: $(length(lists[N])) entries")
end

# 1. the generator's own 20 indicators: every method equals the generator's truth
t20   = IndicatorTable(base)
hits1 = cpu_hash_match(corpus, t20; T = 1)
require(pairs_to_set(hits1, base) == truth, "CPU hash matcher (1 thread) != generator truth: $(length(hits1)) vs $(length(truth))")
for T in THREADS
    require(cpu_hash_match(corpus, t20; T) == hits1, "CPU hash matcher with $T chunks != 1 chunk")
end
lines_main = corpus_lines(corpus, ls_cpu)
require(pairs_to_set(cpu_match_occursin(lines_main, base), base) == truth, "occursin baseline != generator truth")
if !CPU_ONLY
    corpus_d = CuVector(corpus)
    dt20 = DeviceTable(t20)
    r20 = gpu_hash_pipeline(corpus_d, dt20; variant = :global)
    require(Array(r20.line_start) == ls_cpu, "GPU line table != CPU")
    require(host_pairs(r20) == hits1, "GPU hash matcher (global) != CPU")
    hit_s = CuVector{Int32}(undef, length(r20.token_start))
    launch_hash_match!(hit_s, corpus_d, r20.token_start, dt20; variant = :shared)
    require(Array(hit_s) == Array(r20.hit), "GPU hash matcher (shared keys) != global")
    r20d = gpu_direct_pipeline(corpus_d, dt20)
    require(host_pairs(r20d) == hits1, "GPU direct matcher (no compaction) != CPU")
    free_results!(r20d)
    groups20 = device_groups(base)
    masks20 = [CUDA.zeros(UInt32, MAIN_N) for _ in groups20]
    launch_groups!(masks20, corpus_d, groups20, r20.line_start)
    require(group_pairs(masks20) == hits1, "GPU per-indicator matcher != CPU")
    ntok_main = length(r20.token_start)
    free_all!(hit_s, masks20...); free_results!(r20)
end
println("Validation on the generator's $(length(base)) indicators: all methods equal the truth ($(length(truth)) pairs)")

# 2. every list size: the CPU matcher equals the restricted truth; every other method equals the CPU matcher
for N in LISTS
    list = lists[N]; tN = IndicatorTable(list)
    expected = truth_for_list(truth, list)
    hN = cpu_hash_match(corpus, tN; T = 1)
    require(pairs_to_set(hN, list) == expected, "list $N: CPU hash matcher != restricted truth ($(length(hN)) vs $(length(expected)))")
    N <= C2_MAX && require(cpu_match_occursin(lines_main, list) == hN, "list $N: occursin != CPU hash matcher")
    if !CPU_ONLY
        dtN = DeviceTable(tN)
        rN = gpu_hash_pipeline(corpus_d, dtN; variant = :global)
        require(host_pairs(rN) == hN, "list $N: GPU hash matcher != CPU")
        rNd = gpu_direct_pipeline(corpus_d, dtN)
        require(host_pairs(rNd) == hN, "list $N: GPU direct matcher != CPU")
        free_results!(rNd)
        if dtN.capacity <= SHARED_CAP
            hs = CuVector{Int32}(undef, length(rN.token_start))
            launch_hash_match!(hs, corpus_d, rN.token_start, dtN; variant = :shared)
            require(Array(hs) == Array(rN.hit), "list $N: shared-keys variant != global")
            CUDA.unsafe_free!(hs)
        end
        if N <= G1_MAX
            gN = device_groups(list); mN = [CUDA.zeros(UInt32, MAIN_N) for _ in gN]
            launch_groups!(mN, corpus_d, gN, rN.line_start)
            require(group_pairs(mN) == hN, "list $N: GPU per-indicator matcher != CPU")
            free_all!(mN...)
        end
        free_results!(rN)
    end
end
println("Validation on every list size: hit sets equal across methods (hits stay at $(length(truth)) pairs: the cold indicators never occur)")

# 3. hand-made small cases (whole-token semantics, corpus ends, chunk boundaries)
const SMALL_CASES = Ref(0)
function small_case(text, list; expect)
    SMALL_CASES[] += 1
    c = Vector{UInt8}(codeunits(text)); t = IndicatorTable(list)
    ls = cpu_line_starts(c)
    for T in (1, 3)
        got = pairs_to_set(cpu_hash_match(c, t; T), list)
        require(got == Set(expect), "small case $(repr(text[1:min(end, 40)])) (CPU, $T chunks): got $got, expected $expect")
    end
    if !CPU_ONLY
        dt = DeviceTable(t)
        r = gpu_hash_pipeline(CuVector(c), dt; variant = :global)
        require(Array(r.line_start) == ls, "small case line table: $(repr(text[1:min(end, 40)]))")
        require(pairs_to_set(host_pairs(r), list) == Set(expect), "small case $(repr(text[1:min(end, 40)])) (GPU): expected $expect")
        rd = gpu_direct_pipeline(CuVector(c), dt)
        require(pairs_to_set(host_pairs(rd), list) == Set(expect), "small case $(repr(text[1:min(end, 40)])) (GPU direct): expected $expect")
        free_results!(rd)
        if all(length(codeunits(s)) <= MAXPLEN for s in list)      # the per-indicator kernel takes patterns up to MAXPLEN bytes
            g = device_groups(list); m = [CUDA.zeros(UInt32, nlines_of(ls)) for _ in g]
            launch_groups!(m, CuVector(c), g, r.line_start)
            require(pairs_to_set(group_pairs(m), list) == Set(expect), "small case $(repr(text[1:min(end, 40)])) (GPU groups)")
            free_all!(m...)
        end
        free_results!(r)
    end
end
small_case("", ["abc"]; expect = [])
small_case("abc", ["abc"]; expect = [(1, "abc")])                                   # one line, no newline
small_case("x abc\nabc y\n", ["abc"]; expect = [(1, "abc"), (2, "abc")])
small_case("abcd\nxabc\nab\n", ["abc"]; expect = [])                                # inside longer tokens: no match
small_case("a.b\n192.0.2.24 x\n192.0.2.248\n", ["192.0.2.24", "192.0.2.248"]; expect = [(2, "192.0.2.24"), (3, "192.0.2.248")])
small_case("one two\nthree one two\n", ["one", "two"]; expect = [(1, "one"), (1, "two"), (2, "one"), (2, "two")])
small_case("http://app3.invalid/ from 198.51.100.7 port\n", ["app3.invalid", "198.51.100.7"]; expect = [(1, "app3.invalid"), (1, "198.51.100.7")])
small_case("l1 aa\nl2\nl3 bb\nl4 aa bb\nl5\n", ["aa", "bb"]; expect = [(1, "aa"), (3, "bb"), (4, "aa"), (4, "bb")])   # several chunks
small_case("y"^70 * " abc\n", ["abc"]; expect = [(1, "abc")])                       # a token longer than MAXIND before the hit
small_case("y"^MAXIND * " z\n", ["y"^MAXIND]; expect = [(1, "y"^MAXIND)])           # a token of exactly MAXIND bytes is hashed whole
small_case("y"^(MAXIND + 1) * "\n", ["y"^MAXIND]; expect = [])                      # a longer token is never looked up
println("Validation passed: $(SMALL_CASES[]) hand-made cases")
println("Correct!")

# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------
fmt_opt(x, f = string) = x === nothing ? "n/a" : f(x)
pct(x) = @sprintf("%.0f %%", 100x)
if !CPU_ONLY
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
    if isdefined(CUDA, Symbol("@device_code_ptx"))
        @eval function dump_ptx(launcher::Function)
            io = IOBuffer()
            CUDA.@device_code_ptx io=io launcher()
            return String(take!(io))
        end
    else
        dump_ptx(launcher::Function) = ""
    end
    function kernel_body(ptx::AbstractString)
        i = findfirst(".entry", ptx); i === nothing && return ptx
        j = findnext("\n}", ptx, last(i)); j === nothing && return ptx[first(i):end]
        return ptx[first(i):last(j)]
    end
    function ptx_counts(ptx::AbstractString)
        ptx = kernel_body(ptx)
        c(pat) = count(_ -> true, eachmatch(pat, ptx))
        return (ld_global = c(r"ld\.global"), ld_shared = c(r"ld\.shared"), st_shared = c(r"st\.shared"),
                atom = c(r"\b(atom|red)\."), bar = c(r"bar\.sync"), bra = c(r"\bbra\b"), total = c(r"^\s+[a-z@][\w.@%]*\s"m))
    end
end

if !QUICK
    CPU_ONLY || record_device_info()
    mkpath(RESULTS_DIR)
    hostname = replace(strip(Sys.cpu_info()[1].model), r"[^A-Za-z0-9]+" => "-")
    nbytes = length(corpus)
    g1_reps(N) = N <= 300 ? REPS : N <= 1000 ? min(REPS, 10) : min(REPS, 5)

    # ---- sweep A: list size at MAIN_N -----------------------------------------
    A = Dict{Int,Any}()
    csvA = String["N,capacity,table_bytes,buf_bytes" *
                  (CPU_ONLY ? "" : ",line_table_s,token_starts_s,hash_global_s,hash_shared_s,extract_s,pipeline_s,direct_s,pipeline_direct_s,g1_s,g1_groups,probes_per_token,equal_per_token") *
                  join([",cpu_t$(T)_s" for T in THREADS]) * ",occursin_s"]
    for N in LISTS
        list = lists[N]; tN = IndicatorTable(list)
        tb, bb = table_bytes(tN)
        println("\n[list of $(commas(N)) indicators, table $(commas(tb)) B + buffer $(commas(bb)) B]")
        row = Dict{Symbol,Any}(:N => N, :capacity => tN.capacity, :table_bytes => tb, :buf_bytes => bb)
        if !CPU_ONLY
            dtN = DeviceTable(tN)
            flags = CuVector{UInt32}(undef, nbytes)
            row[:t_lt] = time_kernel(() -> free_all!(gpu_line_starts(corpus_d, flags)))
            ls_d = gpu_line_starts(corpus_d, flags)
            row[:t_ts] = time_kernel(() -> free_all!(gpu_token_starts(corpus_d, flags, dtN.is_word)))
            ts_d = gpu_token_starts(corpus_d, flags, dtN.is_word)
            hit_d = CuVector{Int32}(undef, length(ts_d))
            s_hg = time_stats(() -> launch_hash_match!(hit_d, corpus_d, ts_d, dtN; variant = :global))
            row[:t_hg] = s_hg.mean; row[:s_hg] = s_hg
            row[:t_hs] = dtN.capacity <= SHARED_CAP ? time_kernel(() -> launch_hash_match!(hit_d, corpus_d, ts_d, dtN; variant = :shared)) : NaN
            launch_hash_match!(hit_d, corpus_d, ts_d, dtN; variant = :global)
            row[:t_ex] = time_kernel(() -> free_all!(gpu_extract_hits(hit_d, ts_d, ls_d)...))
            s_pipe = time_stats(() -> free_results!(gpu_hash_pipeline(corpus_d, dtN; variant = :global)); reps = min(REPS, 20))
            row[:t_pipe] = s_pipe.mean; row[:s_pipe] = s_pipe
            hp = CuVector{Int32}(undef, HIT_CAP); hi = CuVector{Int32}(undef, HIT_CAP); nh = CuVector{Int32}(undef, 1)
            row[:t_hd] = time_kernel(() -> launch_hash_direct!(hp, hi, nh, corpus_d, dtN))
            s_pdir = time_stats(() -> free_results!(gpu_direct_pipeline(corpus_d, dtN)); reps = min(REPS, 20))
            row[:t_pdir] = s_pdir.mean; row[:s_pdir] = s_pdir
            free_all!(hp, hi, nh)
            counters = CUDA.zeros(UInt64, 2)
            @cuda threads=HASH_THREADS blocks=cld(length(ts_d), HASH_THREADS) probe_counts!(counters, corpus_d, ts_d, dtN.is_word, dtN.keys, dtN.len, dtN.mask)
            probes, equal = Int.(Array(counters))
            row[:probes] = probes / length(ts_d); row[:equal] = equal / length(ts_d); row[:ntok] = length(ts_d)
            if N <= G1_MAX
                gN = device_groups(list); mN = [CUDA.zeros(UInt32, MAIN_N) for _ in gN]
                reset = () -> foreach(m -> fill!(m, UInt32(0)), mN)
                s_g1 = time_stats(() -> launch_groups!(mN, corpus_d, gN, ls_d); reset = reset, reps = g1_reps(N))
                row[:t_g1] = s_g1.mean; row[:s_g1] = s_g1; row[:groups] = length(gN)
                free_all!(mN...)
            else
                row[:t_g1] = NaN; row[:groups] = cld(N, MAXPAT)
            end
            free_all!(flags, ls_d, ts_d, hit_d, counters)
            GC.gc(); CUDA.reclaim()
            println("  GPU: tokens $(ms(row[:t_ts])) ms, hash match $(ms(row[:t_hg])) ms (shared keys $(isnan(row[:t_hs]) ? "n/a" : ms(row[:t_hs]) * " ms")), pipeline $(ms(row[:t_pipe])) ms; direct $(ms(row[:t_hd])) ms, pipeline $(ms(row[:t_pdir])) ms; per-indicator $(isnan(row[:t_g1]) ? "n/a" : ms(row[:t_g1]) * " ms") ($(row[:groups]) groups); $(f2(row[:probes])) probes/token")
        end
        for T in THREADS
            row[Symbol("cpu_t", T)] = time_cpu(() -> cpu_hash_match(corpus, tN; T); reps = CPU_REPS).min
        end
        row[:t_c2] = N <= C2_MAX ? time_cpu(() -> cpu_match_occursin(lines_main, list); reps = N <= 30 ? CPU_REPS : 1).min : NaN
        println("  CPU: " * join(["$T chunk$(T > 1 ? "s" : "") $(f3(row[Symbol("cpu_t", T)])) s" for T in THREADS], ", ") * "; occursin $(isnan(row[:t_c2]) ? "n/a" : f3(row[:t_c2]) * " s")")
        A[N] = row
        push!(csvA, join(string.(vcat([N, tN.capacity, tb, bb],
                                      CPU_ONLY ? [] : [row[:t_lt], row[:t_ts], row[:t_hg], row[:t_hs], row[:t_ex], row[:t_pipe], row[:t_hd], row[:t_pdir], row[:t_g1], row[:groups], row[:probes], row[:equal]],
                                      [row[Symbol("cpu_t", T)] for T in THREADS], [row[:t_c2]])), ","))
    end
    write(joinpath(RESULTS_DIR, CPU_ONLY ? "list_sweep_cpu_$(hostname).csv" : "list_sweep.csv"), join(csvA, "\n") * "\n")

    # ---- sweep B: corpus size at SIZE_LIST_N ---------------------------------
    Nb = SIZE_LIST_N
    listB = indicator_list(Nb, base); tB = IndicatorTable(listB)
    B = Dict{Int,Any}()
    csvB = String["lines,bytes,read_s" * (CPU_ONLY ? "" : ",h2d_s,h2d_pinned_s,pipeline_s,pipeline_direct_s,d2h_s") * join([",cpu_t$(T)_s" for T in THREADS])]
    for nl in SIZES
        ensure_corpus(nl)
        path = corpus_path(nl)
        t_read = time_cpu(() -> read(path); reps = CPU_REPS).min
        c = read(path); n = length(c)
        println("\n[$(commas(nl)) lines, $(f1(n / 1e6)) MB, list of $(commas(Nb))]")
        rowb = Dict{Symbol,Any}(:n => n, :t_read => t_read)
        if !CPU_ONLY
            dtB = DeviceTable(tB)
            cd = CuVector{UInt8}(undef, n)
            rowb[:t_h2d] = time_stats(() -> copyto!(cd, c)).mean
            rowb[:t_h2d_pin] = try
                CUDA.pin(c)
                time_stats(() -> copyto!(cd, c)).mean
            catch
                NaN
            end
            s_pipe = time_stats(() -> free_results!(gpu_hash_pipeline(cd, dtB; variant = :global)); reps = min(REPS, 20))
            rowb[:t_pipe] = s_pipe.mean; rowb[:s_pipe] = s_pipe
            rowb[:t_pdir] = time_stats(() -> free_results!(gpu_direct_pipeline(cd, dtB)); reps = min(REPS, 20)).mean
            res = gpu_hash_pipeline(cd, dtB; variant = :global)
            rowb[:t_d2h] = time_stats(() -> (Array(res.lines); Array(res.inds))).mean
            free_results!(res); free_all!(cd)
            GC.gc(); CUDA.reclaim()
        end
        for T in THREADS
            rowb[Symbol("cpu_t", T)] = time_cpu(() -> cpu_hash_match(c, tB; T); reps = CPU_REPS).min
        end
        B[nl] = rowb
        push!(csvB, join(string.(vcat([nl, n, t_read], CPU_ONLY ? [] : [rowb[:t_h2d], rowb[:t_h2d_pin], rowb[:t_pipe], rowb[:t_pdir], rowb[:t_d2h]],
                                      [rowb[Symbol("cpu_t", T)] for T in THREADS])), ","))
        println("  " * (CPU_ONLY ? "" : "GPU pipeline $(ms(rowb[:t_pipe])) ms ($(f1(mbps(n, rowb[:t_pipe]))) MB/s), direct $(ms(rowb[:t_pdir])) ms, +H2D $(ms(rowb[:t_pipe] + rowb[:t_h2d])) ms; ") * "CPU $(THREADS[end]) chunks $(f3(rowb[Symbol("cpu_t", THREADS[end])])) s ($(f1(mbps(n, rowb[Symbol("cpu_t", THREADS[end])]))) MB/s)")
        c = nothing; GC.gc()
    end
    write(joinpath(RESULTS_DIR, CPU_ONLY ? "size_sweep_cpu_$(hostname).csv" : "size_sweep.csv"), join(csvB, "\n") * "\n")

    if CPU_ONLY
        println("\nCPU-only run finished; CSVs written to $RESULTS_DIR (host $hostname, $(Threads.nthreads()) Julia threads)")
    else
        # ---- evidence: resources, PTX, reference bandwidths -------------------
        copy_bw = measured_copy_bandwidth()
        theo_bw = theoretical_bandwidth()
        dtE = DeviceTable(IndicatorTable(lists[LISTS[end]]))
        flagsE = CuVector{UInt32}(undef, nbytes)
        tsE = gpu_token_starts(corpus_d, flagsE, dtE.is_word); hitE = CuVector{Int32}(undef, length(tsE))
        kh = @cuda launch=false hash_match!(hitE, corpus_d, tsE, dtE.is_word, dtE.keys, dtE.ind, dtE.off, dtE.len, dtE.buf, dtE.mask)
        ks = @cuda launch=false hash_match_shared!(hitE, corpus_d, tsE, dtE.is_word, dtE.keys, dtE.ind, dtE.off, dtE.len, dtE.buf, dtE.mask)
        kw = @cuda launch=false word_flags!(flagsE, corpus_d, dtE.is_word)
        res_h = kernel_resources(kh, HASH_THREADS); res_s = kernel_resources(ks, HASH_THREADS); res_w = kernel_resources(kw, 256)
        ptx = dump_ptx(() -> @cuda launch=false hash_match!(hitE, corpus_d, tsE, dtE.is_word, dtE.keys, dtE.ind, dtE.off, dtE.len, dtE.buf, dtE.mask))
        isempty(ptx) || write(joinpath(RESULTS_DIR, "hash_match.ptx"), ptx)
        pc = ptx_counts(ptx)
        free_all!(flagsE, tsE, hitE)
        l1_bytes = 64 * 1024; l2_bytes = something(device_attr(:L2_CACHE_SIZE), 0)

        # ---- benchmarks.md ---------------------------------------------------
        Tmax = THREADS[end]
        rate(t) = f2(MAIN_N / t / 1e6)                         # M lines/s
        hdrA = ["N", "table (KB)", "GPU hash-set: pipeline (ms)", "M lines/s", "hash kernel (ms)", "shared keys (ms)", "probes/token",
                "GPU direct: pipeline (ms)", "M lines/s", "direct kernel (ms)",
                "GPU per-indicator (ms)", "groups", "M lines/s", "CPU hash-set $Tmax thr. (s)", "M lines/s", "CPU 1 thr. (s)", "occursin (s)"]
        rowsA = [(commas(N), f1((A[N][:table_bytes] + A[N][:buf_bytes]) / 1024), ms(A[N][:t_pipe]), rate(A[N][:t_pipe]), ms(A[N][:t_hg]),
                  isnan(A[N][:t_hs]) ? "n/a" : ms(A[N][:t_hs]), f2(A[N][:probes]),
                  ms(A[N][:t_pdir]), rate(A[N][:t_pdir]), ms(A[N][:t_hd]),
                  isnan(A[N][:t_g1]) ? "n/a" : ms(A[N][:t_g1]), A[N][:groups], isnan(A[N][:t_g1]) ? "n/a" : rate(A[N][:t_g1]),
                  f3(A[N][Symbol("cpu_t", Tmax)]), rate(A[N][Symbol("cpu_t", Tmax)]), f3(A[N][:cpu_t1]),
                  isnan(A[N][:t_c2]) ? "n/a" : f3(A[N][:t_c2])) for N in LISTS]
        hdrB = ["lines", "MB", "GPU pipeline (ms)", "MB/s", "GPU direct pipeline (ms)", "MB/s", "+ H2D pageable (ms)", "MB/s", "H2D pinned (ms)", "CPU $Tmax thr. (s)", "MB/s", "speed-up (GPU)", "speed-up (GPU + H2D)"]
        rowsB = [(commas(nl), f1(B[nl][:n] / 1e6), ms(B[nl][:t_pipe]), f1(mbps(B[nl][:n], B[nl][:t_pipe])),
                  ms(B[nl][:t_pdir]), f1(mbps(B[nl][:n], B[nl][:t_pdir])),
                  ms(B[nl][:t_pipe] + B[nl][:t_h2d]), f1(mbps(B[nl][:n], B[nl][:t_pipe] + B[nl][:t_h2d])),
                  isnan(B[nl][:t_h2d_pin]) ? "n/a" : ms(B[nl][:t_h2d_pin]),
                  f3(B[nl][Symbol("cpu_t", Tmax)]), f1(mbps(B[nl][:n], B[nl][Symbol("cpu_t", Tmax)])),
                  f1(B[nl][Symbol("cpu_t", Tmax)] / B[nl][:t_pipe]), f1(B[nl][Symbol("cpu_t", Tmax)] / (B[nl][:t_pipe] + B[nl][:t_h2d]))) for nl in SIZES]
        Nt = LISTS[argmin(abs.(LISTS .- SIZE_LIST_N))]
        hdrT = ["Julia tasks (chunks)", "time (s)", "M lines/s", "speed-up over 1"]
        rowsT = [(T, f3(A[Nt][Symbol("cpu_t", T)]), rate(A[Nt][Symbol("cpu_t", T)]), f2(A[Nt][:cpu_t1] / A[Nt][Symbol("cpu_t", T)])) for T in THREADS]
        res_rows = [(name, fmt_opt(get(rr, :registers, nothing)), fmt_opt(get(rr, :shared, nothing)), fmt_opt(get(rr, :local, nothing)),
                     get(rr, :occupancy, nothing) === nothing ? "n/a" : pct(rr[:occupancy]), fmt_opt(get(rr, :blocks_per_sm, nothing)))
                    for (name, rr) in (("hash_match! (256 threads)", res_h), ("hash_match_shared! (256 threads)", res_s), ("word_flags! (256 threads)", res_w))]
        b1 = A[Nt]                                             # the breakdown row: the list size of the corpus sweep
        section = """
        ## Topic 10: log indicator matching as the list grows

        $(run_info_md())
        Validation on the $(commas(MAIN_N))-line corpus: the generator's $(length(base)) indicators give $(length(truth)) (line, indicator)
        pairs, found identically by the CPU hash-set matcher (1 to $Tmax chunks), the `occursin` baseline, the GPU hash-set
        matcher (global table and shared keys) and the GPU per-indicator matcher; for every list size the GPU methods and
        the `occursin` baseline (lists up to $(commas(C2_MAX))) equal the CPU matcher, which equals the truth restricted to the
        list; $(SMALL_CASES[]) hand-made cases.  Tokens of the corpus: $(commas(ntok_main)).

        ### List-size sweep ($(commas(MAIN_N)) lines, $(f1(nbytes / 1e6)) MB)

        "GPU hash-set: pipeline" is one timing around line table + token scan + hash match + extraction; "hash kernel"
        is the match kernel alone (tokens already found); "shared keys" the variant with the table keys in shared
        memory (capacity ≤ $(commas(SHARED_CAP))); "GPU per-indicator" is one launch of the Project 2 kernel per group of
        32 indicators (lists up to $(commas(G1_MAX))); "CPU hash-set" is the tuned matcher with $Tmax Julia tasks on
        $(strip(Sys.cpu_info()[1].model)) ($(Sys.CPU_THREADS) hardware threads); "occursin" the library route (lists up to $(commas(C2_MAX))).

        $(md_table(hdrA, rowsA))
        ### Corpus-size sweep (list of $(commas(Nb)) indicators)

        $(md_table(hdrB, rowsB))
        ### CPU threads ($(commas(MAIN_N)) lines, list of $(commas(Nt)))

        $(md_table(hdrT, rowsT))
        ### Evidence

        $(md_table(["kernel", "registers / thread", "shared memory / block (B)", "local memory (B)", "occupancy", "resident blocks / SM"], res_rows))
        PTX of `hash_match!` written by this script to `results/hash_match.ptx`: $(pc.total) instructions, $(pc.ld_global) global loads,
        $(pc.ld_shared) shared loads, $(pc.atom) atomics, $(pc.bra) branches.  Device-to-device copy $(f1(copy_bw)) GB/s (read + write)$(theo_bw === nothing ? "" : "; theoretical DRAM $(f1(theo_bw)) GB/s"); L2 cache $(l2_bytes == 0 ? "n/a" : string(l2_bytes ÷ 1024, " KB")).
        Table footprint per list size (keys + indices + offsets + lengths, 16 B per slot, load ≤ 0.5) and the packed
        indicator buffer: see the CSV; the table of $(commas(LISTS[end])) indicators takes $(f1(A[LISTS[end]][:table_bytes] / 1024)) KB$(l2_bytes == 0 ? "" : " ($(pct(A[LISTS[end]][:table_bytes] / l2_bytes)) of L2)").
        """
        update_section!(BENCH_FILE, "topic10", section)

        # ---- analysis.md -----------------------------------------------------
        Nmax = LISTS[end]; Nmin = LISTS[1]
        g2_rates = [MAIN_N / A[N][:t_pipe] for N in LISTS]
        g2_min, g2_max = extrema(g2_rates)
        g1_N = filter(N -> !isnan(A[N][:t_g1]), LISTS)
        g1_per_group = isempty(g1_N) ? NaN : sum(A[N][:t_g1] for N in g1_N) / sum(A[N][:groups] for N in g1_N)
        g1_pred_max = g1_per_group * cld(Nmax, MAXPAT)
        cross = findfirst(N -> !isnan(A[N][:t_g1]) && A[N][:t_pipe] < A[N][:t_g1] + A[N][:t_lt], LISTS)
        cross_txt = cross === nothing ? "the per-indicator kernel (plus the line table it needs) stayed faster than the hash-set pipeline up to $(commas(g1_N[end])) indicators" :
                    cross == 1 ? "the hash-set pipeline is already faster than the per-indicator kernel (plus the line table it needs) at the smallest list, $(commas(LISTS[1])) indicators" :
                    "the hash-set pipeline overtakes the per-indicator kernel (plus the line table it needs) between $(commas(LISTS[cross - 1])) and $(commas(LISTS[cross])) indicators"
        hs_N = filter(N -> !isnan(A[N][:t_hs]), LISTS)
        hs_txt = isempty(hs_N) ? "" : "With the keys in shared memory the match kernel takes " * join(["$(ms(A[N][:t_hs])) ms at $(commas(N))" for N in hs_N], ", ") * " against " * join(["$(ms(A[N][:t_hg])) ms" for N in hs_N], ", ") * " from global memory: " *
                 (sum(A[N][:t_hs] for N in hs_N) < 0.9 * sum(A[N][:t_hg] for N in hs_N) ? "the table's placement matters while it fits." : "the placement of the table does not matter at these sizes; the probes are served from L1/L2 anyway.")
        cpu1 = [A[N][:cpu_t1] for N in LISTS]; cpuT = [A[N][Symbol("cpu_t", Tmax)] for N in LISTS]
        big = B[SIZES[end]]
        R_gpu = big[:n] / big[:t_pipe]; R_gpu_h2d = big[:n] / (big[:t_pipe] + big[:t_h2d]); R_cpu = big[:n] / big[Symbol("cpu_t", Tmax)]
        R_cpu1 = big[:n] / big[:cpu_t1]
        day = 86_400.0
        vol(x) = x >= 1e13 ? f1(x / 1e12) * " TB/day" : f1(x / 1e9) * " GB/day"
        shares = [("the line table", b1[:t_lt]), ("the token scan (flags, scan, scatter)", b1[:t_ts]), ("the hash-match kernel", b1[:t_hg]), ("the extraction of the hits", b1[:t_ex])]
        largest = shares[argmax(last.(shares))]
        analysis = """
        # Topic 10: performance analysis

        $(run_info_md())
        All numbers are measured by `src/rp_run.jl` on this device and inserted when it runs; the tables are in
        `benchmarks.md`, the raw timings in `list_sweep.csv` and `size_sweep.csv`.

        ## 1. The objective and the headline number

        Log lines per second as the indicator list grows from $(commas(Nmin)) to $(commas(Nmax)) entries, GPU against a tuned
        multithreaded CPU, and the data rate at which the GPU is needed and still keeps up.  On $(commas(MAIN_N)) lines
        ($(f1(nbytes / 1e6)) MB) the GPU hash-set pipeline runs at **$(f2(g2_min / 1e6))–$(f2(g2_max / 1e6)) million lines/s over the whole range of list
        sizes** ($(f2(MAIN_N / A[Nmax][:t_pipe] / 1e6)) M lines/s at $(commas(Nmax))); the tuned CPU matcher with $Tmax tasks runs at
        $(f2(MAIN_N / cpuT[end] / 1e6)) M lines/s at $(commas(Nmax)) ($(f2(MAIN_N / cpu1[end] / 1e6)) with one task), so the GPU is **$(f1(cpuT[end] / A[Nmax][:t_pipe]))×** the
        $Tmax-task CPU on the device and **$(f1(cpuT[end] / (A[Nmax][:t_pipe] + B[MAIN_N in keys(B) ? MAIN_N : SIZES[end]][:t_h2d])))×** once the host-to-device copy is added.
        The per-indicator GPU kernel, one launch per 32 indicators, costs $(ms(g1_per_group)) ms per group on this corpus: measured
        $(join(["$(ms(A[N][:t_g1])) ms at $(commas(N))" for N in g1_N], ", ")), i.e. **$(f2(g1_pred_max)) s predicted at $(commas(Nmax))**, $(f0(g1_pred_max / A[Nmax][:t_pipe]))× the hash-set pipeline.
        The same hash-set match without the token compaction (one thread per byte, hits appended with an atomic
        counter) takes $(ms(A[Nmax][:t_pdir])) ms instead of $(ms(A[Nmax][:t_pipe])) ms at $(commas(Nmax)) (kernel alone $(ms(A[Nmax][:t_hd])) ms against
        token scan + hash match $(ms(A[Nmax][:t_ts] + A[Nmax][:t_hg])) ms): $(A[Nmax][:t_pdir] < A[Nmax][:t_pipe] ? "the compaction costs more than it saves here, because only about one byte in five starts a token and the scan moves 8 bytes per corpus byte" : "the compaction pays off here: the one-thread-per-byte kernel loses more to divergence (lanes walking tokens of different lengths, most lanes idle) than the scan costs").

        ## 2. Scaling with the list size

        The hash-set pipeline is flat in the list size by construction (one pass over the corpus, one hash per
        token, probes independent of N while the load stays ≤ 0.5): measured $(f2(g2_max / g2_min))× between its slowest and
        fastest list size, with $(f2(minimum(A[N][:probes] for N in LISTS)))–$(f2(maximum(A[N][:probes] for N in LISTS))) probes per token.  The list enters only through the table
        footprint ($(f1(A[Nmin][:table_bytes] / 1024)) KB at $(commas(Nmin)) to $(f1(A[Nmax][:table_bytes] / 1024)) KB at $(commas(Nmax))$(l2_bytes == 0 ? "" : ", against $(l2_bytes ÷ 1024) KB of L2")); the hash kernel alone
        went from $(ms(A[Nmin][:t_hg])) ms to $(ms(A[Nmax][:t_hg])) ms.  $hs_txt
        The per-indicator kernel grows linearly with the number of groups, as its cost model says: $cross_txt.
        The tuned CPU matcher is also flat in N ($(f3(cpu1[1]))–$(f3(cpu1[end])) s with one task, $(f3(cpuT[1]))–$(f3(cpuT[end])) s with $Tmax); the library route
        (`occursin` per indicator) grows linearly and is $(isnan(A[LISTS[1]][:t_c2]) ? "n/a" : f1(A[LISTS[1]][:t_c2] / A[LISTS[1]][:cpu_t1]))× slower than the hash-set matcher already at $(commas(LISTS[1])) indicators.

        ## 3. Where the time goes and the limiter

        Shares of the GPU pipeline at $(commas(MAIN_N)) lines and $(commas(b1[:N])) indicators, each step timed on its own: line table
        $(pct(b1[:t_lt] / b1[:t_pipe])), token scan $(pct(b1[:t_ts] / b1[:t_pipe])), hash match $(pct(b1[:t_hg] / b1[:t_pipe])), extraction $(pct(b1[:t_ex] / b1[:t_pipe])) (end to end
        $(ms(b1[:t_pipe])) ms).  The largest step is $(largest[1]) ($(pct(largest[2] / b1[:t_pipe]))).  The two scan steps read and write a 4-byte
        flag per corpus byte (the lecture-7 scan on `UInt32` flags), so they move about 8 bytes per corpus byte against
        the 1 byte the hash kernel reads; the hash kernel itself reads every token once ($(commas(ntok_main)) tokens,
        $(f1(nbytes / ntok_main)) bytes each on average), hashes it and probes the table $(f2(b1[:probes])) times on average.  Its
        achieved rate, $(f1(gbps(nbytes, b1[:t_hg]))) GB/s of corpus against a copy rate of $(f1(copy_bw)) GB/s, says it is bound by the
        per-token work (a serial byte walk and a data-dependent probe per thread, $(pc.bra) branches in the PTX) and not by
        bandwidth; `CUDA.registers` $(fmt_opt(get(res_h, :registers, nothing))) per thread, occupancy $(get(res_h, :occupancy, nothing) === nothing ? "n/a" : pct(res_h[:occupancy])).
        The limiter of the whole pipeline is therefore the scan traffic, which does not depend on the list, which is
        exactly why the pipeline is flat in N.

        ## 4. The data rate: when the GPU is needed and how long it keeps up

        $(md_table(["lines", "GPU pipeline (MB/s)", "GPU direct pipeline (MB/s)", "+ H2D (MB/s)", "CPU $Tmax tasks (MB/s)", "CPU 1 task (MB/s)", "H2D / pipeline"],
                   [(commas(nl), f1(mbps(B[nl][:n], B[nl][:t_pipe])), f1(mbps(B[nl][:n], B[nl][:t_pdir])), f1(mbps(B[nl][:n], B[nl][:t_pipe] + B[nl][:t_h2d])),
                     f1(mbps(B[nl][:n], B[nl][Symbol("cpu_t", Tmax)])), f1(mbps(B[nl][:n], B[nl][:cpu_t1])), f2(B[nl][:t_h2d] / B[nl][:t_pipe])) for nl in SIZES]))
        With a list of $(commas(Nb)) indicators the tuned CPU keeps up with **$(f1(R_cpu / 1e6)) MB/s** on $Tmax tasks ($(f1(R_cpu1 / 1e6)) MB/s per task,
        $(vol(R_cpu * day))); above that rate a GPU is needed, and one GPU keeps up with **$(f1(R_gpu_h2d / 1e6)) MB/s** including the pageable
        copy ($(f1(R_gpu / 1e6)) MB/s with the logs already on the device; $(vol(R_gpu_h2d * day))).  The host-to-device copy costs
        $(f2(big[:t_h2d] / big[:t_pipe]))× the pipeline at $(commas(SIZES[end])) lines$(isnan(big[:t_h2d_pin]) ? "" : " ($(f1(gbps(big[:n], big[:t_h2d]))) GB/s pageable, $(f1(gbps(big[:n], big[:t_h2d_pin]))) GB/s pinned)"): the transfer
        $(big[:t_h2d] > big[:t_pipe] ? "is the wall: the copy, not the kernels, sets the end-to-end rate" : "is not the wall yet; the kernels still set the end-to-end rate").
        One GPU replaces about **$(f0(R_gpu_h2d / R_cpu1)) CPU tasks** of this host at this list size (and the same at $(commas(Nmax)), since neither side depends on N).

        ## 5. The defensive conclusion

        A per-indicator scan is only viable for small lists: on this GPU it costs $(ms(g1_per_group)) ms per 32 indicators and
        $(commas(MAIN_N)) lines, so a threat feed of $(commas(Nmax)) entries would take $(f2(g1_pred_max)) s per $(commas(MAIN_N)) lines, $(f0(g1_pred_max / A[Nmax][:t_pipe]))× the
        hash-set method; a list-independent method (hash set of whole tokens, or an automaton for substring
        semantics) is required for a real feed.  With it, the list size is free: a SOC can match $(commas(Nmax))
        indicators at the same rate as $(commas(Nmin)).  Sizing for $(commas(Nmax)) indicators: one CPU task of this host handles
        $(vol(R_cpu1 * day)), $Tmax tasks $(vol(R_cpu * day)), one GPU $(vol(R_gpu_h2d * day)) with the copy; the GPU is the right tool when the
        daily volume exceeds what the available cores cover, and only if the logs reach it faster than
        $(f1(R_gpu_h2d / 1e6)) MB/s (storage or network), otherwise the storage is the limit.  Limits: synthetic logs; whole-token
        semantics (no substrings, no regular expressions); cold indicators never hit (the hit count is constant);
        the CPU baseline is $Tmax tasks on $(Sys.CPU_THREADS) hardware threads of a shared host; one GPU session; no real logs
        (course policy).
        """
        write(joinpath(RESULTS_DIR, "analysis.md"), analysis)
        println("\nResults written to $BENCH_FILE and $(joinpath(RESULTS_DIR, "analysis.md"))")

        if get(ENV, "RP_NO_PLOTS", "0") != "1"
            try
                include("rp_plots.jl")
                make_plots(RESULTS_DIR, THREADS)
                println("Plots written to $RESULTS_DIR")
            catch err
                println("Plots not drawn (", first(sprint(showerror, err), 200), "); the data is in results/*.csv")
            end
        end
    end
end
