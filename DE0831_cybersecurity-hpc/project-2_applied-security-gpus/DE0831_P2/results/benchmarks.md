

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
| 125,000 | 14.9 | 165.89 | 19779.7 | 19.28 | 2298.8 | 13.19 | 1573.0 | 0.202 | 24.1 | 95.4 | 65.3 |
| 250,000 | 29.8 | 162.79 | 19397.5 | 19.74 | 2351.7 | 13.39 | 1595.8 | 0.189 | 22.5 | 104.5 | 70.9 |
| 500,000 | 59.6 | 155.97 | 18586.7 | 20.46 | 2438.6 | 13.59 | 1619.2 | 0.198 | 23.6 | 103.1 | 68.5 |
| 1,000,000 | 119.2 | 152.33 | 18153.9 | 20.21 | 2409.0 | 13.40 | 1597.3 | 0.182 | 21.7 | 111.2 | 73.7 |
| 2,000,000 | 238.3 | 155.32 | 18508.4 | 19.56 | 2330.8 | 13.02 | 1551.6 | 0.174 | 20.8 | 112.3 | 74.8 |
| 4,000,000 | 476.6 | 137.25 | 16354.8 | 18.43 | 2196.4 | 12.50 | 1489.2 | 0.176 | 21.0 | 104.6 | 70.9 |

### Breakdown at 1,000,000 lines (119.2 MB), every step timed directly

| step | time (ms) | rate (MB/s or GB/s for copies) |
|---:|---:|---:|
| file read from disk (pageable host memory) | 66.482 | 1792.6 |
| host → device copy, pageable | 25.141 | 4.7 |
| host → device copy, pinned | 10.051 | 11.9 |
| line table: newline flags, scan, scatter | 13.053 | 9130.4 |
| match kernel `match_tiled_tri!`: 4 KB tile, three-byte filter (the pipeline's) | 6.565 (min 6.042, max 6.649) | 18153.9 |
| match kernel `match_tiled!`: 1 KB tile, first-byte filter | 12.516 (min 12.029, max 13.484) | 9522.0 |
| match kernel `match_global!`: no tile, first-byte filter | 14.621 | 8151.1 |
| matched lines: compaction + gather | 0.383 |  |
| token starts: flags, scan, scatter | 15.757 | 7563.3 |
| token entropy kernel | 11.194 | 10646.9 |
| entropy histogram | 0.503 |  |
| flagged tokens: compaction | 2.323 |  |
| **GPU pipeline end to end (one timing)** | 49.471 (min 49.006, max 51.370) | 2409.0 |
| device → host copy of the results | 0.089 |  |
| CPU: line table | 131.638 | 905.3 |
| CPU: match (same algorithm) | 789.628 | 150.9 |
| CPU: `occursin` per indicator (library search) | 2508.051 | 47.5 |
| CPU: token starts | 315.069 | 378.3 |
| CPU: token entropies | 3874.789 | 30.8 |
| **CPU pipeline end to end (one timing)** | 5500.147 | 21.7 |

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

Reference bandwidths: device-to-device copy 230.7 GB/s (read + write); theoretical DRAM 320.1 GB/s; INT32 throughput 4.07 × 10¹² ops/s.
<!-- END trackE -->
