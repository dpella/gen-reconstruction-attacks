"""
Anonymeter evaluation for the decoy-augmented datasets.

Mirrors the methodology we described in the CCS rebuttal: each row in the
attacker's view is encoded as

    (quasi-identifiers, per-query membership flags, per-query aggregate
     values, sensitive attribute)

The `ori` view is the n-row reconstructable core (the attacker is told
which rows are "real"), and the `syn` view is the full decoy-augmented
release. Anonymeter's `InferenceEvaluator` then tries to predict the
sensitive attribute from the quasi-identifiers + query information.
Reconstruction is *algebraically* possible via M·s = b, but Anonymeter
probes correlational / ML-predictive privacy — and therefore reports a
near-zero risk, missing the vulnerable records entirely.

Usage:
    python3 anonymeter_eval.py --schema <path> [--decoy-fraction 0.1]
                               [--out <path>] [--n-attacks auto|N]

Outputs `<out>/anonymeter.json` with the risk and attack/baseline rates,
and appends a one-line summary to `<out>/anonymeter.txt`.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Silence noisy warnings from joblib / sklearn under anonymeter.
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from driver import run_pipeline


def _table_to_encoded_df(table, queries, n_core):
    """Convert a Table + query list into a numeric-only DataFrame ready
    for Anonymeter: every column is either numeric or label-encoded."""
    import pandas as pd
    from sklearn.preprocessing import LabelEncoder

    # Base columns
    cols = {}
    for t in table.titles:
        col = list(table[t])
        if not col:
            continue
        sample = col[0]
        if isinstance(sample, (int, float)) and not isinstance(sample, bool):
            cols[t] = pd.to_numeric(col, errors="coerce")
        else:
            enc = LabelEncoder().fit([str(v) for v in col])
            cols[t] = enc.transform([str(v) for v in col])

    # Per-query membership + per-query aggregate value
    for i, q in enumerate(queries):
        vec = q.as_vector(table)
        try:
            agg = float(q(table))
        except (TypeError, ValueError, ZeroDivisionError):
            agg = 0.0
        cols[f"__match_q{i:03d}"] = vec
        cols[f"__agg_q{i:03d}"]   = [agg if v else 0.0 for v in vec]

    cols["__sensitive__"] = list(table.sensitive)

    df = pd.DataFrame(cols)
    return df


def run_anonymeter(cfg: dict, decoy_fraction: float, n_attacks: str | int = "auto") -> dict:
    table, queries, n_core = run_pipeline(cfg, decoy_fraction=decoy_fraction)
    df = _table_to_encoded_df(table, queries, n_core)
    secret = "__sensitive__"
    aux_cols = [c for c in df.columns if c != secret]

    # First n_core rows are the reconstructable core; the remainder are
    # decoys. Anonymeter's `ori` is the private subset, `syn` is the
    # released (decoy-augmented) table, and `control` mirrors the tiny
    # kaggle-era setup where the core is too small for a clean split.
    ori = df.iloc[:n_core][aux_cols + [secret]].reset_index(drop=True)
    syn = df[aux_cols + [secret]].reset_index(drop=True)
    control = ori.copy()

    if n_attacks == "auto":
        # Anonymeter samples n_attacks rows from ori without replacement,
        # so this must not exceed n_core. Cap at 500 to keep runs fast.
        n_attacks_val = min(500, n_core)
    else:
        n_attacks_val = min(int(n_attacks), n_core)

    from anonymeter.evaluators import InferenceEvaluator

    evaluator = InferenceEvaluator(
        ori=ori,
        syn=syn,
        control=control,
        aux_cols=aux_cols,
        secret=secret,
        n_attacks=n_attacks_val,
    )
    evaluator.evaluate(n_jobs=-1)
    results = evaluator.results()
    risk = evaluator.risk()

    def _ci(obj) -> tuple[float, float]:
        # anonymeter.risk() returns a namedtuple-like with .ci (lo, hi)
        ci = getattr(obj, "ci", None)
        if ci is None:
            return (0.0, 0.0)
        return (float(ci[0]), float(ci[1]))

    return {
        "schema":              cfg.get("name"),
        "n_core":              n_core,
        "n_total":             df.shape[0],
        "decoy_fraction":      decoy_fraction,
        "n_attacks":           n_attacks_val,
        "n_aux_cols":          len(aux_cols),
        "risk_value":          float(risk.value),
        "risk_ci_low":         _ci(risk)[0],
        "risk_ci_high":        _ci(risk)[1],
        "attack_rate":         float(results.attack_rate.value),
        "attack_rate_ci":      _ci(results.attack_rate),
        "control_rate":        float(results.control_rate.value),
        "control_rate_ci":     _ci(results.control_rate),
        "baseline_rate":       float(getattr(getattr(results, "baseline_rate", None), "value", float("nan"))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema",          required=True, type=Path)
    ap.add_argument("--out",             required=True, type=Path)
    ap.add_argument("--decoy-fraction",  type=float, default=0.1)
    ap.add_argument("--n-attacks",       default="auto")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.schema.read_text())
    args.out.mkdir(parents=True, exist_ok=True)

    result = run_anonymeter(cfg, args.decoy_fraction, args.n_attacks)
    (args.out / "anonymeter.json").write_text(json.dumps(result, indent=2))

    lines = [
        f"Schema        : {result['schema']}  (decoy-augmented, {int(result['decoy_fraction']*100)}% reconstructable)",
        f"  core / total : {result['n_core']} / {result['n_total']}",
        f"  aux cols     : {result['n_aux_cols']}",
        f"  n_attacks    : {result['n_attacks']}",
        f"  Anonymeter risk : {result['risk_value']:.4f}  CI [{result['risk_ci_low']:.4f}, {result['risk_ci_high']:.4f}]",
        f"  attack rate     : {result['attack_rate']:.4f}  CI [{result['attack_rate_ci'][0]:.4f}, {result['attack_rate_ci'][1]:.4f}]",
        f"  control rate    : {result['control_rate']:.4f}  CI [{result['control_rate_ci'][0]:.4f}, {result['control_rate_ci'][1]:.4f}]",
    ]
    (args.out / "anonymeter.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
