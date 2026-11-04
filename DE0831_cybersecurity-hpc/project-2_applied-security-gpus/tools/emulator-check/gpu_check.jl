using CUDA
const STUDENT_CARD = "251ADM047"; const STUDENT_NAME = "Vagif Asgarli"
const SRC = ARGS[1]; const N = parse(Int, ARGS[2])
include(joinpath(SRC, "p2_common.jl")); include(joinpath(SRC, "p2_data.jl"))
include(joinpath(SRC, "p2_cpu.jl")); include(joinpath(SRC, "p2_gpu.jl"))
const SEED = student_seed(STUDENT_CARD)

corpus = load_corpus(N); inds = load_indicators(N); truth = load_truth(N); etruth = load_entropy_truth(N)
println("corpus $(length(corpus)) B, $(length(inds)) indicators, truth $(length(truth)), entropy truth $(length(etruth))")
pt = PatternTable(inds); dp = DevicePatterns(pt)
corpus_d = CuVector(corpus)

t = @elapsed r = gpu_pipeline(corpus_d, dp)
println("pipeline ran in $(round(t, digits=1)) s (emulator)")

# 1. line table
ls_cpu = cpu_line_starts(corpus)
ls_gpu = Array(r.line_start)
require(ls_gpu == ls_cpu, "line table (gpu $(length(ls_gpu)) vs cpu $(length(ls_cpu)))")
println("line table OK: $(nlines_of(ls_cpu)) lines")

# 2. match set vs truth and vs CPU
mask_gpu = Array(r.line_mask)
mask_cpu = cpu_match(corpus, pt, ls_cpu)
require(mask_gpu == mask_cpu, "line mask gpu == cpu")
mset = match_set(mask_gpu, inds)
require(mset == truth, "match set == truth (gpu $(length(mset)), truth $(length(truth)), missing $(length(setdiff(truth, mset))), extra $(length(setdiff(mset, truth))))")
println("match set OK: $(length(mset)) (line, indicator) pairs")

# 2b. global-memory variant gives the same mask
line_mask2 = CUDA.zeros(UInt32, length(ls_cpu) - 1)
launch_match!(line_mask2, corpus_d, dp, r.line_start; variant = :global)
require(Array(line_mask2) == mask_cpu, "match_global! == cpu")
println("match_global! OK")

# 3. extracted lines
lines = corpus_lines(corpus, ls_cpu)
matched = Array(r.matched)
require(matched == findall(!=(0), mask_cpu), "matched line numbers")
got = unpack_lines(Array(r.packed), Array(r.off), Array(r.len))
require(got == lines[matched], "extracted line text")
println("extraction OK: $(length(got)) lines, $(length(r.packed)) bytes")

# 4. tokens and entropies
ts_cpu = cpu_token_starts(corpus)
ts_gpu = Array(r.token_start)
require(ts_gpu == ts_cpu, "token starts (gpu $(length(ts_gpu)) vs cpu $(length(ts_cpu)))")
H_cpu, L_cpu = cpu_token_entropies(corpus, ts_cpu)
H_gpu = Array(r.H); L_gpu = Array(r.L)
require(L_gpu == L_cpu, "token lengths")
require(maximum(abs.(H_gpu .- Float32.(H_cpu))) < 1e-4, "token entropies gpu vs cpu (max diff $(maximum(abs.(H_gpu .- Float32.(H_cpu)))))")
println("tokens OK: $(length(ts_gpu)) tokens, max |H_gpu - H_cpu| = $(maximum(abs.(H_gpu .- Float32.(H_cpu))))")

# 5. histogram, threshold, flagged vs truth
require(sum(r.hist) == length(ts_gpu), "histogram total")
println("threshold chosen from the histogram: $(round(r.threshold, digits=3)) (empty band $(r.band))")
flagged = Array(r.flagged)
fl = Set((line_of(ls_cpu, ts_gpu[k]), String(corpus[ts_gpu[k]:ts_gpu[k] + L_gpu[k] - 1])) for k in flagged)
truthset = Set((l, t) for (l, t, _) in etruth)
require(fl == truthset, "flagged tokens == entropy truth (flagged $(length(fl)), truth $(length(truthset)))")
# entropy values of the truth tokens
tokidx = Dict{Tuple{Int,String},Int}((line_of(ls_cpu, ts_gpu[k]), String(corpus[ts_gpu[k]:ts_gpu[k] + L_gpu[k] - 1])) => k for k in flagged)
maxdiff = maximum(abs(H_gpu[tokidx[(l, t)]] - h) for (l, t, h) in etruth)
require(maxdiff < 1e-3, "entropy values vs truth (max diff $maxdiff)")
println("entropy flagging OK: $(length(fl)) tokens, max |H - truth| = $(round(maxdiff, digits=6))")

# 6. hand-made small cases
function small_case(text, patterns; expect)
    c = Vector{UInt8}(codeunits(text)); pt2 = PatternTable(patterns); dp2 = DevicePatterns(pt2)
    r2 = gpu_pipeline(CuVector(c), dp2; threshold = 5.0)
    ls2 = cpu_line_starts(c)
    require(Array(r2.line_start) == ls2, "small case line table: $(repr(text))")
    got2 = match_set(Array(r2.line_mask), patterns)
    require(got2 == Set(expect), "small case $(repr(text)): got $got2, expected $expect")
    require(Array(r2.line_mask) == cpu_match(c, pt2, ls2), "small case cpu == gpu: $(repr(text))")
end
small_case("", ["abc"]; expect = [])
small_case("abc", ["abc"]; expect = [(1, "abc")])                               # no trailing newline, at byte 1
small_case("x abc\nabc y\n", ["abc"]; expect = [(1, "abc"), (2, "abc")])
small_case("abcd\nxabc\nab\n", ["abc"]; expect = [])                            # substrings of longer words
small_case("a.b\n192.0.2.24 x\n192.0.2.248\n", ["192.0.2.24", "192.0.2.248"]; expect = [(2, "192.0.2.24"), (3, "192.0.2.248")])
small_case("one two\nthree one two\n", ["one", "two"]; expect = [(1, "one"), (1, "two"), (2, "one"), (2, "two")])
# patterns crossing the tile boundary (tile = 1024 bytes)
pad = "x"^(MATCH_TILE - 3)
small_case(pad * " abcdef " * "y"^20 * "\n", ["abcdef"]; expect = [(1, "abcdef")])   # starts 3 bytes before the tile edge
small_case("y"^(MATCH_TILE - 1) * " abcdef\n", ["abcdef"]; expect = [(1, "abcdef")])  # starts exactly at the tile edge
small_case("y"^(MATCH_TILE - 7) * " abcdef\n", ["abcdef"]; expect = [(1, "abcdef")])  # ends exactly at the tile edge
small_case("abc\n" * "z"^MATCH_TILE * " abc", ["abc"]; expect = [(1, "abc"), (2, "abc")])  # last byte of the corpus
small_case("abc\n" * "z"^MATCH_TILE * "abc", ["abc"]; expect = [(1, "abc")])               # glued to a word: no match
println("small cases OK")
println("Correct!")
