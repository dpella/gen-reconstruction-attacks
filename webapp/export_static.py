"""
Export everything the site's API serves as static files, so the site can be
hosted without a server (e.g. as a page of dpella.io).

    python3 webapp/export_static.py OUT_DIR

Writes, mirroring the API:

    OUT_DIR/schemas.json                         <- /api/schemas
    OUT_DIR/catalog.json                         <- /api/catalog
    OUT_DIR/demo/<schema>.json                   <- /api/demo/<schema>
    OUT_DIR/results/<schema>/<n>/<mode>/<file>   <- /api/results/...

Datasets come from the precomputed cache (generated first if missing), so
run it where the generator's dependencies are installed, e.g. in the image:

    docker run --rm -v "$PWD":/app/webapp/out reconstruction-showcase \
        python webapp/export_static.py webapp/out
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repository root

from webapp.backend import engine, main, schemas  # noqa: E402


def export(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "schemas.json").write_text(json.dumps(main.list_schemas()))
    (out / "catalog.json").write_text(json.dumps(main.catalog()))

    for t in schemas.TEMPLATES.values():
        demo = engine.generate(t.id, engine.DEMO_N, "full")
        (out / "demo").mkdir(exist_ok=True)
        shutil.copyfile(demo / "result.json", out / "demo" / f"{t.id}.json")
        for mode in engine.MODES:
            src = engine.generate(t.id, t.download_n, mode)
            dst = out / "results" / t.id / str(t.download_n) / mode
            dst.mkdir(parents=True, exist_ok=True)
            for name in main.DOWNLOADS:
                shutil.copyfile(src / name, dst / name)

    files = [p for p in out.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print(f"exported {len(files)} files ({size / 1e6:.1f} MB) to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    export(Path(sys.argv[1]))
