# Research project defence: numbers to remember and likely questions

Presentation 14.12.2026, 10 minutes + 5 minutes of questions, live demonstration on Colab.  The
project is graded only at the defence, as a whole (10 points: implementation 3, measurement and
analysis 3, security conclusion 1, report and reproducibility 1, presentation and answers 2).
Speaker notes with timings: `outputs/presentation/speaker-notes.md`.

## Before the day

- Open Colab 20 minutes early: `tools/DE0831_RP_demo.ipynb`, Python 3 + T4, run steps 1–4 and the
  warm-up cell (installs Julia, instantiates, generates the 125k corpus, compiles the kernels).
- Keep the full results open in a second tab (`DE0831_RP/results/benchmarks.md` and the four
  plots) in case the GPU is not available: the logs of the full run are in
  `outputs/colab-t4_2026-11-04/`.
- Start the live-run cell when slide 5 is up; it takes about a minute; show the output at slide 10.

## Numbers to remember (Tesla T4, 1,000,000 lines, 119.2 MB)

| what | value |
|---|---|
| GPU hash-set pipeline | 32.9–33.3 ms, 30 M lines/s, flat from 10 to 10,000 indicators |
| its hash-match kernel alone | 1.9–2.7 ms, 1.4–2.4 probes per token |
| steps at 1,000 indicators | line table 13.3 ms (40 %), token scan 15.7 ms (47 %), hash 2.7 ms (8 %), extraction 2.3 ms (7 %) |
| no-compaction variant | 19.8–24.8 ms, 40–50 M lines/s; kernel 7.3–8.2 ms |
| per-indicator kernel | 5.9 ms per group of 32: 5.6 / 7.7 / 23.7 / 58.6 / 186.6 / 561.4 ms at 10 / 30 / 100 / 300 / 1,000 / 3,000; 1.86 s predicted at 10,000 |
| crossover hash set vs per-indicator | between 30 and 100 indicators (with the line table counted) |
| shared-memory keys | 2.2–3.1 ms vs 1.9–2.7 ms global: no gain, probes come from L1/L2 |
| table | 16 B per slot, load ≤ 0.5: 0.5 KB at 10, 512 KB at 10,000 (12 % of the 4 MB L2) |
| copies | device-to-device 241 GB/s; host-to-device 4.6 GB/s pageable, 11.3 GB/s pinned |
| size sweep (1,000 indicators) | GPU 3.3–3.6 GB/s; no compaction 5.2–5.8; with the copy 1.9–2.0 GB/s |
| CPU, 4-core Xeon 2.1 GHz | 1 task 0.31–0.41 s (290 MB/s), 2 tasks 0.17–0.21 s, 4 tasks 0.086–0.113 s (1.05–1.38 GB/s); 1.92× / 3.63× |
| CPU, Colab host (1 core, 2 threads) | 1 task 0.40–0.65 s, 2 tasks 0.32–0.63 s |
| occursin (4-core host) | 0.80 / 2.5 / 8.0 / 24.8 s at 10 / 30 / 100 / 300; about 14 min at 10,000 |
| speed-ups at 4M lines | with the copy 1.75× the 4-core CPU, 6.7× one core; on the device 3.0× and 11.6×; no compaction 5.3× |
| daily volumes | 1 core 25 TB, 4 cores 94 TB, GPU with the copy 165 TB, GPU on the device 500 TB |
| validation | 894 (line, indicator) pairs for every list and every method; 11 hand-made cases; `Correct!` |
| device | Tesla T4, 40 SMs, 14.56 GiB, CC 7.5, driver 580.82 / CUDA 13.3, CUDA.jl 6.5.1, Julia 1.12.7 |

## Likely questions and answers

### The objective and the data

**Why does the hit count stay at 894 for every list?**  Because the added indicators are cold by
construction (RFC 2544 addresses and random `.invalid` names that cannot occur in the corpus).
That is what a real feed looks like, and it keeps the comparison about the cost of the list, not
of the hits.  The cost of hits is a separate question; at 0.09 % of lines it is negligible here
(extraction 2 ms).

**Why whole tokens and not substrings?**  Indicators in logs are addresses and hostnames, which
appear as tokens; substring matching would report `192.0.2.24` inside `192.0.2.248`.  The rule is
the same in every method, so the comparison is fair; substring semantics would need an automaton
(Aho–Corasick), which is the natural next experiment.

**Is the corpus realistic?**  It is the course generator's corpus: synthetic, two event formats,
documentation address ranges.  Real logs have more formats and longer lines, which changes the
constant (tokens per byte) but not the structure of the result.

### The GPU design

**Why a hash set?**  Because its cost is one hash per token whatever the list: that is the
property the question is about.  The per-indicator kernel of Project 2 is the counter-example,
measured: 5.9 ms per 32 indicators.

**Why FNV-1a?**  A one-multiply-per-byte hash that is computed as the bytes are read, with no
extra pass; the same function on the CPU and in the kernel.  Any good byte hash would do; the
probes per token (1.4–2.4 at load ≤ 0.5) show it spreads the keys well enough.

**Why linear probing and a load of 0.5?**  Linear probing keeps the probe sequence in one cache
line; at load ≤ 0.5 an unsuccessful search needs about 2.5 probes on average, measured 1.4–2.4.

**Why is the pipeline flat if the table grows 1,000×?**  The table of 10,000 indicators is 512 KB,
12 % of the L2; the probes hit L1 or L2 at every size.  The hash kernel went from 2.1 to 2.6 ms.

**Why did the shared-memory table not help?**  Same reason: the probes were already served from
L1/L2, so copying the keys into shared memory only adds the copy.  The kernel is bound by the
serial byte walk and the data-dependent probe of each thread, not by the table's latency.

**What limits the pipeline, then?**  The two scans: 4-byte flags per corpus byte, scanned and
scattered, 8 bytes moved per byte of log; 87 % of the pipeline at 1,000 indicators.  The proof is
the variant without the token scan: 33 → 20 ms.

**Why keep the line table at all?**  Only to name the lines of the hits; it is 13 ms.  Dropping it
would need a different way to number lines (e.g. a per-block newline count fused into the match
kernel), which is the next optimisation, not done here.

**Why not Aho–Corasick / PFAC on the GPU?**  It gives substring semantics and is the classical
GPU multi-pattern method, but its transition table grows with the total pattern length (about
170,000 states × 256 for 10,000 indicators), so it would measure the table-size effect instead of
the list-size effect; the token hash set isolates the question.  It is the obvious follow-up.

**Why one thread per byte in the no-compaction variant, when four lanes in five idle?**  Because
the alternative, the compaction, costs 16 ms of scan traffic; the divergence costs less (8 ms
kernel).  Measured, not assumed.

**Atomics and races?**  The hash-set pipeline has none in the match kernel (PTX: 0 atomics); the
no-compaction variant has one atomic add per hit (894 per million lines); the per-indicator
kernel one atomic OR per hit.  Threads never write the same token slot.

### Measurement

**How do you time?**  Lecture 7: warm-up launch, `CUDA.synchronize()`, one `CUDA.@elapsed` per
launch (CUDA events, GPU time), 100 launches, mean and min–max.  Every step is timed on its own,
the pipeline is one timing of its own, the copy is another; nothing is a difference.

**Did garbage collection or allocation distort the numbers?**  Every launch's outputs are freed at
once, and the device pool is reclaimed between sizes, so no GC lands inside a timed interval.
The min–max spread of the pipeline is a few percent.

**Why is the 2-task CPU sometimes slower than 1 task on Colab?**  The Colab host has one physical
core with two hardware threads; the second thread shares the core's execution units, so the gain
is 1.7× at best and sometimes nothing.  That is why the task scaling is shown on the 4-core host
(1.92×, 3.63×) and the sizing uses those numbers.

**Is the CPU baseline fair?**  It is the same algorithm, tuned: one pass, no allocation per token,
a hand-written table, tasks over newline-aligned chunks.  It is Julia, not vectorised C++, which
would be faster per core and narrow the GPU's margin: said in the limitations.

**Why do rates fall slightly at 4M lines?**  The pipeline rate falls from 3.6 to 3.3 GB/s and the
match kernel of Project 2 showed the same trend; the T4 is a 70 W card that reduces its clock under
sustained load.  Reported as measured, not claimed as a cause.

### The conclusion

**So is the GPU worth it?**  For indicator matching alone, only at high rates: four cores of this
class cover 1 GB/s, a T4 with the copy 2 GB/s.  Most SOCs produce far less (2 TB/day is 23 MB/s).
The GPU pays when the logs are on the device for other analytics, or when one machine must handle
several GB/s.  The result that matters more is the algorithm: list-independent methods make the
feed size free.

**What would you do next?**  Remove the line-table scan (fuse line counting into the match
kernel), test an automaton for substring semantics, measure hit-heavy lists, and compare against
a C++ CPU matcher.

**Ethical and legal?**  Only self-generated data (RFC 5737, RFC 2544, RFC 2606 names); nothing
probed or collected.  In production, logs and matches identify people: retention, purpose
limitation, access control; threat feeds carry sharing restrictions (TLP).

### About the work

**Did you write this yourself?**  Answer from the README's "Declared AI use" paragraph, honestly:
what the assistant drafted, what you reviewed, changed and ran (the Colab runs, the CPU runs,
the checks of the results).  Be ready to explain any function the examiner points at:
`hash_match!`, `hash_match_direct!`, `scan_chunk!`, `IndicatorTable` and the validation in
`rp_run.jl` are the ones to know line by line.

**Relation to Project 2?**  Project 2 built the per-indicator kernel and the lecture-7 compaction;
the research project asks what happens when the list grows, where that kernel is the linear
baseline and the hash set is the answer.  The two share the corpus generator and the timing
harness.
