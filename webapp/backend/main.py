"""FastAPI app: schema catalogue, the n=16 walkthrough, precomputed downloads,
and the built single-page frontend."""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import engine, schemas

STATIC_DIR = Path(os.environ.get("STATIC_DIR", Path(__file__).resolve().parents[1] / "frontend" / "dist"))
DOWNLOADS = {
    "dataset.csv": "text/csv",
    "queries.sql": "application/sql",
    "released_aggregates.csv": "text/csv",
    "reconstruction.json": "application/json",
    "bundle.zip": "application/zip",
}

app = FastAPI(title="Reconstructable health datasets", docs_url="/api/docs", openapi_url="/api/openapi.json")


def _check(schema_id: str, n: int, mode: str) -> None:
    if schemas.get(schema_id) is None:
        raise HTTPException(404, "unknown schema")
    if n not in schemas.SUPPORTED_N:
        raise HTTPException(400, f"n must be one of {schemas.SUPPORTED_N}")
    if mode not in engine.MODES:
        raise HTTPException(400, f"mode must be one of {list(engine.MODES)}")


@app.get("/api/schemas")
def list_schemas():
    return {
        "sizes": schemas.SUPPORTED_N,
        "modes": engine.MODES,
        "demo_n": engine.DEMO_N,
        "categories": schemas.CATEGORIES,
        "schemas": [
            {
                "id": t.id,
                "category": t.category,
                "title": t.title,
                "standard": t.standard,
                "domain": t.domain,
                "summary": t.summary,
                "story": t.story,
                "sensitive": asdict(t.sensitive),
                "download_n": t.download_n,
                "featured": t.featured,
                "sources": [{"label": l, "url": u} for l, u in t.sources],
                "demo_columns": [asdict(c) for c in schemas.fit(t, engine.DEMO_N).columns],
            }
            for t in schemas.TEMPLATES.values()
        ],
    }


@app.get("/api/demo/{schema_id}")
def demo(schema_id: str):
    """The fully reconstructable n=16 table used by the walkthrough."""
    _check(schema_id, engine.DEMO_N, "full")
    path = engine.generate(schema_id, engine.DEMO_N, "full")
    return FileResponse(path / "result.json", media_type="application/json")


@lru_cache(maxsize=None)
def _entry(schema_id: str, n: int, mode: str) -> dict:
    path = engine.generate(schema_id, n, mode)
    summary = json.loads((path / "result.json").read_text())["summary"]
    return {
        "n": n,
        "mode": mode,
        "total_records": summary["total_records"],
        "reconstructable_records": summary["reconstructable_records"],
        "queries": summary["queries"],
        "columns": len(json.loads((path / "result.json").read_text())["header"]),
        "files": {name: (path / name).stat().st_size for name in DOWNLOADS},
    }


@app.get("/api/catalog")
def catalog():
    """Each schema's downloadable datasets (full and 10%) with file sizes."""
    out = {}
    for t in schemas.TEMPLATES.values():
        entries = []
        for mode in engine.MODES:
            entries.append(_entry(t.id, t.download_n, mode))
        out[t.id] = entries
    return out


@app.get("/api/results/{schema_id}/{n}/{mode}/{filename}")
def download(schema_id: str, n: int, mode: str, filename: str):
    _check(schema_id, n, mode)
    if filename not in DOWNLOADS:
        raise HTTPException(404, "unknown file")
    path = engine.generate(schema_id, n, mode)
    return FileResponse(
        path / filename,
        media_type=DOWNLOADS[filename],
        filename=f"{engine.key(schema_id, n, mode)}_{filename}",
    )


@app.get("/api/health")
def health():
    return {"ok": True}


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")
