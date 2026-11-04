# rp_data.jl - data for the research project: the course log corpus from the
# handout generator (src/gen_logs.jl, unchanged, run with the student ID) and
# the indicator lists of growing size, built deterministically from the same
# seed.
#
# Lists: for N <= 20 a subset of the generator's 20 indicators; for N > 20 the
# 20 plus N - 20 synthetic "cold" indicators in the same two forms (addresses
# from the RFC 2544 benchmarking range 198.18.0.0/15 and DGA-style `.invalid`
# hostnames), which cannot occur in the corpus (its addresses come from the
# three RFC 5737 ranges, its hostnames are app1-9.invalid and the 8 planted
# domains).  So the ground truth of every list is the generator's truth
# restricted to the list, and the list size is the only thing that changes.

using SHA, Random

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

"Corpus sizes (lines) of the data-rate sweep; RP_SIZES overrides them."
function corpus_sizes()
    s = get(ENV, "RP_SIZES", "")
    isempty(s) && return [125_000, 250_000, 500_000, 1_000_000, 2_000_000, 4_000_000]
    return parse.(Int, split(s, ","))
end

"Indicator-list sizes of the list sweep; RP_LISTS overrides them."
function list_sizes()
    s = get(ENV, "RP_LISTS", "")
    isempty(s) && return [10, 30, 100, 300, 1_000, 3_000, 10_000]
    return parse.(Int, split(s, ","))
end

"Directory holding the generated files for one corpus size."
size_dir(nlines) = joinpath(DATA_DIR, "lines_$(nlines)")

corpus_path(nlines)     = joinpath(size_dir(nlines), "corpus_$(STUDENT_CARD).log")
indicators_path(nlines) = joinpath(size_dir(nlines), "indicators_$(STUDENT_CARD).txt")
truth_path(nlines)      = joinpath(size_dir(nlines), "truth_$(STUDENT_CARD).csv")

"""
Run the handout generator for `nlines` lines unless its files exist.  The
generator is executed in a separate Julia process exactly as the brief says
(`julia gen_logs.jl <ID> --lines N --out DIR`).
"""
function ensure_corpus(nlines)
    dir = size_dir(nlines)
    files = (corpus_path(nlines), indicators_path(nlines), truth_path(nlines))
    all(isfile, files) && return dir
    mkpath(dir)
    gen = joinpath(@__DIR__, "gen_logs.jl")
    println("Generating $(commas(nlines)) lines with gen_logs.jl into $dir ...")
    run(`$(Base.julia_cmd()) --startup-file=no $gen $STUDENT_CARD --lines $nlines --out $dir`)
    all(isfile, files) || error("generator did not produce the expected files in $dir")
    return dir
end

"The corpus as one flat byte vector."
load_corpus(nlines) = (ensure_corpus(nlines); read(corpus_path(nlines)))

"The generator's indicators (12 addresses, 8 domains), in file order."
load_indicators(nlines) = (ensure_corpus(nlines); String.(filter(!isempty, strip.(readlines(indicators_path(nlines))))))

"The generator's ground truth as a set of (line, indicator) pairs."
function load_truth(nlines)
    ensure_corpus(nlines)
    s = Set{Tuple{Int,String}}()
    for (k, l) in enumerate(eachline(truth_path(nlines)))
        k == 1 && continue                       # header
        a, b = split(l, ',')
        push!(s, (parse(Int, a), String(b)))
    end
    return s
end

"Is the indicator an address (digits and dots) rather than a hostname?"
is_address(s::AbstractString) = all(c -> isdigit(c) || c == '.', s)

"""
The indicator list of size N: a subset of the generator's `base` indicators
for N <= length(base) (addresses first, then domains, about 60 % addresses),
otherwise the whole base followed by N - length(base) synthetic cold
indicators.  Deterministic in (seed, N).
"""
function indicator_list(N::Integer, base::Vector{String}; seed::Integer = SEED)
    N >= 1 || error("list size must be positive")
    ips  = filter(is_address, base)
    doms = filter(!is_address, base)
    if N <= length(base)
        na = min(length(ips), round(Int, 0.6N)); nd = min(length(doms), N - na)
        na = N - nd                                   # if domains are short, take more addresses
        return vcat(ips[1:na], doms[1:nd])
    end
    rng  = MersenneTwister(UInt64(seed) ⊻ (UInt64(N) * 0x9E3779B97F4A7C15))
    seen = Set(base); cold = String[]
    while length(cold) < N - length(base)
        s = rand(rng) < 0.6 ? "198.18.$(rand(rng, 0:255)).$(rand(rng, 1:254))" :
                              String(rand(rng, 'a':'z', rand(rng, 12:20))) * ".invalid"
        s in seen && continue
        push!(seen, s); push!(cold, s)
    end
    return vcat(base, cold)
end

"The ground truth restricted to a list: the (line, indicator) pairs whose indicator is in the list."
function truth_for_list(truth::Set{Tuple{Int,String}}, list::Vector{String})
    inlist = Set(list)
    return Set(p for p in truth if p[2] in inlist)
end
