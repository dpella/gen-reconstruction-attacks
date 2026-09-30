"""
Runs the paper's pipeline (experiments/common/driver.py) for a fitted schema
and stores every artefact the web app serves in a per-configuration cache
directory. All configurations are deterministic (fixed seed), so the Docker
build precomputes them and the running site only reads from the cache.
"""
from __future__ import annotations

import csv
from decimal import ROUND_FLOOR, Decimal
import hashlib
import inspect
import io
import json
import math
import os
import random
import shutil
import re
import sys
import threading
import time
import zipfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "experiments" / "common"))

import driver  # noqa: E402  (also puts REPO_ROOT on sys.path)

from . import schemas  # noqa: E402

CACHE_DIR = Path(os.environ.get("CACHE_DIR", REPO_ROOT / "webapp" / "cache"))
# Reconstructable fraction of the table (0 = all rows are reconstructable).
MODES = {"full": 0.0, "partial": 0.1, "partial5": 0.05}
PREVIEW_ROWS = 200
DEMO_N = 16


def precomputed(template: "schemas.SchemaTemplate"):
    """Everything the site serves for one schema."""
    n = template.download_n
    return [(DEMO_N, "full")] + [(n, mode) for mode in MODES]

# The generator relies on the global `random` state and a logger singleton,
# so runs must never overlap.
_LOCK = threading.Lock()


def key(schema_id: str, n: int, mode: str) -> str:
    return f"{schema_id}_n{n}_{mode}"


def cache_path(schema_id: str, n: int, mode: str) -> Path:
    return CACHE_DIR / key(schema_id, n, mode)


def _release_numeric(header, rows, sql_list, transforms, rng):
    """Map each numeric column from the tool's integer bins to released units:
    value = offset + interval * x, and the same for every SQL range bound.

    Values are floored to the column's precision and clamped inside their
    bin with exact decimal arithmetic, so no value can cross a bin edge
    through rounding (a bin is [k, k+1) in tool units)."""
    idx = {h: i for i, h in enumerate(header)}
    for name, (offset, interval, dec) in transforms.items():
        j = idx[name]
        off, width = Decimal(str(offset)), Decimal(str(interval))
        quantum = Decimal(1).scaleb(-dec)
        for row in rows:
            x = Decimal(row[j])
            k = x.to_integral_value(rounding=ROUND_FLOOR)
            lo = off + width * k
            # The tool places values on the bin's lower edge; spread them
            # uniformly inside the bin instead (membership is unchanged).
            position = x - k if x != k else Decimal(repr(rng.random()))
            value = (lo + width * position).quantize(quantum, rounding=ROUND_FLOOR)
            value = min(max(value, lo), lo + width - quantum)
            row[j] = f"{value:f}"

    pat = re.compile(r"\(([^\W\d]\w*) >= (-?[\d.]+) AND ([^\W\d]\w*) < (-?[\d.]+)\)")

    def bound(name, raw):
        offset, interval, _ = transforms[name]
        return format((Decimal(str(offset)) + Decimal(str(interval)) * Decimal(raw)).normalize(), "f")

    def rewrite(m):
        name = m.group(1)
        return f"({name} >= {bound(name, m.group(2))} AND {m.group(3)} < {bound(name, m.group(4))})"

    return [pat.sub(rewrite, q) for q in sql_list]


def _fingerprint(fitted: "schemas.FittedSchema", mode: str) -> str:
    """Changes whenever anything that shapes the output changes, so edited
    schemas never serve stale cached files."""
    spec = {
        "config": fitted.config,
        "transforms": fitted.transforms,
        "sensitive": vars(fitted.template.sensitive),
        "derive": inspect.getsource(fitted.template.derive) if fitted.template.derive else None,
        "column_order": fitted.template.column_order,
        "mode": MODES[mode],
    }
    return hashlib.sha256(json.dumps(spec, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _is_current(out: Path, fingerprint: str) -> bool:
    f = out / "fingerprint"
    return (out / "result.json").exists() and f.exists() and f.read_text() == fingerprint


def _derive(template, header, rows, sql_list, n_core, seed):
    """Add the template's derived columns (IDs, groupings, BMI, dates, ...)
    computed from each row's released values, then apply the standard's
    column order. Derived columns are never referenced by a query, so they
    cannot affect the published answers or the reconstruction."""
    if template.derive is None:
        return header, rows
    rng = random.Random(f"derive-{seed}")
    records = []
    for i, row in enumerate(rows):
        rec = dict(zip(header, row))
        extra = template.derive(rec, rng, i, i >= n_core)
        clash = set(extra) & set(header)
        assert not clash, f"derived columns overwrite released ones: {clash}"
        rec.update({k: str(v) for k, v in extra.items()})
        records.append(rec)
    derived = [k for k in records[0] if k not in header]
    for name in derived:
        pattern = re.compile(rf"\b{re.escape(name)}\b")
        assert not any(pattern.search(q) for q in sql_list), f"query uses derived column {name}"
    present = set(header + derived)
    order = [c for c in (template.column_order or header + derived) if c in present]
    assert set(order) == present, f"{template.id}: column_order lacks {present - set(order)}"
    assert len(order) == len(set(order)), f"{template.id}: duplicate columns in column_order"
    return order, [[rec[c] for c in order] for rec in records]


def generate(schema_id: str, n: int, mode: str) -> Path:
    out = cache_path(schema_id, n, mode)
    template = schemas.get(schema_id)
    if template is None or mode not in MODES:
        raise ValueError("unknown schema or mode")
    fitted = schemas.fit(template, n)
    cfg = fitted.config
    fingerprint = _fingerprint(fitted, mode)
    if _is_current(out, fingerprint):
        return out

    with _LOCK:
        if _is_current(out, fingerprint):
            return out
        started = time.perf_counter()
        table, queries, n_core = driver.run_pipeline(cfg, decoy_fraction=MODES[mode])

        # The tool draws the sensitive attribute uniformly from [1, 100000].
        # Reconstruction holds for *any* values (it only depends on the query
        # incidence matrix having full rank), so substitute a clinically
        # plausible range for the demo.
        sens = template.sensitive
        rng = random.Random(f"{schema_id}-{n}-{mode}")
        if sens.decimals:
            values = [round(rng.uniform(sens.low, sens.high), sens.decimals) for _ in range(table.shape[0])]
        else:
            values = [rng.randint(int(sens.low), int(sens.high)) for _ in range(table.shape[0])]
        table.set_sensitive_column(values)

        header, rows, sql_list = driver.apply_renames(table, queries, cfg)
        sql_list = _release_numeric(header, rows, sql_list, fitted.transforms,
                                    random.Random(f"bins-{schema_id}-{n}-{mode}"))
        query_columns = list(header)
        header, rows = _derive(template, header, rows, sql_list, n_core, f"{schema_id}-{n}-{mode}")
        answers = [float(q(table)) for q in queries]
        vectors = [q.as_vector(table) for q in queries]
        verification = driver.verify_reconstruction(table, queries, n_core)
        # The driver rounds to integers; solve again to report at the
        # sensitive attribute's own precision.
        M = np.array(vectors, dtype=float)[:, :n_core]
        b = np.array([a * sum(v) for a, v in zip(answers, vectors)])
        s_hat = np.linalg.lstsq(M, b, rcond=None)[0]
        truth = [values[i] for i in range(n_core)]
        reconstructed = [round(float(x), sens.decimals) if sens.decimals else int(round(float(x))) for x in s_hat]
        elapsed = time.perf_counter() - started

    tmp = out.with_name(out.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)

    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows([header] + rows)
    dataset_csv = buf.getvalue()

    queries_sql = "\n".join(sql_list) + "\n"

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["query", "records_matched", f"avg_{sens.name}"])
    for sql, vec, ans in zip(sql_list, vectors, answers):
        w.writerow([sql, sum(vec), repr(ans)])
    aggregates_csv = buf.getvalue()

    reconstruction = {k: v for k, v in verification.items()}
    reconstruction["reconstructed"] = reconstructed
    reconstruction["ground_truth"] = truth
    reconstruction["config"] = cfg

    files = {
        "dataset.csv": dataset_csv,
        "queries.sql": queries_sql,
        "released_aggregates.csv": aggregates_csv,
        "reconstruction.json": json.dumps(reconstruction, indent=2) + "\n",
    }
    if template.extra_files:
        files.update(template.extra_files(header))
    for name, content in files.items():
        (tmp / name).write_text(content)
    with zipfile.ZipFile(tmp / "bundle.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(f"{key(schema_id, n, mode)}/{name}", content)

    total = len(rows)
    preview = rows[:PREVIEW_ROWS]
    if total > n_core:
        # Show a few decoys too, so the difference is visible.
        preview = rows[: min(n_core, PREVIEW_ROWS - 20)] + rows[n_core : n_core + 20]
        preview_index = list(range(min(n_core, PREVIEW_ROWS - 20))) + list(range(n_core, min(total, n_core + 20)))
    else:
        preview_index = list(range(len(preview)))

    result = {
        "schema": schema_id,
        "n": n,
        "mode": mode,
        "summary": {
            "total_records": total,
            "reconstructable_records": n_core,
            "decoy_records": total - n_core,
            "queries": len(queries),
            "matrix_rank": verification["matrix_rank"],
            "full_rank": verification["full_rank"],
            "max_abs_error": verification["max_abs_error"],
            "decoy_leakage": verification["decoy_leakage"],
            "records_per_query": int(cfg["population_value"] * n),
            "reconstructable_fraction": MODES[mode] or 1.0,
            "generation_seconds": round(elapsed, 2),
        },
        "sensitive": {"name": sens.name, "unit": sens.unit, "description": sens.description,
                      "decimals": sens.decimals, "label": sens.label or sens.name},
        "query_columns": query_columns,
        "columns": [
            {"name": c.name, "kind": c.kind, "description": c.description, "detail": c.detail,
             "label": c.label}
            for c in fitted.columns
        ],
        "header": header,
        "preview_rows": preview,
        "preview_index": preview_index,
        "queries": [
            {"sql": s, "matched": sum(v), "answer": a}
            for s, v, a in zip(sql_list, vectors, answers)
        ],
        # Query x reconstructable-record incidence matrix; decoy columns are
        # all zero by construction and omitted.
        "matrix": ["".join("1" if x else "0" for x in v[:n_core]) for v in vectors],
        "ground_truth": truth,
        "reconstructed": reconstructed,
    }
    (tmp / "result.json").write_text(json.dumps(result))

    (tmp / "fingerprint").write_text(fingerprint)
    if out.exists():
        shutil.rmtree(out)
    tmp.rename(out)
    return out


def main() -> int:
    """Precompute everything the site serves."""
    failures = 0
    for schema_id, template in schemas.TEMPLATES.items():
        for n, mode in precomputed(template):
            t = time.perf_counter()
            try:
                path = generate(schema_id, n, mode)
                s = json.loads((path / "result.json").read_text())["summary"]
                ok = s["full_rank"] and s["max_abs_error"] < 0.5 and s["decoy_leakage"] == 0
                failures += not ok
                print(f"{'ok  ' if ok else 'FAIL'} {key(schema_id, n, mode):28s} "
                      f"{s['total_records']:5d} rows  rank {s['matrix_rank']}/{n}  "
                      f"{time.perf_counter() - t:6.1f}s", flush=True)
            except Exception as e:  # keep going; report at the end
                failures += 1
                print(f"FAIL {key(schema_id, n, mode)}: {e!r}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
