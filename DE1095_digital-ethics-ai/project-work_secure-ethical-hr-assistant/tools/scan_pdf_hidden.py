"""Flag text in PDFs that a reader would not see: tiny fonts, white/near-white
colour, text outside the page, plus annotations and metadata.  Prints every
suspicious group with its text."""
import sys, pdfplumber
from pypdf import PdfReader

def is_light(col):
    if col is None: return False
    try:
        vals = [float(v) for v in col]
    except Exception:
        return False
    if len(vals) == 1: return vals[0] >= 0.93            # grey
    if len(vals) == 3: return all(v >= 0.93 for v in vals)   # rgb
    if len(vals) == 4: return all(v <= 0.07 for v in vals)   # cmyk (0,0,0,0) = white
    return False

total_flags = 0
for path in sys.argv[1:]:
    flags = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            W, H = page.width, page.height
            groups = {}
            for c in page.chars:
                reasons = []
                if c["size"] < 5: reasons.append("tiny %.1fpt" % c["size"])
                if is_light(c.get("non_stroking_color")): reasons.append("white fill %s" % (c.get("non_stroking_color"),))
                if c["x1"] < 0 or c["x0"] > W or c["bottom"] < 0 or c["top"] > H: reasons.append("off-page")
                if reasons:
                    key = (pno, tuple(reasons), c["fontname"])
                    groups.setdefault(key, []).append(c)
            for (p, reasons, font), cs in groups.items():
                cs.sort(key=lambda c: (round(c["top"]), c["x0"]))
                text = "".join(ch["text"] for ch in cs).strip()
                if len(text) >= 3:
                    flags.append((p, reasons, font, len(cs), text))
    # annotations and metadata via pypdf
    r = PdfReader(path)
    meta = {k: str(v) for k, v in (r.metadata or {}).items() if v}
    ann_texts = []
    for pno, page in enumerate(r.pages, 1):
        for a in page.get("/Annots", []) or []:
            try:
                a = a.get_object()
                t = a.get("/Contents") or a.get("/T")
                sub = a.get("/Subtype")
                if t and sub != "/Link":
                    ann_texts.append((pno, str(sub), str(t)[:200]))
            except Exception as e:
                ann_texts.append((pno, "err", str(e)[:80]))
    name = path.split("/")[-1]
    status = "OK" if not flags and not ann_texts else "FLAGGED"
    print(f"{status:8} {name}")
    for p, reasons, font, n, text in flags:
        total_flags += 1
        print(f"    page {p:>3}  {' + '.join(reasons)}  font={font}  chars={n}")
        print(f"             {text[:400]}")
    for pno, sub, t in ann_texts:
        total_flags += 1
        print(f"    page {pno:>3}  annotation {sub}: {t}")
    odd = {k: v for k, v in meta.items() if k not in ("/Producer", "/Creator", "/CreationDate", "/ModDate", "/Title", "/Author")}
    if odd: print("    metadata:", odd)
    for k in ("/Title", "/Author", "/Subject", "/Keywords"):
        if k in meta and len(meta[k]) > 80: print("    long metadata", k, meta[k][:200])
print("\nTOTAL flagged groups:", total_flags)
