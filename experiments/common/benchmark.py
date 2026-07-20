"""
Benchmark: sweep MIP base ∈ {4, 8, 16} × target n ∈ schemas
and measure per-section wall-clock time for the reconstruction pipeline.

Each (schema, base) configuration is repeated --repeats times after one
discarded warm-up run to dampen cold-cache / JIT / import-time noise.
All individual runs are written so downstream plotting can compute
means, stdevs, or 95 % CIs directly.

The schema YAML of each experiment determines the target n; this script
overrides `mip_base` and derives the matching `hadamard_order` so the
final record count stays fixed:

    final_n = mip_base · 2^(hadamard_order − 1)
    ⇒ hadamard_order = log2(final_n / mip_base) + 1

Per-section timings:
  t_mip      — Search.generate_fullrank_table
  t_hadamard — Hadamard.generate_new_table  (0 when hadamard_order == 1)
  t_compress — sum of all Compress.compress calls
  t_verify   — np.linalg.lstsq of the n×n aggregate system

Results:
  benchmark_results_raw.csv  — one row per (schema, base, repetition)
  benchmark_results.csv      — one row per (schema, base), with mean,
                                stdev, and 95 % CI half-width per field
  benchmark_results.md       — paper-ready markdown, means only

Flags:
  --repeats N       (default 5)  repetitions per config (after warmup)
  --no-warmup                    skip the discarded first run
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
import time
from pathlib import Path
from typing import List, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.compress import Compress
from src.hadamard import Hadamard
from src.logger import Level, Logger
from src.matrix import Matrix
from src.search.search import Search
from src.table.query import IQuery
from src.table.table import Table


SCHEMAS = [
    ("01_sdtm_vs",             16),
    ("02_adam_adsl",           32),
    ("03_adam_adlb",           64),
    ("04_adam_adpc",          128),
    ("05_adam_adpc_extended", 256),
    ("06_hr_open_n256",       256),
    ("07_hr_open_n512",       512),
    ("08_eurostat_silc_n128", 128),
    ("09_eurostat_silc_n512", 512),
]
MIP_BASES = [4, 8, 16]


def timed_run(cfg: dict, mip_base: int, hadamard_order: int) -> dict:
    """Run the full pipeline with per-section timing. Returns a timings dict."""
    Logger.get_instance().set_level(Level.ERROR.value)  # silence per-iteration noise
    random.seed(cfg["seed"])

    p = cfg["population_value"]
    c = cfg["communality_value"]
    sensitive = cfg["sensitive_column"]

    # --- MIP search ---
    t0 = time.perf_counter()
    table = Table.create_table_with_n_records(
        n=mip_base, population_value=p, titles=[], seed_value=cfg["seed"]
    )
    table.set_sensitive_column_name(sensitive)
    search = Search(p, c, titles=[])
    new_table, queries = search.generate_fullrank_table(table)
    t_mip = time.perf_counter() - t0

    # --- Hadamard expansion ---
    t0 = time.perf_counter()
    if hadamard_order > 1:
        hadamard = Hadamard(Logger.get_instance(), cfg["seed"])
        hadamard.set_sensitive_column_name(sensitive)
        matrix = Matrix.from_queries(new_table, queries[:-1])
        new_table, queries = hadamard.generate_new_table(
            matrix, hadamard_order, titles=[]
        )
    t_hadamard = time.perf_counter() - t0

    # --- Compression ---
    t0 = time.perf_counter()
    for i, group in enumerate(cfg.get("compression_groups", [])):
        compress = (
            Compress(new_table)
            .set_columns_to_compress(group["columns"])
            .set_column_title(f"__comp_{i}")
            .set_interval_length(group["interval"])
        )
        new_table, queries = compress.compress(queries)
    t_compress = time.perf_counter() - t0

    # --- Reconstruction verify ---
    import numpy as np
    t0 = time.perf_counter()
    vectors = [q.as_vector(new_table) for q in queries]
    M = np.array(vectors, dtype=float)
    b = np.array([q(new_table) * sum(q.as_vector(new_table)) for q in queries], dtype=float)
    rank = int(np.linalg.matrix_rank(M))
    s_hat, *_ = np.linalg.lstsq(M, b, rcond=None)
    s_true = np.array(new_table.sensitive, dtype=float)
    max_err = float(np.max(np.abs(s_hat - s_true)))
    t_verify = time.perf_counter() - t0

    return {
        "n": new_table.shape[0],
        "mip_base": mip_base,
        "hadamard_order": hadamard_order,
        "t_mip": t_mip,
        "t_hadamard": t_hadamard,
        "t_compress": t_compress,
        "t_verify": t_verify,
        "t_total": t_mip + t_hadamard + t_compress + t_verify,
        "rank": rank,
        "full_rank": rank == new_table.shape[0],
        "max_abs_error": max_err,
        "exact": max_err < 0.5,
    }


TIME_FIELDS = ["t_mip", "t_hadamard", "t_compress", "t_verify", "t_total"]


def _aggregate(samples: List[dict]) -> dict:
    """Compute mean, stdev, and 95 % CI half-width for the timing fields."""
    import statistics
    agg = {"n_samples": len(samples)}
    for f in TIME_FIELDS:
        xs = [s[f] for s in samples]
        mean = statistics.fmean(xs)
        stdev = statistics.stdev(xs) if len(xs) > 1 else 0.0
        ci95 = 1.96 * stdev / (len(xs) ** 0.5) if len(xs) > 1 else 0.0
        agg[f"{f}_mean"] = mean
        agg[f"{f}_stdev"] = stdev
        agg[f"{f}_ci95"] = ci95
    # Accuracy: report max error across samples (conservative)
    agg["max_abs_error"] = max(s["max_abs_error"] for s in samples)
    agg["full_rank"] = all(s["full_rank"] for s in samples)
    agg["exact"] = all(s["exact"] for s in samples)
    return agg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--repeats", type=int, default=5,
                    help="measured repetitions per (schema, base) after warmup")
    ap.add_argument("--no-warmup", action="store_true",
                    help="skip the initial warmup run (not recommended)")
    args = ap.parse_args()

    raw_rows: List[dict] = []
    agg_rows: List[dict] = []
    for schema_name, n_target in SCHEMAS:
        schema_path = args.out_dir / schema_name / "schema.yaml"
        cfg = yaml.safe_load(schema_path.read_text())
        print(f"\n=== {schema_name}  (n={n_target}) ===")
        for base in MIP_BASES:
            if base > n_target:
                continue
            k = int(round(math.log2(n_target / base))) + 1
            assert base * (2 ** (k - 1)) == n_target, f"{base=} {k=} {n_target=}"
            print(f"  base={base:2d}  k={k}  ", end="", flush=True)

            if not args.no_warmup:
                timed_run(cfg, base, k)  # warmup — discarded
                print("[w]", end="", flush=True)

            samples: List[dict] = []
            for rep in range(args.repeats):
                r = timed_run(cfg, base, k)
                r["schema"] = schema_name
                r["rep"] = rep
                raw_rows.append(r)
                samples.append(r)
                print(f" {r['t_total']:.3f}", end="", flush=True)
            agg = _aggregate(samples)
            agg.update({
                "schema": schema_name,
                "n": n_target,
                "mip_base": base,
                "hadamard_order": k,
            })
            agg_rows.append(agg)
            print(f"  →  total = {agg['t_total_mean']:.3f} ± {agg['t_total_stdev']:.3f}s"
                  f"  exact={agg['exact']}")

    # --- per-run CSV (for custom analysis, error-bar plotting) ---
    raw_path = args.out_dir / "benchmark_results_raw.csv"
    raw_fields = [
        "schema", "n", "mip_base", "hadamard_order", "rep",
        "t_mip", "t_hadamard", "t_compress", "t_verify", "t_total",
        "rank", "full_rank", "max_abs_error", "exact",
    ]
    with raw_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields)
        writer.writeheader()
        for r in raw_rows:
            writer.writerow({k: r[k] for k in raw_fields})

    # --- aggregated CSV (one row per config with mean / stdev / CI) ---
    agg_path = args.out_dir / "benchmark_results.csv"
    agg_fields = [
        "schema", "n", "mip_base", "hadamard_order", "n_samples",
        *[f"{f}_{stat}" for f in TIME_FIELDS for stat in ("mean", "stdev", "ci95")],
        "full_rank", "max_abs_error", "exact",
    ]
    with agg_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=agg_fields)
        writer.writeheader()
        for r in agg_rows:
            writer.writerow({k: r.get(k, "") for k in agg_fields})

    # --- paper markdown (means only) ---
    md_lines = [
        f"# Benchmark — MIP base × target n sweep  (repeats = {args.repeats})",
        "",
        "Timings in seconds: **mean ± stdev** across repeats on the machine",
        "that ran `benchmark.sh` (one warmup run per config, discarded).",
        "`MIP` = MIP-guided full-rank search; `Had` = Hadamard (Sylvester) expansion;",
        "`Cmp` = column compression; `Vrf` = lstsq reconstruction verify.",
        "",
        "| schema | n | base | k | MIP | Had | Cmp | Vrf | **total** | exact |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in agg_rows:
        def cell(field: str) -> str:
            return f"{r[f'{field}_mean']:.3f}±{r[f'{field}_stdev']:.3f}"
        md_lines.append(
            f"| `{r['schema']}` | {r['n']} | {r['mip_base']} | {r['hadamard_order']} | "
            f"{cell('t_mip')} | {cell('t_hadamard')} | {cell('t_compress')} | "
            f"{cell('t_verify')} | **{cell('t_total')}** | "
            f"{'✓' if r['exact'] else '✗'} |"
        )
    md_path = args.out_dir / "benchmark_results.md"
    md_path.write_text("\n".join(md_lines) + "\n")

    print(f"\nWrote {raw_path}  ({len(raw_rows)} per-run samples)")
    print(f"Wrote {agg_path}   ({len(agg_rows)} aggregated configs)")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
