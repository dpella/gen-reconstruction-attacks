# Experiment 08 — Eurostat EU-SILC (n=128)

**Eurostat EU-SILC** (Statistics on Income and Living Conditions) is the
EU's flagship SDMX-compliant microdata source on income, poverty, and
living conditions, collected annually by all member states. One row per
household, 4-year rotational panel design.

Released aggregates over demographic, housing, employment, health, and
material-deprivation predicates uniquely reconstruct the hidden
`total_disposable_income` (equivalised household disposable income,
`HY020` / `HX090` in the EU-SILC DSD — the standard poverty-measurement
variable).

## Configuration

| | |
|---|---|
| Records (n) | 128 |
| MIP base | 8 |
| Hadamard order (k) | 5 (four Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `total_disposable_income` |
| Query count | 128 (127 per-column + 1 all-records) |
| Records per query | p·n = 64 |
| Wall clock (end-to-end) | ≈ 4 s |

## Schema

Released columns (127 queries):

- **Static cross-sectional** (20 numerical × 3 bits = 8 bins):
  `age`, `hh_size`, `hh_children`, `hh_rooms`, `floor_area`,
  `years_education`, `dwelling_age`, `hours_worked_main`,
  `years_paid_work`, `distance_to_work_km`, `commute_minutes`,
  `num_cars`, `hh_employed_count`, `hh_unemployed_count`,
  `months_sick_last_yr`, `chronic_conditions`, `doctor_visits_yr`,
  `years_current_home`, `internet_hours_daily`, `children_under_16`.

- **4-year EU-SILC panel** (4 metrics × 4 years × 3 bits = 48):
  `housing_cost_yN`, `hours_worked_yN`, `heating_cost_yN`,
  `medical_oop_yN`  for N ∈ {1, 2, 3, 4}.

- **Categorical** (19): `sex`, `marital_status`, `country`,
  `education_level`, `urbanization` (Eurostat DEGURBA), `tenure_status`,
  `employment_status`, `health_status`, `chronic_illness`, `disability`,
  and 9 material-deprivation / ICT-access binary flags.

Budget: 20 × 3 + 4 × 4 × 3 + 19 = **127** ✓

> **Omitted (would trivially leak income)**: all income subcomponents —
> `PY010` (employee cash), `PY050` (self-employment), `HY040` (rental),
> `HY090` (interest/dividends), `PY100–140` (social-insurance benefits),
> `HY050–080` (transfers), `HY140` (taxes paid). These are additive
> components of `HY020` and would collapse the reconstruction to
> trivial.

## Reproduce

```bash
bash run.sh
```
