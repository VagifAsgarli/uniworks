# Runs src/rp_run.jl in validation-only mode in a separate Julia process and
# checks that it prints "Correct!": every method (CPU hash-set matcher with 1
# and more tasks, occursin, GPU hash-set matcher with global table and shared
# keys, GPU per-indicator matcher) must produce the ground truth on the main
# corpus for every list size, plus the hand-made cases.
#
# RP_MAIN=<lines> picks the corpus (default 1,000,000; the generator runs if
# the files are missing).  RP_QUICK=0 includes the benchmarks.

using Test

const ROOT  = normpath(joinpath(@__DIR__, ".."))
const QUICK = get(ENV, "RP_QUICK", "1")

@testset "DE0831 research project, topic 10" begin
    script = joinpath(ROOT, "src", "rp_run.jl")
    cmd    = addenv(`$(Base.julia_cmd()) -t auto --project=$ROOT $script`, "RP_QUICK" => QUICK)
    output = try
        read(cmd, String)
    catch err
        @error "rp_run.jl failed" exception = err
        ""
    end
    print(output)
    @test occursin("Correct!", output)
end
