#!/usr/bin/env bash
# Launch Patchwork from anywhere: ./patchwork.sh [options]
HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m patchwork "$@"
