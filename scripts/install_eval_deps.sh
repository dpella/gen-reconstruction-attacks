#!/usr/bin/env bash
# Install (or upgrade) the privacy-metrics evaluation dependencies —
# anonymeter, synthcity, PyTorch, XGBoost, scikit-learn, pandas.
#
# Kept out of the base Dockerfile because synthcity pulls in PyTorch +
# XGBoost and takes 5–15 minutes to install, which was making the
# devcontainer build fragile.
#
# Run this once, and re-run any time you 'git pull' changes that touch
# requirements-eval.txt:
#     bash scripts/install_eval_deps.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

echo "================================================================"
echo "  Installing / upgrading privacy-metrics evaluation dependencies"
echo "  (anonymeter, synthcity, torch>=2.4, opacus<1.5, sklearn, pandas)"
echo "  This will pull in PyTorch and XGBoost — expect 5–15 minutes."
echo "================================================================"
echo

# --upgrade so already-installed packages get bumped when
# requirements-eval.txt tightens a pin (e.g. torch<2.4 → torch>=2.4).
pip install --no-cache-dir --upgrade -r "$REPO/requirements-eval.txt"

echo
echo "-- Installed versions --"
python3 - <<'PY'
def _v(m):
    try:
        mod = __import__(m)
        return getattr(mod, "__version__", "ok")
    except Exception as e:
        return f"IMPORT FAILED: {e.__class__.__name__}: {e}"

for m in ("torch", "opacus", "anonymeter", "synthcity", "sklearn", "pandas"):
    print(f"  {m:<12} {_v(m)}")
PY

echo
echo "Done. You can now run:  bash scripts/reproduce_privacy_metrics.sh"
