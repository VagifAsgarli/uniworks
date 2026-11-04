

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
5.1e-05); 11 hand-made boundary cases.

### Throughput across corpus sizes

Lines/s and MB/s = lines or bytes of the corpus divided by the time.  "Match kernel" is the
multi-pattern kernel alone (the corpus already on the device, line table built); "GPU pipeline"
is one timing around line table + matching + extraction + tokens + entropies + histogram +
flagging; "+ H2D" adds the pageable host-to-device copy of the corpus; "CPU pipeline" is the
single-threaded baseline doing the same steps.

| lines | MB | match kernel (M lines/s) | match (MB/s) | GPU pipeline (M lines/s) | pipeline (MB/s) | pipeline + H2D (M lines/s) | + H2D (MB/s) | CPU pipeline (M lines/s) | CPU (MB/s) | speed-up (GPU) | speed-up (GPU + H2D) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 125,000 | 14.9 | 80.89 | 9644.7 | 17.47 | 2082.5 | 12.33 | 1469.8 | 0.204 | 24.3 | 85.8 | 60.5 |
| 250,000 | 29.8 | 78.99 | 9412.9 | 17.89 | 2131.6 | 12.50 | 1489.8 | 0.200 | 23.8 | 89.6 | 62.7 |
| 500,000 | 59.6 | 78.33 | 9333.8 | 17.78 | 2119.2 | 12.35 | 1472.0 | 0.198 | 23.6 | 89.7 | 62.3 |
| 1,000,000 | 119.2 | 77.55 | 9242.6 | 17.87 | 2129.2 | 12.24 | 1458.4 | 0.194 | 23.1 | 92.0 | 63.0 |
| 2,000,000 | 238.3 | 75.65 | 9014.5 | 17.37 | 2069.8 | 11.91 | 1419.4 | 0.166 | 19.8 | 104.4 | 71.6 |
| 4,000,000 | 476.6 | 72.81 | 8676.0 | 17.06 | 2032.3 | 11.85 | 1411.9 | 0.173 | 20.6 | 98.5 | 68.5 |

### Breakdown at 1,000,000 lines (119.2 MB), every step timed directly

| step | time (ms) | rate (MB/s or GB/s for copies) |
|---:|---:|---:|
| file read from disk (pageable host memory) | 67.970 | 1753.4 |
| host → device copy, pageable | 25.745 | 4.6 |
| host → device copy, pinned | 9.829 | 12.1 |
| line table: newline flags, scan, scatter | 12.944 | 9207.3 |
| match kernel, tiled (shared memory) | 12.894 (min 12.617, max 13.038) | 9242.6 |
| match kernel, global memory variant | 15.194 | 7843.9 |
| matched lines: compaction + gather | 0.381 |  |
| token starts: flags, scan, scatter | 16.422 | 7257.1 |
| token entropy kernel | 10.515 | 11334.0 |
| entropy histogram | 3.162 |  |
| flagged tokens: compaction | 2.950 |  |
| **GPU pipeline end to end (one timing)** | 55.972 (min 55.417, max 57.510) | 2129.2 |
| device → host copy of the results | 0.104 |  |
| CPU: line table | 128.065 | 930.6 |
| CPU: match (same algorithm) | 751.761 | 158.5 |
| CPU: `occursin` per indicator (library search) | 3002.218 | 39.7 |
| CPU: token starts | 363.556 | 327.8 |
| CPU: token entropies | 3731.668 | 31.9 |
| **CPU pipeline end to end (one timing)** | 5150.535 | 23.1 |

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

### Match kernel: operation counts and resources (1,000,000 lines)

Measured with `match_counts!`: 24,218,326 of 119,177,563 byte positions pass the
first-byte filter (20.32 %), costing 225,742,273 byte comparisons in total
(1.894 per corpus byte).  Estimated integer operations per corpus byte in the tiled
kernel: 17.1.  Useful bytes moved per corpus byte: 1 (the corpus is read once;
the pattern tables are read from shared memory).

| kernel | registers / thread | shared memory / block (B) | local memory (B) | occupancy | resident blocks / SM |
|---:|---:|---:|---:|---:|---:|
| match_tiled! (256 threads) | 22 | 3488 | 0 | 100 % | 4 |
| match_global! (256 threads) | 22 | 2432 | 0 | 100 % | 4 |
| token_entropy! (256 threads) | 30 | 16384 | 32 | 100 % | 4 |

PTX of `match_tiled!` written by this script to `results/match_tiled.ptx`: 211 instructions,
9 global loads, 10 shared loads, 7 shared stores, 1 atomics,
1 barriers, 33 branches.

Reference bandwidths: device-to-device copy 230.7 GB/s (read + write); theoretical DRAM 320.1 GB/s; INT32 throughput 4.07 × 10¹² ops/s.
<!-- END trackE -->
