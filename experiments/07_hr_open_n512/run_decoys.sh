#!/usr/bin/env bash
# Re-run this experiment with 10% reconstructable records + 90% decoys.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -s "$HERE/schema.yaml" ]] || python3 "$HERE/generate_schema.py"
python3 "$HERE/../common/driver.py" --schema "$HERE/schema.yaml" --out "$HERE/output_decoys" --decoy-fraction 0.1
