# DE0831 Project 2: Applied Security on GPUs — Track E, log mining (full route)

Student: Vagif Asgarli, ID 251ADM047

**Track E, full route:** one multi-pattern matching kernel over the whole corpus, matched lines
extracted with scan and compaction, and token entropy flagging that reuses the Project 1
scanner idea (per-block privatised histograms, no atomics in the entropy kernel).

## Device

The block below is rewritten by `src/p2_run.jl` when it runs the benchmarks, so it describes
the GPU the results in `results/` were measured on.

<!-- BEGIN device -->
- GPU: Tesla T4
- Compute capability: 7.5.0
- Streaming multiprocessors: 40, up to 1024 resident threads each
- Device memory: 14.56 GiB
- Theoretical DRAM bandwidth: 320.1 GB/s
- Theoretical INT32 throughput: 4.07 × 10¹² ops/s
- CUDA driver: 13.3.0
- CUDA runtime: 13.0.0
- Julia: 1.12.7, CUDA.jl: 6.5.1
- Host CPU: Intel(R) Xeon(R) CPU @ 2.00GHz (2 threads); Julia threads: 1
<!-- END device -->

## Individualisation

The student card number is set once at the top of `src/p2_run.jl`. The handout generator
(`src/gen_logs.jl`, unchanged) derives its RNG seed from it with SHA-256
(`251ADM047` → seed 5175890676511383715), so every corpus size is regenerated identically
from the ID: `julia src/gen_logs.jl 251ADM047 --lines N --out data/lines_N`. The script
runs the generator itself when the files are missing. The header block prints the name,
the ID, the derived seed, the corpus sizes, the device name and the compute capability.

## How to run

Requirements: an NVIDIA GPU with a working driver, Julia 1.12 (the Manifest was resolved
with Julia 1.12.7; CUDA.jl 6.5.1, CairoMakie 0.15 for the plots).

```sh
cd DE0831_P2
julia --project=. -e 'using Pkg; Pkg.instantiate()'   # first time only

julia --project=. src/p2_run.jl        # validation, benchmarks over 6 corpus sizes, results, plots
julia --project=. test/runtests.jl     # validation only (prints Correct!)
```

Options (environment variables): `P2_MAIN=<lines>` corpus used for the validation and the
breakdown (default 1,000,000); `P2_SIZES=125000,250000,...` sizes of the scaling study
(default 125k, 250k, 500k, 1M, 2M, 4M lines; the 4M corpus is 480 MB and needs about 5 GB of
device memory for the scans); `P2_REPS=<n>` timed launches per measurement (default 100);
`P2_CPU_REPS=<n>` CPU repetitions (default 3); `P2_QUICK=1` validation only;
`P2_NO_PLOTS=1` skip the plots.

The run prints the header block, validates every GPU result against the CPU baseline and
the generator's ground truth on the main corpus (it stops with `CHECK FAILED: ...`
otherwise), prints `Correct!`, then measures every step on every corpus size and writes
`results/benchmarks.md`, `results/analysis.md`, the raw timings (`results/timings.csv`,
`entropy_hist.csv`, `threshold_table.csv`), the PTX of the two tiled match kernels
(`results/match_tiled_tri.ptx`, `results/match_tiled.ptx`) and the plots (`results/*.png`).

## Files

| File | Contents |
|---|---|
| `src/p2_run.jl` | header block; validation (`Correct!`); benchmarks; results and analysis generation |
| `src/p2_gpu.jl` | the kernels: newline/token flags, scatter (compaction), `match_tiled!` (1 KB shared-memory tile, first-byte filter, atomic OR into the line mask), `match_tiled_tri!` (4 KB tile, three-byte prefix filter: the pipeline's kernel, built from the measurements of the first), `match_global!` (variant without the tile, for the analysis), `match_counts!` (operation counts of both filters), `gather_lines!`, `token_entropy!`, `entropy_hist!`; the pipeline |
| `src/p2_cpu.jl` | the single-threaded CPU baseline with the same algorithm, the `occursin` baseline, the character classes and the pattern table |
| `src/p2_common.jl` | timing harness (warm-up, `CUDA.@elapsed` per launch, mean/min/max, reset outside the timed region), device information, Markdown tables |
| `src/p2_data.jl` | generator wrapper and loaders for the corpus, indicators and ground truth |
| `src/p2_plots.jl` | the four plots (CairoMakie) |
| `src/gen_logs.jl` | the handout generator, unchanged |
| `test/runtests.jl` | runs the validation and checks for `Correct!` |
| `results/` | benchmark tables, analysis, raw timings, PTX dump, plots (generated) |

## Memory layout and the GPU technique

- The corpus is one flat `UInt8` vector; thread *i* handles byte *i*, so a warp reads 32
  consecutive bytes (coalesced). Flags per byte are `UInt32` so that `accumulate(+, flags)`
  (the lecture-7 scan) gives each flagged byte its output slot, and a scatter kernel packs
  the positions (compaction). Line starts, matched lines, token starts and flagged tokens
  are all produced this way.
- `match_tiled!`: one block per 1024-byte tile; the block copies the pattern table, the
  first-byte mask and the word-character table into shared memory (broadcast reads), loads
  its tile plus a 32-byte halo once with coalesced loads, and compares candidates from shared
  memory. A whole-word match sets the pattern's bit in the line's `UInt32` mask with an atomic
  OR (hits are 0.09 % of lines, so the binary search for the line and the atomic are
  negligible). Boundary handling: the halo covers patterns that cross a tile edge, bounds
  checks cover the last tile and the corpus ends, and word boundaries prevent `192.0.2.24`
  from matching inside `192.0.2.248`. No races: the only shared write is the atomic OR.
- `match_tiled_tri!`: the same kernel after the first measurement. On the T4 the first version ran
  at about 4 % of the copy bandwidth although it reads each byte once: the first-byte filter lets
  20 % of the positions through, so practically every warp of 32 lanes has a candidate and runs
  the candidate loop (a warp runs it whenever one lane needs it). The second version adds a
  three-byte prefix filter (a 4 KB bitmap in shared memory indexed by a 12-bit hash of the three
  bytes at the position, built on the host from the patterns) and uses a 4 KB tile (16 positions
  per thread) to amortise the per-block table copy. Both kernels are validated against the same
  ground truth and both are timed; the pipeline uses the second.
- `token_entropy!`: one thread per token with a private 64-bin histogram in shared memory,
  laid out so that a warp touches consecutive bytes (no bank conflicts); no atomics.
- Design note with the full rationale: `notes/design.md` in the repository.

## Methodology

- Every GPU time: one warm-up launch, `CUDA.synchronize()`, then one `CUDA.@elapsed` per
  launch over 100 launches (mean, min, max). The match kernel accumulates into the line
  mask, which is zeroed before every launch outside the timed region.
- Every step is timed directly (line table, match kernel, extraction, token starts,
  entropies, histogram, flagging), the whole GPU pipeline is one timing of its own, and the
  host-to-device copy, the device-to-host copy and the file read are separate timings.
  No figure in the results is a difference of two timings.
- CPU times are `@elapsed` of CPU code, best of 3 after a warm-up (never around a GPU
  launch).
- Throughput = corpus lines or bytes divided by the time (M lines/s, MB/s = 10⁶ bytes/s);
  copies in GB/s = 10⁹ bytes/s.
- The entropy threshold is chosen from the measured distribution (the midpoint of the widest
  empty band of the GPU histogram above the median token; the zero-entropy spike of one-symbol
  tokens leaves an equally wide empty band near 0 bits, which is why bands below the median are
  not candidates), then checked against `entropy_truth`.
- Evidence in the analysis (operation counts, registers, occupancy, the PTX instruction
  counts) is produced by the script itself.

## Known issues and notes

- The timing tables, the analysis and the plots are produced by running the script on a
  GPU; until then `results/` is empty.
- The generated data is not part of the archive (it is reproducible from the ID); the
  script regenerates it in `data/` on first use (about 5 minutes for all six sizes).
- If your Julia version differs from 1.12.7, run
  `julia --project=. -e 'using Pkg; Pkg.resolve(); Pkg.instantiate()'`.

## Declared AI use

This submission was developed with the help of Claude (Anthropic's AI assistant, used through
Claude Code). The assistant drafted the kernels, the CPU baseline, the tests, this README and
the text of the generated results; because no GPU was available to it, it checked the scripts
by running them against a CPU emulation of the CUDA.jl kernel API (threads as tasks, real
block barriers and per-block shared memory), by compiling every kernel to PTX with the CUDA.jl
compiler, and by mutation tests of the validation. All numbers in `results/` come from running
the scripts on the device listed under "Device".

*Describe here what you reviewed, changed and ran yourself.*

No course-supplied helper files are used except the handout generator `gen_logs.jl`.

## Submission

```sh
# from the directory that contains DE0831_P2:
cp -r DE0831_P2 DE0831_P2_Asgarli_251ADM047
zip -r DE0831_P2_Asgarli_251ADM047.zip DE0831_P2_Asgarli_251ADM047 -x '*/data/*' '*/.gitignore'
```
