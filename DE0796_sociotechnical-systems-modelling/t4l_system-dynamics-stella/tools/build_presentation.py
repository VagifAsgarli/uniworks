"""Builds the T4L defence presentation on the lecturer's template.

    python build_presentation.py [--shots DIR] [--out FILE.pptx]

The template (../materials/t4l_presentation-template-for-defence.pptx) has a title slide and a Content
slide; both are kept (only the name is filled in).  The slides follow the lecturer's Content list:
CLD of T4LPrim, the Stocks and Flows model in STELLA (MODEL and INTERFACE view), the curves of Wolves and
Deers with explanations, conclusions, and the plan of the live demonstration.

--shots DIR   folder with the STELLA screenshots (see t4l_content.SHOTS).  While one is missing the deck is
              a DRAFT: the expected picture from the checking calculation stands in and the slide says so.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))

import t4l_content as C  # noqa: E402
import yellowstone_model as m  # noqa: E402
import yellowstone_sd as sd  # noqa: E402
from lecturer_deck import (GREY, HEAD, INK, PALE, RED, RULE, WHITE, Deck, Inches, MSO_ANCHOR, PP_ALIGN, Pt,  # noqa: E402
                           box, notes, replace_text, text)
from PIL import Image  # noqa: E402

TEMPLATE = os.path.join(HERE, "..", "materials", "t4l_presentation-template-for-defence.pptx")
CLD_FIGURE = os.path.join(HERE, "..", "..", "t4lprim_causal-loop-diagram-yellowstone", "outputs", "figures",
                          "yellowstone_cld.png")
EXPECTED = os.path.join(HERE, "..", "outputs", "reference-simulation")
EXPECTED_MODEL = os.path.join(HERE, "..", "outputs", "model", "model-layer_expected.png")
GRAPH_SHOT = "10_graph_wolves-deers_E1.png"      # optional: the graph pad "Wolves and Deers" alone, enlarged


def shot(key, shots):
    """Returns (path, True if it is the real STELLA screenshot)."""
    name = C.SHOTS.get(key, key)
    if shots and os.path.exists(os.path.join(shots, name)):
        return os.path.join(shots, name), True
    if key == "model":
        return EXPECTED_MODEL, False
    if key == GRAPH_SHOT:
        key = "E1"
        if shots and os.path.exists(os.path.join(shots, C.SHOTS["E1"])):
            return os.path.join(shots, C.SHOTS["E1"]), True
    exp = next(n for n in C.RUNS if n.startswith(key))
    return os.path.join(EXPECTED, sd.slug(exp) + ".png"), False


def place(slide, path, x, y, max_w, max_h, real):
    w, h = Image.open(path).size
    scale = min(max_w / w, max_h / h)
    pw, ph = w * scale, h * scale
    slide.shapes.add_picture(path, Inches(x + (max_w - pw) / 2), Inches(y), width=Inches(pw))
    if not real:
        text(slide, x, y + ph + 0.02, max_w, 0.3,
             "DRAFT: expected picture from the checking calculation; the STELLA screenshot goes here", 10, RED,
             italic=True, align=PP_ALIGN.CENTER)
    return ph


def table(slide, x, y, widths, rows, size=11, row_h=0.36):
    shape = slide.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)),
                                   Inches(row_h * len(rows)))
    tbl = shape.table
    tblPr = shape._element.graphic.graphicData.tbl.tblPr
    for attr in ("bandRow", "firstRow"):
        tblPr.set(attr, "0")
    for c, w in enumerate(widths):
        tbl.columns[c].width = Inches(w)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_h)
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = HEAD if r == 0 else (WHITE if r % 2 else PALE)
            par = cell.text_frame.paragraphs[0]
            par.alignment = PP_ALIGN.LEFT if c == 0 or isinstance(value, str) and not value[:1].isdigit() else PP_ALIGN.CENTER
            run = par.add_run()
            run.text = str(value)
            run.font.size, run.font.name, run.font.bold = Pt(size), "Arial", r == 0
            run.font.color.rgb = WHITE if r == 0 else INK
    return shape


def build(out, shots):
    deck = Deck(TEMPLATE)
    used = []

    def pic(key):
        path, real = shot(key, shots)
        used.append(real)
        return path, real

    # 1 title, 2 content (the lecturer's slides)
    s = deck.title_slide
    replace_text({sh.name: sh for sh in s.shapes}["Rectangle 8"], f"{C.NAME}, {C.STUDENT_ID}")
    notes(s, "Good afternoon. This is my T4L work: the Stocks and Flows model of the Yellowstone ecosystem in STELLA, "
             "built from my Causal Loops Diagram of T4LPrim.")
    notes(deck.content_slide, "I follow the content of the template: first the CLD, then the model in STELLA with its "
                              "MODEL and INTERFACE view, the curves of wolves and deers, the conclusions, and at the end "
                              "I run the model in STELLA.")

    # 3 CLD
    s = deck.new_slide("Yellowstone CLD (T4LPrim)")
    s.shapes.add_picture(CLD_FIGURE, Inches(1.35), Inches(1.0), width=Inches(7.3))
    text(s, 0.55, 5.1, 8.9, 1.2, [
        "[[Reinforced]]: births of wolves (R1) and of deers (R2); vegetation, beavers and water table (R3).",
        "[[Balanced]]: predator and prey (B1), pack fights and diseases (B2), food of the deers (B3), hunting (B4).",
        "Every reinforced loop is held by a balanced one, so the ecosystem is stable while B1 works.",
    ], 12.5, INK, bullet=True, after=3)
    notes(s, "The CLD of T4LPrim. Wolves and deers each grow through births, loops R1 and R2. The predator and prey "
             "loop B1 balances both; B2 limits the wolves through fights and diseases, B3 limits the deers through "
             "their food, B4 through hunting. Vegetation, beavers and the water table form the reinforced loop R3. "
             "Wolves reach it through the chain wolves, deers, vegetation.")

    # 4 from the CLD to the model
    s = deck.new_slide("From the CLD to Stocks and Flows")
    text(s, 0.55, 1.1, 8.9, 0.6,
         f"The variables that carry the loops became [[{len(m.STOCKS)} stocks]]; the links became "
         f"[[{len(m.FLOWS)} flows]] and [[{len(m.CONVERTERS)} converters]], joined by action connectors.", 14)
    rows = [("In the CLD", "In the STELLA model"),
            ("Wolves, Deers, Vegetation, Beavers", "stocks"),
            ("Wolf births (R1), Deers → Wolf births (B1)", "flow wolf births = Wolves born per deer eaten × predation"),
            ("Wolves → Deers (B1)", "flow predation = Kill coefficient × Wolves × Deers"),
            ("Pack fights, diseases (B2)", "converter Fights and diseases in the flow wolf deaths"),
            ("Vegetation → Deer births (B3)", "converter Deer capacity in the flow deer births"),
            ("Deers → Vegetation (B3)", "flow browsing"),
            ("Hunting permits (B4), Winter severity", "sliders Deer hunting rate and Winter severity"),
            ("Vegetation → Beavers → water table (R3)", "converters Willow habitat, Free habitat, Beaver ponds effect")]
    table(s, 0.55, 1.95, (3.7, 5.2), rows, size=11, row_h=0.42)
    text(s, 0.55, 5.85, 8.9, 0.4, f"Run: {m.START}–{m.STOP}, DT = {m.DT} years, Euler's method. Own initial values: "
                                  "31 wolves, 17,000 deers, vegetation 20%, 1 beaver colony.", 12, GREY, italic=True)
    notes(s, "How the CLD became the model. The four variables that carry the loops are the stocks. Each link became a "
             "flow or a converter. For example the link from wolves to deers is the flow predation, equal to the kill "
             "coefficient times wolves times deers. The initial values are my own: 31 wolves as were released, 17,000 "
             "deers as counted in 1995, vegetation at 20 percent and one beaver colony.")

    # 5 MODEL view
    s = deck.new_slide("Stocks and Flows model: MODEL view")
    path, real = pic("model")
    place(s, path, 0.45, 1.05, 9.1, 4.95, real)
    notes(s, "The MODEL layer in STELLA. Rectangles are the stocks, the pipes with valves are the flows, circles are "
             "the converters and the thin arrows are the action connectors. Top left the wolves, on the right the "
             "deers with births, deaths and predation, bottom right the vegetation with regrowth and browsing, bottom "
             "left the beavers. The predation flow of the deers feeds the births of the wolves: that is loop B1.")

    # 6 INTERFACE view
    s = deck.new_slide("Stocks and Flows model: INTERFACE view")
    path, real = pic("E1")
    h = place(s, path, 0.45, 1.05, 9.1, 4.1, real)
    text(s, 0.55, 1.05 + h + 0.35, 8.9, 0.9, [
        "[[Sliders]]: Wolves released, Wolf hunting rate, Deer hunting rate, Winter severity.",
        "[[Buttons]]: Run, Stop, Restore.   [[Graphs]]: Wolves and Deers; Vegetation and Beavers.",
    ], 12.5, INK, bullet=True, after=3)
    notes(s, "The Interface layer. Four sliders change the rates without opening the model: how many wolves are "
             "released, how strongly wolves and deers are hunted, and how severe the winters are. Three buttons run, "
             "stop and restore the model. The two graphs show the four stocks.")

    # 7 curves of wolves and deers
    s = deck.new_slide("Wolves and Deers in time (base run)")
    path, real = pic(GRAPH_SHOT)
    h = place(s, path, 0.45, 1.05, 9.1, 3.0, real)
    b = C.B
    text(s, 0.55, 1.05 + h + 0.38, 8.9, 2.0, [
        f"**Wolves** grow while deers are plentiful (R1): 31 → {b[2000]['Wolves']:.0f} in 2000, peak "
        f"{C.WOLF_PEAK['Wolves']:.0f} in {C.WOLF_PEAK['time']:.0f}; then fewer deers and pack fights bring them to "
        f"about {b[2045]['Wolves']:.0f} (B1, B2).",
        f"**Deers** fall from 17,000 to {C.DEER_MIN['Deers']:,.0f} in {C.DEER_MIN['time']:.0f} and settle near "
        f"{b[2045]['Deers']:,.0f}: fewer deers mean fewer wolves, so the herd does not collapse (B1).",
        "The swings shrink: a [[damped oscillation]], caused by the delay in the balanced loop B1.",
        f"Counted in the park: 174 wolves in 2003, 83–123 since 2009; 6,070 deers in 2010 (Smith et al., 2004; NPS, "
        f"2025, 2026).",
    ], 12, INK, bullet=True, after=3)
    notes(s, "The curves of the two main resources. The wolves grow fast because every wolf finds many deers; they "
             "peak around 2002. By then predation removes more deers than are born, so the deers fall to about six "
             "thousand in 2010. Fewer deers per wolf means fewer pups, and fights between packs add losses, so the "
             "wolves decline too. After that both swing less and less and settle: about a hundred wolves and seven "
             "thousand deers. The counts in the park behaved in a similar way.")

    # 8 experiments
    s = deck.new_slide("Experiments with the sliders")
    rows = [("Experiment", "Wolves", "Deers", "Vegetation, %", "Beavers")]
    for name in m.EXPERIMENTS:
        k = name.split(" ")[0]
        e = C.EEND[k]
        rows.append((name, f"{e['Wolves']:.0f}", f"{e['Deers']:,.0f}", f"{e['Vegetation']:.0f}", f"{e['Beavers']:.1f}"))
    table(s, 0.55, 1.15, (4.1, 1.1, 1.2, 1.4, 1.1), rows, size=12, row_h=0.4)
    text(s, 0.55, 4.05, 8.9, 0.3, "Stocks in 2045, the end of each run", 11, GREY, italic=True)
    text(s, 0.55, 4.45, 8.9, 1.8, [
        "[[E2]]: without wolves nothing changes: many deers, poor vegetation, one beaver colony.",
        "[[E4]]: hunting the wolves reaches the willow and the beavers through the deers.",
        "[[E3, E5]]: with fewer deaths from hunters, or more from winters, the wolves adjust (B1).",
        "[[E6]]: 100 wolves instead of 31 end in the same balance: the system is stable.",
    ], 12.5, INK, bullet=True, after=3)
    notes(s, "Six experiments, each with one slider changed. Without wolves the model stays where the park was in "
             "1995. If people hunt fifteen percent of the wolves a year, there are more deers, less vegetation and "
             "fewer beavers. Without deer hunting or with severe winters the wolves adjust to the number of deers. "
             "With a hundred wolves released the swings are stronger, but the end state is the same as with 31.")

    # 9 two experiments side by side
    s = deck.new_slide("Without wolves and with hunted wolves")
    for k, key in enumerate(("E2", "E4")):
        path, real = pic(key)
        x = 0.45 + k * 4.6
        h = place(s, path, x, 1.15, 4.5, 3.1, real)
        text(s, x, 1.15 + h + 0.32, 4.5, 0.35, C.EXPERIMENT_FIG[key].split(": ", 1)[1], 11.5, HEAD, bold=True,
             align=PP_ALIGN.CENTER)
    text(s, 0.55, 5.05, 8.9, 1.2, [
        f"E2: {C.EEND['E2']['Deers']:,.0f} deers, vegetation {C.EEND['E2']['Vegetation']:.0f}%, "
        f"{C.EEND['E2']['Beavers']:.1f} colonies for 50 years: a second, poor stable state.",
        f"E4: {C.EEND['E4']['Wolves']:.0f} wolves, {C.EEND['E4']['Deers']:,.0f} deers, vegetation "
        f"{C.EEND['E4']['Vegetation']:.0f}%, {C.EEND['E4']['Beavers']:.1f} colonies: the trophic cascade is weaker.",
    ], 12.5, INK, bullet=True, after=3)
    notes(s, "Two experiments in detail. On the left no wolves are released: all four curves are flat. On the right "
             "the wolves are hunted: they stay at about 74, so the deers stay above ten thousand and the vegetation "
             "and the beavers recover less.")

    # 10 conclusions
    s = deck.new_slide("Conclusions")
    e1 = C.EEND["E1"]
    text(s, 0.55, 1.15, 8.9, 5.0, [
        f"**Wolves**: limited by their prey and by themselves; about {e1['Wolves']:.0f} in the long run. People are "
        f"their largest risk.",
        f"**Deers**: a smaller but steady herd, about {e1['Deers']:,.0f} ({e1['Deers'] / 170:.0f}% of 17,000); no "
        f"collapse.",
        f"**Vegetation**: best prospects, but slow: 20% → {e1['Vegetation']:.0f}% in about 20 years, only with wolves.",
        f"**Beavers**: 1 → {e1['Beavers']:.0f} colonies, about ten years after the deers decline.",
        "**Stability**: all runs converge; the swings come from the delay in B1 and die out. Without wolves the "
        "system rests in a second, poor state.",
        "**Limits**: a simple model with my own rates; hunters, winters, drought and bison also act in the park "
        "(MacNulty et al., 2020; Hobbs et al., 2024). It shows directions and delays, not forecasts.",
    ], 13, INK, bullet=True, after=6)
    notes(s, "Conclusions about the prospects of the resources. The wolves limit themselves at about a hundred. The "
             "deers stay at about forty percent of the old herd and do not collapse. The vegetation has the best "
             "prospects but needs twenty years, and the beavers follow ten years later. The system is stable; the "
             "swings come from the delay in the predator and prey loop. The model is simple and its rates are my own, "
             "so it shows directions and delays, not forecasts.")

    # 11 demonstration
    s = deck.new_slide("Demonstration in STELLA")
    steps = ["MODEL layer: the four stocks, their flows, converters and action connectors.",
             "INTERFACE layer: Run with the default values (31 wolves): the base run.",
             "Slider Wolves released = 0, Run: no change in 50 years.",
             "Restore; slider Wolf hunting rate = 0.15, Run: more deers, less vegetation, fewer beavers.",
             "Restore; slider Winter severity = 2, Run: fewer deers and wolves, more vegetation.",
             "Table: the numbers behind the curves."]
    for k, step in enumerate(steps):
        y = 1.3 + k * 0.72
        box(s, 0.6, y, 0.5, 0.5, fill=HEAD, line=None)
        text(s, 0.6, y + 0.06, 0.5, 0.4, str(k + 1), 15, WHITE, bold=True, align=PP_ALIGN.CENTER)
        text(s, 1.3, y + 0.04, 8.1, 0.5, step, 14.5, INK, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "Now I show the model in STELLA: first the MODEL layer, then the base run on the Interface layer, then "
             "three experiments with the sliders, and the table.")

    # 12 references
    s = deck.new_slide("References")
    refs = [r for r in C.REFERENCES if any(k in r for k in ("Ginters", "Hobbs", "MacNulty", "National Park Service. (20",
                                                            "Phillips", "Ripple", "Smith, D. W., Stahler", "White"))]
    tb = text(s, 0.55, 1.1, 8.9, 4.6, refs, 9.5, INK, after=4.5)
    for par in tb.text_frame.paragraphs:
        ppr = par._p.get_or_add_pPr()
        ppr.set("marL", str(int(Inches(0.3))))
        ppr.set("indent", str(-int(Inches(0.3))))
    text(s, 0.55, 5.85, 8.9, 0.45, C.AI_NOTE.replace("drafting the text", "drafting the text and the slides"), 9.5,
         GREY, italic=True)
    notes(s, "The sources, in APA 7 style.")

    draft = not all(used)
    if draft and not out.endswith("_DRAFT.pptx"):
        out = out[:-5] + "_DRAFT.pptx"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    deck.prs.save(out)
    print(f"written {os.path.normpath(out)}: {len(deck.prs.slides)} slides" + ("  (DRAFT: STELLA screenshots missing)" if draft else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shots", default=os.path.join(HERE, "..", "outputs", "stella-screenshots"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    have_all = all(os.path.exists(os.path.join(args.shots, n)) for n in C.SHOTS.values())
    out = args.out or os.path.join(HERE, "..", "outputs", "submission" if have_all else "draft", "VagifAsgarli-T4L.pptx")
    build(out, args.shots)


if __name__ == "__main__":
    main()
