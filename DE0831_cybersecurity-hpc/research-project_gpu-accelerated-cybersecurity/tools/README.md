# Tools for the research project

Helpers used to build, check and run `../DE0831_RP` without a local NVIDIA GPU.  None of them is
part of the submission archive.

## `DE0831_RP_colab.ipynb`: run everything on a Colab GPU

1. Zip the project folder (from `research-project_gpu-accelerated-cybersecurity/`):
   ```sh
   zip -r DE0831_RP.zip DE0831_RP -x '*/data/*' '*/results/*'
   ```
2. colab.research.google.com → File → Upload notebook → this file.
3. Runtime → Change runtime type → **Python 3**, **T4 GPU** (the notebook installs Julia
   1.12.7 itself and runs it with `-t auto`, i.e. the host's 2 threads).
4. Runtime → Run all; upload `DE0831_RP.zip` when asked.  A corrected zip can be uploaded
   again in step 3 (the sources are replaced, the generated data stays), then Runtime → Run
   after on the step 5 cell.

The notebook instantiates the environment, generates the corpora from the student ID, runs
`src/rp_run.jl` (validation, the list-size and corpus-size sweeps, results, plots) and
`test/runtests.jl`, shows `results/`, and downloads `DE0831_RP_Asgarli_251ADM047.zip` (without
`data/`) and `run_logs.zip`.  About 40 minutes.

## CPU-only run on a multicore machine

The tuned CPU baseline scales with tasks; the Colab host has two hardware threads, so the
CPU sweeps are also run on a 4-core machine without a GPU:

```sh
cd DE0831_RP
RP_CPU_ONLY=1 julia -t 4 --project=. src/rp_run.jl
```

writes `results/list_sweep_cpu_<host>.csv` and `results/size_sweep_cpu_<host>.csv` (the
header block names the host CPU); the report quotes both machines.

## `cpu-emulator`: run the scripts on a CPU

The Project 2 emulator (`../../project-2_applied-security-gpus/tools/cpu-emulator/CUDA`) is a
stand-in package named `CUDA` that runs kernels on the CPU (threads as tasks, real block
barriers, per-block shared memory, `@atomic |=`); `CuArray` is a plain `Array`, so timings
are meaningless and it is for correctness only.

```sh
cd research-project_gpu-accelerated-cybersecurity
julia --project=/tmp/rp-emu-env -e 'using Pkg;
    Pkg.develop(path=abspath("../project-2_applied-security-gpus/tools/cpu-emulator/CUDA"));
    Pkg.add(["Printf", "Random", "Test"])'
cd DE0831_RP
RP_QUICK=1 RP_MAIN=20000 RP_LISTS=10,30,100,300,1000 julia -t 4 --project=/tmp/rp-emu-env --check-bounds=yes src/rp_run.jl
```

## `ptx-check/`: compile every kernel for the GPU without a GPU

`ptxcheck.jl` compiles the eight kernels to PTX with the real CUDA.jl/GPUCompiler stack
(target sm_75) and prints their shared-memory allocations, atomics, global loads and
branches.  Environment set-up as in the Project 2 tools README (a CUDA-12.6-pinned
environment built from the project's Manifest):

```sh
julia --project=/tmp/p2-ptx-env tools/ptx-check/ptxcheck.jl DE0831_RP/src
```
