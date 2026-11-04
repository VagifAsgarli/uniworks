# Topic 10: performance analysis

Student: Vagif Asgarli (251ADM047), research project, topic 10 (log indicator matching); generator seed 5175890676511383715.
Device: Tesla T4 (compute capability 7.5.0).
Timing: one warm-up launch + `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch
(CUDA events, GPU time) over 100 launches; tables give the mean, and min–max where the
variation matters.  Every step is timed directly; no figure is a difference of two timings.
CPU times are wall-clock `@elapsed` of CPU code, best of 3 after a warm-up.

All numbers are measured by `src/rp_run.jl` on this device and inserted when it runs; the tables are in
`benchmarks.md`, the raw timings in `list_sweep.csv` and `size_sweep.csv`.

## 1. The objective and the headline number

Log lines per second as the indicator list grows from 10 to 10,000 entries, GPU against a tuned
multithreaded CPU, and the data rate at which the GPU is needed and still keeps up.  On 1,000,000 lines
(119.2 MB) the GPU hash-set pipeline runs at **30.04–30.41 million lines/s over the whole range of list
sizes** (30.20 M lines/s at 10,000); the tuned CPU matcher with 2 tasks runs at
1.87 M lines/s at 10,000 (2.34 with one task), so the GPU is **16.1×** the
2-task CPU on the device and **9.1×** once the host-to-device copy is added.
The per-indicator GPU kernel, one launch per 32 indicators, costs 5.940 ms per group on this corpus: measured
5.588 ms at 10, 7.657 ms at 30, 23.661 ms at 100, 58.598 ms at 300, 186.605 ms at 1,000, 561.365 ms at 3,000, i.e. **1.86 s predicted at 10,000**, 56× the hash-set pipeline.
The same hash-set match without the token compaction (one thread per byte, hits appended with an atomic
counter) takes 20.224 ms instead of 33.109 ms at 10,000 (kernel alone 7.650 ms against
token scan + hash match 18.328 ms): the compaction costs more than it saves here, because only about one byte in five starts a token and the scan moves 8 bytes per corpus byte.

## 2. Scaling with the list size

The hash-set pipeline is flat in the list size by construction (one pass over the corpus, one hash per
token, probes independent of N while the load stays ≤ 0.5): measured 1.01× between its slowest and
fastest list size, with 1.41–2.37 probes per token.  The list enters only through the table
footprint (0.5 KB at 10 to 512.0 KB at 10,000, against 4096 KB of L2); the hash kernel alone
went from 2.098 ms to 2.583 ms.  With the keys in shared memory the match kernel takes 2.216 ms at 10, 2.580 ms at 30, 2.630 ms at 100, 2.465 ms at 300, 3.106 ms at 1,000 against 2.098 ms, 2.534 ms, 2.565 ms, 1.890 ms, 2.664 ms from global memory: the placement of the table does not matter at these sizes; the probes are served from L1/L2 anyway.
The per-indicator kernel grows linearly with the number of groups, as its cost model says: the hash-set pipeline overtakes the per-indicator kernel (plus the line table it needs) between 30 and 100 indicators.
The tuned CPU matcher is also flat in N (0.395–0.427 s with one task, 0.315–0.535 s with 2); the library route
(`occursin` per indicator) grows linearly and is 2.7× slower than the hash-set matcher already at 10 indicators.

## 3. Where the time goes and the limiter

Shares of the GPU pipeline at 1,000,000 lines and 1,000 indicators, each step timed on its own: line table
40 %, token scan 47 %, hash match 8 %, extraction 7 % (end to end
33.287 ms).  The largest step is the token scan (flags, scan, scatter) (47 %).  The two scan steps read and write a 4-byte
flag per corpus byte (the lecture-7 scan on `UInt32` flags), so they move about 8 bytes per corpus byte against
the 1 byte the hash kernel reads; the hash kernel itself reads every token once (20,626,582 tokens,
5.8 bytes each on average), hashes it and probes the table 2.28 times on average.  Its
achieved rate, 44.7 GB/s of corpus against a copy rate of 240.7 GB/s, says it is bound by the
per-token work (a serial byte walk and a data-dependent probe per thread, 15 branches in the PTX) and not by
bandwidth; `CUDA.registers` 28 per thread, occupancy 100 %.
The limiter of the whole pipeline is therefore the scan traffic, which does not depend on the list, which is
exactly why the pipeline is flat in N.

## 4. The data rate: when the GPU is needed and how long it keeps up

| lines | GPU pipeline (MB/s) | GPU direct pipeline (MB/s) | + H2D (MB/s) | CPU 2 tasks (MB/s) | CPU 1 task (MB/s) | H2D / pipeline |
|---:|---:|---:|---:|---:|---:|---:|
| 125,000 | 3433.8 | 5237.1 | 2023.2 | 318.2 | 240.1 | 0.70 |
| 250,000 | 2332.6 | 5596.9 | 1557.6 | 314.7 | 242.8 | 0.50 |
| 500,000 | 3619.6 | 5659.4 | 2035.6 | 275.8 | 159.7 | 0.78 |
| 1,000,000 | 3577.2 | 5805.8 | 2019.2 | 289.6 | 245.0 | 0.77 |
| 2,000,000 | 3542.3 | 5793.3 | 1978.4 | 302.3 | 238.8 | 0.79 |
| 4,000,000 | 3287.7 | 5760.3 | 1908.7 | 315.6 | 237.3 | 0.72 |

With a list of 1,000 indicators the tuned CPU keeps up with **315.6 MB/s** on 2 tasks (237.3 MB/s per task,
27.3 TB/day); above that rate a GPU is needed, and one GPU keeps up with **1908.7 MB/s** including the pageable
copy (3287.7 MB/s with the logs already on the device; 164.9 TB/day).  The host-to-device copy costs
0.72× the pipeline at 4,000,000 lines (4.6 GB/s pageable, 11.3 GB/s pinned): the transfer
is not the wall yet; the kernels still set the end-to-end rate.
One GPU replaces about **8 CPU tasks** of this host at this list size (and the same at 10,000, since neither side depends on N).

## 5. The defensive conclusion

A per-indicator scan is only viable for small lists: on this GPU it costs 5.940 ms per 32 indicators and
1,000,000 lines, so a threat feed of 10,000 entries would take 1.86 s per 1,000,000 lines, 56× the
hash-set method; a list-independent method (hash set of whole tokens, or an automaton for substring
semantics) is required for a real feed.  With it, the list size is free: a SOC can match 10,000
indicators at the same rate as 10.  Sizing for 10,000 indicators: one CPU task of this host handles
20.5 TB/day, 2 tasks 27.3 TB/day, one GPU 164.9 TB/day with the copy; the GPU is the right tool when the
daily volume exceeds what the available cores cover, and only if the logs reach it faster than
1908.7 MB/s (storage or network), otherwise the storage is the limit.  Limits: synthetic logs; whole-token
semantics (no substrings, no regular expressions); cold indicators never hit (the hit count is constant);
the CPU baseline is 2 tasks on 2 hardware threads of a shared host; one GPU session; no real logs
(course policy).
