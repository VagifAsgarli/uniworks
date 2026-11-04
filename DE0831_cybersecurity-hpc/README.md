# DE0831 Cybersecurity Solutions in High-Performance Computing Environments

Cybersecurity Solutions in High-Performance Computing Environments (English)(1), 26/27-R

| | |
|---|---|
| Course code | DE0831 |
| Academic year | 2026/27 |
| Faculty | Faculty of Computer Science, Information Technology and Energy, Institute of Information Technology (RTU) |
| Lecturers | Arnis Lektauers, Assoc. Professor, Dr.sc.ing. (arnis.lektauers@rtu.lv); Marta Narigina, Lecturer, M.sc.ing. (marta.narigina@rtu.lv) |

## Description

The study course covers the theoretical and practical principles of high-performance computing
in the context of cybersecurity by using graphics processing hardware and dedicated software. The
study course includes an overview of architecture, computing algorithms, software libraries and
tools of parallel computing platform CUDA based on graphics processors. An in-depth attention is
devoted to the cross-disciplinary application of CUDA in the areas of vulnerability analysis,
parallel data encryption, surveillance data mining, object detection and recognition. Among to the
theoretical knowledge acquisition during the lectures, the laboratory lessons provide
opportunities to obtain practical skills in the development of information technology solutions
with CUDA.

## Materials

`materials/lectures/` (weeks 1–10, 2026), `materials/labs/` (labs 2, 3, 7), `materials/reference/`
(RTU FCSITE formatting and style guidelines for graduation theses 2025; PMPP chapter 20, "More on
CUDA and GPU computing"; an example report, "A comparison of the Sobel filter in C, OpenCV and
CUDA", Gadler 2019); plain text of every file in `materials/text-extracts/`.

| Week | Date | Lecture / lab |
|---|---|---|
| 1 | 31.08 | L1 Introduction to high-performance computing |
| 2 | 07.09 | L2 CPU versus GPU execution: CUDA and Julia; lab 2 array programming on the GPU |
| 3 | 14.09 | L3 GPU architecture: the CUDA execution model; lab 3 hand-written kernels, stencil processing |
| 4 | 21.09 | L4 GPU kernels for security analytics: threads, indexing and bounds |
| 5 | 28.09 | L5 GPU kernels for security analytics: coalescing and data layout |
| 6 | 05.10 | L6 Shared memory and parallel algorithms: tiles, histograms and reduction; research project brief |
| 7 | 12.10 | L7 Prefix sum, kernel timing and cryptography on GPUs: hash functions, password auditing; lab 7 parallel hashing; Project 2 brief |
| 8 | 19.10 | L8 Password storage, ethics and cryptography on GPUs: block and stream ciphers, parallelisable modes |
| 9 | 26.10 | L9 Image processing for surveillance: pixels, convolution and filters |
| 10 | 02.11 | L10 Image and video processing for surveillance: memory, edges, motion and the frame budget |
| 12–13 | | L12 intrusion detection, L13 log mining (not yet delivered) |

## Assignments

| # | Assignment | Due | Status |
|---|---|---|---|
| 1 | [Project 1: GPU Programming Fundamentals in Julia](project-1_gpu-fundamentals-julia/) | 23.10.2026 | **graded 9.75/10**, defence passed 02.11.2026 |
| 2 | [Project 2: Applied Security on GPUs](project-2_applied-security-gpus/) | 27.11.2026 | started; track to confirm (recommendation E) |
| 3 | [Research Project: GPU-Accelerated Cybersecurity](research-project_gpu-accelerated-cybersecurity/) (in pairs, 30 %, the defence is the exam) | report 11.12.2026, defence 14.12.2026 | topic to choose (recommendation 10, log indicator matching) |
