# PR1: Summary design

Course: [DE0796 Sociotechnical Systems Modelling](../README.md)

| | |
|---|---|
| Task | [`materials/pr1_assignment.pdf`](materials/pr1_assignment.pdf): a summary of no more than one A4 page with a properly formatted reference list, on the lecturer's template; then a presentation |
| Topic (student 251ADM047) | **Application of BPMN 2.0 Diagrams in Modelling Cybersecurity Procedures** ([`materials/pr1_topics.pdf`](materials/pr1_topics.pdf)) |
| Original deadlines | summary: in class on 16 September 2026, by 18:05; presentation: 23 September 2026 |
| New deadline | **2 December 2026**, agreed with the lecturer: the work is late, and he allowed it to be completed with full AI support |
| Register columns | PR1 (summary), PR1 Prez. (presentation); **PR1 Fin** is their mean and is compulsory for exam admission |
| Submission | PDF named `FirstNameLastName-PR1.pdf`, i.e. `VagifAsgarli-PR1.pdf`, by e-mail to `egils.ginters@rtu.lv` |
| Mode | individual |

## Status

- [x] Sources found and every figure checked in the source text (15 references)
- [x] Summary written on the lecturer's template: one A4 page, references and AI note on page 2
- [x] `VagifAsgarli-PR1.pdf` built
- [x] Presentation built (12 slides, lecturer's slide design, speaker notes)
- [x] Explanation and defence questions for the student ([`notes/explanation_az.md`](notes/explanation_az.md))
- [ ] Student reads the summary and the explanation
- [ ] `VagifAsgarli-PR1.pdf` sent to `egils.ginters@rtu.lv` (by 2 December 2026)
- [ ] Presentation given (date to be agreed with the lecturer)

## What the lecturer requires

From [`materials/pr1_assignment.pdf`](materials/pr1_assignment.pdf):

| Requirement | How it is met |
|---|---|
| No more than one A4 page, together with a properly formatted list of references | the summary text fills page 1; the reference list follows on page 2 (see the assumption below) |
| Structure: "Summary", first and last name, date, title of the topic, "Keywords." with at least three keywords | as in the template; five keywords |
| Continuous text without subheadings, except for Keywords | five paragraphs, no subheadings |
| Paragraph 1: relevance at global, European and Latvian level with quantitative data and references | IBM (global cost of a breach), ENISA and NIS2 (Europe), National Cybersecurity Law and CERT.LV (Latvia) |
| Paragraph 2: the most significant problem with data; at least three specific existing solutions with facts, principles, advantages and limitations | prose playbooks (two empirical studies); NIST SP 800-61r3, CACAO 2.0, BPMN 2.0 with SecBPMN |
| Paragraph 3: proposed approach, aim, at least four tasks, methods | standard BPMN 2.0 elements only; aim: CyberFlow; five tasks; four methods |
| Paragraph 4: expected qualitative and quantitative results, potential users, their benefits | three validated models, modelling rules, a 20% target; CISOs, security operations teams, auditors, the CSIRT |
| Paragraph 5: whether the problem is solved completely, limitations, further research | not completely; three limitations; four directions |
| Every fact supported by an in-text citation; citations and reference list in APA 7 | every figure cited; 15 references in APA 7 |
| "Note. Generative AI tools were used for information retrieval and formatting the reference list: ____" | filled in truthfully: Claude (Anthropic), including the drafting of the text |
| PDF named `FirstNameLastName-PR1.pdf`, sent to `egils.ginters@rtu.lv` | `outputs/submission/VagifAsgarli-PR1.pdf` |

**Assumption.** "No more than one A4 page together with a properly formatted list of references" is
read as: the summary itself is at most one page, and the reference list comes with it on the
following page. With 15 APA 7 references the list alone takes most of a page, and the lecturer's
own one-page example ([`materials/apa7_one-page-example.pdf`](materials/apa7_one-page-example.pdf))
is a guide to the reference format. If the lecturer wants summary and references on a single page,
the text and the list have to be shortened.

**Presentation.** The course materials give no template, time limit, number of slides or file name
for the PR1 presentation (checked: the assignment, the topic list, the course introduction and the
T3 lecture). The deck therefore reuses the lecturer's own slide design from the T5L presentation
template (title slide with the RTU logo and faculty lines, red heading with a line, "RTU 2026"
footer, slide number) and follows the five paragraphs of the summary with the same facts and the
same references.

## The goal system

The summary proposes **CyberFlow**: a BPMN 2.0-based method and model repository for the
incident-handling procedures of a medium-sized Latvian organisation subject to NIS2. It is the goal
system that [T5L](../t5l_conceptual-modelling-bpmn2/) continues with (its causal loops diagram and
its BPMN2 model in ARIS Express).

## Layout

```
pr1_summary-design/
├── README.md
├── materials/                     the assignment with the template, the topic list, the APA 7 example
├── notes/
│   └── explanation_az.md          what each paragraph says, the terms, where each figure comes from,
│                                  a speaking plan for the slides, likely questions (in Azerbaijani)
├── tools/
│   ├── build_pr1.py               builds the summary (DOCX) from the text and the reference list
│   └── build_pr1_presentation.py  builds the presentation on the lecturer's slide design
└── outputs/
    ├── preview/                   PDF copy of the presentation, for reading without PowerPoint
    └── submission/                the files handed in:
        ├── VagifAsgarli-PR1.pdf                 the summary (sent by e-mail), with its DOCX source
        ├── VagifAsgarli-PR1.docx
        └── VagifAsgarli-PR1-presentation.pptx   the presentation
```

## How to rebuild

Both scripts need Python with `python-docx` and `python-pptx`; LibreOffice converts to PDF.

```
python tools/build_pr1.py outputs/submission/VagifAsgarli-PR1.docx
soffice --headless --convert-to pdf --outdir outputs/submission outputs/submission/VagifAsgarli-PR1.docx

python tools/build_pr1_presentation.py          # writes outputs/submission/VagifAsgarli-PR1-presentation.pptx
soffice --headless --convert-to pdf --outdir outputs/preview outputs/submission/VagifAsgarli-PR1-presentation.pptx
```

The date printed in the summary is set in `tools/build_pr1.py` (`DATE`, now 30 November 2026);
change it if the summary is sent on another day. After a rebuild check that the five paragraphs
still end on page 1.

## What to send

`outputs/submission/VagifAsgarli-PR1.pdf` to `egils.ginters@rtu.lv` by 2 December 2026. Attach the
presentation as well, or bring it to the defence, as the lecturer prefers.
