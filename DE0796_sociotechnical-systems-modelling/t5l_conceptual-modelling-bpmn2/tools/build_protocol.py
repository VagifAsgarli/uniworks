"""Fills the lecturer's T5L protocol template (materials/t5l_protocol-template.docx).

The template is opened and kept: its title block, questions, numbered tasks, notes and signature line stay
as the lecturer wrote them. The placeholders (name, date, goal system name, description, CLD drawing,
reference list) are replaced, and the answers are written under the lecturer's lines. The text comes from
t5l_content.py.

    python build_protocol.py --out <protocol.docx> --bpmn-figure <diagram.png> [--draft] [--date "DD. MM. 2026"]

--bpmn-figure   the picture of the BPMN2 diagram. For the protocol that is handed in this is the picture
                exported from ArisExpress; with --draft it may be the reference drawing.
--draft         marks the BPMN2 figures as a reference drawing (not for handing in).

Then convert to PDF with LibreOffice or Word. The final file name is vagif.asgarli-T5L.pdf.
"""
from __future__ import annotations

import argparse
import copy
import os
import re
import sys
import tempfile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, Twips
from docx.text.paragraph import Paragraph
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t5l_content as C  # noqa: E402

TEMPLATE = os.path.join(HERE, "..", "materials", "t5l_protocol-template.docx")
CLD_FIGURE = os.path.join(HERE, "..", "outputs", "figures", "fig1_cyberflow_cld.png")
FONT = "Times New Roman"
INDENT_TWIPS = 1004                  # the indent the template uses for text under a numbered heading
BODY_WIDTH_CM = 14.66                # A4 minus the template's side margins


# ----------------------------------------------------------------------------- small helpers
def add_runs(par: Paragraph, text: str, size=12, bold=False, italic=False):
    """Adds text with **bold** and *italic* markup to a paragraph."""
    for i, part in enumerate(re.split(r"(\*\*.+?\*\*|\*.+?\*)", text)):
        if not part:
            continue
        b, it = bold, italic
        if part.startswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("*"):
            part, it = part[1:-1], True
        run = par.add_run(part)
        run.font.name = FONT
        run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
        run.font.size = Pt(size)
        run.bold = b
        run.italic = it
    return par


def par_after(anchor, doc) -> Paragraph:
    """A new empty paragraph right after `anchor` (a paragraph or a table)."""
    el = anchor._p if isinstance(anchor, Paragraph) else anchor._tbl
    p = OxmlElement("w:p")
    el.addnext(p)
    return Paragraph(p, doc._body)


def fmt(par: Paragraph, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=6, hanging_cm=None,
        keep_next=False):
    pf = par.paragraph_format
    pf.alignment = align
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.line_spacing = 1.0
    if indent:
        hang = int(hanging_cm * 567) if hanging_cm else 0
        pf.left_indent = Twips(INDENT_TWIPS + hang)
        if hang:
            pf.first_line_indent = Twips(-hang)
    pf.keep_with_next = keep_next
    return par


def text_after(anchor, doc, text, **kw):
    size = kw.pop("size", 12)
    bold, italic = kw.pop("bold", False), kw.pop("italic", False)
    par = par_after(anchor, doc)
    add_runs(par, text, size=size, bold=bold, italic=italic)
    return fmt(par, **kw)


def replace_text(par: Paragraph, text: str, bold=None, italic=None):
    """Replaces the whole text of a template paragraph, keeping the format of its first run."""
    runs = par.runs
    first = runs[0]
    for r in runs[1:]:
        r._element.getparent().remove(r._element)
    for child in list(first._element):
        if child.tag in (qn("w:tab"), qn("w:br")):
            first._element.remove(child)
    first.text = text
    if bold is not None:
        first.bold = bold
    if italic is not None:
        first.italic = italic
    return par


def replace_tail(par: Paragraph, n_keep: int, value: str):
    """Keeps the first `n_keep` runs of a template line (label and tabs) and writes `value` after them."""
    for r in par.runs[n_keep:]:
        r._element.getparent().remove(r._element)
    add_runs(par, value)


def table_after(anchor, doc, rows, widths_cm, size=10):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    tbl = table._tbl
    (anchor._p if isinstance(anchor, Paragraph) else anchor._tbl).addnext(tbl)
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        borders.append(b)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    look = tblPr.find(qn("w:tblLook"))                # the schema wants borders and layout before tblLook
    for el in (borders, layout):
        if look is not None:
            look.addprevious(el)
        else:
            tblPr.append(el)
    for c, width in enumerate(widths_cm):
        table.columns[c].width = Cm(width)
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            cell = table.cell(r, c)
            cell.width = Cm(widths_cm[c])
            par = cell.paragraphs[0]
            add_runs(par, text, size=size, bold=(r == 0))
            par.paragraph_format.space_after = Pt(2)
            par.paragraph_format.space_before = Pt(2)
            par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if r == 0:                                    # repeat the header row on a new page
            trPr = table.rows[0]._tr.get_or_add_trPr()
            h = OxmlElement("w:tblHeader")
            trPr.append(h)
    for row in table.rows:                            # a row is not split between pages
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
    return table


def picture_after(anchor, doc, path, width_cm=None, height_cm=None):
    par = par_after(anchor, doc)
    run = par.add_run()
    if width_cm:
        run.add_picture(path, width=Cm(width_cm))
    else:
        run.add_picture(path, height=Cm(height_cm))
    fmt(par, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, before=6, after=3, keep_next=True)
    return par


def caption_after(anchor, doc, text, **kw):
    return text_after(anchor, doc, text, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER,
                      after=kw.pop("after", 10), **kw)


def end_section_here(par: Paragraph, body_sectPr, landscape: bool):
    """Makes `par` the last paragraph of a section with the given orientation."""
    sect = copy.deepcopy(body_sectPr)
    pgSz, pgMar = sect.find(qn("w:pgSz")), sect.find(qn("w:pgMar"))
    if landscape:
        pgSz.set(qn("w:w"), "16838")
        pgSz.set(qn("w:h"), "11906")
        pgSz.set(qn("w:orient"), "landscape")
        for side in ("top", "bottom", "left", "right"):
            pgMar.set(qn(f"w:{side}"), "1134")           # 2 cm
    par._p.get_or_add_pPr().append(sect)


def show_whole_title(doc, height_emu=1500000):
    """The title block of the template is a text box of fixed height. Its last lines (institute, department) are cut off
    when the lines wrap, so the box is made tall enough to show all of the lecturer's text."""
    ns_wp = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
    ns_a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    first = doc.paragraphs[0]._p
    for el in first.iter(f"{{{ns_wp}}}extent", f"{{{ns_a}}}ext"):
        if el.get("cy"):
            el.set("cy", str(height_emu))
    for el in first.iter("{urn:schemas-microsoft-com:vml}rect"):
        el.set("style", re.sub(r"height:[\d.]+pt", f"height:{height_emu / 12700:.1f}pt", el.get("style", "")))


def page_break(par: Paragraph):
    par.add_run().add_break(WD_BREAK.PAGE)


# ----------------------------------------------------------------------------- the protocol
def build(out, bpmn_figure, draft, date):
    assert C.N_MAPPED + C.N_UNMAPPED == C.N_CLD_VARIABLES
    doc = Document(TEMPLATE)
    P = doc.paragraphs
    body_sectPr = doc.element.body.sectPr

    def at(i, starts):                                   # the template must be the one this script was written for
        assert P[i].text.strip().startswith(starts), (i, P[i].text)
        return P[i]

    # title block
    show_whole_title(doc)
    replace_tail(at(9, "Students:"), 5, f"{C.NAME} ({C.STUDENT_ID})")
    replace_tail(at(12, "Date:"), 6, date)

    # theoretical rationale: the answers go under the lecturer's questions
    q1, q2 = at(19, "What is BPMN2?"), at(20, "What are the differences")
    last = q1
    for t in C.WHAT_IS_BPMN2:
        last = text_after(last, doc, t, indent=False)
    q2.paragraph_format.space_before = Pt(6)
    last = q2
    for t in C.DIFFERENCES:
        last = text_after(last, doc, t, indent=False)
    last = text_after(last, doc, C.TABLE1_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=3,
                      keep_next=True)
    table_after(last, doc, C.TABLE1, (3.2, 5.4, 6.0))

    # 1. goal system and CLD
    replace_text(at(28, "(Goal system Name)"), f"Goal system name: {C.GOAL_NAME}")
    d = at(29, "(Description)")
    replace_text(d, "Description")
    last = d
    for t in C.DESCRIPTION:
        last = text_after(last, doc, t)
    c = at(30, "(CLD diagram drawing)")
    replace_text(c, "CLD diagram drawing")
    c.paragraph_format.keep_with_next = True
    last = picture_after(c, doc, CLD_FIGURE, width_cm=BODY_WIDTH_CM)
    caption_after(last, doc, C.FIG1_CAPTION)
    last = at(32, "(Draw CLD marking")
    last = text_after(last, doc, C.CLD_INTRO, before=4)
    for label, title, text in C.LOOPS:
        last = text_after(last, doc, f"**{label}, {title}.** {text}")
    text_after(last, doc, C.CLD_OUTRO)

    # 2. BPMN2 model: a) transformation, b) interaction, c) the figure
    last = at(42, "Several Data objects")
    for t in C.TRANSFORM:
        last = text_after(last, doc, t, before=6)
    last = text_after(last, doc, C.TABLE2_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=3,
                      keep_next=True)
    last = table_after(last, doc, C.TABLE2, (4.6, 10.0))
    for k, t in enumerate(C.OPERATION):
        last = text_after(last, doc, t, before=8 if k == 0 else 0)
    last = text_after(last, doc, C.TABLE3_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=3,
                      keep_next=True)
    t3 = table_after(last, doc, C.TABLE3, (4.6, 10.0))
    text_after(t3, doc, C.MODEL_SIZE + " " + C.VERIFICATION, before=6)

    last = at(44, "A BPMN2 model should represent")
    for t in C.INTERACTION:
        last = text_after(last, doc, t, before=6 if last is P[44] else 0)

    last = at(46, "The BPMN2 model must be developed")
    last = text_after(last, doc, C.FIGURE_INTRO_DRAFT if draft else C.FIGURE_INTRO, before=6)
    end_section_here(last, body_sectPr, landscape=False)          # the portrait pages end here

    # the diagram is wide: one landscape page with the whole diagram and two with its halves
    im = Image.open(bpmn_figure).convert("RGB")
    w, h = im.size
    tmp = tempfile.mkdtemp(prefix="t5l_")
    halves = []
    for name, box in (("left", (0, 0, int(w * 0.54), h)), ("right", (int(w * 0.46), 0, w, h))):
        path = os.path.join(tmp, f"bpmn_{name}.png")
        im.crop(box).save(path)
        halves.append((path, box[2] - box[0]))
    suffix = " (DRAFT: reference drawing)" if draft else ""
    page_w, page_h = 25.7, 15.3                                   # usable area of a landscape page, caption excluded
    full_w = min(page_w, page_h * w / h)
    last = picture_after(last, doc, bpmn_figure, width_cm=full_w)
    last = caption_after(last, doc, C.FIG2_CAPTION.replace(" (drawn in ArisExpress)", "") + suffix if draft
                         else C.FIG2_CAPTION)
    for (path, hw), cap in zip(halves, (C.FIG3_CAPTION, C.FIG4_CAPTION)):
        page_break(last)
        half_w = min(page_w, page_h * hw / h)
        last = picture_after(last, doc, path, width_cm=half_w)
        last = caption_after(last, doc, cap + suffix)
    end_section_here(last, body_sectPr, landscape=True)           # back to portrait after this paragraph

    # 3. conclusions (under the lecturer's question)
    last = at(52, "In the Conclusion part")
    for i, t in enumerate(C.CONCLUSIONS, 1):
        last = text_after(last, doc, f"{i}. {t}", before=6 if i == 1 else 0)

    # 4. references
    r = at(56, "(Prepare reference list in APA7 format)")
    first, *rest = C.REFERENCES
    for run in r.runs[1:]:
        run._element.getparent().remove(run._element)
    r.runs[0].text = ""
    r.runs[0].italic = False
    add_runs(r, first, size=12)
    fmt(r, align=WD_ALIGN_PARAGRAPH.LEFT, hanging_cm=1.27, after=4)
    last = r
    for ref in rest:
        last = text_after(last, doc, ref, align=WD_ALIGN_PARAGRAPH.LEFT, hanging_cm=1.27, after=4)
    text_after(last, doc, C.AI_NOTE, italic=True, size=11, align=WD_ALIGN_PARAGRAPH.LEFT, before=8)

    # 5. presentation
    text_after(at(62, "(T5L work protocol"), doc, C.PRESENTATION_NOTE, before=6, indent=False).paragraph_format.left_indent = Cm(1.75)

    at(69, "Signature:")
    doc.core_properties.last_modified_by = C.NAME
    doc.core_properties.title = "T5L: Conceptual modelling in BPMN2"
    doc.save(out)
    print(f"written {out} ({'DRAFT, ' if draft else ''}BPMN2 figure: {os.path.basename(bpmn_figure)}, {w} x {h} px)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bpmn-figure", required=True)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--date", default=C.DATE)
    a = ap.parse_args()
    build(a.out, a.bpmn_figure, a.draft, a.date)


if __name__ == "__main__":
    main()
