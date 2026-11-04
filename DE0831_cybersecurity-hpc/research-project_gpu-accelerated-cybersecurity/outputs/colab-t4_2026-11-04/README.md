# Colab T4 run, 4 November 2026 (research project, topic 10)

`DE0831_RP_colab.ipynb` on a Tesla T4 (driver 580.82 / CUDA 13.3, CUDA.jl 6.5.1, Julia 1.12.7 with
2 threads on the Colab host, Intel Xeon 2.0 GHz, 2 hardware threads).  `Correct!` (every method
equals the ground truth for every list size, 11 hand-made cases; test suite passed), both sweeps,
four plots.  The results are in `DE0831_RP/results/` and in the submission archive
`../submission/DE0831_RP_Asgarli_251ADM047.zip` (built by the notebook from this run; its sources
are identical to the committed `DE0831_RP/src`).  This folder keeps the logs.

Key numbers (1,000,000 lines, 119.2 MB):

| method | 10 → 10,000 indicators |
|---|---|
| GPU hash-set pipeline (scan + compaction) | 32.9–33.3 ms, 30 M lines/s, flat; hash kernel alone 1.9–2.7 ms |
| GPU hash-set pipeline, no compaction | 19.8–24.8 ms, 40–50 M lines/s, flat; kernel alone 7.3–8.2 ms |
| GPU per-indicator (Project 2 kernel per 32) | 5.6 ms at 10 → 561 ms at 3,000 (5.9 ms per group); 1.86 s predicted at 10,000 |
| CPU hash-set, Colab host | 0.40–0.65 s with 1 task, 0.32–0.63 s with 2 (one core, hyper-threaded) |
| CPU `occursin` per indicator | 1.1 s at 10 → 33 s at 300 (linear) |

Corpus-size sweep (list of 1,000): GPU pipeline 3.3–3.6 GB/s, no compaction 5.2–5.8 GB/s, with the
pageable copy 1.9–2.0 GB/s (4.6 GB/s pageable, 11.3 GB/s pinned); Colab CPU 0.28–0.32 GB/s on 2
tasks.  The 4-core host's CPU sweeps (`DE0831_RP/results/*_cpu_Intel-R-Xeon-R-Processor-2-10GHz.csv`,
`../cpu-xeon4_2026-11-04/`) give 1.05–1.38 GB/s with 4 tasks.
