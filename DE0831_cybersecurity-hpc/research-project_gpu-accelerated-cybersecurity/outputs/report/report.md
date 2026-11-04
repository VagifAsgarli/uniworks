**RIGA TECHNICAL UNIVERSITY**

Faculty of Computer Science, Information Technology and Energy

Institute of Information Technology

**LOG INDICATOR MATCHING ON THE GPU AS THE INDICATOR LIST GROWS**

Research project report

DE0831 Cybersecurity Solutions in High-Performance Computing
Environments

Student: Vagif Asgarli, 251ADM047

Lecturers: Assoc. Prof. Dr. sc. ing. Arnis Lektauers, M. sc. ing. Marta
Narigina

Riga 2026

**TABLE OF CONTENTS**

1\. PROBLEM AND MEASURABLE OBJECTIVE 3

2\. APPROACH 3

> 2.1. Data 3
>
> 2.2. Matching semantics 4
>
> 2.3. GPU design: the token hash-set matcher 4
>
> 2.4. The same match without compaction 5
>
> 2.5. GPU baseline: the per-indicator kernel 5

3\. BASELINE AND METHODOLOGY 5

> 3.1. The tuned CPU baseline 5
>
> 3.2. Measurement procedure 5
>
> 3.3. Validation 6

4\. RESULTS 6

> 4.1. Rate against the list size 7
>
> 4.2. Rate against the corpus size and the transfer 9
>
> 4.3. CPU tasks 10
>
> 4.4. Summary of the comparison 11

5\. SECURITY DISCUSSION 11

> 5.1. Implications for a defender 11
>
> 5.2. Limitations 12
>
> 5.3. Ethical and legal notes 12

CONCLUSIONS 12

LIST OF REFERENCES 13

APPENDIX 1. REPRODUCIBILITY 14

**1. PROBLEM AND MEASURABLE OBJECTIVE**

A security operations centre (SOC) matches its logs against
threat-intelligence indicators: addresses and hostnames known to be
malicious. Real indicator lists are long, from a few hundred to tens of
thousands of entries, and almost entirely cold: nearly none of the
indicators ever appears in the logs, yet every one of them has to be
checked against every line. The cost of a matcher therefore depends on
how the list enters the algorithm. A per-indicator scan pays for every
entry on every line; a method that looks each log token up in a set of
the indicators pays once per token, whatever the list size.

The measurable objective of this project is the number of log lines per
second that one GPU matches as the indicator list grows from 10 to
10,000 entries, compared with a tuned multithreaded CPU implementation
of the same algorithm and with the naive library route, with the hit set
verified against the ground truth for every list size. Two secondary
questions follow: the data rate (MB/s, GB per day) at which the CPU
stops keeping up and the GPU is needed once the host-to-device transfer
is counted, and the number of CPU cores that one GPU replaces. The
security conclusion is a sizing rule for a SOC: which method to use for
a feed of a given size, and when a GPU pays.

The target metric is lines per second at a given list size on the course
log corpus, equivalently MB/s of log text, reported with the timing
method of lecture 7; every method is validated before it is timed, so
that no method is fast because it is wrong.

**2. APPROACH**

**2.1. Data**

The course log corpus is produced by the handout generator gen_logs.jl
run with the student ID (the seed is the SHA-256 of 251ADM047):
1,000,000 lines, 119.2 MB, of sshd and nginx events with addresses from
the RFC 5737 documentation ranges and hostnames ending in .invalid (RFC
2606). Its 20 indicators (12 addresses, 8 DGA-style domains) occur in
894 lines, listed in the generator’s truth file. Corpora of 125,000 to
4,000,000 lines are generated the same way for the data-rate curve.
Nothing is collected from any real system.

Indicator lists of 10, 30, 100, 300, 1,000, 3,000 and 10,000 entries are
built deterministically from the same seed. Up to 20 entries they are
subsets of the generator’s indicators; above 20 they are the 20 plus
synthetic cold indicators in the same two forms, addresses from the RFC
2544 benchmarking range 198.18.0.0/15 and DGA-style hostnames of 12 to
20 letters ending in .invalid. Neither form can occur in the corpus, so
the hit set of every list is the generator’s truth restricted to the
list and only the list size changes between runs. This reproduces a real
feed, where almost every indicator is cold, and keeps the comparison
fair: every method must report the same 894 hits for every list.

**2.2. Matching semantics**

An indicator matches a line when it occurs as a whole token: the bytes
before and after it are not word characters \[A-Za-z0-9.-\]. So
192.0.2.24 does not match inside 192.0.2.248 and app3.invalid not inside
xapp3.invalid. Addresses and hostnames are tokens of their own in both
event formats. Every method applies this rule; the library baseline
(occursin) uses substring semantics, which on this corpus gives the same
hits. Under this alphabet the 1M corpus has 20,626,582 tokens of 5.8
bytes on average.

**2.3. GPU design: the token hash-set matcher**

The corpus is one flat byte vector in device memory: thread i handles
byte i and every warp reads 32 consecutive bytes (coalesced). Four
steps, the first three with the lecture-7 pattern of a flag per byte, an
inclusive scan and a scatter kernel (stream compaction):

- Line table: a kernel flags every newline; scan and scatter give the
  first byte of every line plus a sentinel.

- Token starts: a kernel flags every byte that starts a token (a word
  byte not preceded by one); scan and scatter give the token positions.

- Hash match: one thread per token walks its bytes (at most 64; no
  indicator is longer than 27), computes the FNV-1a hash as it reads and
  probes an open-addressing table of the indicators with linear probing;
  a slot holds the hash, the indicator’s index and the offset and length
  of its bytes in a packed buffer, compared on a hash match. The thread
  writes the indicator index, or 0, for its token.

- Extraction: the hit tokens are compacted and a small kernel finds the
  line of every hit by binary search over the line table; the (line,
  indicator) pairs go to the host.

The cost is one pass over the corpus and one hash per token, independent
of the list size; the list enters only through the table’s footprint (16
bytes per slot at a load of at most 0.5: 0.5 KB for 10 indicators, 512
KB for 10,000) against the caches. Two placements are measured: the
table in global memory, served by L1 and L2, and, while it fits, the
keys copied into shared memory by every block (16 KB, lists up to about
2,000). Memory strategy: the corpus read once, coalesced; flags and
scans in global memory, whose 8 bytes of traffic per corpus byte are the
price of the compaction and are measured on their own; outputs
compacted, so the device-to-host copy is a few kilobytes. Decomposition:
one thread per byte for the flags, per token for the match, per hit for
the extraction.

**2.4. The same match without compaction**

A second variant asks whether the compaction is worth its traffic. One
thread per byte, grid-stride, tests whether its byte starts a token and,
if so, walks, hashes and probes it exactly as above; a hit is appended
to a (position, indicator) buffer with one atomic counter, free in
practice because hits are 0.09 % of lines. The line table is kept for
the line numbers of the hits; the token scan disappears. The difference
between the variants is what the compaction costs or saves: scan traffic
against the divergence of a warp whose lanes walk tokens of different
lengths while four lanes in five idle.

**2.5. GPU baseline: the per-indicator kernel**

The unoptimised GPU version of the brief is the Project 2 kernel, which
tests all patterns of a group of at most 32 at every byte position: a
block loads a 4 KB tile and the group’s tables into shared memory, a
three-byte prefix filter and a first-byte mask reject most positions,
candidates are compared byte by byte, and a whole-token hit sets the
pattern’s bit in the line’s 32-bit mask with one atomic OR. For N
indicators it is launched once per group of 32, so its cost grows as
⌈N/32⌉ passes over the corpus; it is validated against the same truth,
measured up to 3,000 indicators (94 launches), and predicted at 10,000
from the cost per group.

**3. BASELINE AND METHODOLOGY**

**3.1. The tuned CPU baseline**

The CPU baseline is the same token hash-set algorithm in Julia, tuned: a
hand-written open-addressing table with the kernel’s layout and hash,
one pass over the bytes that detects tokens, hashes them as they are
read and probes the table, no allocation per token, and the corpus cut
into newline-aligned chunks scanned by one task each (Threads.@threads).
It is measured with 1, 2 and 4 tasks on a 4-core Intel Xeon (2.1 GHz)
and with 1 and 2 tasks on the Colab host that holds the GPU (one core,
two hardware threads). The library route, occursin of every indicator
over every line, is measured for lists up to 300 as the naive reference.

**3.2. Measurement procedure**

Every GPU time follows the lecture-7 method: one warm-up launch, which
also compiles the kernel, CUDA.synchronize(), then one CUDA.@elapsed per
launch (CUDA events, GPU time) over 100 launches; the tables give the
mean and, where it matters, the minimum and maximum. Every step of the
pipeline is timed on its own, the whole pipeline is one timing of its
own, and the host-to-device copy (pageable and pinned) is a separate
timing: no figure is a difference of two timings. Accumulating kernels
are reset outside the timed region and every launch’s outputs are freed
at once, so no garbage collection lands inside a timed interval. CPU
times are wall-clock @elapsed, the best of three runs after a warm-up,
with the number of tasks stated. Rates are lines or bytes divided by the
time. The script produces its own evidence: probes per token from a
counting kernel, table bytes against the cache sizes, registers and
occupancy, the PTX of the hash-match kernel, and the device-to-device
copy rate as the practical bandwidth bound.

**3.3. Validation**

Before any timing the run checks on the 1M corpus that the CPU matcher
with 1 and more tasks equals the generator’s truth for its 20
indicators, that the occursin baseline equals the truth, that the GPU
line table equals the CPU’s, that the GPU hash-set matcher (global table
and shared keys), the variant without compaction and the per-indicator
matcher equal the CPU matcher, and, for every list size, that all
methods equal the truth restricted to the list. Eleven hand-made cases
cover the empty corpus, a corpus without a final newline, indicators
that are prefixes of longer tokens, several hits in one line, chunk
boundaries, and tokens at and beyond the 64-byte limit. The run prints
Correct! only if everything passes.

**4. RESULTS**

All numbers are from a Tesla T4 (40 SMs, 15 GB, compute capability 7.5,
CUDA.jl 6.5.1, Julia 1.12.7) in Google Colab and from the 4-core Xeon
for the CPU task sweeps, as written by the script into the results
folder of the submitted code.

**4.1. Rate against the list size**

Table 4.1 and Fig. 4.1 give the list-size sweep on 1,000,000 lines
(119.2 MB). The GPU hash-set pipeline is flat: 32.9 to 33.3 ms from 10
to 10,000 indicators, 30 million lines/s, a spread of 1 %; its
hash-match kernel alone takes 1.9 to 2.7 ms with 1.4 to 2.4 probes per
token, so even the kernel that touches the table does not see the list.
The variant without compaction is flat as well, at 19.8 to 24.8 ms (40
to 50 million lines/s). The per-indicator kernel grows linearly with the
number of groups, 5.9 ms per group of 32: 5.6 ms at 10 indicators, 187
ms at 1,000, 561 ms at 3,000, and 1.86 s predicted at 10,000, 56 times
the hash-set pipeline. With the line table it needs, it is overtaken by
the hash-set pipeline between 30 and 100 indicators. The tuned CPU
matcher is flat too; the library route grows linearly, 0.80 s at 10
indicators and 24.8 s at 300 on the 4-core host, about 14 minutes per
million lines at 10,000.

Table 4.1

**Matching Time and Rate Against the List Size (1,000,000 lines, 119.2
MB)**

| **Indicators** | **GPU hash-set pipeline, ms (M lines/s)** | **GPU no compaction, ms (M lines/s)** | **GPU per-indicator, ms** | **CPU 4 tasks, s (M lines/s)** | **CPU 1 task, s** | **occursin, s** |
|----------------|-------------------------------------------|---------------------------------------|---------------------------|--------------------------------|-------------------|-----------------|
| 10             | 32.9 (30.4)                               | 24.8 (40.4)                           | 5.6                       | 0.088 (11.4)                   | 0.322             | 0.80            |
| 30             | 33.2 (30.1)                               | 20.7 (48.3)                           | 7.7                       | 0.110 (9.1)                    | 0.407             | 2.50            |
| 100            | 33.0 (30.3)                               | 20.8 (48.0)                           | 23.7                      | 0.094 (10.7)                   | 0.354             | 7.95            |
| 300            | 33.0 (30.3)                               | 19.8 (50.4)                           | 58.6                      | 0.086 (11.6)                   | 0.307             | 24.8            |
| 1,000          | 33.3 (30.0)                               | 20.4 (48.9)                           | 186.6                     | 0.113 (8.9)                    | 0.409             | –               |
| 3,000          | 33.3 (30.1)                               | 20.3 (49.3)                           | 561.4                     | 0.103 (9.7)                    | 0.342             | –               |
| 10,000         | 33.1 (30.2)                               | 20.2 (49.5)                           | 1,860 (predicted)         | 0.089 (11.3)                   | 0.364             | –               |

GPU columns: Tesla T4; CPU columns: 4-core Intel Xeon 2.1 GHz. The
hash-set pipeline is the line table, the token scan, the hash match and
the extraction in one timing; the per-indicator time excludes the line
table (13 ms).

<img src="media/bea5039168bf776668db1c06a1f6253447ecf1d9.png"
style="width:4.64583in;height:2.32292in" />

**Fig. 4.1. Matching rate against the list size on the Tesla T4 and the
Colab host, 1,000,000 lines**

Fig. 4.2 shows where the time of the hash-set pipeline goes. At 1,000
indicators the line table takes 13.3 ms (40 %), the token scan 15.7 ms
(47 %), the hash match 2.7 ms (8 %) and the extraction 2.3 ms (7 %). The
two scan steps read and write a 4-byte flag per corpus byte, about 8
bytes moved per byte of log against the single byte the hash kernel
reads; the hash kernel itself runs at the equivalent of 45 GB/s of
corpus against a device-to-device copy rate of 241 GB/s, bound by the
serial byte walk and the data-dependent probe of every thread rather
than by bandwidth (28 registers per thread, no shared memory, occupancy
100 %, 111 PTX instructions with 15 branches and no atomics). The
limiter of the pipeline is therefore the scan traffic, which does not
depend on the list; that is why the pipeline is flat. Keys in shared
memory do not help (2.2 to 3.1 ms against 1.9 to 2.7 ms from global
memory): the probes are served from L1 and L2 anyway, and even the 512
KB table of 10,000 indicators is 12 % of the 4 MB L2.

The variant without compaction confirms the diagnosis: dropping the
token scan removes 15.7 ms and adds a kernel of 7.3 to 8.2 ms, so the
pipeline falls from 33 to about 20 ms. On this corpus only one byte in
five starts a token, and the divergence of a warp whose lanes walk
tokens of different lengths costs less than the scan it replaces.

<img src="media/4d4a02c0ec569ddfb2df8b9a0bc0220067946dfd.png"
style="width:4.64583in;height:2.32292in" />

**Fig. 4.2. Time of the GPU hash-set pipeline by step against the list
size, 1,000,000 lines**

**4.2. Rate against the corpus size and the transfer**

Table 4.2 and Fig. 4.3 give the corpus-size sweep with a list of 1,000
indicators. On the device the hash-set pipeline runs at 3.3 to 3.6 GB/s
and the variant without compaction at 5.2 to 5.8 GB/s, steady from
125,000 to 4,000,000 lines. The pageable host-to-device copy runs at 4.6
GB/s (11.3 GB/s pinned) and costs 0.7 times the pipeline at 4,000,000
lines, so the rate including the copy is 1.9 to 2.0 GB/s: the copy is
not yet the wall, but it is the next one. The tuned CPU matcher reaches
0.86 to 1.14 GB/s with four tasks on the 4-core host and 0.28 to 0.32
GB/s with two tasks on the Colab host; one task gives 0.27 to 0.31 GB/s
on either machine.

Table 4.2

**Data Rate Against the Corpus Size (list of 1,000 indicators)**

| **Lines** | **MB** | **GPU pipeline, MB/s** | **GPU no compaction, MB/s** | **GPU + copy, MB/s** | **CPU 4 tasks, MB/s** | **CPU 1 task, MB/s** |
|-----------|--------|------------------------|-----------------------------|----------------------|-----------------------|----------------------|
| 125,000   | 14.9   | 3,434                  | 5,237                       | 2,023                | 1,122                 | 288                  |
| 250,000   | 29.8   | 2,333                  | 5,597                       | 1,558                | 859                   | 273                  |
| 500,000   | 59.6   | 3,620                  | 5,659                       | 2,036                | 1,099                 | 305                  |
| 1,000,000 | 119.2  | 3,577                  | 5,806                       | 2,019                | 1,135                 | 295                  |
| 2,000,000 | 238.3  | 3,542                  | 5,793                       | 1,978                | 1,049                 | 290                  |
| 4,000,000 | 476.6  | 3,288                  | 5,760                       | 1,909                | 1,089                 | 283                  |

GPU columns: Tesla T4 (pageable copy at 4.6 GB/s); CPU columns: 4-core
Intel Xeon 2.1 GHz.

<img src="media/680c951dd76352235c97b455210b87db622be1c2.png"
style="width:4.64583in;height:2.32292in" />

**Fig. 4.3. Data rate against the corpus size on the Tesla T4 and the
Colab host, list of 1,000 indicators**

**4.3. CPU tasks**

Table 4.3 and Fig. 4.4 give the task sweep on the 4-core host at
1,000,000 lines and 1,000 indicators: 1.92 times faster with two tasks
and 3.63 times with four, close to linear, since every task scans its
own chunk with no shared state beyond the read-only table. On the Colab
host the second hardware thread of the single core adds 1.7 times at
best, which is why Fig. 4.1 shows that host’s two tasks and Section 5
uses the 4-core numbers.

Table 4.3

**Tuned CPU Matcher Against the Number of Tasks (4-core Intel Xeon 2.1
GHz, 1,000,000 lines, 1,000 indicators)**

| **Tasks** | **Time, s** | **M lines/s** | **MB/s** | **Speed-up over one task** |
|-----------|-------------|---------------|----------|----------------------------|
| 1         | 0.409       | 2.45          | 292      | 1.00                       |
| 2         | 0.213       | 4.70          | 560      | 1.92                       |
| 4         | 0.113       | 8.88          | 1,058    | 3.63                       |

<img src="media/a11b690621d7d5bc23f66453943fb3d0f068fd13.png"
style="width:4.13542in;height:2.07292in" />

**Fig. 4.4. Tuned CPU matcher against the number of tasks on the 4-core
host, 1,000,000 lines, 1,000 indicators**

**4.4. Summary of the comparison**

At 4,000,000 lines and any list size the hash-set pipeline on the device
is 3.0 times the 4-core CPU with four tasks and 11.6 times one core;
including the copy 1.75 times the four tasks and 6.7 times one core; the
variant without compaction on the device is 5.3 times the four tasks.
Against the Colab host’s own CPU (two tasks) the pipeline is 10.4 times
faster on the device and 6.0 times with the copy. One T4 therefore
replaces about seven cores of this class once the transfer is counted,
and about twenty if the logs are already on the device. The
per-indicator kernel and the library route have no place in this
comparison: their cost is a rate divided by the list size.

**5. SECURITY DISCUSSION**

**5.1. Implications for a defender**

The first result is about the method, not the hardware. Any method whose
cost grows with the list is unusable for a real feed: the per-indicator
GPU kernel needs 1.9 s per million lines at 10,000 indicators, the
library route on a core about 14 minutes, 10 GB of logs per day per
core. A list-independent method makes the feed size free: 10,000
indicators at the rate of 10, on the GPU and on the CPU. The algorithm
changes the capacity by three to four orders of magnitude; CPU against
GPU changes it by two to seven times. A SOC should first make sure its
matcher looks tokens up in a set (or runs an automaton for substring
semantics) and only then ask about hardware.

The second result is the sizing rule. With the list-independent method
one core of the 4-core host handles about 290 MB/s, 25 TB of logs per
day; four cores 1.1 GB/s, 94 TB per day; one T4 with the pageable copy
1.9 GB/s, 165 TB per day, and 5.8 GB/s, 500 TB per day, with the logs
already on the device. A site producing 2 TB per day (23 MB/s) is far
below one core; the GPU is needed only above the rate the cores cover,
roughly 1 GB/s for this host, and keeps up to about 2 GB/s if the logs
arrive that fast; otherwise storage or the network, not the matcher, is
the limit. The GPU pays when the logs are on the device for other
analytics (the entropy and matching passes of Project 2 share one corpus
copy) or when one machine must handle several GB/s.

**5.2. Limitations**

The logs are synthetic and every indicator is a whole token; substrings
and regular expressions are out of scope. Cold indicators never hit, so
the hit count is constant, which isolates the cost of the list but not
the cost of hits. The CPU baseline is Julia on a shared 4-core host; a
vectorised C++ matcher would be faster per core and narrow the GPU’s
margin. All GPU numbers come from one Colab session on a Tesla T4, a
2018 inference card with a fraction of a current data-centre GPU’s
bandwidth. The GPU pipeline still carries the line-table scan, needed
only to name the lines of the hits; removing it would add another 13 ms
per million lines to the margin.

**5.3. Ethical and legal notes**

Everything here is self-generated: addresses from the documentation and
benchmarking ranges (RFC 5737, RFC 2544), hostnames under the reserved
.invalid domain (RFC 2606), a corpus from the course generator; nothing
was probed, collected or matched from any real system, network or
person. In production, matching touches personal data: addresses and
hostnames in logs identify people and organisations, so logs and match
results fall under data-protection rules (retention, purpose limitation,
access control), and threat-intelligence feeds carry sharing
restrictions (TLP markings). A faster matcher changes none of that; it
only means the whole retention window can be re-matched when a feed is
updated.

**CONCLUSIONS**

Log indicator matching on a Tesla T4 with a token hash set is flat in
the list size: 30 million lines per second from 10 to 10,000 indicators
with the lecture-7 compaction, 49 million without it, against a
per-indicator kernel that costs 5.9 ms per 32 indicators and a library
route that grows linearly. The limiter of the GPU pipeline is the scan
traffic of the compaction, not the hash table, which is why removing the
token scan gives 1.6 times. A tuned CPU with the same algorithm reaches
1.1 GB/s on four cores; the GPU gives 1.9 GB/s with the host-to-device
copy and 5.8 GB/s on the device, so one T4 replaces about seven cores
once the transfer is counted. For a defender the order of decisions is:
a list-independent algorithm first, which makes the feed size
irrelevant, then hardware only above the rate the available cores cover,
about 1 GB/s for four cores of this class.

**LIST OF REFERENCES**

1\. Lektauers, A., Narigina, M. DE0831 Cybersecurity Solutions in
High-Performance Computing Environments: lecture notes 1–10 and the
research project brief. Riga Technical University, 2026.

2\. Hwu, W.-m. W., Kirk, D. B., El Hajj, I. Programming Massively
Parallel Processors: A Hands-on Approach. 4th ed. Morgan Kaufmann, 2022.

3\. Fowler, G., Noll, L. C., Vo, K.-P., Eastlake, D., Hansen, T. The FNV
Non-Cryptographic Hash Algorithm. IETF Internet-Draft
draft-eastlake-fnv, 2023.

4\. Besard, T., Foket, C., De Sutter, B. Effective Extensible
Programming: Unleashing Julia on GPUs. IEEE Transactions on Parallel and
Distributed Systems, 2019, vol. 30, no. 4, pp. 827–841 (CUDA.jl).

5\. Arkko, J., Cotton, M., Vegoda, L. IPv4 Address Blocks Reserved for
Documentation. RFC 5737, IETF, 2010.

6\. Bradner, S., McQuaid, J. Benchmarking Methodology for Network
Interconnect Devices. RFC 2544, IETF, 1999.

7\. Eastlake, D., Panitz, A. Reserved Top Level DNS Names. RFC 2606,
IETF, 1999.

8\. NVIDIA. CUDA C++ Programming Guide, release 13.0. NVIDIA
Corporation, 2025.

9\. NVIDIA. NVIDIA T4 Tensor Core GPU datasheet. NVIDIA Corporation,
2019.

**APPENDIX 1. REPRODUCIBILITY**

Hardware: Google Colab, Tesla T4 (40 SMs, 14.56 GiB, compute capability
7.5, driver 580.82 for CUDA 13.3), host Intel Xeon 2.0 GHz with two
hardware threads; CPU task sweeps on an Intel Xeon 2.1 GHz with four
hardware threads and 15 GB of RAM. Software: Julia 1.12.7, CUDA.jl
6.5.1, CairoMakie 0.15.17; Project.toml and Manifest.toml fix every
version.

Execution, from the project folder DE0831_RP: julia --project=. -e
'using Pkg; Pkg.instantiate()' once; julia -t auto --project=.
src/rp_run.jl for the validation, both sweeps, the results and the plots
(the generator runs from the student ID when the data is missing, about
40 minutes on Colab); julia --project=. test/runtests.jl for the
validation alone; RP_CPU_ONLY=1 julia -t 4 --project=. src/rp_run.jl for
the CPU sweeps on a machine without a GPU. Environment variables select
the list sizes, corpus sizes, task counts and repetitions. The notebook
DE0831_RP_colab.ipynb reproduces the GPU runs end to end. Outputs:
results/benchmarks.md, results/analysis.md, the CSVs of both sweeps, the
PTX of the hash-match kernel and the four plots; every number in this
report is copied from them.
