#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/../common/driver.py" --schema "$HERE/schema.yaml" --out "$HERE/output"
