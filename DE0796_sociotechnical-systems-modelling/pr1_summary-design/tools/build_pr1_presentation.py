"""Builds the PR1 presentation on the lecturer's own slide design.

The course gives no presentation template for PR1, so the deck starts from the lecturer's T5L template
(../../t5l_conceptual-modelling-bpmn2/materials/t5l_presentation-template.pptx): its title slide (RTU logo,
faculty lines, course name, work title, name) and its content slide (red heading with a line under it,
"RTU 2026" footer, slide number) are reused unchanged; only the texts are replaced and the body is filled.

The content follows the five paragraphs of the summary (build_pr1.py) and uses the same facts and the same
APA 7 references, nothing else.

    python build_pr1_presentation.py [template.pptx] [out.pptx]

Text markup used below:  [[...]] red italics (the lecturer's way of stressing a term), **...** bold, *...* italics.
"""
import copy
import os
import re
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "..", "t5l_conceptual-modelling-bpmn2", "materials",
                        "t5l_presentation-template.pptx")
OUT = os.path.join(HERE, "..", "outputs", "submission", "VagifAsgarli-PR1-presentation.pptx")

NAME = "Vagif Asgarli, 251ADM047"
WORK = "PR1: Summary Design"
TOPIC = ["Application of BPMN 2.0 Diagrams in", "Modelling Cybersecurity Procedures"]

RED = RGBColor(0xC0, 0x00, 0x00)        # the lecturer's emphasis colour
HEAD = RGBColor(0x94, 0x36, 0x34)       # heading colour of the template (accent 2, 25% darker)
BLUE = RGBColor(0x36, 0x5F, 0x91)       # footer colour of the template (accent 1, 25% darker)
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x59, 0x59, 0x59)
RULE = RGBColor(0xBF, 0xBF, 0xBF)
PALE = RGBColor(0xF6, 0xF1, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"

REFERENCES = [
    "Akbari Gurabi, M., Nitz, L., Bregar, A., Popanda, J., Siemers, C., Matzutt, R., & Mandal, A. (2024). "
    "Requirements for playbook-assisted cyber incident response, reporting and automation. *Digital Threats: "
    "Research and Practice, 5*(3), Article 34. https://doi.org/10.1145/3688810",
    "CERT.LV. (2026). *Latvijas kiberdrošības un CERT.LV tehnisko aktivitāšu 2025. gada pārskats* [Report on "
    "Latvian cybersecurity and CERT.LV technical activities in 2025]. "
    "https://cert.lv/lv/2026/09/latvijas-kiberdrosibas-un-cert-lv-tehnisko-aktivitasu-2025-gada-parskats",
    "Directive (EU) 2022/2555 of the European Parliament and of the Council of 14 December 2022 on measures for a "
    "high common level of cybersecurity across the Union (NIS 2 Directive). (2022). *Official Journal of the "
    "European Union, L 333*, 80–152. https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
    "European Union Agency for Cybersecurity. (2026). *ENISA threat landscape 2026*. "
    "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2026",
    "Hornsteiner, M., Stoiber, C., & Schönig, S. (2022). Towards security- and IIoT-aware BPMN: A systematic "
    "literature review. In *Proceedings of the 19th International Conference on Smart Business Technologies* "
    "(pp. 45–56). SciTePress. https://doi.org/10.5220/0011317700003280",
    "IBM. (2026). *Cost of a data breach report 2026*. https://www.ibm.com/reports/data-breach",
    "Jordan, B., & Thomson, A. (Eds.). (2023). *CACAO security playbooks version 2.0* (OASIS Committee "
    "Specification 01). OASIS Open. "
    "https://docs.oasis-open.org/cacao/security-playbooks/v2.0/cs01/security-playbooks-v2.0-cs01.html",
    "Nacionālās kiberdrošības likums [National Cybersecurity Law]. (2024). *Latvijas Vēstnesis*, 128A. "
    "https://likumi.lv/ta/id/353390",
    "Nelson, A., Rekhi, S., Souppaya, M., & Scarfone, K. (2025). *Incident response recommendations and "
    "considerations for cybersecurity risk management: A CSF 2.0 community profile* (NIST Special Publication "
    "800-61r3). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-61r3",
    "Object Management Group. (2011). *Business Process Model and Notation (BPMN), version 2.0* (OMG Document "
    "formal/2011-01-03). https://www.omg.org/spec/BPMN/2.0/PDF",
    "Ottensooser, A., Fekete, A., Reijers, H. A., Mendling, J., & Menictas, C. (2012). Making sense of business "
    "process descriptions: An experimental comparison of graphical and textual notations. *Journal of Systems and "
    "Software, 85*(3), 596–606. https://doi.org/10.1016/j.jss.2011.09.023",
    "Salnitri, M., Dalpiaz, F., & Giorgini, P. (2017). Designing secure business processes with SecBPMN. "
    "*Software & Systems Modeling, 16*(3), 737–757. https://doi.org/10.1007/s10270-015-0499-4",
    "Schlette, D., Empl, P., Caselli, M., Schreck, T., & Pernul, G. (2024). Do you play it by the books? A study "
    "on incident response playbooks and influencing factors. In *2024 IEEE Symposium on Security and Privacy (SP)* "
    "(pp. 3625–3643). IEEE. https://doi.org/10.1109/SP54263.2024.00060",
    "Stevens, R., Votipka, D., Dykstra, J., Tomlinson, F., Quartararo, E., Ahern, C., & Mazurek, M. L. (2022). How "
    "ready is your ready? Assessing the usability of incident response playbook frameworks. In *CHI Conference on "
    "Human Factors in Computing Systems* (pp. 1–18). ACM. https://doi.org/10.1145/3491102.3517559",
    "Zych, M., Mavroeidis, V., Fysarakis, K., & Athanatos, M. (2023). Reviewing BPMN as a modeling notation for "
    "CACAO security playbooks. In *2023 IEEE International Conference on Cyber Security and Resilience (CSR)* "
    "(pp. 490–495). IEEE. https://doi.org/10.1109/CSR57506.2023.10224922",
]
AI_NOTE = ("Note. Generative AI tools were used for information retrieval, drafting of the text and the slides, "
           "and formatting the reference list: Claude (Anthropic).")

MARK = re.compile(r"(\[\[.+?\]\]|\*\*.+?\*\*|\*.+?\*)")

# Metric-compatible stand-ins for Arial Bold and Calibri Bold, used only to measure a line of text.
MEASURE_FONTS = {"Arial": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                 "Calibri": "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"}


def text_width_in(words, size_pt, family="Arial"):
    """Width of one line of bold text in inches (falls back to an average character width)."""
    try:
        from PIL import ImageFont
        return ImageFont.truetype(MEASURE_FONTS[family], 200).getlength(words) / 200 * size_pt / 72
    except Exception:
        return 0.6 * size_pt / 72 * len(words)


# ----------------------------------------------------------------------------------------------- text helpers
def add_runs(par, text, size, color=INK, bold=False, italic=False, font=FONT):
    for piece in MARK.split(text):
        if not piece:
            continue
        b, i, c = bold, italic, color
        if piece.startswith("[["):
            piece, i, c = piece[2:-2], True, RED
        elif piece.startswith("**"):
            piece, b = piece[2:-2], True
        elif piece.startswith("*"):
            piece, i = piece[1:-1], True
        run = par.add_run()
        run.text = piece
        run.font.name, run.font.size, run.font.bold, run.font.italic = font, Pt(size), b, i
        run.font.color.rgb = c


def set_bullet(par, char="q", font="Wingdings", indent_in=0.3, color="943634"):
    ppr = par._p.get_or_add_pPr()
    ppr.set("marL", str(int(Inches(indent_in))))
    ppr.set("indent", str(-int(Inches(indent_in))))
    for tag in ("a:buClr", "a:buFont", "a:buChar", "a:buNone"):
        for old in ppr.findall(qn(tag)):
            ppr.remove(old)
    clr = ppr.makeelement(qn("a:buClr"), {})
    clr.append(clr.makeelement(qn("a:srgbClr"), {"val": color}))
    ppr.append(clr)
    ppr.append(ppr.makeelement(qn("a:buFont"), {"typeface": font, "pitchFamily": "2", "charset": "2"}))
    ppr.append(ppr.makeelement(qn("a:buChar"), {"char": char}))


def text(slide, x, y, w, h, paras, size=15, color=INK, bold=False, italic=False, align=None,
         anchor=MSO_ANCHOR.TOP, after=6, spacing=1.0, bullet=False, margin=0.04):
    """A text box; `paras` is a string or a list of strings (one paragraph each)."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    if isinstance(paras, str):
        paras = [paras]
    for k, ptext in enumerate(paras):
        par = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        if align is not None:
            par.alignment = align
        par.space_after = Pt(after)
        par.line_spacing = spacing
        add_runs(par, ptext, size, color, bold, italic)
        if bullet:
            set_bullet(par)
    return box


def box(slide, x, y, w, h, fill=None, line=RULE, width=0.75, shape=MSO_SHAPE.RECTANGLE):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(width)
    return shp


def line(slide, x1, y1, x2, y2, color=INK, width=1.5, dash=False, arrow=False):
    con = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    con.line.color.rgb = color
    con.line.width = Pt(width)
    ln = con.line._get_or_add_ln()
    if dash:
        ln.append(ln.makeelement(qn("a:prstDash"), {"val": "dash"}))
    if arrow:
        ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return con


def notes(slide, words):
    slide.notes_slide.notes_text_frame.text = words


# ----------------------------------------------------------------------------------------- template handling
def replace_text(shape, new_text):
    """Keeps the formatting of the first run of the shape and replaces the whole text."""
    par = shape.text_frame.paragraphs[0]
    runs = par.runs
    runs[0].text = new_text
    for extra in runs[1:]:
        par._p.remove(extra._r)
    for other in shape.text_frame.paragraphs[1:]:
        other._p.getparent().remove(other._p)


class Deck:
    def __init__(self, template):
        self.prs = Presentation(template)
        self.title_slide, self.content_slide = self.prs.slides[0], self.prs.slides[1]
        by_name = {s.name: s for s in self.content_slide.shapes}
        # the fixed parts of the lecturer's content slide: heading, line under it, footer, slide number
        self.chrome = [copy.deepcopy(by_name[n]._element) for n in
                       ("Rectangle 6", "Straight Connector 13", "Rectangle 1", "Slide Number Placeholder 10")]
        self.layout = self.content_slide.slide_layout

    def new_slide(self, heading):
        slide = self.prs.slides.add_slide(self.layout)
        for ph in list(slide.placeholders):
            ph._element.getparent().remove(ph._element)
        for el in self.chrome:
            slide.shapes._spTree.append(copy.deepcopy(el))
        self.set_heading(slide, heading)
        return slide

    @staticmethod
    def set_heading(slide, heading):
        by_name = {s.name: s for s in slide.shapes}
        head = by_name["Rectangle 6"]
        replace_text(head, heading)
        head.width = Inches(text_width_in(heading, 24) + 0.2)        # 0.1 in inset on each side
        # the template line is 4.0 in long; lengthen it when the heading is longer than that
        rule = by_name["Straight Connector 13"]
        need = head.left + head.width + Inches(0.35) - rule.left
        if need > rule.width:
            rule.width = Emu(int(need))


# ------------------------------------------------------------------------------------------------- the slides
def title_slide(deck):
    s = deck.title_slide
    by_name = {sh.name: sh for sh in s.shapes}
    work = by_name["Rectangle 7"]
    replace_text(work, WORK)
    work.left, work.width = Inches(1.0), Inches(8.0)
    work.top = Inches(4.2)
    # the topic, in the type of the course name above it
    tb = s.shapes.add_textbox(Inches(0.75), Inches(4.85), Inches(8.5), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    for k, row in enumerate(TOPIC):
        par = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        par.alignment = PP_ALIGN.CENTER
        add_runs(par, row, 20, INK, bold=True, font="Times New Roman")
    name = by_name["Rectangle 8"]
    replace_text(name, NAME)
    name.width = Inches(text_width_in(NAME, 18, "Calibri") + 0.2)
    name.left, name.top = Inches(8.35) - name.width, Inches(5.85)
    notes(s, "Good afternoon. My topic for PR1 is the application of BPMN 2.0 diagrams in modelling "
             "cybersecurity procedures. I will go through the summary in the order of its five paragraphs.")


def outline_slide(deck):
    s = deck.content_slide
    body = {sh.name: sh for sh in s.shapes}["Rectangle 7"]
    tx = body._element.find(qn("p:txBody"))
    first = tx.findall(qn("a:p"))[0]
    ppr = copy.deepcopy(first.find(qn("a:pPr")))          # the lecturer's bullet (hollow square)
    lead = copy.deepcopy(first.findall(qn("a:r"))[0])     # his run of spaces after the bullet
    for p in tx.findall(qn("a:p")):
        tx.remove(p)
    items = ["[[Relevance]] of the topic", "[[Problem]] identification and [[existing solutions]]",
             "[[Aim]], [[tasks]], and [[methods]]", "Expected [[results]] and [[target audience]]",
             "[[Further development]]", "References"]
    tf = body.text_frame
    for item in items:
        p = tx.makeelement(qn("a:p"), {})
        p.append(copy.deepcopy(ppr))
        p.append(copy.deepcopy(lead))
        tx.append(p)
        par = tf.paragraphs[-1]
        par.space_after = Pt(14)
        add_runs(par, item, 24)
    body.top = Inches(1.45)
    notes(s, "The structure is the one required for the summary: relevance, the problem with three existing "
             "solutions, my aim, tasks and methods, the expected results and their users, and further development.")


def relevance_slide(deck):
    s = deck.new_slide("Relevance of the topic")
    text(s, 0.55, 1.2, 8.9, 0.7,
         "Cyber incidents have become [[frequent and costly]], so the procedures that an organisation follows "
         "when an incident occurs matter at every level.", 16)
    cards = [
        ("GLOBAL", "USD 4.99 million", "average cost of a data breach in 2026: a record, 12% more than a year "
                                        "earlier", "(IBM, 2026)"),
        ("EUROPE", "8,257 incidents", "recorded in 2025 and analysed by ENISA; 72.9% of them affected "
                                      "essential entities", "(ENISA, 2026)"),
        ("LATVIA", "2,982 incidents", "processed manually by CERT.LV in 2025, 28% more than in 2024",
         "(CERT.LV, 2026)"),
    ]
    for k, (level, figure, what, cite) in enumerate(cards):
        x = 0.55 + k * 3.03
        box(s, x, 2.15, 2.84, 3.0, fill=WHITE, line=RULE)
        box(s, x, 2.15, 2.84, 0.46, fill=HEAD, line=None)
        text(s, x, 2.19, 2.84, 0.4, level, 14, WHITE, bold=True, align=PP_ALIGN.CENTER)
        text(s, x + 0.08, 2.82, 2.68, 0.6, figure, 22, RED, bold=True, align=PP_ALIGN.CENTER)
        text(s, x + 0.15, 3.5, 2.54, 1.1, what, 14, INK, align=PP_ALIGN.CENTER)
        text(s, x + 0.15, 4.65, 2.54, 0.4, cite, 13, GREY, italic=True, align=PP_ALIGN.CENTER)
    text(s, 0.55, 5.4, 8.9, 0.8,
         "The global cost and the Latvian incident count are both rising, and in Europe most of the analysed "
         "incidents hit [[essential entities]].", 15)
    notes(s, "Why the topic matters at three levels. Globally the average breach cost is a record 4.99 million "
             "dollars, 12 per cent up in a year (IBM, 2026). In Europe ENISA analysed 8,257 incidents of 2025 and "
             "72.9 per cent affected essential entities. In Latvia CERT.LV handled 2,982 incidents manually, "
             "28 per cent more than in 2024.")


def deadlines_slide(deck):
    s = deck.new_slide("Relevance: legal deadlines")
    text(s, 0.55, 1.2, 8.9, 0.95,
         "The [[NIS2 Directive]] obliges essential entities to have incident handling in place and to report a "
         "significant incident in three steps (Directive 2022/2555, 2022).", 16)
    y = 3.35
    line(s, 1.0, y, 9.0, y, color=GREY, width=2.25)
    stops = [(1.35, "Significant\nincident", "start", GREY), (3.55, "24 hours", "early warning", RED),
             (6.0, "72 hours", "notification", RED), (8.45, "one month", "final report", RED)]
    for x, top, bottom, colour in stops:
        dot = box(s, x - 0.16, y - 0.16, 0.32, 0.32, fill=colour, line=WHITE, width=1.5, shape=MSO_SHAPE.OVAL)
        big = "\n" not in top
        text(s, x - 1.1, y - (0.75 if big else 0.85), 2.2, 0.6, top.split("\n"), 20 if big else 14,
             colour if big else GREY, bold=True, align=PP_ALIGN.CENTER, after=0)
        text(s, x - 1.1, y + 0.25, 2.2, 0.4, bottom, 15, INK, align=PP_ALIGN.CENTER)
    text(s, 0.55, 4.45, 8.9, 0.95,
         "[[Latvia]]: the same deadlines apply under the National Cybersecurity Law, in force since "
         "1\u00a0September\u00a02024 (Nacionālās kiberdrošības likums, 2024).", 16)
    bar = box(s, 0.55, 5.5, 0.08, 0.7, fill=HEAD, line=None)
    text(s, 0.75, 5.5, 8.7, 0.7,
         "Such deadlines can be met only with procedures that every participant understands alike.", 16,
         INK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "The legal side. NIS2 requires incident handling and three reports on a significant incident: an "
             "early warning within 24 hours, a notification within 72 hours and a final report within one month. "
             "Latvia applies the same deadlines through the National Cybersecurity Law, in force since "
             "1 September 2024. With such deadlines there is no time to argue about what the procedure means.")


def problem_slide(deck):
    s = deck.new_slide("Problem identification")
    text(s, 0.55, 1.2, 8.9, 1.0,
         "Incident-handling procedures ([[playbooks]]) are still written mostly as [[prose]] or as "
         "[[vendor-specific code]], which makes them ambiguous and hard to verify, share and automate.", 16)
    tiles = [
        ("76.7%", "of the practitioners' playbooks were text-based, and the public ones could not be used "
                  "outright because of missing or obsolete information",
         "Study of 1,217 public playbooks and 147 practitioners (Schlette et al., 2024)"),
        ("11 of 24", "playbooks written with two standard frameworks were judged by experts as insufficiently "
                     "detailed for real use", "Experiment with experts (Stevens et al., 2022)"),
    ]
    for k, (figure, what, cite) in enumerate(tiles):
        x = 0.55 + k * 4.55
        box(s, x, 2.45, 4.35, 3.35, fill=PALE, line=None)
        box(s, x, 2.45, 0.08, 3.35, fill=HEAD, line=None)
        text(s, x + 0.3, 2.6, 3.9, 0.8, figure, 36, RED, bold=True)
        text(s, x + 0.3, 3.45, 3.85, 1.45, what, 15, INK)
        text(s, x + 0.3, 4.95, 3.85, 0.7, cite, 13, GREY, italic=True)
    notes(s, "The main problem: playbooks are mostly prose or vendor-specific code. Schlette and colleagues "
             "studied 1,217 public playbooks and asked 147 practitioners: 76.7 per cent of the practitioners' "
             "playbooks were text, and the public ones could not be used as they are. Stevens and colleagues "
             "found that experts judged 11 of 24 playbooks written with two standard frameworks as not detailed "
             "enough for real use.")


def solutions_slide(deck):
    s = deck.new_slide("Existing solutions")
    rows = [
        ("Solution", "Principle", "Advantages", "Limitations"),
        ("**NIST SP 800-61 Rev. 3**\n(Nelson et al., 2025)",
         "Textual recommendations; advises documenting procedures as playbooks",
         "Flexible",
         "Defines no notation, so the ambiguity of prose remains"),
        ("**CACAO Security Playbooks 2.0**\n(Jordan & Thomson, 2023)",
         "OASIS Committee Specification of 27 November 2023: a playbook in JSON as a workflow of eight "
         "step types",
         "Machine-readable and shareable",
         "No native graphical notation; even a simple playbook takes hundreds of lines of code "
         "(Zych et al., 2023)"),
        ("**BPMN 2.0** (OMG, 2011) and security extensions such as **SecBPMN** (Salnitri et al., 2017)",
         "Graphical notation built from flow objects, data, connecting objects, swimlanes and artifacts; "
         "SecBPMN adds security annotations and a query language",
         "Meant to be understood by managers and engineers alike; SecBPMN checked a process of "
         "50 activities in 14.71 seconds",
         "Only 12 security-aware extensions in a review of 1,400 sources (Hornsteiner et al., 2022); not "
         "part of the standard; they annotate business processes instead of describing response procedures; "
         "hard to keep synchronised with executable workflows (Akbari Gurabi et al., 2024)"),
    ]
    widths = [2.0, 2.35, 2.0, 2.55]
    heights = [0.38, 0.8, 1.05, 2.3]
    frame = s.shapes.add_table(len(rows), 4, Inches(0.55), Inches(1.2), Inches(sum(widths)), Inches(sum(heights)))
    table = frame.table
    tbl_pr = frame._element.graphic.graphicData.tbl.tblPr
    for attr in ("bandRow", "firstRow"):
        tbl_pr.set(attr, "0")
    style = tbl_pr.find(qn("a:tableStyleId"))
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"       # "No Style, Table Grid"
    for c, w in enumerate(widths):
        table.columns[c].width = Inches(w)
    for r, row in enumerate(rows):
        table.rows[r].height = Inches(heights[r])
        for c, content in enumerate(row):
            cell = table.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.07)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE if r == 0 else MSO_ANCHOR.TOP
            cell.fill.solid()
            cell.fill.fore_color.rgb = HEAD if r == 0 else (PALE if c == 0 else WHITE)
            tf = cell.text_frame
            tf.word_wrap = True
            for k, ptext in enumerate(content.split("\n")):
                par = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                add_runs(par, ptext, 12, WHITE if r == 0 else INK, bold=(r == 0))
    text(s, 0.55, 5.85, 8.9, 0.5,
         "None of the three gives a [[standard graphical]] description of the [[response procedure]] itself.", 15,
         bold=True, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "Three existing solutions. NIST SP 800-61 Revision 3 gives textual recommendations: flexible, but "
             "no notation. CACAO 2.0 is an OASIS specification that encodes a playbook in JSON with eight step "
             "types: machine-readable and shareable, but with no native graphical notation, and a simple "
             "playbook takes hundreds of lines. BPMN 2.0 is the graphical OMG notation readable by managers and "
             "engineers; SecBPMN checked a 50-activity process in 14.71 seconds, but a review of 1,400 sources "
             "found only 12 security-aware extensions, they are not standard and they annotate business "
             "processes instead of describing response procedures.")


def approach_slide(deck):
    s = deck.new_slide("Proposed approach")
    text(s, 0.55, 1.2, 8.9, 0.95,
         "Describe incident-handling procedures with the [[standard BPMN 2.0 elements only]], so that the "
         "models can be drawn in free tools.", 16)
    text(s, 0.55, 2.2, 3.6, 0.35, "In the procedure", 13, GREY, bold=True)
    text(s, 6.25, 2.2, 3.2, 0.35, "BPMN 2.0 element", 13, GREY, bold=True)
    rows = [("The organisation and the CSIRT", "Pools"), ("Roles", "Swimlanes"),
            ("Legal deadlines", "Timer events"), ("Notifications", "Message flows"),
            ("Evidence and reports", "Data objects")]
    for k, (concept, element) in enumerate(rows):
        y = 2.6 + k * 0.68
        box(s, 0.55, y, 3.6, 0.54, fill=PALE, line=None)
        text(s, 0.65, y, 3.4, 0.54, concept, 15, INK, anchor=MSO_ANCHOR.MIDDLE)
        line(s, 4.25, y + 0.27, 4.8, y + 0.27, color=GREY, width=1.25, arrow=True)
        cx, cy = 5.45, y + 0.27                                # centre of the small symbol
        if element == "Pools":
            box(s, cx - 0.42, cy - 0.2, 0.84, 0.4, fill=WHITE, line=INK, width=1)
            box(s, cx - 0.42, cy - 0.2, 0.14, 0.4, fill=WHITE, line=INK, width=1)
        elif element == "Swimlanes":
            box(s, cx - 0.42, cy - 0.22, 0.84, 0.44, fill=WHITE, line=INK, width=1)
            box(s, cx - 0.42, cy - 0.22, 0.14, 0.44, fill=WHITE, line=INK, width=1)
            line(s, cx - 0.28, cy, cx + 0.42, cy, color=INK, width=1)
        elif element == "Timer events":
            box(s, cx - 0.2, cy - 0.2, 0.4, 0.4, fill=WHITE, line=INK, width=1, shape=MSO_SHAPE.OVAL)
            box(s, cx - 0.15, cy - 0.15, 0.3, 0.3, fill=WHITE, line=INK, width=1, shape=MSO_SHAPE.OVAL)
            line(s, cx, cy, cx, cy - 0.1, color=INK, width=1)
            line(s, cx, cy, cx + 0.08, cy, color=INK, width=1)
        elif element == "Message flows":
            box(s, cx - 0.42, cy - 0.04, 0.08, 0.08, fill=WHITE, line=INK, width=1, shape=MSO_SHAPE.OVAL)
            line(s, cx - 0.34, cy, cx + 0.42, cy, color=INK, width=1.25, dash=True, arrow=True)
        else:
            box(s, cx - 0.15, cy - 0.21, 0.3, 0.42, fill=WHITE, line=INK, width=1, shape=MSO_SHAPE.FOLDED_CORNER)
        text(s, 6.25, y, 3.2, 0.54, element, 16, RED, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "My approach is to use only the standard BPMN 2.0 elements, without any extension. The "
             "organisation and the CSIRT become pools, roles become swimlanes, the legal deadlines become timer "
             "events, notifications become message flows, and evidence and reports become data objects. Because "
             "nothing non-standard is used, the models can be drawn in free tools.")


def aim_slide(deck):
    s = deck.new_slide("Aim, tasks, and methods")
    box(s, 0.55, 1.2, 8.9, 0.95, fill=PALE, line=None)
    box(s, 0.55, 1.2, 0.08, 0.95, fill=HEAD, line=None)
    text(s, 0.78, 1.2, 8.55, 0.95,
         "[[Aim]]: to develop and validate **CyberFlow**, a BPMN 2.0-based method and model repository for the "
         "incident-handling procedures of a medium-sized Latvian organisation subject to NIS2.", 14,
         anchor=MSO_ANCHOR.MIDDLE)
    tasks = [
        "Analyse the legal requirements and the existing playbook formats",
        "Define modelling rules that map roles, deadlines, notifications and documents to BPMN 2.0 elements",
        "Build the conceptual model of the goal system (concept map, causal loop diagram) and BPMN 2.0 models "
        "of three typical procedures: phishing, ransomware and denial of service",
        "Verify the models against the notation and the legal requirements",
        "Validate them in a tabletop exercise against the prose versions",
    ]
    tops = [2.35, 2.83, 3.48, 4.13, 4.61]
    for k, (task, y) in enumerate(zip(tasks, tops)):
        dot = box(s, 0.6, y + 0.03, 0.34, 0.34, fill=HEAD, line=None, shape=MSO_SHAPE.OVAL)
        text(s, 0.6, y + 0.03, 0.34, 0.34, str(k + 1), 13, WHITE, bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, after=0, margin=0)
        text(s, 1.1, y, 8.35, 0.8, task, 14, INK)
    line(s, 0.55, 5.22, 9.45, 5.22, color=RULE, width=0.75)
    text(s, 0.55, 5.34, 8.9, 0.8,
         "[[Methods]]: literature analysis; conceptual modelling (concept maps, causal loop diagrams and "
         "BPMN 2.0 diagrams in ARIS Express); expert review; a comparative experiment.", 14)
    notes(s, "The aim is to develop and validate CyberFlow: a BPMN 2.0-based method and a repository of models "
             "for the incident-handling procedures of a medium-sized Latvian organisation under NIS2. Five "
             "tasks: analyse the legal requirements and playbook formats; define the modelling rules; build the "
             "conceptual model and three BPMN models, for phishing, ransomware and denial of service; verify "
             "them; and validate them in a tabletop exercise against the prose versions. The methods are "
             "literature analysis, conceptual modelling, expert review and a comparative experiment.")


def results_slide(deck):
    s = deck.new_slide("Expected results and target audience")
    text(s, 0.55, 1.2, 4.3, 0.4, "Expected results", 16, HEAD, bold=True)
    text(s, 0.55, 1.65, 4.3, 2.3, [
        "Three validated procedure models: every step has a responsible role, and all three reporting "
        "deadlines appear as explicit events",
        "A set of modelling rules",
        "Measured evidence from the exercise",
    ], 14, bullet=True, after=7)
    box(s, 0.55, 3.75, 4.3, 2.1, fill=PALE, line=None)
    box(s, 0.55, 3.75, 0.08, 2.1, fill=HEAD, line=None)
    text(s, 0.8, 3.82, 3.95, 0.7, "at least 20%", 28, RED, bold=True)
    text(s, 0.8, 4.52, 3.95, 1.3,
         "fewer procedural errors, and a shorter time to the first notification, than with the prose "
         "procedures (the target of the exercise)", 14)
    line(s, 5.0, 1.25, 5.0, 5.9, color=RULE, width=0.75)
    text(s, 5.2, 1.2, 4.25, 0.4, "Potential users", 16, HEAD, bold=True)
    text(s, 5.2, 1.65, 4.25, 1.5,
         "Chief information security officers and security operations teams of essential and important "
         "entities, especially those without automation platforms; auditors; the CSIRT.", 14)
    text(s, 5.2, 3.2, 4.25, 0.4, "What they gain", 16, HEAD, bold=True)
    text(s, 5.2, 3.65, 4.25, 2.6, [
        "A shared and unambiguous description of who does what and when",
        "Faster training of new staff",
        "Documented evidence of compliance",
        "A starting point for automation: extensive use of AI and automation in security is associated with "
        "breach costs that are USD\u00a01.93\u00a0million lower (IBM, 2026)",
    ], 14, bullet=True, after=6)
    notes(s, "Expected results: three validated procedure models where every step has a responsible role and "
             "the three deadlines are explicit events; a set of modelling rules; and measured evidence, with a "
             "target of at least 20 per cent fewer procedural errors and a shorter time to the first "
             "notification than with prose. The users are CISOs and security operations teams of essential and "
             "important entities, auditors and the CSIRT. They get one unambiguous description, faster training, "
             "evidence of compliance and a starting point for automation, which IBM associates with breach "
             "costs lower by 1.93 million dollars.")


def further_slide(deck):
    s = deck.new_slide("Further development")
    text(s, 0.55, 1.2, 8.9, 0.5, "The proposed solution will [[not]] solve the problem completely.", 16)
    text(s, 0.55, 1.85, 4.3, 0.4, "Limitations", 16, HEAD, bold=True)
    text(s, 0.55, 2.3, 4.3, 3.9, [
        "BPMN 2.0 leaves simulation, monitoring and organisational resource models outside its scope "
        "(OMG, 2011): the models show the logic of a procedure, but neither execute it nor predict "
        "response times",
        "Graphical models are understood better only by trained readers (Ottensooser et al., 2012)",
        "The mapping between BPMN and CACAO is not one-to-one (Zych et al., 2023)",
    ], 14, bullet=True, after=8)
    line(s, 5.0, 1.9, 5.0, 5.2, color=RULE, width=0.75)
    text(s, 5.2, 1.85, 4.25, 0.4, "Further research", 16, HEAD, bold=True)
    text(s, 5.2, 2.3, 4.25, 3.9, [
        "Automatic transformation of the validated models into CACAO playbooks for execution",
        "Simulation of response times with system dynamics and discrete-event models",
        "More incident types and sectors in the repository",
        "The evaluation repeated in several organisations",
    ], 14, bullet=True, after=8)
    notes(s, "The solution is not complete. BPMN 2.0 itself leaves simulation, monitoring and resource models "
             "out of scope, so my models show the logic but do not execute it or predict response times. "
             "Graphical models help mainly trained readers, and BPMN does not map one-to-one to CACAO. Further "
             "work: transform the validated models into CACAO playbooks automatically, simulate response times "
             "with system dynamics and discrete-event models, add incident types and sectors, and repeat the "
             "evaluation in several organisations.")


def reference_slides(deck):
    parts = [REFERENCES[:8], REFERENCES[8:]]
    for n, part in enumerate(parts, 1):
        s = deck.new_slide(f"References ({n}/{len(parts)})")
        tb = text(s, 0.55, 1.2, 8.9, 4.9, part, 11, INK, after=6)
        for par in tb.text_frame.paragraphs:
            ppr = par._p.get_or_add_pPr()
            ppr.set("marL", str(int(Inches(0.35))))
            ppr.set("indent", str(-int(Inches(0.35))))
        if n == len(parts):
            text(s, 0.55, 5.55, 8.9, 0.7, AI_NOTE, 11, GREY, italic=True)
        notes(s, "The reference list in APA 7 format, the same fifteen sources as in the written summary."
                 + (" The note states how generative AI was used." if n == len(parts) else ""))


def build(template=TEMPLATE, out=OUT):
    deck = Deck(template)
    title_slide(deck)
    outline_slide(deck)
    relevance_slide(deck)
    deadlines_slide(deck)
    problem_slide(deck)
    solutions_slide(deck)
    approach_slide(deck)
    aim_slide(deck)
    results_slide(deck)
    further_slide(deck)
    reference_slides(deck)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    deck.prs.save(out)
    print(f"written {out}: {len(deck.prs.slides)} slides")


if __name__ == "__main__":
    build(*sys.argv[1:3])
