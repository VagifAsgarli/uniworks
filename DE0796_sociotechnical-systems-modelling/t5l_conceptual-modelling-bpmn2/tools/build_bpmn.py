"""CyberFlow: BPMN 2.0 model of the handling of a significant cyber incident (T5L).

The model is described once, in the tables below, and from them this script

  * checks the logic of the model (see `check`),
  * writes the BPMN 2.0 XML file with the diagram layout (opens in any BPMN 2.0 tool),
  * writes the element and connection tables used in the ARIS Express build guide.

The file is the *reference* of the model. The figure handed in is drawn from it in ARIS Express
(the lecturer's rule); `render_bpmn.js` only draws the reference picture to copy from.

    python build_bpmn.py cyberflow_incident-handling.bpmn [tables.md]
"""
from __future__ import annotations

import sys
from xml.sax.saxutils import escape, quoteattr

# ----------------------------------------------------------------------------- pools and lanes
POOL_X, POOL_W, HEAD = 160, 2330, 30
POOLS = [
    dict(id="Pool_Org", name="Organisation (essential entity)", process="Process_Org", y=80, h=850, lanes=[
        dict(id="Lane_Employee", name="Employee", y=80, h=100),
        dict(id="Lane_IT", name="IT operations", y=180, h=300),
        dict(id="Lane_SOC", name="SOC analyst", y=480, h=220),
        dict(id="Lane_CM", name="Cybersecurity manager (CISO)", y=700, h=230),
    ]),
    dict(id="Pool_CSIRT", name="CSIRT (CERT.LV)", process="Process_CSIRT", y=1000, h=150, lanes=[]),
]
GAP_Y = 965          # the middle of the space between the two pools (message flows bend and are named here)

# ----------------------------------------------------------------------------- flow nodes
# id: (kind, name, lane or pool, centre x, centre y, label box (dx, dy, w, h) relative to the centre or None)
SIZE = {"task": (120, 70), "start": (36, 36), "msgstart": (36, 36), "end": (36, 36), "timer": (36, 36),
        "msgcatch": (36, 36), "xor": (50, 50), "and": (50, 50), "or": (50, 50), "dataobject": (36, 50),
        "datastore": (50, 50)}
BELOW = (-55, 22, 110, 40)
Y_EMP, Y_IT1, Y_IT2, Y_IT3, Y_SOC, Y_CM, Y_CSIRT = 130, 245, 340, 435, 590, 810, 1075
NODES = {
    # Organisation, lane Employee
    "S1":  ("start", "Suspicious activity noticed", "Lane_Employee", 270, Y_EMP, (-55, 22, 110, 28)),
    "T1":  ("task", "Report the suspicious event", "Lane_Employee", 385, Y_EMP, None),
    # lane SOC analyst
    "T2":  ("task", "Register and classify the event", "Lane_SOC", 555, Y_SOC, None),
    "T5":  ("task", "Handle as a routine event", "Lane_SOC", 830, Y_SOC, None),
    "E1":  ("end", "Routine event closed", "Lane_SOC", 943, Y_SOC, (-45, 22, 90, 28)),
    "G2":  ("and", "", "Lane_SOC", 1105, Y_SOC, None),
    "T10": ("task", "Collect and preserve evidence", "Lane_SOC", 1315, Y_SOC, None),
    "G3":  ("and", "", "Lane_SOC", 1500, Y_SOC, None),
    "T12": ("task", "Prepare the initial assessment", "Lane_SOC", 1620, Y_SOC, None),
    # lane Cybersecurity manager
    "T4":  ("task", "Assess the significance", "Lane_CM", 710, Y_CM, None),
    "G1":  ("xor", "Significant incident?", "Lane_CM", 830, Y_CM, (-55, 30, 110, 28)),
    "T6":  ("task", "Activate the incident procedure", "Lane_CM", 960, Y_CM, None),
    "TE1": ("timer", "Time limit: 24 h after becoming aware", "Lane_CM", 1185, Y_CM, BELOW),
    "T11": ("task", "Send the early warning", "Lane_CM", 1315, Y_CM, None),
    "ME1": ("msgcatch", "Feedback and guidance received", "Lane_CM", 1430, Y_CM, (8, 22, 100, 28)),
    "TE2": ("timer", "Time limit: 72 h after becoming aware", "Lane_CM", 1695, Y_CM, BELOW),
    "T13": ("task", "Send the incident notification", "Lane_CM", 1810, Y_CM, None),
    "T15": ("task", "Review and update the procedure model", "Lane_CM", 1970, Y_CM, None),
    "TE3": ("timer", "Time limit: one month after the notification", "Lane_CM", 2088, Y_CM, BELOW),
    "T16": ("task", "Prepare and send the final report", "Lane_CM", 2206, Y_CM, None),
    "E2":  ("end", "Incident closed", "Lane_CM", 2324, Y_CM, (-45, 22, 90, 14)),
    # lane IT operations
    "G4":  ("or", "Which measures are needed?", "Lane_IT", 1185, Y_IT2, (-73, -66, 66, 42)),
    "T7":  ("task", "Isolate the affected systems", "Lane_IT", 1315, Y_IT1, None),
    "T8":  ("task", "Block accounts and addresses", "Lane_IT", 1315, Y_IT2, None),
    "T9":  ("task", "Switch to backup systems", "Lane_IT", 1315, Y_IT3, None),
    "G5":  ("or", "", "Lane_IT", 1440, Y_IT2, None),
    "T14": ("task", "Remove the cause, restore services", "Lane_IT", 1810, Y_IT3, None),
    # pool CSIRT
    "CS1": ("msgstart", "Early warning received", "Pool_CSIRT", 1125, Y_CSIRT, (-45, 22, 90, 28)),
    "C1":  ("task", "Register and assess the early warning", "Pool_CSIRT", 1240, Y_CSIRT, None),
    "C2":  ("task", "Send feedback and guidance", "Pool_CSIRT", 1430, Y_CSIRT, None),
    "CS2": ("msgcatch", "Incident notification received", "Pool_CSIRT", 1810, Y_CSIRT, (-50, 22, 100, 28)),
    "C3":  ("task", "Assess the incident notification", "Pool_CSIRT", 1960, Y_CSIRT, None),
    "CS3": ("msgcatch", "Final report received", "Pool_CSIRT", 2206, Y_CSIRT, (-45, 22, 90, 28)),
    "C4":  ("task", "Evaluate the final report, close the case", "Pool_CSIRT", 2324, Y_CSIRT, None),
    "CE":  ("end", "Case closed", "Pool_CSIRT", 2437, Y_CSIRT, (-40, 22, 80, 14)),
}

# data objects and data stores: id: (kind, name, lane, centre x, centre y, label box relative to the centre)
DATA = {
    "DO1":  ("dataobject", "Incident ticket", "Lane_SOC", 655, 665, (24, -14, 70, 28)),
    "DS1a": ("datastore", "Procedure models", "Lane_CM", 960, 890, (30, -12, 70, 28)),
    "DO2":  ("dataobject", "Evidence package", "Lane_SOC", 1315, 520, (24, -14, 70, 28)),
    "DO3":  ("dataobject", "Initial assessment", "Lane_SOC", 1715, 665, (24, -14, 70, 28)),
    "DS1b": ("datastore", "Procedure models", "Lane_CM", 1970, 890, (-102, -12, 70, 28)),
    "DO4":  ("dataobject", "Final report", "Lane_CM", 2206, 740, (24, -8, 70, 14)),
}
DATASTORE_ROOT = ("DataStore_Models", "Procedure models (CyberFlow repository)")

# ----------------------------------------------------------------------------- connections
# sequence flows: id, from, side, to, side, name, optional corner coordinate (x of the vertical or y of the horizontal part)
# a side is l, r, t or b, optionally with a shift along the side, e.g. "t+20"
SEQ = [
    ("F01", "S1", "r", "T1", "l", "", None),
    ("F02", "T1", "r", "T2", "l", "", 470),
    ("F03", "T2", "b", "T4", "l", "", None),
    ("F04", "T4", "r", "G1", "l", "", None),
    ("F05", "G1", "t", "T5", "b", "No", None),
    ("F06", "T5", "r", "E1", "l", "", None),
    ("F07", "G1", "r", "T6", "l", "Yes", None),
    ("F08", "T6", "r", "G2", "l", "", 1055),
    ("F09", "G2", "t", "G4", "l", "", None),
    ("F10", "G2", "r", "T10", "l", "", None),
    ("F11", "G2", "b", "TE1", "l", "", None),
    ("F12", "G4", "t", "T7", "l", "", None),
    ("F13", "G4", "r", "T8", "l", "", None),
    ("F14", "G4", "b", "T9", "l", "", None),
    ("F15", "T7", "r", "G5", "t", "", None),
    ("F16", "T8", "r", "G5", "l", "", None),
    ("F17", "T9", "r", "G5", "b", "", None),
    ("F18", "TE1", "r", "T11", "l", "", None),
    ("F19", "T11", "r", "ME1", "l", "", None),
    ("F20", "G5", "r", "G3", "t", "", None),
    ("F21", "T10", "r", "G3", "l", "", None),
    ("F22", "ME1", "r", "G3", "b", "", None),
    ("F23", "G3", "r", "T12", "l", "", None),
    ("F24", "T12", "b", "TE2", "l", "", None),
    ("F25", "TE2", "r", "T13", "l", "", None),
    ("F26", "T13", "t+20", "T14", "b+20", "", None),
    ("F27", "T14", "r", "T15", "t", "", None),
    ("F28", "T15", "r", "TE3", "l", "", None),
    ("F29", "TE3", "r", "T16", "l", "", None),
    ("F30", "T16", "r", "E2", "l", "", None),
    ("F31", "CS1", "r", "C1", "l", "", None),
    ("F32", "C1", "r", "C2", "l", "", None),
    ("F33", "C2", "r", "CS2", "l", "", None),
    ("F34", "CS2", "r", "C3", "l", "", None),
    ("F35", "C3", "r", "CS3", "l", "", None),
    ("F36", "CS3", "r", "C4", "l", "", None),
    ("F37", "C4", "r", "CE", "l", "", None),
]
# message flows: id, from, side, to, side, name, label box (x, y, w, h); a flow whose ends are not one above
# the other bends in the space between the pools
MSG = [
    ("M1", "T11", "b", "CS1", "t", "Early warning", (1178, 945, 84, 14)),
    ("M2", "C2", "t", "ME1", "b", "Feedback and guidance", (1438, 951, 84, 28)),
    ("M3", "T13", "b", "CS2", "t", "Incident notification", (1818, 951, 70, 28)),
    ("M4", "T16", "b", "CS3", "t", "Final report", (2214, 958, 70, 14)),
]
# data lines (data associations): id, from, to, the two end points
ASSOC = [
    ("D1", "T2", "DO1", (607, 625), (639, 646)),
    ("D2", "DO1", "T4", (661, 690), (690, 775)),
    ("D3", "DS1a", "T6", (960, 865), (960, 845)),
    ("D4", "T10", "DO2", (1315, 555), (1315, 545)),
    ("D5", "T12", "DO3", (1680, 612), (1699, 648)),
    ("D6", "DO3", "T13", (1722, 690), (1780, 775)),
    ("D7", "T15", "DS1b", (1970, 845), (1970, 865)),
    ("D8", "T16", "DO4", (2206, 775), (2206, 765)),
]
# the split and the join that belong together
PAIRS = [("G2", "G3", "and"), ("G4", "G5", "or")]

KIND_TEXT = {"start": "Start event", "msgstart": "Start event (Message)", "end": "End event",
             "timer": "Intermediate event (Timer)", "msgcatch": "Intermediate event (Message, catch)",
             "task": "Task", "xor": "Gateway XOR (exclusive)", "and": "Gateway AND (parallel)",
             "or": "Gateway OR (inclusive)", "dataobject": "Data object", "datastore": "Data store"}


# ----------------------------------------------------------------------------- geometry
def bounds(node_id):
    kind, _, _, cx, cy, _ = (NODES.get(node_id) or DATA[node_id])
    w, h = SIZE[kind]
    return cx - w / 2, cy - h / 2, w, h


def dock(node_id, side):
    x, y, w, h = bounds(node_id)
    shift = 0
    if len(side) > 1:
        shift = int(side[1:])
        side = side[0]
    return {"l": (x, y + h / 2 + shift), "r": (x + w, y + h / 2 + shift),
            "t": (x + w / 2 + shift, y), "b": (x + w / 2 + shift, y + h)}[side]


def route(src, s_side, dst, d_side, corner=None):
    """Right-angled line between two docking points."""
    (sx, sy), (dx, dy) = dock(src, s_side), dock(dst, d_side)
    s_h, d_h = s_side[0] in "lr", d_side[0] in "lr"
    if s_h and d_h:
        if sy == dy:
            return [(sx, sy), (dx, dy)]
        mx = corner if corner is not None else (sx + dx) / 2
        return [(sx, sy), (mx, sy), (mx, dy), (dx, dy)]
    if not s_h and not d_h:
        if sx == dx:
            return [(sx, sy), (dx, dy)]
        my = corner if corner is not None else (sy + dy) / 2
        return [(sx, sy), (sx, my), (dx, my), (dx, dy)]
    if s_h:                                     # horizontal first, then vertical
        return [(sx, sy), (dx, sy), (dx, dy)]
    return [(sx, sy), (sx, dy), (dx, dy)]       # vertical first, then horizontal


def pool_of(place):
    for p in POOLS:
        if place == p["id"] or any(l["id"] == place for l in p["lanes"]):
            return p["id"]
    raise KeyError(place)


def segments(points):
    return list(zip(points[:-1], points[1:]))


def crosses(a, b):
    """True if two segments cross or overlap (touching at a shared end point does not count)."""
    (x1, y1), (x2, y2) = a
    (x3, y3), (x4, y4) = b
    ends = {(x1, y1), (x2, y2)} & {(x3, y3), (x4, y4)}

    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (v > 1e-9) - (v < -1e-9)

    def on(p, q, r):
        return min(p[0], q[0]) - 1e-9 <= r[0] <= max(p[0], q[0]) + 1e-9 and min(p[1], q[1]) - 1e-9 <= r[1] <= max(p[1], q[1]) + 1e-9

    p1, p2, p3, p4 = (x1, y1), (x2, y2), (x3, y3), (x4, y4)
    o1, o2, o3, o4 = orient(p1, p2, p3), orient(p1, p2, p4), orient(p3, p4, p1), orient(p3, p4, p2)
    if o1 != o2 and o3 != o4:
        hit = True
    else:
        hit = (o1 == 0 and on(p1, p2, p3)) or (o2 == 0 and on(p1, p2, p4)) or (o3 == 0 and on(p3, p4, p1)) or (o4 == 0 and on(p3, p4, p2))
    if not hit:
        return False
    if ends:                                    # they share an end point: only a real overlap counts
        if o1 == o2 == o3 == o4 == 0:           # collinear
            shared = next(iter(ends))
            others = [p for p in (p1, p2, p3, p4) if p != shared]
            return any(on(p1, p2, o) and on(p3, p4, o) for o in others)
        return False
    return True


def seg_hits_box(seg, box, pad=2):
    """True if a segment passes through a rectangle (x, y, w, h)."""
    (x1, y1), (x2, y2) = seg
    bx, by, bw, bh = box
    bx, by, bw, bh = bx + pad, by + pad, bw - 2 * pad, bh - 2 * pad
    for k in range(41):
        t = k / 40
        px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        if bx < px < bx + bw and by < py < by + bh:
            return True
    return False


# ----------------------------------------------------------------------------- checks
def check():
    problems = []
    seq_out, seq_in = {n: [] for n in NODES}, {n: [] for n in NODES}
    for fid, s, _, d, _, _, _ in SEQ:
        seq_out[s].append(d)
        seq_in[d].append(s)
        if pool_of(NODES[s][2]) != pool_of(NODES[d][2]):
            problems.append(f"{fid}: a sequence flow crosses a pool border ({s} -> {d})")
    for mid, s, _, d, _, _, _ in MSG:
        if pool_of(NODES[s][2]) == pool_of(NODES[d][2]):
            problems.append(f"{mid}: a message flow inside one pool ({s} -> {d})")
    msg_in = {m[3] for m in MSG}
    for n, (kind, *_rest) in NODES.items():
        i, o = len(seq_in[n]), len(seq_out[n])
        if kind in ("start", "msgstart") and (i != 0 or o != 1):
            problems.append(f"{n}: a start event needs no incoming and one outgoing flow")
        if kind == "end" and (i < 1 or o != 0):
            problems.append(f"{n}: an end event needs incoming flows only")
        if kind in ("task", "timer", "msgcatch") and (i != 1 or o != 1):
            problems.append(f"{n}: needs exactly one incoming and one outgoing flow (has {i}, {o})")
        if kind in ("xor", "and", "or") and not ((i == 1 and o >= 2) or (i >= 2 and o == 1)):
            problems.append(f"{n}: a gateway must either split or join (has {i} in, {o} out)")
        if kind in ("msgstart", "msgcatch") and n not in msg_in:
            problems.append(f"{n}: a message event without an incoming message flow")
    starts = [n for n, v in NODES.items() if v[0] in ("start", "msgstart")]
    ends = {n for n, v in NODES.items() if v[0] == "end"}

    def reach(frm, graph):
        seen, todo = set(), list(frm)
        while todo:
            n = todo.pop()
            if n not in seen:
                seen.add(n)
                todo.extend(graph[n])
        return seen

    forward, backward = reach(starts, seq_out), reach(ends, seq_in)
    for n in NODES:
        if n not in forward:
            problems.append(f"{n}: cannot be reached from a start event")
        if n not in backward:
            problems.append(f"{n}: no path from here to an end event")
    for split, join, kind in PAIRS:              # every branch of the split must meet again at its own join
        if NODES[split][0] != kind or NODES[join][0] != kind:
            problems.append(f"{split}/{join}: split and join are not both {kind}")
        for first in seq_out[split]:
            n, steps = first, 0
            while n != join and steps < 50:
                if len(seq_out[n]) != 1 and not any(n == s for s, _, _ in PAIRS):
                    problems.append(f"{split}: branch through {first} leaves the block at {n}")
                    break
                # a nested block: jump to its join
                nested = [j for s, j, _ in PAIRS if s == n]
                n = seq_out[nested[0]][0] if nested else seq_out[n][0]
                steps += 1
        if len(seq_in[join]) != len(seq_out[split]):
            problems.append(f"{split}/{join}: {len(seq_out[split])} branches leave, {len(seq_in[join])} arrive")
    # layout: no line crosses another line or runs through a symbol that it does not connect
    lines = [(f[0], f[1], f[3], route(f[1], f[2], f[3], f[4], f[6])) for f in SEQ]
    lines += [(m[0], m[1], m[3], route(m[1], m[2], m[3], m[4], GAP_Y)) for m in MSG]
    lines += [(a[0], a[1], a[2], [a[3], a[4]]) for a in ASSOC]
    for i, (id1, s1, d1, pts1) in enumerate(lines):
        for seg in segments(pts1):
            for other in list(NODES) + list(DATA):
                if other not in (s1, d1) and seg_hits_box(seg, bounds(other)):
                    problems.append(f"{id1}: the line runs through {other}")
        for id2, s2, d2, pts2 in lines[i + 1:]:
            if any(crosses(a, b) for a in segments(pts1) for b in segments(pts2)):
                problems.append(f"{id1} and {id2}: the lines cross or overlap")
    for n in list(NODES) + list(DATA):           # every symbol lies inside its lane or pool
        place = (NODES.get(n) or DATA[n])[2]
        x, y, w, h = bounds(n)
        for p in POOLS:
            for area in [p] + p["lanes"]:
                if area["id"] == place and not (area["y"] <= y and y + h <= area["y"] + area["h"]
                                                and POOL_X + HEAD <= x and x + w <= POOL_X + POOL_W):
                    problems.append(f"{n}: outside {place}")
    return problems


def summary():
    kinds = {}
    for kind, *_ in NODES.values():
        kinds[kind] = kinds.get(kind, 0) + 1
    lines = ["Model contents:"]
    lines.append(f"  pools: {len(POOLS)} (" + "; ".join(f"{p['name']}: {len(p['lanes']) or 'no'} lanes" for p in POOLS) + ")")
    lines.append("  events: " + ", ".join(f"{kinds.get(k, 0)} x {KIND_TEXT[k]}" for k in ("start", "msgstart", "timer", "msgcatch", "end")))
    lines.append("  gateways: " + ", ".join(f"{kinds.get(k, 0)} x {k.upper()}" for k in ("xor", "and", "or")))
    lines.append(f"  tasks: {kinds['task']}; sequence flows: {len(SEQ)}; message flows: {len(MSG)}; data lines: {len(ASSOC)}")
    lines.append(f"  data objects: {sum(1 for v in DATA.values() if v[0] == 'dataobject')}; "
                 f"data store symbols: {sum(1 for v in DATA.values() if v[0] == 'datastore')} (one store shown twice)")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- BPMN 2.0 XML
TAG = {"task": "task", "start": "startEvent", "msgstart": "startEvent", "end": "endEvent",
       "timer": "intermediateCatchEvent", "msgcatch": "intermediateCatchEvent",
       "xor": "exclusiveGateway", "and": "parallelGateway", "or": "inclusiveGateway"}


def xml():
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
         'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
         'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
         'id="Definitions_CyberFlow" targetNamespace="http://bpmn.io/schema/bpmn" '
         'exporter="build_bpmn.py" exporterVersion="1.0">',
         '  <bpmn:collaboration id="Collaboration_CyberFlow">']
    for p in POOLS:
        o.append(f'    <bpmn:participant id="{p["id"]}" name={quoteattr(p["name"])} processRef="{p["process"]}" />')
    for mid, s, _, d, _, name, _ in MSG:
        o.append(f'    <bpmn:messageFlow id="{mid}" name={quoteattr(name)} sourceRef="{s}" targetRef="{d}" />')
    o.append('  </bpmn:collaboration>')
    o.append(f'  <bpmn:dataStore id="{DATASTORE_ROOT[0]}" name={quoteattr(DATASTORE_ROOT[1])} />')
    for p in POOLS:
        o.append(f'  <bpmn:process id="{p["process"]}" name={quoteattr(p["name"])} isExecutable="false">')
        members = [n for n, v in NODES.items() if pool_of(v[2]) == p["id"]]
        if p["lanes"]:
            o.append(f'    <bpmn:laneSet id="LaneSet_{p["id"]}">')
            for lane in p["lanes"]:
                o.append(f'      <bpmn:lane id="{lane["id"]}" name={quoteattr(lane["name"])}>')
                o += [f'        <bpmn:flowNodeRef>{n}</bpmn:flowNodeRef>' for n in members if NODES[n][2] == lane["id"]]
                o.append('      </bpmn:lane>')
            o.append('    </bpmn:laneSet>')
        for n in members:
            kind, name, *_ = NODES[n]
            attrs = f'id="{n}"' + (f' name={quoteattr(name)}' if name else "")
            o.append(f'    <bpmn:{TAG[kind]} {attrs}>')
            o += [f'      <bpmn:incoming>{f[0]}</bpmn:incoming>' for f in SEQ if f[3] == n]
            o += [f'      <bpmn:outgoing>{f[0]}</bpmn:outgoing>' for f in SEQ if f[1] == n]
            inputs = [a for a in ASSOC if a[2] == n]
            if inputs:
                o.append(f'      <bpmn:property id="Property_{n}" name="__targetRef_placeholder" />')
            for a in inputs:
                o.append(f'      <bpmn:dataInputAssociation id="{a[0]}"><bpmn:sourceRef>{a[1]}</bpmn:sourceRef>'
                         f'<bpmn:targetRef>Property_{n}</bpmn:targetRef></bpmn:dataInputAssociation>')
            for a in [a for a in ASSOC if a[1] == n]:
                o.append(f'      <bpmn:dataOutputAssociation id="{a[0]}"><bpmn:targetRef>{a[2]}</bpmn:targetRef>'
                         f'</bpmn:dataOutputAssociation>')
            if kind == "timer":
                o.append(f'      <bpmn:timerEventDefinition id="TimerDef_{n}" />')
            if kind in ("msgstart", "msgcatch"):
                o.append(f'      <bpmn:messageEventDefinition id="MessageDef_{n}" />')
            o.append(f'    </bpmn:{TAG[kind]}>')
        for d, (kind, name, place, *_rest) in DATA.items():
            if pool_of(place) != p["id"]:
                continue
            if kind == "dataobject":
                o.append(f'    <bpmn:dataObjectReference id="{d}" name={quoteattr(name)} dataObjectRef="DataObject_{d}" />')
                o.append(f'    <bpmn:dataObject id="DataObject_{d}" />')
            else:
                o.append(f'    <bpmn:dataStoreReference id="{d}" name={quoteattr(name)} dataStoreRef="{DATASTORE_ROOT[0]}" />')
        for fid, s, _, d, _, name, _ in SEQ:
            if pool_of(NODES[s][2]) == p["id"]:
                o.append(f'    <bpmn:sequenceFlow id="{fid}"' + (f' name={quoteattr(name)}' if name else "")
                         + f' sourceRef="{s}" targetRef="{d}" />')
        o.append('  </bpmn:process>')
    # diagram interchange
    o.append('  <bpmndi:BPMNDiagram id="BPMNDiagram_CyberFlow">')
    o.append('    <bpmndi:BPMNPlane id="BPMNPlane_CyberFlow" bpmnElement="Collaboration_CyberFlow">')

    def shape(elem, x, y, w, h, extra="", label=None):
        o.append(f'      <bpmndi:BPMNShape id="{elem}_di" bpmnElement="{elem}"{extra}>')
        o.append(f'        <dc:Bounds x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" />')
        if label:
            o.append(f'        <bpmndi:BPMNLabel><dc:Bounds x="{label[0]:g}" y="{label[1]:g}" width="{label[2]:g}" '
                     f'height="{label[3]:g}" /></bpmndi:BPMNLabel>')
        o.append('      </bpmndi:BPMNShape>')

    def edge(elem, pts, label=None):
        o.append(f'      <bpmndi:BPMNEdge id="{elem}_di" bpmnElement="{elem}">')
        o.extend(f'        <di:waypoint x="{x:g}" y="{y:g}" />' for x, y in pts)
        if label:
            o.append(f'        <bpmndi:BPMNLabel><dc:Bounds x="{label[0]:g}" y="{label[1]:g}" width="{label[2]:g}" '
                     f'height="{label[3]:g}" /></bpmndi:BPMNLabel>')
        o.append('      </bpmndi:BPMNEdge>')

    for p in POOLS:
        shape(p["id"], POOL_X, p["y"], POOL_W, p["h"], ' isHorizontal="true"')
        for lane in p["lanes"]:
            shape(lane["id"], POOL_X + HEAD, lane["y"], POOL_W - HEAD, lane["h"], ' isHorizontal="true"')
    for n in list(NODES) + list(DATA):
        kind, name, _, cx, cy, lab = (NODES.get(n) or DATA[n])
        x, y, w, h = bounds(n)
        label = (cx + lab[0], cy + lab[1], lab[2], lab[3]) if (lab and name) else None
        shape(n, x, y, w, h, ' isMarkerVisible="true"' if kind == "xor" else "", label)
    for fid, s, ss, d, ds, name, corner in SEQ:
        pts = route(s, ss, d, ds, corner)
        label = None
        if name:                                   # "Yes" / "No" next to the first segment
            (x1, y1), (x2, y2) = pts[0], pts[1]
            label = (x1 + 6, (y1 + y2) / 2 - 7, 24, 14) if x1 == x2 else (x1 + 6, y1 - 20, 24, 14)
        edge(fid, pts, label)
    for mid, s, ss, d, ds, name, label in MSG:
        edge(mid, route(s, ss, d, ds, GAP_Y), label)
    for aid, _, _, p1, p2 in ASSOC:
        edge(aid, [p1, p2])
    o += ['    </bpmndi:BPMNPlane>', '  </bpmndi:BPMNDiagram>', '</bpmn:definitions>', '']
    return "\n".join(o)


# ----------------------------------------------------------------------------- tables for the build guide
def place_text(place):
    for p in POOLS:
        if place == p["id"]:
            return p["name"]
        for lane in p["lanes"]:
            if lane["id"] == place:
                return f'{p["name"]} / {lane["name"]}'
    return place


def tables():
    rows = ["| ID | Type | Name | Pool / Swimlane |", "|---|---|---|---|"]
    order = sorted(NODES, key=lambda n: (pool_of(NODES[n][2]) != "Pool_Org", NODES[n][3], NODES[n][4]))
    for n in order:
        kind, name, place, *_ = NODES[n]
        rows.append(f"| {n} | {KIND_TEXT[kind]} | {name or '(no name)'} | {place_text(place)} |")
    for d, (kind, name, place, *_rest) in DATA.items():
        rows.append(f"| {d} | {KIND_TEXT[kind]} | {name} | {place_text(place)} |")
    rows += ["", "| ID | From | To | Type | Label |", "|---|---|---|---|---|"]

    def nm(n):
        v = NODES.get(n) or DATA[n]
        return f"{n} {v[1]}".strip()

    for fid, s, _, d, _, name, _ in SEQ:
        rows.append(f"| {fid} | {nm(s)} | {nm(d)} | Sequence flow | {name} |")
    for mid, s, _, d, _, name, _ in MSG:
        rows.append(f"| {mid} | {nm(s)} | {nm(d)} | Message flow | {name} |")
    for aid, s, d, _, _ in ASSOC:
        rows.append(f"| {aid} | {nm(s)} | {nm(d)} | Data line (data association) | |")
    return "\n".join(rows) + "\n"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    problems = check()
    print(summary())
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("checks passed: flows stay inside their pools, message flows connect different pools, every node lies "
          "on a path from a start to an end event, every split has its join, no line crosses another line or a symbol")
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(xml())
    print("written", sys.argv[1])
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(tables())
        print("written", sys.argv[2])


if __name__ == "__main__":
    main()
