"""The T4L Yellowstone stocks-and-flows model, written down once.

Everything else is generated from this file:
  * yellowstone_sd.py      runs the equations (Euler, like STELLA) and writes the expected tables and graphs;
  * build_stmx.py          writes the STELLA model file (XMILE, .stmx) with the same equations and a layout;
  * check_stmx.py          runs the .stmx with an independent XMILE simulator and compares the numbers.

Names follow the STELLA convention: a name may contain spaces; inside an equation the spaces are
written as underscores.  Equations use only + - * / ( ) and MAX, so they mean the same in STELLA,
in XMILE and in Python.

The four stocks are the four variables of the T4LPrim causal loops diagram that carry the loops:
Wolves, Deers (elk), Vegetation (willow, aspen) and Beavers.
"""
from __future__ import annotations

START, STOP, DT, TIME_UNITS = 1995, 2045, 0.25, "Years"

# name, initial value (an equation), inflows, outflows, units, description, position on the model layer
STOCKS = [
    dict(name="Wolves", init="Wolves_released", inflows=["wolf births"], outflows=["wolf deaths"],
         units="wolves", x=360, y=170,
         doc="Wolves living in the park. The run starts in 1995 with the wolves that were released."),
    dict(name="Deers", init="Initial_deers", inflows=["deer births"], outflows=["deer deaths", "predation"],
         units="deers", x=820, y=350, label="center",
         doc="Deers (elk) of the northern Yellowstone herd, the main prey of the wolves."),
    dict(name="Vegetation", init="Initial_vegetation", inflows=["regrowth"], outflows=["browsing"],
         units="percent", x=820, y=720,
         doc="Condition of the willow, aspen and cottonwood stands, in percent of what the land can carry (100 = full)."),
    dict(name="Beavers", init="Initial_beaver_colonies", inflows=["colony growth"], outflows=["colony loss"],
         units="colonies", x=360, y=720,
         doc="Beaver colonies on the streams of the northern range."),
]

# name, equation, units, description, the two end points of the pipe (a point that is not on a stock is a
# cloud), side of the name
FLOWS = [
    dict(name="wolf births", eqn="Wolves_born_per_deer_eaten*predation", units="wolves/year",
         pts=[(510, 170), (382.5, 170)], label="top",
         doc="Pups that survive their first year: the more deers the packs kill, the more pups they raise."),
    dict(name="wolf deaths", eqn="Wolves*(Wolf_death_rate+Fights_and_diseases+Wolf_hunting_rate)", units="wolves/year",
         pts=[(337.5, 170), (190, 170)], label="top",
         doc="Wolves dying of age, of fights between packs and diseases (more when the wolves are many) and shot by people."),
    dict(name="deer births", eqn="Deer_birth_rate*Deers*MAX(0, 1-Deers/Deer_capacity)", units="deers/year",
         pts=[(650, 350), (797.5, 350)], label="top",
         doc="Calves that survive: fewer when the herd is close to the number the land can feed."),
    dict(name="deer deaths", eqn="Deers*(Deer_death_rate*Winter_severity+Bears_and_cougars_rate+Deer_hunting_rate)", units="deers/year",
         pts=[(842.5, 350), (990, 350)], label="top",
         doc="Deers dying of age and hunger in winter, killed by bears and cougars, and shot by hunters."),
    dict(name="predation", eqn="Kill_coefficient*Wolves*Deers", units="deers/year",
         pts=[(820, 332.5), (820, 240)], label="right",
         doc="Deers killed by wolves in a year."),
    dict(name="regrowth", eqn="Vegetation_growth_rate*Vegetation*MAX(0, 1-Vegetation/100)*Beaver_ponds_effect",
         units="percent/year", pts=[(650, 720), (797.5, 720)], label="bottom",
         doc="New growth of willow and aspen: slows down near 100 percent, faster where beaver ponds raise the water table."),
    dict(name="browsing", eqn="Browsing_per_1000_deers*Vegetation*Deers/1000", units="percent/year",
         pts=[(842.5, 720), (990, 720)], label="bottom",
         doc="Young willow and aspen eaten by the deers."),
    dict(name="colony growth", eqn="Beaver_growth_rate*Beavers*Free_habitat", units="colonies/year",
         pts=[(510, 720), (382.5, 720)], label="top",
         doc="New beaver colonies: beavers settle where tall willow gives food and dam material and the stream is free."),
    dict(name="colony loss", eqn="Beavers*Beaver_loss_rate", units="colonies/year",
         pts=[(337.5, 720), (190, 720)], label="top",
         doc="Colonies abandoned in a year."),
]

# name, equation or value, units, description, position; "slider": (min, max, step) puts it on the Interface layer
CONVERTERS = [
    # wolves
    dict(name="Wolves released", eqn="31", units="wolves", x=360, y=80, label="bottom", slider=(0, 100, 1),
         doc="Wolves brought to the park at the start (31 were released in 1995-1996). 0 = no reintroduction."),
    dict(name="Wolves born per deer eaten", eqn="0.032", units="wolves/deers", x=590, y=130, label="top",
         doc="Surviving pups per deer killed by the packs."),
    dict(name="Wolf death rate", eqn="0.15", units="1/year", x=180, y=260, label="bottom",
         doc="Share of the wolves dying in a year when the wolves are few."),
    dict(name="Strife coefficient", eqn="0.0012", units="1/wolves/year", x=360, y=280, label="top",
         doc="Extra death rate for every wolf living in the park."),
    dict(name="Fights and diseases", eqn="Strife_coefficient*Wolves", units="1/year", x=280, y=270, label="bottom",
         doc="Extra death rate from fights between packs and from diseases; grows with the number of wolves."),
    dict(name="Wolf hunting rate", eqn="0", units="1/year", x=90, y=230, label="bottom", slider=(0, 0.3, 0.01),
         doc="Share of the wolves shot by people in a year (0 inside the park)."),
    # deers
    dict(name="Initial deers", eqn="17000", units="deers", x=900, y=260, label="top",
         doc="Deers at the start: about 17,000 were counted when the wolves came back in 1995."),
    dict(name="Kill coefficient", eqn="0.0012", units="1/wolves/year", x=700, y=290, label="left",
         doc="Share of the herd one wolf kills in a year (0.0012 of 17,000 deers = 20 deers per wolf per year)."),
    dict(name="Deer birth rate", eqn="0.3", units="1/year", x=640, y=440, label="bottom",
         doc="Surviving calves per deer in a year when food is plentiful."),
    dict(name="Deer capacity", eqn="Grassland_capacity+Browse_capacity_gain*Vegetation/100", units="deers", x=724, y=480, label="right",
         doc="Deers the land can feed: the grassland plus the willow and aspen browse."),
    dict(name="Grassland capacity", eqn="25250", units="deers", x=620, y=520, label="left",
         doc="Deers the grassland alone can feed."),
    dict(name="Browse capacity gain", eqn="8000", units="deers", x=640, y=600, label="bottom",
         doc="Extra deers fed when the willow and aspen stands are at 100 percent."),
    dict(name="Deer death rate", eqn="0.04", units="1/year", x=916, y=420, label="bottom",
         doc="Share of the deers dying of age and hunger in a normal winter."),
    dict(name="Winter severity", eqn="1", units="1", x=1000, y=450, label="bottom", slider=(0.5, 3, 0.1),
         doc="1 = normal winter; 2 = twice as many deers die of cold and hunger."),
    dict(name="Bears and cougars rate", eqn="0.02", units="1/year", x=1090, y=420, label="bottom",
         doc="Share of the deers killed by bears and cougars in a year."),
    dict(name="Deer hunting rate", eqn="0.05", units="1/year", x=1100, y=300, label="top", slider=(0, 0.2, 0.01),
         doc="Share of the herd shot by hunters outside the park in a year."),
    # vegetation
    dict(name="Initial vegetation", eqn="20", units="percent", x=920, y=640, label="right",
         doc="Condition of the willow and aspen stands at the start: heavily browsed."),
    dict(name="Vegetation growth rate", eqn="0.35", units="1/year", x=724, y=690, label="top",
         doc="Regrowth per year when the stands are far below 100 percent."),
    dict(name="Browsing per 1000 deers", eqn="0.0165", units="1/deers/year", x=1000, y=750, label="bottom",
         doc="Share of the vegetation eaten in a year by 1,000 deers."),
    # beavers
    dict(name="Initial beaver colonies", eqn="1", units="colonies", x=290, y=640, label="bottom",
         doc="Beaver colonies at the start: one colony was found on the northern range in 1996."),
    dict(name="Beaver growth rate", eqn="2", units="1/year", x=420, y=810, label="bottom",
         doc="New colonies per colony in a year where tall willow is everywhere and the streams are free."),
    dict(name="Willow habitat", eqn="MAX(0, (Vegetation-Willow_threshold)/(100-Willow_threshold))", units="1", x=680, y=820, label="bottom",
         doc="Share of the streams with willow tall enough for beavers (0 to 1)."),
    dict(name="Willow threshold", eqn="15", units="percent", x=780, y=850, label="bottom",
         doc="Vegetation condition below which no stream can hold a colony."),
    dict(name="Free habitat", eqn="MAX(0, Willow_habitat-Beavers/Beaver_capacity)", units="1", x=520, y=780, label="bottom",
         doc="Share of the streams with tall willow that no colony occupies yet."),
    dict(name="Beaver capacity", eqn="30", units="colonies", x=580, y=740, label="right",
         doc="Colonies the streams of the northern range can hold."),
    dict(name="Beaver loss rate", eqn="0.05", units="1/year", x=200, y=810, label="bottom",
         doc="Share of the colonies abandoned in a year."),
    dict(name="Beaver ponds effect", eqn="1+Beaver_effect*Beavers/Beaver_capacity", units="1", x=460, y=640, label="left",
         doc="Faster regrowth where beaver ponds raise the water table (1 = no beavers)."),
    dict(name="Beaver effect", eqn="0.3", units="1", x=520, y=590, label="top",
         doc="Extra regrowth when the beavers are at their capacity."),
]

# the experiments of the protocol: name -> changed converter values
EXPERIMENTS = {
    "E1 base run: 31 wolves released": {},
    "E2 no wolves": {"Wolves released": 0},
    "E3 no deer hunting": {"Deer hunting rate": 0},
    "E4 wolves hunted, 15 % a year": {"Wolf hunting rate": 0.15},
    "E5 severe winters": {"Winter severity": 2},
    "E6 100 wolves released": {"Wolves released": 100},
}


def ident(name: str) -> str:
    """The name as it is written inside equations."""
    return name.replace(" ", "_")


def all_names() -> list[str]:
    return [v["name"] for v in STOCKS + FLOWS + CONVERTERS]


def dependencies(eqn: str) -> list[str]:
    """Names of the model variables an equation uses, in the order they appear."""
    import re
    known = {ident(n): n for n in all_names()}
    found = []
    for token in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", eqn):
        if token in known and known[token] not in found:
            found.append(known[token])
    return found
