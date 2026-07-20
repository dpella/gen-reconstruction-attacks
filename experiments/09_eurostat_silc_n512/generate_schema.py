"""
Emit schema.yaml for the Eurostat EU-SILC integrated with HBS (n=512).

Budget: 511 query-columns for n=512:
    20 static EU-SILC numerical fields × 3 bits         =  60
    + 4 panel-years × 12 metrics × 3 bits               = 144
    + 12 months × 8 HBS COICOP categories × 3 bits      = 288
    + 19 binary/categorical                              =  19
    = 511
"""
from pathlib import Path

YEARS = ["y1", "y2", "y3", "y4"]                     # EU-SILC 4-year panel
MONTHS = [f"m{m:02d}" for m in range(1, 13)]         # HBS: 12 months of diary
COICOP = [
    "food",            # CP01 food and non-alcoholic beverages
    "housing_utils",   # CP04 housing, water, electricity, gas
    "transport",       # CP07 transport
    "communication",   # CP08 communication
    "recreation",      # CP09 recreation and culture
    "education",       # CP10 education
    "health",          # CP06 health
    "restaurants",     # CP11 restaurants and hotels
]  # 8 COICOP-1 aggregates


def main() -> None:
    lines = []
    w = lines.append

    w("# Eurostat EU-SILC × HBS (Household Budget Survey) integrated flat file — n=512")
    w("#")
    w("# Schema origin: EU-SILC (Income & Living Conditions) and HBS (Household")
    w("# Budget Survey) are both SDMX-compliant Eurostat microdata surveys.")
    w("# NSIs routinely materialise an INTEGRATED per-household flat file for")
    w("# poverty-and-living-standards modelling — pairing EU-SILC's annual")
    w("# income/labour/health variables with HBS's 12-month expenditure diary")
    w("# across the COICOP classification. The integrated file is a standard")
    w("# analytical warehouse output.")
    w("#")
    w("# Construction: MIP base=8 with (p, c) = (0.5, 0.25), Hadamard k=7")
    w("# (six Sylvester doublings) → n=512 households. 511 per-column queries")
    w("# + 1 all-records = 512 queries. Each query aggregates p·n = 256")
    w("# households.")
    w("#")
    w("# Sensitive (not released): total_disposable_income — equivalised")
    w("# household disposable income (HY020 / HX090 in the EU-SILC DSD).")
    w("#")
    w("# All income subcomponents are OMITTED from the released schema.")
    w("# Note: monthly expenditure is released as a range predicate — this")
    w("# does NOT leak income because expenditure partially tracks income")
    w("# but is not a deterministic function of it (households differ in")
    w("# savings rate, debt, etc.).")
    w("")
    w("name: eurostat_silc_n512")
    w("n_records: 512")
    w("seed: 42")
    w("")
    w("mip_base: 8")
    w("hadamard_order: 7")
    w("population_value: 0.5")
    w("communality_value: 0.25")
    w("log_level: WARNING")
    w("")
    w("sensitive_column: total_disposable_income")
    w("")
    w("# 60 + 144 + 288 + 19 = 511")
    w("compression_groups:")

    col = 0

    def group(name: str, bits: int, interval: int, note: str) -> None:
        nonlocal col
        cols = ", ".join(f"column_{col + j}" for j in range(bits))
        col += bits
        w(f"  - name: {name}")
        w(f"    columns: [{cols}]")
        w(f"    interval: {interval}   # {note}")

    # --- Static cross-sectional (20 × 3 bits = 60) ---
    group("age",                    3, 10, "years, 0-80")
    group("hh_size",                3,  1, "HH size, 0-8")
    group("hh_children",            3,  1, "children in HH, 0-8")
    group("hh_rooms",               3,  1, "rooms, 0-8")
    group("floor_area",             3, 20, "m², 0-160")
    group("years_education",        3,  3, "years educ, 0-24")
    group("dwelling_age",           3, 10, "dwelling yrs, 0-80")
    group("distance_to_work_km",    3, 10, "km, 0-80")
    group("commute_minutes",        3, 15, "min, 0-120")
    group("num_cars",               3,  1, "cars, 0-8")
    group("hh_employed_count",      3,  1, "employed in HH, 0-8")
    group("hh_unemployed_count",    3,  1, "unemployed in HH, 0-8")
    group("years_in_current_home",  3,  5, "yrs, 0-40")
    group("chronic_conditions",     3,  1, "count, 0-8")
    group("internet_hours_daily",   3,  2, "hrs, 0-16")
    group("children_under_16",      3,  1, "count, 0-8")
    group("adults_over_65",         3,  1, "count, 0-8")
    group("pets_count",             3,  1, "pets, 0-8")
    group("bedrooms",               3,  1, "bedrooms, 0-8")
    group("bathrooms",              3,  1, "bathrooms, 0-8")

    # --- 4-year panel × 12 metrics × 3 bits = 144 ---
    for y in YEARS:
        group(f"housing_cost_{y}",     3, 250, f"€/mo housing cost, {y}")
    for y in YEARS:
        group(f"hours_worked_{y}",     3,  8, f"hrs/wk avg, {y}")
    for y in YEARS:
        group(f"heating_cost_{y}",     3, 40, f"€/mo heating, {y}")
    for y in YEARS:
        group(f"medical_oop_{y}",      3, 100, f"€/yr OOP medical, {y}")
    for y in YEARS:
        group(f"months_employed_{y}",  3,  2, f"months employed, {y}")
    for y in YEARS:
        group(f"months_unemployed_{y}",3,  2, f"months unemp, {y}")
    for y in YEARS:
        group(f"months_sick_{y}",      3,  2, f"months sick, {y}")
    for y in YEARS:
        group(f"savings_deposit_{y}",  3, 200, f"€/yr savings, {y}")
    for y in YEARS:
        group(f"doctor_visits_{y}",    3,  5, f"GP visits, {y}")
    for y in YEARS:
        group(f"training_hours_{y}",   3, 10, f"training hrs/yr, {y}")
    for y in YEARS:
        group(f"child_care_cost_{y}",  3, 100, f"€/mo childcare, {y}")
    for y in YEARS:
        group(f"commute_cost_{y}",     3, 50, f"€/mo commuting, {y}")

    # --- HBS monthly expenditure: 12 months × 8 COICOP × 3 bits = 288 ---
    for cat in COICOP:
        for m in MONTHS:
            group(f"exp_{cat}_{m}", 3, 100, f"€ monthly expenditure on {cat}, {m}")

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

    assert col == 511, f"Expected 511 columns, got {col}"

    out = Path(__file__).parent / "schema.yaml"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out}  ({col} columns budgeted)")


if __name__ == "__main__":
    main()
