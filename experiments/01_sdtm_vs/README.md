# Experiment 01 — SDTM VS (Vital Signs), n=16

CDISC **SDTM Vital Signs** domain pivoted wide (one row per subject).
Released aggregates over vital-sign predicates fully reconstruct the
hidden `sysbp` (systolic BP) of every subject.

## Configuration

| | |
|---|---|
| Records (n) | 16 |
| MIP base | 8 |
| Hadamard order (k) | 2 (one Sylvester doubling) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `sysbp` |
| Query count | 16 (15 per-column + 1 all-records) |
| Records per query | p·n = 8 |

## Schema

Released columns (15): 3 binary/categorical + 5 numerical (range-compressed):

| Column | Type | Domain |
|---|---|---|
| `sex`, `race`, `vsblfl` | categorical | {M,F}, {WHITE,BLACK,ASIAN,OTHER}, {Y,N} |
| `diabp`, `pulse` | numerical (3 bits → 8 bins) | 0–80 |
| `height`, `weight`, `bmi` | numerical (2 bits → 4 bins) | 0–120 / 0–120 / 0–40 |

## Reproduce

```bash
bash run.sh
```

Outputs land in `output/`: `table.csv`, `queries.sql`, `reconstruction.{txt,json}`.

Verification solves the aggregated system `M·s = b` and compares with the
ground-truth sensitive column. Success criterion: full rank + max
absolute reconstruction error < 0.5.
