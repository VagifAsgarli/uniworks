# rp_plots.jl - the plots of the study, drawn in Julia with CairoMakie (works
# headless) from the CSV files that rp_run.jl writes.

using CairoMakie
using DelimitedFiles

function read_csv(path)
    raw = readdlm(path, ',', String)
    return String.(raw[1, :]), parse.(Float64, raw[2:end, :])
end
sizelabel(n) = n >= 1e6 ? string(round(n / 1e6; digits = 2), "M") : n >= 1e3 ? string(round(Int, n / 1e3), "k") : string(round(Int, n))

function make_plots(results_dir, threads)
    Tmax = maximum(threads)
    hdr, M = read_csv(joinpath(results_dir, "list_sweep.csv"))
    col(name) = M[:, findfirst(==(name), hdr)]
    N = col("N")
    lines_main = nothing
    # the corpus size of the list sweep is not in the CSV: lines/s uses the size sweep's "lines" of the main row
    hdr2, M2 = read_csv(joinpath(results_dir, "size_sweep.csv"))
    col2(name) = M2[:, findfirst(==(name), hdr2)]

    # 1. lines/s against the list size (the main plot)
    main_lines = parse(Float64, get(ENV, "RP_MAIN", "1000000"))
    rate(t) = main_lines ./ t ./ 1e6
    f = Figure(size = (1000, 520))
    ax = Axis(f[1, 1]; xlabel = "indicators in the list", ylabel = "million lines / s", xscale = log10, yscale = log10,
              xticks = (N, sizelabel.(N)), title = "Log indicator matching: rate against the list size (1M lines)")
    series = [("GPU hash-set pipeline", rate(col("pipeline_s"))),
              ("GPU hash-match kernel alone", rate(col("hash_global_s"))),
              ("GPU per-indicator (Project 2 kernel, per 32)", rate(col("g1_s"))),
              ("CPU hash-set, $Tmax tasks", rate(col("cpu_t$(Tmax)_s"))),
              ("CPU hash-set, 1 task", rate(col("cpu_t1_s"))),
              ("CPU occursin per indicator", rate(col("occursin_s")))]
    for (label, y) in series
        keep = .!isnan.(y)
        any(keep) && scatterlines!(ax, N[keep], y[keep]; label)
    end
    Legend(f[1, 2], ax)
    save(joinpath(results_dir, "rate_vs_list.png"), f; px_per_unit = 2)

    # 2. GPU pipeline breakdown against the list size
    steps = [("line table", "line_table_s"), ("token scan", "token_starts_s"), ("hash match", "hash_global_s"), ("extraction", "extract_s")]
    f2 = Figure(size = (900, 500))
    ax2 = Axis(f2[1, 1]; xlabel = "indicators in the list", ylabel = "time (ms)", title = "GPU hash-set pipeline: where the time goes (1M lines)",
               xticks = (1:length(N), sizelabel.(N)))
    xs = Int[]; ys = Float64[]; grp = Int[]
    for i in eachindex(N), (g, (_, c)) in enumerate(steps)
        push!(xs, i); push!(ys, col(c)[i] * 1e3); push!(grp, g)
    end
    barplot!(ax2, xs, ys; stack = grp, color = grp, colormap = :tab10, colorrange = (1, 10))
    Legend(f2[1, 2], [PolyElement(color = Makie.to_colormap(:tab10)[g]) for g in 1:length(steps)], first.(steps))
    save(joinpath(results_dir, "breakdown_vs_list.png"), f2; px_per_unit = 2)

    # 3. MB/s against the corpus size (the data-rate question)
    lines_ = col2("lines"); bytes = col2("bytes")
    mbps(t) = bytes ./ t ./ 1e6
    f3 = Figure(size = (1000, 500))
    ax3 = Axis(f3[1, 1]; xlabel = "corpus size (lines)", ylabel = "MB/s", xscale = log10, yscale = log10,
               xticks = (lines_, sizelabel.(lines_)), title = "Data rate against the corpus size (list of $(sizelabel(parse(Float64, get(ENV, "RP_SIZE_LIST", "1000")))) indicators)")
    for (label, y) in [("GPU pipeline", mbps(col2("pipeline_s"))),
                       ("GPU pipeline + host-to-device copy", mbps(col2("pipeline_s") .+ col2("h2d_s"))),
                       ("CPU hash-set, $Tmax tasks", mbps(col2("cpu_t$(Tmax)_s"))),
                       ("CPU hash-set, 1 task", mbps(col2("cpu_t1_s")))]
        scatterlines!(ax3, lines_, y; label)
    end
    Legend(f3[1, 2], ax3)
    save(joinpath(results_dir, "rate_vs_size.png"), f3; px_per_unit = 2)

    # 4. CPU tasks scaling at the list size of the corpus sweep
    Nt = N[argmin(abs.(N .- parse(Float64, get(ENV, "RP_SIZE_LIST", "1000"))))]
    i = findfirst(==(Nt), N)
    f4 = Figure(size = (600, 420))
    ax4 = Axis(f4[1, 1]; xlabel = "Julia tasks", ylabel = "million lines / s", xticks = threads,
               title = "CPU hash-set matcher: tasks (1M lines, $(sizelabel(Nt)) indicators)")
    barplot!(ax4, threads, [rate(col("cpu_t$(T)_s"))[i] for T in threads]; color = :steelblue)
    save(joinpath(results_dir, "cpu_threads.png"), f4; px_per_unit = 2)
    return nothing
end
