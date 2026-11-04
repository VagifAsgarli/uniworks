# DE0831 Research Project: Log indicator matching as the list grows (topic 10)

Student: Vagif Asgarli, ID 251ADM047 (alone, by agreement)

**Measurable objective:** log lines per second of indicator matching on one GPU as the indicator
list grows from 10 to 10,000 entries, against a tuned multithreaded CPU baseline; the data rate
at which the GPU is needed and the rate it keeps up with once the host-to-device copy is
counted; the factor that limits each method.

## Device

The block below is rewritten by `src/rp_run.jl` when it runs the benchmarks, so it describes
the GPU the results in `results/` were measured on.

<!-- BEGIN device -->
*Not measured yet: run the script on the GPU (see below).*
<!-- END device -->

## Data

The course log corpus from the handout generator (`src/gen_logs.jl`, unchanged) run with the
student ID (`251ADM047` → seed 5175890676511383715): 1,000,000 lines (119.2 MB) for the list
sweep and 125k–4M lines for the corpus-size sweep; the script regenerates the files in `data/`
when they are missing.  Indicator lists of 10, 30, 100, 300, 1,000, 3,000 and 10,000 entries are
built deterministically from the same seed (`src/rp_data.jl`): the generator's 20 indicators
(ground truth: 894 lines) plus synthetic "cold" indicators in the same two forms (addresses
from the RFC 2544 benchmarking range 198.18.0.0/15, DGA-style `.invalid` hostnames) that cannot
occur in the corpus, so the hit set of every list is known exactly and only the list size
changes.  Nothing is collected from any real system.

Matching semantics: an indicator matches a line when it occurs as a whole token (the bytes
before and after it are not word characters `[A-Za-z0-9.-]`); every method applies this rule.

## Methods

| | method | file | cost model |
|---|---|---|---|
| G2 | **GPU hash-set** (the method): token starts by flags → scan → scatter (lecture 7); one thread per token hashes its bytes (FNV-1a) and probes an open-addressing table of the indicators (global memory, or the keys in shared memory while the table fits); hits compacted to (line, indicator) | `src/rp_gpu.jl` | one pass, independent of the list size |
| G1 | **GPU per-indicator** (unoptimised GPU baseline): the Project 2 kernel (4 KB shared-memory tile, three-byte prefix filter, atomic OR of the pattern bit into the line's mask), one launch per group of 32 indicators | `src/rp_gpu.jl` | passes ∝ ⌈N/32⌉ |
| C1 | **CPU tuned**: the G2 algorithm in Julia, hand-written open-addressing table, no allocation per token, one task per newline-aligned chunk (`Threads.@threads`; 1, 2, 4 tasks) | `src/rp_cpu.jl` | one pass |
| C2 | **CPU library**: `occursin` per indicator over the lines (lists up to 300) | `src/rp_cpu.jl` | lines × N |

## How to run

Requirements: an NVIDIA GPU with a working driver, Julia 1.12 (the Manifest was resolved with
Julia 1.12.7; CUDA.jl 6.5.1, CairoMakie 0.15 for the plots).

```sh
cd DE0831_RP
julia --project=. -e 'using Pkg; Pkg.instantiate()'          # first time only

julia -t auto --project=. src/rp_run.jl      # validation, both sweeps, results, plots
julia --project=. test/runtests.jl           # validation only (prints Correct!)
RP_CPU_ONLY=1 julia -t 4 --project=. src/rp_run.jl   # CPU methods only, on a machine without a GPU
```

Options (environment variables): `RP_MAIN=<lines>` corpus of the validation and the list sweep
(default 1,000,000); `RP_LISTS=10,30,...` list sizes; `RP_SIZES=125000,...` corpus sizes of the
data-rate sweep; `RP_SIZE_LIST=<N>` list size of that sweep (default 1,000); `RP_THREADS=1,2,4`
task counts of the CPU matcher (capped at Julia's thread count, must include 1); `RP_REPS` timed
launches per measurement (default 100); `RP_CPU_REPS` (default 3); `RP_G1_MAX` largest list for
the per-indicator kernel (default 3,000); `RP_C2_MAX` largest list for `occursin` (default
300); `RP_QUICK=1` validation only; `RP_CPU_ONLY=1`; `RP_NO_PLOTS=1`.

The run prints the header block, validates every method against the ground truth for every
list size (it stops with `CHECK FAILED: ...` otherwise) and the hand-made cases, prints
`Correct!`, then writes `results/benchmarks.md`, `results/analysis.md`, `results/list_sweep.csv`,
`results/size_sweep.csv`, the PTX of the hash-match kernel (`results/hash_match.ptx`) and the
plots (`results/*.png`).  A CPU-only run writes `results/list_sweep_cpu_<host>.csv` and
`results/size_sweep_cpu_<host>.csv`.

## Files

| File | Contents |
|---|---|
| `src/rp_run.jl` | header block; validation (`Correct!`); the list-size, corpus-size and CPU-task sweeps; results and analysis generation |
| `src/rp_gpu.jl` | kernels: `newline_flags!`, `word_flags!`, `scatter_positions!` (compaction), `hash_match!`, `hash_match_shared!`, `probe_counts!` (measurement), `hit_pairs!`, `match_tiled_tri!` (Project 2 kernel for the per-indicator baseline); the pipeline |
| `src/rp_cpu.jl` | the word alphabet, FNV-1a, the open-addressing indicator table, the tuned multithreaded CPU matcher, the `occursin` baseline |
| `src/rp_data.jl` | generator wrapper, loaders, the indicator lists |
| `src/rp_common.jl` | timing harness (warm-up, `CUDA.@elapsed` per launch, mean/min/max), device information, Markdown tables |
| `src/rp_plots.jl` | the four plots (CairoMakie) |
| `src/gen_logs.jl` | the handout generator, unchanged |
| `test/runtests.jl` | runs the validation and checks for `Correct!` |
| `results/` | tables, analysis, raw timings, PTX dump, plots (generated) |

## Methodology

- Every GPU time: one warm-up launch, `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
  over 100 launches (mean, min, max).  The per-indicator kernel accumulates into masks that are
  zeroed before every launch outside the timed region.
- Every step of the hash-set pipeline is timed directly (line table, token scan, hash match,
  extraction), the whole pipeline is one timing of its own, and the host-to-device copy is a
  separate timing.  No figure is a difference of two timings.
- CPU times are `@elapsed` of CPU code, best of 3 after a warm-up, with the number of tasks
  stated; the host CPU and its hardware thread count are printed in the header block.
- Rates = corpus lines or bytes divided by the time.
- Evidence (probes per token, table bytes against the caches, registers, occupancy, the PTX
  instruction counts) is produced by the script itself.

## Declared AI use

This submission was developed with the help of Claude (Anthropic's AI assistant, used through
Claude Code). The assistant drafted the kernels, the CPU matcher, the tests, this README and the
text of the generated results; because no GPU was available to it, it checked the scripts by
running them against a CPU emulation of the CUDA.jl kernel API and by compiling every kernel to
PTX with the CUDA.jl compiler. All numbers in `results/` come from running the scripts on the
device listed under "Device".

*Describe here what you reviewed, changed and ran yourself.*

No course-supplied helper files are used except the handout generator `gen_logs.jl`.
