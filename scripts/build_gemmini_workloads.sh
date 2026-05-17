#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

CONFIG="${CONFIG:-GemminiRocketConfig}"
MAKE_JOBS="${MAKE_JOBS:-$(nproc)}"
RUN_ROOT="${RUN_ROOT:-}"
TEST_ROOT="$GEMMINI_HOME/software/gemmini-rocc-tests"
BUILD_ROOT="$TEST_ROOT/build/bareMetalC"

if [ -n "$RUN_ROOT" ]; then
  mkdir -p "$RUN_ROOT"
  RUN_ROOT=$(cd "$RUN_ROOT" && pwd)
  INSTALL_ROOT="$RUN_ROOT/workloads"
else
  INSTALL_ROOT="$ROOT_DIR/sim/binaries/$CONFIG"
fi

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

copy_binary() {
  local test_name="$1"
  local binary_name="$test_name"
  if [[ "$binary_name" != *-baremetal ]]; then
    binary_name="${binary_name}-baremetal"
  fi
  if [ ! -f "$BUILD_ROOT/$binary_name" ]; then
    echo "Missing built binary: $BUILD_ROOT/$binary_name" >&2
    exit 1
  fi
  if [ -n "$RUN_ROOT" ]; then
    mkdir -p "$INSTALL_ROOT/$test_name"
    cp -f "$BUILD_ROOT/$binary_name" "$INSTALL_ROOT/$test_name/"
  else
    cp -f "$BUILD_ROOT/$binary_name" "$INSTALL_ROOT/"
  fi
}

echo "==> exporting workload binaries to $INSTALL_ROOT"
if [ "$#" -eq 0 ]; then
  find "$BUILD_ROOT" -maxdepth 1 -type f -name '*-baremetal' | while read -r built_binary; do
    binary_name=$(basename "$built_binary")
    test_name=${binary_name%-baremetal}
    if [ -n "$RUN_ROOT" ]; then
      mkdir -p "$INSTALL_ROOT/$test_name"
      cp -f "$built_binary" "$INSTALL_ROOT/$test_name/"
    else
      cp -f "$built_binary" "$INSTALL_ROOT/"
    fi
  done
else
  for test_name in "$@"; do
    copy_binary "$test_name"
  done
fi

echo "Built workloads are available under: $INSTALL_ROOT"
