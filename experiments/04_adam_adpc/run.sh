#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Regenerate schema.yaml (reproducibility); skip if user edited by hand.
[[ -s "$HERE/schema.yaml" ]] || python3 "$HERE/generate_schema.py"
python3 "$HERE/../common/driver.py" --schema "$HERE/schema.yaml" --out "$HERE/output"
