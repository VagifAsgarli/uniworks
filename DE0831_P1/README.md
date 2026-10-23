# DE0831 Project 1: GPU Programming Fundamentals in Julia

Student: Vagif Asgarli, ID: 251ADM047 (individualised problem: N = 1152, seed = 51047, α = 7)

Four CUDA.jl exercises: a grid-stride SAXPY, a naive and a shared-memory tiled matrix
transpose, a naive and a privatised byte histogram, and a sliding-window Shannon entropy
scanner (both the basic and the fused route).

## Device

The block below is rewritten by every script when it runs its benchmarks, so it always
describes the GPU the results in `results/` were measured on.

<!-- BEGIN device -->
*Not measured yet: run the scripts on the GPU (see below).*
<!-- END device -->

## Individualisation

The header block from the brief is at the top of every script.  The student card number
`251ADM047` contains letters, so the formulas `STUDENT_ID % 37` and `STUDENT_ID % 100_000` use its
digits, `STUDENT_ID = 251047`; the full card number is what the scripts print and record:

```julia
const STUDENT_CARD = "251ADM047"
const STUDENT_ID   = parse(Int, filter(isdigit, STUDENT_CARD))   # 251047
```

This gives N = 1024 + (251047 mod 37) · 64 = 1152, SEED = 51047 and α = 1 + (251047 mod 7) = 7.

## How to run

Requirements: an NVIDIA GPU with a working driver, Julia 1.12 (the manifest was resolved with
Julia 1.12.7; CUDA.jl 6.4.2, Plots.jl 1.41.7).

```sh
cd DE0831_P1
julia --project=. -e 'using Pkg; Pkg.instantiate()'   # first time only

julia --project=. src/p1_ex1.jl      # SAXPY
julia --project=. src/p1_ex2.jl      # transpose
julia --project=. src/p1_ex3.jl      # histogram
julia --project=. src/p1_ex4.jl      # entropy scanner, plot, analysis

julia --project=. test/runtests.jl   # runs all four scripts, checks each prints Correct!
```

Each script prints the header (student, ID, N, seed, device), validates every kernel against a
CPU reference (it stops with `CHECK FAILED: ...` otherwise), prints `Correct!`, then runs its
benchmarks and writes its section of `results/benchmarks.md`.  `p1_ex4.jl` also writes
`testfile.bin`, `results/entropy_plot.png` and `results/analysis.md`.

Environment variables: `P1_QUICK=1` runs only the correctness checks (the default in
`test/runtests.jl`; use `P1_QUICK=0` there to include the benchmarks), `P1_REPS=<n>` changes the
number of timed launches (default 100, as in the brief).

## Files

| File | Contents |
|---|---|
| `src/p1_ex1.jl` | `saxpy!` grid-stride kernel; checks at blocks ∈ {1, 16, 64, 256, 1024} and N ∈ {1, 31, 32, 33, 255, 256, 257}; bandwidth table |
| `src/p1_ex2.jl` | `transpose_naive!`, `transpose_tiled!` (shared memory padded to (TILE+1) × TILE); checks against `Array(A)'`; bandwidth for TILE ∈ {8, 16, 32}; unpadded tiled kernel and a 2D copy as references |
| `src/p1_ex3.jl` | `hist_naive!` (one global atomic per byte), `hist_privatised!` (per-block shared-memory histogram, merged once per block); uniform and 90 % 0x00 datasets; speedups |
| `src/p1_ex4.jl` | `window_hist!` (basic route) and `entropy_fused!` (fused route with a shared-memory tree reduction); test file with a known high-entropy section; boundary tests; plot; throughput; performance analysis |
| `src/p1_common.jl` | host-side helpers shared by the scripts: timing (warm-up + `CUDA.@elapsed`, reset-aware variant for state-changing kernels), device information, Markdown tables |
| `test/runtests.jl` | runs the four scripts end to end and checks for `Correct!` |
| `results/benchmarks.md` | all timing tables (generated) |
| `results/analysis.md` | the exercise 4 performance analysis (generated from the measurements) |
| `results/entropy_plot.png` | H_j against j for `testfile.bin` |

## Methodology

- Every kernel time is measured with one warm-up launch, `CUDA.synchronize()`, and then
  `CUDA.@elapsed` (CUDA events) around 100 launches; the mean per launch is reported.
  `@time`/`@btime` are not used for kernels.
- The histogram kernels accumulate into their output, so they are timed with the reset-aware
  variant: the histogram is zeroed before each launch outside the timed region and each launch
  has its own `CUDA.@elapsed`.
- Bandwidth = bytes moved / time / 10⁹ (GB/s); throughput in exercise 4 = input bytes / time /
  10⁶ (MB/s).  The bytes counted per kernel are stated above each table.
- Inputs are generated on the CPU from the seeded RNG (`Random.seed!(SEED)`) and copied to the
  GPU, so every run with the same student ID uses the same data.
- Exercise 4 reads N in the boundary tests both as a number of windows (N · 4096 bytes) and as a
  number of bytes (one partial window).  A partial last window is normalised by its real length.

## Known issues and notes

- The timing tables, `analysis.md` and the plot are produced by running the scripts on a GPU;
  they are not included until the scripts have been run on the target device.
- The theoretical DRAM bandwidth and FP32 peak are computed from device attributes (memory clock,
  bus width, SM clock, FP32 lanes per SM).  If the driver does not report them, the analysis uses
  the measured device-to-device copy bandwidth as the roof instead and says so.
- `results/analysis.md` is regenerated every time `p1_ex4.jl` runs its benchmarks; the
  conclusions it draws (which limiter, which optimisation) are chosen from the measured numbers.
  Check the text against your numbers before submitting.
- If your Julia version differs from 1.12.7, run `julia --project=. -e 'using Pkg; Pkg.resolve(); Pkg.instantiate()'`.

## Declared AI use

This submission was developed with the help of Claude (Anthropic's AI assistant, used through
Claude Code).  The assistant drafted the kernels, the host code and tests, this README and the
text of the generated benchmark/analysis sections; because no GPU was available to it, it
checked the scripts by running them against a CPU emulation of the CUDA.jl kernel API (threads
as tasks, real block barriers and per-block shared memory).  All numbers in `results/` come from
running the scripts on the device listed under "Device".

*Describe here what you reviewed, changed and ran yourself.*

No course-supplied helper files are used; the timing helper in `src/p1_common.jl` follows the
measurement pattern given in the project brief.

## Submission

```sh
# from the directory that contains DE0831_P1:
cp -r DE0831_P1 DE0831_P1_Asgarli_251ADM047
zip -r DE0831_P1_Asgarli_251ADM047.zip DE0831_P1_Asgarli_251ADM047 -x '*/testfile.bin' '*/.gitignore'
```

The Colab notebook `DE0831_P1_colab.ipynb` (next to this folder in the repository) does all
of the above on a free Colab T4 GPU and downloads the finished archive.
