"""Builds the T5L presentation on the lecturer's template (materials/t5l_presentation-template.pptx).

The two slides of the template are kept (title slide with the name filled in, "Content" slide as it is);
the other slides are copies of the template's content slide, so heading, line, footer and slide number are
the lecturer's. Order of the slides = the order of the template's "Content" list:
goal system summary, CLD and its description, BPMN2 diagram, conclusions.

    python build_presentation.py --out <deck.pptx> --bpmn-figure <diagram.png> [--draft]

--bpmn-figure     picture of the BPMN2 diagram: for the deck that is handed in, the picture exported from
                  ArisExpress; with --draft the reference drawing.
--detail-figures  optional enlarged parts of the diagram, one slide each, in the order of the process.
                  Without them the diagram is cut into a left and a right half.
"""
from __future__ import annotations

import argparse
import copy
import os
import sys
import tempfile

from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t5l_content as C  # noqa: E402

TEMPLATE = os.path.join(HERE, "..", "materials", "t5l_presentation-template.pptx")
CLD_FIGURE = os.path.join(HERE, "..", "outputs", "figures", "fig1_cyberflow_cld.png")
FONT = "Arial"
INK = RGBColor(0x1A, 0x1A, 0x1A)
RED = RGBColor(0xC0, 0x00, 0x00)        # the colour the template uses for key terms
GREY = RGBColor(0x55, 0x55, 0x55)
LEFT, TOP, WIDTH, BOTTOM = Inches(0.55), Inches(1.15), Inches(8.9), Inches(6.25)


def clone_slide(prs, src):
    """A new slide with a copy of every shape of the template's content slide."""
    slide = prs.slides.add_slide(src.slide_layout)
    for shp in list(slide.shapes):
        shp._element.getparent().remove(shp._element)
    for el in list(src.shapes._spTree)[2:]:
        slide.shapes._spTree.append(copy.deepcopy(el))
    return slide


def set_heading(slide, text):
    heading = next(s for s in slide.shapes if s.name == "Rectangle 6")
    runs = heading.text_frame.paragraphs[0].runs
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    # the heading box does not wrap and its text is centred: give the box the width of the new text,
    # so that every heading starts at the same place as the template's "Content"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 240)
        width_pt = font.getlength(text) / 10          # Liberation Sans has the metrics of Arial; 24 pt
    except OSError:
        width_pt = 0.6 * 24 * len(text)
    heading.width = Emu(int(width_pt * 12700) + 2 * 91440)
    body = next(s for s in slide.shapes if s.name == "Rectangle 7")
    body._element.getparent().remove(body._element)


def add_text(slide, items, top=TOP, size=16, left=LEFT, width=WIDTH, height=None, gap=8):
    """items: list of paragraphs; a paragraph is a list of (text, style) with style in '', 'b', 'r' (red), 'i', 'g'."""
    box = slide.shapes.add_textbox(left, top, width, height or (BOTTOM - top))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.space_after = Pt(gap)
        if isinstance(item, str):
            item = [(item, "")]
        for text, style in item:
            run = par.add_run()
            run.text = text
            run.font.name = FONT
            run.font.size = Pt(size - 4 if "g" in style else size)
            run.font.bold = "b" in style
            run.font.italic = "i" in style
            run.font.color.rgb = RED if "r" in style else (GREY if "g" in style else INK)
    return box


def add_picture(slide, path, top=TOP, max_h=None, max_w=WIDTH, left=None):
    """Places a picture as large as the given area allows; centred unless `left` is given.
    Returns the bottom edge, or (right edge, bottom edge) when `left` is given."""
    with Image.open(path) as im:
        w, h = im.size
    max_h = max_h or (BOTTOM - top)
    scale = min(max_w / w, max_h / h)
    pw, ph = int(w * scale), int(h * scale)
    x = int((Inches(10) - pw) / 2) if left is None else left
    slide.shapes.add_picture(path, x, top, pw, ph)
    return top + ph if left is None else (x + pw, top + ph)


def add_table(slide, rows, col_widths_in, top=TOP, size=12):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), LEFT, top, WIDTH, Inches(0.3) * len(rows))
    table = shape.table
    tblPr = shape._element.graphic.graphicData.tbl.tblPr
    style = tblPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"       # "No Style, Table Grid": plain black grid
    for c, w in enumerate(col_widths_in):
        table.columns[c].width = Inches(w)
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            cell = table.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            par = cell.text_frame.paragraphs[0]
            par.alignment = PP_ALIGN.LEFT
            run = par.add_run()
            run.text = text
            run.font.name = FONT
            run.font.size = Pt(size)
            run.font.bold = (r == 0)
            run.font.color.rgb = INK
    return shape


# the three enlarged parts of the diagram and what happens in each of them
DETAILS = [
    ("BPMN2 diagram: detection", [
        [("Start event: ", "b"), ("an employee notices suspicious activity and reports it.", "")],
        [("SOC analyst ", "b"), ("registers and classifies the event; Data object “Incident ticket”.", "")],
        [("Cybersecurity manager ", "b"), ("assesses the significance.", "")],
        [("Gateway XOR ", "br"), ("“Significant incident?”: exactly one path. No: routine event, End event. Yes: "
                                  "the incident procedure is activated; it is read from the Data store “Procedure "
                                  "models”.", "")],
    ]),
    ("BPMN2 diagram: handling", [
        [("Gateway AND: ", "br"), ("three branches run in parallel.", "")],
        [("IT operations: ", "b"), ("Gateway OR", "br"), (" “Which measures are needed?”: one, two or all three "
                                                         "measures; a second OR merges them.", "")],
        [("SOC analyst: ", "b"), ("collects and preserves evidence; Data object “Evidence package”.", "")],
        [("Cybersecurity manager: ", "b"), ("Timer event (24 h), early warning as a Message flow to the CSIRT, "
                                            "Message event “Feedback and guidance received”.", "")],
        [("CSIRT: ", "b"), ("Message start event, registers and assesses the warning, sends feedback and "
                            "guidance.", "")],
        [("Second Gateway AND: ", "br"), ("waits for all three branches.", "")],
    ]),
    ("BPMN2 diagram: reporting", [
        [("SOC analyst ", "b"), ("prepares the initial assessment (Data object).", "")],
        [("Timer event (72 h): ", "br"), ("incident notification as a Message flow.", "")],
        [("IT operations ", "b"), ("remove the cause and restore the services.", "")],
        [("Review: ", "b"), ("the procedure model is updated in the Data store (the learning loop R1 of the CLD).", "")],
        [("Timer event (one month): ", "br"), ("final report as a Message flow; End event “Incident closed”.", "")],
        [("CSIRT: ", "b"), ("two Message intermediate events, End event “Case closed”.", "")],
    ]),
]


def build(out, bpmn_figure, draft, detail_figures=None):
    prs = Presentation(TEMPLATE)
    title, content = prs.slides[0], prs.slides[1]
    name = next(s for s in title.shapes if s.name == "Rectangle 8")
    name.text_frame.paragraphs[0].runs[0].text = C.NAME

    def slide(heading):
        s = clone_slide(prs, content)
        set_heading(s, heading)
        return s

    # 1. goal system
    s = slide(f"Goal system: {C.GOAL_NAME}")
    add_text(s, [
        [(f"{C.GOAL_NAME}", "br"), (": a BPMN 2.0-based method and model repository for the incident-handling "
                                    "procedures of a medium-sized Latvian organisation subject to NIS2 "
                                    "(goal system of the PR1 topic).", "")],
        [("Why: ", "b"), ("procedures are mostly text: 76.7% of practitioners’ playbooks are text-based (Schlette "
                          "et al., 2024), while the law leaves little time: early warning in ", ""), ("24 h", "r"),
         (", incident notification in ", ""), ("72 h", "r"), (", final report in ", ""), ("one month", "r"),
         (" (Directive 2022/2555, 2022; Nacionālās kiberdrošības likums, 2024). CERT.LV (2026) manually processed "
          "2,982 incidents in 2025.", "")],
        [("Social part: ", "b"), ("employee, SOC analyst, cybersecurity manager, IT operations and the national "
                                  "CSIRT (CERT.LV).", "")],
        [("Technical part: ", "b"), ("procedure models in BPMN 2.0, the model repository and the modelling rules "
                                     "(roles, time limits, notifications and documents as BPMN 2.0 elements).", "")],
        [("Purpose: ", "b"), ("every participant understands a procedure in the same way: fewer procedural "
                              "errors, time limits met.", "")],
    ], size=18, gap=10)

    # 2. CLD and its description
    s = slide("CLD of the goal system")
    y = add_picture(s, CLD_FIGURE, top=Inches(1.05), max_h=Inches(4.95))
    add_text(s, [[("Blue “+”: same direction; red “−”: opposite direction; two strokes: delay; R: reinforced loop; "
                   "B: balanced loop; italics: outside influence.", "g")]], top=y + Inches(0.02), size=15,
             height=Inches(0.3))

    s = slide("CLD: feedback loops")
    short = {
        "B1": "losses → management support → procedure models → staff understanding → fewer errors → shorter "
              "response time → lower losses. Reacts to losses, with a delay.",
        "B2": "more models → more maintenance workload → models out of date. Limits the growth of the repository.",
        "R1": "models are used in real incidents → lessons learned → better models. Unused models are not improved.",
        "R2": "procedural errors → analyst workload → more errors.",
        "R3": "short response time → timely notification → CSIRT guidance → shorter response time.",
    }
    items = []
    for label, title_, _ in C.LOOPS:
        kind = title_.split(" (")[0]
        items.append([(f"{label} ", "br"), (f"{kind}: ", "b"), (short[label], "")])
    items.append([("Stability: ", "b"), ("reinforcing loops must be balanced, otherwise the system is unstable "
                                         "(Ginters, 2026a). R1 is limited by B2; when R2 or R3 run in the harmful "
                                         "direction, losses grow and B1 is activated.", "")])
    items.append([(f"{C.N_CLD_VARIABLES} variables, {C.N_CLD_LINKS} links, 2 balanced and 3 reinforced loops; "
                   "polarity checked by counting the negative links.", "g")])
    add_text(s, items, size=16, gap=9)

    # 3. BPMN2 diagram
    s = slide("From CLD to BPMN2")
    add_text(s, [[("A CLD variable is a state, not an activity: each variable was traced to the place of the "
                   "process where it appears.", "")]], size=15, height=Inches(0.6))
    add_table(s, C.TABLE2, (3.3, 5.6), top=Inches(1.8), size=12)

    note = [("Reference drawing (draft): to be replaced by the figure exported from ArisExpress.", "g")] if draft \
        else [("Drawn in ArisExpress (files in ADF and PDF format).", "g")]

    s = slide("BPMN2 diagram")
    y = add_picture(s, bpmn_figure, top=Inches(1.2), max_w=Inches(9.6))
    add_text(s, [
        [(f"2 Pools: “{C.POOL_ORG}” with 4 Swimlanes and “{C.POOL_CSIRT}”; {C.N_TASKS} tasks, {C.N_EVENTS} events, "
          f"{C.N_GATEWAYS} gateways, {C.N_MSG} message flows, {C.N_DATA_OBJECTS} data objects and a data store.", "")],
        note,
    ], top=y + Inches(0.15), size=14, gap=4)

    if detail_figures:                                 # enlarged parts with a short walk through the process
        for (heading, steps), path in zip(DETAILS, detail_figures):
            s = slide(heading)
            right, _ = add_picture(s, path, top=Inches(1.05), max_h=Inches(5.2), max_w=Inches(6.3), left=Inches(0.3))
            x = right + Inches(0.25)
            add_text(s, steps, top=Inches(1.1), left=x, width=Inches(9.8) - x, size=13, gap=7)
        details = []
    else:                                              # no enlarged parts given: a left and a right half
        im = Image.open(bpmn_figure).convert("RGB")
        w, h = im.size
        tmp = tempfile.mkdtemp(prefix="t5l_")
        details = []
        for part, box in (("left part", (0, 0, int(w * 0.54), h)), ("right part", (int(w * 0.46), 0, w, h))):
            path = os.path.join(tmp, f"bpmn_{part.split()[0]}.png")
            im.crop(box).save(path)
            details.append((f"BPMN2 diagram: {part}", path))
    for heading, path in details:
        s = slide(heading)
        add_picture(s, path, top=Inches(1.05), max_h=Inches(5.2), max_w=Inches(9.6))

    s = slide("Mandatory elements")
    add_table(s, C.TABLE3, (3.0, 5.9), top=Inches(1.2), size=13)
    add_text(s, [[("Verified before drawing: sequence flows stay inside their Pool, message flows connect "
                   "different Pools, every element lies on a path from a start to an end event, AND and OR splits "
                   "have joins of the same type, no line crosses another.", "g")]], top=Inches(5.6), size=16,
             height=Inches(0.8))

    # 4. conclusions
    s = slide("Conclusions")
    add_text(s, [
        [("No mechanical transformation: ", "b"), (f"{C.N_MAPPED} of {C.N_CLD_VARIABLES} CLD variables could be "
                                                   "traced to a BPMN2 element; procedural errors, analyst workload "
                                                   "and management support have none.", "")],
        [("Feedback loops are not visible in BPMN2: ", "b"), ("one run goes from start to end; the learning loop "
                                                              "appears only as a task that updates the data store.", "")],
        [("Convenient: ", "b"), ("the CLD had fixed the border and the participants: the CSIRT became the second "
                                 "Pool, its links became Message flows.", "")],
        [("Main problem: ", "b"), ("missing information. Roles, order, conditions, time limits and documents had "
                                   "to be taken from the legal requirements.", "")],
        [("Time limits: ", "b"), ("“not later than 24 h” is not a waiting time; the Timer events only mark the "
                                  "limits (Ginters, 2026b).", "")],
        [("The models complement each other: ", "b"), ("the CLD explains why, the BPMN2 model shows who does what "
                                                       "and when.", "")],
    ], size=16, gap=9)

    s = slide("References")
    add_text(s, [[(ref.replace("*", ""), "")] for ref in C.REFERENCES], size=10, gap=5)

    prs.save(out)
    print(f"written {out}: {len(prs.slides)} slides ({'DRAFT' if draft else 'final'}, BPMN2 figure "
          f"{os.path.basename(bpmn_figure)})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bpmn-figure", required=True)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--detail-figures", nargs="*")
    a = ap.parse_args()
    build(a.out, a.bpmn_figure, a.draft, a.detail_figures)


if __name__ == "__main__":
    main()
