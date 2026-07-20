# Experiment 05 — ADaM ADPC extended (parent + metabolite), n=256

CDISC **ADaM Pharmacokinetic Concentrations** dataset in its standard
bioequivalence / bioavailability configuration: one row per subject,
columns = PK concentrations of (parent drug + principal metabolite M1)
at 20 nominal timepoints across two study periods (single-dose p1,
steady-state p2). This is a routine FDA / EMA submission layout.

Released aggregates over concentration-range predicates fully reconstruct
the hidden 24-hour single-dose parent concentration `conc_24h` — a
CYP-phenotype / trough-concentration proxy not derivable from metabolite
levels without the subject's (unknown) metabolic ratio.

## Configuration

| | |
|---|---|
| Records (n) | 256 |
| MIP base | 8 |
| Hadamard order (k) | 6 (five Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `conc_24h` (parent, p1, 24 h) |
| Query count | 256 (255 per-column + 1 all-records) |
| Records per query | p·n = 128 |
| Wall clock (end-to-end) | ≈ 9 s |

## Schema

Released columns (255 queries over 82 table columns):

- **Parent drug, period 1 (single-dose)** — 19 timepoints: 0, 0.25, 0.5,
  1, 1.5, 2, 3, 4, 6, 8, 12, 16, 36, 48, 72, 96, 120, 144, 168 h.
  (24 h is the sensitive column, excluded.)
- **Parent drug, period 2 (steady-state)** — 20 timepoints (same set
  plus 24 h).
- **Metabolite M1, periods 1 & 2** — 40 timepoint columns.
- Each concentration column: 3 bits → 8 bins × 50 ng/mL (parent) or
  × 25 ng/mL (metabolite).
- **Baseline covariates** (compressed): `age` (3 bits), `heightbl`,
  `weightbl`, `bmibl`, `base_creat`, `base_alt`, `base_bili` (2 bits
  each).
- **Categorical** (binary-encoded): `sex`, `race`, `country`.

Budget: 79 × 3 + 3 + 2·4 + 2·3 + 3 = 237 + 3 + 8 + 6 + 3 = **255** ✓

## Reproduce

```bash
bash run.sh
```

`run.sh` calls `generate_schema.py` to emit `schema.yaml` (86 compression
groups + 3 categorical renames — tedious by hand, so the generator is
committed), then invokes the common driver.

## Why this schema supports n=256

A crossover parent-plus-metabolite PK study at dense serial sampling
produces ~80 numerical columns that are independent by biology (each
timepoint captures a different elimination-curve phase; metabolite
concentrations depend on a subject-specific metabolic ratio not
recoverable from parent alone). Combined with routine baseline
renal/hepatic covariates, the released aggregates supply > 255
independent linear constraints on the 256-subject sensitive vector —
enough for exact reconstruction.
