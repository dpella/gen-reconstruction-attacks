#!/usr/bin/env bash
# Reproduce every schema's decoy-augmented experiment (10% reconstructable).
# Outputs land in each experiment's output_decoys/ (original output/ untouched).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SUMMARY=()
for exp in 01_sdtm_vs 02_adam_adsl 03_adam_adlb 04_adam_adpc 05_adam_adpc_extended 06_hr_open_n256 07_hr_open_n512 08_eurostat_silc_n128 09_eurostat_silc_n512; do
    echo
    echo "=== $exp (decoys) ==="
    bash "$HERE/$exp/run_decoys.sh"
    SUMMARY+=("$exp: $(tail -n1 "$HERE/$exp/output_decoys/reconstruction.txt")")
done

echo
echo "=== All decoy experiments complete ==="
for line in "${SUMMARY[@]}"; do
    echo "  $line"
done
