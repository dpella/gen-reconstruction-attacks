# Showcase web app

A public site that helps people working with health data (pharma,
hospitals, registers) see a subtle but important risk, and test the privacy
metrics and disclosure rules they may be using. It is built on the paper
*Schema-Driven Generation of Reconstructable Datasets from Aggregate
Releases* (to appear at NordSec 2026).

## The scenario

The core message: **releasing quasi-identifiers while allowing averages of a
sensitive attribute to be queried can let anyone infer that attribute for
every patient.** The site follows the attacker model from the paper's
introduction:

- a data holder **releases** each patient's ordinary attributes (age, sex,
  region, treatment, …), with or without direct identifiers such as name or
  personnummer;
- it **withholds** one sensitive attribute (e.g. HbA1c);
- for transparency, it still **allows averages** of that attribute over
  groups defined by the released attributes, each covering half of the
  patients.

Those averages recover the withheld value of every patient exactly. The
released attributes are quasi-identifiers, so once the value is recovered,
patients can be re-identified through traditional linkage attacks.

The site describes this as a common, well-intentioned practice with a
subtle risk, not as a mistake. Scenarios are phrased as "Suppose…", and no
organisation is described as releasing data this way.

## The three tabs

1. **Why it matters**: six short steps, in plain language:
   - what feels safe (de-identified attributes, withheld values, averages);
   - why that was fine when releases were rare;
   - the growth of releases with the European Health Data Space;
   - the scenario above;
   - the Dinur–Nissim result (an interactive three-patient puzzle, with
     links to the US Census Bureau's reconstruction and to recent attacks);
   - why safeguards built for a different world need checking.
2. **How it works**: two examples each for pharma, healthcare and the
   Swedish public sector. Visitors:
   - see the released attributes of 16 synthetic patients and the 16
     allowed averages;
   - select an average to see which patients it covers and the equation it
     gives;
   - solve the equations to recover the withheld column.
3. **Examples of reconstructable datasets**: every schema, with links to
   its source standard and its scenario. Each is available in three
   variants:
   - fully reconstructable;
   - hidden among decoys so that 10% of the rows are reconstructable;
   - hidden among decoys so that 5% of the rows are reconstructable.

   Every dataset is known to leak, so a reliable privacy metric should flag
   it.

## Datasets

Every schema follows a published one-row-per-person standard, with its
official variable names, codes and derivations (`backend/standards/`).
Variables a standard derives (BMI, age groups, eGFR, risk scores, dates,
IDs, …) are derived the same way, and never from the withheld attribute.

| Category | Schema | Withheld attribute | n |
|---|---|---|---|
| Pharma | CDISC ADaM ADSL, Alzheimer's trial (CDISC pilot study) | `MMSETOT` (MMSE) | 32 |
| Pharma | CDISC ADaM ADSL, EU type 2 diabetes trial | `HBA1CBL` (HbA1c) | 32 |
| Healthcare | OMOP CDM + OHDSI FeatureExtraction, type 2 diabetes cohort | HbA1c value | 64 |
| Healthcare | OMOP CDM + OHDSI FeatureExtraction, HIV cohort | HIV-1 viral load | 64 |
| Healthcare | OMOP CDM + OHDSI FeatureExtraction, COVID-19 cohort | Hospital Frailty Risk Score | 64 |
| Public sector | SWEDEHEART RIKS-HIA | `Maxvärde_markör` (peak troponin) | 64 |
| Public sector | Nationella Diabetesregistret (NDR) | `R_HbA1c` | 32 |
| Public sector | SCB LISA | `SjukP_Ndag_MiDAS` (sick-leave days) | 32 |

`n` records need `n − 1` independent queries, so `n` is as large as each
standard's variables support. The walkthrough uses the 16-record table found
by the MIP solver alone. The downloads scale it with Hadamard doublings.
The walkthrough shows the schemas marked `featured` in `backend/schemas.py`.

Each download contains:

- `dataset.csv`: including the withheld column, so the attack can be
  verified;
- `queries.sql` and `released_aggregates.csv`: the queries and their
  answers;
- `reconstruction.json`: the ground truth;
- for OMOP, `covariate_ref.csv`.

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
  - Texts are in `src/Intro.tsx`, `src/Walkthrough.tsx` and
    `src/Downloads.tsx`.
  - Links and the paper title are in `src/links.ts`.
- `check_datasets.py` verifies the published files independently of the
  generator:
  - every query, run as SQL on the CSV, reproduces its published answer;
  - solving the published averages gives full rank and exact values;
  - in the decoy variants, no decoy satisfies any query and the catch-all
    query was replaced.

  It runs during the Docker build, so a failing dataset cannot be deployed.

Two substitutions keep the data realistic without affecting reconstruction,
which depends only on which records each query covers:

- the tool's `[1, 100000]` values for the withheld attribute are replaced
  by plausible ranges;
- numeric columns are mapped to realistic units and bins, with the SQL bounds
  rewritten to match.

### Adding a schema

Add a `SchemaTemplate` in `backend/standards/` and register it in
`_templates()` in `backend/schemas.py`. Then check that it fits and
validates:

```bash
python3 -c "from webapp.backend import schemas; t = schemas.TEMPLATES['<id>']; [schemas.fit(t, n) for n in (16, t.download_n)]"
```

`fit()` rejects names that are not SQL identifiers, ambiguous category
labels, and bins finer than the released precision. A Docker build then
generates the datasets and verifies them.

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
