#!/usr/bin/env bash
# Runs the full local KOTH scoring PoC (scenarios 1-8).
# Usage: bash poc/run_poc.sh [--serve]
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 poc/simulate.py "$@"
