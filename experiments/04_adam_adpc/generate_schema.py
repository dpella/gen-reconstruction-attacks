"""
Emit schema.yaml for the ADPC (n=128) experiment.

Budget: 127 query-columns for n=128:
    39 PK concentration columns × 3 bits = 117
    + age (3) + heightbl (2) + weightbl (2) + 3 binary = 10
    = 127
"""
from pathlib import Path

PERIOD_1_TPS = ["0h", "0_25h", "0_5h", "1h", "1_5h", "2h", "3h", "4h", "6h", "8h",
                "12h", "16h", "36h", "48h", "72h", "96h", "120h", "144h", "168h"]  # 19 (24h excluded — sensitive)
PERIOD_2_TPS = ["0h", "0_25h", "0_5h", "1h", "1_5h", "2h", "3h", "4h", "6h", "8h",
                "12h", "16h", "24h", "36h", "48h", "72h", "96h", "120h", "144h", "168h"]  # 20

def main() -> None:
    lines = []
    w = lines.append

    w("# ADaM ADPC (Pharmacokinetic Concentrations) — n=128")
    w("#")
    w("# Schema origin: CDISC ADaM Pharmacokinetic Concentrations dataset.")
    w("# Pivoted so each subject has one row, and each column is the PK")
    w("# concentration at one nominal timepoint in one study period")
    w("# (two-period crossover: single-dose [p1] + steady-state [p2]).")
    w("#")
    w("# Construction: MIP base=8 with (p, c) = (0.5, 0.25), Hadamard k=5")
    w("# (four Sylvester doublings) → n=128 subjects. 127 per-column queries +")
    w("# 1 all-records = 128 queries. Each query aggregates p·n = 64 subjects.")
    w("#")
    w("# Sensitive (not released): conc_24h — the 24-hour post-dose")
    w("# concentration in period 1 (trough surrogate / CYP-phenotype proxy).")
    w("")
    w("name: adam_adpc")
    w("n_records: 128")
    w("seed: 42")
    w("")
    w("mip_base: 8")
    w("hadamard_order: 5")
    w("population_value: 0.5")
    w("communality_value: 0.25")
    w("log_level: WARNING")
    w("")
    w("sensitive_column: conc_24h")
    w("")
    w("# 39 concentration columns × 3 bits + demographics + 3 binary = 127")
    w("compression_groups:")

    col = 0

    def group(name: str, bits: int, interval: int, note: str) -> None:
        nonlocal col
        cols = ", ".join(f"column_{col + j}" for j in range(bits))
        col += bits
        w(f"  - name: {name}")
        w(f"    columns: [{cols}]")
        w(f"    interval: {interval}   # {note}")

    # Period 1 concentrations (single-dose), excluding 24h (sensitive)
    for tp in PERIOD_1_TPS:
        group(f"c1_{tp}", 3, 50, f"ng/mL, period 1 t={tp.replace('_', '.')}")

    # Period 2 concentrations (steady-state)
    for tp in PERIOD_2_TPS:
        group(f"c2_{tp}", 3, 50, f"ng/mL, period 2 t={tp.replace('_', '.')}")

    # Demographics (compressed)
    group("age", 3, 10, "years, 8 bins × 10 = 0-80")
    group("heightbl", 2, 40, "cm, 4 bins × 40 = 0-160")
    group("weightbl", 2, 40, "kg, 4 bins × 40 = 0-160")

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

    assert col == 127, f"Expected 127 columns, got {col}"

    out = Path(__file__).parent / "schema.yaml"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out}  ({col} columns budgeted)")


if __name__ == "__main__":
    main()
