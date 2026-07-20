"""
Emit schema.yaml for the HR Open Standards (n=256) experiment.

Budget: 255 query-columns for n=256:
    18 static HR numerical fields × 3 bits       =  54
    + 2 monthly metrics × 24 months × 4 bits     = 192
    + 9 binary/categorical                        =   9
    = 255
"""
from pathlib import Path

MONTHS = [
    "y1m01", "y1m02", "y1m03", "y1m04", "y1m05", "y1m06",
    "y1m07", "y1m08", "y1m09", "y1m10", "y1m11", "y1m12",
    "y2m01", "y2m02", "y2m03", "y2m04", "y2m05", "y2m06",
    "y2m07", "y2m08", "y2m09", "y2m10", "y2m11", "y2m12",
]


def main() -> None:
    lines = []
    w = lines.append

    w("# HR Open Standards (subject-level employee profile with 2 years of")
    w("# monthly metrics) — n=256")
    w("#")
    w("# Schema origin: HR Open Standards / HR-XML — the schema family used by")
    w("# enterprise HRIS (Workday, SuccessFactors, BambooHR) and consulting")
    w("# firms' people-analytics teams. One row per employee, columns = static")
    w("# career & demographic fields + 24 months of per-employee KPIs.")
    w("#")
    w("# Construction: MIP base=8 with (p, c) = (0.5, 0.25), Hadamard k=6")
    w("# (five Sylvester doublings) → n=256 employees. 255 per-column queries +")
    w("# 1 all-records = 256 queries. Each query aggregates p·n = 128 employees.")
    w("#")
    w("# Sensitive (not released): salary — annual base salary.")
    w("# This mirrors the paper's motivating scenario: a consulting firm")
    w("# publishes aggregate analytics over demographics, tenure, performance,")
    w("# and monthly billable-hours / utilization, while withholding per-")
    w("# employee salary — yet the release uniquely determines it.")
    w("#")
    w("# Derived compensation fields (bonus, equity, total_comp, billing_rate)")
    w("# are OMITTED from the released schema: they are functions of salary")
    w("# and would leak trivially.")
    w("")
    w("name: hr_open_n256")
    w("n_records: 256")
    w("seed: 42")
    w("")
    w("mip_base: 8")
    w("hadamard_order: 6")
    w("population_value: 0.5")
    w("communality_value: 0.25")
    w("log_level: WARNING")
    w("")
    w("sensitive_column: salary")
    w("")
    w("# 54 + 192 + 9 = 255")
    w("compression_groups:")

    col = 0

    def group(name: str, bits: int, interval: int, note: str) -> None:
        nonlocal col
        cols = ", ".join(f"column_{col + j}" for j in range(bits))
        col += bits
        w(f"  - name: {name}")
        w(f"    columns: [{cols}]")
        w(f"    interval: {interval}   # {note}")

    # --- Static career / demographic numerical fields (18 × 3 bits = 54) ---
    group("age",                  3, 10, "years, 0-80")
    group("tenure_years",         3,  5, "yrs at company, 0-40")
    group("years_experience",     3,  6, "total career yrs, 0-48")
    group("years_in_role",        3,  2, "yrs in current role, 0-16")
    group("direct_reports",       3,  3, "direct reports, 0-24")
    group("training_hours_ytd",   3, 10, "training hrs YTD, 0-80")
    group("pto_balance_days",     3,  4, "PTO balance days, 0-32")
    group("sick_days_ytd",        3,  2, "sick days YTD, 0-16")
    group("overtime_hours_ytd",   3, 30, "OT hrs YTD, 0-240")
    group("utilization_pct_ytd",  3, 15, "utilization %, 0-120")
    group("commute_miles",        3,  6, "miles, 0-48")
    group("certifications_count", 3,  2, "certs held, 0-16")
    group("languages_spoken",     3,  1, "languages, 0-8")
    group("projects_count_ytd",   3,  3, "projects YTD, 0-24")
    group("publications_count",   3,  2, "publications, 0-16")
    group("patents_count",        3,  1, "patents, 0-8")
    group("engagement_score",     3,  2, "engagement survey 0-16")
    group("customer_sat_score",   3,  2, "CSAT 0-16")

    # --- 24 months of 2 KPI metrics (4 bits each = 16 bins) ---
    for m in MONTHS:
        group(f"bill_hrs_{m}", 4, 15, f"billable hrs in {m}, 0-240")
    for m in MONTHS:
        group(f"util_pct_{m}", 4, 8, f"utilization % in {m}, 0-128")

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
        ("equity_eligible",  '{"1": Y, "0": N, "2": NA, "3": UNK}'),   # decoy-ready ('2','3' distinct from '0')
        ("benefits_tier",    '{"1": PREMIUM, "0": STANDARD, "2": STANDARD, "3": BASIC}'),
    ]:
        w(f"  column_{col}:")
        w(f"    name: {col_name}")
        w(f"    values: {values}")
        col += 1

    assert col == 255, f"Expected 255 columns, got {col}"

    out = Path(__file__).parent / "schema.yaml"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out}  ({col} columns budgeted)")


if __name__ == "__main__":
    main()
