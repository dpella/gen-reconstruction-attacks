# Experiment 09 — Eurostat EU-SILC × HBS integrated (n=512)

Integrated **EU-SILC × HBS** (Household Budget Survey) per-household
flat file — the analytical warehouse NSIs materialise to pair EU-SILC's
annual income / labour / health variables with HBS's **12-month
expenditure diary across the COICOP classification**. Both surveys
publish SDMX-compliant DSDs; the integrated file is standard output
for poverty-and-living-standards modelling.

511 released per-cohort aggregate queries — a typical statistical
bulletin's worth of cuts — uniquely reconstruct every household's
hidden `total_disposable_income`.

## Configuration

| | |
|---|---|
| Records (n) | **512** |
| MIP base | 8 |
| Hadamard order (k) | 7 (six Sylvester doublings) |
| (p, c) | (0.5, 0.25) |
| Seed | 42 |
| Sensitive column | `total_disposable_income` |
| Query count | 512 (511 per-column + 1 all-records) |
| Records per query | p·n = 256 |
| Wall clock (end-to-end) | ≈ 28 s |

## Schema

Released columns (511 queries):

- **Static cross-sectional** (20 × 3 bits = 60): `age`, `hh_size`,
  `hh_children`, `hh_rooms`, `floor_area`, `years_education`,
  `dwelling_age`, `distance_to_work_km`, `commute_minutes`, `num_cars`,
  `hh_employed_count`, `hh_unemployed_count`, `years_in_current_home`,
  `chronic_conditions`, `internet_hours_daily`, `children_under_16`,
  `adults_over_65`, `pets_count`, `bedrooms`, `bathrooms`.

- **4-year EU-SILC panel** (12 metrics × 4 years × 3 bits = 144):
  `housing_cost_yN`, `hours_worked_yN`, `heating_cost_yN`,
  `medical_oop_yN`, `months_employed_yN`, `months_unemployed_yN`,
  `months_sick_yN`, `savings_deposit_yN`, `doctor_visits_yN`,
  `training_hours_yN`, `child_care_cost_yN`, `commute_cost_yN`.

- **12-month HBS expenditure diary** (8 COICOP × 12 months × 3 bits = 288):
  `exp_food_mMM`, `exp_housing_utils_mMM`, `exp_transport_mMM`,
  `exp_communication_mMM`, `exp_recreation_mMM`, `exp_education_mMM`,
  `exp_health_mMM`, `exp_restaurants_mMM`.

- **Categorical** (19): same set as experiment 08 — demographics,
  housing tenure, health, and material-deprivation flags.

Budget: 60 + 144 + 288 + 19 = **511** ✓

> **Why monthly expenditure is OK to release**: expenditure tracks
> income in aggregate but is not a deterministic function of it —
> households differ in savings rate, debt service, inter-household
> transfers, and informal-sector activity. Range-predicate aggregates
> over monthly COICOP expenditures therefore constrain income without
> leaking it, exactly as the reconstruction-theorem requires.

> **Omitted (would trivially leak income)**: all EU-SILC income
> sub-components (`PY010–140`, `HY040–090`, `HY140`).

## Reproduce

```bash
bash run.sh
```
