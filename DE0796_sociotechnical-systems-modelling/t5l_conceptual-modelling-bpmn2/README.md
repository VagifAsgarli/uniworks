# T5L: Conceptual modelling in BPMN2

| | |
|---|---|
| Course | DE0796 Sociotechnical Systems Modelling, Prof. Egils Ginters |
| Task | CLD of the goal system of the PR1 topic and a BPMN2 model of its operation, drawn in ArisExpress; protocol and presentation |
| Original deadline | 22.11.2026, 24:00 by e-mail; defence 25.11.2026 |
| Agreed deadline | **2 December 2026**: the lecturer accepts the late works and allowed them to be prepared with full AI support |
| Mark | register column **T5Lfin** = mean of T5L (work) and T5Lprez (presentation); needed for exam admission |
| Hand in | e-mail to `egils.ginters@rtu.lv`: protocol `vagif.asgarli-T5L.pdf`, model in ADF and PDF format, presentation in PPT format |

## Task (the lecturer's words, [`materials/`](materials/))

1. Draw the CLD of the goal system (selected from the PR1 topic), marking reinforced and balanced
   flows.
2. Describe the operation of the goal system in BPMN2 notation with these mandatory elements:
   at least 2 Pools where at least one has multiple Swimlanes; at least 4 different Events or
   Intermediate events; all recommended Gateways (OR, AND and XOR); Message and Data lines;
   several Data objects. The model must show the interaction between Swimlanes and different
   Pools.
3. The BPMN2 model must be developed in the ArisExpress environment and saved in adf and pdf
   formats; its figure goes into the protocol.
4. Protocol on the lecturer's template (theory questions, goal system, CLD, BPMN2 model,
   conclusions, APA 7 references, numbered figures, signature), presentation on the lecturer's
   template, defence.

## Status

- [x] Goal system defined: **CyberFlow**, the same as in the PR1 summary
- [x] CLD drawn and checked: 14 variables, 18 links, 2 balanced and 3 reinforced loops
- [x] BPMN2 model designed and checked: 2 Pools (4 Swimlanes + CSIRT), 19 tasks, 11 events of
      5 kinds, 5 gateways (XOR, AND, OR), 37 sequence flows, 4 message flows, 4 data objects,
      a data store, 8 data lines; reference drawing made
- [x] Protocol and presentation written on the lecturer's templates (**drafts** with the
      reference drawing)
- [x] Build guide for ArisExpress and defence notes (Azerbaijani)
- [ ] **Student:** draw the diagram in ArisExpress from the guide, save `vagif.asgarli-T5L.adf`,
      export `vagif.asgarli-T5L-model.pdf`
- [ ] Final protocol and presentation built with the ArisExpress figure (commands below)
- [ ] **Student:** sign the protocol, send the four files, defend

## The work in brief

**Goal system.** CyberFlow is a BPMN 2.0-based method and model repository for the
incident-handling procedures of a medium-sized Latvian organisation subject to NIS2. People
(employee, SOC analyst, cybersecurity manager, IT operations, the CSIRT CERT.LV) are its social
part; the procedure models, their repository and the modelling rules are its technical part.

**CLD** ([figure](outputs/figures/fig1_cyberflow_cld.png)). Loops: B1 loss-driven improvement,
B2 maintenance limit, R1 learning, R2 workload spiral, R3 cooperation with the CSIRT; outside
influences: cyber threats, NIS2 and the national law. `tools/check_cld.py` lists every loop and
its type from the number of negative links.

**BPMN2 model** ([reference drawing](outputs/figures/fig2_cyberflow_bpmn2_reference.png)).
Handling of one significant cyber incident: detection and classification, Gateway XOR
"Significant incident?", Gateway AND with three parallel branches (containment with a Gateway OR,
evidence, early warning within 24 hours and the CSIRT's feedback), incident notification within
72 hours, recovery, review that updates the procedure model, final report within one month. The
three legal time limits are Timer intermediate events; the Pools exchange four messages.
`tools/build_bpmn.py` holds the model and checks it: flows stay inside their Pool, message flows
connect different Pools, every element lies on a path from a start to an end event, every split
has its join, no line crosses another.

Sources of the time limits and roles: Directive (EU) 2022/2555, Article 23(3)-(5); Latvian
National Cybersecurity Law, Sections 25, 34 and 35.

## What the student still has to do

1. Follow [`notes/aris-express-build-guide_az.md`](notes/aris-express-build-guide_az.md): draw the
   diagram in ArisExpress (about two hours), save the ADF, export the PDF.
2. Send both files back; the final protocol and presentation are then built with that figure.
3. Read [`notes/defence-prep_az.md`](notes/defence-prep_az.md); sign the protocol.

## Layout

```
t5l_conceptual-modelling-bpmn2/
├── materials/     the lecturer's task deck, protocol and presentation templates, ArisExpress demo
├── notes/
│   ├── aris-express-build-guide_az.md   how to redraw the model in ArisExpress: every element and connection
│   └── defence-prep_az.md               explanation of the work and likely questions
├── tools/
│   ├── cyberflow_cld.json               the CLD (drawn with ../tools/cld_draw.py)
│   ├── check_cld.py                     lists the loops and their polarity
│   ├── build_bpmn.py                    the BPMN2 model, its checks, the BPMN 2.0 file and the guide's tables
│   ├── cyberflow_incident-handling.bpmn the model as a BPMN 2.0 file with layout (reference)
│   ├── render_bpmn.js                   reference drawing (bpmn-js)
│   ├── figure_from_pdf.py               picture from the PDF that ArisExpress exports
│   ├── t5l_content.py                   the text of the protocol and the presentation
│   ├── build_protocol.py                fills the lecturer's protocol template
│   └── build_presentation.py            builds the deck on the lecturer's presentation template
└── outputs/
    ├── figures/     fig1 CLD (PNG, SVG); fig2 BPMN2 reference drawing (PNG, SVG) and three enlarged parts
    ├── draft/       protocol and presentation with the reference drawing (not for handing in)
    └── submission/  the files handed in (created by the final build)
```

## Rebuilding

Python with `matplotlib`, `python-docx`, `python-pptx` and `pillow`; Node with `bpmn-js` and
`playwright` for the reference drawing; LibreOffice or Word for the PDF.

```
python ../tools/cld_draw.py tools/cyberflow_cld.json outputs/figures/fig1_cyberflow_cld.png outputs/figures/fig1_cyberflow_cld.svg
python tools/check_cld.py tools/cyberflow_cld.json
python tools/build_bpmn.py tools/cyberflow_incident-handling.bpmn
node tools/render_bpmn.js tools/cyberflow_incident-handling.bpmn outputs/figures/fig2_cyberflow_bpmn2_reference.svg outputs/figures/fig2_cyberflow_bpmn2_reference.png 2

# drafts (reference drawing)
python tools/build_protocol.py --draft --out outputs/draft/vagif.asgarli-T5L_DRAFT.docx --bpmn-figure outputs/figures/fig2_cyberflow_bpmn2_reference.png
python tools/build_presentation.py --draft --out outputs/draft/vagif.asgarli-T5L-presentation_DRAFT.pptx --bpmn-figure outputs/figures/fig2_cyberflow_bpmn2_reference.png --detail-figures outputs/figures/fig2_reference_detail1_detection.png outputs/figures/fig2_reference_detail2_handling.png outputs/figures/fig2_reference_detail3_reporting.png

# final (after the ArisExpress export is in outputs/submission/)
python tools/figure_from_pdf.py outputs/submission/vagif.asgarli-T5L-model.pdf outputs/figures/fig2_cyberflow_bpmn2_arisexpress.png
python tools/build_protocol.py --out outputs/submission/vagif.asgarli-T5L.docx --bpmn-figure outputs/figures/fig2_cyberflow_bpmn2_arisexpress.png --date "DD. MM. 2026"
python tools/build_presentation.py --out outputs/submission/vagif.asgarli-T5L-presentation.pptx --bpmn-figure outputs/figures/fig2_cyberflow_bpmn2_arisexpress.png
# then convert vagif.asgarli-T5L.docx to vagif.asgarli-T5L.pdf
```

The final builds must use the ArisExpress figure: the reference drawing is only what the
diagram is copied from. If the diagram drawn in ArisExpress differs from the reference (an
element renamed, added or left out), change `tools/build_bpmn.py` first, so that the counts in
the protocol stay true.
