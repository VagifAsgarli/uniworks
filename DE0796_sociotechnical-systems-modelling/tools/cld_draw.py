"""Draws a Causal Loops Diagram (CLD) in the notation of the course templates.

Notation (T4 lecture, slides 11-15, and the example in the T4LPrim template):
  * variables are plain text;
  * a blue arrow with "+" at its head: the two variables change in the same direction;
  * a red arrow with "-" at its head: they change in opposite directions;
  * two short strokes across an arrow: the effect comes with a delay;
  * a circular arrow with a bold letter inside a loop: R = reinforced, B = balanced feedback.

The diagram is described in a JSON file, so every drawing can be repeated and corrected:

    {
      "xlim": [0, 16], "ylim": [0, 9], "figsize": [12.8, 7.2], "fontsize": 11,
      "nodes": {"wolves": [4.2, 5.3, "Wolves"], ...},            key: [x, y, label]
      "links": [["deers", "wolves", "+", 0.25, {"delay": true}], ...],
               from, to, sign, bend (0 = straight; the sign of the bend picks the side), options
               options: "delay" (bool), "sign_side" (1 or -1), "sign_back" (distance from the head)
      "loops": [["B1", 5.8, 6.3, "cw"], ...]                     label, x, y, direction of the loop
    }

    python cld_draw.py diagram.json out.png [out.svg]
"""
from __future__ import annotations

import json
import math
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path

BLUE = "#1f6fb2"
RED = "#b5121b"
INK = "#1a1a1a"


def _bezier(a, c, b, t):
    return ((1 - t) ** 2 * a[0] + 2 * t * (1 - t) * c[0] + t * t * b[0],
            (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * c[1] + t * t * b[1])


def _tangent(a, c, b, t):
    dx = 2 * (1 - t) * (c[0] - a[0]) + 2 * t * (b[0] - c[0])
    dy = 2 * (1 - t) * (c[1] - a[1]) + 2 * t * (b[1] - c[1])
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _inside(box, p, pad=0.0):
    return box[0] - pad <= p[0] <= box[2] + pad and box[1] - pad <= p[1] <= box[3] + pad


def draw_cld(spec: dict, out_png: str, out_svg: str | None = None):
    fontsize = spec.get("fontsize", 11)
    fig, ax = plt.subplots(figsize=tuple(spec.get("figsize", (12.8, 7.2))))
    ax.set_xlim(*spec["xlim"])
    ax.set_ylim(*spec["ylim"])
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)

    texts, boxes = {}, {}
    for key, (x, y, label) in spec["nodes"].items():
        exo = label.startswith("~")          # "~" marks an outside influence: drawn in italics
        texts[key] = ax.text(x, y, label.lstrip("~"), ha="center", va="center", fontsize=fontsize,
                             color=INK, style="italic" if exo else "normal", linespacing=1.05,
                             bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none"), zorder=3)
    fig.canvas.draw()
    inv = ax.transData.inverted()
    for key, t in texts.items():
        bb = t.get_bbox_patch().get_window_extent()
        (x0, y0), (x1, y1) = inv.transform((bb.x0, bb.y0)), inv.transform((bb.x1, bb.y1))
        boxes[key] = (x0, y0, x1, y1)

    for link in spec["links"]:
        src, dst, sign = link[0], link[1], link[2]
        rad = link[3] if len(link) > 3 else 0.2
        opts = link[4] if len(link) > 4 else {}
        color = BLUE if sign == "+" else RED
        a, b = texts[src].get_position(), texts[dst].get_position()
        # a quadratic curve between the two centres (control point: middle + bend * normal)
        dx, dy = b[0] - a[0], b[1] - a[1]
        c = ((a[0] + b[0]) / 2 + rad * dy, (a[1] + b[1]) / 2 - rad * dx)
        length = math.hypot(dx, dy) or 1.0
        # where the arrow leaves the source box and reaches the target box (boxes are in data units, so
        # the result does not depend on the output resolution)
        t_out, t_in = 0.0, 1.0
        for k in range(1, 400):
            if not _inside(boxes[src], _bezier(a, c, b, k / 400)):
                t_out = k / 400
                break
        for k in range(399, 0, -1):
            if not _inside(boxes[dst], _bezier(a, c, b, k / 400)):
                t_in = k / 400
                break
        gap = 0.05 / length
        ts = [t_out + gap + (t_in - t_out - 2 * gap) * k / 60 for k in range(61)]
        ax.add_patch(FancyArrowPatch(path=Path([_bezier(a, c, b, t) for t in ts]), arrowstyle="-|>",
                                     mutation_scale=15, lw=1.6, color=color, zorder=2))
        # the sign: a little before the head, beside the line
        back = opts.get("sign_back", 0.42)
        t_sign = max(t_out, t_in - back / length)
        p = _bezier(a, c, b, t_sign)
        tx, ty = _tangent(a, c, b, t_sign)
        side = opts.get("sign_side", 1 if rad >= 0 else -1)   # default: outer side of the bend
        off = opts.get("sign_off", 0.23)
        ax.text(p[0] + side * ty * off, p[1] - side * tx * off, "+" if sign == "+" else "−",
                ha="center", va="center", fontsize=fontsize + 3, fontweight="bold", color=color, zorder=4)
        if opts.get("delay"):
            t_mid = (t_out + t_in) / 2
            p = _bezier(a, c, b, t_mid)
            tx, ty = _tangent(a, c, b, t_mid)
            for shift in (-0.06, 0.06):
                q = (p[0] + tx * shift, p[1] + ty * shift)
                ax.plot([q[0] - ty * 0.16, q[0] + ty * 0.16], [q[1] + tx * 0.16, q[1] - tx * 0.16],
                        color=color, lw=1.6, zorder=4, solid_capstyle="butt")

    for label, x, y, direction in spec.get("loops", []):
        r = spec.get("loop_radius", 0.34)
        start, sweep = 70.0, 300.0
        angles = [start + sweep * k / 60 for k in range(61)]
        if direction == "cw":
            angles = [180.0 - ang for ang in angles]
        verts = [(x + r * math.cos(math.radians(ang)), y + r * math.sin(math.radians(ang))) for ang in angles]
        ax.add_patch(FancyArrowPatch(path=Path(verts), arrowstyle="-|>", mutation_scale=11, lw=1.4,
                                     color=RED if label.startswith("B") else BLUE, zorder=2))
        ax.text(x, y, label, ha="center", va="center", fontsize=fontsize, fontweight="bold", color=INK, zorder=4)

    fig.savefig(out_png, dpi=300, facecolor="white")
    if out_svg:
        fig.savefig(out_svg, facecolor="white")
    plt.close(fig)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    draw_cld(spec, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print(f"written {sys.argv[2]}: {len(spec['nodes'])} variables, {len(spec['links'])} links, "
          f"{len(spec.get('loops', []))} loops marked")


if __name__ == "__main__":
    main()
