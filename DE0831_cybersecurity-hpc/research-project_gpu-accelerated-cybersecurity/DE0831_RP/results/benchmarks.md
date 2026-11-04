

<!-- BEGIN topic10 -->
## Topic 10: log indicator matching as the list grows

Student: Vagif Asgarli (251ADM047), research project, topic 10 (log indicator matching); generator seed 5175890676511383715.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
(CUDA events, GPU time) over 100 launches; tables give the mean, and min–max where the
variation matters.  Every step is timed directly; no figure is a difference of two timings.
CPU times are wall-clock `@elapsed` of CPU code, best of 3 after a warm-up.

Validation on the 1,000,000-line corpus: the generator's 20 indicators give 894 (line, indicator)
pairs, found identically by the CPU hash-set matcher (1 to 2 chunks), the `occursin` baseline, the GPU hash-set
matcher (global table and shared keys) and the GPU per-indicator matcher; for every list size the GPU methods and
the `occursin` baseline (lists up to 300) equal the CPU matcher, which equals the truth restricted to the
list; 11 hand-made cases.  Tokens of the corpus: 20,626,582.

### List-size sweep (1,000,000 lines, 119.2 MB)

"GPU hash-set: pipeline" is one timing around line table + token scan + hash match + extraction; "hash kernel"
is the match kernel alone (tokens already found); "shared keys" the variant with the table keys in shared
memory (capacity ≤ 4,096); "GPU per-indicator" is one launch of the Project 2 kernel per group of
32 indicators (lists up to 3,000); "CPU hash-set" is the tuned matcher with 2 Julia tasks on
Intel(R) Xeon(R) CPU @ 2.00GHz (2 hardware threads); "occursin" the library route (lists up to 300).

| N | table (KB) | GPU hash-set: pipeline (ms) | M lines/s | hash kernel (ms) | shared keys (ms) | probes/token | GPU direct: pipeline (ms) | M lines/s | direct kernel (ms) | GPU per-indicator (ms) | groups | M lines/s | CPU hash-set 2 thr. (s) | M lines/s | CPU 1 thr. (s) | occursin (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.7 | 32.881 | 30.41 | 2.098 | 2.216 | 1.43 | 24.775 | 40.36 | 7.791 | 5.588 | 1 | 178.97 | 0.315 | 3.17 | 0.395 | 1.069 |
| 30 | 1.5 | 33.231 | 30.09 | 2.534 | 2.580 | 2.37 | 20.722 | 48.26 | 8.181 | 7.657 | 1 | 130.60 | 0.403 | 2.48 | 0.527 | 3.121 |
| 100 | 5.6 | 33.040 | 30.27 | 2.565 | 2.630 | 2.05 | 20.815 | 48.04 | 8.026 | 23.661 | 4 | 42.26 | 0.634 | 1.58 | 0.439 | 11.101 |
| 300 | 21.1 | 33.014 | 30.29 | 1.890 | 2.465 | 1.41 | 19.826 | 50.44 | 7.300 | 58.598 | 10 | 17.07 | 0.382 | 2.62 | 0.434 | 33.239 |
| 1,000 | 49.4 | 33.287 | 30.04 | 2.664 | 3.106 | 2.28 | 20.434 | 48.94 | 8.010 | 186.605 | 32 | 5.36 | 0.380 | 2.63 | 0.651 | n/a |
| 3,000 | 179.2 | 33.252 | 30.07 | 2.724 | n/a | 1.70 | 20.279 | 49.31 | 7.830 | 561.365 | 94 | 1.78 | 0.338 | 2.96 | 0.424 | n/a |
| 10,000 | 684.3 | 33.109 | 30.20 | 2.583 | n/a | 1.53 | 20.224 | 49.45 | 7.650 | n/a | 313 | n/a | 0.535 | 1.87 | 0.427 | n/a |

### Corpus-size sweep (list of 1,000 indicators)

| lines | MB | GPU pipeline (ms) | MB/s | GPU direct pipeline (ms) | MB/s | + H2D pageable (ms) | MB/s | H2D pinned (ms) | CPU 2 thr. (s) | MB/s | speed-up (GPU) | speed-up (GPU + H2D) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 125,000 | 14.9 | 4.340 | 3433.8 | 2.846 | 5237.1 | 7.367 | 2023.2 | 2.150 | 0.047 | 318.2 | 10.8 | 6.4 |
| 250,000 | 29.8 | 12.771 | 2332.6 | 5.322 | 5596.9 | 19.126 | 1557.6 | 4.830 | 0.095 | 314.7 | 7.4 | 5.0 |
| 500,000 | 59.6 | 16.461 | 3619.6 | 10.528 | 5659.4 | 29.270 | 2035.6 | 5.674 | 0.216 | 275.8 | 13.1 | 7.4 |
| 1,000,000 | 119.2 | 33.316 | 3577.2 | 20.527 | 5805.8 | 59.024 | 2019.2 | 11.303 | 0.411 | 289.6 | 12.4 | 7.0 |
| 2,000,000 | 238.3 | 67.283 | 3542.3 | 41.140 | 5793.3 | 120.469 | 1978.4 | 23.981 | 0.788 | 302.3 | 11.7 | 6.5 |
| 4,000,000 | 476.6 | 144.976 | 3287.7 | 82.745 | 5760.3 | 249.723 | 1908.7 | 42.337 | 1.510 | 315.6 | 10.4 | 6.0 |

### CPU threads (1,000,000 lines, list of 1,000)

| Julia tasks (chunks) | time (s) | M lines/s | speed-up over 1 |
|---:|---:|---:|---:|
| 1 | 0.651 | 1.54 | 1.00 |
| 2 | 0.380 | 2.63 | 1.71 |

### Evidence

| kernel | registers / thread | shared memory / block (B) | local memory (B) | occupancy | resident blocks / SM |
|---:|---:|---:|---:|---:|---:|
| hash_match! (256 threads) | 28 | 0 | 0 | 100 % | 4 |
| hash_match_shared! (256 threads) | 28 | 16384 | 0 | 100 % | 4 |
| word_flags! (256 threads) | 14 | 0 | 0 | 100 % | 4 |

PTX of `hash_match!` written by this script to `results/hash_match.ptx`: 111 instructions, 12 global loads,
0 shared loads, 0 atomics, 15 branches.  Device-to-device copy 240.7 GB/s (read + write); theoretical DRAM 320.1 GB/s; L2 cache 4096 KB.
Table footprint per list size (keys + indices + offsets + lengths, 16 B per slot, load ≤ 0.5) and the packed
indicator buffer: see the CSV; the table of 10,000 indicators takes 512.0 KB (12 % of L2).
<!-- END topic10 -->
