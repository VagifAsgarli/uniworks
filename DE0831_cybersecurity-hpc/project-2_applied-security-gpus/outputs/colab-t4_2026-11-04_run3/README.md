# Colab T4 run 3, 4 November 2026 (both match kernels)

Full run of `DE0831_P2` with the second match kernel.  `Correct!` (18 boundary cases, all three
kernel variants on every case, test suite passed), six corpus sizes measured, plots drawn.

| File | Contents |
|---|---|
| `results/` | `benchmarks.md`, `analysis.md`, the CSVs, the PTX of both tiled kernels, the four plots, exactly as the script wrote them |
| `logs/` | `instantiate.log`, `p2_run.log`, `runtests.log` |
| `device.md` | the device block the script wrote into the README |

Key numbers (1,000,000 lines, 119.2 MB): `match_tiled_tri!` 6.6 ms (18.0 GB/s), `match_tiled!`
13.1 ms (9.1 GB/s), `match_global!` 15.5 ms; line table 13.0 ms, token starts 15.8 ms, token
entropies 11.4 ms; GPU pipeline 49.7 ms (2.4 GB/s), with the pageable copy 76.4 ms; CPU pipeline
5.66 s.  Largest corpus (4M lines): 18.1 M lines/s on the device, 12.3 M lines/s with the copy,
109× / 74× the single core.  Filters: 20.3 % of positions pass the first byte, 0.95 % the three
bytes; 0 % vs 71.5 % of warps skip the candidate loop.  Threshold 4.12 bits/char, precision =
recall = 1.

One sentence of `analysis.md` in this run quotes the first kernel's share of the pipeline
(26 %) where the pipeline's kernel (13 %) was meant; the template was corrected afterwards and
the submission's `results/` come from the following run.
