# Tools for Project 2

Helpers used to build, check and run `../DE0831_P2` without a local NVIDIA GPU.  None of them is
part of the submission archive.

## `DE0831_P2_colab.ipynb`: run everything on a Colab GPU

1. Zip the project folder (from `project-2_applied-security-gpus/`):
   ```sh
   zip -r DE0831_P2.zip DE0831_P2 -x '*/data/*' '*/results/*'
   ```
2. colab.research.google.com → File → Upload notebook → this file.
3. Runtime → Change runtime type → **Python 3**, **T4 GPU** (not the Julia runtime: the notebook
   installs Julia 1.12.7 itself, the version the Manifest was resolved with).
4. Runtime → Run all; upload `DE0831_P2.zip` when asked.

The notebook instantiates the environment, generates the six corpora from the student ID, runs
`src/p2_run.jl` (validation, benchmarks, results, Julia/CairoMakie plots) and `test/runtests.jl`,
shows `results/`, and downloads `DE0831_P2_Asgarli_251ADM047.zip` (without `data/`) and
`run_logs.zip`.  About 35–45 minutes: ~15 for CUDA.jl and CairoMakie, ~5 for the generator,
the rest for the benchmarks over six corpus sizes.

## `cpu-emulator/`: run the scripts on a CPU

`cpu-emulator/CUDA` is the Project 1 stand-in package named `CUDA` (every GPU thread is a Julia
task, `sync_threads()` is a real block barrier, `CuStaticSharedArray` is per block and starts
filled with garbage), extended for Project 2: `@atomic` also accepts `-=`, `|=`, `&=` and `⊻=`
(the match kernel ORs pattern bits into the line mask), and `unsafe_free!` and `@allowscalar`
exist.  `CuArray` is a plain `Array`, so `accumulate`, `fill!` and broadcasting are the Base ones
and all timings are meaningless; it is for correctness only.

```sh
cd project-2_applied-security-gpus
julia --project=/tmp/p2-emu-env -e 'using Pkg;
    Pkg.develop(path=abspath("tools/cpu-emulator/CUDA"));
    Pkg.add(["Printf", "Random", "Test"])'
cd DE0831_P2
P2_QUICK=1 P2_MAIN=20000 julia --project=/tmp/p2-emu-env --check-bounds=yes src/p2_run.jl
```

`P2_MAIN=20000` keeps the emulated run to a few minutes (the generator is called for the
20,000-line corpus the first time).  `emulator-check/gpu_check.jl` is the longer stand-alone
check used during development: the whole pipeline on the chosen corpus against the CPU baseline
and the ground truth, the global-memory kernel variant, and the eleven boundary cases:

```sh
julia --project=/tmp/p2-emu-env --check-bounds=yes tools/emulator-check/gpu_check.jl DE0831_P2/src 20000
```

Mutation testing of the validation (each mutant of `p2_gpu.jl` must make the run fail): removing
the tile boundary check, removing the halo, removing `sync_threads()` from the match kernel, an
off-by-one in the scatter, a token start without the previous-byte check, an off-by-one in the
binary search and a sign error in the entropy are all caught.  Disabling the first-byte filter
survives, as it must: the filter only skips positions no pattern can start at, so it cannot
change the match set (its effect shows in the candidate/compare counts of `match_counts!`, not
in the result).

## `ptx-check/`: compile every kernel for the GPU without a GPU

`ptxcheck.jl` compiles the nine track-E kernels to PTX with the real CUDA.jl/GPUCompiler stack
(target sm_75) and prints their shared-memory allocations, atomic instructions, global-load and
branch counts, which catches device-side compilation errors the emulator cannot (dynamic
dispatch, unsupported types, `Int` vs `Int32` indexing).  Without a driver, CUDA.jl selects no
toolkit, so the environment pins one:

```sh
cd project-2_applied-security-gpus
mkdir -p /tmp/p2-ptx-env && cp DE0831_P2/Project.toml DE0831_P2/Manifest.toml /tmp/p2-ptx-env/
# make the toolkit JLLs direct dependencies so that their version preference applies
sed -i 's/^\[deps\]/[deps]\nCUDA_Compiler_jll = "d1e2174e-dfdc-576e-b43e-73b79eb1aca8"\nCUDA_Runtime_jll = "76a88914-d11a-5bdc-97e0-2f5a05c973a2"/' /tmp/p2-ptx-env/Project.toml
printf '[CUDA_Compiler_jll]\nversion = "12.6"\n\n[CUDA_Runtime_jll]\nversion = "12.6"\n' > /tmp/p2-ptx-env/LocalPreferences.toml
julia --project=/tmp/p2-ptx-env -e 'using Pkg; Pkg.instantiate()'
julia --project=/tmp/p2-ptx-env tools/ptx-check/ptxcheck.jl DE0831_P2/src
```
