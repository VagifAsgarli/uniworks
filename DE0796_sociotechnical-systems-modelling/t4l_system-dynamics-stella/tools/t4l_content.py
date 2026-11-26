"""The text of the T4L protocol and presentation (one place, so both say the same).

Numbers of the experiments are not typed here: they are taken from the reference run
(yellowstone_sd.py), which uses the same equations as the STELLA model.
"""
from __future__ import annotations

import yellowstone_model as m
import yellowstone_sd as sd

NAME, STUDENT_ID = "Vagif Asgarli", "251ADM047"
DATE = "30. 11. 2026"

# --------------------------------------------------------------------------------------------- results
RUNS = {name: sd.simulate(change) for name, change in m.EXPERIMENTS.items()}


def _at(rows, year):
    return next(r for r in rows if abs(r["time"] - year) < 1e-9)


def _fmt(v, digits=0):
    return f"{v:,.{digits}f}"


BASE = RUNS[next(iter(RUNS))]
B = {y: _at(BASE, y) for y in (1995, 2000, 2002, 2005, 2010, 2015, 2020, 2025, 2045)}
WOLF_PEAK = max(BASE, key=lambda r: r["Wolves"])
DEER_MIN = min(BASE, key=lambda r: r["Deers"])
END = {name: rows[-1] for name, rows in RUNS.items()}
E = {name.split(" ")[0]: rows for name, rows in RUNS.items()}          # "E1" -> rows
EEND = {k: rows[-1] for k, rows in E.items()}
EPEAK = {k: max(rows, key=lambda r: r["Wolves"]) for k, rows in E.items()}
EMIN = {k: min(rows, key=lambda r: r["Deers"]) for k, rows in E.items()}

# ------------------------------------------------------------------------------------------ theory
STOCKS_AND_FLOWS = [
    "A Stocks and Flows model is the quantitative model of System Dynamics. A **stock** is an accumulation that "
    "characterizes the state of the system at a moment of time (here: the number of wolves); a **flow** is the "
    "rate that fills or drains a stock per unit of time (births per year). A stock changes only through its "
    "flows, so stocks accumulate the difference between inflows and outflows and are responsible for the delays "
    "in the system; mathematically stocks and flows represent differential equations (Ginters, 2026b). In STELLA "
    "two more elements complete the notation: a **converter** holds a constant or an auxiliary calculation, and "
    "an **action connector** shows that one element is used in the equation of another (Ginters, 2026b).",
    "Every element has a value or an equation, so the model can be simulated: the program calculates each stock "
    "step by step, Stock(t) = Stock(t − DT) + (inflows − outflows) × DT, and shows how the resources change in "
    "time and how they react to different rates.",
]

DIFFERENCES_INTRO = (
    "Both models describe the same feedback system, but at different levels (Table 1). The CLD is the conceptual "
    "model of systems thinking: it shows the cause and effect relationships between the variables and the "
    "balancing and reinforcing loops (Ginters, 2026a). The Stocks and Flows model is built from it for simulation.")

TABLE1_CAPTION = "Table 1. Differences between a Causal Loops Diagram and a Stocks and Flows model"
TABLE1 = [
    ("Aspect", "Causal Loops Diagram (CLD)", "Stocks and Flows model"),
    ("Purpose", "to understand the structure: what influences what, in which direction",
     "to calculate the behaviour: how much and when"),
    ("Elements", "variables, links with + or −, marks of reinforced (R) and balanced (B) feedbacks, delay marks",
     "stocks, flows, converters, action connectors"),
    ("Kinds of variables", "all variables look alike", "accumulations (stocks) are separated from rates (flows) and "
                                                         "from parameters (converters)"),
    ("Numbers", "none: no values, units or equations", "every element has a value or an equation; initial values "
                                                        "of the stocks and the time step DT are required"),
    ("Time", "not shown, only delay marks", "explicit: graphs and tables over the simulated period"),
    ("Result", "an explanation and a reasoned opinion, for example about stability",
     "curves, tables and experiments with changed rates"),
    ("Limit", "cannot tell which loop is stronger or how large an effect is",
     "needs values and assumptions, more work to build"),
]

# ------------------------------------------------------------------------------------- 1. CLD summary
CLD_SUMMARY = [
    "The CLD of T4LPrim (Figure 1) has 14 variables. In its centre are two populations, **Wolves** and **Deers** "
    "(the elk of the park). Each of them grows through a reinforced feedback of births (R1, R2). The predator and "
    "prey loop B1 balances both: more deers feed more wolf births, more wolves kill more deers, and the delay "
    "between them makes the two populations swing. The wolves are also limited by fights between packs and "
    "diseases (B2); the deers by their food, because they eat the vegetation their births depend on (B3), and by "
    "the hunting permits that people issue (B4).",
    "Vegetation, beavers and the water table form the reinforced feedback R3: willow feeds beavers, beaver ponds "
    "raise the water table, and wet banks grow more willow. The wolves reach this loop through the chain "
    "Wolves − Deers − Vegetation (two minus links, so more wolves mean more vegetation). Coyotes and scavengers "
    "depend on the wolves without closing a loop; winter severity and bears and cougars act from outside. Every "
    "reinforced loop is held by at least one balanced loop, so my opinion in T4LPrim was that the ecosystem is "
    "stable as long as the balanced feedbacks, above all B1, work.",
]
FIG_CLD_CAPTION = "Figure 1. Causal Loops Diagram of the Yellowstone ecosystem (T4LPrim)"

# ------------------------------------------------------------------------------------ 2. the model
MODEL_INTRO = [
    "The model was built in the STELLA environment from the CLD. The four variables that carry the loops became "
    "the **stocks**: Wolves, Deers, Vegetation (condition of the willow and aspen stands, in percent of what the "
    "land can carry) and Beavers (colonies). The links of the CLD became **flows** and **converters** (Table 2). "
    f"The model has {len(m.STOCKS)} stocks, {len(m.FLOWS)} flows and {len(m.CONVERTERS)} converters; it runs from "
    f"{m.START} to {m.STOP} with DT = {m.DT} years and Euler's method.",
]
TABLE2_CAPTION = "Table 2. From the CLD to the Stocks and Flows model"
TABLE2 = [
    ("In the CLD", "In the Stocks and Flows model"),
    ("Wolves, Deers (elk), Vegetation, Beavers", "the four stocks"),
    ("Wolf births (R1); Deers → Wolf births (B1)", "flow *wolf births* = Wolves born per deer eaten × predation"),
    ("Wolves → Deers (B1)", "flow *predation* = Kill coefficient × Wolves × Deers"),
    ("Pack fights, diseases (B2)", "converter *Fights and diseases* = Strife coefficient × Wolves, in the flow "
                                   "*wolf deaths*"),
    ("Deer births (R2); Vegetation → Deer births (B3)", "flow *deer births*, limited by the converter *Deer "
                                                        "capacity*, which grows with Vegetation"),
    ("Deers → Vegetation (B3)", "flow *browsing* = Browsing per 1000 deers × Vegetation × Deers / 1000"),
    ("Hunting permits (B4)", "converter *Deer hunting rate* (slider) in the flow *deer deaths*"),
    ("Winter severity; Bears, cougars", "converters *Winter severity* (slider) and *Bears and cougars rate* in "
                                        "the flow *deer deaths*"),
    ("Vegetation → Beavers (R3)", "converters *Willow habitat* and *Free habitat* in the flow *colony growth*"),
    ("Beaver ponds, water table → Vegetation (R3)", "converter *Beaver ponds effect* in the flow *regrowth*"),
    ("Coyotes; Carcasses; Scavengers", "not in the model: they do not act back on the four stocks"),
]

TABLE3_CAPTION = "Table 3. Stocks and flows of the model (as on the Equation layer)"


def table3():
    rows = [("Element", "Initial value or equation")]
    for s in m.STOCKS:
        rows.append((f"Stock **{s['name']}**", f"INIT = {s['init']};  inflow: {', '.join(s['inflows'])};  "
                                               f"outflow: {', '.join(s['outflows'])}"))
    for f in m.FLOWS:
        rows.append((f"Flow *{f['name']}*", f["eqn"].replace("*", "\\*")))
    for c in m.CONVERTERS:
        if not _is_number(c["eqn"]):
            rows.append((f"Converter {c['name']}", c["eqn"].replace("*", "\\*")))
    return rows


def _is_number(text):
    try:
        float(text)
        return True
    except ValueError:
        return False


VALUES_INTRO = (
    "**My own initial values and rates** are in Table 4. Three of them are taken from counts in the park; the "
    "others I chose so that (a) without wolves the model stays where the park was in 1995 and (b) with 31 wolves "
    "the base run resembles the later counts (section on experiments). They are assumptions of a simple teaching "
    "model, not measured rates.")
TABLE4_CAPTION = "Table 4. Initial values and rates (converters with a constant value)"
BASIS = {
    "Wolves released": "31 wolves were released in 1995–1996 (Phillips & Smith, 1997); **slider**",
    "Initial deers": "about 17,000 counted when the wolves came back in 1995 (National Park Service [NPS], 2025)",
    "Initial beaver colonies": "one colony on the northern range in 1996 (Ripple & Beschta, 2012)",
    "Initial vegetation": "own value: heavily browsed stands (Ripple & Beschta, 2012)",
    "Kill coefficient": "own value: 0.0012 × 17,000 = 20 deers per wolf per year; counted: 18–22 (NPS, 2026)",
    "Deer hunting rate": "own value; the late hunt took 5.7–18.7% of the herd in 1995–2002 (MacNulty et al., "
                         "2020); **slider**",
    "Wolf hunting rate": "0 inside the park; **slider** for the experiment",
    "Winter severity": "1 = normal winter; **slider**",
}


def table4():
    rows = [("Converter", "Value", "Unit", "Basis")]
    for c in m.CONVERTERS:
        if _is_number(c["eqn"]):
            rows.append((c["name"], c["eqn"], c["units"], BASIS.get(c["name"], "own value: " + c["doc"][0].lower() + c["doc"][1:].rstrip("."))))
    return rows


INTERFACE_TEXT = (
    "The **Interface layer** (Figure 2) is used to run the experiments without touching the model. It has four "
    "sliders (Wolves released, Wolf hunting rate, Deer hunting rate, Winter severity), three buttons (Run, Stop, "
    "Restore) and two graphs (Wolves and Deers; Vegetation and Beavers). Table output is shown in Figure 3.")
FIG_INTERFACE_CAPTION = "Figure 2. Interface layer of the model in STELLA after the base run (E1)"
FIG_TABLE_CAPTION = "Figure 3. Table of the stocks in STELLA, base run (E1)"
FIG_MODEL_CAPTION = "Figure 4. MODEL layer of the Yellowstone Stocks and Flows model in STELLA"
MODEL_LAYER_TEXT = (
    "Figure 4 is the MODEL layer. Each stock has its flows; the converters around a flow are the parameters of "
    "its equation, and every action connector corresponds to a variable used in an equation (Table 3).")

BASE_TEXT = [
    f"**Base run (E1): 31 wolves released.** The wolves grow fast while the deers are plentiful (R1): "
    f"{_fmt(B[2000]['Wolves'])} in 2000 and a peak of {_fmt(WOLF_PEAK['Wolves'])} in {WOLF_PEAK['time']:.0f}. "
    f"Predation then removes more deers than are born, and the herd falls from 17,000 to "
    f"{_fmt(DEER_MIN['Deers'])} in {DEER_MIN['time']:.0f} (B1). With fewer deers per wolf fewer pups survive, "
    f"fights and diseases (B2) add to the losses, and the wolves decline to about {_fmt(B[2020]['Wolves'])} in "
    f"2020. After that both populations swing with a shrinking amplitude and settle near "
    f"{_fmt(B[2045]['Wolves'])} wolves and {_fmt(B[2045]['Deers'])} deers: a damped oscillation, the behaviour of "
    f"a balanced loop with a delay.",
    f"The vegetation recovers only after the deers have declined ({_fmt(B[1995]['Vegetation'])}% in 1995, "
    f"{_fmt(B[2005]['Vegetation'])}% in 2005, {_fmt(B[2045]['Vegetation'])}% in 2045), and the beavers follow "
    f"about ten years later ({_fmt(B[2005]['Beavers'], 1)} colonies in 2005, {_fmt(B[2010]['Beavers'], 1)} in "
    f"2010, {_fmt(B[2015]['Beavers'], 1)} in 2015), because colonies need tall willow first (R3). The run "
    f"resembles the counts in the park: 174 wolves in 2003 (Smith et al., 2004) and 83–123 since 2009 (NPS, "
    f"2026); 6,070 deers in 2010 (NPS, 2025) and 7,226 in 2025 (Cassidy et al., 2026); 12 beaver colonies in 2009 "
    f"(Ripple & Beschta, 2012) and 18 in 2015 (Beschta & Ripple, 2016).",
]

TABLE5_CAPTION = "Table 5. Experiments: the stocks at the end of the run (2045) and the extremes on the way"


def table5():
    rows = [("Experiment", "Changed slider", "Wolves", "Deers", "Vegetation, %", "Beavers", "Wolf peak (year)",
             "Deer minimum (year)")]
    for name, change in m.EXPERIMENTS.items():
        k = name.split(" ")[0]
        ch = ", ".join(f"{a} = {b}" for a, b in change.items()) or "none"
        rows.append((name, ch, _fmt(EEND[k]["Wolves"]), _fmt(EEND[k]["Deers"]), _fmt(EEND[k]["Vegetation"]),
                     _fmt(EEND[k]["Beavers"], 1), f"{_fmt(EPEAK[k]['Wolves'])} ({EPEAK[k]['time']:.0f})",
                     f"{_fmt(EMIN[k]['Deers'])} ({EMIN[k]['time']:.0f})"))
    return rows


def _pct(a, b):
    return f"{abs(a / b - 1) * 100:.0f}%"


EXPERIMENT_TEXT = {
    "E2": f"**E2, no wolves.** Nothing changes for 50 years: {_fmt(EEND['E2']['Deers'])} deers, vegetation "
          f"{_fmt(EEND['E2']['Vegetation'])}%, {_fmt(EEND['E2']['Beavers'], 1)} beaver colonies. The deers are "
          f"limited only by food, winters and hunters (B3, B4), and R3 stays in its poor state. This is the park "
          f"before 1995: stable, but degraded.",
    "E3": f"**E3, no deer hunting.** More deers survive at first, and the wolves answer: their peak is "
          f"{_fmt(EPEAK['E3']['Wolves'])} and they settle at {_fmt(EEND['E3']['Wolves'])} instead of "
          f"{_fmt(EEND['E1']['Wolves'])}. The herd ends at {_fmt(EEND['E3']['Deers'])}, only "
          f"{_pct(EEND['E3']['Deers'], EEND['E1']['Deers'])} above the base run: the wolves take most of what "
          f"the hunters leave (B1).",
    "E4": f"**E4, wolves hunted, 15% a year.** The wolves settle at {_fmt(EEND['E4']['Wolves'])}, the deers at "
          f"{_fmt(EEND['E4']['Deers'])} ({_pct(EEND['E4']['Deers'], EEND['E1']['Deers'])} more than in the base "
          f"run), the vegetation reaches only {_fmt(EEND['E4']['Vegetation'])}% and the beavers "
          f"{_fmt(EEND['E4']['Beavers'], 1)} colonies. A decision of people about the top predator reaches the "
          f"willow and the beavers through the chain Wolves − Deers − Vegetation.",
    "E5": f"**E5, severe winters (twice the winter deaths).** The herd is smaller ({_fmt(EEND['E5']['Deers'])}), "
          f"so the wolves have less food ({_fmt(EEND['E5']['Wolves'])}), while the vegetation "
          f"({_fmt(EEND['E5']['Vegetation'])}%) and the beavers ({_fmt(EEND['E5']['Beavers'], 1)}) are the highest "
          f"of all runs. Winter replaces a part of the predation; the system stays stable at another level.",
    "E6": f"**E6, 100 wolves released.** The peak is higher and earlier ({_fmt(EPEAK['E6']['Wolves'])} in "
          f"{EPEAK['E6']['time']:.0f}) and the deer minimum deeper ({_fmt(EMIN['E6']['Deers'])} in "
          f"{EMIN['E6']['time']:.0f}), but the run ends where the base run ends: {_fmt(EEND['E6']['Wolves'])} "
          f"wolves, {_fmt(EEND['E6']['Deers'])} deers, {_fmt(EEND['E6']['Vegetation'])}%, "
          f"{_fmt(EEND['E6']['Beavers'], 1)} colonies. The balance does not depend on the initial number of "
          f"wolves, which is what stability means.",
}
EXPERIMENT_FIG = {
    "E2": "Figure 5. Experiment E2 in STELLA: no wolves (Wolves released = 0)",
    "E3": "Figure 6. Experiment E3 in STELLA: no deer hunting (Deer hunting rate = 0)",
    "E4": "Figure 7. Experiment E4 in STELLA: wolves hunted (Wolf hunting rate = 0.15)",
    "E5": "Figure 8. Experiment E5 in STELLA: severe winters (Winter severity = 2)",
    "E6": "Figure 9. Experiment E6 in STELLA: 100 wolves released",
}
EXPERIMENTS_INTRO = (
    "Six experiments were run from the Interface layer; before each one the Restore button returned the sliders "
    "to their default positions, then one slider was changed (Table 5).")

# --------------------------------------------------------------------------------------- 3. conclusions
CONCLUSIONS = [
    f"**Wolves.** Their prospects are good but limited by themselves and by their prey: in the model they do not "
    f"grow beyond {_fmt(WOLF_PEAK['Wolves'])} and settle near {_fmt(EEND['E1']['Wolves'])}, close to the 83–123 "
    f"counted since 2009 (NPS, 2026). The largest threat is people: hunting 15% a year lowers them to "
    f"{_fmt(EEND['E4']['Wolves'])}.",
    f"**Deers.** A smaller but steady herd of about {_fmt(EEND['E1']['Deers'])}, "
    f"{EEND['E1']['Deers'] / 17000 * 100:.0f}% of the 17,000 before the wolves; the park reports the northern herd "
    f"at about 40% of its pre-wolf abundance (White et al., 2024). The herd does not collapse, because fewer deers "
    f"mean fewer wolves (B1).",
    f"**Vegetation.** The best prospects of the four resources, but slow: from {_fmt(B[1995]['Vegetation'])}% to "
    f"{_fmt(EEND['E1']['Vegetation'])}% in about 20 years, and only if the wolves stay; without wolves it remains "
    f"at {_fmt(EEND['E2']['Vegetation'])}%.",
    f"**Beavers.** They gain the most (from 1 to {_fmt(EEND['E1']['Beavers'], 1)} colonies) and react last, "
    f"about ten years after the deers decline. They depend on decisions about wolves: "
    f"{_fmt(EEND['E4']['Beavers'], 1)} colonies when the wolves are hunted.",
    "**Stability.** The simulation supports the opinion of T4LPrim. All runs converge; different numbers of "
    "released wolves (E1, E6) lead to the same balance; without wolves (E2) the system rests in a second, poor "
    "state. The swings come from the delay in loop B1 and die out.",
    "**People.** Hunting rates and the policy on wolves are the levers of the system, which makes it a "
    "sociotechnical one: each slider changed the final state of all four stocks.",
    "**Limits.** The model is simple and its rates are my own values. It lets the wolves cause most of the decline "
    "of the deers, while studies also name hunters, winters, drought and bears (MacNulty et al., 2020), and it has "
    "no bison, no random weather and no stream hydrology, which can keep willow from recovering (Hobbs et al., "
    "2024). The results show directions and delays, not forecasts.",
    "**CLD and Stocks and Flows.** The CLD named the loops; the Stocks and Flows model showed which of them "
    "dominates and when: B1 sets the level of wolves and deers within about 15 years, R3 answers a decade later.",
]

PRESENTATION_NOTE = (
    "The presentation was prepared in MS PowerPoint on the template from ORTUS. The protocol (PDF), the stocks "
    "and flows model and the presentation are sent to egils.ginters@rtu.lv; the model is demonstrated in the "
    "STELLA environment during the defence.")

REFERENCES = [
    "Beschta, R. L., & Ripple, W. J. (2016). Riparian vegetation recovery in Yellowstone: The first two decades "
    "after wolf reintroduction. *Biological Conservation, 198*, 93–103. https://doi.org/10.1016/j.biocon.2016.03.031",
    "Cassidy, K. A., Stahler, D. R., Stahler, E. E., Metz, M., Rabe, J., SunderRaj, J., Rabe, T., Tatton, N., "
    "Packila, M., Cassidy, B., Binder, W., Lacey, C., Scott, G., & Ho, C. (2026). *Yellowstone National Park Wolf, "
    "Cougar, and Elk Project annual report 2025* (YCR-2026-01). National Park Service. "
    "https://www.nps.gov/yell/learn/upload/2025-YELL-Wolf-Cougar-Elk-Project-Annual-Report-508.pdf",
    "Ginters, E. (2026a). *T4. Systems thinking and dynamics simulation* [Lecture slides]. Riga Technical University.",
    "Ginters, E. (2026b). *T4L. System dynamics simulation in STELLA* [Lecture slides]. Riga Technical University.",
    "Hobbs, N. T., Johnston, D. B., Marshall, K. N., Wolf, E. C., & Cooper, D. J. (2024). Does restoring apex "
    "predators to food webs restore ecosystems? Large carnivores in Yellowstone as a model system. *Ecological "
    "Monographs, 94*(2), Article e1598. https://doi.org/10.1002/ecm.1598",
    "MacNulty, D. R., Stahler, D. R., Wyman, T., Ruprecht, J., Smith, L. M., Kohl, M. T., & Smith, D. W. (2020). "
    "Population dynamics of northern Yellowstone elk after wolf reintroduction. In D. W. Smith, D. R. Stahler, & "
    "D. R. MacNulty (Eds.), *Yellowstone wolves: Science and discovery in the world's first national park* "
    "(pp. 184–199). University of Chicago Press.",
    "National Park Service. (2025, April 18). *Elk*. Yellowstone National Park. "
    "https://www.nps.gov/yell/learn/nature/elk.htm",
    "National Park Service. (2026, September 9). *Wolf ecology*. Yellowstone National Park. "
    "https://www.nps.gov/yell/learn/nature/wolf.htm",
    "Phillips, M. K., & Smith, D. W. (1997). *Yellowstone Wolf Project: Biennial report 1995 and 1996* "
    "(YCR-NR-97-4). National Park Service. https://www.nps.gov/yell/learn/nature/upload/wolfreport_95-96_508.pdf",
    "Ripple, W. J., & Beschta, R. L. (2012). Trophic cascades in Yellowstone: The first 15 years after wolf "
    "reintroduction. *Biological Conservation, 145*(1), 205–213. https://doi.org/10.1016/j.biocon.2011.11.005",
    "Smith, D. W., Stahler, D. R., & Guernsey, D. S. (2004). *Yellowstone Wolf Project: Annual report, 2003* "
    "(YCR-NR-2004-04). National Park Service. https://www.nps.gov/yell/learn/nature/upload/wolfrpt03.pdf",
    "White, P. J., Stahler, D. R., Smith, D. W., MacNulty, D. R., & Garrott, R. A. (2024). *Northern Yellowstone "
    "elk: Resilience and adaptation to changes in management policies and the ecosystem*. National Park Service. "
    "https://www.nps.gov/yell/learn/nature/upload/ELK-BOOK-FOR-WEB_accessible.pdf",
]
AI_NOTE = ("Note. Generative AI tools were used for information retrieval, for designing and checking the model, "
           "for drafting the text and for formatting the reference list: Claude (Anthropic).")

# the screenshots taken in STELLA (see notes/stella-guide_az.md): file name -> what it shows
SHOTS = {
    "model": "01_model-layer.png",
    "E1": "02_interface_E1.png",
    "table": "03_table_E1.png",
    "E2": "04_interface_E2.png",
    "E3": "05_interface_E3.png",
    "E4": "06_interface_E4.png",
    "E5": "07_interface_E5.png",
    "E6": "08_interface_E6.png",
}
