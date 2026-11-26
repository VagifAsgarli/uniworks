# T4L: System Dynamics Simulation in STELLA (Yellowstone)

| | |
|---|---|
| Course | DE0796 Sociotechnical Systems Modelling, Prof. Egils Ginters |
| Task | a detailed Stocks and Flows model of the Yellowstone ecosystem in STELLA, built from the T4LPrim CLD; own initial values and rates; sliders and buttons on the Interface layer; protocol and presentation; live demonstration at the defence |
| Original deadline | 24.10.2026 by e-mail; defence 28.10.2026 |
| Agreed deadline | **2 December 2026**: the lecturer accepts the late works and allowed them to be prepared with full AI support |
| Mark | register column **T4LFin** = mean of T4L (work) and T4LPrez (presentation); needed for exam admission |
| Hand in | e-mail to `egils.ginters@rtu.lv`: protocol (PDF), model (STM format), presentation (PPT/PPTX) |

## Task (the lecturer's words, lab deck slide 14)

1. Based on T4Lprim Yellowstone CLD materials and analysis of information sources create a detail
   SD stocks and flows model in the STELLA environment of the ecosystem functioning.
2. Select your own initial values for resources Wolves, Deers etc. and other parameters/rates.
   Demonstrate how resources changing in time and are influenced by different rates.
3. Use sliders and buttons in Yellowstone SD model interface.
4. Prepare a T4L protocol including the simulation results in graphical and table form as well as
   screenshots from running the Yellowstone SD stocks and flows model.
5. Prepare a T4L presentation in the Power Point environment, as well as demonstrate the operation
   of the Yellowstone SD model in the STELLA environment during defence.

## Status

- [x] Model designed from the CLD: 4 stocks (Wolves, Deers, Vegetation, Beavers), 9 flows,
      28 converters, 41 action connectors; 4 sliders and 3 buttons on the Interface layer
- [x] Own initial values and rates chosen and justified; the base run resembles the counts in the
      park (wolves peak 167 in 2002, counted 174 in 2003; deers 6,000 in 2010, counted 6,070;
      beavers 18.7 colonies in 2015, counted 18)
- [x] Six experiments defined and calculated (reference run)
- [x] STELLA model file written (XMILE, `.stmx`) and checked with an independent simulator:
      identical numbers in all six experiments
- [x] Step-by-step guide for STELLA 9.0.4 (build by hand) and for Stella Architect (open the file),
      in Azerbaijani
- [x] Protocol on the lecturer's template: **draft** (12 pages); the figures that must be STELLA
      screenshots are marked
- [x] Presentation on the lecturer's template: **draft** (12 slides, speaker notes)
- [x] Explanation and likely questions for the student, in Azerbaijani
- [ ] **Student**: build or open the model in STELLA, check the numbers, run the six experiments,
      take the nine screenshots (list in the guide), save the model
- [ ] Final protocol and presentation built with the STELLA screenshots (`outputs/submission/`)
- [ ] Student: sign the protocol, send the three files, demonstrate the model at the defence

## Which STELLA

The lecturer works in classic STELLA, version 9 (file format STM); a classmate names the version
as 9.0.4. The course materials say so in three places:

- the task asks for the model "in STM format" (lab deck, slide 15; protocol template);
- the lab deck describes the four tabbed layers Map, Model, Interface and Equation, cites Fisher's
  textbook for STELLA 9 (2nd edition, 2007), and its screenshots show the classic graph pad and
  equation listing;
- in the T2 lecture the link "Demonstrations in STELLA environment" (slide 37) points to the
  lecturer's own model `CesDem2017.STM`.

None of the videos embedded in the lectures shows STELLA (they cover other topics and tools); the
lecturer demonstrates STELLA live. STELLA 9 cannot open the STMX files of the current version, so
the first route below is the one that follows the lecturer's rules.

| Route | Model file handed in | Work for the student |
|---|---|---|
| **STELLA 9.0.4** (recommended; the installer the classmates use, or a computer of the university lab) | `VagifAsgarli-T4L.STM` | build the model by hand with the guide (1.5–2 hours) |
| Stella Architect (current version, 30-day evaluation), only if STELLA 9 cannot be obtained | `VagifAsgarli-T4L.stmx` | open the prepared file, check it, take the screenshots (30–40 minutes) |

Stella Architect cannot save the old STM format, and the lecturer's STELLA cannot open STMX. If the
second route is used, the e-mail to the lecturer says so in one sentence: "The model was built in
Stella Architect, the current version of STELLA, which saves in STMX format."

## The model in short

| Stock | Inflow | Outflows | Initial value |
|---|---|---|---|
| Wolves | wolf births | wolf deaths | Wolves released = 31 (slider) |
| Deers | deer births | deer deaths, predation | 17,000 |
| Vegetation (% of capacity) | regrowth | browsing | 20 |
| Beavers (colonies) | colony growth | colony loss | 1 |

Run: 1995–2045, DT = 0.25 years, Euler's method. Sliders: Wolves released, Wolf hunting rate, Deer
hunting rate, Winter severity. All equations: [`outputs/model/model-specification.md`](outputs/model/model-specification.md).

| Experiment | Wolves | Deers | Vegetation, % | Beavers |
|---|---|---|---|---|
| E1 base run: 31 wolves released | 102 | 7,022 | 72 | 19.4 |
| E2 no wolves | 0 | 17,036 | 21 | 1.2 |
| E3 no deer hunting | 133 | 8,090 | 68 | 17.9 |
| E4 wolves hunted, 15% a year | 74 | 10,073 | 58 | 14.6 |
| E5 severe winters | 77 | 6,281 | 75 | 20.5 |
| E6 100 wolves released | 101 | 7,025 | 72 | 19.5 |

(stocks in 2045)

## Layout

```
t4l_system-dynamics-stella/
├── README.md
├── materials/                               the lecturer's lab deck, handouts, protocol and presentation templates
├── notes/
│   ├── stella-guide_az.md                   how to build/open the model, run the experiments, take the screenshots
│   └── defence-prep_az.md                   explanation of the model and likely questions (Azerbaijani)
├── tools/
│   ├── yellowstone_model.py                 the model, written down once: stocks, flows, converters, layout, experiments
│   ├── yellowstone_sd.py                    reference run of the same equations (Euler, like STELLA): tables and graphs
│   ├── build_stmx.py                        writes the STELLA files, the specification and the expected MODEL-layer drawing
│   ├── check_stmx.py                        runs the .stmx with PySD and compares it with the reference run
│   ├── t4l_content.py                       text of the protocol and the presentation
│   ├── build_protocol.py                    fills the lecturer's protocol template
│   └── build_presentation.py                fills the lecturer's presentation template
└── outputs/
    ├── model/                               Yellowstone.stmx, Yellowstone_with-interface.stmx, model-specification.md,
    │                                        model-layer_expected.png
    ├── reference-simulation/                expected tables (CSV) and graphs (PNG) of the six experiments
    ├── stella-screenshots/                  the screenshots taken in STELLA (to be added by the student)
    ├── draft/                               protocol and presentation drafts (expected pictures stand in for screenshots)
    └── submission/                          the files handed in (created by the final build)
```

## Rebuild

```
cd tools
python yellowstone_sd.py                     # reference run: tables and graphs
python build_stmx.py ../outputs/model        # STELLA files, specification, expected drawing, layout check
python check_stmx.py ../outputs/model/Yellowstone.stmx
python build_protocol.py [--date "DD. MM. 2026"]     # draft while screenshots are missing, final when all are there
python build_presentation.py
```

Needs Python with `matplotlib`, `pysd`, `python-docx`, `python-pptx`, `pillow`; the `.docx` and
`.pptx` are converted to PDF with LibreOffice or Word.

## What is real and what is a checking aid

- The model that is handed in and demonstrated is the STELLA model. The protocol shows STELLA
  screenshots only.
- `yellowstone_sd.py`, the expected graphs and `model-layer_expected.png` are checking aids: they
  tell what STELLA must show. In the drafts they stand in for the screenshots and are marked as
  such; they are not in the final files.
- `Yellowstone_with-interface.stmx` has the sliders, buttons and graphs of the Interface layer
  written from the XMILE specification. It could not be opened in STELLA here; if the Interface
  layer comes up empty, `Yellowstone.stmx` is used and the Interface is built by hand (guide,
  section B2).
- The rates are the student's own values for a simple teaching model. The protocol states the
  limits: the model lets the wolves cause most of the decline of the deers, while studies also name
  hunters, winters, drought and bears.
