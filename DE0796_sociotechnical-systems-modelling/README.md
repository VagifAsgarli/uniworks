# DE0796 Sociotechnical Systems Modelling

Riga Technical University, Institute of Information Technology, autumn semester 2026/27
("Sociotechnical Systems Modelling (English)(1), 26/27-R" on ORTUS).

| | |
|---|---|
| Lecturer | Prof. Egils Ginters, `egils.ginters@rtu.lv` (all assignments are sent to this address) |
| Classes | Wednesdays 14:30–16:05 (Zunda 10-506) and 16:30–18:05 (Zunda 10-533) |
| Platforms | ORTUS (materials), Zoom, teachsys.com (tests after or during each lecture) |
| Assessment | labs and practical assignments ≤ 50 %, automated exam ≤ 50 %; +0.5 to the final grade if the test average is 80 % or higher |
| Exam admission | **all laboratory works and individual design tasks must be submitted and defended**, otherwise the exam is not allowed (course introduction, slide 6) |
| Rules | plagiarism is strictly prohibited: copy and paste without references leads to exmatriculation; every statement from a source needs a reference (APA 7) |

## Where the student stands (register of 25 November 2026)

[`materials/register/results_2026-11-25.pdf`](materials/register/results_2026-11-25.pdf) is the
lecturer's register. The **yellow** columns are the final marks of the compulsory works; a yellow
cell with 0 is a work that is still owed. Row `251ADM047`:

| Column (date) | What it is | Mark | Needed for the exam |
|---|---|---|---|
| T1 (02.09), T2.1 (09.09), T2.2 (16.09), T3 (30.09), T4 (07.10), T4II (21.10), T5 (11.11) | lecture tests on teachsys.com | 0 or empty | no (bonus only) |
| **PR1 Fin** (23.09) = mean of PR1 (16.09) and PR1 Prez. (23.09) | one-page summary of the assigned topic and its presentation | **0** | **yes** |
| **T4LprimFin** (07.10) | causal loop diagram of the Yellowstone ecosystem, presented | **0** | **yes** |
| **T4LFin** (28.10) = mean of T4L and T4LPrez (T4LTest is a separate test) | STELLA stocks-and-flows model of Yellowstone: protocol, model, presentation with a live demonstration | **0** | **yes** |
| **T5Lfin** (25.11) = mean of T5L and T5Lprez | BPMN2 model of the goal system in ARIS Express: protocol, model, presentation | **0** | **yes** |

How the final marks are formed was read off the rows of other students (for example 68 and 75
give 72; 85 and 95 give 90).

## Assignments

The lecturer accepts the four works late: he asked for them **by 2 December 2026** and allowed them
to be prepared with full AI support (the student's account of the conversation, 26.11.2026). Each
work is sent to `egils.ginters@rtu.lv` and then defended.

| # | Assignment | Original deadline | What is handed in | Status (26.11.2026) |
|---|---|---|---|---|
| PR1 | [Summary design](pr1_summary-design/): one A4 page on "Application of BPMN 2.0 Diagrams in Modelling Cybersecurity Procedures" with APA 7 references, then a presentation | in class 16.09 (summary), 23.09 (presentation) | `VagifAsgarli-PR1.pdf`; presentation | **ready**: summary (PDF) and presentation (12 slides) |
| T4LPrim | [Causal loop diagram of Yellowstone](t4lprim_causal-loop-diagram-yellowstone/): CLD with reinforced and balanced feedbacks, opinion on the stability of the ecosystem | 07.10 | presentation on the lecturer's template | **ready**: CLD and presentation (10 slides) |
| T4L | [System dynamics simulation in STELLA](t4l_system-dynamics-stella/): stocks-and-flows model of Yellowstone with sliders and buttons | 24.10 (e-mail), defence 28.10 | protocol (PDF), model (STM), presentation (PPT/PPTX); the model is run during the defence | model, guide and **drafts** ready; the student builds or opens the model in STELLA and takes the screenshots, then the final files are built |
| T5L | [Conceptual modelling in BPMN2](t5l_conceptual-modelling-bpmn2/): CLD of the goal system of the PR1 topic and its BPMN2 model in ARIS Express | 22.11, 24:00 (e-mail), defence 25.11 | protocol `vagif.asgarli-T5L.pdf`, model (ADF, PDF), presentation (PPT) | CLD, BPMN2 design, guide and **drafts** ready; the diagram must exist in ARIS Express (ADF and PDF), then the final files are built |

What the student still has to do, step by step, is in
[`notes/setup-for-vagif_az.md`](notes/setup-for-vagif_az.md) (Azerbaijani).

The four works build on each other: PR1 defines the topic and the goal system; T4LPrim and T4L
are the Yellowstone exercise (CLD, then stocks and flows); T5L returns to the goal system of
PR1 (CLD, then BPMN2).

## Materials

| Folder | Contents |
|---|---|
| [`materials/lectures/`](materials/lectures/) | T0 course introduction (PPTX); T1 sociotechnical systems fundamentals, T2 modelling and simulation techniques, T3 summarization and concretization of ideas, T4 systems thinking and dynamics simulation, T5 parallelization of work and data flows (BPMN2), as PDF |
| [`materials/register/`](materials/register/) | the lecturer's results register of 25.11.2026 |
| [`materials/text-extracts/`](materials/text-extracts/) | plain text of every lecture, lab deck, template and assignment |
| `<assignment>/materials/` | what the course gives for that assignment: task decks, protocol and presentation templates, the lecturer's ARIS Express demo |

The original decks T1, T2, T3 and T5 carry embedded videos (T2 alone is 1 GB), which is more
than GitHub accepts in one file. The PDFs here were made from copies with the video payloads
removed; the slides themselves are complete. The originals stay in the student's Google Drive
folder. All 20 files were checked for hidden text (white or tiny text, off-slide shapes,
annotations): none found.

## Tools the course requires

| Tool | Used for | Notes |
|---|---|---|
| STELLA (isee systems) | T4L model and its demonstration | the lab deck shows classic STELLA with Map, Model, Interface and Equation layers (version 9; file format STM). The current version, Stella Architect, has a 30-day evaluation and saves STMX; it cannot save STM. Both routes are prepared in the T4L folder |
| ARIS Express 2.4 | T5L BPMN2 model | free download from ariscommunity.com (registration); saves `.adf`, exports PDF. The `.adf` format is closed, so the diagram has to be drawn in ARIS Express itself; the program asks for the user's ARIS Community login at first start, so the student draws it on their own computer |
| MS PowerPoint | every presentation | the lecturer's templates are in the assignment folders |

## Shared tools in this folder

| File | What it does |
|---|---|
| [`tools/cld_draw.py`](tools/cld_draw.py) | draws a Causal Loops Diagram from a JSON description in the notation of the lecture and of the T4LPrim template (blue "+" links, red "−" links, delay marks, R and B loop marks) |
| [`tools/lecturer_deck.py`](tools/lecturer_deck.py) | builds presentations on the lecturer's slide templates (his title slide, heading, footer and slide number are kept) |
| [`tools/lecturer_protocol.py`](tools/lecturer_protocol.py) | fills the lecturer's protocol templates (his lines are kept, the answers are written under them) |
