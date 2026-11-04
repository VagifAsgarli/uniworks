# Runs src/p2_run.jl in validation-only mode in a separate Julia process and
# checks that it prints "Correct!".  The script validates the GPU results
# against the CPU baseline and the generator's ground truth over the whole
# corpus (line table, match set, extracted lines, tokens, entropies,
# flagging) plus the hand-made boundary cases, and throws if any check fails.
#
# P2_MAIN=<lines> picks the corpus (default 1,000,000; the generator runs if
# the files are missing).  P2_QUICK=0 includes the benchmarks.

using Test

const ROOT  = normpath(joinpath(@__DIR__, ".."))
const QUICK = get(ENV, "P2_QUICK", "1")

@testset "DE0831 Project 2, track E" begin
    script = joinpath(ROOT, "src", "p2_run.jl")
    cmd    = addenv(`$(Base.julia_cmd()) --project=$ROOT $script`, "P2_QUICK" => QUICK)
    output = try
        read(cmd, String)
    catch err
        @error "p2_run.jl failed" exception = err
        ""
    end
    print(output)
    @test occursin("Correct!", output)
end
