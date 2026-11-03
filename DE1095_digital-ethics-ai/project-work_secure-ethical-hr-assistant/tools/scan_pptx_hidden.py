"""Flag hidden content in PPTX: hidden slides, notes, tiny or white text,
shapes outside the slide, and text in the slide masters/layouts."""
import sys
from pptx import Presentation
from pptx.util import Emu

def run_flags(run, on_dark):
    f = run.font
    reasons = []
    try:
        if f.size is not None and f.size.pt < 5: reasons.append("tiny %.1fpt" % f.size.pt)
    except Exception: pass
    try:
        if f.color is not None and f.color.type is not None and f.color.rgb is not None:
            rgb = str(f.color.rgb)
            if rgb.upper() in ("FFFFFF", "FEFEFE", "FDFDFD") and not on_dark: reasons.append("white text " + rgb)
    except Exception: pass
    return reasons

for path in sys.argv[1:]:
    prs = Presentation(path)
    W, H = prs.slide_width, prs.slide_height
    print("==", path.split("/")[-1], "slides:", len(prs.slides), "size:", Emu(W).inches, "x", Emu(H).inches, "in")
    n = 0
    for i, slide in enumerate(prs.slides, 1):
        hidden = slide._element.get("show") == "0"
        if hidden:
            n += 1; print(f"  slide {i}: HIDDEN SLIDE. text:", " | ".join(sh.text_frame.text[:120] for sh in slide.shapes if sh.has_text_frame))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            n += 1; print(f"  slide {i}: NOTES:", slide.notes_slide.notes_text_frame.text.strip()[:300])
        bg_dark = False
        for sh in slide.shapes:
            # position outside the slide
            if sh.left is not None and sh.width is not None:
                if sh.left + sh.width < 0 or sh.left > W or sh.top + sh.height < 0 or sh.top > H:
                    t = sh.text_frame.text[:200] if sh.has_text_frame else ""
                    n += 1; print(f"  slide {i}: shape '{sh.name}' OUTSIDE slide at ({Emu(sh.left).inches:.1f},{Emu(sh.top).inches:.1f}) in; text: {t!r}")
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        fl = run_flags(r, bg_dark)
                        if fl and r.text.strip():
                            n += 1; print(f"  slide {i}: shape '{sh.name}' {fl}: {r.text[:200]!r}")
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        for p in cell.text_frame.paragraphs:
                            for r in p.runs:
                                fl = run_flags(r, False)
                                if fl and r.text.strip():
                                    n += 1; print(f"  slide {i}: table cell {fl}: {r.text[:200]!r}")
    # masters and layouts: text placeholders are normal; flag any non-placeholder text
    for m in prs.slide_masters:
        for sh in m.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip() and not sh.is_placeholder:
                n += 1; print("  MASTER text shape:", sh.name, sh.text_frame.text.strip()[:200])
        for lay in m.slide_layouts:
            for sh in lay.shapes:
                if sh.has_text_frame and sh.text_frame.text.strip() and not sh.is_placeholder:
                    n += 1; print("  LAYOUT", lay.name, "text shape:", sh.name, sh.text_frame.text.strip()[:200])
    print("  flags:", n)
