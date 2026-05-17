#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export FLOW_VARIANT="${FLOW_VARIANT:-noaddermap}"
export ADDER_MAP_FILE=

exec "$SCRIPT_DIR/run_stage2_openroad.sh" "$@"
