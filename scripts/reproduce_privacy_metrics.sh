#!/usr/bin/env bash
# Reproduce the §6.3 privacy-metrics evaluation.
#
# For each of the nine schemas:
#   1. Regenerate the decoy-augmented dataset (10% reconstructable core
#      + 90% decoys) so that the privacy metrics have inputs to score.
#   2. Run Anonymeter's InferenceEvaluator.
#   3. Run synthcity's DataLeakageXGB and IdentifiabilityScore.
#   4. Run a Privacy-Meter-style Random-Forest attribute-inference
#      attack.
#
# Every dataset's aggregate release is algebraically reconstructable by
# our tool, yet all three privacy metrics should report near-zero risk
# — that is the point of §6.3.
#
# Runtime: substantial. synthcity+XGBoost fit models per experiment;
# expect on the order of an hour on a laptop for all nine schemas.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"

EXPERIMENTS=(
    01_sdtm_vs
    02_adam_adsl
    03_adam_adlb
    04_adam_adpc
    05_adam_adpc_extended
    06_hr_open_n256
    07_hr_open_n512
    08_eurostat_silc_n128
    09_eurostat_silc_n512
)

echo "================================================================"
echo "  Reproducing privacy-metrics experiments"
echo "  Repository: $REPO"
echo "  Logs:       $LOG_DIR"
echo "  Count:      ${#EXPERIMENTS[@]} experiments x 3 metric families"
echo "================================================================"
echo

# --- Dependency check -----------------------------------------------------
echo "-- Checking dependencies --"
missing=0
for cmd in python3 glpsol; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "  MISSING: $cmd"
        missing=1
    else
        echo "  OK:      $cmd"
    fi
done
if ! python3 -c "import pulp, cvxpy, sympy" 2>/dev/null; then
    echo "  MISSING: tool deps (pulp / cvxpy / sympy)"
    echo "           Install with:  pip install -r requirements.txt"
    missing=1
else
    echo "  OK:      tool deps"
fi
if ! python3 -c "import anonymeter, synthcity, sklearn, pandas" 2>/dev/null; then
    echo "  MISSING: evaluation deps (anonymeter / synthcity / sklearn / pandas)"
    echo "           These are kept out of the base Docker image because"
    echo "           they pull in PyTorch and XGBoost. Install once with:"
    echo
    echo "               bash scripts/install_eval_deps.sh"
    echo
    missing=1
else
    echo "  OK:      evaluation deps (anonymeter, synthcity, sklearn, pandas)"
fi
if (( missing )); then
    echo
    echo "Dependencies missing — aborting."
    exit 2
fi
echo

# --- Stage runner ---------------------------------------------------------
SUCCEEDED=()
FAILED=()

run_stage () {
    local label="$1"; shift
    local logfile="$LOG_DIR/pm_${label//[^a-zA-Z0-9_]/_}.log"
    printf -- "-- [%s] running --\n" "$label"
    if "$@" > "$logfile" 2>&1; then
        printf "   OK  %s   (log: %s)\n" "$label" "$logfile"
        SUCCEEDED+=("$label")
    else
        printf "   FAIL %s   (log: %s)\n" "$label" "$logfile"
        echo "      --- last 10 log lines ---"
        tail -n 10 "$logfile" | sed 's/^/      /'
        FAILED+=("$label")
    fi
    echo
}

# --- Stage 1: decoy-augmented datasets ------------------------------------
echo "================================================================"
echo "  Stage 1/3: decoy-augmented dataset generation"
echo "================================================================"
for exp in "${EXPERIMENTS[@]}"; do
    run_stage "decoys/$exp" bash "$REPO/experiments/$exp/run_decoys.sh"
done

# --- Stage 2: Anonymeter --------------------------------------------------
echo "================================================================"
echo "  Stage 2/3: Anonymeter InferenceEvaluator"
echo "================================================================"
for exp in "${EXPERIMENTS[@]}"; do
    run_stage "anonymeter/$exp" python3 \
        "$REPO/experiments/common/anonymeter_eval.py" \
        --schema "$REPO/experiments/$exp/schema.yaml" \
        --out    "$REPO/experiments/$exp/output_decoys" \
        --decoy-fraction 0.1
done
run_stage "anonymeter/summary" python3 \
    "$REPO/experiments/common/anonymeter_summary.py" \
    --exp-dir "$REPO/experiments"

# --- Stage 3: synthcity + Privacy Meter -----------------------------------
echo "================================================================"
echo "  Stage 3/3: synthcity + Privacy Meter"
echo "================================================================"
for exp in "${EXPERIMENTS[@]}"; do
    run_stage "synthcity/$exp" python3 \
        "$REPO/experiments/common/synthcity_eval.py" \
        --schema "$REPO/experiments/$exp/schema.yaml" \
        --out    "$REPO/experiments/$exp/output_decoys" \
        --decoy-fraction 0.1
    run_stage "privacy_meter/$exp" python3 \
        "$REPO/experiments/common/privacy_meter_eval.py" \
        --schema "$REPO/experiments/$exp/schema.yaml" \
        --out    "$REPO/experiments/$exp/output_decoys" \
        --decoy-fraction 0.1
done
run_stage "privacy_metrics/summary" python3 \
    "$REPO/experiments/common/privacy_metrics_summary.py" \
    --exp-dir "$REPO/experiments"

# --- Summary --------------------------------------------------------------
echo "================================================================"
echo "  Summary"
echo "================================================================"
echo "  Succeeded (${#SUCCEEDED[@]} stages):"
for s in "${SUCCEEDED[@]}"; do echo "    OK   $s"; done
echo "  Failed    (${#FAILED[@]} stages):"
for f in "${FAILED[@]}"; do echo "    FAIL $f"; done
echo

if (( ${#FAILED[@]} > 0 )); then
    echo "One or more stages failed. Inspect $LOG_DIR/pm_*.log for details."
    exit 1
fi

echo "All privacy-metrics stages succeeded."
echo "Aggregate results:"
echo "  experiments/anonymeter_results.md"
echo "  experiments/privacy_metrics_results.md"
echo
echo "A follow-up  git diff experiments/*/output_decoys experiments/*.md"
echo "shows any drift from the checked-in results."
