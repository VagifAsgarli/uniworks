# T4LPrim: Causal Loops Diagram of Yellowstone

| | |
|---|---|
| Course | DE0796 Sociotechnical Systems Modelling, Prof. Egils Ginters |
| Task | Causal Loops Diagram (CLD) of the processes in Yellowstone nature, reinforced and balanced feedbacks marked, a justified opinion about the stability of the ecosystem; presented on the lecturer's template |
| Original deadline | 07.10.2026 (presented in class) |
| Agreed deadline | **2 December 2026**: the lecturer accepts the late works and allowed them to be prepared with full AI support |
| Mark | register column **T4LprimFin**; needed for exam admission |
| Hand in | the presentation, by e-mail to `egils.ginters@rtu.lv`, then presented to the lecturer |

## Task (the lecturer's words, template slide 2)

- Design and present Causal Loops Diagram (CLD) of the interoperable dynamics processes in
  Yellowstone nature;
- Mark reinforced and balanced feedbacks in CLD;
- Justify your opinion about ecosystem stability.

## Status

- [x] CLD drawn in the notation of the lecture and of the template example: 14 variables, 20 links,
      3 reinforced (R1–R3) and 4 balanced (B1–B4) feedbacks, 3 delays, 2 outside influences
- [x] Every statement on the slides checked against its source (National Park Service pages,
      Yellowstone Wolf Project reports, journal articles); APA 7 reference list
- [x] Presentation on the lecturer's template: 10 slides with speaker notes
- [x] Explanation and likely questions for the student, in Azerbaijani
- [ ] Student: read the explanation, send the presentation, present it

## The diagram in one paragraph

Wolves and Deers (the elk of the park) each grow through births (R1, R2). The predator and prey
loop B1 balances both, with a delay that makes them swing. Wolves are also limited by fights
between packs and diseases (B2), deers by their food (B3) and by hunting permits (B4). Vegetation,
beavers and the water table support each other (R3). Wolves reach R3 through the chain
Wolves − Deers − Vegetation. Opinion: the ecosystem is stable as long as its balanced feedbacks
work; without wolves it rests in a second, poor state.

## Layout

```
t4lprim_causal-loop-diagram-yellowstone/
├── README.md
├── materials/
│   └── t4lprim_presentation-template.pptx      the lecturer's template (title, Task, Example)
├── notes/
│   └── defence-prep_az.md                      explanation, speaking plan, likely questions (Azerbaijani)
├── tools/
│   ├── yellowstone_cld.json                    the diagram: variables, links, signs, loops
│   └── build_t4lprim_presentation.py           builds the presentation on the template
└── outputs/
    ├── figures/yellowstone_cld.png, .svg       the diagram
    ├── preview/VagifAsgarli-T4LPrim.pdf        PDF copy for reading
    └── submission/VagifAsgarli-T4LPrim.pptx    the file handed in
```

The diagram is drawn by [`../tools/cld_draw.py`](../tools/cld_draw.py); the slide helpers are in
[`../tools/lecturer_deck.py`](../tools/lecturer_deck.py).

## Rebuild

```
python ../tools/cld_draw.py tools/yellowstone_cld.json outputs/figures/yellowstone_cld.png outputs/figures/yellowstone_cld.svg
python tools/build_t4lprim_presentation.py
```

Needs Python with `matplotlib`, `python-pptx` and `pillow`.

## Notes

- The lecturer writes "Deers"; in Yellowstone the main prey of the wolves is the elk, the largest
  deer of the park. The diagram says "Deers (elk)".
- The same diagram is Figure 1 of the T4L protocol, and the T4L model is built from it
  ([`../t4l_system-dynamics-stella/`](../t4l_system-dynamics-stella/)).
- The last slide carries a note on the use of generative AI, as the course asks in PR1.
