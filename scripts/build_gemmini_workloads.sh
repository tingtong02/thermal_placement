#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

CONFIG="${CONFIG:-GemminiRocketConfig}"
MAKE_JOBS="${MAKE_JOBS:-$(nproc)}"
TEST_ROOT="$GEMMINI_HOME/software/gemmini-rocc-tests"
BUILD_ROOT="$TEST_ROOT/build/bareMetalC"
INSTALL_ROOT="$ROOT_DIR/sim/binaries/$CONFIG"

mkdir -p "$INSTALL_ROOT"

if ! command -v riscv64-unknown-elf-gcc >/dev/null 2>&1; then
  cat >&2 <<EOF
Missing RISC-V bare-metal toolchain: riscv64-unknown-elf-gcc

Expected one of:
  - RISCV/bin/riscv64-unknown-elf-gcc
  - $CHIPYARD_HOME/toolchains/riscv-tools/install/bin/riscv64-unknown-elf-gcc
  - $CHIPYARD_HOME/toolchains/riscv-tools/riscv/bin/riscv64-unknown-elf-gcc

After the toolchain is available, rerun this script.
EOF
  exit 1
fi

targets=()
if [ "$#" -eq 0 ]; then
  targets=("BAREMETAL_ONLY=1")
else
  targets=("BAREMETAL_ONLY=1")
  for test_name in "$@"; do
    if [[ "$test_name" == *-baremetal ]]; then
      targets+=("$test_name")
    else
      targets+=("${test_name}-baremetal")
    fi
  done
fi

echo "==> building Gemmini bare-metal workloads with MAKE_JOBS=$MAKE_JOBS"
(
  cd "$TEST_ROOT"
  if [ ! -d build ]; then
    autoconf
    mkdir build
    (
      cd build
      ../configure
    )
  fi
  if [ "$#" -eq 0 ]; then
    (
      cd build
      make -j "$MAKE_JOBS" "${targets[@]}"
    )
  else
    mkdir -p build/bareMetalC
    (
      cd build/bareMetalC
      make -j "$MAKE_JOBS" \
        -f "$TEST_ROOT/bareMetalC/Makefile" \
        abs_top_srcdir="$TEST_ROOT" \
        src_dir="$TEST_ROOT/bareMetalC" \
        XLEN=64 \
        PREFIX=examples-bareMetalC \
        BAREMETAL_ONLY=1 \
        "${targets[@]:1}"
    )
  fi
)

echo "==> exporting workload binaries to $INSTALL_ROOT"
if [ "$#" -eq 0 ]; then
  find "$BUILD_ROOT" -maxdepth 1 -type f -name '*-baremetal' -exec cp -f {} "$INSTALL_ROOT/" \;
else
  for test_name in "$@"; do
    binary_name="$test_name"
    if [[ "$binary_name" != *-baremetal ]]; then
      binary_name="${binary_name}-baremetal"
    fi
    cp -f "$BUILD_ROOT/$binary_name" "$INSTALL_ROOT/"
  done
fi

echo "Built workloads are available under: $INSTALL_ROOT"
