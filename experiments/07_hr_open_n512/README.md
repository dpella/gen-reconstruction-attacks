# Experiment 07 — HR Open Standards (n=512)

Extension of exp. 06 to a **3-year performance horizon**, the standard
time window for the "integrated people-analytics warehouse" flat files
that enterprise HRIS (Workday, SuccessFactors, BambooHR) and consulting
firms' analytics teams routinely materialize for downstream modeling —
attrition, compensation equity, utilization forecasting.

Per-column structure: **one row per employee, 511 released per-cohort
aggregate queries** — a typical BI dashboard's worth of cuts —
uniquely reconstruct every employee's hidden annual salary.

## Configuration

| | |
|---|---|
| Records (n) | **512** |
| MIP base | 8 |
| Hadamard order (k) | 7 (six Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `salary` |
| Query count | 512 (511 per-column + 1 all-records) |
| Records per query | p·n = 256 |
| Wall clock (end-to-end) | ≈ 28 s |

## Schema

Released columns (511 queries):

- **Static + yearly summary** (23 numerical × 3 bits):
  `age`, `tenure_years`, `years_experience`, `years_in_role`,
  `years_in_company`, `direct_reports`, `indirect_reports_span`,
  `training_hours_y{1,2,3}`, `pto_balance_days`, `sick_days_ytd`,
  `pto_taken_y{1,2,3}`, `commute_miles`, `certifications_count`,
  `languages_spoken`, `projects_count_y{1,2,3}`,
  `publications_count`, `patents_count`.

- **Monthly KPIs for 36 months** (4 metrics × 36 months × 3 bits = 8 bins):
  `bill_hrs_yNmMM`, `util_pct_yNmMM`, `overtime_yNmMM`,
  `hours_worked_yNmMM` for N ∈ {1, 2, 3}, MM ∈ {01..12}.

- **Categorical** (10): `sex`, `department`, `employment_type`,
  `education_level`, `country`, `remote_flag`, `union_member`,
  `equity_eligible`, `benefits_tier`, `stock_eligible`.

Budget: 23 × 3 + 4 × 36 × 3 + 10 = 69 + 432 + 10 = **511** ✓

> **Omitted (would trivially leak salary)**: `bonus`, `equity_grants`,
> `total_comp`, `billing_rate`.

## Reproduce

```bash
bash run.sh
```

## Why this schema supports n=512

A 3-year per-employee monthly flat file has ~150 independent numerical
KPI columns by default — billable hours, utilization, overtime, hours
worked, training hours, PTO taken, and customer-facing metrics — all
time-series that are biologically independent month to month in
terms of aggregate queries. Combined with static career covariates,
this easily supplies > 511 linearly-independent aggregate constraints,
enabling exact reconstruction of a 512-subject salary vector from an
otherwise-ordinary-looking HR BI release.
