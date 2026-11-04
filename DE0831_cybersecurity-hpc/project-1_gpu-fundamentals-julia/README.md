# Project 1: GPU Programming Fundamentals in Julia

Course: [DE0831 Cybersecurity Solutions in High-Performance Computing Environments](../README.md)

| | |
|---|---|
| Issued | week 3, 14.09.2026 |
| Due | Friday of week 8, **23.10.2026, 23:59** |
| Weight | 25 % of the final grade (implementation half: laboratory work; analysis half: individual study) |
| Defence | lab session of week 9 |
| Submission | one archive `DE0831_P1_Asgarli_251ADM047.zip` via ORTUS |
| Brief | [`materials/project-1_brief.pdf`](materials/project-1_brief.pdf), [`materials/project-1_step-by-step-guide.md`](materials/project-1_step-by-step-guide.md) |

## Task

Four CUDA.jl exercises, each validated against a CPU reference (`Correct!`) and benchmarked:

1. SAXPY with a grid-stride loop, correct for any grid size.
2. N × N matrix transpose: naive and shared-memory tiled with a (TILE+1) × TILE tile.
3. 256-bin byte histogram: naive (global atomics) and privatised (shared memory), on uniform and
   90 % 0x00 data.
4. Sliding-window Shannon entropy scanner (W = 4096): basic and fused routes, test file with a known
   high-entropy section, plot, throughput and a half-page performance analysis.

Individualisation (student ID `251ADM047`, digits 251047): **N = 1152, SEED = 51047, α = 7**.

## Status

- [x] All four exercises implemented; both routes of exercise 4.
- [x] Correctness checks, known-answer examples of the guide and boundary tests pass
      (`test/runtests.jl`).
- [x] Measured on Google Colab, Tesla T4, 23.10.2026; every script printed `Correct!`
      ([logs](outputs/colab-t4_2026-10-23/logs)).
- [x] Submission archive built: [`outputs/submission/DE0831_P1_Asgarli_251ADM047.zip`](outputs/submission/DE0831_P1_Asgarli_251ADM047.zip).
- [x] Uploaded to ORTUS.
- [x] Defence 02.11.2026: passed.
- [x] **Graded: 9.75 / 10** (implementation 10/10, analysis 9.5/10): [`outputs/feedback_2026-11-02.md`](outputs/feedback_2026-11-02.md).

## Feedback and lessons

Four remarks, all in the analysis side (full text and causes in the feedback file):

1. A comment in `p1_ex3.jl` says "16 blocks per SM": that is the grid size, not the number of
   resident blocks (4 × 256 threads on a T4). Do not confuse grid size with occupancy.
2. The "0.056 ms for the 23.6 MB count matrix" figure came from subtracting two timings instead
   of measuring the array step directly, and one of the two was anomalous. A number that breaks a
   physical bound (here: 2 TB/s on a 320 GB/s GPU) is a measurement error, not evidence, and must
   not be used for a conclusion, even with a caveat.
3. The analysis cites `CUDA.@device_code_ptx` output that the submitted scripts never produce
   (it came from a separate check in `tools/`). Evidence has to be reproducible from the
   submission itself.
4. The entropy plot was drawn with matplotlib in the Colab notebook because GR failed there; the
   task requires Julia only. Use a headless-capable Julia plotting path next time.

The submitted files are kept exactly as handed in. If the issues are fixed later for the exam
(19 January 2027), do it in a new run folder under `outputs/` and leave the submission untouched.

## Results (Tesla T4)

| Exercise | Result |
|---|---|
| 1. SAXPY | 235.4 GB/s at 1024 blocks on 4.7 M elements (copy: 233 GB/s); at N = 1152 launch overhead dominates (~11–14 µs) |
| 2. Transpose | best tiled 163.0 GB/s (TILE 16) vs naive 101.8 GB/s; at TILE 32 padding doubles bandwidth (63.6 → 130.9 GB/s) |
| 3. Histogram | privatised 13.1× faster on uniform data, 20.1× on 90 % 0x00 data |
| 4. Entropy | fused 56.1 GB/s (56 076 MB/s) on 94 MB, 24 % of copy bandwidth; CPU reference 970 MB/s; high-entropy windows 129–192 found |

Full tables: [`DE0831_P1/results/benchmarks.md`](DE0831_P1/results/benchmarks.md); analysis:
[`DE0831_P1/results/analysis.md`](DE0831_P1/results/analysis.md); plot:
[`DE0831_P1/results/entropy_plot.png`](DE0831_P1/results/entropy_plot.png).

## Layout

```
project-1_gpu-fundamentals-julia/
├── README.md            this file
├── materials/           the brief and the step-by-step guide from the course
├── DE0831_P1/           the Julia project, laid out as the brief's submission folder
│   ├── README.md        device, how to run, methodology, known issues
│   ├── Project.toml, Manifest.toml
│   ├── src/             p1_common.jl, p1_ex1.jl … p1_ex4.jl
│   ├── test/            runtests.jl
│   └── results/         benchmarks.md, analysis.md, entropy_plot.png, entropy_profile.csv
├── tools/               Colab notebook, CPU emulator of CUDA.jl, PTX compile check
└── outputs/
    ├── colab-t4_2026-10-23/   logs of the T4 run and the archive the notebook downloaded
    └── submission/            the archive for ORTUS
```

## Notes

- The analysis in the archive the notebook downloaded chose "atomic contention" as the limiter
  because all-0x00 input was 2.2× slower; on the test-file mix the time equals the uniform-data
  time, so the limiter is instruction throughput.  The selection logic in `p1_ex4.jl` was fixed and
  `analysis.md` regenerated from the same T4 measurements; the final archive in
  `outputs/submission/` contains the fixed version.
- On Colab the plot is drawn with matplotlib from `results/entropy_profile.csv`; elsewhere
  `p1_ex4.jl` draws it with Plots.jl.
