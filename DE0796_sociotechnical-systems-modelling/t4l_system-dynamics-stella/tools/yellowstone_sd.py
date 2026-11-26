"""Reference simulation of the T4L Yellowstone stocks-and-flows model.

The same equations as the STELLA model (see ../notes/model-specification.md), integrated the way
STELLA does it by default: Euler's method, flows computed from the stock values at the start of
the step, uniflows never negative.  It is used to choose the parameters, to produce the expected
curves and tables, and to check the STELLA model: the STELLA table must show the same numbers.

    python yellowstone_sd.py [--out DIR]      # runs the experiments, writes CSV tables and PNG graphs
"""
from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass, asdict, replace


@dataclass(frozen=True)
class Params:
    # run specification (STELLA: Run > Run Specs)
    start: float = 1995.0
    stop: float = 2045.0
    dt: float = 0.25
    # initial values of the stocks
    wolves_released: float = 31.0          # slider: wolves brought to the park (0 = no reintroduction)
    initial_elk: float = 17000.0           # northern Yellowstone herd before the wolves
    initial_vegetation: float = 20.0       # willow/aspen condition, % of its potential
    initial_beavers: float = 1.0           # beaver colonies on the northern range
    # elk
    elk_birth_rate: float = 0.30           # calves per elk per year at low density
    elk_base_capacity: float = 25250.0     # elk the grassland alone can feed
    browse_capacity_gain: float = 8000.0   # extra elk fed when the woody vegetation is at its potential
    elk_death_rate: float = 0.06           # natural deaths per elk per year in a normal winter
    winter_severity: float = 1.0           # slider: multiplier of the natural death rate
    elk_hunting_rate: float = 0.05         # slider: share of the herd taken by hunters per year
    kill_coefficient: float = 0.0010       # elk killed per wolf per year, per elk present
    # wolves
    wolves_per_elk_eaten: float = 0.029    # new wolves raised per elk killed
    wolf_death_rate: float = 0.18          # natural deaths per wolf per year
    strife_coefficient: float = 0.0006     # extra death rate per wolf present (fights between packs, disease)
    wolf_hunting_rate: float = 0.0         # slider: share of the wolves shot per year
    # vegetation (willow, aspen, cottonwood)
    vegetation_growth_rate: float = 0.35   # regrowth per year when far below the potential
    vegetation_capacity: float = 100.0     # the potential, %
    browsing_per_1000_elk: float = 0.0165  # share of the vegetation eaten per year by 1,000 elk
    beaver_effect: float = 0.30            # extra regrowth when the beavers are at their capacity (ponds, water table)
    # beavers
    beaver_growth_rate: float = 2.0        # new colonies per colony per year where tall willow is unlimited
    beaver_capacity: float = 30.0          # colonies the streams of the northern range can hold
    beaver_loss_rate: float = 0.05         # colonies abandoned per colony per year
    willow_threshold: float = 15.0         # vegetation condition (%) below which no stream can hold a colony


def simulate(p: Params):
    """Euler integration; returns a list of rows (dicts), one per DT, like a STELLA table."""
    veg, elk, wolves, beavers = p.initial_vegetation, p.initial_elk, p.wolves_released, p.initial_beavers
    rows = []
    steps = int(round((p.stop - p.start) / p.dt))
    for k in range(steps + 1):
        t = p.start + k * p.dt
        # converters
        elk_capacity = p.elk_base_capacity + p.browse_capacity_gain * veg / p.vegetation_capacity
        beaver_help = 1.0 + p.beaver_effect * beavers / p.beaver_capacity
        habitat_share = max(0.0, (veg - p.willow_threshold) / (p.vegetation_capacity - p.willow_threshold))
        # flows (uniflows: never negative)
        regrowth = max(0.0, p.vegetation_growth_rate * veg * (1.0 - veg / p.vegetation_capacity) * beaver_help)
        browsing = max(0.0, p.browsing_per_1000_elk * veg * elk / 1000.0)
        elk_births = max(0.0, p.elk_birth_rate * elk * (1.0 - elk / elk_capacity))
        elk_deaths = max(0.0, p.elk_death_rate * p.winter_severity * elk)
        predation = max(0.0, p.kill_coefficient * wolves * elk)
        hunting = max(0.0, p.elk_hunting_rate * elk)
        wolf_births = max(0.0, p.wolves_per_elk_eaten * predation)
        wolf_deaths = max(0.0, (p.wolf_death_rate + p.strife_coefficient * wolves + p.wolf_hunting_rate) * wolves)
        colony_growth = max(0.0, p.beaver_growth_rate * beavers * habitat_share)
        colony_loss = max(0.0, (p.beaver_loss_rate + p.beaver_growth_rate * beavers / p.beaver_capacity) * beavers)
        rows.append(dict(time=t, Vegetation=veg, Elk=elk, Wolves=wolves, Beavers=beavers,
                         Regrowth=regrowth, Browsing=browsing, Elk_births=elk_births, Elk_deaths=elk_deaths,
                         Predation=predation, Hunting=hunting, Wolf_births=wolf_births, Wolf_deaths=wolf_deaths,
                         Colony_growth=colony_growth, Colony_loss=colony_loss, Elk_capacity=elk_capacity, Habitat_share=habitat_share))
        # stocks at the next step
        veg += (regrowth - browsing) * p.dt
        elk += (elk_births - elk_deaths - predation - hunting) * p.dt
        wolves += (wolf_births - wolf_deaths) * p.dt
        beavers += (colony_growth - colony_loss) * p.dt
        veg, elk, wolves, beavers = max(veg, 0.0), max(elk, 0.0), max(wolves, 0.0), max(beavers, 0.0)
    return rows


EXPERIMENTS = {
    "E1_base_31_wolves": dict(),
    "E2_no_wolves": dict(wolves_released=0.0),
    "E3_no_elk_hunting": dict(elk_hunting_rate=0.0),
    "E4_wolf_hunting_15pct": dict(wolf_hunting_rate=0.15),
    "E5_severe_winters": dict(winter_severity=2.0),
    "E6_100_wolves_released": dict(wolves_released=100.0),
}


def yearly(rows, every=5.0):
    return [r for r in rows if abs((r["time"] - rows[0]["time"]) / every - round((r["time"] - rows[0]["time"]) / every)) < 1e-9]


def write_csv(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([f"{r[c]:.2f}" if c != "time" else f"{r[c]:.2f}" for c in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "reference-simulation"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    base = Params()
    results = {name: simulate(replace(base, **change)) for name, change in EXPERIMENTS.items()}
    stocks = ["time", "Vegetation", "Elk", "Wolves", "Beavers"]
    for name, rows in results.items():
        write_csv(os.path.join(args.out, f"{name}.csv"), [r for r in rows if float(r["time"]).is_integer()], stocks)
    write_csv(os.path.join(args.out, "E1_base_all_variables_every_dt.csv"), results["E1_base_31_wolves"], list(results["E1_base_31_wolves"][0].keys()))
    for name, rows in results.items():
        print(f"\n{name}  ({EXPERIMENTS[name] or 'default parameters'})")
        print(f"{'year':>6} {'Vegetation':>11} {'Elk':>8} {'Wolves':>8} {'Beavers':>8}")
        for r in yearly(rows):
            print(f"{r['time']:6.0f} {r['Vegetation']:11.1f} {r['Elk']:8.0f} {r['Wolves']:8.1f} {r['Beavers']:8.1f}")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib is not installed: tables written, graphs skipped")
        return
    panels = [("Elk", "animals"), ("Wolves", "animals"), ("Vegetation", "% of potential"), ("Beavers", "colonies")]
    for name, rows in results.items():
        fig, axes = plt.subplots(2, 2, figsize=(10, 6.2), sharex=True)
        t = [r["time"] for r in rows]
        for ax, (var, unit) in zip(axes.flat, panels):
            ax.plot(t, [r[var] for r in rows], color="#1f4e79", lw=1.8)
            ax.set_title(var, fontsize=11); ax.set_ylabel(unit, fontsize=9); ax.grid(alpha=0.3); ax.set_ylim(bottom=0)
        fig.suptitle(name.replace("_", " "), fontsize=12)
        fig.tight_layout(); fig.savefig(os.path.join(args.out, f"{name}.png"), dpi=150); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.8), sharex=True)
    for ax, (var, unit) in zip(axes.flat, panels):
        for name, rows in results.items():
            ax.plot([r["time"] for r in rows], [r[var] for r in rows], lw=1.5, label=name.replace("_", " "))
        ax.set_title(var, fontsize=11); ax.set_ylabel(unit, fontsize=9); ax.grid(alpha=0.3); ax.set_ylim(bottom=0)
    axes[0, 0].legend(fontsize=7, loc="upper right")
    fig.tight_layout(); fig.savefig(os.path.join(args.out, "all_experiments.png"), dpi=150); plt.close(fig)
    print(f"\ntables and graphs written to {os.path.normpath(args.out)}")


if __name__ == "__main__":
    main()
