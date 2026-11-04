# Track E: performance analysis

Student: Vagif Asgarli (251ADM047), track E (log mining), full route; generator seed 5175890676511383715.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
(CUDA events, GPU time) over 100 launches; tables give the mean, and min–max where the
variation matters.  Every step is timed directly; no figure is a difference of two timings.
CPU times are wall-clock `@elapsed` of CPU code, best of 3 after a warm-up.

All numbers are measured by `src/p2_run.jl` on this device and inserted when it runs; the
tables are in `benchmarks.md`.

## 1. The headline number

On the largest corpus (4,000,000 lines, 476.6 MB) the GPU pipeline
processes **18.13 million lines/s (2160.8 MB/s)**
with the corpus resident on the device, and **12.32 million lines/s
(1468.6 MB/s)** including the pageable host-to-device copy; the match kernel alone
runs at 16156.5 MB/s.  Converted to a day: **1709.6 GB/day is where one CPU core
stops keeping up** (19.8 MB/s single-threaded, same algorithm), while one GPU keeps up to
**126.9 TB/day** including the copy.  Assumptions: 20 indicators (12 addresses, 8 domains),
lines of about 119 bytes, the corpus already in host memory (reading the file took
313.309 ms = 1521.3 MB/s on this machine, from the page cache after the generator wrote it, so not a limit here), batch processing of
whole files, results small enough that the device-to-host copy is negligible (0.297 ms).

## 2. The limiter

Shares of the pipeline at 1,000,000 lines, each step timed on its own: line table 26 %,
match kernel 26 %, extraction 1 %, token starts 32 %,
token entropies 23 %, histogram and flagging 6 % (the steps sum to
50.060 ms, the end-to-end timing is 49.662 ms).  The largest step is the token-start flags, scan and scatter
(32 %).  The scan steps read and write a 4-byte flag per corpus byte (the lecture-7 scan on `UInt32` flags), so they move more bytes than the match kernel, which reads each byte once; the end-to-end rate is set by them, the match kernel is analysed below.

The match kernels' operational intensity is low and integer: about 17.1 (`match_tiled!`) and
11.1 (`match_tiled_tri!`) integer operations per byte, counted per lane from the measured candidate and
compare counts, against 1 byte moved, so on the integer roofline (4.07 × 10¹² ops/s
against 320.1 GB/s) the balance point is 12.7 ops/byte and both kernels sit
to the left of it (memory side).
A roofline built from lane counts is only an upper bound here, because the lanes of a warp do not work independently.
The limiter is **warp-level control flow, not bandwidth and not the lane-counted integer work**.  The first kernel, `match_tiled!`, reads the corpus at 9.1 GB/s (4 % of the copy rate) although every byte is loaded once and coalesced: the bandwidth model predicts 0.372 ms and the integer model with 17.1 lane operations per byte 0.501 ms, yet it takes 13.073 ms.  The gap is how a warp executes the candidate loop: the loop runs whenever one of the 32 lanes has a candidate, for as long as its slowest lane needs.  With 20.32 % candidate positions, a warp of 32 consecutive positions has none in only 0.00 % of the cases (independent bytes would give 0.07 %), so practically every warp runs the loop, over up to 7 patterns for the busiest first byte, with data-dependent shared-memory lookups (33 branches in its PTX).  `match_tiled_tri!` tests this diagnosis: its three-byte prefix filter leaves 0.953 % candidates, so 71.50 % of the warps skip the loop entirely, and its 4 KB tile amortises the per-block table copy; it takes 6.622 ms, 1.97× faster, at 18.0 GB/s (8 % of the copy rate), which confirms that the warp-level loop, not the byte count, set the time.  What remains between 6.622 ms and the bandwidth roof (0.372 ms) is the per-position filter itself (three shared loads and the hash for every byte, 33 branches in the PTX) and the 29 % of warps that still enter the loop.
The shared-memory tile alone (same first-byte filter) makes `match_tiled!` 1.19× faster than the global-memory variant (15.541 vs 13.073 ms): the global variant re-reads up to 32 bytes per candidate position from L1/L2, the tiled one from shared memory.

Evidence (all produced by the script): achieved bandwidth 9.1 GB/s (`match_tiled!`) and 18.0 GB/s
(`match_tiled_tri!`) vs copy 231.5 GB/s; `CUDA.registers` 26 per thread,
10656 B shared memory per block, occupancy 100 %,
4 resident blocks per SM for `match_tiled_tri!`; measured candidate fractions
20.32 % and 0.953 %, warps without a candidate 0.00 % and 71.50 %;
PTX (`results/match_tiled.ptx`, `results/match_tiled_tri.ptx`) with 33 and 33 branches, 1 and 1
atomics.  Nsight Compute counters were not collected; the limiter is inferred from these measurements and from the
measured effect of the change between the two kernels.

## 3. Scaling and the transfer wall

| lines | match kernel (MB/s) | GPU pipeline (MB/s) | H2D copy (ms) | pipeline (ms) | copy / pipeline | file read (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 125,000 | 20100.2 | 2309.6 | 2.988 | 6.453 | 0.46 | 8.429 |
| 250,000 | 18735.2 | 2414.8 | 6.678 | 12.336 | 0.54 | 7.238 |
| 500,000 | 18531.0 | 2353.1 | 13.226 | 25.321 | 0.52 | 15.045 |
| 1,000,000 | 17997.5 | 2399.8 | 26.707 | 49.662 | 0.54 | 66.630 |
| 2,000,000 | 17191.8 | 2308.7 | 51.149 | 103.231 | 0.50 | 132.324 |
| 4,000,000 | 16156.5 | 2160.8 | 103.973 | 220.588 | 0.47 | 313.309 |

The pipeline rate goes from 2309.6 MB/s at 125,000 lines to
2160.8 MB/s at 4,000,000; the best rate over the sizes is
2414.8 MB/s at 250,000 lines.  The kernels are
streaming kernels: once the launch and scan overheads are amortised their time grows with the bytes (see the
table).  The host-to-device copy costs 0.47× the whole
GPU pipeline at the largest size (4.6 GB/s pageable, 10.9 GB/s pinned):
the transfer wall is not reached: the pipeline is slower than the copy, so the GPU work still dominates end to end.
Reading the file (1521.3 MB/s here, page cache) was faster than both on this machine; a disk slower than the pipeline would become the wall.

## 4. CPU comparison

Against the single-threaded baseline with the same algorithm, the GPU pipeline is **109.2×** faster
on the device and **74.2×** including the copy (largest corpus).  Per step at
1,000,000 lines: matching 131.3× (the library `occursin` search is 390.5× slower than the
kernel), token entropies 330.2×, line table 14.0×.  The CPU numbers are one core; a tuned
multithreaded matcher would scale with the core count, which is the research project's question.

## 5. The defensive conclusion

A SOC that must match 20 indicators against its logs every day can size the job from these rates: one
CPU core covers up to **1709.6 GB/day**, one GPU (including the copy) up to **126.9 TB/day**.  For a site
producing 2 TB/day that is **2 CPU cores or 1 GPU** (2 × 10¹² / (86,400 × 19.8 × 10⁶) and
2 × 10¹² / (86,400 × 1468.6 × 10⁶)); below 1709.6 GB/day a single core keeps up and a GPU is not needed.
The crossover moves with the indicator count (the research project measures 10 to 10,000) and with the storage
rate: the file read here (1521.3 MB/s, page cache) was not a limit, but storage slower than the pipeline would be, so logs should be streamed to the device as they arrive or kept in device memory.
Entropy flagging at 4.12 bits/char produced 243 flags in 1,000,000 lines
with precision 1.000 and recall 1.000 on the planted payloads, i.e. about
243.0 flags per million lines for an analyst to look at: the threshold is chosen from the
measured distribution, not from the generator's hint, because the payloads of this corpus start at 4.49 bits.
Limits: synthetic logs, 20 fixed-length indicators, no regular expressions, a single GPU session; nothing here
processes real logs (course policy).
