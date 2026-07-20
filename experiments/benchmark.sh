#!/usr/bin/env bash
# Sweep MIP base ∈ {4, 8, 16} × target n ∈ {16, …, 512} across all schemas,
# with repeated measurements and per-phase timing.
#
# Default: 5 repetitions per (schema, base) + 1 warmup run (discarded).
# Override via env var REPEATS:
#     REPEATS=10 bash experiments/benchmark.sh
#
# Produces:
#     experiments/benchmark_results_raw.csv   per-run samples
#     experiments/benchmark_results.csv       mean / stdev / 95 % CI per config
#     experiments/benchmark_results.md        paper-ready markdown table
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPEATS="${REPEATS:-5}"
python3 "$HERE/common/benchmark.py" --out-dir "$HERE" --repeats "$REPEATS"
