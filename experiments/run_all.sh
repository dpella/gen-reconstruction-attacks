#!/usr/bin/env bash
# Reproduce all CDISC-schema experiments from scratch.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SUMMARY=()
for exp in 01_sdtm_vs 02_adam_adsl 03_adam_adlb 04_adam_adpc 05_adam_adpc_extended 06_hr_open_n256 07_hr_open_n512 08_eurostat_silc_n128 09_eurostat_silc_n512; do
    echo
    echo "=== $exp ==="
    bash "$HERE/$exp/run.sh"
    SUMMARY+=("$exp: $(tail -n1 "$HERE/$exp/output/reconstruction.txt")")
done

echo
echo "=== All experiments complete ==="
for line in "${SUMMARY[@]}"; do
    echo "  $line"
done
