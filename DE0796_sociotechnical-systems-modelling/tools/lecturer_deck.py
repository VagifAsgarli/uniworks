"""Shared helpers for the presentations built on the lecturer's slide templates (DE0796).

The lecturer's templates (T4LPrim, T4L, T5L) share one design: a title slide (RTU logo, faculty lines,
course name, work title, names) and a content slide (red heading with a line under it, "RTU 2026" footer,
slide number).  `Deck` reuses these parts unchanged, replaces only the texts and adds new content slides
that carry the same heading, line, footer and slide number.

Text markup:  [[...]] red italics (the lecturer's way of stressing a term), **...** bold, *...* italics.
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

RED = RGBColor(0xC0, 0x00, 0x00)        # the lecturer's emphasis colour
HEAD = RGBColor(0x94, 0x36, 0x34)       # heading colour of the template (accent 2, 25% darker)
BLUE = RGBColor(0x36, 0x5F, 0x91)       # footer colour of the template (accent 1, 25% darker)
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x59, 0x59, 0x59)
RULE = RGBColor(0xBF, 0xBF, 0xBF)
PALE = RGBColor(0xF6, 0xF1, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"

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
