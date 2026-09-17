#!/usr/bin/env python3
"""Guard: the H2 leave-one-model-out claims in main.tex must match the canonical LOMO run.

Checks that, for each retained frame, the 'LOMO sign stability' cell in Table 2 and the
table note agree with outputs/canonical/h2_fe_lomo.csv:
  sign stable = coefficient keeps its sign in all 15 leave-one-model-out fits
  (a frame can be sign-stable and still never statistically significant -- the two
  properties are reported separately, and the note must say so).

Exit code 0 = consistent; 1 = at least one claim contradicts the data.
"""
import csv
import re
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parent
CAN = HOME / "outputs" / "canonical"
MAIN = Path.home() / "Documents" / "value-sensitivity-llm-audit" / "main.tex"
FRAMES = {
    "access_barriers": "Access barriers",
    "collective_responsibility": "Collective responsibility",
    "coercive_backlash": "Coercive backlash",
}


def main() -> int:
    rows = list(csv.DictReader(open(CAN / "h2_fe_lomo.csv", newline="")))
    tex = MAIN.read_text()
    problems = []
    for key, label in FRAMES.items():
        b = [float(r[f"{key}_b"]) for r in rows]
        p = [float(r[f"{key}_p"]) for r in rows]
        stable = all(v > 0 for v in b) or all(v < 0 for v in b)
        any_sig = any(v < 0.05 for v in p)
        row = next((ln for ln in tex.splitlines() if ln.startswith(label + " &")), None)
        if row is None:
            problems.append(f"{label}: table row not found")
            continue
        claim = row.rstrip("\\ ").split("&")[-1].strip()
        says_stable = claim.lower().startswith("yes")
        says_sig = "not significant" in claim.lower()
        if says_stable != stable:
            problems.append(f"{label}: table says sign stability={claim!r} but data says stable={stable} "
                            f"(range {min(b):+.2f} to {max(b):+.2f})")
        if stable and not any_sig and not says_sig:
            problems.append(f"{label}: sign-stable but never significant -- the cell must say so "
                            f"(currently {claim!r})")
        flip = " " if stable else " NOT"
        print(f"  {label:<24} range {min(b):+.2f}..{max(b):+.2f}  sign-stable={stable:<5} "
              f"ever p<0.05={any_sig:<5} -> table cell {claim!r}")
    note = re.search(r"LOMO sign stability indicates([^\\\\]*)", tex)
    if "does not imply statistical significance" not in tex:
        problems.append("table note does not state that sign stability is not statistical significance")
    if problems:
        print("\nFAIL:")
        for pr in problems:
            print("  -", pr)
        return 1
    print("\nTable 2 LOMO claims are consistent with the canonical run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
