# Colab T4 run 2, 4 November 2026 (first complete run)

The first complete run of `DE0831_P2` on a Tesla T4 (run 1 stopped at the threshold check,
see the commit "threshold above the median").  Everything validated (`Correct!`, 11 boundary
cases, test suite passed) and all six corpus sizes were measured.  These results are kept as
the baseline that led to the second match kernel; the submission's `results/` come from the
later run with both kernels.

| File | Contents |
|---|---|
| `results/` | `benchmarks.md`, `analysis.md`, the CSVs, the PTX of `match_tiled!`, the four plots, exactly as the script wrote them |
| `logs/` | `instantiate.log` (CUDA.jl 6.5.1, driver 580.82 / CUDA 13.3), `p2_run.log`, `runtests.log` |
| `device.md` | the device block the script wrote into the README |

Key numbers (1,000,000 lines, 119.2 MB): match kernel `match_tiled!` 12.9 ms (9.2 GB/s, 4 % of
the 230.7 GB/s copy rate), line table 12.9 ms, token starts 16.4 ms, token entropies 10.5 ms,
GPU pipeline 56.0 ms (2.1 GB/s), pageable copy 25.7 ms (4.6 GB/s), pinned 9.8 ms (12.1 GB/s);
CPU pipeline 5.15 s (23 MB/s); threshold 4.12 bits/char, precision = recall = 1.

What the run showed: the match kernel is neither bandwidth-bound (4 % of the copy rate) nor
explained by its lane-counted integer work (0.5 ms predicted); the first-byte filter passes
20.3 % of the positions, so every warp runs the candidate loop.  That diagnosis produced
`match_tiled_tri!` (three-byte filter, 4 KB tile), measured in the next run.
