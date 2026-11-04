# Fake CUDA.jl for testing on a machine without a GPU.
# Every GPU thread runs as a cooperative Julia Task, so sync_threads() is a
# real barrier and shared memory is shared per block.  Kernels that never
# call sync_threads/shared memory are later run sequentially for speed.
module CUDA

using Random

export @cuda, CuArray, CuVector, CuMatrix, threadIdx, blockIdx, blockDim, gridDim,
       sync_threads, CuStaticSharedArray

const CuArray  = Array
const CuVector = Vector
const CuMatrix = Matrix

struct FakeDevice end
device() = FakeDevice()
name(::FakeDevice) = "FakeGPU (CPU emulator)"
capability(::FakeDevice) = v"8.6"
const DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT    = :sm
const DEVICE_ATTRIBUTE_MEMORY_CLOCK_RATE       = :memclk
const DEVICE_ATTRIBUTE_CLOCK_RATE              = :clk
const DEVICE_ATTRIBUTE_GLOBAL_MEMORY_BUS_WIDTH = :bus
const ATTRS = Dict(:sm => 2, :memclk => 9_751_000, :clk => 1_695_000, :bus => 384)
attribute(::FakeDevice, a) = Int32(ATTRS[a])
totalmem(::FakeDevice) = 24 * 2^30
driver_version()  = v"13.0.0"
runtime_version() = v"13.0.0"
functional() = true
synchronize() = nothing
zeros(T::Type, dims...) = Base.zeros(T, dims...)
fill(x, dims...) = Base.fill(x, dims...)

macro elapsed(ex)
    quote
        local t0 = time_ns()
        $(esc(ex))
        Float32((time_ns() - t0) / 1e9)
    end
end

# A read-modify-write is atomic here: tasks only switch at sync_threads.
const ATOMIC_OPS = Dict(:(+=) => :+, :(-=) => :-, :(|=) => :|, :(&=) => :&, :(⊻=) => :⊻)
macro atomic(ex)
    haskey(ATOMIC_OPS, ex.head) || error("fake @atomic supports only +=, -=, |=, &=, ⊻=")
    op = ATOMIC_OPS[ex.head]
    ref, val = ex.args
    Meta.isexpr(ref, :ref) || error("@atomic needs an array reference")
    arr = esc(ref.args[1]); idx = map(esc, ref.args[2:end])
    quote
        local A = $arr
        local I = ($(idx...),)
        A[I...] = $op(A[I...], convert(eltype(A), $(esc(val))))
        nothing
    end
end
# CUDA.jl's `accumulate`, `map`, broadcasting and indexing on CuArray are
# plain Base operations here because CuArray === Array.
unsafe_free!(x) = nothing
reclaim(args...; kwargs...) = nothing
macro allowscalar(ex)
    esc(ex)
end

# ---- execution model --------------------------------------------------------

mutable struct BlockState
    nthreads::Int
    arrived::Int
    exited::Int
    gen::Int
    diverged::Bool
    cond::Condition
    shmem::Vector{Any}
    shbytes::Int
    task_mode::Bool
end

mutable struct ThreadCtx
    tid::NTuple{3,Int32}
    bid::NTuple{3,Int32}
    bdim::NTuple{3,Int32}
    gdim::NTuple{3,Int32}
    block::BlockState
    shk::Int
end

const SEQ_CTX = Ref{ThreadCtx}()
ctx() = (t = current_task(); t.storage === nothing ? SEQ_CTX[] :
         get(() -> SEQ_CTX[], t.storage, :fakecuda_ctx))::ThreadCtx

threadIdx() = (c = ctx(); (x = c.tid[1], y = c.tid[2], z = c.tid[3]))
blockIdx()  = (c = ctx(); (x = c.bid[1], y = c.bid[2], z = c.bid[3]))
blockDim()  = (c = ctx(); (x = c.bdim[1], y = c.bdim[2], z = c.bdim[3]))
gridDim()   = (c = ctx(); (x = c.gdim[1], y = c.gdim[2], z = c.gdim[3]))

const USES_SYNC = Dict{Any,Bool}()

function sync_threads()
    c = ctx(); b = c.block
    b.task_mode || error("fake: sync_threads in sequential mode")
    gen = b.gen
    b.arrived += 1
    if b.arrived == b.nthreads
        b.arrived = 0
        b.gen += 1
        notify(b.cond)
    else
        if b.arrived + b.exited == b.nthreads
            b.diverged = true; notify(b.cond)
            error("fake: barrier divergence (some threads exited)")
        end
        while b.gen == gen
            wait(b.cond)
            b.diverged && error("fake: barrier divergence")
        end
    end
    return nothing
end

function CuStaticSharedArray(::Type{T}, dims) where {T}
    c = ctx(); b = c.block
    b.task_mode || error("fake: shared memory in sequential mode")
    c.shk += 1
    if c.shk > length(b.shmem)
        A = T <: AbstractFloat ? Base.fill(T(NaN), dims) : rand(T, dims)   # garbage
        b.shbytes += sizeof(A)
        b.shbytes <= 48 * 1024 || error("fake: more than 48 KiB static shared memory")
        push!(b.shmem, A)
    end
    A = b.shmem[c.shk]
    size(A) == Tuple(dims) || error("fake: shared array shape mismatch")
    return A::Array{T}
end

dim3(x::Integer) = (Int32(x), Int32(1), Int32(1))
dim3(x::Tuple) = ntuple(i -> i <= length(x) ? Int32(x[i]) : Int32(1), 3)

const NLAUNCH = Ref(0)

function fake_launch(f, args; threads = 1, blocks = 1)
    bdim, gdim = dim3(threads), dim3(blocks)
    nthr = prod(Int.(bdim))
    1 <= nthr <= 1024 || error("fake: invalid threads per block $threads")
    all(>=(1), gdim) || error("fake: invalid grid $blocks")
    gdim[2] <= 65535 && gdim[3] <= 65535 || error("fake: grid y/z too large")
    NLAUNCH[] += 1
    task_mode = get(USES_SYNC, f, true)
    used = false
    for bz in 1:gdim[3], by in 1:gdim[2], bx in 1:gdim[1]
        bid = (Int32(bx), Int32(by), Int32(bz))
        b = BlockState(nthr, 0, 0, 0, false, Condition(), Any[], 0, task_mode)
        if task_mode
            tasks = Task[]
            for tz in 1:bdim[3], ty in 1:bdim[2], tx in 1:bdim[1]
                c = ThreadCtx((Int32(tx), Int32(ty), Int32(tz)), bid, bdim, gdim, b, 0)
                t = Task() do
                    task_local_storage(:fakecuda_ctx, c)
                    r = f(args...)
                    r === nothing || error("fake: kernel returned $(typeof(r)), not nothing")
                    b.exited += 1
                    if b.arrived > 0 && b.arrived + b.exited == b.nthreads
                        b.diverged = true; notify(b.cond)
                    end
                end
                push!(tasks, t)
                schedule(t)
            end
            for t in tasks
                wait(t)
            end
            b.arrived == 0 || error("fake: threads left waiting at a barrier")
            used |= b.gen > 0 || !isempty(b.shmem)
        else
            for tz in 1:bdim[3], ty in 1:bdim[2], tx in 1:bdim[1]
                SEQ_CTX[] = ThreadCtx((Int32(tx), Int32(ty), Int32(tz)), bid, bdim, gdim, b, 0)
                r = f(args...)
                r === nothing || error("fake: kernel returned $(typeof(r)), not nothing")
            end
        end
    end
    task_mode && !used && (USES_SYNC[f] = false)
    return nothing
end

struct FakeKernel{F}
    f::F
    fun::Symbol
end
(k::FakeKernel)(args...; threads = 1, blocks = 1) = fake_launch(k.f, args; threads, blocks)

macro cuda(args...)
    call = args[end]
    kw = Dict{Symbol,Any}()
    for a in args[1:end-1]
        Meta.isexpr(a, :(=)) || error("fake @cuda: bad keyword $a")
        kw[a.args[1]] = esc(a.args[2])
    end
    Meta.isexpr(call, :call) || error("fake @cuda: last argument must be a call")
    f = esc(call.args[1]); fargs = map(esc, call.args[2:end])
    quote
        let f = $f, a = ($(fargs...),)
            if $(get(kw, :launch, true))
                fake_launch(f, a; threads = $(get(kw, :threads, 1)), blocks = $(get(kw, :blocks, 1)))
            else
                FakeKernel(f, :fun)
            end
        end
    end
end

registers(::FakeKernel) = 30
memory(::FakeKernel) = (; :local => 0, shared = 2048, constant = 0)
occupancy(::Symbol, threads::Integer; shmem::Integer = 0) = 1.0
active_blocks(::Symbol, threads::Integer; shmem::Integer = 0) = 8

end
