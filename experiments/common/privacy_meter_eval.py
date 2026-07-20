"""
Privacy Meter – style attribute inference on the decoy-augmented datasets.

Follows the evaluation protocol described in
Appendix~\\ref{sec:appendix_privacy_metrics}: a Random Forest regressor
(100 estimators, max depth 10) is trained on the synthetic / released
dataset to predict the sensitive column, then tested on the
reconstructable core.  High mean relative error is interpreted as good
privacy protection under this threat model.

Reference: Shokri et al., "Membership Inference Attacks against Machine
Learning Models", S&P 2017. The ML-attribute-inference variant is
standard practice in privacy-metric literature and is what the paper
refers to when it cites \\cite{shokri2017membership}.

Usage:
    python3 privacy_meter_eval.py --schema <yaml> --out <dir>
                                  [--decoy-fraction 0.1]
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

warnings.filterwarnings("ignore")

from anonymeter_eval import _table_to_encoded_df
from driver import run_pipeline


def run_privacy_meter(cfg: dict, decoy_fraction: float) -> dict:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    table, queries, n_core = run_pipeline(cfg, decoy_fraction=decoy_fraction)
    df = _table_to_encoded_df(table, queries, n_core)
    secret = "__sensitive__"
    feat_cols = [c for c in df.columns if c != secret]

    # Train on the full release (attacker's view), test on the
    # reconstructable core (what the attacker wants to predict).
    X_train = df[feat_cols].to_numpy()
    y_train = df[secret].to_numpy()
    X_test  = df.iloc[:n_core][feat_cols].to_numpy()
    y_test  = df.iloc[:n_core][secret].to_numpy()

    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=cfg["seed"])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    abs_err  = np.abs(y_test - y_pred)
    rel_err  = abs_err / np.clip(np.abs(y_test), 1e-9, None)
    mae      = float(mean_absolute_error(y_test, y_pred))
    mre      = float(np.mean(rel_err))
    rmse     = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2       = float(r2_score(y_test, y_pred))

    # "Success" under Anonymeter-style ±5% tolerance (paper rebuttal).
    success_rate = float(np.mean(rel_err <= 0.05))

    return {
        "schema":            cfg.get("name"),
        "n_core":            n_core,
        "n_total":           df.shape[0],
        "decoy_fraction":    decoy_fraction,
        "n_features":        len(feat_cols),
        "mean_abs_error":    mae,
        "mean_rel_error":    mre,
        "rmse":              rmse,
        "r2":                r2,
        "attack_success_5pct": success_rate,  # fraction of records within ±5%
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema",         required=True, type=Path)
    ap.add_argument("--out",            required=True, type=Path)
    ap.add_argument("--decoy-fraction", type=float, default=0.1)
    args = ap.parse_args()

    cfg = yaml.safe_load(args.schema.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    result = run_privacy_meter(cfg, args.decoy_fraction)
    (args.out / "privacy_meter.json").write_text(json.dumps(result, indent=2))

    lines = [
        f"Schema                : {result['schema']}  (decoy-augmented, "
        f"{int(result['decoy_fraction']*100)}% reconstructable)",
        f"  core / total         : {result['n_core']} / {result['n_total']}",
        f"  features             : {result['n_features']}",
        f"  mean relative error  : {result['mean_rel_error']*100:.2f}%",
        f"  mean absolute error  : {result['mean_abs_error']:.2f}",
        f"  RMSE                 : {result['rmse']:.2f}",
        f"  R²                   : {result['r2']:.4f}",
        f"  attack success (±5%) : {result['attack_success_5pct']*100:.2f}% of core",
    ]
    (args.out / "privacy_meter.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
