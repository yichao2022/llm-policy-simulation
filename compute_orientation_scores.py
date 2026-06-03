#!/usr/bin/env python3
"""
Compute policy-value orientation scores from orientation_responses_filled.csv.
Outputs: orientation_scores.csv, table2_orientation_profiles.csv, table2_orientation_profiles.tex
"""

import csv
import statistics
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
INPUT_CSV = PROJECT / "outputs" / "orientation_responses_filled.csv"
OUTPUT_SCORES = PROJECT / "outputs" / "orientation_scores.csv"
OUTPUT_TABLE_CSV = PROJECT / "outputs" / "table2_orientation_profiles.csv"
OUTPUT_TABLE_TEX = PROJECT / "outputs" / "table2_orientation_profiles.tex"

DIMENSIONS = ["AP", "ST", "CO", "BS", "CA"]


def load_filled(path: Path) -> list[dict]:
    """Load filled CSV and compute reverse-coded scores."""
    rows = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get("raw_score", "").strip()
            if raw and row.get("score_valid", "").strip() == "1":
                score = int(raw)
                rev = int(row.get("reverse_coded", "0"))
                row["_score"] = 8 - score if rev == 1 else score
            else:
                row["_score"] = None
            rows.append(row)
    return rows


def compute_dimension_means(rows: list[dict]) -> dict:
    """Compute per-model mean scores for each dimension."""
    # Group by (model, dimension)
    dim_scores = defaultdict(list)
    for r in rows:
        if r["_score"] is not None:
            dim_scores[(r["model"], r["dimension"])].append(r["_score"])

    model_dims = defaultdict(dict)
    for (model, dim), scores in dim_scores.items():
        if scores:
            model_dims[model][dim] = round(statistics.mean(scores), 2)

    return model_dims


def compute_z_scores(model_dims: dict) -> dict:
    """Compute z-scores for each dimension across models."""
    all_models = sorted(model_dims.keys())
    z_scores = defaultdict(dict)

    for dim in DIMENSIONS:
        values = [model_dims[m].get(dim) for m in all_models if dim in model_dims[m]]
        if len(values) < 2:
            continue
        mean = statistics.mean(values)
        sd = statistics.stdev(values)
        for model in all_models:
            if dim in model_dims[model]:
                raw = model_dims[model][dim]
                z_scores[model][f"z_{dim}"] = round((raw - mean) / sd, 3) if sd > 0 else 0.0

    return z_scores


def compute_pvc(z_scores: dict) -> dict:
    """PVC = z_AP - z_ST - z_CO + z_BS + z_CA"""
    pvc = {}
    for model, zs in z_scores.items():
        pvc[model] = round(
            zs.get("z_AP", 0)
            - zs.get("z_ST", 0)
            - zs.get("z_CO", 0)
            + zs.get("z_BS", 0)
            + zs.get("z_CA", 0),
            3,
        )
    return pvc


def export_scores(model_dims, z_scores, pvc):
    """Write orientation_scores.csv."""
    all_models = sorted(model_dims.keys())
    fieldnames = ["model", "provider"] + DIMENSIONS + [f"z_{d}" for d in DIMENSIONS] + ["PVC"]

    with open(OUTPUT_SCORES, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for model in all_models:
            row = {"model": model, "provider": ""}
            for dim in DIMENSIONS:
                row[dim] = model_dims[model].get(dim, "")
            for dim in DIMENSIONS:
                row[f"z_{dim}"] = z_scores.get(model, {}).get(f"z_{dim}", "")
            row["PVC"] = pvc.get(model, "")
            writer.writerow(row)

    print(f"Scores saved: {OUTPUT_SCORES}")


def export_table2(model_dims, pvc, z_scores):
    """Write table2 CSV and TeX, sorted by PVC descending."""
    # Build table rows
    table = []
    for model, pvc_val in sorted(pvc.items(), key=lambda x: x[1], reverse=True):
        row = {"Model": model, "PVC": pvc_val}
        for dim in DIMENSIONS:
            row[dim] = model_dims[model].get(dim, "")
        table.append(row)

    # CSV
    with open(OUTPUT_TABLE_CSV, "w", newline="") as f:
        fieldnames = ["Model"] + DIMENSIONS + ["PVC"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table)
    print(f"Table 2 CSV saved: {OUTPUT_TABLE_CSV}")

    # TeX
    tex_lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Policy-Value Orientation Profiles by Model (sorted by PVC)}",
        r"\label{tab:orientation-profiles}",
        r"\begin{tabular}{l" + "c" * (len(DIMENSIONS) + 1) + "}",
        r"\toprule",
        r"Model & " + " & ".join(DIMENSIONS) + r" & PVC \\",
        r"\midrule",
    ]
    for row in table:
        vals = " & ".join(str(row.get(d, "")) for d in DIMENSIONS)
        tex_lines.append(f"{row['Model']} & {vals} & {row['PVC']} \\\\")

    tex_lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    with open(OUTPUT_TABLE_TEX, "w") as f:
        f.write("\n".join(tex_lines) + "\n")
    print(f"Table 2 TeX saved: {OUTPUT_TABLE_TEX}")


def print_table(model_dims, pvc):
    """Pretty-print Table 2 to terminal."""
    header = f"{'Model':<30} {'AP':>6} {'ST':>6} {'CO':>6} {'BS':>6} {'CA':>6} {'PVC':>8}"
    sep = "-" * len(header)
    print(f"\n{sep}")
    print(header)
    print(sep)
    for model, pvc_val in sorted(pvc.items(), key=lambda x: x[1], reverse=True):
        dims = " ".join(f"{model_dims[model].get(d, '-'):>6}" for d in DIMENSIONS)
        print(f"{model:<30} {dims} {pvc_val:>8.3f}")
    print(sep)


def validate_input(rows: list[dict]) -> bool:
    """Run pre-flight checks on the filled responses."""
    print("=== Pre-flight validation ===")
    all_ok = True

    # 1. Row count
    print(f"Total rows: {len(rows)}")
    if len(rows) != 180:
        print(f"  FAIL: expected 180 rows, got {len(rows)}")
        all_ok = False

    # 2. Score validity
    invalid = [r for r in rows if r.get("score_valid", "").strip() != "1"]
    if invalid:
        print(f"  FAIL: {len(invalid)} rows with score_valid != 1")
        for r in invalid[:5]:
            print(f"    {r['model']} {r['item_id']}: raw_score={r.get('raw_score','?')}")
        all_ok = False
    else:
        print("  OK: all 180 rows have score_valid = 1")

    # 3. raw_score in [1,7]
    out_of_range = []
    for r in rows:
        raw = r.get("raw_score", "").strip()
        if raw:
            try:
                s = int(raw)
                if s < 1 or s > 7:
                    out_of_range.append(r)
            except ValueError:
                out_of_range.append(r)
    if out_of_range:
        print(f"  FAIL: {len(out_of_range)} rows with raw_score outside [1,7]")
        for r in out_of_range[:5]:
            print(f"    {r['model']} {r['item_id']}: {r.get('raw_score','?')}")
        all_ok = False
    else:
        print("  OK: all raw_scores in [1,7]")

    # 4. Each model has exactly 20 items
    from collections import Counter
    model_counts = Counter(r["model"] for r in rows)
    for model, count in sorted(model_counts.items()):
        if count != 20:
            print(f"  FAIL: {model} has {count} items (expected 20)")
            all_ok = False
    print(f"  OK: all models have 20 items" if all(
        c == 20 for c in model_counts.values()
    ) else f"  Model item counts: {dict(model_counts)}")

    # 5. Each model × dimension has exactly 4 items
    dim_counts = Counter((r["model"], r["dimension"]) for r in rows)
    dim_issues = {k: v for k, v in dim_counts.items() if v != 4}
    if dim_issues:
        print(f"  FAIL: {len(dim_issues)} model×dimension groups with != 4 items")
        for (m, d), c in dim_issues.items():
            print(f"    {m} / {d}: {c}")
        all_ok = False
    else:
        print("  OK: each model×dimension has exactly 4 items")

    if all_ok:
        print("=== All checks passed ===\n")
    else:
        print("=== SOME CHECKS FAILED ===\n")
    return all_ok


def main():
    if not INPUT_CSV.exists():
        print(f"ERROR: {INPUT_CSV} not found. Run run_orientation.py first.")
        return

    rows = load_filled(INPUT_CSV)
    if not validate_input(rows):
        print("Aborting due to validation failures.")
        return
    model_dims = compute_dimension_means(rows)
    z_scores = compute_z_scores(model_dims)
    pvc = compute_pvc(z_scores)

    print_table(model_dims, pvc)
    export_scores(model_dims, z_scores, pvc)
    export_table2(model_dims, pvc, z_scores)


if __name__ == "__main__":
    main()
