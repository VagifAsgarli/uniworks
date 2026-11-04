# p2_data.jl - the individualised data for track E: calls the handout
# generator (src/gen_logs.jl, unchanged) for every corpus size and loads the
# corpus, the indicator set and the two ground-truth files.
#
# Everything is derived from the student card number: the generator hashes it
# with SHA-256 into the RNG seed, so the grader can regenerate the same data.

using SHA

"""
The generator's seed for a student ID: a numeric ID is its own seed, an RTU ID
such as 251ADM047 is hashed with SHA-256 (the first 8 bytes, big-endian).
Copied from gen_logs.jl so that the header block can print the derived value.
"""
function student_seed(id::AbstractString)
    n = tryparse(Int, id)
    n !== nothing && return n
    foldl((a, b) -> (a << 8) | b, UInt64.(sha256(id)[1:8]))
end

"Corpus sizes (lines) for the measurement study; P2_SIZES overrides them."
function corpus_sizes()
    s = get(ENV, "P2_SIZES", "")
    isempty(s) && return [125_000, 250_000, 500_000, 1_000_000, 2_000_000, 4_000_000]
    return parse.(Int, split(s, ","))
end

"Directory holding the generated files for one corpus size."
size_dir(nlines) = joinpath(DATA_DIR, "lines_$(nlines)")

corpus_path(nlines)  = joinpath(size_dir(nlines), "corpus_$(STUDENT_CARD).log")
indicators_path(nlines) = joinpath(size_dir(nlines), "indicators_$(STUDENT_CARD).txt")
truth_path(nlines)   = joinpath(size_dir(nlines), "truth_$(STUDENT_CARD).csv")
etruth_path(nlines)  = joinpath(size_dir(nlines), "entropy_truth_$(STUDENT_CARD).csv")

"""
Run the handout generator for `nlines` lines unless its four files exist.
The generator is executed in a separate Julia process exactly as the brief
says (`julia gen_logs.jl <ID> --lines N --out DIR`).
"""
function ensure_corpus(nlines)
    files = (corpus_path(nlines), indicators_path(nlines), truth_path(nlines), etruth_path(nlines))
    all(isfile, files) && return files
    dir = size_dir(nlines)
    mkpath(dir)
    gen = joinpath(@__DIR__, "gen_logs.jl")
    println("Generating $(commas(nlines)) lines with gen_logs.jl into $dir ...")
    run(`$(Base.julia_cmd()) --startup-file=no $gen $STUDENT_CARD --lines $nlines --out $dir`)
    all(isfile, files) || error("generator did not produce the expected files in $dir")
    return files
end

"The corpus as a flat byte vector (the memory layout the kernels use)."
load_corpus(nlines) = read(corpus_path(nlines))

"The indicator strings, in file order (pattern p = line p of the file)."
load_indicators(nlines) = String.(filter(!isempty, strip.(readlines(indicators_path(nlines)))))

"""
Ground truth for matching: the set of (line number, indicator) pairs.  A line
may carry one indicator in the generated data, but the set form also works if
it carried several.
"""
function load_truth(nlines)
    s = Set{Tuple{Int,String}}()
    for (k, row) in enumerate(eachline(truth_path(nlines)))
        k == 1 && continue                      # header
        isempty(strip(row)) && continue
        line, ind = split(row, ",")
        push!(s, (parse(Int, line), String(strip(ind))))
    end
    return s
end

"Ground truth for entropy flagging: vector of (line, token, entropy)."
function load_entropy_truth(nlines)
    out = Tuple{Int,String,Float64}[]
    for (k, row) in enumerate(eachline(etruth_path(nlines)))
        k == 1 && continue
        isempty(strip(row)) && continue
        line, tok, h = split(row, ",")
        push!(out, (parse(Int, line), String(tok), parse(Float64, h)))
    end
    return out
end
