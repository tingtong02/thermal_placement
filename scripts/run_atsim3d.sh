#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CALLER_DIR=$(pwd)
ATSIM3D_ROOT="${ATSIM3D_ROOT:-$ROOT_DIR/third_party/ATSim3D_pub}"
ATSIM3D_PYTHON="${ATSIM3D_PYTHON:-$ROOT_DIR/tools/atsim3d-py38/bin/python}"

if [[ ! -x "$ATSIM3D_PYTHON" ]]; then
  echo "ATSim3D Python runtime not found or not executable: $ATSIM3D_PYTHON" >&2
  exit 1
fi

if [[ ! -f "$ATSIM3D_ROOT/src/ATSim3D.py" ]]; then
  echo "ATSim3D entry not found: $ATSIM3D_ROOT/src/ATSim3D.py" >&2
  exit 1
fi

abs_path() {
  local path="$1"
  if [[ "$path" = /* ]]; then
    printf '%s\n' "$path"
  else
    printf '%s/%s\n' "$CALLER_DIR" "$path"
  fi
}

args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lcfFile|--ConfigFile|--SimParamsFile)
      if [[ $# -lt 2 ]]; then
        echo "missing value for $1" >&2
        exit 1
      fi
      args+=("$1" "$(abs_path "$2")")
      shift 2
      ;;
    --lcfFile=*|--ConfigFile=*|--SimParamsFile=*)
      key="${1%%=*}"
      value="${1#*=}"
      args+=("$key=$(abs_path "$value")")
      shift
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

cd "$ATSIM3D_ROOT/src"
exec "$ATSIM3D_PYTHON" ATSim3D.py "${args[@]}"
