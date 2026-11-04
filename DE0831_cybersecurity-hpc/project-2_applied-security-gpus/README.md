# Project 2: Applied Security on GPUs

Course: [DE0831 Cybersecurity Solutions in High-Performance Computing Environments](../README.md)

| | |
|---|---|
| Issued | week 7, 12.10.2026 |
| Due | Friday of week 13, **27.11.2026** |
| Weight | 25 % of the final grade (implementation half: laboratory work; analysis half: individual study) |
| Defence | lab session of week 14 |
| Submission | one archive `DE0831_P2_Asgarli_251ADM047.zip` via ORTUS, same structure as Project 1 (README, Project.toml, Manifest.toml, src/, results/, test/); a Colab notebook may replace the project files |
| Brief | [`materials/project-2_brief.pdf`](materials/project-2_brief.pdf) ([text](materials/project-2_brief.txt)); data generators for tracks C–E in [`materials/data_generators/`](materials/data_generators/) |
| Track | **to be confirmed** (recommendation: E, full route; see below) |

## The task

One of five tracks, all with the same weight and grading. Deliverable: a GPU implementation
validated against a reference, a measurement study ending in one headline number, and a
defensive conclusion backed by the measurement.

| Track | Headline number | Input | Sources |
|---|---|---|---|
| A Password auditing (SHA-256 kernel, dictionary + ≥ 3 mangling rules) | hash rate (H/s) and the storage policy that follows | `hashes_<ID>.txt` **from the instructors** + shared `wordlist.txt` | lectures 7, 8; lab 7 |
| B Data encryption (AES-128-CTR or ChaCha20 kernel) | cipher throughput (GB/s, 1 MB–1 GB) and the share of host–device transfer | key and nonce derived from the ID (rule in lecture 8) | lecture 8 |
| C Surveillance imaging (Float32 conversion, separable Gaussian blur, Sobel, frame differencing; shared-memory tiles with halos) | simultaneous 1080p streams at 25 fps per GPU, and the limiting stage | `gen_footage.jl` (60 frames 1920×1080, 124 MB) + `motion_truth_<ID>.csv` | lectures 9, 10; lab 10 |
| D Intrusion detection (dense NN, own forward/backward, gradient check) | inference throughput (flows/s) and what the false-positive rate costs per day | `gen_ids_dataset.jl` (300k train / 75k test, 12 features, 5 classes, 1.2 % attacks) | lecture 12; lab 12 |
| E Log mining (multi-pattern matcher with scan + compaction; token entropy flagging reusing the Project 1 scanner) | lines/s and MB/s, and the daily log volume at which one CPU core no longer keeps up and one GPU does | `gen_logs.jl` (1M lines, 119 MB) + `indicators_<ID>.txt` (12 IPs, 8 domains), `truth_<ID>.csv` (894 lines), `entropy_truth_<ID>.csv` (243 payloads) | lecture 7 (scan, compaction); lecture 13, lab 13 |

Basic route caps the implementation half at 8/10 (E: one indicator at a time with array
operations and `findall`); full route up to 10/10 (E: one multi-pattern kernel, matched lines
extracted with scan and compaction).

Requirements for all tracks: header block (name, ID, derived parameters, device, compute
capability); a single-threaded CPU baseline of the same computation; the Project 1 warm-up +
`CUDA.@elapsed` harness over a range of sizes (≥ 4 input sizes for C–E); documented, coalesced
memory layout; roofline or, for integer workloads (A, B, E), an integer-operation count or a
bandwidth analysis; `Project.toml`, `Manifest.toml`, README with device, track, route, declared
AI use, how to run.

Analysis (~1 page): headline number with its measurement and assumptions; limiter with evidence
(achieved bandwidth, occupancy, `CUDA.registers`, or Nsight); scaling with input size and the
transfer wall (kernel time vs host–device time; "no crossover observed" is a valid result); CPU
comparison against the single-threaded baseline; the defensive conclusion (C–E: a sizing
decision, e.g. "one GPU covers N streams, so the site needs M GPUs").

Grading: implementation 4 (complete and correct vs reference and ground truth) + 2 (end-to-end
run on the individualised input with a working CPU baseline) + 2 (GPU technique fits: coalesced
layout, boundary handling, no races) + 2 (individualisation, header, code quality, reproducible
environment); analysis 2 (methodology) + 3 (headline number across the range, assumptions) + 3
(roofline, limiter with evidence, scaling, transfer wall) + 2 (defensive conclusion with the
arithmetic).

Authorised use: only the instructor-supplied hash set (A); only the handout generators (C–E); no
real footage, traffic or logs; nothing leaves the course. Reference material: FIPS 180-4, FIPS
197, NIST SP 800-38A, RFC 8439, OWASP Password Storage Cheat Sheet.

## Track choice

Recommendation: **Track E, full route.**

- It continues Project 1: the brief itself says to reuse the entropy scanner for the token
  flagging, and the measurement harness carries over.
- Everything needed is in hand now: the generator, the indicator set and two exact ground-truth
  files (the full match set, not a sample), so correctness is binary and checkable on a CPU.
  Tracks A and B wait for instructor-provided input (hash file; key/nonce rule).
- The GPU technique is well defined and gradeable: one multi-pattern matching kernel over the
  corpus bytes, line boundaries and matched lines extracted with scan and compaction (lecture 7,
  already delivered), coalesced byte access as in Project 1.
- The headline number and the defensive conclusion are clean: lines/s and MB/s across ≥ 4 corpus
  sizes, the CPU-core vs GPU crossover in daily log volume, and a sizing decision.
- Risk to note: lecture 13 / lab 13 are delivered close to the deadline; the design does not
  depend on them.

Alternative if preferred: **Track C** (imaging): all its lectures are already delivered, the tiled
stencil kernels are classic GPU work, and the capacity number (streams per GPU) is intuitive.

Generated with the student ID (hashed with SHA-256 by the generators), sizes for information:
E: `corpus_251ADM047.log` 1,000,000 lines, 119.2 MB, 894 indicator lines (0.0894 %), 243 encoded
payloads; D: 300,000 / 75,000 rows, 1.19 % / 1.21 % attacks; C: 60 frames, 124.4 MB, 3 movers.
The generated data is not committed (it is reproducible from the ID); the generators are.

## Lessons from Project 1 applied here

From the Project 1 feedback (9.75/10):

1. Every number in the analysis is measured directly, never derived by subtraction; a figure that
   violates a physical bound is a measurement error, not a finding.
2. Every piece of "evidence" is produced by the submitted scripts (e.g. the PTX dump written to
   `results/` by the script itself), so the grader can regenerate it.
3. Comments are checked against the device facts (grid size ≠ resident blocks).
4. Plots are made in Julia only (headless-capable backend); the Colab notebook does nothing the
   submission does not.

## Status

- [x] Brief read and extracted; scanned for hidden text (clean); generators stored; data generated
      for the ID to check sizes.
- [x] Lectures 1–10 and labs 2, 3, 7 collected into `../materials/` (lecture 7 covers prefix sum
      and timing; lectures 12–13 not yet delivered).
- [ ] Track confirmed (aligned with the research-project topic: track E ↔ topic 10).
- [ ] Design note (`notes/design.md`): memory layout, kernels, validation plan, measurement plan.
- [ ] Implementation + CPU baseline + tests, checked on the CPU emulator and by PTX compilation.
- [ ] Colab T4 run; benchmarks, roofline, analysis, plots (Julia).
- [ ] Archive built; upload by 27.11.2026; defence week 14.
