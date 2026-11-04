# Track E (log mining), full route: design note

Goal of the track: a GPU matcher that finds every log line carrying one of the supplied
indicators and flags high-entropy tokens, validated against the generator's ground truth over the
whole corpus, measured over at least four corpus sizes, and turned into one headline number: the
daily log volume at which one CPU core no longer keeps up and one GPU does.

The course primitives used are the ones taught: scan with `accumulate(+, flags)` and
compaction with a scatter kernel (lecture 7, slide 4: "the log-mining pattern: billions of log
lines filtered to the few that match an indicator of compromise"), coalesced byte access and
shared-memory tiles (lectures 5–6), privatised histograms and the Project 1 entropy kernel
(lecture 6, Project 1), the warm-up + `CUDA.@elapsed` harness (lecture 7, Project 1).

## 1. Data

`gen_logs.jl <ID> --lines N` (the handout generator, SHA-256 of the ID as seed) writes

| File | Content | For 1,000,000 lines |
|---|---|---|
| `corpus_<ID>.log` | one event per line, sshd (45 %) or nginx (55 %) | 119.2 MB |
| `indicators_<ID>.txt` | 12 addresses (x.y.z.200–254 of the RFC 5737 ranges) + 8 `.invalid` DGA domains | 20 patterns, 11–27 bytes |
| `truth_<ID>.csv` | `line,indicator` for every line that carries an indicator | 894 lines (0.089 %) |
| `entropy_truth_<ID>.csv` | `line,token,entropy` for every planted base64 payload (`/upload?d=<blob>`) | 243 tokens, 40–120 chars, 5.1–6.0 bits/char |

Background hosts use .1–.199, indicators .200–.254, so an indicator can never occur by chance;
the truth is exact. Corpus sizes for the measurement: 125k, 250k, 500k, 1M, 2M, 4M lines
(15 MB … 480 MB), each generated separately with `--lines` (the generator is deterministic, so
every size is reproducible from the ID).

Authorised use: only this generated data; nothing real.

## 2. Memory layout (what the kernels see)

| Array | Type | Size (1M lines) | Access pattern |
|---|---|---|---|
| `corpus` | `CuVector{UInt8}`, the file bytes as they are | 119 MB | thread *i* ↔ byte *i*; a warp reads 32 consecutive bytes: **coalesced** (one 32-byte sector per warp per load) |
| `line_start` | `CuVector{Int32}`, offset of each line's first byte + sentinel at the end | 4 MB | written by the scatter kernel at scanned positions; read by binary search only for the rare hits |
| `line_mask` | `CuVector{UInt32}`, bit *p* set if pattern *p* matched the line | 4 MB | `@atomic |=` by the few hitting threads (0.09 % of lines) |
| `patterns` | `UInt8[32, 32]` + `plen[32]`, copied once into **shared memory** per block (1 KB) | | every thread reads the same address: shared-memory broadcast, no bank conflict |
| `first_mask[256]` | `UInt32`, bit *p* set if pattern *p* starts with this byte; shared memory (1 KB) | | the **first-byte filter**: one lookup decides whether any pattern can start here |
| `tile` | `UInt8[TILE + HALO]` in shared memory | | the block loads its tile and the halo (longest pattern − 1 bytes) **once** from global memory, coalesced, then matches from shared memory |
| `token_start`, `token_entropy` | `Int32`, `Float32` per token | ~70 MB each | produced by flags → scan → scatter; one thread per token |

All offsets are 1-based `Int32` (fine up to 2 GB corpora). No structure of arrays is needed: the
only "record" is a byte.

## 3. Pipeline and kernels

```
file ──read──> corpus (host) ──copyto!──> corpus (device)
   [K1] newline_flags!      flags[i] = corpus[i] == '\n'                    (1 B read, 4 B write / byte)
        scan                 pos = accumulate(+, flags)                       (lecture 7)
   [K2] scatter!             line_end[pos[i]] = i  where flags[i] == 1         (compaction)
        line_start = [1; line_end .+ 1]  (array ops)
   [K3] match!               per byte i: first-byte filter, then compare the candidate patterns
                             against the shared-memory tile; on a hit: line = binary search in
                             line_start; @atomic line_mask[line] |= 1 << p
   [K4] flags → scan → scatter    matched = line indices with line_mask != 0   (compaction)
        lengths → scan → offsets; [K5] gather! copies each matched line into a packed buffer
   [K6] token_flags!         start[i] = is_tok[corpus[i]] && !is_tok[corpus[i-1]]
        scan → [K2] scatter  token_start
   [K7] token_entropy!       one thread per token: length by forward scan (≤ 255), 64-symbol
                             counts in shared memory (UInt8[64] per thread), H = −Σ p log2 p
   [K8] flags → scan → scatter    flagged tokens (H ≥ threshold) with their line (binary search)
```

The threshold is not the brief's ~5.0 hint but is read off the data: `entropy_hist!` (privatised
128-bin histogram of all token entropies, 0.05 bits per bin) and the host picks the midpoint of
the widest empty band **above the median token**.  On the 1M corpus the ordinary tokens end at
3.78 bits and the payloads start at 4.49, so the band is 3.80–4.45 and the threshold 4.125;
a 5.0 threshold would miss 49 of the 243 payloads.  Bands below the median are excluded
because the zero-entropy spike of one-symbol tokens leaves an equally wide empty band near 0.

K3 in detail (one block = one tile of `TILE` bytes, 256 threads, 4 bytes per thread in the
load phase, or `TILE = 256` with one byte per thread; decided by measurement):

1. Load the tile and the halo into shared memory (coalesced).
2. `sync_threads()`.
3. For each byte position *i* the thread owns: `m = first_mask[tile[i]]`; if `m == 0` continue
   (true for > 95 % of positions: most bytes are not `1`, `2` or the first letters of the
   domains). Otherwise for each set bit *p* of `m`: compare `plen[p]` bytes from the tile
   (shared memory) with `patterns[:, p]`; require a **token boundary** on both sides (the byte
   before and after must not be a token character), so `192.0.2.24` never matches inside
   `192.0.2.248`; on a full match, find the line (binary search over `line_start`, ≤ 22 steps,
   hits only) and `@atomic line_mask[line] |= 1 << (p-1)`.

Why this is the right technique: the bytes are read exactly once from global memory
(coalesced, 32 B per warp load); the comparison runs on shared memory; the first-byte filter
keeps the inner loop rare so divergence stays small; there is no race because the only shared
write is an atomic OR into a per-line word; boundary handling is explicit (tile halo for
patterns crossing tile edges, line sentinel at the corpus end, bounds checks on the last tile).

Variants kept for the analysis (each a one-line switch): K3 without shared memory (direct
global loads) and K3 without the first-byte filter. The measured difference is the evidence for
the limiter discussion.

## 4. CPU baseline (single-threaded, same computation)

`cpu_match(corpus, patterns)`: for each line, for each position, the same first-byte filter and
byte comparison with boundary check → set of (line, pattern). `cpu_token_entropy(corpus)`:
same tokenisation and entropy. Timed with `@elapsed` after one warm-up (CPU code; the GPU
harness is used for every GPU step). A second, library-style CPU version (`findall` with
`occursin` per indicator = the basic route) is reported too, so the comparison is not only
against a naive loop.

## 5. Validation (binary, over the whole corpus)

| Check | Expected |
|---|---|
| line table | `line_start` equals the CPU `findall('\n')` result; line count = N |
| match set | the set of (line, indicator) from `line_mask` **equals** `truth_<ID>.csv` exactly (894 rows for 1M); also equals the CPU baseline's set |
| extracted lines | the packed buffer, split, equals the corpus lines at those indices |
| tokens | token starts equal the CPU tokeniser's; entropies of the truth tokens equal `entropy_truth` to 1e-3 |
| flagging | at the chosen threshold, flagged set equals `entropy_truth` (precision = recall = 1); the table of precision/recall at 3.5, 4.0, the chosen value, 4.5, 5.0, 5.5 shows why |
| small cases | hand-made corpora: empty, one line without newline at the end, a pattern at byte 1, at the last byte, across a tile boundary, two patterns in one line, pattern as a substring of a longer token (must not match) |

Every check prints `Correct!` only when all pass; `test/runtests.jl` runs them.

## 6. Measurement plan

Harness: one warm-up launch, `CUDA.synchronize()`, then `CUDA.@elapsed` around each launch
(100 samples; mean, min, max), as in Project 1; the step that accumulates (`line_mask`) is
zeroed outside the timed region. **Every step is timed directly**: K1–K8 and the scans each get
their own number; the end-to-end GPU time is one `@elapsed` around the whole pipeline (not a
sum, not a difference). Transfer wall: host→device copy of the corpus (pageable and pinned),
device→host copy of the results, and the file read from disk, each timed separately.

Reported per corpus size (6 sizes): lines/s and MB/s for the match kernel alone, for the full
GPU pipeline, for the pipeline including the host→device copy, and for the CPU baseline;
plus the breakdown. Plots (Julia, CairoMakie, headless): throughput vs size, time breakdown,
entropy distribution with the threshold, precision/recall vs threshold.

Integer-operation count for K3 (for the roofline substitute accepted for track E): per byte,
the filter costs ~6 integer ops (load, table lookup, test, index arithmetic); per candidate
position (fraction *f* measured from the data, expected 3–5 %) up to Σ plen ≈ 350 compares in
the worst case, in practice a handful because the first mismatching byte ends each pattern.
The script counts the candidate fraction and the compare count on the GPU (atomics into two
counters, in a measurement-only variant), so the intensity (int ops per byte) is measured, not
guessed; bytes moved per byte = 1 (corpus) + ~0.03 (flags/scans amortised). With T4 figures
(2560 cores × 1.59 GHz ≈ 4.1 × 10¹² int ops/s; 320 GB/s) the model predicts whether the kernel
is bound by bandwidth or by instruction throughput; the measured achieved bandwidth,
`CUDA.registers`/occupancy and the PTX dump (written to `results/` **by the script**, with the
instruction counts extracted by the script) are the evidence.

## 7. The defensive conclusion (arithmetic)

Capacity per day = sustained rate × 86,400 s. With *R_cpu* bytes/s for one core and *R_gpu* for
the end-to-end GPU pipeline (including the copy): a site producing *V* bytes/day needs
⌈*V* / (86,400 *R_cpu*)⌉ cores or ⌈*V* / (86,400 *R_gpu*)⌉ GPUs; the crossover is the volume
above which one core cannot keep up (*V* > 86,400 *R_cpu*). Stated with the assumptions:
indicator count 20, line length ~120 B, logs already on the machine (the disk/network rate is
the next wall), batch processing with the corpus resident in device memory. Entropy flagging
adds the analyst-side number: flagged tokens per day at the chosen threshold and the measured
precision.

## 8. Files

```
DE0831_P2/
├── README.md, Project.toml, Manifest.toml
├── src/p2_common.jl      header block, timing harness (mean/min/max), device info, md tables
├── src/p2_data.jl        generator wrapper (calls gen_logs.jl for each size), loaders, truth parsing
├── src/p2_cpu.jl         CPU baseline: line table, matcher, tokeniser, entropy
├── src/p2_gpu.jl         kernels K1–K8 and the pipeline
├── src/p2_run.jl         header, validation (Correct!), benchmarks, results/benchmarks.md, analysis.md, plots
├── test/runtests.jl      runs p2_run.jl in check-only mode and the small hand-made cases
└── results/              benchmarks.md, analysis.md, *.png, ptx dump, raw timings (csv)
```

Lessons from Project 1 applied: no number derived by subtraction; evidence generated by the
scripts; comments checked against device facts; plots in Julia only; implausible numbers are
investigated before they are used.

## 9. Open points

- `TILE` and threads per block: 256 threads × 1 byte vs 256 threads × 4 bytes (`UInt32` loads)
  — decide by measurement, keep both in the results.
- Whether to time a pinned-memory copy (`CUDA.pin`) in addition to the pageable one.
- CairoMakie precompilation time on Colab (expected 5–10 min); fallback is to write the plot
  data as CSV and draw it in a second Julia step.
