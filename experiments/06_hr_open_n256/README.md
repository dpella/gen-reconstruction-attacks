# Experiment 06 — HR Open Standards (n=256)

**HR Open Standards / HR-XML** — the schema family used by enterprise
HRIS platforms (Workday, SuccessFactors, BambooHR) and consulting-firm
people-analytics teams. One row per employee, columns = static
career / demographic fields + **24 months of per-employee KPIs**.

This is the paper's motivating scenario made concrete: a consulting firm
publishes aggregate analytics over demographics, tenure, performance,
and monthly billable-hours / utilization, while withholding per-employee
salary — yet the release uniquely determines every salary.

## Configuration

| | |
|---|---|
| Records (n) | 256 |
| MIP base | 8 |
| Hadamard order (k) | 6 (five Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `salary` |
| Query count | 256 (255 per-column + 1 all-records) |
| Records per query | p·n = 128 |
| Wall clock (end-to-end) | ≈ 9 s |

## Schema

Released columns (255 queries):

- **Static career / demographic** (18 numerical, each 3 bits → 8 bins):
  `age`, `tenure_years`, `years_experience`, `years_in_role`,
  `direct_reports`, `training_hours_ytd`, `pto_balance_days`,
  `sick_days_ytd`, `overtime_hours_ytd`, `utilization_pct_ytd`,
  `commute_miles`, `certifications_count`, `languages_spoken`,
  `projects_count_ytd`, `publications_count`, `patents_count`,
  `engagement_score`, `customer_sat_score`.

- **Monthly KPIs for 24 months** (2 metrics × 24 months × 4 bits = 16 bins):
  `bill_hrs_y{1,2}m{01..12}` (monthly billable hours) and
  `util_pct_y{1,2}m{01..12}` (monthly utilization %).

- **Categorical** (9): `sex` (M/F), `department`
  (CONSULTING/SALES/ENGINEERING/OPERATIONS), `employment_type`
  (FULLTIME/PARTTIME/CONTRACTOR/INTERN), `education_level`
  (PHD/BS/MS/HS), `country` (USA/DEU/GBR/IND), `remote_flag`,
  `union_member`, `equity_eligible`, `benefits_tier`
  (PREMIUM/STANDARD/BASIC).

Budget: 18 × 3 + 2 × 24 × 4 + 9 = **255** ✓

> **Omitted (would trivially leak salary)**: `bonus`, `equity_grants`,
> `total_comp`, `billing_rate`. These are direct functions of `salary`.

## Reproduce

```bash
bash run.sh
```

`run.sh` regenerates `schema.yaml` via `generate_schema.py` (65
compression groups + 9 categorical — tedious by hand), then invokes the
common driver.
