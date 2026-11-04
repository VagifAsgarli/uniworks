# Log Indicator Matching on the GPU as the Indicator List Grows

DE0831 Cybersecurity Solutions in High-Performance Computing Environments, research project
(topic 10).  Vagif Asgarli, 251ADM047.  Draft: sections 1–3 and 6 are written from the design;
sections 4–5 are filled from `DE0831_RP/results/` after the measurement runs.  The final
document follows the RTU FCSITE formatting guidelines (Times New Roman, 1.5 spacing, margins
3.18/2.54 cm, centred numbered headings, "Fig. n.m." below figures, "Table n.m" above tables,
references in LVS ISO 690).

## 1. Problem and measurable objective

A security operations centre matches its logs against threat-intelligence indicators: addresses
and hostnames known to be malicious.  Real indicator lists are long (thousands to tens of
thousands of entries) and mostly cold: almost no indicator ever appears in the logs, but every
one of them must be checked against every line.  The question of this project is the cost of
the list: **how many log lines per second can one GPU match as the indicator list grows from 10
to 10,000 entries, against a tuned multithreaded CPU implementation, and what limits each
method?**  Two secondary questions follow from it: the data rate at which the CPU stops keeping
up and the GPU is needed, including the host-to-device transfer, and the rate the GPU itself
keeps up with; and the number of CPU cores that one GPU replaces.

The target metric is lines per second (equivalently MB/s of log text) at a given list size,
measured on the course corpus, with the hit set verified against the ground truth for every
list size, so that no method is faster because it is wrong.

## 2. Approach

### 2.1. Data

The course log corpus is generated with the handout generator `gen_logs.jl` run with the
student ID (seed from SHA-256 of `251ADM047`): 1,000,000 lines, 119.2 MB, of sshd and nginx
events with addresses from the RFC 5737 documentation ranges and `.invalid` hostnames (RFC
2606).  Its 20 indicators (12 addresses, 8 DGA-style domains) occur in 894 lines, listed in the
generator's truth file.  Corpora of 125,000 to 4,000,000 lines are generated the same way for
the data-rate curve.  Nothing is collected from any real system.

Indicator lists of 10, 30, 100, 300, 1,000, 3,000 and 10,000 entries are built deterministically
from the same seed.  For sizes up to 20 they are subsets of the generator's indicators; above
20 they are the 20 plus synthetic cold indicators in the same two forms: addresses from the
RFC 2544 benchmarking range 198.18.0.0/15 and DGA-style hostnames of 12–20 letters ending in
`.invalid`.  Neither form can occur in the corpus, so the hit set of every list is the
generator's truth restricted to the list, and only the list size changes between runs.  This
reproduces the situation of a real feed (most indicators cold) and keeps the comparison fair:
every method does the same matching work and reports the same 894 hits whatever the list.

### 2.2. Matching semantics

An indicator matches a line when it occurs as a whole token: the bytes before and after it are
not word characters (`[A-Za-z0-9.-]`).  So `192.0.2.24` does not match inside `192.0.2.248`
and `app3.invalid` not inside `xapp3.invalid`.  Addresses and hostnames are tokens of their own
in both event formats (`from 192.0.2.24 port`, `"http://app3.invalid/"`).  Every method,
on the CPU and on the GPU, applies the same rule; the library baseline (`occursin`) uses
substring semantics, which on this corpus gives the same hits.

### 2.3. GPU design: the token hash-set matcher

The method treats the corpus as one flat byte vector in device memory and works in three
steps, all with the lecture-7 pattern of a flag per byte, an inclusive scan and a scatter
(stream compaction), so that every warp reads 32 consecutive bytes (coalesced):

1. **Line table.** A kernel flags every newline; the scan and the scatter give the start of
   every line and a sentinel, the same table as the CPU builds.
2. **Token starts.** A kernel flags every byte that starts a token (a word byte not preceded
   by one); scan and scatter give the token positions, about 22 million for the 1M corpus.
3. **Hash match.** One thread per token walks its bytes (at most 64, no indicator is longer
   than 27), computing the FNV-1a hash as it reads, then probes an open-addressing hash
   table of the indicators with linear probing: the table holds, per slot, the hash, the
   indicator's index, and the offset and length of its bytes in a packed buffer; on a hash
   match the bytes are compared.  The thread writes the indicator index (or 0) for its token.
   A token longer than 64 bytes cannot be an indicator and is not looked up.
4. **Extraction.** The hit tokens are compacted (flags, scan, scatter) and a small kernel
   finds the line of every hit by binary search over the line table; the (line, indicator)
   pairs are copied to the host.

The cost is one pass over the corpus and one hash per token, independent of the list size;
the list enters only through the table's footprint (16 bytes per slot at a load of at most
0.5: 10 KB for 300 indicators, 320 KB for 10,000) against the GPU's caches.  Two placements of
the table are measured: in global memory (served by L1/L2) and, while it fits, with the keys
copied into shared memory by every block (16 KB, lists up to about 2,000).

The memory strategy is therefore: corpus read once, coalesced; flags and scans in global
memory (their traffic, 8 bytes per corpus byte, is the price of the compaction pattern and
is measured separately); the small table in cache or shared memory; outputs compacted so that
the device-to-host copy is a few kilobytes.  The decomposition is one thread per byte for the
flags, one thread per token for the match, and one thread per hit for the extraction.

### 2.4. GPU baseline: the per-indicator kernel

The unoptimised GPU version of the brief is the matching kernel of Project 2, which tests all
patterns of a group of at most 32 at every byte position: a block loads a 4 KB tile of the
corpus and the group's tables into shared memory, a three-byte prefix filter and a first-byte
mask reject most positions, candidates are compared byte by byte, and a whole-token hit sets
the pattern's bit in the line's 32-bit mask with one atomic OR.  For a list of N indicators it
is launched once per group of 32, so its cost grows as ⌈N/32⌉ passes over the corpus.  It is
validated against the same ground truth and measured up to 3,000 indicators (94 launches);
its cost at 10,000 is predicted from the measured cost per group.

## 3. Baseline and methodology

### 3.1. The tuned CPU baseline

The CPU baseline implements the same token hash-set algorithm in Julia, tuned: a hand-written
open-addressing table (the same layout and hash as the kernel), a single pass over the bytes
that detects tokens, hashes them as they are read and probes the table, with no allocation per
token; the corpus is cut into newline-aligned chunks and each chunk is scanned by one task
(`Threads.@threads`), with the line numbers of the chunks counted in parallel first.  It is
measured with 1, 2 and 4 tasks on a 4-core Intel Xeon (2.1 GHz) and with 1 and 2 tasks on the
Colab host (Intel Xeon 2.0 GHz, 2 hardware threads), the machine that holds the GPU.  The
library route of the brief, `occursin` of every indicator over every line, is measured for
lists up to 300 as the naive reference.

### 3.2. Measurement procedure

Every GPU time follows the lecture-7 method: one warm-up launch (which also compiles the
kernel), `CUDA.synchronize()`, then one `CUDA.@elapsed` per launch (CUDA events: GPU time)
over 100 launches; tables give the mean and, where it matters, the minimum and maximum.
Every step of the pipeline is timed on its own, the whole pipeline is one timing of its own,
and the host-to-device copy (pageable and pinned) is a separate timing; no figure is a
difference of two timings.  Kernels that accumulate (the per-indicator masks) are reset
before every launch outside the timed region, and every launch's outputs are freed at once
so that no garbage collection lands inside a timed interval.  CPU times are wall-clock
`@elapsed` of CPU code, the best of three runs after a warm-up, with the number of tasks
stated.  Rates are corpus lines or bytes divided by the time.

The script produces its own evidence: the probes per token and the hash-equal compares from a
counting kernel, the table bytes against the L1 and L2 sizes, registers, shared memory and
occupancy of every kernel, the PTX of the hash-match kernel with its instruction classes,
and the device-to-device copy rate as the practical bandwidth bound.

### 3.3. Validation

Before any timing the run checks, on the 1M corpus: the CPU matcher (with 1 and more tasks)
equals the generator's truth for its 20 indicators; the `occursin` baseline equals the truth;
the GPU line table equals the CPU's; the GPU hash-set matcher (global table and shared keys)
and the GPU per-indicator matcher equal the CPU matcher; and for every list size all methods
equal the truth restricted to the list.  Eleven hand-made cases cover the empty corpus, a
corpus without a final newline, indicators that are prefixes of longer tokens, several hits in
one line, chunk boundaries of the CPU matcher, and tokens at and beyond the 64-byte hashing
limit.  The run prints `Correct!` only if everything passes.

## 4. Results

*(to be filled from `results/benchmarks.md`: Table 4.1 list-size sweep; Table 4.2 corpus-size
sweep; Table 4.3 CPU tasks; Fig. 4.1 rate vs list size; Fig. 4.2 breakdown vs list size;
Fig. 4.3 rate vs corpus size; Fig. 4.4 CPU tasks; the evidence table.)*

## 5. Security discussion

*(to be filled from `results/analysis.md`: the per-indicator method's linear cost and the list
size where it stops being viable; the list-independent method's flat rate; the data rate at
which the CPU stops keeping up and the GPU's ceiling with the copy; cores replaced; sizing
arithmetic for a feed of 10,000 indicators and V GB/day; limitations: synthetic logs,
whole-token semantics, constant hit count, one GPU session; ethical/legal notes: only
self-generated data, documentation and benchmarking address ranges, nothing probed or
collected, course policy.)*

## 6. Reproducibility appendix

Hardware: Google Colab, Tesla T4 (40 SMs, 15 GB, compute capability 7.5), host Intel Xeon
2.0 GHz with 2 hardware threads; CPU sweeps also on a 4-core Intel Xeon 2.1 GHz.  Software:
Julia 1.12.7, CUDA.jl 6.5.1 (CUDA driver and runtime as recorded in the README's device
block), CairoMakie 0.15.  Execution: `julia --project=. -e 'using Pkg; Pkg.instantiate()'`,
then `julia -t auto --project=. src/rp_run.jl` (validation, sweeps, results, plots; the
generator runs automatically from the student ID) and `julia --project=. test/runtests.jl`;
`RP_CPU_ONLY=1 julia -t 4 --project=. src/rp_run.jl` for the CPU sweeps on a machine without
a GPU; the Colab notebook `DE0831_RP_colab.ipynb` reproduces the GPU runs end to end.  All
numbers in the report are copied from `results/` as written by the script.
