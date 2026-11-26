"""Reference run of the T4L Yellowstone stocks-and-flows model (checking aid, not handed in).

Takes the equations from yellowstone_model.py and integrates them the way STELLA does by default:
Euler's method, flows computed from the stock values at the start of the step, stocks and flows
never negative.  The STELLA table must show the same numbers as the tables written here.

    python yellowstone_sd.py [--out DIR]      # runs the experiments, writes CSV tables and PNG graphs
"""
from __future__ import annotations

import argparse
import csv
import os

import yellowstone_model as m

OBSERVED_WOLVES = {1995: 21, 1996: 51, 2000: 119, 2001: 132, 2002: 148, 2003: 174, 2004: 171, 2005: 118, 2006: 136,
                   2007: 171, 2008: 124, 2009: 96, 2010: 97, 2011: 98, 2012: 83, 2013: 95, 2014: 104, 2015: 98,
                   2016: 108, 2017: 97, 2018: 80, 2019: 94, 2020: 123, 2021: 97, 2022: 108, 2023: 124, 2024: 108,
                   2025: 84}       # wolves in the park at the end of the year (Yellowstone Wolf Project annual reports)
OBSERVED_DEERS = {1995: 17000, 1998: 12000, 2000: 14000, 2004: 8335, 2010: 6070, 2013: 3915, 2018: 7579,
                  2023: 6651, 2024: 5597, 2025: 7226}   # northern Yellowstone elk winter counts (NPS; White et al., 2024)
OBSERVED_BEAVERS = {1996: 1, 2009: 12, 2015: 18}        # colonies on the northern range (Ripple & Beschta, 2012; Beschta & Ripple, 2016)


def simulate(changes: dict | None = None, start=m.START, stop=m.STOP, dt=m.DT):
    """Euler integration; returns a list of rows (dicts), one per DT, like a STELLA table."""
    changes = changes or {}
    eqn = {v["name"]: str(changes.get(v["name"], v["eqn"])) for v in m.FLOWS + m.CONVERTERS}
    code = {name: compile(e, name, "eval") for name, e in eqn.items()}
    order = _evaluation_order(eqn)
    env = {"MAX": max, "MIN": min, "__builtins__": {}}

    def evaluate(stocks):
        values = {m.ident(k): v for k, v in stocks.items()}
        for name in order:
            values[m.ident(name)] = float(eval(code[name], env, values))
        return values

    # initial values of the stocks may use converters (the sliders): evaluate the constants first
    constants = {}
    for name in order:
        try:
            constants[m.ident(name)] = float(eval(code[name], env, constants))
        except NameError:
            pass
    stocks = {s["name"]: float(eval(s["init"], env, constants)) for s in m.STOCKS}
    rows = []
    for k in range(int(round((stop - start) / dt)) + 1):
        values = evaluate(stocks)
        row = {"time": start + k * dt}
        row.update({name: values[m.ident(name)] for name in m.all_names()})
        rows.append(row)
        for s in m.STOCKS:
            net = sum(max(0.0, values[m.ident(f)]) for f in s["inflows"]) - sum(max(0.0, values[m.ident(f)]) for f in s["outflows"])
            stocks[s["name"]] = max(0.0, stocks[s["name"]] + net * dt)
    return rows


def _evaluation_order(eqn: dict) -> list[str]:
    stock_names = {s["name"] for s in m.STOCKS}
    done, order = set(stock_names), []
    while len(order) < len(eqn):
        progressed = False
        for name, e in eqn.items():
            if name not in done and all(d in done for d in m.dependencies(e)):
                order.append(name)
                done.add(name)
                progressed = True
        if not progressed:
            raise ValueError("circular equations: " + ", ".join(n for n in eqn if n not in done))
    return order


def every(rows, years=5.0):
    return [r for r in rows if abs((r["time"] - rows[0]["time"]) / years - round((r["time"] - rows[0]["time"]) / years)) < 1e-9]


def write_csv(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([f"{r[c]:.2f}" for c in cols])


def slug(name: str) -> str:
    """'E2 no wolves' -> 'E2_no-wolves'."""
    import re
    code, _, rest = name.partition(" ")
    return code + "_" + re.sub(r"[^a-z0-9]+", "-", rest.lower()).strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "reference-simulation"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    results = {name: simulate(change) for name, change in m.EXPERIMENTS.items()}
    stock_cols = ["time"] + [s["name"] for s in m.STOCKS]
    for name, rows in results.items():
        write_csv(os.path.join(args.out, f"{slug(name)}.csv"), [r for r in rows if float(r["time"]).is_integer()], stock_cols)
    base = results[next(iter(results))]
    write_csv(os.path.join(args.out, "E1_all-variables_every-dt.csv"), base, list(base[0].keys()))
    for name, rows in results.items():
        print(f"\n{name}")
        print(f"{'year':>6} {'Wolves':>8} {'Deers':>8} {'Vegetation':>11} {'Beavers':>8}")
        for r in every(rows):
            print(f"{r['time']:6.0f} {r['Wolves']:8.1f} {r['Deers']:8.0f} {r['Vegetation']:11.1f} {r['Beavers']:8.1f}")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib is not installed: tables written, graphs skipped")
        return
    panels = [("Wolves", "wolves", OBSERVED_WOLVES), ("Deers", "deers", OBSERVED_DEERS),
              ("Vegetation", "% of capacity", None), ("Beavers", "colonies", OBSERVED_BEAVERS)]
    for name, rows in results.items():
        fig, axes = plt.subplots(2, 2, figsize=(10, 6.2), sharex=True)
        t = [r["time"] for r in rows]
        for ax, (var, unit, obs) in zip(axes.flat, panels):
            ax.plot(t, [r[var] for r in rows], color="#1f4e79", lw=1.8, label="model")
            if obs and name.startswith("E1"):
                ax.plot(list(obs), list(obs.values()), "o", ms=3.5, color="#b5121b", label="counted in the park")
                ax.legend(fontsize=7, frameon=False)
            ax.set_title(var, fontsize=11)
            ax.set_ylabel(unit, fontsize=9)
            ax.grid(alpha=0.3)
            ax.set_ylim(bottom=0)
        fig.suptitle(name, fontsize=12)
        fig.tight_layout()
        fig.savefig(os.path.join(args.out, f"{slug(name)}.png"), dpi=150)
        plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.8), sharex=True)
    for ax, (var, unit, _) in zip(axes.flat, panels):
        for name, rows in results.items():
            ax.plot([r["time"] for r in rows], [r[var] for r in rows], lw=1.5, label=name)
        ax.set_title(var, fontsize=11)
        ax.set_ylabel(unit, fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_ylim(bottom=0)
    axes[0, 0].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "all-experiments.png"), dpi=150)
    plt.close(fig)
    print(f"\ntables and graphs written to {os.path.normpath(args.out)}")


if __name__ == "__main__":
    main()
