"""Builds the T4LPrim presentation on the lecturer's template.

    python build_t4lprim_presentation.py [out.pptx]

The template (../materials/t4lprim_presentation-template.pptx) has three slides: title, Task, Example.
The title slide and the Task slide are kept (only the name is filled in), the Example slide is replaced
by the work itself: background, the Causal Loops Diagram, the reinforced and the balanced feedbacks,
the opinion about the stability of the ecosystem, references.

The diagram is drawn by ../../tools/cld_draw.py from yellowstone_cld.json.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))

from lecturer_deck import (BLUE, GREY, HEAD, INK, PALE, RED, RULE, WHITE, Deck, Inches, MSO_ANCHOR, MSO_SHAPE,  # noqa: E402
                           PP_ALIGN, RGBColor, box, line, notes, replace_text, text, text_width_in)

TEMPLATE = os.path.join(HERE, "..", "materials", "t4lprim_presentation-template.pptx")
FIGURE = os.path.join(HERE, "..", "outputs", "figures", "yellowstone_cld.png")
OUT = os.path.join(HERE, "..", "outputs", "submission", "VagifAsgarli-T4LPrim.pptx")
NAME = "Vagif Asgarli, 251ADM047"

LINK_BLUE = RGBColor(0x1F, 0x6F, 0xB2)      # the "+" arrows of the diagram
LINK_RED = RGBColor(0xB5, 0x12, 0x1B)       # the "-" arrows of the diagram

REFERENCES = [
    "Barber-Meyer, S. M., Mech, L. D., & White, P. J. (2008). Elk calf survival and mortality following wolf "
    "restoration to Yellowstone National Park. *Wildlife Monographs, 169*, 1–30. https://doi.org/10.2193/2008-004",
    "Beschta, R. L., & Ripple, W. J. (2016). Riparian vegetation recovery in Yellowstone: The first two decades "
    "after wolf reintroduction. *Biological Conservation, 198*, 93–103. https://doi.org/10.1016/j.biocon.2016.03.031",
    "Bilyeu, D. M., Cooper, D. J., & Hobbs, N. T. (2008). Water tables constrain height recovery of willow on "
    "Yellowstone's northern range. *Ecological Applications, 18*(1), 80–92. https://doi.org/10.1890/07-0212.1",
    "Cassidy, K. A., Stahler, D. R., Stahler, E. E., Metz, M., Rabe, J., SunderRaj, J., Rabe, T., Tatton, N., "
    "Packila, M., Cassidy, B., Binder, W., Lacey, C., Scott, G., & Ho, C. (2026). *Yellowstone National Park Wolf, "
    "Cougar, and Elk Project annual report 2025* (YCR-2026-01). National Park Service. "
    "https://www.nps.gov/yell/learn/upload/2025-YELL-Wolf-Cougar-Elk-Project-Annual-Report-508.pdf",
    "Cubaynes, S., MacNulty, D. R., Stahler, D. R., Quimby, K. A., Smith, D. W., & Coulson, T. (2014). "
    "Density-dependent intraspecific aggression regulates survival in northern Yellowstone wolves (*Canis lupus*). "
    "*Journal of Animal Ecology, 83*(6), 1344–1356. https://doi.org/10.1111/1365-2656.12238",
    "Ginters, E. (2026). *T4. Systems thinking and dynamics simulation* [Lecture slides]. Riga Technical University.",
    "Hobbs, N. T., Johnston, D. B., Marshall, K. N., Wolf, E. C., & Cooper, D. J. (2024). Does restoring apex "
    "predators to food webs restore ecosystems? Large carnivores in Yellowstone as a model system. *Ecological "
    "Monographs, 94*(2), Article e1598. https://doi.org/10.1002/ecm.1598",
    "MacNulty, D. R., Stahler, D. R., Wyman, T., Ruprecht, J., Smith, L. M., Kohl, M. T., & Smith, D. W. (2020). "
    "Population dynamics of northern Yellowstone elk after wolf reintroduction. In D. W. Smith, D. R. Stahler, & "
    "D. R. MacNulty (Eds.), *Yellowstone wolves: Science and discovery in the world's first national park* "
    "(pp. 184–199). University of Chicago Press.",
    "National Park Service. (n.d.). *Wolf management*. Yellowstone National Park. Retrieved November 26, 2026, "
    "from https://www.nps.gov/yell/learn/management/wolf.htm",
    "National Park Service. (2025a, April 18). *Beaver*. Yellowstone National Park. "
    "https://www.nps.gov/yell/learn/nature/beaver.htm",
    "National Park Service. (2025b, April 18). *Coyote*. Yellowstone National Park. "
    "https://www.nps.gov/yell/learn/nature/coyote.htm",
    "National Park Service. (2025c, April 18). *Elk*. Yellowstone National Park. "
    "https://www.nps.gov/yell/learn/nature/elk.htm",
    "National Park Service. (2025d, September 9). *History of wolf management*. Yellowstone National Park. "
    "https://www.nps.gov/yell/learn/historyculture/wolf-management.htm",
    "National Park Service. (2026, September 9). *Wolf ecology*. Yellowstone National Park. "
    "https://www.nps.gov/yell/learn/nature/wolf.htm",
    "Phillips, M. K., & Smith, D. W. (1997). *Yellowstone Wolf Project: Biennial report 1995 and 1996* "
    "(YCR-NR-97-4). National Park Service. https://www.nps.gov/yell/learn/nature/upload/wolfreport_95-96_508.pdf",
    "Ripple, W. J., & Beschta, R. L. (2012). Trophic cascades in Yellowstone: The first 15 years after wolf "
    "reintroduction. *Biological Conservation, 145*(1), 205–213. https://doi.org/10.1016/j.biocon.2011.11.005",
    "Smith, D., Stahler, D., Albers, E., McIntyre, R., Metz, M., Irving, J., Raymond, R., Anton, C., "
    "Cassidy-Quimby, K., & Bowersock, N. (2011). *Yellowstone Wolf Project: Annual report, 2010* (YCR-2011-06). "
    "National Park Service. https://www.nps.gov/yell/learn/nature/upload/wolf_ar_2010.pdf",
    "Smith, D. W., Stahler, D. R., & Guernsey, D. S. (2004). *Yellowstone Wolf Project: Annual report, 2003* "
    "(YCR-NR-2004-04). National Park Service. https://www.nps.gov/yell/learn/nature/upload/wolfrpt03.pdf",
    "White, P. J., Stahler, D. R., Smith, D. W., MacNulty, D. R., & Garrott, R. A. (2024). *Northern Yellowstone "
    "elk: Resilience and adaptation to changes in management policies and the ecosystem*. National Park Service. "
    "https://www.nps.gov/yell/learn/nature/upload/ELK-BOOK-FOR-WEB_accessible.pdf",
]
AI_NOTE = ("Note. Generative AI tools were used for information retrieval, for drawing the diagram, for drafting "
           "the text and for formatting the reference list: Claude (Anthropic).")


def title_slide(deck):
    s = deck.title_slide
    name = {sh.name: sh for sh in s.shapes}["Rectangle 8"]
    replace_text(name, NAME)
    notes(s, "Good afternoon. This is my T4LPrim work: a Causal Loops Diagram of the processes in Yellowstone "
             "nature, with the reinforced and balanced feedbacks marked, and my opinion about the stability of "
             "the ecosystem.")


def task_slide(deck):
    notes(deck.content_slide, "The task has three parts: design the Causal Loops Diagram of Yellowstone, mark the "
                              "reinforced and the balanced feedbacks, and justify an opinion about stability.")


def background_slide(deck):
    s = deck.new_slide("Yellowstone: what happened")
    text(s, 0.55, 1.15, 8.9, 0.75,
         "People removed the top predator and later brought it back, so the park shows how one variable moves "
         "the whole ecosystem.", 16)
    cards = [
        ("1914–1926", "at least 136 wolves killed in the park; a survey in the 1970s found no wolf population",
         "(National Park Service [NPS], 2025d)"),
        ("by 1995", "about 17,000 deers (elk) on the northern range; young willow and aspen eaten down; one "
                    "beaver colony left in 1996", "(NPS, 2025c; Ripple & Beschta, 2012)"),
        ("1995–1996", "31 wolves from Canada released; 174 wolves by 2003, between 83 and 123 since 2009",
         "(Phillips & Smith, 1997; Smith et al., 2004; NPS, 2026)"),
        ("today", "5,600–7,200 deers counted in 2024–2025; 18 beaver colonies by 2015; willow and aspen taller "
                  "in many places", "(Cassidy et al., 2026; Beschta & Ripple, 2016)"),
    ]
    for k, (when, what, cite) in enumerate(cards):
        x = 0.5 + k * 2.28
        box(s, x, 2.1, 2.14, 3.55, fill=WHITE, line=RULE)
        box(s, x, 2.1, 2.14, 0.5, fill=HEAD, line=None)
        text(s, x, 2.15, 2.14, 0.42, when, 15, WHITE, bold=True, align=PP_ALIGN.CENTER)
        text(s, x + 0.1, 2.75, 1.94, 1.9, what, 13.5, INK, align=PP_ALIGN.LEFT, spacing=1.0)
        text(s, x + 0.1, 4.75, 1.94, 0.85, cite, 10.5, GREY, italic=True, anchor=MSO_ANCHOR.BOTTOM)
    for k in range(3):
        x = 0.5 + (k + 1) * 2.28 - 0.14
        line(s, x, 3.85, x + 0.14, 3.85, color=HEAD, width=1.5, arrow=True)
    text(s, 0.55, 5.8, 8.9, 0.45,
         "In the diagram the lecturer's “Deers” are the elk (wapiti), the largest deer of the park and the main "
         "prey of the wolves.", 12.5, GREY, italic=True)
    notes(s, "Why Yellowstone. Between 1914 and 1926 at least 136 wolves were killed and by the 1970s no wolf "
             "population was left. Without wolves the elk, which are the deers of the task, reached about 17,000 "
             "on the northern range and browsed the young willow and aspen; in 1996 only one beaver colony was "
             "found there. In 1995 and 1996, 31 wolves were released. Wolves peaked at 174 in 2003 and have been "
             "between 83 and 123 since 2009. The deers went down to about 6,000 to 7,000, beaver colonies rose to "
             "18 by 2015 and willow and aspen grew taller in many places.")


def diagram_slide(deck):
    s = deck.new_slide("Causal Loops Diagram of Yellowstone")
    pic_w = 9.3
    s.shapes.add_picture(FIGURE, Inches(0.35), Inches(1.0), width=Inches(pic_w))
    y = 6.02
    legend = [("+", LINK_BLUE, "same direction"), ("−", LINK_RED, "opposite direction"), ("||", INK, "delay"),
              ("R", LINK_BLUE, "reinforced feedback"), ("B", LINK_RED, "balanced feedback"),
              ("italics", GREY, "outside influence")]
    x = 0.45
    for sym, colour, meaning in legend:
        wsym = text_width_in(sym, 13) + 0.1
        text(s, x, y, wsym, 0.3, sym, 13, colour, bold=sym != "italics", italic=sym == "italics", margin=0.0)
        wmean = text_width_in(meaning, 11) * 0.93 + 0.12
        text(s, x + wsym, y + 0.02, wmean, 0.3, meaning, 11, GREY, margin=0.0)
        x += wsym + wmean + 0.12
    notes(s, "This is my diagram. A blue arrow with a plus means the two variables change in the same direction, "
             "a red arrow with a minus means the opposite direction, two strokes mean a delay. In the middle are "
             "the wolves and the deers. On the right the deers eat the vegetation, and the vegetation, the beavers "
             "and the water table support each other. On the left are the effects of wolves on coyotes and on "
             "scavengers. Winter severity and bears and cougars are outside influences. There are three reinforced "
             "and four balanced feedbacks.")


def loop_rows(s, rows, top, row_h):
    """rows: (tag, chain, meaning).  The chain uses (+) and (-) which are coloured like the arrows."""
    for k, (tag, chain, meaning) in enumerate(rows):
        y = top + k * row_h
        colour = LINK_BLUE if tag.startswith("R") else LINK_RED
        if k:
            line(s, 0.55, y - 0.07, 9.45, y - 0.07, color=RULE, width=0.75)
        circ = box(s, 0.55, y + 0.05, 0.56, 0.56, fill=WHITE, line=colour, width=2.0, shape=MSO_SHAPE.OVAL)
        tf = circ.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        par = tf.paragraphs[0]
        par.alignment = PP_ALIGN.CENTER
        run = par.add_run()
        run.text = tag
        run.font.size, run.font.bold, run.font.name = Inches(0.17), True, "Arial"
        run.font.color.rgb = INK
        tb = s.shapes.add_textbox(Inches(1.25), Inches(y), Inches(8.2), Inches(0.36))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.04)
        tf.margin_top = tf.margin_bottom = Inches(0.02)
        par = tf.paragraphs[0]
        for piece in chain.replace("(+)", "|+|").replace("(-)", "|-|").split("|"):
            if not piece:
                continue
            run = par.add_run()
            run.font.name, run.font.size, run.font.bold = "Arial", Inches(14.5 / 72), True
            if piece == "+":
                run.text, run.font.color.rgb = " + → ", LINK_BLUE
            elif piece == "-":
                run.text, run.font.color.rgb = " − → ", LINK_RED
            else:
                run.text, run.font.color.rgb = piece.strip(), INK
        text(s, 1.25, y + 0.36, 8.2, row_h - 0.45, meaning, 12.5, INK, spacing=1.0)


def reinforced_slide(deck):
    s = deck.new_slide("Reinforced feedbacks")
    text(s, 0.55, 1.1, 8.9, 0.6,
         "A reinforced feedback [[compounds a change]] in one direction (Ginters, 2026): no minus link in the "
         "loop, so growth feeds growth and decline feeds decline.", 14.5)
    rows = [
        ("R1", "Wolves (+) Wolf births (+) Wolves",
         "More wolves raise more pups: a litter has five pups on average (NPS, 2026). From 31 released wolves "
         "the park had 174 in 2003 (Smith et al., 2004)."),
        ("R2", "Deers (+) Deer births (+) Deers",
         "More deers give birth to more calves. After the culling in the park had ended, the herd grew from "
         "about 4,300 in 1969 to about 12,600 in 1975 (White et al., 2024)."),
        ("R3", "Vegetation (+) Beavers (+) Beaver ponds, water table (+) Vegetation",
         "Tall willow feeds beavers; their ponds raise the water table, which lets willow grow (NPS, 2025a; "
         "Bilyeu et al., 2008). It works both ways: little willow, few beavers, drier banks, even less willow."),
    ]
    loop_rows(s, rows, 1.95, 1.3)
    box(s, 0.55, 5.82, 0.07, 0.42, fill=HEAD, line=None)
    text(s, 0.75, 5.8, 8.7, 0.5, "A reinforced loop alone would never stop: each one must be held by a balanced loop.",
         13.5, INK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "Three reinforced feedbacks. R1: more wolves, more wolf births, more wolves. R2: the same for the "
             "deers. R3 is the most interesting one: willow and aspen feed the beavers, the beaver ponds raise the "
             "water table, and wet banks let more willow grow. It also works in the bad direction, which is what "
             "happened when the wolves were gone. A reinforced loop alone would grow or collapse without limit, "
             "so each of them must be balanced.")


def balanced_slide(deck):
    s = deck.new_slide("Balanced feedbacks")
    text(s, 0.55, 1.1, 8.9, 0.6,
         "A balanced feedback [[opposes a change]] and keeps the system near a level (Ginters, 2026): an odd "
         "number of minus links in the loop.", 14.5)
    rows = [
        ("B1", "Deers (+) Wolf births (+) Wolves (-) Deers",
         "Predator and prey. A wolf kills 18–22 deers a year (NPS, 2026); when the deers fell, the wolves fell "
         "43% from 2007 to 2010 (Smith et al., 2011). The delay makes both go up and down."),
        ("B2", "Wolves (+) Pack fights, diseases (-) Wolves",
         "Crowded packs fight: 42% of adult wolf deaths in the park are caused by other wolves (NPS, 2026; "
         "Cubaynes et al., 2014)."),
        ("B3", "Deers (-) Vegetation (+) Deer births (+) Deers",
         "Too many deers eat their own food. In 1998 all measured leaders of young aspen were browsed, by 2010 "
         "under 25%, after the herd had shrunk (Ripple & Beschta, 2012)."),
        ("B4", "Deers (+) Hunting permits (-) Deers",
         "People follow the herd: permits for the late hunt went from 2,882 in 2000 to 140 in 2006 and to none "
         "by 2010 (White et al., 2024)."),
    ]
    loop_rows(s, rows, 1.85, 1.07)
    notes(s, "Four balanced feedbacks. B1 is the predator and prey loop: more deers feed more wolves, more wolves "
             "kill more deers; because the wolves react with a delay, both populations swing. B2 limits the wolves "
             "themselves through fights between packs and diseases. B3 is the food limit of the deers. B4 is the "
             "human one: the more deers, the more hunting permits; the permits were cut when the herd fell.")


def cascade_slide(deck):
    s = deck.new_slide("Chains and outside influences")
    text(s, 0.55, 1.15, 8.9, 0.5, "Not every arrow belongs to a loop: some carry an effect through the ecosystem.", 14.5)
    rows = [
        ("Trophic cascade", "Wolves (-) Deers (-) Vegetation (+) Beavers",
         "Two minus links in a row give a plus: more wolves, fewer deers, more vegetation. This is how the wolves "
         "reach R3 (Ripple & Beschta, 2012)."),
        ("Coyotes", "Wolves (-) Coyotes",
         "After the wolves returned, the coyotes of the northern range decreased by as much as 50% (NPS, 2025b)."),
        ("Scavengers", "Wolves (+) Carcasses (+) Scavengers",
         "Wolf kills benefit a variety of scavengers, ravens among them (NPS, n.d., 2025d); deer carcasses feed "
         "bears and at least 12 scavenger species, including bald eagles (NPS, 2025c)."),
        ("Outside", "Winter severity (-) Deers;   Bears, cougars (-) Deers",
         "3,000–5,800 deers starved in the winter of 1989 (White et al., 2024); bears caused 58–60% of the calf "
         "deaths in 2003–2005 (Barber-Meyer et al., 2008)."),
    ]
    top, row_h = 1.8, 1.08
    for k, (tag, chain, meaning) in enumerate(rows):
        y = top + k * row_h
        if k:
            line(s, 0.55, y - 0.07, 9.45, y - 0.07, color=RULE, width=0.75)
        text(s, 0.55, y + 0.02, 1.6, 0.6, tag, 13, HEAD, bold=True)
        tb = s.shapes.add_textbox(Inches(2.15), Inches(y), Inches(7.3), Inches(0.36))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.04)
        tf.margin_top = tf.margin_bottom = Inches(0.02)
        par = tf.paragraphs[0]
        for piece in chain.replace("(+)", "|+|").replace("(-)", "|-|").split("|"):
            if not piece:
                continue
            run = par.add_run()
            run.font.name, run.font.size, run.font.bold = "Arial", Inches(14 / 72), True
            if piece == "+":
                run.text, run.font.color.rgb = " + → ", LINK_BLUE
            elif piece == "-":
                run.text, run.font.color.rgb = " − → ", LINK_RED
            else:
                run.text, run.font.color.rgb = piece.strip() if ";" not in piece else piece.strip().replace(";", ";   "), INK
        text(s, 2.15, y + 0.36, 7.3, row_h - 0.45, meaning, 12.5, INK, spacing=1.0)
    notes(s, "Some arrows are chains, not loops. The most famous is the trophic cascade: wolves reduce the deers, "
             "fewer deers eat less vegetation, so more wolves mean more vegetation and, through it, more beavers. "
             "Wolves also reduce coyotes and feed scavengers with carcasses. Winter severity and bears and cougars "
             "act on the deers from outside the loops.")


def stability_slide(deck):
    s = deck.new_slide("Ecosystem stability: my opinion")
    box(s, 0.55, 1.12, 8.9, 0.92, fill=PALE, line=None)
    box(s, 0.55, 1.12, 0.07, 0.92, fill=HEAD, line=None)
    text(s, 0.78, 1.15, 8.55, 0.86,
         "The ecosystem is [[stable]] as long as its balanced feedbacks work: with the wolves it returns to a "
         "balance after a disturbance; it is a moving balance, not a fixed state.", 15, INK, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    points = [
        "**Every reinforced loop is held.** R1 by B1 and B2; R2 by B1, B3 and B4; R3 by B3. The lecture rule is "
        "met: reinforced loops must be balanced, otherwise the system is unstable (Ginters, 2026).",
        "**Without wolves B1 was missing.** The deers were limited only by food, winters and hunters, the "
        "vegetation was eaten down and R3 turned the wrong way: one beaver colony in 1996 (Ripple & Beschta, 2012). "
        "Stable, but in a poor state.",
        "**With wolves the swings die out.** Wolves 174 in 2003, then 83–123 since 2009 (NPS, 2026); deers "
        "from 17,000 in 1995 to 5,600–7,200 in 2024–2025 (Cassidy et al., 2026). The delays cause the overshoot, "
        "the balanced loops damp it.",
        "**Limits of this opinion.** Hunters, winters and bears also moved the herd (MacNulty et al., 2020). "
        "Along small streams willow reached its full height only where dams raised the water and browsing was "
        "reduced, which points to a second stable state (Hobbs et al., 2024).",
    ]
    text(s, 0.55, 2.25, 8.9, 3.9, points, 14, INK, bullet=True, after=9, spacing=1.0)
    notes(s, "My opinion: the ecosystem is stable as long as its balanced feedbacks work. First, each reinforced "
             "loop has a balanced loop that holds it. Second, when the wolves were removed, the predator and prey "
             "loop B1 was missing; the system was still stable, but in a poor state with many deers, little "
             "willow and almost no beavers. Third, after the wolves returned, the counts show swings that die "
             "out: that is how a stable system with delays behaves. Fourth, I am careful: hunters, winters and "
             "bears also changed the herd, and in some places the willow has not recovered, so the ecosystem has "
             "more than one stable state.")


def reference_slides(deck):
    per_slide = (len(REFERENCES) + 1) // 2
    parts = [REFERENCES[:per_slide], REFERENCES[per_slide:]]
    for k, part in enumerate(parts):
        s = deck.new_slide(f"References ({k + 1}/{len(parts)})")
        tb = text(s, 0.55, 1.1, 8.9, 4.9, part, 9.5, INK, after=4.5, spacing=1.0)
        for par in tb.text_frame.paragraphs:
            ppr = par._p.get_or_add_pPr()
            ppr.set("marL", str(int(Inches(0.3))))
            ppr.set("indent", str(-int(Inches(0.3))))
        if k == len(parts) - 1:
            text(s, 0.55, 5.75, 8.9, 0.5, AI_NOTE, 9.5, GREY, italic=True)
        notes(s, "The sources, in APA 7 style.")


def build(out=OUT):
    deck = Deck(TEMPLATE)
    prs = deck.prs
    # remove the template's Example slide (the third one)
    sld_ids = prs.slides._sldIdLst
    example = sld_ids[2]
    prs.part.drop_rel(example.rId)
    sld_ids.remove(example)
    title_slide(deck)
    task_slide(deck)
    background_slide(deck)
    diagram_slide(deck)
    reinforced_slide(deck)
    balanced_slide(deck)
    cascade_slide(deck)
    stability_slide(deck)
    reference_slides(deck)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    prs.save(out)
    print(f"written {os.path.normpath(out)}: {len(prs.slides)} slides")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else OUT)
