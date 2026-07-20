"""
Emit schema.yaml for the ADPC-extended (n=256) experiment.

Budget: 255 query-columns for n=256:
    79 PK concentration columns × 3 bits                       = 237
    + age (3) + heightbl (2) + weightbl (2) + bmibl (2)        =  9
    + base_creat (2) + base_alt (2) + base_bili (2)            =  6
    + 3 binary (sex, race, country)                            =  3
    = 255
"""
from pathlib import Path

# 20 nominal PK timepoints (hours). 24 h in period 1 for the parent drug is
# the sensitive column, so that one slot is *excluded* from the released set.
ALL_TPS = ["0h", "0_25h", "0_5h", "1h", "1_5h", "2h", "3h", "4h", "6h", "8h",
           "12h", "16h", "24h", "36h", "48h", "72h", "96h", "120h", "144h", "168h"]

P1_PARENT_TPS = [t for t in ALL_TPS if t != "24h"]  # 19 (24h is sensitive)
P2_PARENT_TPS = ALL_TPS                              # 20
P1_METAB_TPS  = ALL_TPS                              # 20
P2_METAB_TPS  = ALL_TPS                              # 20


def main() -> None:
    lines = []
    w = lines.append

    w("# ADaM ADPC (extended: parent + metabolite, two-period crossover) — n=256")
    w("#")
    w("# Schema origin: CDISC ADaM Pharmacokinetic Concentrations dataset in its")
    w("# standard bioequivalence/bioavailability configuration: one row per subject,")
    w("# columns = PK concentrations of (parent drug + principal metabolite) at")
    w("# 20 nominal timepoints across two study periods (single-dose and")
    w("# steady-state). This is a routine FDA/EMA submission layout.")
    w("#")
    w("# Construction: MIP base=8 with (p, c) = (0.5, 0.25), Hadamard k=6")
    w("# (five Sylvester doublings) → n=256 subjects. 255 per-column queries +")
    w("# 1 all-records = 256 queries. Each query aggregates p·n = 128 subjects.")
    w("#")
    w("# Sensitive (not released): conc_24h — 24-hour post-dose PARENT-drug")
    w("# concentration in period 1. Clinically sensitive trough / CYP-phenotype")
    w("# proxy; not derivable from metabolite concentrations without the")
    w("# subject's (unknown) metabolic ratio.")
    w("")
    w("name: adam_adpc_extended")
    w("n_records: 256")
    w("seed: 42")
    w("")
    w("mip_base: 8")
    w("hadamard_order: 6")
    w("population_value: 0.5")
    w("communality_value: 0.25")
    w("log_level: WARNING")
    w("")
    w("sensitive_column: conc_24h")
    w("")
    w("# 79 × 3 + 15 + 3 = 255")
    w("compression_groups:")

    col = 0

    def group(name: str, bits: int, interval: int, note: str) -> None:
        nonlocal col
        cols = ", ".join(f"column_{col + j}" for j in range(bits))
        col += bits
        w(f"  - name: {name}")
        w(f"    columns: [{cols}]")
        w(f"    interval: {interval}   # {note}")

    # Parent drug — period 1 (single-dose), 24h excluded (sensitive)
    for tp in P1_PARENT_TPS:
        group(f"pc1_{tp}", 3, 50, f"parent, ng/mL, p1 t={tp.replace('_', '.')}")
    # Parent drug — period 2 (steady-state)
    for tp in P2_PARENT_TPS:
        group(f"pc2_{tp}", 3, 50, f"parent, ng/mL, p2 t={tp.replace('_', '.')}")
    # Metabolite M1 — period 1
    for tp in P1_METAB_TPS:
        group(f"mc1_{tp}", 3, 25, f"metab, ng/mL, p1 t={tp.replace('_', '.')}")
    # Metabolite M1 — period 2
    for tp in P2_METAB_TPS:
        group(f"mc2_{tp}", 3, 25, f"metab, ng/mL, p2 t={tp.replace('_', '.')}")

    # Demographics + baseline renal/hepatic covariates (compressed)
    group("age",        3, 10, "years, 0-80")
    group("heightbl",   2, 40, "cm,    0-160")
    group("weightbl",   2, 40, "kg,    0-160")
    group("bmibl",      2, 10, "kg/m², 0-40")
    group("base_creat", 2,  1, "creatinine mg/dL, 0-4")
    group("base_alt",   2, 20, "ALT U/L, 0-80")
    group("base_bili",  2,  1, "total bilirubin mg/dL, 0-4")

    w("")
    w("binary_rename:")
    w(f"  column_{col}:")
    w(f'    name: sex')
    w(f'    values: {{"1": M, "0": F, "2": F, "3": F}}')
    col += 1
    w(f"  column_{col}:")
    w(f'    name: race')
    w(f'    values: {{"1": WHITE, "0": BLACK, "2": ASIAN, "3": OTHER}}')
    col += 1
    w(f"  column_{col}:")
    w(f'    name: country')
    w(f'    values: {{"1": USA, "0": DEU, "2": FRA, "3": GBR}}')
    col += 1

    assert col == 255, f"Expected 255 columns, got {col}"

    out = Path(__file__).parent / "schema.yaml"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out}  ({col} columns budgeted)")


if __name__ == "__main__":
    main()
