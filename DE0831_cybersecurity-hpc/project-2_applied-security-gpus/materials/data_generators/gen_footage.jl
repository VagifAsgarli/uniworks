#!/usr/bin/env julia
# DE0831 Project 2, track C: synthetic surveillance-style footage.
#
# Generates a fixed-camera scene with moving objects. Entirely synthetic: no real
# footage, no real location, and no person appears in it, so the privacy notice of
# lecture 10 is satisfied by construction.
#
#   julia gen_footage.jl 123456 [--frames 60] [--width 1920] [--height 1080] [--out .]
#
# Writes:
#   footage_<ID>.raw          W*H*NFRAMES bytes, UInt8 grayscale, frame-major
#   footage_<ID>.meta         width, height, frames, fps
#   motion_truth_<ID>.csv     frame,object,x0,y0,x1,y1  (ground-truth boxes)
#   preview_<ID>_f000.pgm     first and middle frame, viewable in most image tools

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

function parse_args()
    isempty(ARGS) && error("usage: julia gen_footage.jl <student_id> [--frames N] [--width W] [--height H] [--out DIR]")
    id = uppercase(strip(ARGS[1]))
    o = Dict("frames"=>60, "width"=>1920, "height"=>1080, "out"=>".")
    i = 2
    while i <= length(ARGS)
        k = lstrip(ARGS[i], '-'); haskey(o, k) || error("unknown option $(ARGS[i])")
        o[k] = k == "out" ? ARGS[i+1] : parse(Int, ARGS[i+1]); i += 2
    end
    id, o
end

"Static scene: vertical gradient, a few fixed structures, and low-frequency texture."
function background(rng, W, H)
    bg = Matrix{Float32}(undef, H, W)
    for x in 1:W, y in 1:H
        bg[y, x] = 40f0 + 60f0 * (y / H)
    end
    for _ in 1:6                                  # fixed structures, sized to the frame
        w = rand(rng, max(4, W ÷ 24):max(5, W ÷ 7))
        h = rand(rng, max(4, H ÷ 18):max(5, H ÷ 3))
        x0, y0 = rand(rng, 1:max(1, W - w)), rand(rng, 1:max(1, H - h))
        bg[y0:min(y0 + h, H), x0:min(x0 + w, W)] .= Float32(rand(rng, 20:90))
    end
    coarse = rand(rng, Float32, cld(H,16)+1, cld(W,16)+1) .* 18f0   # smooth texture
    for x in 1:W, y in 1:H
        bg[y, x] += coarse[cld(y,16), cld(x,16)]
    end
    bg
end

struct Mover
    w::Int; h::Int; x0::Float64; y0::Float64; vx::Float64; vy::Float64
    amp::Float64; freq::Float64; shade::Float32
end

function main()
    id, o = parse_args()
    W, H, N, outdir = o["width"], o["height"], o["frames"], o["out"]
    mkpath(outdir)
    rng = MersenneTwister(student_seed(id))

    bg = background(rng, W, H)
    mw = max(3, W ÷ 24); mh = max(4, H ÷ 12)
    movers = [Mover(rand(rng, mw:2mw), rand(rng, mh:2mh),
                    rand(rng) * W * 0.3, rand(rng) * H * 0.6 + H * 0.2,
                    rand(rng, 6.0:0.5:16.0) * W / 1920, rand(rng, -2.0:0.5:2.0) * H / 1080,
                    rand(rng, 10.0:30.0) * H / 1080, rand(rng) * 0.25 + 0.05,
                    Float32(rand(rng, 150:235))) for _ in 1:3]

    raw   = joinpath(outdir, "footage_$(id).raw")
    truth = joinpath(outdir, "motion_truth_$(id).csv")
    frame = Matrix{Float32}(undef, H, W)
    out   = Matrix{UInt8}(undef, H, W)

    open(raw, "w") do io
        open(truth, "w") do ft
            println(ft, "frame,object,x0,y0,x1,y1")
            for f in 0:N-1
                copyto!(frame, bg)
                for (k, m) in enumerate(movers)
                    x = m.x0 + m.vx * f
                    y = m.y0 + m.vy * f + m.amp * sin(m.freq * f)
                    x = mod(x, W + m.w) - m.w                     # wrap across the scene
                    x0 = clamp(round(Int, x),     1, W); x1 = clamp(x0 + m.w, 1, W)
                    y0 = clamp(round(Int, y),     1, H); y1 = clamp(y0 + m.h, 1, H)
                    if x1 > x0 && y1 > y0
                        @views frame[y0:y1, x0:x1] .= m.shade
                        println(ft, "$f,$k,$x0,$y0,$x1,$y1")
                    end
                end
                @inbounds for i in eachindex(frame)               # sensor noise
                    out[i] = round(UInt8, clamp(frame[i] + 6f0 * randn(rng, Float32), 0f0, 255f0))
                end
                write(io, out)
                if f == 0 || f == N ÷ 2                           # human-viewable previews
                    open(joinpath(outdir, @sprintf("preview_%s_f%03d.pgm", id, f)), "w") do ip
                        write(ip, "P5\n$W $H\n255\n"); write(ip, permutedims(out))
                    end
                end
            end
        end
    end

    open(joinpath(outdir, "footage_$(id).meta"), "w") do io
        println(io, "width=$W\nheight=$H\nframes=$N\nfps=25\ndtype=UInt8")
        println(io, "layout=frames back to back; each frame is a Julia $(H)x$(W) UInt8 matrix in column-major order")
    end

    @printf("footage_%s.raw   %d x %d x %d frames, %.1f MB\n", id, W, H, N, W*H*N/1e6)
    @printf("motion_truth_%s.csv  ground-truth boxes for %d moving objects\n", id, length(movers))
    @printf("previews: preview_%s_f000.pgm, preview_%s_f%03d.pgm\n", id, id, N ÷ 2)
    @printf("\nRead a frame in Julia:\n")
    @printf("  f = Array{UInt8}(undef, %d, %d); read!(\"footage_%s.raw\", f)   # first frame\n", H, W, id)
end

main()
