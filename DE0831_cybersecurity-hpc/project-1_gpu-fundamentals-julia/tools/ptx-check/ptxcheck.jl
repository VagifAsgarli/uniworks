# Compile every assessed kernel to PTX with the real CUDA.jl/GPUCompiler stack
# (no GPU needed) to catch device-side compilation errors.
using CUDA
const CC  = CUDA.CUDACore
const GPC = CC.GPUCompiler
const AS  = CC.AS

src = ARGS[1]

# Load only the definitions (functions, consts) of a script into a module.
function load_defs(file)
    m = Module(:K)
    Core.eval(m, :(using CUDA))
    ex = Meta.parseall(read(file, String); filename = file)
    for a in ex.args
        a isa Expr || continue
        keep = a.head in (:function, :const) ||
               (a.head == :(=) && a.args[1] isa Expr && a.args[1].head in (:call, :where))
        keep || continue
        try
            Core.eval(m, a)
        catch
        end
    end
    return m
end

function ptx(f, tt; sm = (7, 5))
    target = GPC.PTXCompilerTarget(; cap = VersionNumber(sm...), ptx = v"7.5", debuginfo = false)
    params = CC.CUDACompilerParams(; sm = CC.SMVersion(sm...), ptx = v"7.5")
    config = GPC.CompilerConfig(target, params; kernel = true, name = nothing, always_inline = false)
    job = GPC.CompilerJob(GPC.methodinstance(typeof(f), Base.to_tuple_type(tt)), config)
    asm, _ = GPC.JuliaContext() do ctx
        GPC.compile(:asm, job)
    end
    return asm
end

DV{T} = CuDeviceArray{T,1,AS.Global}
DM{T} = CuDeviceArray{T,2,AS.Global}

ex1 = load_defs(joinpath(src, "p1_ex1.jl"))
ex2 = load_defs(joinpath(src, "p1_ex2.jl"))
ex3 = load_defs(joinpath(src, "p1_ex3.jl"))
ex4 = load_defs(joinpath(src, "p1_ex4.jl"))

jobs = Any[
    ("saxpy!", ex1.saxpy!, (DV{Float32}, Float32, DV{Float32})),
    ("transpose_naive!", ex2.transpose_naive!, (DM{Float32}, DM{Float32})),
    ("copy2d!", ex2.copy2d!, (DM{Float32}, DM{Float32})),
]
for T in (8, 16, 32)
    push!(jobs, ("transpose_tiled! TILE=$T", ex2.transpose_tiled!, (DM{Float32}, DM{Float32}, Val{T})))
    push!(jobs, ("transpose_tiled_nopad! TILE=$T", ex2.transpose_tiled_nopad!, (DM{Float32}, DM{Float32}, Val{T})))
end
append!(jobs, [
    ("hist_naive!", ex3.hist_naive!, (DV{UInt32}, DV{UInt8})),
    ("hist_privatised!", ex3.hist_privatised!, (DV{UInt32}, DV{UInt8})),
    ("window_hist!", ex4.window_hist!, (DM{UInt32}, DV{UInt8})),
    ("entropy_fused!", ex4.entropy_fused!, (DV{Float32}, DV{UInt8})),
])

failed = false
for (name, f, tt) in jobs
    try
        asm = ptx(f, tt)
        shared = [m.match for m in eachmatch(r"\.shared[^\n;]*\[\d+\]", asm)]
        atoms  = unique([m.match for m in eachmatch(r"(atom|red)\.[a-z0-9.]+", asm)])
        math   = unique([m.match for m in eachmatch(r"(lg2|div|rcp)\.[a-z0-9.]+", asm)])
        calls  = unique([m.match for m in eachmatch(r"call[^\n]*", asm)])
        println(rpad(name, 32), "OK  shared=", shared, " atomics=", atoms, " math=", math,
                isempty(calls) ? "" : "  calls=" * string(first(calls, 3)))
    catch err
        global failed = true
        println(rpad(name, 32), "FAILED: ", sprint(showerror, err)[1:min(end, 1500)])
    end
end
failed && exit(1)
