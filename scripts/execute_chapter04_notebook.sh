#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PYTHONUSERBASE="$ROOT_DIR/.python-user"
export MPLCONFIGDIR="$ROOT_DIR/.matplotlib"
export IPYTHONDIR="$ROOT_DIR/.ipython"
export JUPYTER_CONFIG_DIR="$ROOT_DIR/.jupyter"
export JUPYTER_DATA_DIR="$ROOT_DIR/.jupyter-data"
export JUPYTER_RUNTIME_DIR="$ROOT_DIR/.jupyter-runtime"

cd "$ROOT_DIR"
python3 -m nbconvert \
  --to notebook \
  --execute \
  --inplace \
  notebooks/chapter-04/traffic_accident_panel_analysis.ipynb
