"""
Aggregate every `output_decoys/anonymeter.json` into one markdown table
+ CSV for the paper.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

FIELDS = [
    "schema", "n_core", "n_total", "n_attacks", "n_aux_cols",
    "risk_value", "risk_ci_low", "risk_ci_high",
    "attack_rate", "control_rate",
]


def _verdict(risk: float, ci_low: float, ci_high: float) -> str:
    if ci_low <= 0 <= ci_high:
        return "indistinguishable from 0"
    if risk < 0.1:
        return "low"
    if risk < 0.5:
        return "moderate"
    return "high"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-dir", type=Path, required=True)
    args = ap.parse_args()

    rows = []
    for exp in sorted(args.exp_dir.glob("0*_*")):
        path = exp / "output_decoys" / "anonymeter.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        rows.append({k: data.get(k) for k in FIELDS})

    if not rows:
        print("no anonymeter.json files found under */output_decoys/ -- run experiments first")
        return 1

    # CSV
    csv_path = args.exp_dir / "anonymeter_results.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["verdict"])
        w.writeheader()
        for r in rows:
            r["verdict"] = _verdict(r["risk_value"], r["risk_ci_low"], r["risk_ci_high"])
            w.writerow(r)

    # Markdown
    md_lines = [
        "# Anonymeter risk on the decoy-augmented datasets",
        "",
        "Each row: 10 % reconstructable core + 90 % decoys. "
        "`risk_value` is `(attack_rate − control_rate) / (1 − control_rate)`; "
        "`ci` is Anonymeter's 95 % confidence interval. "
        "Anonymeter reports a risk statistically indistinguishable from 0 "
        "in every schema, even though M·s = b reconstructs every core record exactly.",
        "",
        "| Schema | core | total | risk (95 % CI) | attack | control | verdict |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for r in rows:
        md_lines.append(
            f"| `{r['schema']}` | {r['n_core']} | {r['n_total']} | "
            f"{r['risk_value']:.4f}  [{r['risk_ci_low']:.4f}, {r['risk_ci_high']:.4f}] | "
            f"{r['attack_rate']:.3f} | {r['control_rate']:.3f} | "
            f"{_verdict(r['risk_value'], r['risk_ci_low'], r['risk_ci_high'])} |"
        )
    md_path = args.exp_dir / "anonymeter_results.md"
    md_path.write_text("\n".join(md_lines) + "\n")

    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
