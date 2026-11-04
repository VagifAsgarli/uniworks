# Research project proposal (for the instructor), topic 10: Log indicator matching

Student: Vagif Asgarli, 251ADM047, working alone (agreed).

**Measurable objective.** Log lines per second of indicator matching on one GPU as the indicator
list grows from 10 to 10,000 entries, against a tuned multithreaded CPU baseline; the data rate
(MB/s and GB/day) at which the GPU exceeds the CPU once the host-to-device transfer is
counted; and the factor that limits each method as the list grows (passes over the corpus,
hash-table size against the L2 cache, warp divergence).

**Data.** The course log corpus from `gen_logs.jl` generated with my student ID (1,000,000
lines, 119 MB; also 125k–4M lines for the data-rate curve).  Indicator lists of 10, 30, 100,
300, 1,000, 3,000 and 10,000 entries: the generator's 20 indicators (with their ground truth)
plus synthetic indicators in the same two forms (addresses from the RFC 2544 benchmarking
range 198.18.0.0/15, DGA-style `.invalid` hostnames) that cannot collide with the corpus, so the
hit set is known exactly for every list size and only the list size changes.  Nothing is
collected from any real system.

**GPU design.** Two matching methods on the GPU, both validated against the ground truth:
(1) a *per-indicator* matcher (the Project 2 kernel: shared-memory tile, prefix filter, one
pass per group of 32 indicators) whose cost grows with the list; (2) a *token hash-set*
matcher: tokens are found with the lecture-7 scan and compaction, one thread per token hashes
its bytes (FNV-1a) and probes an open-addressing table of the indicators, so the cost is one
pass whatever the list size.  Memory strategy: coalesced byte access, the table in shared memory
while it fits and in global memory (L2) beyond that, which is the factor to measure.

**Baseline.** A tuned CPU implementation of the same token hash-set method, multithreaded with
Julia threads (measured on 1, 2 and 4 threads), plus the library route (`occursin` per
indicator) for small lists.

**Measurement.** Lecture-7 method: warm-up, `CUDA.@elapsed` per launch, 100 samples, mean and
min–max; every step timed directly; CPU wall-clock best of 3.  Tables and scaling plots of
lines/s against list size and against corpus size; GPU vs CPU crossover with the transfer.

**Security conclusion.** For a SOC with N indicators and V GB of logs per day: the cores or
GPUs needed, where the limit sits, and when a list-independent method is required.

**Deliverables.** Julia code with `Project.toml`/`Manifest.toml`, a script that reproduces
every run on Google Colab (Tesla T4; GPU model and session limits stated), the 6–10 page
report (11.12) and the 10-minute presentation with a live run (14.12).
