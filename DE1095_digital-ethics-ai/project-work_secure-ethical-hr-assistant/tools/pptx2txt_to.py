import sys
from pptx import Presentation
src, dst = sys.argv[1], sys.argv[2]
out = []
for i, slide in enumerate(Presentation(src).slides, 1):
    out.append(f"=== Slide {i} ===")
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            out.append(shape.text_frame.text.strip())
        if getattr(shape, "has_table", False) and shape.has_table:
            for row in shape.table.rows:
                out.append(" | ".join(c.text for c in row.cells))
open(dst, "w").write("\n".join(out) + "\n")
