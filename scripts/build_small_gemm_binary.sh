#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

CONFIG="${CONFIG:-GemminiRocketConfig}"
SRC="$ROOT_DIR/workloads/small_gemm/small_gemm.c"
OUT_DIR="$ROOT_DIR/sim/binaries/$CONFIG"
OUT="$OUT_DIR/small_gemm-baremetal"
COMMON="$GEMMINI_HOME/software/gemmini-rocc-tests/riscv-tests/benchmarks/common"
TEST_ROOT="$GEMMINI_HOME/software/gemmini-rocc-tests"

mkdir -p "$OUT_DIR"

riscv64-unknown-elf-gcc \
  -DPREALLOCATE=1 \
  -DMULTITHREAD=1 \
  -mcmodel=medany \
  -std=gnu99 \
  -O2 \
  -ffast-math \
  -fno-common \
  -fno-builtin-printf \
  -fno-tree-loop-distribute-patterns \
  -march=rv64gc \
  -Wa,-march=rv64gc \
  -I"$TEST_ROOT" \
  -I"$TEST_ROOT/riscv-tests" \
  -I"$TEST_ROOT/riscv-tests/env" \
  -I"$COMMON" \
  -nostdlib \
  -nostartfiles \
  -static \
  -T "$COMMON/test.ld" \
  -DBAREMETAL=1 \
  "$SRC" \
  "$COMMON/syscalls.c" \
  "$COMMON/crt.S" \
  -o "$OUT"

echo "$OUT"
