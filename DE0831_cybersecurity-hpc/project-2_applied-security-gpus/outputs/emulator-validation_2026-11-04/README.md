# Emulator validation of DE0831_P2 (no GPU), 4 November 2026

Evidence that the track-E scripts run and validate before the Colab T4 run.  Nothing here is a
measurement: the "GPU" is the CPU emulator in `../../tools/cpu-emulator`.

| File | What it is |
|---|---|
| `p2_run_quick_emulator.log` | `P2_QUICK=1 P2_MAIN=20000 julia --check-bounds=yes src/p2_run.jl` on the emulator: header block, all validation checks against the CPU baseline and the generator's ground truth, the eleven boundary cases, `Correct!` |
| `ptx_check.log` | `tools/ptx-check/ptxcheck.jl`: the nine kernels compiled to PTX (sm_75) with the real CUDA.jl 6.5.1 compiler; shared-memory allocations and atomics per kernel |
| `mutation_results.log` | eight mutants of `p2_gpu.jl` run through the validation: seven caught, the first-byte-filter mutant survives because the filter cannot change the match set (equivalent mutant) |
| `emulator-benchmark-run/` | `P2_QUICK=0 P2_SIZES=20000 P2_REPS=2` on the emulator: shows that the benchmark, results and analysis generators run end to end; **all numbers are meaningless** (emulated timings, empty PTX dump) and the real `results/` come from the T4 run |

Reading the PTX: the only atomic in the kernel bodies is `atom.global.or.b32` in `match_tiled!` and
`match_global!` (the OR into the line mask) and the counter adds in `match_counts!` and
`entropy_hist!`.  The `atom.cas.b32` listed for `scatter_positions!`, `token_entropy!` and
`entropy_hist!` is inside CUDA.jl's `gpu_signal_exception` helper, which is linked into every kernel
that keeps a bounds check or a checked `Int32` conversion; `p2_run.jl` therefore counts
instructions inside the kernel's `.entry` body only.
