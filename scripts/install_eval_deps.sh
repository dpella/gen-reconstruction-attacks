#!/usr/bin/env bash
# Install the privacy-metrics evaluation dependencies (anonymeter,
# synthcity, scikit-learn, pandas). Kept out of the base Dockerfile
# because synthcity pulls in PyTorch + XGBoost and takes 5-15 minutes
# to install on a fresh image, which makes the devcontainer build
# fragile.
#
# Run this once inside the devcontainer terminal:
#     bash scripts/install_eval_deps.sh
#
# Afterwards, scripts/reproduce_privacy_metrics.sh can run.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

echo "================================================================"
echo "  Installing privacy-metrics evaluation dependencies"
echo "  (anonymeter, synthcity, scikit-learn, pandas)"
echo "  This will pull in PyTorch and XGBoost — expect 5-15 minutes."
echo "================================================================"
echo

pip install --no-cache-dir -r "$REPO/requirements-eval.txt"

echo
echo "-- Verifying imports --"
python3 -c "import anonymeter; print('anonymeter', anonymeter.__version__ if hasattr(anonymeter, '__version__') else 'ok')"
python3 -c "import synthcity;  print('synthcity',  synthcity.__version__  if hasattr(synthcity,  '__version__') else 'ok')"
python3 -c "import sklearn;    print('sklearn',    sklearn.__version__)"
python3 -c "import pandas;     print('pandas',     pandas.__version__)"

echo
echo "Done. You can now run:  bash scripts/reproduce_privacy_metrics.sh"
