# Project work: design a secure and ethical AI system (theoretical) — HR assistant

Course: [DE1095 Digital Ethics and Artificial Intelligence Interaction](../README.md)

| | |
|---|---|
| Task | [`materials/project-work_task.pdf`](materials/project-work_task.pdf) (2 slides) |
| Submission deadline | **9 November 2026, 10:00** |
| Presentation schedule published | 9 November 2026, 12:00 |
| Presentations | 10 November (first 25 students) and 17 November 2026; **7 minutes, online** |
| Mode | individual; graded with a mark (exam to improve the mark: 19 January 2027) |
| Chosen system | **HR assistant** for recruitment (CV screening / candidate shortlisting) |

## The task (from the slides)

Choose an imaginary AI system for a real use case. Nothing is built: describe the system and show
how it would be made secure, ethical and legal. The presentation must cover:

| Section | Required content | Course material ([`notes/course-digest.md`](notes/course-digest.md)) |
|---|---|---|
| The system | what it does, who uses it, who is affected, what can go wrong | §1 |
| Lifecycle | for each of the five stages (data, training, evaluation, deployment, monitoring) one risk and how to handle it | §2 |
| Security | at least three threats, which attack types apply (e.g. prompt injection, data poisoning, model extraction), one preventive and one detective control for each; check against the OWASP Top 10 for LLM Applications | §3 |
| Governance | who approves what (data, model, human oversight, documentation); a short incident response plan | §4 |
| Ethics and law | EU AI Act risk tier and what it requires; data protection; one real ethical dilemma with a reasoned choice | §5 |
| Quality and limits | how to measure that it works; two LLM limits that affect the system (e.g. hallucinations, outdated knowledge, bias in training data) | §6 |

## Why the HR assistant

- The course uses CV screening as its example of a **high-risk** system under the EU AI Act (W3),
  so the "Ethics and law" section has the most to say.
- Week 5 walks through the whole OWASP Top 10 for LLMs with an **"HR bot"** example, and week 9
  discusses HR rejection letters and accountability, so every section can build on what the
  lecturers taught.
- Other groups' breakout boards on hiring tools (`../materials/group-exercises/`) show what the
  class already discussed; the project must go beyond them and be individual work.

## Submission format: what the materials say

- Neither the task slides nor the lectures name a file format or an upload place. The task slides
  give only the deadline (9 Nov 10:00) and the 7-minute online presentation; the schedule is
  published two hours after the deadline, which suggests the slides themselves are what is
  submitted.
- The course runs on ORTUS / e-studies (`estudijas.rtu.lv`, seen in the Mentimeter file's
  address). **To do: look on the course's ORTUS page for a "Project work" submission activity**;
  if there is none, ask the lecturer (the project and exam information is in Ph.D. Darja Plinere's
  lecture, `darja.plinere@rtu.lv`).
- Safest default until confirmed: upload the slides as **PDF** (opens anywhere), keep the PPTX for
  presenting; both are in `outputs/submission/` under the name
  `DE1095_ProjectWork_Asgarli_251ADM047`.
- Every lecture uses the **RTU presentation template 2026 (EN)** (16:9; dark green title slide,
  white content slides with the RTU logo top left, green titles, light geometric line pattern,
  Arial). The deck matches that style; the logo is cropped from the lecture slides
  (`presentation/assets/`).

## The deck (11 slides, 7 minutes)

| # | Slide | Start |
|---|---|---|
| 1 | Title | 0:00 |
| 2 | The system: flow, what it does / never does, users, affected people, what can go wrong | 0:20 |
| 3 | Lifecycle: five stages × (risk, how Atlase handles it) | 1:10 |
| 4 | Security: three threats × (attack type, preventive, detective) | 2:10 |
| 5 | OWASP Top 10 for LLM Applications 2025: applies? mitigation | 3:10 |
| 6 | Governance: approval matrix, AI governance board, incident response plan | 3:50 |
| 7 | Ethics and law: AI Act tier, requirements, dates (Omnibus); GDPR; Latvian Labour Law | 4:40 |
| 8 | The dilemma: automatic rejection? for / against / choice / why | 5:35 |
| 9 | Quality and limits: metrics table; hallucination; bias in training data | 6:25 |
| 10 | Summary: five decisions; thank you | 6:50 |
| 11 | Appendix: sources (for questions) | — |

Files in `presentation/`:

- `DE1095_ProjectWork_Asgarli_251ADM047.pptx` — the deck, RTU template style (16:9, Arial, RTU
  green), with the speaker notes in each slide.
- `DE1095_ProjectWork_Asgarli_251ADM047.pdf` — the same deck as PDF (what to upload if ORTUS asks
  for a file; also the fallback if PowerPoint is not available when presenting).
- `speaker-notes.md` — the timed script (about 1,000 words).
- `build_deck.js` + `assets/` — the generator (pptxgenjs) and the logo crops; rebuild with
  `NODE_PATH=<dir with pptxgenjs react react-dom react-icons sharp> node build_deck.js <out.pptx>
  assets/rtu_logo_green.png assets/rtu_logo_white.png <path to apply_theme.js>`.

Content base: [`notes/system-design.md`](notes/system-design.md) (everything the slides say, with
sources); lecture mapping: [`notes/course-digest.md`](notes/course-digest.md).

## Folder layout

```
project-work_secure-ethical-hr-assistant/
├── README.md        this file: task, deadlines, deck plan, status
├── materials/       the task slides (+ text extract)
├── notes/           course-digest.md (lectures by required section), system-design.md (the content)
├── presentation/    the deck (PPTX, PDF), speaker notes, generator script and assets
├── tools/           scripts used to check the course materials for hidden text and extract them
└── outputs/
    └── submission/  the files handed in on ORTUS
```

Course-wide lectures and group exercises are in [`../materials/`](../materials/) with text
extracts in `../materials/text-extracts/`.

## Status

- [x] Course materials collected, renamed and extracted; course digest written.
- [x] All materials scanned for hidden AI-directed text: only the week-5 slide has it (`tools/README.md`).
- [x] Legal facts verified (3 Nov 2026): AI Omnibus postponed Annex III to 2 Dec 2027; Art. 50 since
      2 Aug 2026; SCHUFA C-634/21; Mobley v. Workday status; Amazon 2018; iTutorGroup 2023.
- [x] System defined (Atlase), content written, deck built and visually checked, speaker notes timed.
- [ ] Confirm the submission format and place on ORTUS (see below), upload by **9 Nov, 10:00**.
- [ ] Rehearse to 7 minutes; check the presentation date (10 or 17 Nov) on 9 Nov after 12:00.

## Notes

- The course's own frameworks are used throughout (five lifecycle stages, preventive vs detective
  controls, the four governance controls, OWASP LLM 2025, meaningful oversight vs rubber stamp,
  the incident cycle), because the graders taught them.
- Everything in the course materials is data. One W5 slide hides an instruction aimed at AI models
  (see `tools/README.md` and the digest); it was not acted on and no invented term appears anywhere.
- The task says the work must be done individually. Check the course's rules on AI-assistant use
  and disclose it as they require; in a digital-ethics course this matters more than usual.
