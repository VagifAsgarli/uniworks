# Tools for Project 1

Helpers used to build, check and run `../DE0831_P1` without a local NVIDIA GPU.  None of them is
part of the submission archive.

## `DE0831_P1_colab.ipynb`: run everything on a Colab GPU

1. Zip the project folder (from `project-1_gpu-fundamentals-julia/`):
   ```sh
   zip -r DE0831_P1.zip DE0831_P1 -x '*/testfile.bin'
   ```
2. colab.research.google.com → File → Upload notebook → this file.
3. Runtime → Change runtime type → **Python 3**, **T4 GPU** (not the Julia runtime: the notebook
   installs Julia 1.12.7 itself, the version the Manifest was resolved with).
4. Runtime → Run all; upload `DE0831_P1.zip` when asked.

The notebook runs the four scripts and `test/runtests.jl`, draws `results/entropy_plot.png` with
matplotlib from `results/entropy_profile.csv` (GR, the Plots.jl backend, does not load on Colab, so
the scripts run with `P1_NO_PLOTS=1`) and downloads `DE0831_P1_Asgarli_251ADM047.zip` and
`run_logs.zip`.  About 15–20 minutes, most of it installing CUDA.jl.

## `cpu-emulator/`: run the scripts on a CPU

`cpu-emulator/CUDA` is a stand-in package named `CUDA` that runs kernels on the CPU: every GPU
thread is a Julia task, `sync_threads()` is a real block barrier, `CuStaticSharedArray` is shared
per block and starts filled with garbage (NaN or random bits), and launches check the block size,
the 48 KiB static shared-memory limit and barrier divergence.  `CuArray` is a plain `Array`, so the
timings it produces are meaningless; it is for correctness only.

```sh
cd project-1_gpu-fundamentals-julia
julia --project=/tmp/p1-emu-env -e 'using Pkg;
    Pkg.develop(path=abspath("tools/cpu-emulator/CUDA"));
    Pkg.add(["Plots", "Printf", "Random", "Test"])'
rm -rf /tmp/p1-emu && cp -r DE0831_P1 /tmp/p1-emu
cp /tmp/p1-emu-env/Project.toml /tmp/p1-emu-env/Manifest.toml /tmp/p1-emu/
cd /tmp/p1-emu && P1_QUICK=1 julia --project=. test/runtests.jl
```

## `ptx-check/`: compile every kernel for the GPU without a GPU

`ptxcheck.jl` compiles all assessed kernels to PTX with the real CUDA.jl/GPUCompiler stack (target
sm_75) and prints their shared-memory sizes and atomic instructions, which catches device-side
compilation errors the emulator cannot.  Without a driver, CUDA.jl selects no toolkit, so the
environment pins one:

```sh
cd project-1_gpu-fundamentals-julia
mkdir -p /tmp/p1-ptx-env && cp DE0831_P1/Project.toml DE0831_P1/Manifest.toml /tmp/p1-ptx-env/
# make the toolkit JLLs direct dependencies so that their version preference applies
sed -i 's/^\[deps\]/[deps]\nCUDA_Compiler_jll = "d1e2174e-dfdc-576e-b43e-73b79eb1aca8"\nCUDA_Runtime_jll = "76a88914-d11a-5bdc-97e0-2f5a05c973a2"/' /tmp/p1-ptx-env/Project.toml
printf '[CUDA_Compiler_jll]\nversion = "12.6"\n\n[CUDA_Runtime_jll]\nversion = "12.6"\n' > /tmp/p1-ptx-env/LocalPreferences.toml
julia --project=/tmp/p1-ptx-env -e 'using Pkg; Pkg.instantiate()'
julia --project=/tmp/p1-ptx-env tools/ptx-check/ptxcheck.jl DE0831_P1/src
```
