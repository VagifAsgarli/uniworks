# Research Project: GPU-Accelerated Cybersecurity

Course: [DE0831 Cybersecurity Solutions in High-Performance Computing Environments](../README.md)

| | |
|---|---|
| Brief | [`materials/research-project_brief.pdf`](materials/research-project_brief.pdf) ([text](materials/research-project_brief.txt)), issued 05.10.2026 (week 6) |
| Mode | **in pairs** (alone by agreement) |
| Topic | one of 11 topics, first come first served, chosen in the ORTUS choice activity "Choosing a Research Project Topic" (closes **7.12.2026, 14:30**); objective, baseline and data **agreed with an instructor** (was planned for week 6) |
| Report due | **Friday 11.12.2026** (week 15), report and code via ORTUS |
| Presentation | **14.12.2026** (week 16): 10 min + 5 min questions, **live demonstration** (own device or Colab; a recording is not accepted); both sessions of week 16 must be attended |
| Weight | **30 % of the final grade: the project defence is the exam.** Graded only at the defence, as a whole; each member of a pair is graded individually |

## What it is

A **measurable performance study** with an objective beyond "implement it on the GPU", e.g.
*"Determine the data rate at which GPU log mining exceeds a tuned multicore CPU baseline and
identify the factors that limit throughput as the input grows."*

Deliverables: a working GPU implementation (own device or Colab), a written report of 6–10
pages (excluding title page, contents, references, appendices), a 10-minute presentation with a
live demo, reproducible code with benchmarks.

Requirements: runs reproducibly on a stated GPU within one session's limits; a baseline (tuned
CPU implementation, a library, or an unoptimised GPU version); a measurement (throughput,
scaling, or a cost/accuracy curve) with the lecture-7 timing method (warm-up, `CUDA.@elapsed`,
repeated samples); a defensive or analytical conclusion for a real security decision;
`Project.toml`, `Manifest.toml`, a script or notebook that reproduces the runs, a README.

Report sections: 1 problem and measurable objective; 2 approach (GPU design, memory strategy,
decomposition); 3 baseline and methodology; 4 results (tables, scaling plots); 5 security
discussion (implications, limitations, ethical/legal notes); 6 reproducibility appendix.

Grading (10): technical implementation 3; measurement and analysis (baseline, methodology,
scaling) 3; security relevance and conclusion 1; report quality and reproducibility 1;
presentation, demonstration and answers at the defence 2. "A small, well-measured result is
preferable to an ambitious implementation with no baseline."

Authorised use: only self-generated or instructor-provided data, only own devices or own Colab
session; no probing or collecting from any external system, network or person.

## The 11 topics

| # | Topic | Measurable objective | Taught in | ORTUS status (4.11) |
|---|---|---|---|---|
| 1 | Password hashing cost | guesses/s on GPU and CPU for salted hashes; the iteration count that brings the GPU rate below a stated target | L7, L8, lab 7 | open |
| 2 | Password policy strength | time to try every password of a given length and character set on one GPU, ≥ 4 policies | L7 | **full** |
| 3 | Bulk encryption | AES-CTR or ChaCha20 throughput GPU vs CPU; file size at which the GPU wins once transfers are counted | L8 | open |
| 4 | Encrypted-file detection | byte-entropy scanner (ransomware indicator): throughput and share of files classified correctly as the block size changes | L6, Project 1 | open |
| 5 | File integrity checking | hashing many files on GPU and CPU; the batch size at which the GPU wins | L7 | open |
| 6 | Surveillance edge detection | 720p and 1080p streams processed in real time by Sobel + motion detection | L9–10, lab 10 | **full** |
| 7 | Filter size and frame rate | frame rate as the convolution filter grows; largest filter within the frame budget | L10 | open |
| 8 | IDS training speed | training time of a small NN on the IDS dataset, GPU vs CPU, at equal accuracy | L12, lab 12 | open |
| 9 | IDS precision | inference throughput gained by Float16 over Float32 and the accuracy it costs | L12 | open |
| 10 | Log indicator matching | log lines per second as the number of indicators grows from 10 to 10,000 | L13, lab 13 | open |
| 11 | Scan and brute-force detection | per-address event counting on the log corpus: events/s, GPU vs CPU | L6, L13 | open |
| — | Own topic (by agreement) | same shape: one measurable objective, one baseline, one security conclusion | | |

Topics 6–11 use the course datasets (footage, IDS records, log corpus: the Project 2 generators).

## Topic choice

Recommendation: **Topic 10, Log indicator matching**, together with **Project 2 track E**.

- One codebase serves both deliverables: Project 2 builds the multi-pattern matcher for 20
  indicators over the 1M-line corpus; the research project turns it into a study of how the
  rate (lines/s) changes as the indicator set grows from 10 to 10,000, which is exactly where
  the algorithm matters: a per-indicator scan costs O(lines × indicators), a tokenised hash-set
  lookup (or an Aho–Corasick automaton) costs O(bytes) whatever the indicator count.
- Baseline: a tuned multithreaded CPU matcher (and the per-indicator GPU array version as the
  "unoptimised GPU" baseline); data: `gen_logs.jl` plus indicator sets of 10, 100, 1,000,
  10,000 generated from the same documentation address ranges with ground truth.
- Conclusion with arithmetic: for a SOC with N indicators and X GB of logs per day, how many
  CPU cores or GPUs keep up, and where the limit sits (bandwidth, hash probes, divergence).
- Knowing one problem deeply is what the defence (the exam, graded per person) rewards.

Alternative: **Topic 4, Encrypted-file detection**, which reuses the Project 1 entropy scanner
(10/10) almost directly; the study is a cost/accuracy curve over block sizes. Lowest risk, but
less new work to show, and it overlaps with Project 2 track E's entropy flagging.

Topic 5 (file integrity checking) fits Project 2 track A (SHA-256 kernel), not track E.

## Status

- [x] Brief, lectures 1–10, labs 2, 3, 7 and the reference documents collected and extracted
      (`../materials/`); scanned for hidden text: clean.
- [x] Working alone, by agreement with the instructor.
- [x] Topic 10 ("Log indicator matching") and working alone agreed with the instructor in person;
      `notes/proposal.md` keeps the objective, baseline and data as a one-page statement for the
      report (not sent).  Still to check: the ORTUS choice activity shows "Log indicator
      matching" (not "IDS training speed").
- [x] Design (`notes/design.md`): data (course corpus + indicator lists of 10–10,000 built from
      the seed), four methods (GPU hash-set, GPU per-indicator, tuned multithreaded CPU,
      `occursin`), measurement matrix, expected results, validation.
- [x] Code (`DE0831_RP/`): kernels, CPU matcher, validation against the ground truth for every
      list size, both sweeps, results/analysis generators, plots, tests, README, Colab notebook.
- [ ] Emulator and PTX checks; Colab T4 run; CPU-only run on the 4-core machine.
- [ ] Report (6–10 pages, RTU format) and code by 11.12; presentation with live demo, speaker
      notes and Q&A, 14.12.

## Layout

```
research-project_gpu-accelerated-cybersecurity/
├── README.md        this file
├── materials/       the brief (+ text extract)
├── notes/           proposal, design and research notes
├── DE0831_RP/       the project (code, tests, results; data/ is regenerated from the ID)
├── tools/           Colab notebook and checks without a GPU
└── outputs/         runs, report, slides, feedback
```

Course materials shared with the other assignments (lectures, labs, reference documents such as
the RTU FCSITE thesis formatting guidelines, PMPP chapter 20 and an example Sobel-filter report)
are in [`../materials/`](../materials/).
