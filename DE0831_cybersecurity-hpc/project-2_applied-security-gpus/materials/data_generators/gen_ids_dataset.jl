#!/usr/bin/env julia
# DE0831 Project 2, track D: synthetic network-flow dataset for intrusion detection.
#
# Entirely synthetic. No traffic is captured from any real network, and no record
# corresponds to a real host or person. Class balance deliberately mirrors reality:
# attacks are rare, so accuracy is a useless metric and precision/recall are not.
#
#   julia gen_ids_dataset.jl 123456 [--train 300000] [--test 75000] [--out .]
#
# Writes train_<ID>.csv, test_<ID>.csv (12 features + label), and a summary.

using Random, Printf, SHA

"""
Seed for a student ID. A numeric ID is its own seed, so `123456` gives the same data as
before; an RTU ID such as `251ADM055` is hashed with SHA-256, which is stable across
Julia versions (unlike `hash`).
"""
function student_seed(id::AbstractString)
    n = tryparse(Int, id)
    n !== nothing && return n
    foldl((a, b) -> (a << 8) | b, UInt64.(sha256(id)[1:8]))
end

const FEATURES = ["duration","src_bytes","dst_bytes","src_pkts","dst_pkts","pkt_rate",
                  "byte_ratio","syn_ratio","rst_ratio","distinct_ports","iat_mean","iat_std"]

# label => (weight, per-feature (mean, sd) in log/linear space as appropriate)
const CLASSES = Dict(
  "benign"      => (0.9880, [ 2.4 0.9; 6.5 1.4; 7.4 1.5; 2.6 0.8; 2.9 0.9; 1.6 0.7;
                              0.0 0.6; 0.10 0.06; 0.02 0.02; 1.0 0.6; 1.2 0.8; 0.9 0.6]),
  "dos"         => (0.0055, [ 0.6 0.7; 3.2 0.9; 1.0 0.8; 6.5 1.0; 0.8 0.6; 6.2 0.8;
                              2.2 0.7; 0.85 0.10; 0.30 0.12; 0.3 0.3;-1.8 0.6; 0.2 0.3]),
  "probe"       => (0.0035, [ 0.3 0.5; 1.6 0.7; 0.9 0.7; 1.4 0.6; 0.9 0.5; 3.4 0.9;
                              0.6 0.6; 0.55 0.15; 0.60 0.15; 4.2 0.7;-0.9 0.7; 1.6 0.6]),
  "bruteforce"  => (0.0020, [ 3.1 0.8; 4.6 0.8; 4.2 0.8; 4.0 0.7; 3.8 0.7; 2.9 0.7;
                              0.1 0.4; 0.35 0.12; 0.12 0.08; 0.5 0.4; 0.1 0.5; 0.4 0.4]),
  "exfil"       => (0.0010, [ 5.2 1.0; 9.8 1.1; 4.0 1.0; 5.6 0.9; 3.2 0.8; 1.9 0.7;
                             -2.4 0.7; 0.08 0.05; 0.01 0.01; 0.4 0.3; 1.4 0.7; 1.9 0.7]),
)
const ORDER = ["benign","dos","probe","bruteforce","exfil"]

const BENIGN = CLASSES["benign"][2]

"""
Draw one flow. `blend` pulls the sample toward the benign centroid: 0 is a textbook
example of the class, 1 is indistinguishable from normal traffic. Real attack traffic
is a mixture of the two, which is what makes detection hard and what stops a
nearest-centroid classifier from solving this dataset.
"""
function sample_row!(buf, rng, spec, blend::Float64 = 0.0)
    for j in 1:12
        m = (1 - blend) * spec[j,1] + blend * BENIGN[j,1]
        sd = (1 - blend) * spec[j,2] + blend * BENIGN[j,2] * 1.35
        v = m + sd * randn(rng)
        # columns 1-6, 10-12 are log-scaled counts; 7 is a log ratio; 8-9 are fractions
        buf[j] = j in (8, 9) ? clamp(v, 0.0, 1.0) : v
    end
    buf
end

"""
How far this flow hides in the noise. Attacks: a little over half are stealthy.
Benign: a small tail of bursty hosts that look like an attack, which is where a
detector's false positives come from.
"""
function blend_for(rng, lab)
    if lab == "benign"
        return rand(rng) < 0.03 ? 0.45 + 0.25 * rand(rng) : 0.0
    end
    rand(rng) < 0.55 ? 0.60 + 0.30 * rand(rng) : 0.15 * rand(rng)
end

function draw_label(rng, cum)
    r = rand(rng)
    for (lab, c) in cum
        r <= c && return lab
    end
    "benign"
end

function write_split(path, rng, n, cum, id)
    counts = Dict(l => 0 for l in ORDER)
    buf = zeros(Float64, 12)
    open(path, "w") do io
        println(io, join(FEATURES, ","), ",label")
        for _ in 1:n
            lab = draw_label(rng, cum)
            counts[lab] += 1
            b = blend_for(rng, lab)
            spec = lab == "benign" && b > 0 ?
                   CLASSES[ORDER[rand(rng, 2:length(ORDER))]][2] : CLASSES[lab][2]
            # a bursty benign host is drawn *toward* an attack profile, not away from it
            sample_row!(buf, rng, spec, lab == "benign" && b > 0 ? 1.0 - b : b)
            print(io, join((@sprintf("%.5f", v) for v in buf), ","))
            println(io, ",", lab)
        end
    end
    counts
end

function main()
    isempty(ARGS) && error("usage: julia gen_ids_dataset.jl <student_id> [--train N] [--test N] [--out DIR]")
    id = uppercase(strip(ARGS[1]))
    o = Dict("train"=>300_000, "test"=>75_000, "out"=>".")
    i = 2
    while i <= length(ARGS)
        k = lstrip(ARGS[i], '-'); haskey(o,k) || error("unknown option $(ARGS[i])")
        o[k] = k == "out" ? ARGS[i+1] : parse(Int, ARGS[i+1]); i += 2
    end
    mkpath(o["out"])
    rng = MersenneTwister(student_seed(id))

    acc = 0.0
    cum = [(l, acc += CLASSES[l][1]) for l in ORDER]

    tr = write_split(joinpath(o["out"], "train_$(id).csv"), rng, o["train"], cum, id)
    te = write_split(joinpath(o["out"], "test_$(id).csv"),  rng, o["test"],  cum, id)

    @printf("%-12s %10s %10s\n", "class", "train", "test")
    for l in ORDER
        @printf("%-12s %10d %10d\n", l, tr[l], te[l])
    end
    atk_tr = sum(tr[l] for l in ORDER if l != "benign")
    atk_te = sum(te[l] for l in ORDER if l != "benign")
    @printf("\nattack rate: train %.3f %%, test %.3f %%\n", 100atk_tr/o["train"], 100atk_te/o["test"])
    @printf("A classifier that predicts \"benign\" for everything scores %.2f %% accuracy\n",
            100(o["test"] - atk_te)/o["test"])
    @printf("and has recall 0. Report precision, recall and the confusion matrix.\n")
end

main()
