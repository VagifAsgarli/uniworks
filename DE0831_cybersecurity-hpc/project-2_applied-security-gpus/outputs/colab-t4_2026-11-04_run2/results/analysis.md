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
processes **17.06 million lines/s (2032.3 MB/s)**
with the corpus resident on the device, and **11.85 million lines/s
(1411.9 MB/s)** including the pageable host-to-device copy; the match kernel alone
runs at 8676.0 MB/s.  Converted to a day: **1782.1 GB/day is where one CPU core
stops keeping up** (20.6 MB/s single-threaded, same algorithm), while one GPU keeps up to
**121990.7 GB/day** including the copy.  Assumptions: 20 indicators (12 addresses, 8 domains),
lines of about 119 bytes, the corpus already in host memory (reading the file took
326.073 ms = 1461.8 MB/s on this machine, from the page cache after the generator wrote it, so not a limit here), batch processing of
whole files, results small enough that the device-to-host copy is negligible (0.215 ms).

## 2. The limiter

Shares of the pipeline at 1,000,000 lines, each step timed on its own: line table 23 %,
match kernel 23 %, extraction 1 %, token starts 29 %,
token entropies 19 %, histogram and flagging 11 % (the steps sum to
59.268 ms, the end-to-end timing is 55.972 ms).  The largest step is the token-start flags, scan and scatter
(29 %).  The scan steps read and write a 4-byte flag per corpus byte (the lecture-7 scan on `UInt32` flags), so they move more bytes than the match kernel, which reads each byte once; the end-to-end rate is set by them, the match kernel is analysed below.

The match kernel's operational intensity is low and integer: about 17.1 integer operations per byte
(an estimate built from the measured candidate and compare counts) against 1 byte moved, so on the integer roofline
(4.07 × 10¹² ops/s against 320.1 GB/s) the balance point is
12.7 ops/byte: the kernel sits to the right of it (compute side).
The limiter is **instruction throughput, not bandwidth**: the tiled kernel reads the corpus at only 9.2 GB/s (4 % of the copy rate) although every byte is loaded exactly once and coalesced; the bandwidth model predicts 0.372 ms, the integer model with the estimated 17.1 operations per byte 0.501 ms, and the measured time is 12.894 ms, i.e. the kernel is bound by the per-byte instruction work (table lookups, index arithmetic, the candidate loop with its data-dependent branches: 33 branches in the PTX).
The shared-memory tile makes the kernel 1.18× faster than the global-memory variant (15.194 vs 12.894 ms): the global variant re-reads up to 32 bytes per candidate position from L1/L2, the tiled one from shared memory.

Evidence (all produced by the script): achieved bandwidth 9.2 GB/s vs copy 230.7 GB/s;
`CUDA.registers` 22 per thread, 3488 B shared memory per block,
occupancy 100 %, 4 resident blocks per SM;
measured candidate fraction 20.32 % and 1.894 compares per byte; PTX (`results/match_tiled.ptx`)
with 9 global and 10 shared loads, 33 branches, 1 atomics.  Nsight Compute counters were
not collected; the limiter is inferred from these measurements.

## 3. Scaling and the transfer wall

| lines | match kernel (MB/s) | GPU pipeline (MB/s) | H2D copy (ms) | pipeline (ms) | copy / pipeline | file read (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 125,000 | 9644.7 | 2082.5 | 2.984 | 7.157 | 0.42 | 7.757 |
| 250,000 | 9412.9 | 2131.6 | 6.020 | 13.975 | 0.43 | 7.049 |
| 500,000 | 9333.8 | 2119.2 | 12.362 | 28.116 | 0.44 | 31.710 |
| 1,000,000 | 9242.6 | 2129.2 | 25.745 | 55.972 | 0.46 | 67.970 |
| 2,000,000 | 9014.5 | 2069.8 | 52.765 | 115.147 | 0.46 | 129.981 |
| 4,000,000 | 8676.0 | 2032.3 | 103.046 | 234.535 | 0.44 | 326.073 |

The pipeline rate goes from 2082.5 MB/s at 125,000 lines to
2032.3 MB/s at 4,000,000; the best rate over the sizes is
2131.6 MB/s at 250,000 lines.  The kernels are
streaming kernels: once the launch and scan overheads are amortised their time grows with the bytes (see the
table).  The host-to-device copy costs 0.44× the whole
GPU pipeline at the largest size (4.6 GB/s pageable, 11.2 GB/s pinned):
the transfer wall is not reached: the pipeline is slower than the copy, so the GPU work still dominates end to end.
Reading the file (1461.8 MB/s here, page cache) was faster than both on this machine; a disk slower than the pipeline would become the wall.

## 4. CPU comparison

Against the single-threaded baseline with the same algorithm, the GPU pipeline is **98.5×** faster
on the device and **68.5×** including the copy (largest corpus).  Per step at
1,000,000 lines: matching 58.3× (the library `occursin` search is 232.8× slower than the
kernel), token entropies 354.9×, line table 9.9×.  The CPU numbers are one core; a tuned
multithreaded matcher would scale with the core count, which is the research project's question.

## 5. The defensive conclusion

A SOC that must match 20 indicators against its logs every day can size the job from these rates: one
CPU core covers up to **1782.1 GB/day**, one GPU (including the copy) up to **121990.7 GB/day**.  For a site
producing 2 TB/day that is **2 CPU cores or 1 GPU** (2 × 10¹² / (86,400 × 20.6 × 10⁶) and
2 × 10¹² / (86,400 × 1411.9 × 10⁶)); below 1782.1 GB/day a single core keeps up and a GPU is not needed.
The crossover moves with the indicator count (the research project measures 10 to 10,000) and with the storage
rate: the file read here (1461.8 MB/s, page cache) was not a limit, but storage slower than the pipeline would be, so logs should be streamed to the device as they arrive or kept in device memory.
Entropy flagging at 4.12 bits/char produced 243 flags in 1,000,000 lines
with precision 1.000 and recall 1.000 on the planted payloads, i.e. about
243.0 flags per million lines for an analyst to look at: the threshold is chosen from the
measured distribution, not from the generator's hint, because the payloads of this corpus start at 4.49 bits.
Limits: synthetic logs, 20 fixed-length indicators, no regular expressions, a single GPU session; nothing here
processes real logs (course policy).
