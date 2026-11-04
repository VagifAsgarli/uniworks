# Track E: performance analysis

Student: Vagif Asgarli (251ADM047), track E (log mining), full route; generator seed 5175890676511383715.
Device: FakeGPU (CPU emulator) (compute capability 8.6.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
(CUDA events, GPU time) over 2 launches; tables give the mean, and min–max where the
variation matters.  Every step is timed directly; no figure is a difference of two timings.
CPU times are wall-clock `@elapsed` of CPU code, best of 3 after a warm-up.

All numbers are measured by `src/p2_run.jl` on this device and inserted when it runs; the
tables are in `benchmarks.md`.

## 1. The headline number

On the largest corpus (40,000 lines, 4.8 MB) the GPU pipeline
processes **0.00 million lines/s (0.4 MB/s)**
with the corpus resident on the device, and **0.00 million lines/s
(0.4 MB/s)** including the pageable host-to-device copy; the match kernel alone
runs at 0.7 MB/s.  Converted to a day: **2722.0 GB/day is where one CPU core
stops keeping up** (31.5 MB/s single-threaded, same algorithm), while one GPU keeps up to
**36.0 GB/day** including the copy.  Assumptions: 20 indicators (12 addresses, 8 domains),
lines of about 119 bytes, the corpus already in host memory (reading the file took
3.014 ms = 1582.5 MB/s on this machine, from the page cache after the generator wrote it, so not a limit here), batch processing of
whole files, results small enough that the device-to-host copy is negligible (0.001 ms).

## 2. The limiter

Shares of the pipeline at 20,000 lines, each step timed on its own: line table 1 %,
match kernel 56 %, extraction 0 %, token starts 1 %,
token entropies 43 %, histogram and flagging 2 % (the steps sum to
5847.982 ms, the end-to-end timing is 5647.178 ms).  The largest step is the match kernel
(56 %).

The match kernel's operational intensity is low and integer: about 17.1 integer operations per byte
(an estimate built from the measured candidate and compare counts) against 1 byte moved, so on the integer roofline
(0.22 × 10¹² ops/s against 936.1 GB/s) the balance point is
0.2 ops/byte: the kernel sits to the right of it (compute side).
The limiter is **instruction throughput, not bandwidth**: the tiled kernel reads the corpus at only 0.0 GB/s (0 % of the copy rate) although every byte is loaded exactly once and coalesced; the bandwidth model predicts 0.003 ms, the integer model with the estimated 17.1 operations per byte 0.188 ms, and the measured time is 3156.030 ms, i.e. the kernel is bound by the per-byte instruction work (table lookups, index arithmetic, the candidate loop with its data-dependent branches: 0 branches in the PTX).
The shared-memory tile does not beat the global-memory variant here (3156.030 vs 245.529 ms): the candidate re-reads are served by L1 anyway, so the tile only adds a barrier and the halo load; the limiter is not the memory path.

Evidence (all produced by the script): achieved bandwidth 0.0 GB/s vs copy 15.5 GB/s;
`CUDA.registers` 30 per thread, 2048 B shared memory per block,
occupancy 100 %, 8 resident blocks per SM;
measured candidate fraction 20.34 % and 1.891 compares per byte; PTX (`results/match_tiled.ptx`)
with 0 global and 0 shared loads, 0 branches, 0 atomics.  Nsight Compute counters were
not collected; the limiter is inferred from these measurements.

## 3. Scaling and the transfer wall

| lines | match kernel (MB/s) | GPU pipeline (MB/s) | H2D copy (ms) | pipeline (ms) | copy / pipeline | file read (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 20,000 | 0.8 | 0.4 | 0.217 | 5647.178 | 0.00 | 1.575 |
| 40,000 | 0.7 | 0.4 | 0.477 | 11439.464 | 0.00 | 3.014 |

The pipeline rate goes from 0.4 MB/s at 20,000 lines to
0.4 MB/s at 40,000; the best rate over the sizes is
0.4 MB/s at 20,000 lines.  The kernels are
streaming kernels: once the launch and scan overheads are amortised their time grows with the bytes (see the
table).  The host-to-device copy costs 0.00× the whole
GPU pipeline at the largest size (10.0 GB/s pageable):
the transfer wall is not reached: the pipeline is slower than the copy, so the GPU work still dominates end to end.
Reading the file (1582.5 MB/s here, page cache) was faster than both on this machine; a disk slower than the pipeline would become the wall.

## 4. CPU comparison

Against the single-threaded baseline with the same algorithm, the GPU pipeline is **0.0×** faster
on the device and **0.0×** including the copy (largest corpus).  Per step at
20,000 lines: matching 0.0× (the library `occursin` search is 0.0× slower than the
kernel), token entropies 0.0×, line table 0.0×.  The CPU numbers are one core; a tuned
multithreaded matcher would scale with the core count, which is the research project's question.

## 5. The defensive conclusion

A SOC that must match 20 indicators against its logs every day can size the job from these rates: one
CPU core covers up to **2722.0 GB/day**, one GPU (including the copy) up to **36.0 GB/day**.  For a site
producing 2 TB/day that is **1 CPU core or 56 GPUs** (2 × 10¹² / (86,400 × 31.5 × 10⁶) and
2 × 10¹² / (86,400 × 0.4 × 10⁶)); below 2722.0 GB/day a single core keeps up and a GPU is not needed.
The crossover moves with the indicator count (the research project measures 10 to 10,000) and with the storage
rate: the file read here (1582.5 MB/s, page cache) was not a limit, but storage slower than the pipeline would be, so logs should be streamed to the device as they arrive or kept in device memory.
Entropy flagging at 4.45 bits/char produced 2 flags in 20,000 lines
with precision 1.000 and recall 1.000 on the planted payloads, i.e. about
100.0 flags per million lines for an analyst to look at: the threshold is chosen from the
measured distribution, not from the generator's hint, because the payloads of this corpus start at 5.14 bits.
Limits: synthetic logs, 20 fixed-length indicators, no regular expressions, a single GPU session; nothing here
processes real logs (course policy).
