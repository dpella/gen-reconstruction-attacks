"""
synthcity privacy evaluation on the decoy-augmented datasets.

Runs two synthcity metrics against each schema's 10%-reconstructable-core
release:

  * DataLeakageXGB  — XGBoost-based attribute inference; reports the
    improvement in predicting every sensitive feature on the real data
    when trained on synthetic vs. on a random baseline. Analogous to
    Anonymeter InferenceEvaluator but with an XGB backbone.
  * IdentifiabilityScore — distance-based re-identification risk of Yoon
    et al. (ADS-GAN, JBHI 2019). Measures whether synthetic records are
    close enough to real records that the latter could be re-identified.

Both take (X_gt, X_syn), built as Anonymeter's views (see `_split_views`
in anonymeter_eval.py): X_gt is the reconstructable core minus the
held-out control rows, and X_syn is the release without the control rows,
with the secret column zeroed because the secret is only released through
the per-query aggregates. Both are label-encoded to numeric.

Usage:
    python3 synthcity_eval.py --schema <yaml> --out <dir>
                              [--decoy-fraction 0.1]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

warnings.filterwarnings("ignore")

from anonymeter_eval import _split_views, _table_to_encoded_df
from driver import run_pipeline


def run_synthcity(cfg: dict, decoy_fraction: float) -> dict:
    from synthcity.metrics.eval_attacks import DataLeakageXGB
    from synthcity.metrics.eval_privacy import IdentifiabilityScore
    from synthcity.plugins.core.dataloader import GenericDataLoader

    table, queries, n_core = run_pipeline(cfg, decoy_fraction=decoy_fraction)
    df = _table_to_encoded_df(table, queries, n_core)
    secret = "__sensitive__"
    ori, syn, _ = _split_views(df, n_core, secret)

    X_gt  = GenericDataLoader(ori.reset_index(drop=True), sensitive_features=[secret])
    X_syn = GenericDataLoader(syn, sensitive_features=[secret])

    # The zeroed secret column gives DataLeakageXGB nothing to learn from:
    # with a single value it is treated as a class label, the real secrets
    # of X_gt are then unknown classes, and synthcity raises. Report n/a.
    if syn[secret].nunique() > 1:
        leakage_xgb = DataLeakageXGB().evaluate(X_gt, X_syn)
    else:
        leakage_xgb = {}
    ident       = IdentifiabilityScore().evaluate(X_gt, X_syn)

    return {
        "schema":              cfg.get("name"),
        "n_core":              n_core,
        "n_total":             df.shape[0],
        "decoy_fraction":      decoy_fraction,
        "data_leakage_xgb":    float(leakage_xgb.get("mean", float("nan"))),
        "identifiability":     float(ident.get("score", float("nan"))),
        "identifiability_oc":  float(ident.get("score_OC", float("nan"))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema",         required=True, type=Path)
    ap.add_argument("--out",            required=True, type=Path)
    ap.add_argument("--decoy-fraction", type=float, default=0.1)
    args = ap.parse_args()

    cfg = yaml.safe_load(args.schema.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    result = run_synthcity(cfg, args.decoy_fraction)
    # NaN is not valid JSON: write the missing scores as null.
    json_result = {k: None if isinstance(v, float) and math.isnan(v) else v
                   for k, v in result.items()}
    (args.out / "synthcity.json").write_text(json.dumps(json_result, indent=2))

    lines = [
        f"Schema           : {result['schema']}  (decoy-augmented, "
        f"{int(result['decoy_fraction']*100)}% reconstructable)",
        f"  core / total    : {result['n_core']} / {result['n_total']}",
        "  DataLeakageXGB  : n/a (the release's secret column is zeroed)"
        if math.isnan(result["data_leakage_xgb"]) else
        f"  DataLeakageXGB  : {result['data_leakage_xgb']:.4f}",
        f"  Identifiability : {result['identifiability']:.4f}  "
        f"(one-class: {result['identifiability_oc']:.4f})",
    ]
    (args.out / "synthcity.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
