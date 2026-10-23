# Runs every exercise script end to end in its own Julia process and checks
# that it completes and prints "Correct!".  Each script performs its own
# validation against a CPU reference (including the boundary sizes
# N ∈ {1, 31, 32, 33, 255, 256, 257} for exercises 1 and 4) and throws if any
# check fails.
#
# By default the benchmarks are skipped (P1_QUICK=1); run with P1_QUICK=0 to
# include them:   P1_QUICK=0 julia --project=. test/runtests.jl

using Test

const ROOT  = normpath(joinpath(@__DIR__, ".."))
const QUICK = get(ENV, "P1_QUICK", "1")

@testset "DE0831 Project 1" begin
    for ex in 1:4
        script = joinpath(ROOT, "src", "p1_ex$ex.jl")
        @testset "p1_ex$ex.jl" begin
            cmd    = addenv(`$(Base.julia_cmd()) --project=$ROOT $script`, "P1_QUICK" => QUICK)
            output = try
                read(cmd, String)
            catch err
                @error "p1_ex$ex.jl failed" exception = err
                ""
            end
            print(output)
            @test occursin("Correct!", output)
        end
    end
end
