

<!-- BEGIN trackE -->
## Track E: log mining (full route)

Student: Vagif Asgarli (251ADM047), track E (log mining), full route; generator seed 5175890676511383715.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
(CUDA events, GPU time) over 100 launches; tables give the mean, and min–max where the
variation matters.  Every step is timed directly; no figure is a difference of two timings.
CPU times are wall-clock `@elapsed` of CPU code, best of 3 after a warm-up.

Validation on the 1,000,000-line corpus: line table equal to the CPU's; the match set of
the tiled kernel, of the global-memory kernel, of the CPU baseline and of the `occursin` baseline
all equal `truth_251ADM047.csv` (894 lines); extracted line text equal to the
corpus lines; 22,350,735 tokens with entropies equal to the CPU's (max difference
2.9e-06) and to `entropy_truth` for the 243 payloads (max difference
5.1e-05); 18 hand-made boundary cases.

### Throughput across corpus sizes

Lines/s and MB/s = lines or bytes of the corpus divided by the time.  "Match kernel" is the
multi-pattern kernel `match_tiled_tri!` alone (the corpus already on the device, line table built); "GPU pipeline"
is one timing around line table + matching + extraction + tokens + entropies + histogram +
flagging; "+ H2D" adds the pageable host-to-device copy of the corpus; "CPU pipeline" is the
single-threaded baseline doing the same steps.

| lines | MB | match kernel (M lines/s) | match (MB/s) | GPU pipeline (M lines/s) | pipeline (MB/s) | pipeline + H2D (M lines/s) | + H2D (MB/s) | CPU pipeline (M lines/s) | CPU (MB/s) | speed-up (GPU) | speed-up (GPU + H2D) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 125,000 | 14.9 | 168.58 | 20100.2 | 19.37 | 2309.6 | 13.24 | 1578.7 | 0.201 | 23.9 | 96.5 | 66.0 |
| 250,000 | 29.8 | 157.23 | 18735.2 | 20.27 | 2414.8 | 13.15 | 1566.7 | 0.202 | 24.1 | 100.1 | 65.0 |
| 500,000 | 59.6 | 155.51 | 18531.0 | 19.75 | 2353.1 | 12.97 | 1545.7 | 0.196 | 23.3 | 100.8 | 66.2 |
| 1,000,000 | 119.2 | 151.01 | 17997.5 | 20.14 | 2399.8 | 13.09 | 1560.5 | 0.177 | 21.1 | 113.9 | 74.1 |
| 2,000,000 | 238.3 | 144.27 | 17191.8 | 19.37 | 2308.7 | 12.96 | 1543.8 | 0.173 | 20.6 | 111.8 | 74.8 |
| 4,000,000 | 476.6 | 135.59 | 16156.5 | 18.13 | 2160.8 | 12.32 | 1468.6 | 0.166 | 19.8 | 109.2 | 74.2 |

### Breakdown at 1,000,000 lines (119.2 MB), every step timed directly

| step | time (ms) | rate (MB/s or GB/s for copies) |
|---:|---:|---:|
| file read from disk (pageable host memory) | 66.630 | 1788.6 |
| host → device copy, pageable | 26.707 | 4.5 |
| host → device copy, pinned | 10.417 | 11.4 |
| line table: newline flags, scan, scatter | 12.956 | 9198.6 |
| match kernel `match_tiled_tri!`: 4 KB tile, three-byte filter (the pipeline's) | 6.622 (min 6.173, max 6.765) | 17997.5 |
| match kernel `match_tiled!`: 1 KB tile, first-byte filter | 13.073 (min 12.900, max 13.699) | 9116.1 |
| match kernel `match_global!`: no tile, first-byte filter | 15.541 | 7668.7 |
| matched lines: compaction + gather | 0.369 |  |
| token starts: flags, scan, scatter | 15.807 | 7539.4 |
| token entropy kernel | 11.385 | 10468.0 |
| entropy histogram | 0.531 |  |
| flagged tokens: compaction | 2.390 |  |
| **GPU pipeline end to end (one timing)** | 49.662 (min 49.052, max 51.677) | 2399.8 |
| device → host copy of the results | 0.101 |  |
| CPU: line table | 181.115 | 658.0 |
| CPU: match (same algorithm) | 869.297 | 137.1 |
| CPU: `occursin` per indicator (library search) | 2586.183 | 46.1 |
| CPU: token starts | 360.353 | 330.7 |
| CPU: token entropies | 3759.623 | 31.7 |
| **CPU pipeline end to end (one timing)** | 5658.072 | 21.1 |

### Entropy threshold

Token entropies of all 22,350,735 tokens were histogrammed on the GPU (0.05-bit
bins, `results/entropy_hist.csv`).  The ordinary tokens end at 3.78 bits (the highest
entropy of any token shorter than 32 characters), the 243 long tokens start at
4.49 bits; the widest empty band of the histogram above the median token is 3.80–4.45 bits and
its midpoint, **4.12 bits/char**, is the threshold.  A token of *n* characters has at most
log2(*n*) bits of entropy, so a threshold of 4.12 can only be exceeded by tokens of
18+ characters, which is why ordinary log fields never reach it.

| threshold (bits/char) | flagged | true positives | false positives | false negatives | precision | recall |
|---:|---:|---:|---:|---:|---:|---:|
| 3.50 | 452 | 243 | 209 | 0 | 0.538 | 1.000 |
| 4.00 | 243 | 243 | 0 | 0 | 1.000 | 1.000 |
| **4.12 (chosen)** | 243 | 243 | 0 | 0 | 1.000 | 1.000 |
| 4.50 | 242 | 242 | 0 | 1 | 1.000 | 0.996 |
| 5.00 | 194 | 194 | 0 | 49 | 1.000 | 0.798 |
| 5.50 | 42 | 42 | 0 | 201 | 1.000 | 0.173 |

### Match kernels: operation counts and resources (1,000,000 lines)

Measured with `match_counts!` on the device: 24,218,326 of 119,177,563 byte positions pass the
first-byte filter (20.32 %), costing 225,742,273 byte comparisons (1.894 per corpus
byte); 1,135,767 positions (0.953 %) also pass the three-byte filter, costing
49,157,911 comparisons (0.412 per byte).  Seen per warp of 32 consecutive positions
(computed on the CPU from the same tables): 0.00 % of the warps have no candidate under the
first-byte filter and skip the candidate loop, 71.50 % under the three-byte filter.
Estimated integer operations per corpus byte, counted per lane: 17.1 (`match_tiled!`),
11.1 (`match_tiled_tri!`).  Useful bytes moved per corpus byte: 1 (the corpus is read once; the
tables are read from shared memory); per block the table copy is 2,432 B for a 1,024 B tile
and 6,528 B for a 4,096 B tile.

| kernel | registers / thread | shared memory / block (B) | local memory (B) | occupancy | resident blocks / SM |
|---:|---:|---:|---:|---:|---:|
| match_tiled_tri! (256 threads) | 26 | 10656 | 0 | 100 % | 4 |
| match_tiled! (256 threads) | 22 | 3488 | 0 | 100 % | 4 |
| match_global! (256 threads) | 22 | 2432 | 0 | 100 % | 4 |
| token_entropy! (256 threads) | 30 | 16384 | 32 | 100 % | 4 |

PTX written by this script: `results/match_tiled_tri.ptx` has 236 instructions, 11 global loads,
13 shared loads, 9 shared stores, 1 atomics, 1 barriers, 33 branches;
`results/match_tiled.ptx` has 211 instructions, 9 global loads, 10 shared loads,
7 shared stores, 1 atomics, 1 barriers, 33 branches.

Reference bandwidths: device-to-device copy 231.5 GB/s (read + write); theoretical DRAM 320.1 GB/s; INT32 throughput 4.07 × 10¹² ops/s.
<!-- END trackE -->
