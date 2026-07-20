# Experiment 02 — ADaM ADSL (Subject-Level Analysis), n=32

CDISC **ADaM Subject-Level Analysis Dataset**, the canonical
one-row-per-subject backbone of clinical trial analysis.  Released
aggregates over demographic and baseline-covariate predicates fully
reconstruct the hidden `egfrbl` (baseline estimated Glomerular Filtration
Rate) of every subject.

## Configuration

| | |
|---|---|
| Records (n) | 32 |
| MIP base | 8 |
| Hadamard order (k) | 3 (two Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `egfrbl` |
| Query count | 32 (31 per-column + 1 all-records) |
| Records per query | p·n = 16 |

## Schema

Released columns (31): 10 binary/categorical + 6 numerical (range-compressed):

| Column | Type | Domain |
|---|---|---|
| `sex` | cat | M / F |
| `race` | cat | WHITE / BLACK / ASIAN / OTHER |
| `ethnic` | cat | HISPANIC OR LATINO / NOT HISPANIC OR LATINO |
| `country` | cat | USA / DEU / FRA / GBR |
| `armcd` | cat | PLACEBO / ACTIVE |
| `agegr1` | cat | 18-64 / 65-80 |
| `saffl`, `ittfl`, `compfl`, `fasfl` | flags | Y / N |
| `age` | num (4 bits) | 0–80 years |
| `heightbl` | num (4 bits) | 0–160 cm |
| `weightbl` | num (4 bits) | 0–160 kg |
| `bmibl` | num (3 bits) | 0–40 kg/m² |
| `durdis` | num (3 bits) | 0–48 months |
| `trtdurd` | num (3 bits) | 0–240 days |

## Reproduce

```bash
bash run.sh
```

Outputs land in `output/` with the standard structure.
