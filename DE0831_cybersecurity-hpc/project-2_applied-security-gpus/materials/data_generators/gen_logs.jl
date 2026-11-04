#!/usr/bin/env julia
# DE0831 Project 2, track E: synthetic log corpus for parallel pattern matching.
#
# Entirely synthetic. Every address is drawn from the RFC 5737 documentation ranges
# (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and every hostname ends in
# .invalid (RFC 2606), so nothing here resolves or corresponds to a real system.
#
#   julia gen_logs.jl 123456 [--lines 1000000] [--out .]
#
# Writes:
#   corpus_<ID>.log         the corpus, one event per line
#   indicators_<ID>.txt     the indicator set to match (input to your matcher)
#   truth_<ID>.csv          line,indicator          ground truth for IOC matching
#   entropy_truth_<ID>.csv  line,token,entropy      ground truth for entropy flagging

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

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
const USERS  = ["root","admin","deploy","backup","oracle","test","git","www-data","ubuntu","postgres"]
const PATHS  = ["/","/index.html","/api/v1/items","/api/v1/users","/static/app.js",
                "/health","/login","/assets/logo.png","/search","/api/v1/orders"]
const AGENTS = ["Mozilla/5.0 (X11; Linux x86_64)", "curl/8.4.0", "python-requests/2.31.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Go-http-client/2.0"]
const B64    = collect("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")

# The documentation ranges are partitioned so that background traffic can never
# collide with an indicator by chance: hosts .1-.199 are background, .200-.254 are
# reserved for the indicator set. Without this the ground truth is silently wrong.
const NETS = ["192.0.2.", "198.51.100.", "203.0.113."]
docip(rng)  = rand(rng, NETS) * string(rand(rng, 1:199))
iocip(rng)  = rand(rng, NETS) * string(rand(rng, 200:254))

function shannon(s::AbstractString)
    counts = Dict{Char,Int}()
    for c in s; counts[c] = get(counts, c, 0) + 1; end
    n = length(s); h = 0.0
    for (_, c) in counts; p = c / n; h -= p * log2(p); end
    h
end

dga(rng) = String(rand(rng, 'a':'z', rand(rng, 12:20))) * ".invalid"
b64blob(rng) = String(rand(rng, B64, rand(rng, 40:120)))

function main()
    isempty(ARGS) && error("usage: julia gen_logs.jl <student_id> [--lines N] [--out DIR]")
    id = uppercase(strip(ARGS[1]))
    o = Dict("lines"=>1_000_000, "out"=>".")
    i = 2
    while i <= length(ARGS)
        k = lstrip(ARGS[i], '-'); haskey(o,k) || error("unknown option $(ARGS[i])")
        o[k] = k == "out" ? ARGS[i+1] : parse(Int, ARGS[i+1]); i += 2
    end
    mkpath(o["out"]); N = o["lines"]
    rng = MersenneTwister(student_seed(id))

    # The indicator set: 12 addresses and 8 domains the student must find.
    ioc_ips     = unique([iocip(rng) for _ in 1:40])[1:12]
    ioc_domains = unique([dga(rng) for _ in 1:10])[1:8]
    indicators  = vcat(ioc_ips, ioc_domains)
    open(joinpath(o["out"], "indicators_$(id).txt"), "w") do io
        for ind in indicators; println(io, ind); end
    end

    corpus = joinpath(o["out"], "corpus_$(id).log")
    ft = open(joinpath(o["out"], "truth_$(id).csv"), "w")
    fe = open(joinpath(o["out"], "entropy_truth_$(id).csv"), "w")
    println(ft, "line,indicator"); println(fe, "line,token,entropy")
    nioc = 0; nent = 0

    open(corpus, "w") do io
        for ln in 1:N
            mon = rand(rng, MONTHS); day = rand(rng, 1:28)
            hh, mm, ss = rand(rng, 0:23), rand(rng, 0:59), rand(rng, 0:59)
            ts = @sprintf("%s %2d %02d:%02d:%02d", mon, day, hh, mm, ss)

            hit_ioc = rand(rng) < 0.0009            # ~1 in 1100 lines carries an indicator
            hit_b64 = rand(rng) < 0.0004            # ~1 in 2500 carries an encoded payload

            if rand(rng) < 0.45                                     # sshd auth event
                ip = hit_ioc ? rand(rng, ioc_ips) : docip(rng)
                u  = rand(rng, USERS)
                line = rand(rng) < 0.3 ?
                  "$ts host$(rand(rng,1:24)) sshd[$(rand(rng,1000:9999))]: Failed password for invalid user $u from $ip port $(rand(rng,1024:65535)) ssh2" :
                  "$ts host$(rand(rng,1:24)) sshd[$(rand(rng,1000:9999))]: Accepted publickey for $u from $ip port $(rand(rng,1024:65535)) ssh2"
                println(io, line)
                if hit_ioc; println(ft, "$ln,$ip"); nioc += 1; end
            else                                                    # nginx access event
                ip = hit_ioc && rand(rng) < 0.5 ? rand(rng, ioc_ips) : docip(rng)
                host = hit_ioc && ip ∉ ioc_ips ? rand(rng, ioc_domains) : "app$(rand(rng,1:9)).invalid"
                path = rand(rng, PATHS)
                if hit_b64
                    blob = b64blob(rng)
                    path = "/upload?d=" * blob
                    h = shannon(blob)
                    println(fe, "$ln,$blob,$(round(h, digits=4))"); nent += 1
                end
                println(io, "$ip - - [$(lpad(day,2,'0'))/$mon/2026:$(lpad(hh,2,'0')):$(lpad(mm,2,'0')):$(lpad(ss,2,'0')) +0200] \"GET $path HTTP/1.1\" $(rand(rng,[200,200,200,304,404,500])) $(rand(rng,120:98000)) \"http://$host/\" \"$(rand(rng,AGENTS))\"")
                if hit_ioc
                    ind = ip ∈ ioc_ips ? ip : host
                    println(ft, "$ln,$ind"); nioc += 1
                end
            end
        end
    end
    close(ft); close(fe)

    sz = filesize(corpus) / 1e6
    @printf("corpus_%s.log            %d lines, %.1f MB\n", id, N, sz)
    @printf("indicators_%s.txt        %d indicators (%d addresses, %d domains)\n",
            id, length(indicators), length(ioc_ips), length(ioc_domains))
    @printf("truth_%s.csv             %d lines carry an indicator (%.4f %%)\n", id, nioc, 100nioc/N)
    @printf("entropy_truth_%s.csv     %d encoded payloads, entropy ~5.5-6.0 bits/char\n", id, nent)
    @printf("\nNormal log tokens sit near 3.5-4.5 bits/char, so a threshold around 5.0\n")
    @printf("separates them. Justify whatever threshold you choose from your own data.\n")
end

main()
