"""
Experiment driver for the attack-smt tool.

Mirrors `src/program.Program.run()` but returns the final Table and query
list as Python objects so downstream postprocessing (column renaming,
CSV/SQL emission, reconstruction verification) does not have to parse stdout.

Invoked from each experiment's run.sh as:
    python3 driver.py --schema schema.yaml --out output/

With `--decoy-fraction F` (0 < F < 1), the pipeline implements the partially
reconstructive construction of Section 4.2 + Theorem 3 in the paper:

  1. Build the reconstructable core of size n as usual (search -> Hadamard).
  2. Replace the final `SELECT AVG(...) FROM table;` (the all-records query
     introduced by the Hadamard expansion) with `WHERE <col> = '0'` on
     `column_{n-3}` — the unique column whose raw values in the core are
     exactly `{'0','1'}`. This is the negation of the `= '1'` query on the
     same column. Without this swap, decoys would be silently counted by
     the unconditional all-records query, which has no WHERE clause to
     exclude them.
  3. Append (n / F − n) decoy rows (stock `src/decoy.py`, every column
     sampled from `Table.no(random=True) ∈ {'2','3'}`) — *before*
     compression runs, not after.
  4. Only then run compression. `Compress.compress_record` treats any
     value other than `'1'` as a "no", so a decoy's `'2'`/`'3'` values walk
     the same branch as an all-zero record and land in the one range
     bucket (`[0, 1)` after full halving) that the generated range queries
     structurally never test (their check-sets only cover the odd-indexed
     dyadic sub-intervals, i.e. "this bit is 1" tests). No decoy ever
     satisfies a compressed range query, so a plain string sentinel is
     enough — no numeric `-1.0` fill needed for post-compression columns.
  5. Verification: the decoy rows contribute zero to every row of the
     released matrix, so `b` is identical to the pre-decoy case. Solve
     `M[:, :n] · s = b` and compare with the first n ground-truth values.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import List, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.compress import Compress
from src.decoy import Decoy
from src.hadamard import Hadamard
from src.logger import Logger, Level
from src.matrix import Matrix
from src.search.search import Search
from src.table.condition import EQ
from src.table.query import IQuery, SelectQuery, SelectWhereQuery
from src.table.table import Table


def _binary_column_name(cfg: dict) -> str:
    """Return the raw column name whose records-of-the-core values are
    exactly {'0', '1'}. Under the Hadamard pipeline, `Table.no(False)` is
    only called at iteration i = n−2, so `column_{n-3}` is the binary one.
    """
    n = cfg["n_records"]
    return f"column_{n - 3}"


def _decoy_count(n: int, fraction: float) -> int:
    """Number of decoys so the reconstructable core is `fraction` of total."""
    total = round(n / fraction)
    return total - n


def run_pipeline(cfg: dict, decoy_fraction: float = 0.0) -> Tuple[Table, List[IQuery], int]:
    """Run MIP search -> Hadamard expansion -> compression (-> decoys).

    Returns `(table, queries, n_core)` where `n_core` is the count of
    reconstructable records. When `decoy_fraction == 0`, `n_core ==
    table.shape[0]`; with decoys, the first `n_core` rows of the table
    are reconstructable and the rest are non-matching decoys.
    """
    logger = Logger.get_instance()
    logger.set_level(Level[cfg.get("log_level", "WARNING").upper()].value)

    mip_base = cfg["mip_base"]
    seed = cfg["seed"]
    p = cfg["population_value"]
    c = cfg["communality_value"]
    hadamard_order = cfg["hadamard_order"]
    sensitive = cfg["sensitive_column"]

    random.seed(seed)

    table = Table.create_table_with_n_records(
        n=mip_base, population_value=p, titles=[], seed_value=seed
    )
    table.set_sensitive_column_name(sensitive)

    search = Search(p, c, titles=[])
    new_table, queries = search.generate_fullrank_table(table)

    if hadamard_order and hadamard_order > 1:
        hadamard = Hadamard(logger, seed)
        hadamard.set_sensitive_column_name(sensitive)
        matrix = Matrix.from_queries(new_table, queries[:-1])
        new_table, queries = hadamard.generate_new_table(
            matrix, hadamard_order, titles=[]
        )

    n_core = new_table.shape[0]

    if decoy_fraction > 0:
        # Replace the all-records SelectQuery (inserted by Hadamard) with the
        # negation of the `= '1'` query on the binary column, *before* adding
        # decoys — otherwise the unconditional all-records query would count
        # the decoy rows too, since it has no WHERE clause to exclude them.
        bin_col = _binary_column_name(cfg)
        if bin_col not in new_table.titles:
            raise ValueError(
                f"Expected binary column {bin_col} in the pre-compression table; "
                "check the schema's binary_rename / compression_groups."
            )
        idxs = [
            i for i, q in enumerate(queries)
            if isinstance(q, SelectQuery) and not isinstance(q, SelectWhereQuery)
        ]
        if len(idxs) != 1:
            raise ValueError(
                f"Expected exactly one all-records SelectQuery in the pipeline "
                f"output; found {len(idxs)} — pipeline mismatch."
            )
        negation = SelectWhereQuery(sensitive, bin_col, EQ(bin_col, Table.no(False)))
        queries = queries[:idxs[0]] + [negation] + queries[idxs[0] + 1:]

        # Stock decoy generator: every column gets a string '2'/'3' sentinel.
        # Safe to run before compression — see module docstring step 4 for
        # why compression can't turn a decoy into a false match.
        n_decoys = _decoy_count(n_core, decoy_fraction)
        new_table, queries = Decoy(n_decoys).generate_decoy_table(new_table, queries)

    for i, group in enumerate(cfg.get("compression_groups", [])):
        compress = (
            Compress(new_table)
            .set_columns_to_compress(group["columns"])
            .set_column_title(f"__comp_{i}")
            .set_interval_length(group["interval"])
        )
        new_table, queries = compress.compress(queries)

    return new_table, queries, n_core


def _parse_binary_rename(cfg: dict) -> dict:
    """Normalize the binary_rename entry.

    Accepts either form:
        binary_rename:
          column_12: sex                        # header-only rename
          column_13:                            # header + value remap
            name: race
            values: {"1": WHITE, "0": BLACK, "2": ASIAN, "3": OTHER}
    """
    out = {}
    for raw, spec in cfg.get("binary_rename", {}).items():
        if isinstance(spec, str):
            out[raw] = {"name": spec, "values": None}
        else:
            out[raw] = {
                "name": spec["name"],
                "values": {str(k): str(v) for k, v in (spec.get("values") or {}).items()},
            }
    return out


def apply_renames(table: Table, queries: List[IQuery], cfg: dict) -> Tuple[List[str], List[List[str]], List[str]]:
    """Apply the schema's rename map — header, cell values, and SQL."""
    comp_rename = {
        f"__comp_{i}": group["name"]
        for i, group in enumerate(cfg.get("compression_groups", []))
    }
    bin_rename = _parse_binary_rename(cfg)

    # --- header ---
    header = []
    for t in table.titles:
        if t in comp_rename:
            header.append(comp_rename[t])
        elif t in bin_rename:
            header.append(bin_rename[t]["name"])
        else:
            header.append(t)
    header.append(table.sensitive_column_name)

    # --- rows (with value remapping on binary/categorical columns) ---
    rows: List[List[str]] = []
    n = table.shape[0]
    for i in range(n):
        row = []
        for t in table.titles:
            v = str(table[t][i])
            if t in bin_rename and bin_rename[t]["values"]:
                v = bin_rename[t]["values"].get(v, v)
            row.append(v)
        row.append(str(table.sensitive[i]))
        rows.append(row)

    # --- SQL: rename columns, then rewrite the matching-value literal ---
    sql_list = []
    for q in queries:
        s = q.sql
        # Column names: longest-first to avoid column_1 matching inside column_10
        all_names = list(comp_rename.items()) + [(k, v["name"]) for k, v in bin_rename.items()]
        for raw, new in sorted(all_names, key=lambda kv: -len(kv[0])):
            s = s.replace(raw, new)
        # Value literal rewrite: rewrite every `<renamed_col> = 'X'` using the
        # configured mapping for X. Covers the standard `= '1'` matching
        # queries and the decoy-mode `= '0'` negation query.
        for raw_col, spec in bin_rename.items():
            if not spec["values"]:
                continue
            new_col = spec["name"]
            for raw_val, mapped_val in spec["values"].items():
                s = s.replace(f"{new_col} = '{raw_val}'", f"{new_col} = '{mapped_val}'")
        sql_list.append(s)

    return header, rows, sql_list


def verify_reconstruction(table: Table, queries: List[IQuery], n_core: int) -> dict:
    """Solve the reconstruction system for the first `n_core` records.

    When `n_core == table.shape[0]`, this is the standard end-to-end check.
    When `n_core < table.shape[0]` (decoy mode), the remaining rows are
    decoys whose columns in the incidence matrix are all zero; we filter
    them out and solve `M[:, :n_core] · s = b` against the first `n_core`
    ground-truth values.
    """
    import numpy as np

    N = table.shape[0]
    vectors = [q.as_vector(table) for q in queries]
    M_full = np.array(vectors, dtype=float)  # queries × N
    b = np.array([q(table) * sum(q.as_vector(table)) for q in queries], dtype=float)

    # Sanity check: decoy rows must have zero columns in M_full.
    decoy_block = M_full[:, n_core:]
    decoy_mass = float(decoy_block.sum()) if decoy_block.size else 0.0

    M = M_full[:, :n_core]
    rank = int(np.linalg.matrix_rank(M))
    s_hat, *_ = np.linalg.lstsq(M, b, rcond=None)
    s_true = np.array(table.sensitive[:n_core], dtype=float)
    max_err = float(np.max(np.abs(s_hat - s_true)))

    return {
        "n_total":          N,
        "n_reconstructable": n_core,
        "n_queries":        len(queries),
        "matrix_rank":      rank,
        "full_rank":        rank == n_core,
        "decoy_leakage":    decoy_mass,  # should be 0.0 when decoys are invisible
        "max_abs_error":    max_err,
        "reconstructed":    s_hat.round().astype(int).tolist(),
        "ground_truth":     s_true.astype(int).tolist(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--decoy-fraction", type=float, default=0.0,
                    help="reconstructable fraction of total records; 0 = no decoys")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.schema.read_text())
    args.out.mkdir(parents=True, exist_ok=True)

    table, queries, n_core = run_pipeline(cfg, decoy_fraction=args.decoy_fraction)
    header, rows, sql_list = apply_renames(table, queries, cfg)

    csv_path = args.out / "table.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    sql_path = args.out / "queries.sql"
    sql_path.write_text("\n".join(sql_list) + "\n")

    result = verify_reconstruction(table, queries, n_core)
    result["config"] = {
        "name": cfg.get("name"),
        "n_records_target": cfg.get("n_records"),
        "mip_base": cfg["mip_base"],
        "hadamard_order": cfg["hadamard_order"],
        "population_value": cfg["population_value"],
        "communality_value": cfg["communality_value"],
        "seed": cfg["seed"],
        "sensitive_column": cfg["sensitive_column"],
        "decoy_fraction": args.decoy_fraction,
    }
    (args.out / "reconstruction.json").write_text(json.dumps(result, indent=2))

    summary_lines = [
        f"Experiment: {cfg['name']}"
        + (f"  [decoys: {args.decoy_fraction:.0%} reconstructable]"
           if args.decoy_fraction else ""),
        f"  total records : {result['n_total']}",
        f"  reconstructable: {result['n_reconstructable']}",
        f"  n queries     : {result['n_queries']}",
        f"  matrix rank   : {result['matrix_rank']} / {result['n_reconstructable']}",
        f"  full rank?    : {result['full_rank']}",
    ]
    if args.decoy_fraction:
        summary_lines.append(f"  decoy leakage : {result['decoy_leakage']}")
    summary_lines += [
        f"  max |ŝ − s|   : {result['max_abs_error']:.3e}",
        f"  reconstructed : {'EXACT' if result['max_abs_error'] < 0.5 else 'APPROXIMATE'}",
    ]
    summary = "\n".join(summary_lines)
    (args.out / "reconstruction.txt").write_text(summary + "\n")
    print(summary)
    return 0 if result["full_rank"] and result["max_abs_error"] < 0.5 else 1


if __name__ == "__main__":
    sys.exit(main())
