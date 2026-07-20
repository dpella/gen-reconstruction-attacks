# Experiment 04 — ADaM ADPC (Pharmacokinetic Concentrations), n=128

CDISC **ADaM Pharmacokinetic Concentrations** dataset pivoted so each
subject has one row and each column is the PK concentration at one
nominal timepoint in one study period (two-period crossover:
single-dose `p1` and steady-state `p2`).  Released aggregates over
concentration-range predicates fully reconstruct the hidden
24-hour single-dose concentration `conc_24h` — a clinically sensitive
trough/CYP-phenotype proxy — for every subject.

## Configuration

| | |
|---|---|
| Records (n) | 128 |
| MIP base | 8 |
| Hadamard order (k) | 5 (four Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `conc_24h` |
| Query count | 128 (127 per-column + 1 all-records) |
| Records per query | p·n = 64 |
| Wall clock (end-to-end) | ≈ 5 s |

## Schema

Released columns (127 queries):

- **19 single-dose (p1) concentrations** at timepoints 0 h, 0.25 h,
  0.5 h, 1 h, 1.5 h, 2 h, 3 h, 4 h, 6 h, 8 h, 12 h, 16 h, 36 h, 48 h,
  72 h, 96 h, 120 h, 144 h, 168 h. Each 3 bits → 8 bins × 50 ng/mL
  = 0–400 ng/mL.  (The 24-h p1 timepoint is the **sensitive** column,
  so it is *excluded* from the released set.)
- **20 steady-state (p2) concentrations** at the same timepoints
  including 24 h. Each 3 bits → 8 bins × 50 ng/mL = 0–400 ng/mL.
- **Demographics**: `age` (3 bits, 0–80 years), `heightbl` (2 bits,
  0–160 cm), `weightbl` (2 bits, 0–160 kg).
- **Categorical**: `sex` (M/F), `race` (WHITE/BLACK/ASIAN/OTHER),
  `country` (USA/DEU/FRA/GBR).

Budget: 39 × 3 + 3 + 2 + 2 + 3 = **127** ✓

## Reproduce

```bash
bash run.sh
```

`run.sh` regenerates `schema.yaml` via `generate_schema.py` (the 43
compression groups are tedious by hand; the generator is committed for
reproducibility) and then invokes the common driver.

## Why this schema supports n=128

Dense serial PK sampling gives many numerical columns that are
independent by biology (each timepoint captures a different
elimination-curve phase) and in multiple periods. A realistic PK
study release therefore supplies enough independent aggregate
constraints to uniquely determine `conc_24h` for every subject —
even though no single released aggregate concerns any single subject.
