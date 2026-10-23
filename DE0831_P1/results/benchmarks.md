# DE0831 Project 1: benchmark results

Each exercise script replaces its own section below when it runs its benchmarks
(`julia --project=. src/p1_exK.jl`).  Device details are in `README.md`.

<!-- BEGIN ex1 -->
## Exercise 1: SAXPY with a grid-stride loop

Student: Vagif Asgarli (251ADM047), N = 1152, seed = 51047.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then `CUDA.@elapsed` (CUDA events, GPU
time) over 100 launches; the tables report the mean time per launch.  Kernel times exclude
host/device transfers, file I/O, plotting and CPU checks unless a row says otherwise.

α = 7.0, 256 threads per block.  y is restored from an unchanged copy before every timed
launch (outside the timed interval), so each of the 100 samples is one `CUDA.@elapsed`
around one launch; the result after the last sample is checked against the CPU.  Bytes per
launch = 12 · n (read x, read y, write y, Float32); effective bandwidth = 12n / mean time / 10⁹.

**Required size, n = N = 1152** (13.8 kB per launch)

| blocks | threads in grid | elements per thread | mean time (µs) | min – max (µs) | bandwidth (GB/s) |
|---:|---:|---:|---:|---:|---:|
| 1 | 256 | 5 | 10.76 | 8.74 – 20.03 | 1.3 |
| 16 | 4096 | 1 | 12.25 | 10.21 – 33.06 | 1.1 |
| 64 | 16384 | 1 | 12.50 | 8.16 – 26.43 | 1.1 |
| 256 | 65536 | 1 | 12.17 | 8.16 – 24.58 | 1.1 |
| 1024 | 262144 | 1 | 14.28 | 10.14 – 26.66 | 1.0 |

**Additional size, n = 4096 · N = 4718592** (56.6 MB per launch),
large enough that the time is set by memory traffic rather than launch overhead

| blocks | threads in grid | elements per thread | mean time (µs) | min – max (µs) | bandwidth (GB/s) |
|---:|---:|---:|---:|---:|---:|
| 1 | 256 | 18432 | 7497.13 | 6454.02 – 11196.45 | 7.6 |
| 16 | 4096 | 1152 | 561.09 | 551.01 – 587.23 | 100.9 |
| 64 | 16384 | 288 | 275.32 | 270.34 – 297.06 | 205.7 |
| 256 | 65536 | 72 | 252.39 | 248.06 – 278.27 | 224.4 |
| 1024 | 262144 | 18 | 240.54 | 236.26 – 262.14 | 235.4 |

Reference points: device-to-device `copyto!` reaches 233.3 GB/s
(read + write); theoretical DRAM bandwidth is 320.1 GB/s.
<!-- END ex1 -->

<!-- BEGIN ex2 -->
## Exercise 2: matrix transpose

Student: Vagif Asgarli (251ADM047), N = 1152, seed = 51047.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then `CUDA.@elapsed` (CUDA events, GPU
time) over 100 launches; the tables report the mean time per launch.  Kernel times exclude
host/device transfers, file I/O, plotting and CPU checks unless a row says otherwise.

Matrix: 1152 × 1152 Float32 (5.3 MB).  Thread block = TILE × TILE for every kernel.
Bytes per launch = 2 · N² · 4 B (each element read once and written once);
bandwidth = bytes / time / 10⁹.  "Tiled, no padding" and "copy reference" are
extra kernels for comparison: the copy is a transpose-free 2D copy with both accesses coalesced.

| TILE | threads per block | naive (µs) | naive (GB/s) | tiled (µs) | tiled (GB/s) | tiled, no padding (GB/s) | copy reference (GB/s) | speedup tiled / naive |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 64 | 80.12 | 132.5 | 66.54 | 159.6 | 164.4 | 186.7 | 1.20 |
| 16 | 256 | 104.26 | 101.8 | 65.13 | 163.0 | 133.2 | 193.3 | 1.60 |
| 32 | 1024 | 256.72 | 41.4 | 81.08 | 130.9 | 63.6 | 154.8 | 3.17 |

**Why padding reduces bank conflicts.** Shared memory is split into 32 banks of 4-byte
words and threads of a warp that hit different words of the same bank are serialised; in
the store phase a warp reads one row of the column-major tile, whose elements in an
unpadded 32 × 32 tile are 32 words apart and so all sit in the same bank (a 32-way conflict).
Padding the leading dimension to TILE + 1 = 33 words puts consecutive row elements 33 words
apart, so they fall into 32 different banks and the warp is served in one shared-memory
access instead of 32.
<!-- END ex2 -->

<!-- BEGIN ex3 -->
## Exercise 3: privatised histogram

Student: Vagif Asgarli (251ADM047), N = 1152, seed = 51047.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then `CUDA.@elapsed` (CUDA events, GPU
time) over 100 launches; the tables report the mean time per launch.  Kernel times exclude
host/device transfers, file I/O, plotting and CPU checks unless a row says otherwise.

Input: N · 10000 = 11520000 bytes (UInt8), 256 bins (UInt32).  Uniform: random bytes; skewed:
exactly 90 % of the positions hold 0x00 and the rest random non-zero bytes, shuffled with the
seeded RNG.  Both kernels see identical data.  Grid = 640 blocks × 256
threads (16 blocks per SM) for both kernels.  The histogram is zeroed before every launch
outside the timed region (reset-aware timing, one `CUDA.@elapsed` per launch).  Bandwidth =
input bytes / time / 10⁹; speedup = naive time / privatised time.

| dataset | fraction 0x00 | naive (ms) | naive (GB/s) | privatised (ms) | privatised (GB/s) | speedup privatised / naive |
|---:|---:|---:|---:|---:|---:|---:|
| uniform | 0.004 | 2.963 | 3.9 | 0.227 | 50.8 | 13.06 |
| skewed (90 % 0x00) | 0.900 | 8.893 | 1.3 | 0.442 | 26.0 | 20.10 |

**Speedup of privatised over naive: 13.06× on uniform data, 20.10× on skewed data.**

**Why the speedup depends on the data.** Atomic updates of the *same* address cannot proceed in
parallel: the hardware serialises them.  With uniform bytes the naive kernel's global atomics
are spread over 256 different addresses, so the L2 atomic units process many of them
concurrently and the naive kernel is already reasonably fast.  With 90 % of the bytes equal to
0x00, nine out of ten global atomics from every thread on the GPU target the single counter
`hist[1]`, so they queue up behind each other in L2 and the naive kernel slows down sharply.
The privatised kernel moves that contention into shared memory, where each block has its own
copy of `hist[1]`: only the threads of one block compete, shared-memory atomics have far lower
latency than L2 atomics, and the SMs work on their copies in parallel.  The skewed data still costs the privatised kernel some time (its shared `hist[1]` is contended too), but much less than it costs the naive kernel, which is why the speedup is larger on the skewed dataset (20.10× against 13.06×).
<!-- END ex3 -->

<!-- BEGIN ex4 -->
## Exercise 4: entropy scanner

Student: Vagif Asgarli (251ADM047), N = 1152, seed = 51047.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then `CUDA.@elapsed` (CUDA events, GPU
time) over 100 launches; the tables report the mean time per launch.  Kernel times exclude
host/device transfers, file I/O, plotting and CPU checks unless a row says otherwise.

Window convention: width W = 4096 bytes, step W (adjacent, non-overlapping windows), a short
final window is kept and normalised by its actual length m; the CPU reference uses the same
convention.  One block of 256 threads per window, each thread counts 16 bytes.  Throughput =
input bytes / time / 10⁶ (MB/s); every input byte is counted once (no dropped tail, no
overlapping reads).  "Basic: kernel + array ops" is the whole basic route (count kernel, then
`p = c / m`, `-p log2 p` and `sum(...; dims=1)` as GPU array operations) and gives the basic
throughput; the counting kernel alone is listed too, the difference being the cost of writing
and re-reading the count matrix (1 KB per 4 KB window).  The fused route is a single kernel.
Inputs are already on the GPU; the host-to-device copy is listed separately.

| input | bytes | windows | basic: histogram kernel (µs) | basic: kernel + array ops (µs) | basic (MB/s) | fused kernel (µs) | fused (MB/s) | fused DRAM bandwidth (GB/s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| testfile.bin | 1310720 | 320 | 43.21 | 82.98 | 15795.6 | 48.97 | 26767.0 | 26.8 |
| test file × 72 | 94371840 | 23040 | 2695.37 | 2751.14 | 34302.8 | 1682.95 | 56075.4 | 56.1 |

**Content dependence** (fused kernel, 94371840 bytes, same size, different contents):

| input content | time (ms) | throughput (MB/s) |
|---:|---:|---:|
| all 0x00 | 3.664 | 25756.3 |
| letters a-z | 1.637 | 57656.2 |
| uniform random | 1.658 | 56935.0 |
| test-file mix | 1.683 | 56075.4 |

Other measurements on the 94371840-byte input: host-to-device `copyto!` (pageable memory)
19.835 ms = 4.8 GB/s; single-threaded CPU reference
0.097 s = 970.1 MB/s (`@elapsed`, CPU code, best of 3).
Device-to-device copy bandwidth: 237.5 GB/s.
<!-- END ex4 -->
