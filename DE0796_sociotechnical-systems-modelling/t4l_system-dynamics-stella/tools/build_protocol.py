"""Fills the lecturer's T4L protocol template (materials/t4l_protocol-template.docx).

    python build_protocol.py [--shots DIR] [--date "DD. MM. 2026"] [--out FILE.docx]

The template is opened and kept: title block, questions, numbered tasks, the lecturer's notes and the
signature line stay as he wrote them; the answers are written under his lines.  The text comes from
t4l_content.py, the numbers from the reference run of the same equations.

--shots DIR   folder with the screenshots taken in STELLA (names in t4l_content.SHOTS, listed in
              notes/stella-guide_az.md).  The protocol that is handed in needs all of them.  While one is
              missing, the script builds a DRAFT: the missing figure is replaced by the expected picture
              from the checking calculation, the figure is marked as a draft, and the file gets the
              suffix _DRAFT.

Then convert the .docx to PDF (LibreOffice or Word).  Final name: VagifAsgarli-T4L.pdf.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile

from docx import Document
from docx.shared import Pt
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))

import t4l_content as C  # noqa: E402
import yellowstone_sd as sd  # noqa: E402
from lecturer_protocol import (BODY_WIDTH_CM, WD_ALIGN_PARAGRAPH, caption_after, fmt, picture_after,  # noqa: E402
                               replace_tail, show_whole_title, table_after, text_after)

TEMPLATE = os.path.join(HERE, "..", "materials", "t4l_protocol-template.docx")
CLD_FIGURE = os.path.join(HERE, "..", "..", "t4lprim_causal-loop-diagram-yellowstone", "outputs", "figures",
                          "yellowstone_cld.png")
EXPECTED = os.path.join(HERE, "..", "outputs", "reference-simulation")
EXPECTED_MODEL = os.path.join(HERE, "..", "outputs", "model", "model-layer_expected.png")
DRAFT_MARK = " (DRAFT: expected picture from the checking calculation, to be replaced by the STELLA screenshot)"


def placeholder(text, path, size=(1500, 420)):
    im = Image.new("RGB", size, "#fff4f4")
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, size[0] - 5, size[1] - 5], outline="#b5121b", width=5)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 40)
    except OSError:
        font = ImageFont.load_default()
    lines = text.split("\n")
    y = size[1] / 2 - 30 * len(lines)
    for line in lines:
        w = d.textlength(line, font=font)
        d.text(((size[0] - w) / 2, y), line, fill="#b5121b", font=font)
        y += 60
    im.save(path)
    return path


def figure(key, shots, tmp):
    """Returns (path of the picture, True if it is the real STELLA screenshot)."""
    name = C.SHOTS[key]
    if shots and os.path.exists(os.path.join(shots, name)):
        return os.path.join(shots, name), True
    if key == "model":
        return EXPECTED_MODEL, False
    if key == "table":
        return placeholder(f"STELLA screenshot to be inserted here:\n{name}\n(Table of the stocks after the base run)",
                           os.path.join(tmp, "table.png")), False
    exp = next(n for n in C.RUNS if n.startswith(key))
    return os.path.join(EXPECTED, sd.slug(exp) + ".png"), False


def build(out, shots, date):
    doc = Document(TEMPLATE)
    P = doc.paragraphs
    tmp = tempfile.mkdtemp(prefix="t4l_")
    pics = {k: figure(k, shots, tmp) for k in C.SHOTS}
    draft = not all(real for _, real in pics.values())

    def at(i, starts):                       # the template must be the one this script was written for
        assert P[i].text.strip().startswith(starts), (i, P[i].text)
        return P[i]

    def cap(text, key):
        return text + ("" if pics[key][1] else DRAFT_MARK)

    def pic_width(key, max_w=BODY_WIDTH_CM, max_h=11.0):
        w, h = Image.open(pics[key][0]).size
        return min(max_w, max_h * w / h)

    # title block
    show_whole_title(doc)
    replace_tail(at(9, "Students:"), 5, f"{C.NAME} ({C.STUDENT_ID})")
    replace_tail(at(12, "Date:"), 6, date)

    # theoretical rationale: the answers go under the lecturer's questions
    q1, q2 = at(19, "What are Stocks and Flow"), at(20, "What are the differences")
    last = q1
    for t in C.STOCKS_AND_FLOWS:
        last = text_after(last, doc, t, indent=False)
    q2.paragraph_format.space_before = Pt(6)
    last = text_after(q2, doc, C.DIFFERENCES_INTRO, indent=False)
    last = text_after(last, doc, C.TABLE1_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=3,
                      keep_next=True)
    table_after(last, doc, C.TABLE1, (2.9, 5.6, 6.1))

    # 1. summary of the CLD
    last = at(29, "(Be concise")
    for k, t in enumerate(C.CLD_SUMMARY):
        last = text_after(last, doc, t, before=6 if k == 0 else 0)
    last = picture_after(last, doc, CLD_FIGURE, width_cm=BODY_WIDTH_CM)
    caption_after(last, doc, C.FIG_CLD_CAPTION)

    # 2. the model: description, values, interface, base run
    last = at(34, "(Create a SD")
    for k, t in enumerate(C.MODEL_INTRO):
        last = text_after(last, doc, t, before=6 if k == 0 else 0)
    last = text_after(last, doc, C.TABLE2_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=3,
                      keep_next=True)
    last = table_after(last, doc, C.TABLE2, (5.6, 9.0))
    last = text_after(last, doc, C.TABLE3_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, before=8,
                      after=3, keep_next=True)
    last = table_after(last, doc, C.table3(), (4.2, 10.4), size=9)
    last = text_after(last, doc, C.VALUES_INTRO, before=8)
    last = text_after(last, doc, C.TABLE4_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=3,
                      keep_next=True)
    last = table_after(last, doc, C.table4(), (3.9, 1.5, 2.3, 6.9), size=9)
    last = text_after(last, doc, C.INTERFACE_TEXT, before=8)
    last = picture_after(last, doc, pics["E1"][0], width_cm=pic_width("E1"))
    last = caption_after(last, doc, cap(C.FIG_INTERFACE_CAPTION, "E1"))
    for t in C.BASE_TEXT:
        last = text_after(last, doc, t)
    last = picture_after(last, doc, pics["table"][0], width_cm=pic_width("table", max_h=9.0))
    caption_after(last, doc, cap(C.FIG_TABLE_CAPTION, "table"))

    # the MODEL layer screenshot
    last = at(36, "(Include the MODEL layer screenshot)")
    last = text_after(last, doc, C.MODEL_LAYER_TEXT, before=6)
    last = picture_after(last, doc, pics["model"][0], width_cm=pic_width("model", max_h=12.5))
    caption_after(last, doc, cap(C.FIG_MODEL_CAPTION, "model"))

    # experiments
    last = at(38, "(Carry out experiments")
    last = text_after(last, doc, C.EXPERIMENTS_INTRO, before=6)
    last = text_after(last, doc, C.TABLE5_CAPTION, size=10, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=3,
                      keep_next=True)
    last = table_after(last, doc, C.table5(), (2.9, 2.8, 1.4, 1.3, 1.6, 1.5, 1.5, 1.66), size=8)
    for k, key in enumerate(("E2", "E3", "E4", "E5", "E6")):
        last = text_after(last, doc, C.EXPERIMENT_TEXT[key], before=8 if k == 0 else 4, keep_next=True)
        last = picture_after(last, doc, pics[key][0], width_cm=pic_width(key, max_h=8.5))
        last = caption_after(last, doc, cap(C.EXPERIMENT_FIG[key], key))

    # 3. conclusions
    last = at(43, "(Here and below, present conclusions")
    for i, t in enumerate(C.CONCLUSIONS, 1):
        last = text_after(last, doc, f"{i}. {t}", before=6 if i == 1 else 0)

    # 4. presentation, then the reference list and the note on AI use
    last = text_after(at(50, "(T4L work protocol"), doc, C.PRESENTATION_NOTE, before=6)
    last = text_after(last, doc, "References", bold=True, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, before=14,
                      after=6, keep_next=True)
    for ref in C.REFERENCES:
        last = text_after(last, doc, ref, align=WD_ALIGN_PARAGRAPH.LEFT, hanging_cm=1.27, after=4, indent=False)
        fmt(last, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=4)
        last.paragraph_format.left_indent = Pt(36)
        last.paragraph_format.first_line_indent = Pt(-36)
    text_after(last, doc, C.AI_NOTE, italic=True, size=11, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, before=8)

    at(56, "Signature:")
    if draft and not out.endswith("_DRAFT.docx"):
        out = out[:-5] + "_DRAFT.docx"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    doc.save(out)
    missing = [C.SHOTS[k] for k, (_, real) in pics.items() if not real]
    print(f"written {os.path.normpath(out)}" + (f"  DRAFT, missing STELLA screenshots: {', '.join(missing)}" if draft else
                                              "  final: all figures are STELLA screenshots"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shots", default=os.path.join(HERE, "..", "outputs", "stella-screenshots"))
    ap.add_argument("--date", default=C.DATE)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    have_all = all(os.path.exists(os.path.join(args.shots, n)) for n in C.SHOTS.values())
    out = args.out or os.path.join(HERE, "..", "outputs", "submission" if have_all else "draft", "VagifAsgarli-T4L.docx")
    build(out, args.shots, args.date)


if __name__ == "__main__":
    main()
