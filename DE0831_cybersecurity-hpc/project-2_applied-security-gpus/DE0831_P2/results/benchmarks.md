

<!-- BEGIN trackE -->
## Track E: log mining (full route)

Student: Vagif Asgarli (251ADM047), track E (log mining), full route; generator seed 5175890676511383715.
Device: FakeGPU (CPU emulator) (compute capability 8.6.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
(CUDA events, GPU time) over 2 launches; tables give the mean, and min–max where the
variation matters.  Every step is timed directly; no figure is a difference of two timings.
CPU times are wall-clock `@elapsed` of CPU code, best of 3 after a warm-up.

Validation on the 20,000-line corpus: line table equal to the CPU's; the match set of
the tiled kernel, of the global-memory kernel, of the CPU baseline and of the `occursin` baseline
all equal `truth_251ADM047.csv` (20 lines); extracted line text equal to the
corpus lines; 447,722 tokens with entropies equal to the CPU's (max difference
1.9e-06) and to `entropy_truth` for the 2 payloads (max difference
8.3e-06); 11 hand-made boundary cases.

### Throughput across corpus sizes

Lines/s and MB/s = lines or bytes of the corpus divided by the time.  "Match kernel" is the
multi-pattern kernel alone (the corpus already on the device, line table built); "GPU pipeline"
is one timing around line table + matching + extraction + tokens + entropies + histogram +
flagging; "+ H2D" adds the pageable host-to-device copy of the corpus; "CPU pipeline" is the
single-threaded baseline doing the same steps.

| lines | MB | match kernel (M lines/s) | match (MB/s) | GPU pipeline (M lines/s) | pipeline (MB/s) | pipeline + H2D (M lines/s) | + H2D (MB/s) | CPU pipeline (M lines/s) | CPU (MB/s) | speed-up (GPU) | speed-up (GPU + H2D) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20,000 | 2.4 | 0.01 | 0.8 | 0.00 | 0.4 | 0.00 | 0.4 | 0.254 | 30.4 | 0.0 | 0.0 |
| 40,000 | 4.8 | 0.01 | 0.7 | 0.00 | 0.4 | 0.00 | 0.4 | 0.264 | 31.5 | 0.0 | 0.0 |

### Breakdown at 20,000 lines (2.4 MB), every step timed directly

| step | time (ms) | rate (MB/s or GB/s for copies) |
|---:|---:|---:|
| file read from disk (pageable host memory) | 1.575 | 1516.4 |
| host → device copy, pageable | 0.217 | 11.0 |
| host → device copy, pinned | n/a | n/a |
| line table: newline flags, scan, scatter | 51.409 | 46.4 |
| match kernel, tiled (shared memory) | 3156.030 (min 3003.062, max 3308.998) | 0.8 |
| match kernel, global memory variant | 245.529 | 9.7 |
| matched lines: compaction + gather | 18.458 |  |
| token starts: flags, scan, scatter | 65.750 | 36.3 |
| token entropy kernel | 2452.509 | 1.0 |
| entropy histogram | 90.302 |  |
| flagged tokens: compaction | 13.524 |  |
| **GPU pipeline end to end (one timing)** | 5647.178 (min 5638.147, max 5656.209) | 0.4 |
| device → host copy of the results | 0.001 |  |
| CPU: line table | 1.380 | 1730.1 |
| CPU: match (same algorithm) | 12.602 | 189.5 |
| CPU: `occursin` per indicator (library search) | 31.015 | 77.0 |
| CPU: token starts | 23.014 | 103.8 |
| CPU: token entropies | 56.900 | 42.0 |
| **CPU pipeline end to end (one timing)** | 78.674 | 30.4 |

### Entropy threshold

Token entropies of all 447,722 tokens were histogrammed on the GPU (0.05-bit
bins, `results/entropy_hist.csv`).  The ordinary tokens end at 3.78 bits (the highest
entropy of any token shorter than 32 characters), the 2 long tokens start at
5.14 bits; the widest empty band of the histogram above the median token is 3.80–5.10 bits and
its midpoint, **4.45 bits/char**, is the threshold.  A token of *n* characters has at most
log2(*n*) bits of entropy, so a threshold of 4.45 can only be exceeded by tokens of
22+ characters, which is why ordinary log fields never reach it.

| threshold (bits/char) | flagged | true positives | false positives | false negatives | precision | recall |
|---:|---:|---:|---:|---:|---:|---:|
| 3.50 | 7 | 2 | 5 | 0 | 0.286 | 1.000 |
| 4.00 | 2 | 2 | 0 | 0 | 1.000 | 1.000 |
| **4.45 (chosen)** | 2 | 2 | 0 | 0 | 1.000 | 1.000 |
| 4.50 | 2 | 2 | 0 | 0 | 1.000 | 1.000 |
| 5.00 | 2 | 2 | 0 | 0 | 1.000 | 1.000 |
| 5.50 | 0 | 0 | 0 | 2 | 1.000 | 0.000 |

### Match kernel: operation counts and resources (20,000 lines)

Measured with `match_counts!`: 485,601 of 2,387,898 byte positions pass the
first-byte filter (20.34 %), costing 4,514,748 byte comparisons in total
(1.891 per corpus byte).  Estimated integer operations per corpus byte in the tiled
kernel: 17.1.  Useful bytes moved per corpus byte: 1 (the corpus is read once;
the pattern tables are read from shared memory).

| kernel | registers / thread | shared memory / block (B) | local memory (B) | occupancy | resident blocks / SM |
|---:|---:|---:|---:|---:|---:|
| match_tiled! (256 threads) | 30 | 2048 | 0 | 100 % | 8 |
| match_global! (256 threads) | 30 | 2048 | 0 | 100 % | 8 |
| token_entropy! (256 threads) | 30 | 2048 | 0 | 100 % | 8 |

PTX of `match_tiled!` written by this script to `results/match_tiled.ptx`: 0 instructions,
0 global loads, 0 shared loads, 0 shared stores, 0 atomics,
0 barriers, 0 branches.

Reference bandwidths: device-to-device copy 15.5 GB/s (read + write); theoretical DRAM 936.1 GB/s; INT32 throughput 0.22 × 10¹² ops/s.
<!-- END trackE -->
