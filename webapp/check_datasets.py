"""
End-to-end check of the published artefacts, independent of the generator:

1. Consistency: load `dataset.csv` into SQLite, run every published query,
   and compare the answer and group size with what the site publishes.
2. Reconstruction, attacker's view: using only the SQL predicates (on the
   non-sensitive columns) and the published averages, build the linear
   system and solve it. Every row covered by some query must be recovered
   exactly, those rows must be exactly the n vulnerable records (decoys are
   never covered), and the system must have full rank n.
3. Decoys (10% and 5% variants): the table has exactly n/f - n decoy rows
   for reconstructable fraction f, no decoy
   satisfies any published query, and deleting every decoy leaves every
   published average unchanged.
4. Catch-all replacement (decoy variants): the construction replaces the
   unconditional `SELECT AVG(s) FROM table` (which would count the decoys)
   with `WHERE <col> = '<no>'`, the negation of `<col> = '<yes>'`. Check that
   no unconditional query remains, and that on the vulnerable rows the pair
   is an exact partition while neither query matches any decoy.

    python3 webapp/check_datasets.py [CACHE_DIR]   # default: webapp/cache
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np


def _is_number(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


def check(path: Path) -> int:
    header, *rows = list(csv.reader((path / "dataset.csv").open()))
    numeric = [all(_is_number(r[i]) for r in rows) for i in range(len(header))]

    con = sqlite3.connect(":memory:")
    cols = ", ".join(f'"{h}" {"REAL" if num else "TEXT"}' for h, num in zip(header, numeric))
    con.execute(f"CREATE TABLE t ({cols})")
    con.executemany(
        f"INSERT INTO t VALUES ({', '.join('?' * len(header))})",
        [[float(v) if num else v for v, num in zip(r, numeric)] for r in rows],
    )

    result = json.loads((path / "result.json").read_text())
    sensitive = result["sensitive"]["name"]
    n = result["summary"]["reconstructable_records"]
    failures = 0
    incidence, sums = [], []
    for q in result["queries"]:
        sql = q["sql"].replace("FROM table", "FROM t")
        where = sql[sql.index(" FROM"):]
        if sensitive in where:
            failures += 1
            print(f"  query filters on the sensitive column: {q['sql'][:80]}")
        answer = con.execute(sql).fetchone()[0]
        members = [r[0] - 1 for r in con.execute(f"SELECT rowid{where}")]
        if answer is None or abs(answer - q["answer"]) > 1e-6 or len(members) != q["matched"]:
            failures += 1
            if failures <= 3:
                print(f"  mismatch: {q['sql'][:80]} published {q['answer']} over {q['matched']}, "
                      f"got {answer} over {len(members)}")
        row = np.zeros(len(rows))
        row[members] = 1
        incidence.append(row)
        sums.append(q["answer"] * q["matched"])  # published average x group size

    # Decoys: none may satisfy a query, and removing them changes nothing.
    decoy_problems = 0
    catch_all = ""
    n_decoys = len(rows) - n
    fraction = result["summary"].get("reconstructable_fraction", 1.0)
    if fraction < 1:
        expected = round(n / fraction) - n
        if n_decoys != expected:
            decoy_problems += 1
            print(f"  expected {expected} decoys, found {n_decoys}")
        hits = int(np.array(incidence)[:, n:].sum())  # decoy rows matched by any query
        if hits:
            decoy_problems += 1
            print(f"  decoys satisfy published queries {hits} times")
        con.execute(f"DELETE FROM t WHERE rowid > {n}")
        for q in result["queries"]:
            core_only = con.execute(q["sql"].replace("FROM table", "FROM t")).fetchone()[0]
            if core_only is None or abs(core_only - q["answer"]) > 1e-6:
                decoy_problems += 1
                if decoy_problems <= 3:
                    print(f"  average changes without decoys: {q['sql'][:80]}")
        # The catch-all replacement: the query pair on the negation column.
        if any(" WHERE " not in q["sql"] for q in result["queries"]):
            decoy_problems += 1
            print("  an unconditional query remains; it would count the decoys")
        neg_col = result["columns"][-2]["name"]
        pair = [
            i for i, q in enumerate(result["queries"])
            if re.search(rf" WHERE {re.escape(neg_col)} = '[^']*';$", q["sql"])
        ]
        if len(pair) != 2:
            decoy_problems += 1
            print(f"  expected a yes/no query pair on {neg_col}, found {len(pair)}")
        else:
            both = np.array(incidence)[pair]
            partition = np.array_equal(both[:, :n].sum(axis=0), np.ones(n))
            if not partition or both[:, n:].any():
                decoy_problems += 1
                print(f"  {neg_col} pair is not an exact partition of the vulnerable rows")
            else:
                yes_label = result["columns"][-2]["detail"].split(" / ")[0]
                negation = next(
                    result["queries"][i]["sql"] for i in pair
                    if not result["queries"][i]["sql"].endswith(f"= '{yes_label}';")
                )
                catch_all = f"catch-all replaced by {negation.split(' WHERE ')[1].rstrip(';')}"
    elif n_decoys:
        decoy_problems += 1
        print(f"  fully reconstructable table has {n_decoys} extra rows")
    failures += decoy_problems

    # Attacker: solve for every record any query touches.
    M = np.array(incidence)
    touched = np.flatnonzero(M.any(axis=0))
    M = M[:, touched]
    rank = int(np.linalg.matrix_rank(M))
    solution, *_ = np.linalg.lstsq(M, np.array(sums), rcond=None)
    sens_idx = header.index(result["sensitive"]["name"])
    truth = np.array([float(rows[i][sens_idx]) for i in touched])
    tolerance = 0.5 * 10 ** -result["sensitive"].get("decimals", 0)
    max_err = float(np.max(np.abs(solution - truth))) if len(touched) else float("inf")
    recovered = int(np.sum(np.abs(solution - truth) < tolerance))

    ok = (
        failures == 0
        and rank == n
        and len(touched) == n
        and list(touched) == list(range(n))  # exactly the vulnerable rows
        and recovered == n
    )
    print(f"{'ok  ' if ok else 'FAIL'} {path.name:30s} {len(rows):5d} rows, {len(result['queries']):3d} queries, "
          f"{failures} problems | rank {rank}/{n}, recovered {recovered}/{len(touched)} "
          f"(max error {max_err:.1e})"
          + (f" | {n_decoys} decoys: 0 matched, averages unchanged without them; {catch_all}"
             if fraction < 1 and not decoy_problems else ""))
    return 0 if ok else 1


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "cache"
    dirs = sorted(d for d in root.iterdir() if (d / "result.json").exists())
    if not dirs:
        print(f"no results under {root}")
        return 1
    return 1 if sum(check(d) for d in dirs) else 0


if __name__ == "__main__":
    sys.exit(main())
