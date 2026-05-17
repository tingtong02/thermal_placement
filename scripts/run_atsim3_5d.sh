#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ATSIM3_5D_BIN="${ATSIM3_5D_BIN:-$ROOT_DIR/tools/atsim3d-bin/ATSim3_5D}"

if [[ ! -x "$ATSIM3_5D_BIN" ]]; then
  echo "ATSim3_5D binary not found or not executable: $ATSIM3_5D_BIN" >&2
  exit 1
fi

if [[ -z "${FONTCONFIG_FILE:-}" && -f /etc/fonts/fonts.conf ]]; then
  export FONTCONFIG_FILE=/etc/fonts/fonts.conf
fi

exec "$ATSIM3_5D_BIN" "$@"
