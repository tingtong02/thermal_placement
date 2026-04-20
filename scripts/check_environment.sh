#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

source "$ROOT/tools/env_gemmini_thermal.sh"

run() {
  local label="$1"
  shift
  echo "==> $label"
  "$@"
}

run_shell() {
  local label="$1"
  shift
  echo "==> $label"
  bash -lc "$*"
}

check_required_paths() {
  local missing=0
  local paths=(
    "$CHIPYARD_HOME/build.sbt"
    "$GEMMINI_HOME/src/main/scala"
    "$GEMMINI_HOME/software/gemmini-rocc-tests"
    "$GEMMINI_HOME/software/gemmini-rocc-tests/riscv-tests/env"
    "$GEMMINI_HOME/software/libgemmini"
    "$CHIPYARD_HOME/generators/rocket-chip/dependencies/chisel"
    "$CHIPYARD_HOME/generators/rocket-chip/dependencies/hardfloat/berkeley-softfloat-3"
    "$FLOW_HOME/Makefile"
    "$HOTSPOT_HOME/hotspot"
    "$OPENROAD_EXE"
    "$YOSYS_EXE"
  )

  for path in "${paths[@]}"; do
    if [[ ! -e "$path" ]]; then
      echo "missing required path: $path" >&2
      missing=1
    fi
  done

  if [[ "$missing" -ne 0 ]]; then
    return 1
  fi
}

check_chipyard_submodules() {
  local bad
  bad="$(
    git -C "$CHIPYARD_HOME" submodule status --recursive \
      | awk '$1 ~ /^-/ {print $2}' \
      | grep -Ev '^(generators/ara/ara/toolchain/riscv-llvm|generators/gemmini/software/onnxruntime-riscv)$' \
      || true
  )"

  if [[ -n "$bad" ]]; then
    echo "required Chipyard submodules are missing:" >&2
    echo "$bad" >&2
    return 1
  fi

  echo "Chipyard required submodules ok; only Ara LLVM and Gemmini ONNX Runtime may be absent"
}

check_verilator() {
  cat > "$TMP_DIR/tiny.sv" <<'SV'
module tiny(input logic clk, input logic rst, output logic q);
  always_ff @(posedge clk) begin
    if (rst) q <= 1'b0;
    else q <= ~q;
  end
endmodule
SV
  verilator --lint-only "$TMP_DIR/tiny.sv"
}

check_yosys() {
  cat > "$TMP_DIR/tiny.v" <<'V'
module tiny(input clk, input rst, output reg q);
  always @(posedge clk) begin
    if (rst) q <= 1'b0;
    else q <= ~q;
  end
endmodule
V
  yosys -q -p "read_verilog $TMP_DIR/tiny.v; synth -top tiny"
}

check_opensta() {
  printf 'puts "sta smoke ok"\nexit\n' | sta -no_splash
}

check_openroad() {
  printf 'puts "openroad smoke ok"\nexit\n' | openroad -no_splash
}

check_hotspot() {
  (
    cd "$HOTSPOT_HOME/examples/example1"
    hotspot -c example.config -f ev6.flp -p gcc.ptrace -o "$TMP_DIR/hotspot.ttrace" >/dev/null
  )
  test -s "$TMP_DIR/hotspot.ttrace"
  hotfloorplan -h >/dev/null 2>&1 || true
}

run "required paths" check_required_paths
run "Chipyard required submodules" check_chipyard_submodules
run "Python analysis packages and VCD parser" python "$ROOT/scripts/check_python_env.py"
run "Make" make --version
run "Bash" bash --version
run "Java" java -version
run "sbt launcher" sbt --script-version
run_shell "Chipyard sbt project load" "cd '$CHIPYARD_HOME' && sbt -batch -Dsbt.log.noformat=true 'show version'"
run "Verilator version" verilator --version
run "Verilator lint smoke" check_verilator
run "Yosys version" yosys -V
run "Yosys synth smoke" check_yosys
run "OpenSTA version" sta -version
run "OpenSTA Tcl smoke" check_opensta
run "OpenROAD version" openroad -version
run "OpenROAD Tcl smoke" check_openroad
run_shell "ORFS tool checks" "make -C '$FLOW_HOME' check-yosys check-openroad"
run "HotSpot thermal smoke" check_hotspot

echo "environment check passed"
