"""Writes the STELLA model file of the T4L Yellowstone model from yellowstone_model.py.

    python build_stmx.py OUT_DIR

writes
    Yellowstone.stmx                   the model: MODEL layer with the diagram, two graphs and a table;
                                       the Interface layer is left empty and is built by hand in STELLA
                                       (sliders and buttons, see notes/stella-guide_az.md)
    Yellowstone_with-interface.stmx    the same model with sliders, buttons and a graph already placed on
                                       the Interface layer (written from the XMILE 1.0 specification; if
                                       STELLA does not show them, use the first file)
    model-layer_expected.png           a drawing of how the MODEL layer should look after opening
    model-specification.md             every stock, flow and converter with its equation, unit and meaning
    equations_expected.txt             the listing the Equation layer of STELLA should show for this model

The file format is XMILE 1.0 (OASIS standard), which STELLA reads and writes as .stmx.  The element
names and attributes of the diagram, graphs and table follow model files saved by STELLA itself.
After opening, save the model from STELLA: the saved file is the one that is handed in.
"""
from __future__ import annotations

import math
import os
import sys
from xml.sax.saxutils import escape, quoteattr

import yellowstone_model as m

STOCK_W, STOCK_H, AUX_R = 45, 35, 18
PAGE_W, PAGE_H = 1240, 1250


def valve(flow):
    (x0, y0), (x1, y1) = flow["pts"]
    return (x0 + x1) / 2, (y0 + y1) / 2


def position(name):
    for s in m.STOCKS:
        if s["name"] == name:
            return s["x"], s["y"]
    for f in m.FLOWS:
        if f["name"] == name:
            return valve(f)
    for c in m.CONVERTERS:
        if c["name"] == name:
            return c["x"], c["y"]
    raise KeyError(name)


def connectors():
    """(from, to) for every variable used in the equation of a flow or converter."""
    pairs = []
    for v in m.FLOWS + m.CONVERTERS:
        for dep in m.dependencies(v["eqn"]):
            pairs.append((dep, v["name"]))
    return pairs


def angle(src, dst):
    (sx, sy), (tx, ty) = position(src), position(dst)
    return math.degrees(math.atan2(-(ty - sy), tx - sx)) % 360


VIEW_STYLE = """			<style color="black" background="white" font_style="normal" font_weight="normal" text_decoration="none" text_align="center" vertical_text_align="center" font_color="black" font_family="Arial" font_size="10pt" padding="2" border_color="black" border_width="thin" border_style="none">
				<text_box color="black" background="white" text_align="left" vertical_text_align="top" font_size="12pt"/>
				<numeric_display color="blue" background="white" font_size="9pt" isee:transparent="false"/>
				<graph color="black" background="white" font_size="12pt" axis_color="#666666" grid_color="#C8C8C8" isee:graph_area_color="white" legend_position="bottom" isee:transparent="false" isee:hide_border="false"/>
				<table color="black" background="#E0E0E0" text_align="right" font_size="12pt" orientation="vertical" wrap_text="false" isee:auto_fit="true" isee:use_alternate_row_colors="false" isee:unlimited_table_length="false" blank_column_width="80" column_width="160" isee:report_month_names="false" interval="1" report_balances="beginning" report_flows="instantaneous"/>
				<button color="black" background="#E0E0E0" font_size="9pt" transparent="false" corner_radius="0" isee:flat="false" icon_side="top"/>
				<slider color="black" background="white" num_ticks="3" label_side="top" wrap_title="true" input_expands="true" input_width="100"/>
				<knob color="black" background="white" label_side="bottom" wrap_title="true"/>
				<numeric_input color="black" background="white" label_side="left" wrap_title="true" input_expands="false" input_width="100"/>
				<switch color="black" background="#E0E0E0" font_size="9pt" label_side="top" wrap_title="true" isee:appearance="switch"/>
			</style>
"""

MODEL_STYLE = """				<style color="black" background="white" font_style="normal" font_weight="normal" text_decoration="none" text_align="center" vertical_text_align="center" font_color="black" font_family="Arial" font_size="9pt" padding="2" border_color="black" border_width="thin" border_style="none">
					<stock color="blue" background="white" font_color="blue" label_side="top">
						<shape type="rectangle" width="45" height="35"/>
					</stock>
					<flow color="blue" background="white" font_color="blue" label_side="bottom"/>
					<aux color="blue" background="white" font_color="blue" label_side="bottom">
						<shape type="circle" radius="18"/>
					</aux>
					<connector color="#FF007F" background="white" font_color="#FF007F" isee:thickness="1"/>
					<text_box color="black" background="white"/>
					<numeric_display color="black" background="white" isee:transparent="false"/>
					<graph color="black" background="white" font_size="12pt" axis_color="#666666" grid_color="#C8C8C8" isee:graph_area_color="white" legend_position="bottom" isee:transparent="false" isee:hide_border="false"/>
					<table color="black" background="white" orientation="vertical" wrap_text="false" isee:auto_fit="true" isee:use_alternate_row_colors="false" isee:unlimited_table_length="false" blank_column_width="80" column_width="160" isee:report_month_names="false" interval="1" report_balances="beginning" report_flows="instantaneous"/>
				</style>
"""

PLOT_COLORS = ["blue", "red", "#008F44", "#FF7F00"]


def graph_xml(uid, x, y, w, h, title, names, indent="\t\t\t\t"):
    out = [f'{indent}<stacked_container uid="{uid}" x="{x}" y="{y}" width="{w}" height="{h}">',
           f'{indent}\t<graph background="white" font_family="Arial" axis_label_font_size="9pt" x="{x + w / 2:g}" y="{y + h / 2:g}" '
           f'type="time_series" isee:time_precision="1" isee:time_scale_by="1" show_grid="true" include_units_in_legend="false" '
           f'plot_numbers="true" num_x_grid_lines="5" num_y_grid_lines="5" num_x_labels="6" num_y_labels="3" title={quoteattr(title)} '
           f'left_axis_multi_scale="true" left_axis_auto_scale="true" right_axis_multi_scale="true" right_axis_auto_scale="true">']
    for i, name in enumerate(names):
        out += [f'{indent}\t\t<plot color="{PLOT_COLORS[i % 4]}" pen_width="1" index="{i}" show_y_axis="true">',
                f'{indent}\t\t\t<format precision="1" scale_by="1"/>',
                f'{indent}\t\t\t<entity name="{m.ident(name)}"/>',
                f'{indent}\t\t</plot>']
    out += [f'{indent}\t</graph>', f'{indent}</stacked_container>']
    return out


def table_xml(uid, x, y, w, h, title, names, indent="\t\t\t\t"):
    out = [f'{indent}<stacked_container uid="{uid}" x="{x}" y="{y}" width="{w}" height="{h}">',
           f'{indent}\t<table background="#E0E0E0" font_family="Arial" font_size="9pt" orientation="vertical" column_width="80" interval="5" '
           f'report_balances="beginning" report_flows="instantaneous" header_text_align="center" header_font_size="9pt" '
           f'x="{x}" y="{y}" width="{w}" height="{h}" title={quoteattr(title)}>',
           f'{indent}\t\t<item type="time"/>']
    for name in names:
        out += [f'{indent}\t\t<item>', f'{indent}\t\t\t<format precision="0.1" scale_by="1" delimit_000s="true"/>',
                f'{indent}\t\t\t<entity name="{m.ident(name)}"/>', f'{indent}\t\t</item>']
    out += [f'{indent}\t</table>', f'{indent}</stacked_container>']
    return out


def build(with_interface: bool) -> str:
    x = ['<?xml version="1.0" encoding="utf-8"?>',
         '<xmile version="1.0" xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0" xmlns:isee="http://iseesystems.com/XMILE">',
         '\t<header>',
         '\t\t<smile version="1.0" namespace="std, isee"/>',
         '\t\t<name>Yellowstone</name>',
         '\t\t<uuid>7d3f4b52-0796-4a4c-9e1b-251a0d047e01</uuid>',
         '\t\t<vendor>RTU DE0796 T4L, Vagif Asgarli</vendor>',
         '\t\t<product version="1.0" lang="en">yellowstone_model.py (XMILE 1.0 for STELLA)</product>',
         '\t</header>',
         f'\t<sim_specs method="Euler" time_units="{m.TIME_UNITS}">',
         f'\t\t<start>{m.START}</start>', f'\t\t<stop>{m.STOP}</stop>', f'\t\t<dt>{m.DT}</dt>',
         '\t</sim_specs>',
         '\t<model>', '\t\t<variables>']
    for s in m.STOCKS:
        x += [f'\t\t\t<stock name={quoteattr(s["name"])}>', f'\t\t\t\t<doc>{escape(s["doc"])}</doc>',
              f'\t\t\t\t<eqn>{escape(s["init"])}</eqn>']
        x += [f'\t\t\t\t<inflow>{m.ident(f)}</inflow>' for f in s["inflows"]]
        x += [f'\t\t\t\t<outflow>{m.ident(f)}</outflow>' for f in s["outflows"]]
        x += ['\t\t\t\t<non_negative/>', f'\t\t\t\t<units>{escape(s["units"])}</units>', '\t\t\t</stock>']
    for f in m.FLOWS:
        x += [f'\t\t\t<flow name={quoteattr(f["name"])}>', f'\t\t\t\t<doc>{escape(f["doc"])}</doc>',
              f'\t\t\t\t<eqn>{escape(f["eqn"])}</eqn>', '\t\t\t\t<non_negative/>',
              f'\t\t\t\t<units>{escape(f["units"])}</units>', '\t\t\t</flow>']
    for c in m.CONVERTERS:
        x += [f'\t\t\t<aux name={quoteattr(c["name"])}>', f'\t\t\t\t<doc>{escape(c["doc"])}</doc>',
              f'\t\t\t\t<eqn>{escape(c["eqn"])}</eqn>']
        if "slider" in c:
            x.append(f'\t\t\t\t<range min="{c["slider"][0]:g}" max="{c["slider"][1]:g}"/>')
        x += [f'\t\t\t\t<units>{escape(c["units"])}</units>', '\t\t\t</aux>']
    x += ['\t\t</variables>', '\t\t<views>', VIEW_STYLE.rstrip("\n"),
          f'\t\t\t<view isee:show_pages="false" page_width="{PAGE_W}" page_height="{PAGE_H}" type="stock_flow">',
          MODEL_STYLE.rstrip("\n")]
    uid = 0
    for src, dst in connectors():
        uid += 1
        x += [f'\t\t\t\t<connector uid="{uid}" angle="{angle(src, dst):.3f}">',
              f'\t\t\t\t\t<from>{m.ident(src)}</from>', f'\t\t\t\t\t<to>{m.ident(dst)}</to>', '\t\t\t\t</connector>']
    for s in m.STOCKS:
        x.append(f'\t\t\t\t<stock label_side="{s.get("label", "top")}" x="{s["x"]}" y="{s["y"]}" name={quoteattr(s["name"])}/>')
    for f in m.FLOWS:
        vx, vy = valve(f)
        x += [f'\t\t\t\t<flow label_side="{f.get("label", "bottom")}" x="{vx:g}" y="{vy:g}" name={quoteattr(f["name"])}>', '\t\t\t\t\t<pts>']
        x += [f'\t\t\t\t\t\t<pt x="{px:g}" y="{py:g}"/>' for px, py in f["pts"]]
        x += ['\t\t\t\t\t</pts>', '\t\t\t\t</flow>']
    for c in m.CONVERTERS:
        x.append(f'\t\t\t\t<aux label_side="{c.get("label", "bottom")}" x="{c["x"]}" y="{c["y"]}" name={quoteattr(c["name"])}/>')
    stocks = [s["name"] for s in m.STOCKS]
    uid += 1
    x += graph_xml(uid, 60, 840, 540, 330, "Wolves and Deers", ["Wolves", "Deers"])
    uid += 1
    x += graph_xml(uid, 640, 840, 540, 330, "Vegetation and Beavers", ["Vegetation", "Beavers"])
    uid += 1
    x += table_xml(uid, 60, 1190, 520, 300, "Stocks every 5 years", stocks)
    x.append('\t\t\t</view>')
    if not with_interface:
        x += ['\t\t\t<view isee:show_pages="false" background="white" page_width="1066" page_height="600" home_view="true" type="interface">',
              '\t\t\t\t<style/>', '\t\t\t</view>']
    else:
        x += ['\t\t\t<view isee:show_pages="false" background="white" page_width="1066" page_height="600" home_view="true" type="interface">',
              '\t\t\t\t<style/>']
        uid += 1
        x.append(f'\t\t\t\t<text_box font_size="14pt" font_weight="bold" appearance="transparent" uid="{uid}" x="30" y="15" width="700" height="30">'
                 'Yellowstone: Wolves, Deers, Vegetation and Beavers</text_box>')
        sy = 70
        for c in m.CONVERTERS:
            if "slider" not in c:
                continue
            uid += 1
            lo, hi, _ = c["slider"]
            x += [f'\t\t\t\t<slider uid="{uid}" x="30" y="{sy}" width="230" height="48" min="{lo:g}" max="{hi:g}" show_name="true">',
                  f'\t\t\t\t\t<entity name="{m.ident(c["name"])}"/>', '\t\t\t\t</slider>']
            sy += 80
        for i, (label, action) in enumerate([("Run", "run"), ("Stop", "stop"), ("Restore all", "restore_all")]):
            uid += 1
            x += [f'\t\t\t\t<button uid="{uid}" x="{30 + 80 * i}" y="{sy + 10}" width="72" height="34" label="{label}">',
                  f'\t\t\t\t\t<menu_action>{action}</menu_action>', '\t\t\t\t</button>']
        uid += 1
        x += graph_xml(uid, 300, 60, 730, 250, "Wolves and Deers", ["Wolves", "Deers"])
        uid += 1
        x += graph_xml(uid, 300, 325, 730, 250, "Vegetation and Beavers", ["Vegetation", "Beavers"])
        x.append('\t\t\t</view>')
    x += ['\t\t</views>', '\t</model>', '</xmile>', '']
    return "\n".join(x)


def label_box(name):
    """Approximate box (x0, y0, x1, y1) of the name of an object on the model layer."""
    w = 5.4 * len(name) + 4
    for s in m.STOCKS:
        if s["name"] == name:
            if s.get("label") == "center":
                return (s["x"] - w / 2, s["y"] - 7, s["x"] + w / 2, s["y"] + 7)
            return (s["x"] - w / 2, s["y"] - STOCK_H / 2 - 18, s["x"] + w / 2, s["y"] - STOCK_H / 2 - 4)
    for f in m.FLOWS:
        if f["name"] == name:
            vx, vy = valve(f)
            side = f.get("label", "bottom")
            if side == "top":
                return (vx - w / 2, vy - 28, vx + w / 2, vy - 14)
            if side == "bottom":
                return (vx - w / 2, vy + 14, vx + w / 2, vy + 28)
            if side == "right":
                return (vx + 14, vy - 7, vx + 14 + w, vy + 7)
            return (vx - 14 - w, vy - 7, vx - 14, vy + 7)
    for c in m.CONVERTERS:
        if c["name"] == name:
            side = c.get("label", "bottom")
            if side == "top":
                return (c["x"] - w / 2, c["y"] - AUX_R - 17, c["x"] + w / 2, c["y"] - AUX_R - 3)
            if side == "right":
                return (c["x"] + AUX_R + 4, c["y"] - 7, c["x"] + AUX_R + 4 + w, c["y"] + 7)
            if side == "left":
                return (c["x"] - AUX_R - 4 - w, c["y"] - 7, c["x"] - AUX_R - 4, c["y"] + 7)
            return (c["x"] - w / 2, c["y"] + AUX_R + 3, c["x"] + w / 2, c["y"] + AUX_R + 17)
    raise KeyError(name)


def _seg_point_dist(a, b, p):
    (ax, ay), (bx, by), (px, py) = a, b, p
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _segments_cross(a, b, c, d):
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0


def _seg_hits_box(a, b, box, pad=2):
    x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    if any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in (a, b)):
        return True
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return any(_segments_cross(a, b, corners[i], corners[(i + 1) % 4]) for i in range(4))


def connector_segment(src, dst):
    (sx, sy), (tx, ty) = position(src), position(dst)
    d = math.hypot(tx - sx, ty - sy) or 1.0
    r0 = STOCK_H / 2 + 4 if any(s["name"] == src for s in m.STOCKS) else (9 if any(f["name"] == src for f in m.FLOWS) else AUX_R)
    r1 = 9 if any(f["name"] == dst for f in m.FLOWS) else AUX_R
    return (sx + (tx - sx) * r0 / d, sy + (ty - sy) * r0 / d), (tx - (tx - sx) * r1 / d, ty - (ty - sy) * r1 / d)


def check_layout():
    """Lists what would look untidy on the model layer: lines through objects or names, crossed lines."""
    problems = []
    segs = {(a, b): connector_segment(a, b) for a, b in connectors()}
    names = m.all_names()
    boxes = {n: label_box(n) for n in names}
    clouds = []
    for f in m.FLOWS:
        for p in f["pts"]:
            if not any(abs(p[0] - s["x"]) <= STOCK_W / 2 + 0.1 and abs(p[1] - s["y"]) <= STOCK_H / 2 + 0.1 for s in m.STOCKS):
                clouds.append((f["name"], p))
    for (a, b), (p, q) in segs.items():
        for n in names:
            if n in (a, b):
                continue
            centre = position(n)
            radius = 30 if any(s["name"] == n for s in m.STOCKS) else (13 if any(f["name"] == n for f in m.FLOWS) else AUX_R + 4)
            if _seg_point_dist(p, q, centre) < radius:
                problems.append(f"connector {a} -> {b} runs through {n}")
        for fname, c in clouds:
            if _seg_point_dist(p, q, c) < 15:
                problems.append(f"connector {a} -> {b} runs through the cloud of {fname}")
        for n, box in boxes.items():
            if n in (a, b) and any(st["name"] == n and st.get("label") == "center" for st in m.STOCKS):
                continue
            if _seg_hits_box(p, q, box):
                problems.append(f"connector {a} -> {b} runs through the name of {n}")
        for f in m.FLOWS:
            if f["name"] in (a, b) and False:
                continue
            (x0, y0), (x1, y1) = f["pts"]
            if _segments_cross(p, q, (x0, y0), (x1, y1)):
                problems.append(f"connector {a} -> {b} crosses the pipe of {f['name']}")
    keys = list(segs)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if len({*keys[i], *keys[j]}) == 4 and _segments_cross(*segs[keys[i]], *segs[keys[j]]):
                problems.append(f"connectors {keys[i][0]} -> {keys[i][1]} and {keys[j][0]} -> {keys[j][1]} cross")
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = boxes[names[i]], boxes[names[j]]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                problems.append(f"names of {names[i]} and {names[j]} overlap")
        for n in names:
            if n == names[i]:
                continue
            cx, cy = position(n)
            r = AUX_R if any(c["name"] == n for c in m.CONVERTERS) else (9 if any(f["name"] == n for f in m.FLOWS) else 24)
            a = boxes[names[i]]
            if a[0] - r < cx < a[2] + r and a[1] - r < cy < a[3] + r:
                problems.append(f"name of {names[i]} lies on {n}")
        for fname, c in clouds:
            a = boxes[names[i]]
            if a[0] - 11 < c[0] < a[2] + 11 and a[1] - 11 < c[1] < a[3] + 11:
                problems.append(f"name of {names[i]} lies on the cloud of {fname}")
    return problems


def draw_preview(path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

    blue, pink = "#1f3fbf", "#e0007f"
    xs = [position(n)[0] for n in m.all_names()] + [p[0] for f in m.FLOWS for p in f["pts"]]
    ys = [position(n)[1] for n in m.all_names()] + [p[1] for f in m.FLOWS for p in f["pts"]]
    x0, x1, y0, y1 = min(xs) - 90, max(xs) + 90, min(ys) - 50, max(ys) + 60
    fig, ax = plt.subplots(figsize=(12.4, 12.4 * (y1 - y0) / (x1 - x0)))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    for src, dst in connectors():
        a, b = connector_segment(src, dst)
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=8, lw=0.8, color=pink, zorder=2))
    for f in m.FLOWS:
        (fx0, fy0), (fx1, fy1) = f["pts"]
        ax.add_patch(FancyArrowPatch((fx0, fy0), (fx1, fy1), arrowstyle="-|>", mutation_scale=16, lw=4, color=blue, zorder=1,
                                     shrinkA=0, shrinkB=0))
        vx, vy = valve(f)
        ax.add_patch(Circle((vx, vy), 9, fc="white", ec=blue, lw=1.2, zorder=3))
        for p in ((fx0, fy0), (fx1, fy1)):
            if not any(abs(p[0] - s["x"]) <= STOCK_W / 2 + 0.1 and abs(p[1] - s["y"]) <= STOCK_H / 2 + 0.1 for s in m.STOCKS):
                ax.add_patch(Circle(p, 11, fc="white", ec=blue, lw=1, ls=(0, (2, 1.5)), zorder=3))
    for s in m.STOCKS:
        ax.add_patch(Rectangle((s["x"] - STOCK_W / 2, s["y"] - STOCK_H / 2), STOCK_W, STOCK_H, fc="white", ec=blue, lw=1.6, zorder=3))
    for c in m.CONVERTERS:
        ax.add_patch(Circle((c["x"], c["y"]), AUX_R, fc="#fff3c4" if "slider" in c else "white", ec=blue, lw=1.2, zorder=3))
    for n in m.all_names():
        bx0, by0, bx1, by1 = label_box(n)
        bold = any(s["name"] == n for s in m.STOCKS)
        ax.text((bx0 + bx1) / 2, (by0 + by1) / 2, n, ha="center", va="center", fontsize=7.6 if not bold else 9,
                fontweight="bold" if bold else "normal", color=blue, zorder=4)
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def specification() -> str:
    out = ["# Yellowstone stocks-and-flows model: specification", "",
           "Generated by `tools/build_stmx.py` from `tools/yellowstone_model.py`; the STELLA file has the same "
           "equations. This is what the Equation layer of STELLA lists.", "",
           f"Run specification: from {m.START} to {m.STOP}, DT = {m.DT} {m.TIME_UNITS.lower()}, Euler's method, "
           "stocks and flows non-negative.", "", "## Stocks", "",
           "| Stock | Initial value | Inflows | Outflows | Unit | Meaning |", "|---|---|---|---|---|---|"]
    for s in m.STOCKS:
        out.append(f'| {s["name"]} | `{s["init"]}` | {", ".join(s["inflows"])} | {", ".join(s["outflows"])} | {s["units"]} | {s["doc"]} |')
    out += ["", "Each stock follows `Stock(t) = Stock(t - dt) + (inflows - outflows) * dt`.", "", "## Flows", "",
            "| Flow | Equation | Unit | Meaning |", "|---|---|---|---|"]
    for f in m.FLOWS:
        out.append(f'| {f["name"]} | `{f["eqn"]}` | {f["units"]} | {f["doc"]} |')
    out += ["", "## Converters", "", "Converters with a slider range are the ones placed on the Interface layer.", "",
            "| Converter | Equation or value | Slider (min, max, step) | Unit | Meaning |", "|---|---|---|---|---|"]
    for c in m.CONVERTERS:
        sl = ", ".join(f"{v:g}" for v in c["slider"]) if "slider" in c else ""
        out.append(f'| {c["name"]} | `{c["eqn"]}` | {sl} | {c["units"]} | {c["doc"]} |')
    out += ["", "## Action connectors", "",
            f"{len(connectors())} connectors: one from every variable that appears in an equation to the flow or "
            "converter that uses it.", "", "| From | To |", "|---|---|"]
    out += [f"| {a} | {b} |" for a, b in connectors()]
    out += ["", "## Experiments", "", "| Experiment | Changed on the Interface layer |", "|---|---|"]
    for name, change in m.EXPERIMENTS.items():
        out.append(f'| {name} | {", ".join(f"{k} = {v}" for k, v in change.items()) or "nothing (default values)"} |')
    return "\n".join(out) + "\n"


def equations_listing() -> str:
    """What the Equation layer of classic STELLA lists for this model (stocks with their flows, then converters)."""
    out = []
    flow = {f["name"]: f for f in m.FLOWS}
    for s in sorted(m.STOCKS, key=lambda v: v["name"].lower()):
        name = m.ident(s["name"])
        ins = " + ".join(m.ident(f) for f in s["inflows"])
        outs = "".join(" - " + m.ident(f) for f in s["outflows"])
        out.append(f"{name}(t) = {name}(t - dt) + ({ins}{outs}) * dt")
        out.append(f"INIT {name} = {s['init']}")
        out.append("INFLOWS:")
        out += [f"    {m.ident(f)} = {flow[f]['eqn']}" for f in s["inflows"]]
        out.append("OUTFLOWS:")
        out += [f"    {m.ident(f)} = {flow[f]['eqn']}" for f in s["outflows"]]
    for c in sorted(m.CONVERTERS, key=lambda v: v["name"].lower()):
        out.append(f"{m.ident(c['name'])} = {c['eqn']}")
    return "\n".join(out) + "\n"


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)
    for fname, flag in (("Yellowstone.stmx", False), ("Yellowstone_with-interface.stmx", True)):
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(build(flag))
    with open(os.path.join(out_dir, "model-specification.md"), "w", encoding="utf-8") as f:
        f.write(specification())
    with open(os.path.join(out_dir, "equations_expected.txt"), "w", encoding="utf-8") as f:
        f.write(equations_listing())
    draw_preview(os.path.join(out_dir, "model-layer_expected.png"))
    for problem in check_layout():
        print("layout:", problem)
    print(f"{len(m.STOCKS)} stocks, {len(m.FLOWS)} flows, {len(m.CONVERTERS)} converters, {len(connectors())} connectors "
          f"written to {os.path.normpath(out_dir)}")


if __name__ == "__main__":
    main()
