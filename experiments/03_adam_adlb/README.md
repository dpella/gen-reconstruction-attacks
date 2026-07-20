# Experiment 03 — ADaM ADLB (Laboratory Analysis, Chem + Hematology), n=64

CDISC **ADaM Laboratory Analysis Dataset** covering a standard clinical
chemistry + hematology panel, pivoted so each subject has one row with
baseline values for every lab parameter.  Released aggregates over
per-parameter range predicates fully reconstruct the hidden `aval`
(target-parameter analysis value, here fasting plasma glucose) of every
subject.

## Configuration

| | |
|---|---|
| Records (n) | 64 |
| MIP base | 8 |
| Hadamard order (k) | 4 (three Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `aval` (target `paramcd` = `GLUC`) |
| Query count | 64 (63 per-column + 1 all-records) |
| Records per query | p·n = 32 |

## Schema

Released columns (63 queries over 25 table columns): 4 binary/categorical + 21
numerical (range-compressed).

**Chemistry panel** (15 baseline values × 3 bits = 8 bins each):
`base_alt`, `base_ast`, `base_bun`, `base_creat`, `base_chol`, `base_hdl`,
`base_ldl`, `base_tg`, `base_hgb`, `base_hct`, `base_plt`, `base_wbc`,
`base_alb`, `base_bili`, `base_alp`.

**Target-parameter context**:
| Column | Bits | Range |
|---|---|---|
| `base` (baseline glucose) | 2 | 0–120 mg/dL |
| `age` | 3 | 0–80 years |
| `avisitn` | 2 | 0–4 visits |
| `ady` | 3 | 0–240 days |
| `anrlo` | 2 | 0–80 mg/dL |
| `anrhi` | 2 | 0–120 mg/dL |

**Categorical**: `sex` (M/F), `race` (WHITE/BLACK/ASIAN/OTHER),
`paramcd` (GLUC/CHOL/TG/HDL), `saffl` (Y/N).

> The derived fields `chg`, `pchg`, and `anrind` are **omitted** from
> the released schema because they are direct functions of `aval` and
> would trivially leak the sensitive value.

## Reproduce

```bash
bash run.sh
```
