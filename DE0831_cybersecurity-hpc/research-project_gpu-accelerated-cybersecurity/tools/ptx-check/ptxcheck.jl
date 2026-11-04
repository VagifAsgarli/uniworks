# Compile every research-project kernel to PTX with the real CUDA.jl/GPUCompiler stack (no GPU needed).
using CUDA
const CC  = CUDA.CUDACore
const GPC = CC.GPUCompiler
const AS  = CC.AS
const STUDENT_CARD = "251ADM047"; const STUDENT_NAME = "Vagif Asgarli"
src = ARGS[1]
include(joinpath(src, "rp_common.jl")); include(joinpath(src, "rp_cpu.jl")); include(joinpath(src, "rp_gpu.jl"))

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
U8 = DV{UInt8}; U32 = DV{UInt32}; I32 = DV{Int32}; F32 = DV{Float32}; U64 = DV{UInt64}
jobs = [
    ("newline_flags!", newline_flags!, (U32, U8)),
    ("word_flags!", word_flags!, (U32, U8, U8)),
    ("scatter_positions!", scatter_positions!, (I32, U32, U32)),
    ("hash_match!", hash_match!, (I32, U8, I32, U8, U32, I32, I32, I32, U8, UInt32)),
    ("hash_match_shared!", hash_match_shared!, (I32, U8, I32, U8, U32, I32, I32, I32, U8, UInt32)),
    ("probe_counts!", probe_counts!, (U64, U8, I32, U8, U32, I32, UInt32)),
    ("hit_pairs!", hit_pairs!, (I32, I32, I32, I32, I32, I32)),
    ("hash_match_direct!", hash_match_direct!, (I32, I32, I32, U8, U8, U32, I32, I32, I32, U8, UInt32)),
    ("pos_lines!", pos_lines!, (I32, I32, I32)),
    ("match_tiled_tri!", match_tiled_tri!, (U32, U8, U8, I32, U32, U8, U8, I32)),
]
failed = false
for (name, f, tt) in jobs
    try
        asm = ptx(f, tt)
        shared = [m.match for m in eachmatch(r"\.shared[^\n;]*\[\d+\]", asm)]
        atoms  = unique([m.match for m in eachmatch(r"\b(atom|red)\.[a-z0-9_.]+", asm)])
        nglob  = count(_ -> true, eachmatch(r"ld\.global", asm))
        nbra   = count(_ -> true, eachmatch(r"\bbra\b", asm))
        println(rpad(name, 20), "OK  shared=", shared, " atomics=", atoms, " ld.global=", nglob, " bra=", nbra)
    catch err
        global failed = true
        println(rpad(name, 20), "FAILED: ", first(sprint(showerror, err), 1500))
    end
end
failed && exit(1)
