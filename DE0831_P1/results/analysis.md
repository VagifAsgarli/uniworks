# Exercise 4: performance analysis of the entropy scanner

Student: Vagif Asgarli (251ADM047), N = 1152, seed = 51047.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then `CUDA.@elapsed` (CUDA events, GPU
time) over 100 launches; the tables report the mean time per launch.  Kernel times exclude
host/device transfers, file I/O, plotting and CPU checks unless a row says otherwise.

All numbers below are measured by `src/p1_ex4.jl` on this device and inserted when the script
runs; the timing tables are in `benchmarks.md` (Exercise 4).

## 1. Roofline placement

Operation-count convention: per window the fused kernel performs 256 divisions, 256
multiplications and 255 additions, i.e. 767 FLOPs, plus 256 base-2
logarithms counted separately (a logarithm costs far more than an addition).  Byte convention:
useful global bytes, not measured DRAM traffic: each 4096-byte window is read once and one
Float32 is written, 4100 bytes per window.  The operational intensity is therefore
**0.187 FLOP/byte** (plus 0.062 log2/byte).  The basic route does the
same arithmetic but also writes the 256 × windows count matrix (1 KB per 4 KB window) and reads it
back in the array operations, so its intensity is lower still.  On this GPU the ridge point is
**25.4 FLOP/byte** (8140.8 GFLOP/s FP32 peak / 320.1 GB/s theoretical DRAM bandwidth), so the scanner sits about 136× to the left of
the ridge, deep in the **memory-bound** region: the roofline caps it at
0.187 FLOP/B × 320.1 GB/s = 59.9 GFLOP/s, i.e. at streaming the input at
full DRAM bandwidth.  Measured: on the 94.4 MB input the fused kernel takes
1.683 ms, which is 56.1 GB/s of DRAM traffic and 10.5 GFLOP/s,
i.e. **24 % of the measured device-to-device copy bandwidth (237.5 GB/s)** and 18 % of the theoretical 320.1 GB/s.
The roofline does not model atomic contention or special-function (log2) throughput, so it is
an upper bound here, not a prediction.

## 2. The limiter

**The limiter is instruction throughput / memory-level parallelism.**  The kernel reaches
only 24 % of copy bandwidth, yet occupancy is adequate (100 %)
and on realistic data the time hardly depends on the content: the test-file mix takes
1.02× and letters (26 distinct values) 0.99× the uniform-data time, so atomic
contention is not what limits it there.  Contention does appear on degenerate input: on all-0x00 bytes, where all 256 threads of a block update one bin, the kernel is 2.21× slower than on uniform bytes, which matters for zero-filled regions (unallocated space, padding) but not for the test-file mix.  What remains is the instruction mix: every
input byte costs one 1-byte load, one shared-memory atomic and the index arithmetic, and
a warp's load fetches only 32 bytes, so the SMs issue many instructions per byte and keep
few bytes in flight; each block also does only 16 loop iterations before it pays for
barriers, the reduction and its own launch.

Observed on this GPU (Nsight Compute counters were not collected, so the limiter named above is
an inference from these observations, not a profiler measurement):
- `CUDA.registers`: 33 registers per thread (fused), 34 (basic kernel);
  shared memory 2048 bytes per block, local memory (spills) 0 bytes.
- Occupancy (`CUDA.occupancy`, 256 threads per block): 100 %, 4 resident blocks per SM.
- Achieved bandwidth: 56.1 GB/s = 24 % of copy bandwidth.
- Generated code (`CUDA.@device_code_ptx`): the counting loop is fully unrolled into 16
  single-byte global loads and 16 `atom.acq_rel.gpu.shared.add.u32` per thread, i.e. one
  shared-memory atomic per input byte, and CUDA.jl's `@atomic` always uses acquire-release
  ordering (CUDA C's `atomicAdd` is relaxed).
- Content dependence (fused kernel, same 94.4 MB size): all-0x00 bytes 3.664 ms,
  letters a-z 1.637 ms, uniform random bytes 1.658 ms, test-file mix 1.683 ms;
  all-0x00 is 2.21× and letters 0.99× the uniform time.
- Basic route on the same input: counting kernel alone 2.695 ms, whole scan (kernel +
  array step) 2.751 ms, so writing the count matrix and reading it back costs
  0.056 ms (2 % of the basic scan); the fused kernel, which
  removes that step, takes 1.683 ms. The counting kernel alone was slower than the complete fused kernel although its only extra work is writing the 1 KB count column per window (23.6 MB in total, coalesced, ≈ 0.099 ms at copy bandwidth); this ordering is reported as measured and was not investigated with a profiler.
- Divergence is ruled out as the limiter: the only data-dependent branches are the bounds
  check (false only in a partial last window), the `c > 0` test on one value per thread and
  the reduction's `t <= s`, which is warp-uniform for s ≥ 32; the work per thread is identical.

| kernel | registers / thread | shared memory / block (B) | local memory (B) | occupancy | resident blocks / SM |
|---:|---:|---:|---:|---:|---:|
| window_hist! (basic) | 34 | 1024 | 0 | 100 % | 4 |
| entropy_fused! | 33 | 2048 | 0 | 100 % | 4 |

## 3. One further optimisation (not implemented)

**Vectorised loads: read 4 bytes per load (`UInt32`) and unpack them in registers.**  Each
thread would issue 4 loads of 4 bytes instead of 16 loads of 1 byte, so a warp request moves
128 bytes instead of 32 and the load instruction count drops 4×, with the same number of
shared atomics.  Estimate: per input byte the kernel issues one load and one shared atomic, so
assume loads are a fraction f = 0.5 of the issued work (an assumption: no profiler counter was
collected); making that part s = 4 times cheaper gives 1 / ((1 − f) + f / s) =
**1.60×**, which may not exceed the measured headroom to a coalesced copy,
237.5 / 56.1 GB/s = 4.23×.

## 4. Security relevance: what the throughput means for triage

The scanner is a triage tool, so what matters is how fast it can answer *where in this data
is something encrypted, compressed or packed?*  Measured on this GPU, the fused kernel scans
at **56075.4 MB/s** on a 94.4 MB input, versus **970.1 MB/s**
for the single-threaded CPU reference (57.8× faster); including the
pageable host-to-device copy (4.8 GB/s) the end-to-end rate is 4385.7 MB/s.
At these measured rates a 1 TB disk image would take approximately 17.8 s of kernel
time, 3.8 min including the host-to-device copy, and 17.2 min on one CPU
core, in each case excluding reading the image from storage.  Consequences for practice:

- **The GPU is not the bottleneck; data movement is.**  The kernel (56.1 GB/s)
  is faster than the host-to-device copy (4.8 GB/s) and than typical storage (a fast
  NVMe SSD reads a few GB/s, a network share or HDD far less), so a GPU entropy scan can run
  *inline* with acquisition or ingestion instead of as a separate pass, and the effort should
  go into overlapping transfer and compute rather than into the kernel.
- **Batch small files.**  A single 1.25 MiB file (320 windows) takes 48.97 µs, only
  26767.0 MB/s (48 % of the large-input rate), because 320
  blocks cannot fill the GPU and the fixed launch cost dominates.  Triaging a file system file
  by file would waste most of the GPU; files should be packed into large buffers and scanned
  with one launch.
- **Resolution and statistics.**  With W = 4096 (one page) the scanner localises a
  high-entropy region to 4 KiB, as the plot shows (windows 129-192
  above 6.5 bits/byte), but 4096 samples of 256 symbols bias the estimate down by
  about 0.05 bits, so random data reads ≈ 7.95 rather than 8.0 and thresholds must allow for it.
- **The same scan checks encryption.**  Correct ciphertext is indistinguishable from random
  bytes, so every window of an encrypted volume or of the output of a GPU encryption kernel
  should read ≈ 7.95 bits/byte at W = 4096; a run of low-entropy windows inside it points to
  unencrypted sectors, padding, or a broken cipher mode (e.g. ECB on repetitive data), which
  is a vulnerability the scan finds without decrypting anything.
- **Entropy is a signal, not a verdict.**  High entropy flags encrypted containers, ransomware
  output, packed or encrypted malware sections and exfiltration archives, but also every
  ordinary JPEG, ZIP or video, so it ranks data for deeper analysis rather than detecting
  malice; and an adversary can lower it deliberately (Base64 encoding caps it at 6
  bits/byte, padding with low-entropy bytes dilutes a window).  A high-entropy region still
  needs closer inspection: identifying its format (archive, media, encrypted container),
  trying to decompress it, signature or YARA scanning, or disassembly.  Fast scanning
  matters because it lets an analyst apply this cheap signal to *all* the data and reserve
  the expensive tools for the flagged regions.
