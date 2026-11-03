"""
Aggregate Anonymeter, synthcity, and Privacy Meter results into one
paper-ready table per metric.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _load(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def _fmt(value, spec: str, scale: float = 1.0, suffix: str = "") -> str:
    """Format a metric for the markdown table, or `n/a` when it is missing."""
    return "n/a" if value is None else f"{value * scale:{spec}}{suffix}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-dir", type=Path, required=True)
    args = ap.parse_args()

    rows = []
    for exp in sorted(args.exp_dir.glob("0*_*")):
        out = exp / "output_decoys"
        a = _load(out / "anonymeter.json")
        s = _load(out / "synthcity.json")
        p = _load(out / "privacy_meter.json")
        if not (a or s or p):
            continue
        schema = (a or s or p).get("schema")
        rows.append({
            "schema":     schema,
            "n_core":     (a or s or p).get("n_core"),
            "n_total":    (a or s or p).get("n_total"),
            "anonymeter_risk":          a["risk_value"]       if a else None,
            "anonymeter_attack":        a["attack_rate"]      if a else None,
            "anonymeter_control":       a["control_rate"]     if a else None,
            "synthcity_leakage_xgb":    s["data_leakage_xgb"] if s else None,
            "synthcity_identifiability":s["identifiability"]  if s else None,
            "pm_mean_rel_error":        p["mean_rel_error"]   if p else None,
            "pm_r2":                    p["r2"]               if p else None,
            "pm_success_5pct":          p["attack_success_5pct"] if p else None,
            "pm_control_success_5pct":  p.get("control_success_5pct") if p else None,
        })

    if not rows:
        print("no privacy-metric JSONs found under */output_decoys/ -- run experiments first")
        return 1

    # CSV
    csv_path = args.exp_dir / "privacy_metrics_results.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Markdown
    md = [
        "# Privacy-metric results on the decoy-augmented datasets",
        "",
        "Every row: 10 % reconstructable core + 90 % decoys. "
        "All metrics rate the releases as low-risk even though `M·s = b` "
        "recovers every core record exactly.",
        "",
        "| Schema | n core | n total | Anonymeter risk | attack | control | "
        "synthcity XGB | synthcity Ident. | Privacy Meter MRE | R² | ±5 % succ. | "
        "±5 % control |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        md.append(
            f"| `{r['schema']}` | {r['n_core']} | {r['n_total']} | "
            f"{_fmt(r['anonymeter_risk'], '.4f')} | "
            f"{_fmt(r['anonymeter_attack'], '.3f')} | "
            f"{_fmt(r['anonymeter_control'], '.3f')} | "
            f"{_fmt(r['synthcity_leakage_xgb'], '.4f')} | "
            f"{_fmt(r['synthcity_identifiability'], '.4f')} | "
            f"{_fmt(r['pm_mean_rel_error'], '.1f', 100, '%')} | "
            f"{_fmt(r['pm_r2'], '.3f')} | "
            f"{_fmt(r['pm_success_5pct'], '.1f', 100, '%')} | "
            f"{_fmt(r['pm_control_success_5pct'], '.1f', 100, '%')} |"
        )
    (args.exp_dir / "privacy_metrics_results.md").write_text("\n".join(md) + "\n")

    print(f"wrote {csv_path}")
    print(f"wrote {args.exp_dir / 'privacy_metrics_results.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
