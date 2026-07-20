"""
Emit schema.yaml for the HR Open Standards (n=512) experiment.

Budget: 511 query-columns for n=512:
    23 static HR numerical fields × 3 bits        =  69
    + 4 monthly metrics × 36 months × 3 bits      = 432
    + 10 binary/categorical                        =  10
    = 511
"""
from pathlib import Path

# 36 months (3 fiscal years) — standard "3-year performance horizon" in HRIS
MONTHS = [
    f"y{y}m{m:02d}" for y in (1, 2, 3) for m in range(1, 13)
]
assert len(MONTHS) == 36


def main() -> None:
    lines = []
    w = lines.append

    w("# HR Open Standards (subject-level employee profile with 3 years of")
    w("# monthly KPIs — the 'integrated people-analytics warehouse' flat file) — n=512")
    w("#")
    w("# Schema origin: HR Open Standards / HR-XML. Enterprise HRIS warehouses")
    w("# (Workday, SuccessFactors, BambooHR) and consulting-firm people-analytics")
    w("# teams routinely materialize per-employee flat files with 3 years of")
    w("# monthly KPIs for downstream modeling (attrition, compensation equity,")
    w("# utilization forecasting). 511 released aggregates correspond to a")
    w("# typical BI dashboard's worth of per-cohort metrics.")
    w("#")
    w("# Construction: MIP base=8 with (p, c) = (0.5, 0.25), Hadamard k=7")
    w("# (six Sylvester doublings) → n=512 employees. 511 per-column queries +")
    w("# 1 all-records = 512 queries. Each query aggregates p·n = 256 employees.")
    w("#")
    w("# Sensitive (not released): salary — annual base salary.")
    w("# Derived comp fields (bonus, equity, total_comp, billing_rate) are")
    w("# OMITTED from the released schema — they are functions of salary.")
    w("")
    w("name: hr_open_n512")
    w("n_records: 512")
    w("seed: 42")
    w("")
    w("mip_base: 8")
    w("hadamard_order: 7")
    w("population_value: 0.5")
    w("communality_value: 0.25")
    w("log_level: WARNING")
    w("")
    w("sensitive_column: salary")
    w("")
    w("# 69 + 432 + 10 = 511")
    w("compression_groups:")

    col = 0

    def group(name: str, bits: int, interval: int, note: str) -> None:
        nonlocal col
        cols = ", ".join(f"column_{col + j}" for j in range(bits))
        col += bits
        w(f"  - name: {name}")
        w(f"    columns: [{cols}]")
        w(f"    interval: {interval}   # {note}")

    # --- Static career / demographic / baseline KPIs (23 × 3 bits = 69) ---
    group("age",                    3, 10, "years, 0-80")
    group("tenure_years",           3,  5, "yrs at company, 0-40")
    group("years_experience",       3,  6, "total career yrs, 0-48")
    group("years_in_role",          3,  2, "yrs in current role, 0-16")
    group("years_in_company",       3,  5, "yrs total in company group, 0-40")
    group("direct_reports",         3,  3, "direct reports, 0-24")
    group("indirect_reports_span",  3,  8, "indirect reports, 0-64")
    group("training_hours_y1",      3, 10, "training hrs yr1, 0-80")
    group("training_hours_y2",      3, 10, "training hrs yr2, 0-80")
    group("training_hours_y3",      3, 10, "training hrs yr3, 0-80")
    group("pto_balance_days",       3,  4, "PTO balance days, 0-32")
    group("sick_days_ytd",          3,  2, "sick days YTD, 0-16")
    group("pto_taken_y1",           3,  4, "PTO taken yr1, 0-32")
    group("pto_taken_y2",           3,  4, "PTO taken yr2, 0-32")
    group("pto_taken_y3",           3,  4, "PTO taken yr3, 0-32")
    group("commute_miles",          3,  6, "miles, 0-48")
    group("certifications_count",   3,  2, "certs held, 0-16")
    group("languages_spoken",       3,  1, "languages, 0-8")
    group("projects_count_y1",      3,  3, "projects yr1, 0-24")
    group("projects_count_y2",      3,  3, "projects yr2, 0-24")
    group("projects_count_y3",      3,  3, "projects yr3, 0-24")
    group("publications_count",     3,  2, "publications, 0-16")
    group("patents_count",          3,  1, "patents, 0-8")

    # --- 36 months × 4 KPI metrics (3 bits each = 8 bins) ---
    for m in MONTHS:
        group(f"bill_hrs_{m}", 3, 30, f"billable hrs, {m}, 0-240")
    for m in MONTHS:
        group(f"util_pct_{m}", 3, 15, f"utilization %, {m}, 0-120")
    for m in MONTHS:
        group(f"overtime_{m}", 3, 10, f"OT hrs, {m}, 0-80")
    for m in MONTHS:
        group(f"hours_worked_{m}", 3, 30, f"hrs worked, {m}, 0-240")

    w("")
    w("binary_rename:")
    for col_name, values in [
        ("sex",              '{"1": M, "0": F, "2": F, "3": F}'),
        ("department",       '{"1": CONSULTING, "0": SALES, "2": ENGINEERING, "3": OPERATIONS}'),
        ("employment_type",  '{"1": FULLTIME, "0": PARTTIME, "2": CONTRACTOR, "3": INTERN}'),
        ("education_level",  '{"1": PHD, "0": BS, "2": MS, "3": HS}'),
        ("country",          '{"1": USA, "0": DEU, "2": GBR, "3": IND}'),
        ("remote_flag",      '{"1": Y, "0": N, "2": N, "3": N}'),
        ("union_member",     '{"1": Y, "0": N, "2": N, "3": N}'),
        ("equity_eligible",  '{"1": Y, "0": N, "2": N, "3": N}'),
        ("benefits_tier",    '{"1": PREMIUM, "0": STANDARD, "2": BASIC, "3": COMP}'),   # decoy-ready ('2','3' distinct from '0')
        ("stock_eligible",   '{"1": Y, "0": N, "2": N, "3": N}'),
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
