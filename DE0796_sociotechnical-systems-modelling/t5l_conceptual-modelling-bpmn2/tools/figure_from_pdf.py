"""Turns the PDF that ArisExpress exports into the picture used by the protocol and the presentation.

The page is rendered with pdftoppm (poppler) and the white border around the diagram is cut off.

    python figure_from_pdf.py <model.pdf> <out.png> [page] [dpi]
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    pdf, out = sys.argv[1], sys.argv[2]
    page = sys.argv[3] if len(sys.argv) > 3 else "1"
    dpi = sys.argv[4] if len(sys.argv) > 4 else "300"
    tmp = os.path.join(tempfile.mkdtemp(prefix="t5l_"), "page")
    subprocess.run(["pdftoppm", "-f", page, "-l", page, "-r", dpi, "-png", "-singlefile", pdf, tmp], check=True)
    im = Image.open(tmp + ".png").convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    if box:
        pad = 20
        box = (max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad))
        im = im.crop(box)
    im.save(out)
    print(f"written {out}: {im.width} x {im.height} px (page {page} of {os.path.basename(pdf)} at {dpi} dpi)")


if __name__ == "__main__":
    main()
