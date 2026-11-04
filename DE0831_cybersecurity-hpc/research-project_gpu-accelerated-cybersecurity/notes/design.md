# Research design: log indicator matching as the list grows (topic 10)

Student: Vagif Asgarli, 251ADM047 (alone, by agreement).  Code in `DE0831_RP/`.

## 1. Question and the measurable objective

How do log lines per second change when the indicator list grows from 10 to 10,000, for a GPU
and for a tuned multithreaded CPU, and what limits each method?  Secondary: the data rate at
which the GPU beats the CPU once the host-to-device copy is counted, and the number of CPU
cores it replaces.  The security context is a SOC matching a threat-intelligence list (tens to
tens of thousands of addresses and domains) against its daily logs.

## 2. Data

- The course corpus: `gen_logs.jl 251ADM047` → 1,000,000 lines, 119.2 MB (plus 125k, 250k,
  500k, 2M, 4M lines for the data-rate curve).  Its 20 indicators (12 addresses, 8 domains)
  hit 894 lines; the ground truth is the generator's `truth` file.
- Indicator lists of size N ∈ {10, 30, 100, 300, 1,000, 3,000, 10,000}: for N ≤ 20 a subset
  of the 20 (N = 10: 6 addresses + 4 domains); for N > 20 the 20 plus N − 20 synthetic "cold"
  indicators in the same forms: addresses `198.18.x.y` (RFC 2544 benchmarking range, never in
  the corpus) and DGA-style hostnames `[a-z]{12..20}.invalid` (checked against the corpus
  vocabulary).  Lists are generated from the student seed, deterministic.  The ground truth of
  every list is the generator's truth restricted to the list (verified by the CPU reference,
  which also catches any accidental hit).
- Why the hit count does not grow with N: a real threat list is mostly cold (most indicators
  never appear), and the question is the cost of the list, not of the hits.  Hits stay at
  0.09 % of lines for every N, so the methods are compared on the same work.

## 3. Matching semantics

An indicator matches a line when it occurs as a whole token: the bytes before and after are
not word characters (`[A-Za-z0-9.-]`), the Project 2 rule.  Tokens of the corpus under this
alphabet: timestamps' parts, hostnames, `sshd[1234]` pieces, addresses, paths' pieces …; the
addresses and the `.invalid` hostnames are tokens of their own in both line formats
(`from 192.0.2.24 port`, `"http://app3.invalid/"`).

## 4. Methods

| | method | cost model | where the list lives |
|---|---|---|---|
| G1 | **GPU per-indicator**: the Project 2 kernel `match_tiled_tri!` generalised to N patterns by iterating groups of 32 inside the block (the tile stays in shared memory; per group: table copy, three-byte filter, candidate loop) | bytes × ⌈N/32⌉ (one pass over the tile per group) | shared memory, per group |
| G2 | **GPU token hash-set**: token starts by flags → scan → scatter (lecture 7); one thread per token: FNV-1a hash of the token bytes, open-addressing probe into a table of (hash, offset, length) entries, byte compare on hash equality, atomic OR / flag per line | bytes (tokenise) + tokens × probes; independent of N except through the table size | global memory (L2/L1 cached); shared-memory copy when the table fits (N ≤ ~1,500 at 16 B/entry, 24 KB) as a measured variant |
| C1 | **CPU tuned**: the G2 algorithm in Julia, hand-written open-addressing table, no allocation per token, `Threads.@threads` over line chunks (1, 2, 4 threads on the 4-core Xeon; 1–2 on the Colab host) | bytes + tokens × probes | L1/L2 |
| C2 | **CPU library**: `occursin` per indicator over the lines (the brief's basic route) | lines × N | – |

G1 is the "unoptimised GPU version" baseline of the brief: it shows the linear law and the
list size at which G2 overtakes it.  G2 is the method; C1 the tuned CPU baseline; C2 the
library baseline for N ≤ 300.

| G3 | **GPU hash-set without compaction**: one thread per byte, grid-stride; a thread whose byte starts a token walks it, hashes and probes exactly as G2; hits appended to (position, indicator) buffers with one atomic counter (hits are 0.09 % of lines); line numbers of the hits by binary search afterwards | bytes (one pass), with warp divergence instead of the scan traffic | same table |

G3 answers a question the first CPU measurements raised: the tuned CPU matcher reaches about
1.1 GB/s on four cores because it does one pass with no compaction, while G2 pays the
lecture-7 scan twice (line table and token starts: 8 bytes of flag traffic per corpus byte).
G3 keeps the line table (needed only to name the lines of the few hits) and drops the token
scan; the measured difference between G2 and G3 is what the compaction costs or saves.

Hash table: capacity = next power of two ≥ 2N (load ≤ 0.5), linear probing; entry = `UInt32`
hash, `Int32` offset into a packed pattern byte buffer, `Int32` length (12 B); a token is
hashed once (FNV-1a 32-bit over its bytes, same function on CPU and GPU), probed until an
empty slot; on hash equality the bytes are compared from global memory (the packed buffer,
L2-resident).  Expected probes per lookup at load 0.5 (unsuccessful search, linear probing):
about 2.5; measured per run with a counter kernel.

Token alphabet for G2/C1: `[A-Za-z0-9.-]` (word characters), so indicators are whole tokens;
tokens longer than 64 bytes are hashed on their first 64 (no indicator is longer than 27, so a
longer token cannot be an indicator; the compare rejects it).

## 5. Kernels (G2)

- `word_flags!`: flag per byte = token start under the word alphabet (reuse of `token_flags!`
  with the word table).
- scan (`accumulate`) + `scatter_positions!` → `token_start`, count (Project 2 code).
- `hash_match!`: one thread per token: walk the token (≤ 64 bytes), FNV-1a; probe the table;
  on a hit `CUDA.@atomic line_hit[line] |= 1` where the line is found by binary search over
  `line_start` (Project 2) — or, cheaper, write `hit_token[k] = entry` and let compaction
  produce the (line, indicator) pairs.  Output: the list of (token index, indicator index) of
  the hits, compacted; the line number from the binary search at extraction time.
- `probe_counts!`: measurement-only kernel: probes per token, hash-equal compares.
- G1: `match_groups!` = `match_tiled_tri!` with an outer loop over pattern groups (tables
  re-copied per group, `sync_threads()` between groups) and a per-line 32-bit mask per group,
  or simpler: one launch per group (N/32 launches, each 4 ms at 1M lines on the T4) with the
  mask array of size lines × groups: the launch form is simpler and the cost is the same
  within a few percent (checked by timing both at N = 1,000).

## 6. Measurement matrix

| sweep | fixed | varied | methods |
|---|---|---|---|
| list size | 1M lines | N = 10 … 10,000 | G1 (to 1,000 or 3,000), G2 (global and shared table), C1 (1/2/4 threads), C2 (to 300) |
| corpus size | N = 1,000 | 125k … 4M lines | G2 (+ H2D pageable and pinned), C1 (4 threads) |
| threads | 1M lines, N = 1,000 | 1, 2, 4 threads | C1 |

Timing: lecture 7 (warm-up, `CUDA.@elapsed` per launch, 100 samples, mean and min–max); every
step timed directly (tokenise, hash-match, extraction, copy); CPU wall-clock best of 3; the
Project 2 harness (`time_stats`, `time_cpu`) reused.  Evidence per run: probes per token, table
bytes vs L2 (4 MB on the T4) and L1, registers/occupancy, device-to-device copy rate.

## 7. Expected results and the analysis

- G1: time ∝ ⌈N/32⌉: 6.6 ms × 313 ≈ 2 s at N = 10,000 and 1M lines (0.5 M lines/s).
- G2: tokenise ≈ 15 ms (the scan), hash-match ≈ 5–10 ms for 22 M tokens, flat in N until the
  table leaves L1 (N ≈ 2,000 at 12 B × 2N) and then L2 (N ≈ 170,000: never in this study), so
  the curve should be flat to 10,000 with a small step; G2 overtakes G1 at N ≈ 64–128.
- C1: ≈ 30–60 MB/s per thread (hash per token), 4 threads ≈ 150 MB/s; G2 ≈ 4–6 GB/s on the
  device, ≈ 1.5 GB/s with the pageable copy → the GPU replaces ≈ 10–40 cores at any N; the
  crossover data rate is the CPU's rate × cores.
- The limiter of G2: the scan traffic (8 bytes per corpus byte) and the token walk, not the
  table; of G1: the passes over the tile; of C1: one hash per token, memory-latency bound.
- Security conclusion: a per-indicator scan is only viable for lists below ≈ 100; a
  list-independent method is required for a real threat feed; the sizing arithmetic per
  GB/day for N = 10,000.

## 8. Validation

Every method's hit set equals the ground truth of its list on the 1M corpus (and the CPU
reference equals the generator's truth for N = 20); G2 global and shared variants agree;
small hand-made cases: token at corpus start/end, indicator that is a prefix of a token
(`192.0.2.24` vs `192.0.2.248`), two indicators in one line, empty list.

## 9. Report (6–10 pages, RTU format) and presentation

Sections as the brief: problem and objective; approach (design, memory, decomposition);
baseline and methodology; results (tables, plots: lines/s vs N for all methods, lines/s vs
corpus size with and without copy, CPU threads scaling, time breakdown of G2); security
discussion; reproducibility appendix.  Presentation: 10 slides, live run on Colab
(`RP_QUICK=1` run: N = 1,000 on 125k lines, about a minute).

## 10. Timeline

- 4–7.11: code (G2, G1, C1, C2), validation on the emulator, PTX check; proposal to the
  instructor.
- 8–12.11: Colab T4 runs; CPU runs on the 4-core machine; results and plots.
- 13–30.11: report draft; L13/lab 13 material folded in when delivered.
- 1–10.12: report final, slides, speaker notes, Q&A; 11.12 submit; 14.12 defend.
