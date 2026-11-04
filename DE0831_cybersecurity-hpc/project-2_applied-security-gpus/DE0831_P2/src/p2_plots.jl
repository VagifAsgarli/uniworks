# p2_plots.jl - the plots of the measurement study, drawn in Julia with
# CairoMakie (works headless) from the CSV files that p2_run.jl writes.

using CairoMakie
using DelimitedFiles

"Read a CSV with a header line into (header, matrix of Float64)."
function read_csv(path)
    raw = readdlm(path, ',', String)
    return String.(raw[1, :]), parse.(Float64, raw[2:end, :])
end

function make_plots(results_dir, threshold)
    hdr, M = read_csv(joinpath(results_dir, "timings.csv"))
    col(name) = M[:, findfirst(==(name), hdr)]
    lines_ = col("lines"); bytes = col("bytes")
    mbps(t) = bytes ./ t ./ 1e6

    # 1. throughput vs corpus size
    sizelabel(n) = n >= 1e6 ? string(round(n / 1e6; digits = 2), "M") : string(round(Int, n / 1e3), "k")
    f = Figure(size = (1000, 500))
    ax = Axis(f[1, 1]; xlabel = "corpus size (lines)", ylabel = "throughput (MB/s)", xscale = log10, yscale = log10,
              xticks = (lines_, sizelabel.(lines_)), title = "Track E: throughput against corpus size")
    series = [("match kernel (GPU)", mbps(col("match_tiled_s"))),
              ("GPU pipeline", mbps(col("pipeline_s"))),
              ("GPU pipeline + host-to-device copy", mbps(col("pipeline_s") .+ col("h2d_s"))),
              ("CPU pipeline, one core", mbps(col("cpu_pipeline_s"))),
              ("CPU match, one core", mbps(col("cpu_match_s")))]
    for (label, y) in series
        scatterlines!(ax, lines_, y; label)
    end
    Legend(f[1, 2], ax)
    save(joinpath(results_dir, "throughput_vs_size.png"), f; px_per_unit = 2)

    # 2. time breakdown at every size (stacked)
    steps = [("line table", "line_table_s"), ("match (tiled)", "match_tiled_s"), ("extraction", "extract_s"),
             ("token starts", "token_starts_s"), ("token entropy", "entropy_s"), ("histogram + flags", nothing),
             ("host-to-device copy", "h2d_s")]
    f2 = Figure(size = (900, 500))
    ax2 = Axis(f2[1, 1]; xlabel = "corpus size (lines)", ylabel = "time (ms)", title = "Where the time goes",
               xticks = (1:length(lines_), string.(round.(Int, lines_))))
    xs = Int[]; ys = Float64[]; grp = Int[]
    for (i, _) in enumerate(lines_)
        for (g, (label, c)) in enumerate(steps)
            v = c === nothing ? (col("hist_s")[i] + col("flag_s")[i]) : col(c)[i]
            push!(xs, i); push!(ys, v * 1e3); push!(grp, g)
        end
    end
    barplot!(ax2, xs, ys; stack = grp, color = grp, colormap = :tab10, colorrange = (1, 10))
    Legend(f2[1, 2], [PolyElement(color = Makie.cgrad(:tab10, 10; categorical = true)[g]) for g in 1:length(steps)],
           first.(steps))
    save(joinpath(results_dir, "time_breakdown.png"), f2; px_per_unit = 2)

    # 3. entropy distribution with the threshold
    hh, Hm = read_csv(joinpath(results_dir, "entropy_hist.csv"))
    f3 = Figure(size = (900, 450))
    ax3 = Axis(f3[1, 1]; xlabel = "token entropy (bits/char)", ylabel = "tokens (log scale)", yscale = log10,
               title = "Token entropy distribution and the chosen threshold")
    cnt = Hm[:, 2]; lo = Hm[:, 1]
    keep = cnt .> 0
    barplot!(ax3, lo[keep] .+ 0.025, cnt[keep]; width = 0.05, color = (:steelblue, 0.8))
    vlines!(ax3, [threshold]; color = :red, linestyle = :dash, label = "threshold $(round(threshold, digits = 2))")
    axislegend(ax3; position = :rt)
    save(joinpath(results_dir, "entropy_distribution.png"), f3; px_per_unit = 2)

    # 4. precision and recall against the threshold
    th, T = read_csv(joinpath(results_dir, "threshold_table.csv"))
    f4 = Figure(size = (700, 450))
    ax4 = Axis(f4[1, 1]; xlabel = "threshold (bits/char)", ylabel = "precision / recall", title = "Flagging quality against the threshold")
    scatterlines!(ax4, T[:, 1], T[:, 6]; label = "precision")
    scatterlines!(ax4, T[:, 1], T[:, 7]; label = "recall")
    vlines!(ax4, [threshold]; color = :red, linestyle = :dash, label = "chosen $(round(threshold, digits = 2))")
    axislegend(ax4; position = :lb)
    save(joinpath(results_dir, "threshold_precision_recall.png"), f4; px_per_unit = 2)
    return nothing
end
