# Colab T4 run 4, 4 November 2026 (final run)

The run whose `results/` are in `DE0831_P2/results/` and in the submission archive
`../submission/DE0831_P2_Asgarli_251ADM047.zip` (built by the notebook from this run; the
archive's sources are identical to the committed `DE0831_P2/src`).  `Correct!`, test suite
passed, six corpus sizes, both match kernels, all plots.

| File | Contents |
|---|---|
| `logs/` | `instantiate.log`, `p2_run.log` (full console output), `runtests.log` |
| `run_logs.zip` | the same logs as downloaded from Colab |

Key numbers (1,000,000 lines, 119.2 MB, Tesla T4): `match_tiled_tri!` 6.6 ms (18.2 GB/s),
`match_tiled!` 12.5 ms (9.5 GB/s), `match_global!` 14.6 ms; line table 13.1 ms, token starts
15.8 ms, token entropies 11.2 ms; GPU pipeline 49.5 ms (2.4 GB/s), with the pageable copy
74.6 ms; CPU pipeline 5.50 s.  Largest corpus (4M lines): 18.4 M lines/s on the device,
12.5 M lines/s with the copy, 105× / 71× the single core; 1.8 TB/day per core, 129 TB/day per
GPU.  Threshold 4.12 bits/char, precision = recall = 1.
