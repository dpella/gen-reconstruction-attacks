"""
Emit schema.yaml for the Eurostat EU-SILC (n=128) experiment.

Budget: 127 query-columns for n=128:
    20 static EU-SILC numerical fields × 3 bits        =  60
    + 4 panel-years × 4 yearly metrics × 3 bits        =  48
    + 19 binary/categorical                             =  19
    = 127
"""
from pathlib import Path

YEARS = ["y1", "y2", "y3", "y4"]  # EU-SILC 4-year rotational panel


def main() -> None:
    lines = []
    w = lines.append

    w("# Eurostat EU-SILC (European Union Statistics on Income and Living")
    w("# Conditions) — subject-level household profile, 4-year rotational")
    w("# panel — n=128")
    w("#")
    w("# Schema origin: EU-SILC is the EU's flagship microdata source on")
    w("# income, poverty, and living conditions, collected annually by all")
    w("# member states under SDMX-compliant DSDs. One row per household,")
    w("# columns = demographics + employment + housing + health +")
    w("# material-deprivation flags + 4-year panel of labor-market and cost")
    w("# variables.  Eurostat publishes hundreds of aggregate cuts annually")
    w("# (by country × age × sex × household type × urbanisation).")
    w("#")
    w("# Construction: MIP base=8 with (p, c) = (0.5, 0.25), Hadamard k=5")
    w("# (four Sylvester doublings) → n=128 households. 127 per-column")
    w("# queries + 1 all-records = 128 queries. Each query aggregates")
    w("# p·n = 64 households.")
    w("#")
    w("# Sensitive (not released): total_disposable_income —")
    w("# equivalised household disposable income (HY020 / HX090 in the")
    w("# EU-SILC DSD). This is the standard poverty-measurement variable.")
    w("#")
    w("# All income subcomponents (PY010, PY050, HY040, HY090, PY100-140,")
    w("# HY050-080, HY140, …) are OMITTED from the released schema —")
    w("# they are additive components of the sensitive variable and would")
    w("# leak trivially.")
    w("")
    w("name: eurostat_silc_n128")
    w("n_records: 128")
    w("seed: 42")
    w("")
    w("mip_base: 8")
    w("hadamard_order: 5")
    w("population_value: 0.5")
    w("communality_value: 0.25")
    w("log_level: WARNING")
    w("")
    w("sensitive_column: total_disposable_income")
    w("")
    w("# 60 + 48 + 19 = 127")
    w("compression_groups:")

    col = 0

    def group(name: str, bits: int, interval: int, note: str) -> None:
        nonlocal col
        cols = ", ".join(f"column_{col + j}" for j in range(bits))
        col += bits
        w(f"  - name: {name}")
        w(f"    columns: [{cols}]")
        w(f"    interval: {interval}   # {note}")

    # --- Static cross-sectional numerical fields (20 × 3 bits = 60) ---
    group("age",                     3, 10, "years, 0-80")
    group("hh_size",                 3,  1, "household size, 0-8")
    group("hh_children",             3,  1, "number of children, 0-8")
    group("hh_rooms",                3,  1, "number of rooms, 0-8")
    group("floor_area",              3, 20, "dwelling floor area m², 0-160")
    group("years_education",         3,  3, "years completed education, 0-24")
    group("dwelling_age",            3, 10, "dwelling age yrs, 0-80")
    group("hours_worked_main",       3,  8, "hours/wk main job, 0-64")
    group("years_paid_work",         3,  6, "total yrs in paid work, 0-48")
    group("distance_to_work_km",     3, 10, "km to workplace, 0-80")
    group("commute_minutes",         3, 15, "commute min, 0-120")
    group("num_cars",                3,  1, "cars owned, 0-8")
    group("hh_employed_count",       3,  1, "employed persons in HH, 0-8")
    group("hh_unemployed_count",     3,  1, "unemployed persons in HH, 0-8")
    group("months_sick_last_yr",     3,  2, "months sick, 0-16")
    group("chronic_conditions",      3,  1, "chronic conditions, 0-8")
    group("doctor_visits_yr",        3,  5, "GP visits last yr, 0-40")
    group("years_current_home",      3,  5, "yrs in current home, 0-40")
    group("internet_hours_daily",    3,  2, "internet hrs/day, 0-16")
    group("children_under_16",       3,  1, "children <16, 0-8")

    # --- 4-year panel of yearly variables (4y × 4 metrics × 3 bits = 48) ---
    for y in YEARS:
        group(f"housing_cost_{y}",   3, 250, f"€/month housing cost, {y}, 0-2000")
    for y in YEARS:
        group(f"hours_worked_{y}",   3,  8, f"avg hrs/wk worked, {y}, 0-64")
    for y in YEARS:
        group(f"heating_cost_{y}",   3, 40, f"€/month heating, {y}, 0-320")
    for y in YEARS:
        group(f"medical_oop_{y}",    3, 100, f"€/yr medical out-of-pocket, {y}, 0-800")

    # --- Binary / categorical (19) ---
    w("")
    w("binary_rename:")
    for col_name, values in [
        ("sex",                  '{"1": F, "0": M, "2": M, "3": M}'),
        ("marital_status",       '{"1": MARRIED, "0": SINGLE, "2": DIVORCED, "3": WIDOWED}'),
        ("country",              '{"1": DEU, "0": FRA, "2": ITA, "3": ESP}'),
        ("education_level",      '{"1": TERTIARY, "0": UPPER_SEC, "2": LOWER_SEC, "3": PRIMARY}'),
        ("urbanization",         '{"1": DENSE, "0": INTERMEDIATE, "2": THIN, "3": THIN}'),
        ("tenure_status",        '{"1": OWNER_FREE, "0": OWNER_MORTGAGE, "2": TENANT_MARKET, "3": TENANT_REDUCED}'),
        ("employment_status",    '{"1": EMPLOYED, "0": UNEMPLOYED, "2": RETIRED, "3": OTHER_INACTIVE}'),
        ("health_status",        '{"1": VERY_GOOD, "0": GOOD, "2": FAIR, "3": POOR}'),
        ("chronic_illness",      '{"1": Y, "0": N, "2": N, "3": N}'),
        ("disability",           '{"1": Y, "0": N, "2": N, "3": N}'),
        ("internet_access",      '{"1": Y, "0": N, "2": N, "3": N}'),
        ("mobile_phone",         '{"1": Y, "0": N, "2": N, "3": N}'),
        ("pc_access",            '{"1": Y, "0": N, "2": N, "3": N}'),
        ("hh_arrears_rent",      '{"1": Y, "0": N, "2": N, "3": N}'),
        ("hh_arrears_utility",   '{"1": Y, "0": N, "2": N, "3": N}'),
        ("hh_afford_vacation",   '{"1": Y, "0": N, "2": N, "3": N}'),
        ("hh_afford_meat_meal",  '{"1": Y, "0": N, "2": N, "3": N}'),
        ("hh_afford_warm_home",  '{"1": Y, "0": N, "2": NA, "3": UNK}'),   # decoy-ready ('2','3' distinct from '0')
        ("hh_material_deprived", '{"1": Y, "0": N, "2": N, "3": N}'),
    ]:
        w(f"  column_{col}:")
        w(f"    name: {col_name}")
        w(f"    values: {values}")
        col += 1

    assert col == 127, f"Expected 127 columns, got {col}"

    out = Path(__file__).parent / "schema.yaml"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out}  ({col} columns budgeted)")


if __name__ == "__main__":
    main()
