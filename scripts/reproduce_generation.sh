#!/usr/bin/env bash
# Reproduce all table-generation experiments (nine industry-schema
# scenarios drawn from CDISC SDTM/ADaM, HR Open, and SDMX / Eurostat).
#
# For each experiment, runs `experiments/<NN_name>/run.sh`, captures the
# full log under logs/, and prints a compact success/failure summary at
# the end.  Exits non-zero if any experiment fails.
#
# Runtime: ~1--5 minutes on a modern laptop.
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
echo "  Reproducing table-generation experiments"
echo "  Repository: $REPO"
echo "  Logs:       $LOG_DIR"
echo "  Count:      ${#EXPERIMENTS[@]} experiments"
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
        echo "  OK:      $cmd  ($(command -v "$cmd"))"
    fi
done
if ! python3 -c "import pulp, cvxpy, sympy, numpy, scipy" 2>/dev/null; then
    echo "  MISSING: one of pulp, cvxpy, sympy, numpy, scipy"
    echo "           Install with:  pip install -r requirements.txt"
    missing=1
else
    echo "  OK:      Python deps (pulp, cvxpy, sympy, numpy, scipy)"
fi
if (( missing )); then
    echo
    echo "Dependencies missing — aborting."
    exit 2
fi
echo

# --- Run each experiment --------------------------------------------------
SUCCEEDED=()
FAILED=()

for exp in "${EXPERIMENTS[@]}"; do
    logfile="$LOG_DIR/gen_${exp}.log"
    printf -- "-- [%s] running --\n" "$exp"
    if bash "$REPO/experiments/$exp/run.sh" > "$logfile" 2>&1; then
        # tail the last summary line so the user sees the reconstruction result
        last="$(tail -n 1 "$logfile" | tr -d '\r')"
        printf "   OK  %s\n" "$exp"
        [[ -n "$last" ]] && printf "        %s\n" "$last"
        SUCCEEDED+=("$exp")
    else
        printf "   FAIL %s  (see %s)\n" "$exp" "$logfile"
        echo "      --- last 10 log lines ---"
        tail -n 10 "$logfile" | sed 's/^/      /'
        FAILED+=("$exp")
    fi
    echo
done

# --- Summary --------------------------------------------------------------
echo "================================================================"
echo "  Summary"
echo "================================================================"
echo "  Succeeded (${#SUCCEEDED[@]}):"
for s in "${SUCCEEDED[@]}"; do echo "    OK   $s"; done
echo "  Failed    (${#FAILED[@]}):"
for f in "${FAILED[@]}"; do echo "    FAIL $f"; done
echo
if (( ${#FAILED[@]} > 0 )); then
    echo "One or more experiments failed. Inspect $LOG_DIR/gen_*.log for details."
    exit 1
fi

echo "All ${#SUCCEEDED[@]} generation experiments succeeded."
echo "Outputs are under experiments/<NN_name>/output/. A follow-up"
echo "  git diff experiments/*/output"
echo "shows any drift from the checked-in results."
