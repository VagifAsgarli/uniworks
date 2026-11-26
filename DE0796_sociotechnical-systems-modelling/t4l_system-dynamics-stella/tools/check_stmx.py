"""Checks the STELLA model file against the reference run.

    python check_stmx.py ../outputs/model/Yellowstone.stmx

The .stmx is read and simulated by PySD (an independent XMILE simulator) for every experiment of
yellowstone_model.py; the stocks must agree with yellowstone_sd.py at every DT.  This proves that
the equations written into the file are the ones of the specification; it does not replace opening
the file in STELLA.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import pysd

import yellowstone_model as m
import yellowstone_sd as sd


def main():
    path = sys.argv[1]
    work = tempfile.mkdtemp()
    local = os.path.join(work, "model.stmx")
    shutil.copy(path, local)
    model = pysd.read_xmile(local)
    worst = 0.0
    for name, change in m.EXPERIMENTS.items():
        ref = sd.simulate(change)
        params = {m.ident(k).lower(): v for k, v in change.items()}
        model.reload() if hasattr(model, "reload") else None
        out = model.run(params=params, return_columns=[s["name"] for s in m.STOCKS])
        diff = 0.0
        for row in ref:
            for s in m.STOCKS:
                got = float(out.loc[row["time"], s["name"]])
                diff = max(diff, abs(got - row[s["name"]]) / max(1.0, abs(row[s["name"]])))
        worst = max(worst, diff)
        last = out.iloc[-1]
        print(f"{name:34s} max relative difference {diff:.2e}   2045: " +
              ", ".join(f"{s['name']} {float(last[s['name']]):.1f}" for s in m.STOCKS))
    shutil.rmtree(work, ignore_errors=True)
    if worst > 1e-9:
        sys.exit(f"MISMATCH: the model file and the reference run differ (max {worst:.3e})")
    print(f"OK: {os.path.basename(path)} reproduces the reference run in all {len(m.EXPERIMENTS)} experiments")


if __name__ == "__main__":
    main()
