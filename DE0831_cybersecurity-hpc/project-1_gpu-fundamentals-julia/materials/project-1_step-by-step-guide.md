# Project 1: step-by-step support

DE0831 Cybersecurity Solutions in High Performance Computing Environment

*Course material, copied for reference from the course page.*

- Authors: Arnis Lektauers (Assoc. Professor, Dr.sc.ing., arnis.lektauers@rtu.lv),
  Marta Narigina (Lecturer, M.sc.ing., marta.narigina@rtu.lv)
- Affiliation: Faculty of Computer Science, Information Technology and Energy, Institute of
  Information Technology
- Published 17. 09. 2026, modified 12. 10. 2026

This guide supports the Project 1 brief issued on 14 September.

## Start here

The project develops a GPU tool that locates regions of a file with high byte entropy. You first
practise distributing work, arranging data and counting bytes. The final exercise combines those
ideas. High entropy occurs in compressed as well as encrypted data, so a high-entropy region is a
candidate for closer inspection.

| Exercise | Plain-language task | GPU idea |
|---|---|---|
| 1. SAXPY | Scale each input value and add it to an output value | Distribute a loop across threads |
| 2. Transpose | Exchange matrix rows and columns | Arrange memory access and reuse a tile |
| 3. Histogram | Count how often each byte value appears | Combine contributions without losing counts |
| 4. Entropy | Summarise the distribution in each file window | A histogram per window, then array operations (basic) or a block reduction (fused) |

Recommended first session: run Julia, trace the small SAXPY example below, and make one GPU result
agree with its CPU reference. Leave performance tuning until the result is correct.

## Optional support files

Download the support pack:

- CPU reference functions
- Known-answer examples
- GPU timing helper
- Results-table template
- Usage and attribution notes
- Starter files, one per exercise (in the pack, folder `starters/`): exercise 1, exercise 2,
  exercise 3, exercise 4 basic route and fused route, shared header

After extracting the folder, run `julia check_examples.jl` in that folder. This checks the supplied
CPU examples; it does not check your GPU implementation.

You may reuse these helpers; acknowledge them in your README. The GPU kernels, the measurements and
the analysis are your own work.

### Starter files

Each starter is a complete script with the GPU kernels left open. The header block, test data,
launch configuration, comparison with the CPU reference, the boundary sizes of the brief and the
results table are already written. The kernels contain numbered TODO steps that name the lecture
slide with the pattern.

1. Set `STUDENT_ID` and `STUDENT_NAME` once in `starters/common.jl`.
2. Run a starter unchanged. It lists every check as NOT YET.
3. Complete the TODO steps in order and run again. Each check reports separately, so the naive
   kernel of exercises 2 and 3 can pass before the second kernel is started.
4. When every check passes, the starter prints `Correct!` and then the measurement table for
   `results/benchmarks.md`.

The starters are optional, and work already written to the brief stays valid.

## A workflow for every exercise

1. Trace a tiny input. Write the expected output before launching the GPU.
2. Write or use a CPU reference. Keep an unchanged copy of the input.
3. Implement a simple GPU version. Work with bounds checks enabled.
4. Compare the entire output. A correct total can hide wrong elements.
5. Try boundary cases. Check where a final block or tile is incomplete.
6. Measure the correct version. Warm up and synchronise; state what you timed.
7. Explain one observation. Support the explanation with your own results.

The focused prerequisite bridge, Julia primer, computing foundations and lectures 4–6 reference
explain the terms used below.

## Input sizes and repeatability

Use the published ID-derived N, SEED and alpha for the required measurements. The tiny inputs in
this guide are for development only. In exercise 2, N is the matrix side length. In exercise 3, the
byte array has length N * 10000. Exercise 4 uses the generated file in the brief.

For the boundary tests in exercises 1 and 4, use the listed small lengths for the respective vector
or byte input. Keep your assigned N for the main results.

A simple reproducible approach is to generate random data on the CPU using the published seed and
copy it to the GPU. `Random.seed!` does not seed the GPU random-number generator. Keep identical
input values when comparing two implementations.

## Exercise 1: SAXPY

Meaning: for each position, compute `alpha * x[i] + y[i]` and store it in `y[i]`.

| Input | Values |
|---|---|
| alpha | 2.0f0 |
| x | [1, 2, 3] |
| Initial y | [10, 20, 30] |
| Expected final y | [12, 24, 36] |

Build it in stages:

- Trace the first result: 2 * 1 + 10 = 12.
- Map each thread to its first index, using the indexing diagram of lecture 4.
- Calculate the total number of threads in the launch, which is the stride.
- After processing an index, advance by the stride while the index is valid.
- Check with one block before comparing the five required block counts.

For a paper example with ten elements and four total threads, thread 1 handles indices 1, 5, 9;
thread 2 handles 2, 6, 10. Trace the remaining threads. The kernel must therefore work with fewer
threads than values.

Check and measure:

```julia
include("cpu_checks.jl")              # adapt the path to your folder
using .Project1Checks
x_host = Float32[1, 2, 3]
y_initial = Float32[10, 20, 30]
expected = saxpy_reference(x_host, y_initial, 2.0f0)
# Launch YOUR kernel on GPU copies, then:
# @assert Array(y_device) ≈ expected
```

SAXPY changes y. Restore the original y before each independent correctness check or timing
sample. Otherwise you are repeatedly adding to a previous result.

Report all published block counts: 1, 16, 64, 256 and 1024. For Float32, the useful traffic is 12N
bytes: read x, read y, write y. Effective GB/s is 12N / time_in_seconds / 1e9.

## Exercise 2: matrix transpose

Meaning: a value at row i, column j moves to row j, column i.

```
Input                 Expected transpose
1  2  3               1  4
4  5  6               2  5
                      3  6
```

The example is rectangular to make the exchange visible; the assessed matrices are N × N.

Build it in stages:

- Complete the naive kernel and compare the full result with the CPU transpose.
- Sketch a small tile. Mark which thread loads each element.
- Load the tile into shared memory, then place a block-wide barrier before reading values loaded
  by other threads.
- Work out the transposed output tile position as well as the position inside the tile. Draw
  coordinates before coding.
- Pad the first shared-array dimension to (TILE + 1, TILE) as specified.
- Compare both kernels for TILE 8, 16 and 32.

Julia stores the first array index contiguously. Padding changes the stride of a column-to-column
access and reduces bank conflicts. See the worked layout explanation in the lectures 4–6
reference.

Do not put a barrier inside a condition reached by only part of the block. Separate conditional
loads/stores from the barrier that all threads must reach.

Bandwidth: use 8N² / seconds / 1e9, counting one Float32 read and write per matrix element. Use the
same counting convention for both implementations.

## Exercise 3: byte-frequency histogram

Meaning: there are 256 possible byte values. Each bin counts one value.

For `UInt8[0, 0, 1, 255]`:

| Byte value | Julia bin index | Expected count |
|---|---|---|
| 0 | 1 | 2 |
| 1 | 2 | 1 |
| 255 | 256 | 1 |
| Every other value | Its value + 1 | 0 |

The sum of all bins must equal the input length, but also compare every bin with the CPU
reference: counts placed in the wrong bins can still have the right total.

Build it in stages:

- Make the global-atomic version match `histogram_reference(bytes_host)`.
- For the privatised version, sketch a block's 256 local bins.
- Initialise all local bins, then synchronise before updates begin.
- Accumulate into local bins without losing simultaneous contributions.
- Synchronise before merging local counts into the global histogram.
- Verify both versions on both required distributions before timing them.

Clear the global output before each independent run. Otherwise the counts of the previous run are
added to the new ones.

For the skewed dataset, put zero in exactly 90% of positions and nonzero random bytes in the
remainder, then shuffle using your seeded RNG. If your existing generator samples the remainder
from all byte values, report the realised zero fraction.

Speedup: naive_time / privatised_time, using identical data and timing scope. A result below 1
means the privatised version was slower; report it as measured and explain it. Many updates to the
same bin compete for access, which is called contention.

## Exercise 4: window entropy

Meaning: entropy summarises how spread out the byte frequencies are within one window. For each
nonempty bin, calculate its probability p, then add -p*log2(p). A zero-count bin contributes zero;
do not evaluate log2(0).

| Tiny input | Entropy in bits per byte |
|---|---|
| [0, 0, 0, 0] | 0 |
| [0, 1, 0, 1] | 1 |
| Each byte value 0–255 exactly once | 8 |

These are exact reference cases. A finite random sample is not guaranteed to have exactly 8 bits
per byte.

### Window conventions

The brief does not fix the step or the treatment of a short final window. The lab examples use
adjacent windows, which is step W: window 1 covers bytes 1:W, window 2 covers W+1:2W, and so on.

For a final short window containing m bytes, normalise counts by m, not by W. The published formula
count/W applies to a full window. For example, five identical bytes have entropy 0 even when
W=4096.

The supplied CPU reference includes the short final window by default. It also supports
`tail=:drop` and an explicit step so you can match an existing window convention. State your width,
step and final-window treatment and compare the GPU with a CPU reference using the same convention.
If your existing work uses a different convention, keep it and bring it to a consultation.

### Two routes

| | Basic route | Fused route |
|---|---|---|
| Marks for exercise 4 | up to 2 of 3 | up to 3 of 3 |
| GPU kernel | per-window histogram in shared memory, copied to a count matrix | the same histogram, then a block reduction of the entropy terms |
| Entropy | broadcasting and sum on the count matrix, as in lab 2 | inside the kernel |
| `sync_threads()` calls | 2 | 4, one of them inside a loop |
| Starter | `p1_ex4_basic_starter.jl` | `p1_ex4_starter.jl` |

The basic route needs lab 3, exercise 6 and nothing from the reduction part of lecture 6. The fused
route adds the block reduction. The counting code is the same in both, so a working basic route is
a starting point for the fused one and a second check of its result. Submit the route you
completed. If you submit both, the fused one is marked.

Both routes need the checks, timing, plot and half-page analysis of the brief. In the basic route,
time the whole scan (kernel and array step) for the throughput, and report the counting kernel
alone as well: the difference is the cost of writing the count matrix (1 KB per 4 KB window) and
reading it back. The analysis can use that difference for its further optimisation.

Build it in stages:

- Calculate the entropy of one tiny input on paper and with the CPU reference.
- Reuse the histogram idea from exercise 3 for one GPU window. Each block has 256 threads, so every
  thread counts W/256 = 16 bytes of its window.
- Assign one block to each window.

Basic route:

- Each thread copies its bin to column `blockIdx().x` of a 256 × windows matrix.
- Divide each column by its window length, convert every probability p to -p*log2(p) (zero for
  p = 0), and sum each column with `sum(T; dims=1)`.

Fused route:

- Convert counts to entropy contributions in shared memory, treating zero bins separately.
- Combine contributions with a block reduction. The worked reduction explains the
  synchronisation; adapt it to your own entropy kernel.

Both routes:

- Compare the complete profile with the CPU reference.
- Run the file generator from the brief and plot entropy against window index.

CPU functions and separate temporary stages can help you debug, but do not replace the GPU
implementation of the route you submit.

Compare with a floating-point tolerance: the supplied CPU reference uses Float64, and the GPU may
sum Float32 terms in another order. For the small reference examples, start with an absolute
tolerance of 1e-4 bits per byte and investigate larger differences.

The supplied file generator places its random-byte region at byte positions 524289:786432. With
adjacent full windows of width 4096, those are windows 129–192. The profile should show that
region at a higher entropy level.

Throughput: input bytes divided by seconds and by 1e6 gives decimal MB/s. State whether dropped
tail bytes or repeated reads of overlapping windows are included in your numerator.

## Measuring without changing the input between samples

The optional helper performs one warm-up and uses `CUDA.@elapsed` for repeated samples. Preparation
runs outside the timed interval. Use the same measurement scope when comparing implementations.

```julia
using CUDA
include("gpu_timing.jl")
using .Project1Timing

# x_d, y_d and y_initial_d are preallocated CuArrays.
# saxpy! is YOUR already validated implementation.
launch!() = @cuda threads=256 blocks=64 saxpy!(y_d, alpha, x_d)
restore!() = copyto!(y_d, y_initial_d)

measurement = time_gpu(launch!; prepare! = restore!, repeats=100)
seconds = measurement.mean_seconds
println("Time (ms): ", seconds * 1000)
println("Effective GB/s: ", 12 * length(x_d) / seconds / 1e9)
```

For an accumulating histogram, a preparation function can use `fill!(counts_d, 0)`. For an output
fully overwritten by a kernel, preparation may be unnecessary. If output clearing is part of the
algorithm whose runtime you report, include it in the timed operation for both implementations and
label the scope accordingly.

Validate separately using the same starting state, including after a measured run. Do not put
printing, plotting or CPU result comparisons inside the timed operation. Kernel timings exclude
file reading, host/device transfers and plotting unless you explicitly include those operations.
Small kernels are sensitive to launch/event overhead; inspect the variation between samples.

Source: CUDA.jl benchmarking and profiling.

## Writing the half-page analysis

Use your own results to answer the published analysis requirements. You can organise half a page
around these prompts:

- **Roofline:** "Using this operation-count convention and this estimate of bytes moved, I obtain
  an intensity of … . My device's ridge point is … ." Count logarithms separately: a logarithm
  costs more than an addition. State whether you count useful global bytes or measured traffic.
  The roofline model does not account for atomic contention or special-function throughput.
- **Likely limiter:** "I observed … . This supports … because … ." A register count alone does not
  identify a bottleneck. Separate what you observed from what you infer, and say so when a
  profiler counter is unavailable.
- **Further optimisation:** "I would change … . If the affected part takes fraction f of runtime
  and becomes s times faster, the estimated overall speedup is 1 / ((1-f) + f/s)." State where
  your estimates came from.
- **Security relevance:** "At my measured input rate, processing this volume would take
  approximately …, excluding … . A high-entropy region still needs … ."

## Troubleshooting and consultations

| Observation | First check |
|---|---|
| No GPU is available | Use the lab setup guide; bring the exact error. You can work on CPU checks meanwhile. |
| SAXPY agrees once, then differs | Restore initial y; check the grid-stride loop. |
| Transpose correct near the origin only | Trace block coordinates as well as tile-local coordinates. |
| Histogram totals grow every run | Clear the global bins before a fresh run. |
| Histogram sum is correct but bins differ | Check the bin index Int(byte) + 1 as well as the sum. |
| Entropy contains NaN | Skip zero-count logarithms; check the nonempty window length. |
| Short-window entropy differs | Match the tail convention and use actual bytes in the probability denominator. |
| Kernel waits indefinitely | Check that every thread reaches each block barrier. |
| First timing is much longer | Warm up compilation and synchronise before measuring. |

Bring the smallest input that reproduces the problem, its expected output, the actual output or
error, and one change you already tried. Unfinished code is welcome at a consultation.

Suggested use of the project sessions:

- Week 4: trace indexing, get SAXPY working, establish a correct naive transpose.
- Week 5: compare coalesced and uncoalesced access in the transpose.
- Week 6: shared-memory tiling, histogram accumulation and reduction.
- Weeks 7–8: finish the entropy scanner, validate, measure and discuss the analysis.

Tell the lecturer early if environment problems or prerequisite gaps prevent these steps.

## Before submission and defence

Follow the issued brief's folder structure and rubric. Use this optional final check:

- All four exercises run, validate their outputs and print `Correct!` after checks pass.
- Student name, ID-derived parameters and device information are printed.
- Required configurations and both histogram distributions are measured.
- The entropy plot locates the known high-entropy region.
- The half-page analysis, per-kernel explanations and environment files are included.
- The README acknowledges supplied helpers and declares any AI-assistant use.

Practise explaining one index calculation, one barrier, one correctness test and one measured
result from your own code. For example: identify what changes when one block must process more
elements than it has threads.
