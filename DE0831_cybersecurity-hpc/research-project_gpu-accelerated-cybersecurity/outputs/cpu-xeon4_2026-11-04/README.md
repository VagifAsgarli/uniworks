# CPU-only run, 4 November 2026 (4-core Intel Xeon, no GPU)

`RP_CPU_ONLY=1 julia -t 4 --project=. src/rp_run.jl` on the development container
(Intel Xeon 2.10 GHz, 4 hardware threads, 15 GB RAM; Julia 1.12.7).  Validation `Correct!`
(every CPU method equals the ground truth for every list size, 11 hand-made cases), then the
list-size sweep (1, 2, 4 tasks; `occursin` to 300) and the corpus-size sweep (125k–4M lines,
list of 1,000).  The CSVs are in `DE0831_RP/results/list_sweep_cpu_Intel-R-Xeon-R-Processor-2-10GHz.csv`
and `size_sweep_cpu_...csv`; this folder keeps the console log.

Key numbers (1,000,000 lines, 119.2 MB): tuned hash-set matcher 0.31–0.41 s with one task
(290–390 MB/s), 0.17–0.21 s with two, 0.086–0.113 s with four (1.05–1.38 GB/s), flat from 10 to
10,000 indicators; `occursin` per indicator 0.80 s at 10, 2.5 s at 30, 7.9 s at 100, 24.8 s at
300 (linear).  Corpus-size sweep with four tasks: 0.86–1.14 GB/s from 125k to 4M lines.
