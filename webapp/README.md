# Showcase web app

A public site showing that releasing aggregate statistics about health data
can reveal every individual, built on the paper *Schema-Driven Generation of
Reconstructable Datasets from Aggregate Releases* (to appear at NordSec 2026).
It has three tabs:

1. **Why it matters**: a plain-language version of the paper's introduction,
   from "statistics feel safe" to the European Health Data Space and the
   Dinur–Nissim reconstruction result.
2. **How it works**: two examples each for pharma, healthcare and the
   Swedish public sector. Visitors see a 16-record private table and its 16
   published averages, then solve them to recover the hidden column.
3. **Examples of reconstructable datasets**: downloads for every schema,
   fully reconstructable and hidden among decoys (10% and 5% reconstructable).

## Datasets

Every schema follows a published one-row-per-person standard, with its
official variable names, codes and derivations (`backend/standards/`):

| Category | Standard | n |
|---|---|---|
| Pharma | CDISC ADaM ADSL (CDISC pilot study; EU diabetes trial) | 32 |
| Healthcare | OMOP CDM + OHDSI FeatureExtraction (T2DM, HIV, COVID-19 cohorts) | 64 |
| Public sector | SWEDEHEART RIKS-HIA (64), NDR (32), SCB LISA (32) | 32–64 |

`n` records need `n − 1` independent queries, so `n` is as large as each
standard's variables support. The walkthrough uses the 16-record table found
by the MIP solver alone. The downloads scale it with Hadamard doublings.

## Architecture

- `backend/schemas.py` fits a template into the generator's budget and
  validates it. `backend/standards/` holds the templates.
- `backend/engine.py` runs `experiments/common/driver.py` and writes each
  dataset's files to a cache. Every configuration is deterministic, so
  `python -m webapp.backend.engine` precomputes all of them at image build
  time. The running site never runs the solver.
- `backend/main.py` is a FastAPI app that serves the API and the built
  frontend.
- `frontend/` is a Vite + React + TypeScript single-page app.
- `check_datasets.py` verifies the published files independently of the
  generator:
  - every query, run as SQL on the CSV, reproduces its published answer;
  - solving the published averages gives full rank and exact values;
  - in the decoy variants, no decoy satisfies any query and the catch-all
    query was replaced.

  It runs during the Docker build, so a failing dataset cannot be deployed.

Two substitutions keep the data realistic without affecting reconstruction,
which depends only on which records each query covers:

- the tool's `[1, 100000]` hidden values are replaced by plausible ranges;
- numeric columns are mapped to realistic units and bins, with the SQL bounds
  rewritten to match.

## Run

```bash
docker compose -f webapp/docker-compose.yml up -d --build   # port 10000
```

The build precomputes and checks every dataset, which takes about a minute.
The app serves plain HTTP on port 10000 on all interfaces. Put a
TLS-terminating reverse proxy in front of it if HTTPS is needed.

## Develop

```bash
# backend (needs the tool's requirements + glpk-utils)
pip install -r requirements.txt -r webapp/backend/requirements.txt
python -m webapp.backend.engine          # precompute into webapp/cache
python webapp/check_datasets.py          # verify every published dataset
uvicorn webapp.backend.main:app --port 8000

# frontend, proxies /api to :8000
cd webapp/frontend && npm ci && npm run dev
```
