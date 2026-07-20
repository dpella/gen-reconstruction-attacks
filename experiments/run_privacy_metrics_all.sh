#!/usr/bin/env bash
# Run all three privacy metric frameworks on the nine decoy-augmented
# datasets: Anonymeter (already in run_anonymeter_all.sh), synthcity, and
# Privacy Meter style RF attribute inference.
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
    echo "=== $exp (synthcity) ==="
    python3 "$HERE/common/synthcity_eval.py" \
        --schema "$HERE/$exp/schema.yaml" \
        --out    "$HERE/$exp/output_decoys" \
        --decoy-fraction 0.1

    echo
    echo "=== $exp (Privacy Meter) ==="
    python3 "$HERE/common/privacy_meter_eval.py" \
        --schema "$HERE/$exp/schema.yaml" \
        --out    "$HERE/$exp/output_decoys" \
        --decoy-fraction 0.1
done

python3 "$HERE/common/privacy_metrics_summary.py" --exp-dir "$HERE"
echo
echo "Done. See $HERE/privacy_metrics_results.md for the summary table."
