# Project 2 defence: speaker notes and likely questions

Defence in week 14 (after the upload by 27.11.2026).  Numbers below are from the Colab T4 run
(`DE0831_P2/results/`); the exact figures of the final run may differ by a few percent, so read
them from `results/benchmarks.md` before the defence.

## 1. What the grader sees first

- `README.md`: track E, full route, device block (Tesla T4, 40 SMs, 320 GB/s, CUDA.jl 6.5.1),
  how to run, the files, the technique, the methodology, known issues, the declared AI use.
- `results/benchmarks.md`: the tables; `results/analysis.md`: headline, limiter, scaling, CPU
  comparison, defensive conclusion; four plots; the PTX of both match kernels.
- `src/p2_run.jl` prints `Correct!` after validating everything against the generator's truth.

## 2. Opening statement (about 3 minutes, speak slowly)

"My project is track E, the full route: indicator matching in logs on the GPU.  The data is the
course generator run with my student ID: one million lines, 119 MB, 20 indicators (12 addresses,
8 domains), 894 lines carry an indicator and 243 tokens are encoded payloads.

The GPU design is one flat byte vector; thread i owns byte i, so every warp reads 32
consecutive bytes, coalesced.  Line starts, matched lines, token starts and flagged tokens are
all found with the same pattern from lecture 7: a flag per byte, an inclusive scan, and a
scatter kernel that packs the flagged positions, that is stream compaction.

The matching kernel is one kernel for all 20 patterns at once.  A block loads a tile of the
corpus plus a halo into shared memory, together with the pattern table; each thread tests its
positions with a prefix filter and compares candidates byte by byte from shared memory; a whole-
word hit sets the pattern's bit in the line's mask with one atomic OR.  Hits are rare, 0.09 %
of lines, so the atomic costs nothing measurable.

Correctness: the GPU line table equals the CPU's; the match set of every kernel variant equals
the generator's truth file exactly; the extracted lines equal the corpus lines; entropies
agree with the CPU to 3 × 10⁻⁶ and with the truth file to 5 × 10⁻⁵; eighteen hand-made
boundary cases cover tile edges, corpus ends and word boundaries.

The entropy threshold is not the hint of 5.0: I histogram all 22 million token entropies on
the GPU and take the midpoint of the widest empty band above the median, 4.12 bits.  At 5.0 I
would miss 49 of the 243 payloads; at 4.12 precision and recall are both 1.

Measurement: one warm-up, then one `CUDA.@elapsed` per launch over 100 launches; every step is
timed on its own; nothing is a difference of timings.  The headline: 18 million lines per
second on the device, 12 million including the host-to-device copy, about 110× one CPU core
with the same algorithm.

The most interesting result is the limiter.  My first match kernel ran at 9 GB/s, 4 % of the
device-to-device copy rate, although it reads each byte once.  Its integer model predicts half
a millisecond, it took thirteen.  The reason is warp-level: the first-byte filter lets 20 % of
the positions through, so every warp of 32 lanes has a candidate and runs the candidate loop at
the pace of its slowest lane.  I tested that diagnosis with a second kernel: a three-byte prefix
filter in shared memory, 0.95 % candidates, 71 % of the warps skip the loop, plus a 4 KB tile
to amortise the table copy.  It is 1.97× faster, 6.6 ms.  So the limiter was control flow at
warp level, not bandwidth and not arithmetic.

The defensive conclusion: one CPU core keeps up with about 1.7 TB of logs per day; one T4
including the copy with about 127 TB per day.  For a 2 TB/day site two cores are enough; the
GPU pays off when the indicator list grows, which is my research project."

## 3. Numbers to remember (1,000,000 lines, 119.2 MB, Tesla T4)

| what | value |
|---|---|
| match kernel v2 (`match_tiled_tri!`) | 6.6 ms, 18.0 GB/s, 151 M lines/s |
| match kernel v1 (`match_tiled!`) | 13.1 ms, 9.1 GB/s |
| global-memory variant | 15.5 ms |
| line table (flags, scan, scatter) | 13.0 ms |
| token starts | 15.8 ms (largest step, 32 %) |
| token entropies (22.35 M tokens) | 11.4 ms |
| GPU pipeline end to end | 49.7 ms = 2.4 GB/s; with pageable copy 76 ms |
| host→device copy | 26.7 ms pageable (4.5 GB/s), 10.4 ms pinned (11.4 GB/s) |
| device→device copy reference | 231 GB/s (read + write); theoretical DRAM 320 GB/s |
| CPU pipeline, one core | 5.66 s = 21 MB/s; CPU match 0.87 s; `occursin` 2.6 s |
| speed-up (4M lines) | 109× on the device, 74× with the copy |
| filters | first byte: 20.3 % candidates, 0 % of warps skip; three bytes: 0.95 %, 71.5 % skip |
| candidate loop | up to 7 patterns behind the busiest first byte |
| resources v2 | 26 registers, 10.7 KB shared per block, occupancy 100 %, 4 blocks/SM |
| threshold | 4.12 bits (band 3.80–4.45); ordinary tokens end at 3.78, payloads start at 4.49 |
| precision/recall at 4.12 | 1.000 / 1.000; at 5.0 recall 0.80 |
| daily volume | 1.7 TB/day per CPU core, 127 TB/day per GPU incl. copy |

## 4. Likely questions and answers

### Design and GPU technique

**Why one kernel for all patterns instead of one launch per pattern?**
Each launch would re-read the whole corpus: 20 launches = 20 × 119 MB of traffic.  One kernel
reads each byte once and tests all patterns from a shared-memory table; the first-byte mask (a
256-entry bitmask) says which patterns can start at a byte, so most bytes test nothing.

**Why shared memory for the tile?  The global variant exists, how much does the tile give?**
A candidate position compares up to 32 bytes; from global memory those are L1/L2 re-reads,
from shared memory they are broadcast reads.  Measured: 15.5 ms global vs 13.1 ms tiled (1.19×).
The tile matters less than the warp-level loop, which is why v2 attacks the loop.

**How do you handle a pattern that crosses a tile edge?**
Each block loads its tile plus a 32-byte halo (MAXPLEN); a pattern that starts in this tile
is compared entirely from the tile, even if it ends in the next one.  The next tile does not
report it again because a match is attributed to the tile where it starts.  Test cases
"crosses the tile edge", "starts at the edge", "ends at the edge" for both tile sizes (1 KB
and 4 KB) check this.

**What about the corpus end and the last line without a newline?**
Bounds checks on `g + L - 1 <= n`; the halo is zero-filled past the end; a last line without
a newline gets a line start and the sentinel `n + 2`; test cases "last byte of the corpus" and
"one line, no newline".

**Why word boundaries?**
`192.0.2.24` must not match inside `192.0.2.248` and `app3.invalid` not inside
`xapp3.invalid`; the byte before and after the match must not be a word character
(alphanumeric, `.`, `-`).  Both kernels and the CPU baseline apply the same rule, and the
`occursin` baseline (substring semantics) is kept separately for the comparison table.

**Where are the atomics and are there races?**
The only shared write in the match kernels is the atomic OR into the line mask (one PTX
`atom.global.or.b32`).  The entropy kernel has no atomics: one thread per token with a private
64-bin histogram in shared memory laid out so a warp touches consecutive bytes.  The histogram
kernel uses a block-private histogram with shared atomics and one global add per bin per block.

**Why `UInt32` flags for the scan and not `UInt8`?**
The inclusive scan result must hold counts up to 119 million, so the scan output is 32-bit;
`accumulate` keeps the element type, so the flags are `UInt32` as well.  That makes the scan
steps the largest part of the pipeline (they move 8 bytes per corpus byte); halving the flag
traffic (8-bit flags scanned into 32-bit) is the first next step I would take.

**Why is the binary search for the line acceptable inside the kernel?**
It runs only on a hit, 894 times per million lines, at most 20 steps each.

### Correctness and validation

**How do you know the result is right?**
Three independent references: the CPU baseline with the same algorithm, the `occursin`
library baseline, and the generator's truth files; all match sets are identical (894 lines),
all three kernel variants agree, the extracted text equals the corpus lines, and the test
suite runs the same validation (`test/runtests.jl`, prints `Correct!`).

**Did you test on a GPU or only on Colab?**
On a Tesla T4 in Colab; the device block in the README and the logs record the device, driver
and CUDA.jl version.  Before that the code was checked with a CPU emulator of the kernel API,
by compiling every kernel to PTX, and with mutation tests of the validation (the tools are in
the repository, not in the archive).

### Measurement

**Why `CUDA.@elapsed` and not `@elapsed`?**
Kernel launches are asynchronous: `@elapsed` would time the launch call, not the kernel.
`CUDA.@elapsed` records CUDA events on the stream and measures GPU time between them.  A warm-
up launch first, so compilation is excluded, then 100 timed launches; mean and min–max reported.

**Is any number derived by subtraction?**  No.  Every step is timed directly, the pipeline is
one timing of its own, and the copy is a separate timing; "pipeline + H2D" is a sum, stated as
such.  (This was a remark on Project 1 and it is fixed here.)

**Why does the match rate fall slightly with corpus size (20 → 16 GB/s)?**
The measured trend is in the table; the kernel is the same per byte, so the likely causes are
clock behaviour of the T4 under sustained load and L2 effects; I report the trend and do not
claim a cause I did not measure.

**What is the CPU baseline and is it fair?**
Single-threaded Julia, same algorithm (first-byte filter, byte compare, word boundary), best of
three runs after a warm-up; the `occursin` baseline is the library route.  It is a one-core
number: a tuned multithreaded matcher scales with cores, which is exactly the research project's
question.

### The analysis and the limiter

**What limits the match kernel?**
Not bandwidth (v1 at 4 %, v2 at 8 % of the copy rate) and not the lane-counted integer work
(the model gives 0.5 ms, measured 13 ms).  The limiter is warp-level control flow: a warp runs
the candidate loop whenever one lane has a candidate, for as long as its slowest lane needs.
With 20 % candidates per byte no warp is free of candidates (measured 0.00 %; independent bytes
would give 0.8³² = 0.07 %).  The three-byte filter makes 71 % of the warps skip the loop and the
kernel is 1.97× faster: the prediction and the measurement agree.

**Why is v2 still at 8 % of bandwidth?**
Every position still pays the filter: three shared loads, the hash, the bitmap test; 29 % of the
warps still enter the loop; the per-block table copy is 6.5 KB per 4 KB tile.  Next steps would
be a longer tile or persistent blocks (tables loaded once), and a filter that tests several
positions per lane with one load.

**Why no Nsight Compute?**
Not available in Colab.  The limiter is inferred from measurements the script produces: achieved
bandwidth against the copy rate, candidate and compare counts, warp-skip fractions, registers,
shared memory, occupancy, and the PTX instruction classes, plus the measured effect of the change.

**What is the roofline here?**
An integer roofline: INT32 throughput 4.07 × 10¹² ops/s against 320 GB/s gives a balance point of
12.7 ops/byte.  By lane count v1 (17.1) is to the right, v2 (11.1) to the left; but the roofline
built from lane counts is an upper bound, because lanes of a warp do not work independently.

### Security conclusion

**What does a SOC do with these numbers?**
Size the job: one core handles about 1.7 TB/day, so a 2 TB/day site needs two cores or one GPU.
The GPU pays off when the indicator list grows (hundreds to thousands) or when the logs are
already on the device; it does not pay off when the logs come from a disk slower than the
pipeline, so streaming or keeping logs on the device is the architecture question.

**Why not the threshold the brief suggested (5.0)?**
Because the data says otherwise: the payloads of this corpus start at 4.49 bits (the generator's
hint "5.5–6.0" is for its own blobs on average), and 5.0 misses 49 of 243.  The threshold is
chosen from the measured distribution (the widest empty band above the median) and then
checked against the truth file; the table shows precision and recall at 3.5, 4.0, 4.12, 4.5,
5.0, 5.5.

**Limits of the study?**
Synthetic logs; 20 fixed-string indicators (no regular expressions); a single GPU session; no
real logs (course policy); CPU baseline single-threaded.

### About the work itself

**Did you write this yourself?**
Answer from the README's "Declared AI use" section, honestly: say what you reviewed, changed
and ran yourself (the Colab runs, the data generation with your ID, the checks of the results),
and what the assistant drafted.  Be ready to explain any function the examiner points at: the
kernels in `p2_gpu.jl` are the ones to know line by line (`match_tiled_tri!`, `token_entropy!`,
`scatter_positions!`).

**Can you show it running?**
`P2_QUICK=1 P2_MAIN=125000 julia --project=. src/p2_run.jl` validates a 125k-line corpus in
about a minute on a GPU and prints `Correct!`; `P2_SIZES=125000 P2_REPS=20` runs a short
benchmark.

## 5. If something goes wrong in the demo

- No GPU in the room: show `results/` and the logs from Colab (`run_logs.zip`), they carry the
  device name, driver and the full console output of the run.
- A question you cannot answer: say which measurement would answer it and how you would run it
  (the script's options make most variations a one-line change).
