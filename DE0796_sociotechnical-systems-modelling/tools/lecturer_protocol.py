"""Shared helpers for filling the lecturer's protocol templates (DE0796, python-docx).

The template is opened and kept as the lecturer wrote it; the answers are written under his lines.
Text markup: **bold**, *italic*; write \\* for a literal asterisk.
"""
from __future__ import annotations

import re

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, Twips
from docx.text.paragraph import Paragraph

FONT = "Times New Roman"
INDENT_TWIPS = 1004                  # the indent the templates use for text under a numbered heading
BODY_WIDTH_CM = 14.66                # A4 minus the templates' side margins


def add_runs(par: Paragraph, text: str, size=12, bold=False, italic=False):
    """Adds text with **bold** and *italic* markup to a paragraph."""
    text = text.replace("\\*", "\ufffe")                # "\*" is a literal asterisk (equations)
    for i, part in enumerate(re.split(r"(\*\*.+?\*\*|\*.+?\*)", text)):
        if not part:
            continue
        b, it = bold, italic
        if part.startswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("*"):
            part, it = part[1:-1], True
        run = par.add_run(part.replace("\ufffe", "*"))
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
