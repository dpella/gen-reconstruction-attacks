#!/usr/bin/env bash
# Run Anonymeter's InferenceEvaluator on every decoy-augmented dataset
# (10% reconstructable core + 90% decoys) and show that the privacy risk
# score is statistically indistinguishable from zero, even though the
# sensitive column is algebraically reconstructable from the released
# aggregates.
#
# Outputs `anonymeter.{json,txt}` per experiment inside `output_decoys/`
# and a top-level `anonymeter_results.md` table.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

EXPERIMENTS=(
    01_sdtm_vs 02_adam_adsl 03_adam_adlb
    04_adam_adpc 05_adam_adpc_extended
    06_hr_open_n256 07_hr_open_n512
    08_eurostat_silc_n128 09_eurostat_silc_n512
)

for exp in "${EXPERIMENTS[@]}"; do
    echo
    echo "=== $exp (Anonymeter) ==="
    python3 "$HERE/common/anonymeter_eval.py" \
        --schema "$HERE/$exp/schema.yaml" \
        --out    "$HERE/$exp/output_decoys" \
        --decoy-fraction 0.1
done

python3 "$HERE/common/anonymeter_summary.py" --exp-dir "$HERE"
echo
echo "Done. See $HERE/anonymeter_results.md for the summary table."
