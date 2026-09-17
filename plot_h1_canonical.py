#!/usr/bin/env python3
"""Regenerate the H1 scatter (paper fig: output.png) from canonical outputs."""
import csv
from pathlib import Path
import numpy as np, statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = Path("/Users/cary/Documents/New project/outputs/canonical")
OUT = Path("/Users/cary/Documents/value-sensitivity-llm-audit/output.png")
prof = {r["Model"]: float(r["PVC"]) for r in csv.DictReader(open(P / "table2_orientation_profiles.csv", newline=""))}
burd = {r["Model"]: float(r["Mean_Delta"]) for r in csv.DictReader(open(P / "table3_burden_effects.csv", newline=""))}
models = sorted(prof, key=lambda m: prof[m], reverse=True)
PVC = np.array([prof[m] for m in models]); DELTA = np.array([burd[m] for m in models])
r1 = sm.OLS(DELTA, sm.add_constant(PVC)).fit()

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(PVC, DELTA, color="steelblue", s=70, zorder=5)
for i, m in enumerate(models):
    ax.annotate(m.replace(" Instruct", ""), (PVC[i], DELTA[i]), textcoords="offset points",
                xytext=(6, 4), fontsize=8)
xr = np.linspace(PVC.min() - 1, PVC.max() + 1, 100)
ax.plot(xr, r1.predict(sm.add_constant(xr)), color="darkred", linewidth=1.5, linestyle="--",
        label=rf"$\beta$={r1.params[1]:.2f}, $R^2$={r1.rsquared:.2f}")
ax.set_xlabel("PVOC (Policy-Value Orientation Composite)", fontsize=11)
ax.set_ylabel(r"Mean Burden Effect ($\Delta$ willingness)", fontsize=11)
ax.set_title("H1: Orientation-Effect Regression", fontsize=13)
ax.axhline(y=0, color="gray", linewidth=0.5, linestyle=":")
ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
plt.tight_layout(); fig.savefig(OUT, dpi=150); plt.close()
print(f"wrote {OUT}  beta={r1.params[1]:+.3f} R2={r1.rsquared:.3f} N={len(models)}")
