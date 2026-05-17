#!/usr/bin/env python3
"""Build and run a Verilator Gemmini gate boundary replay harness."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from phase1b_gate_replay_common import read_json, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary-map", required=True, type=Path)
    parser.add_argument("--boundary-vectors", required=True, type=Path)
    parser.add_argument("--gate-netlist", required=True, type=Path)
    parser.add_argument("--asap7-verilog-dir", required=True, type=Path)
    parser.add_argument("--sram-model-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--emit-vcd", type=Path, default=None)
    parser.add_argument("--trace-depth", type=int, default=3)
    parser.add_argument("--max-cycles", type=int, default=None)
    parser.add_argument("--jobs", type=int, default=128)
    parser.add_argument("--verilator-threads", type=int, default=1)
    parser.add_argument("--output-split", type=int, default=20000)
    parser.add_argument("--output-split-cfuncs", type=int, default=20000)
    parser.add_argument("--output-groups", type=int, default=None)
    parser.add_argument("--cflags", default="")
    parser.add_argument("--verilator-opt", default=None)
    parser.add_argument("--extra-verilator-flag", action="append", default=[])
    parser.add_argument("--skip-build-if-exists", action="store_true")
    parser.add_argument("--relink-if-build-exists", action="store_true")
    parser.add_argument("--use-referenced-cells-only", action="store_true")
    parser.add_argument("--manual-make", action="store_true")
    parser.add_argument("--make-cxx", default=None)
    parser.add_argument("--make-link", default=None)
    parser.add_argument("--max-mismatch-rows", type=int, default=10000)
    parser.add_argument("--progress-interval-cycles", type=int, default=10000)
    parser.add_argument("--build-timeout-sec", type=int, default=3600)
    parser.add_argument("--run-timeout-sec", type=int, default=3600)
    parser.add_argument("--module", default="Gemmini")
    return parser.parse_args()


def cpp_type(width: int) -> str:
    if width <= 8:
        return "uint8_t"
    if width <= 16:
        return "uint16_t"
    if width <= 32:
        return "uint32_t"
    if width <= 64:
        return "uint64_t"
    return "wide"


def infer_payload_valid_ports(outputs: list[dict[str, object]]) -> dict[str, str]:
    output_names = {str(port["name"]) for port in outputs}
    payload_valid: dict[str, str] = {}
    for port in outputs:
        name = str(port["name"])
        marker = "_bits"
        if marker not in name:
            continue
        prefix = name.split(marker, 1)[0]
        valid_name = f"{prefix}_valid"
        if valid_name in output_names:
            payload_valid[name] = valid_name
    return payload_valid


def generate_cpp(args: argparse.Namespace, ports: list[dict[str, object]], cpp_path: Path) -> dict[str, object]:
    inputs = [p for p in ports if p["direction"] == "input" and p["name"] != "clock"]
    outputs = [p for p in ports if p["direction"] == "output"]
    payload_valid = infer_payload_valid_ports(outputs)
    control_outputs = [str(p["name"]) for p in outputs if str(p["name"]) not in payload_valid]
    payload_outputs = sorted(payload_valid)

    def assign_lines(port: dict[str, object], row_name: str) -> list[str]:
        name = str(port["name"])
        width = int(port["width"])
        idx = f'idx.at("{name}")'
        token = f'{row_name}[{idx}]'
        if width <= 64:
            return [f'    top->{name} = static_cast<{cpp_type(width)}>(parse_bits64({token}));']
        words = (width + 31) // 32
        return [f'    assign_wide(top->{name}, {words}, {token});']

    def output_expr(port: dict[str, object]) -> str:
        name = str(port["name"])
        width = int(port["width"])
        if width <= 64:
            return f'bits_from64(top->{name}, {width})'
        words = (width + 31) // 32
        return f'bits_from_wide(top->{name}, {words}, {width})'

    lines: list[str] = []
    lines.extend(
        [
            '#include "VGemmini.h"',
            '#include "verilated.h"',
        ]
    )
    if args.emit_vcd:
        lines.append('#include "verilated_vcd_c.h"')
    lines.extend(
        [
            "#include <algorithm>",
            "#include <chrono>",
            "#include <cstdint>",
            "#include <fstream>",
            "#include <iostream>",
            "#include <sstream>",
            "#include <stdexcept>",
            "#include <string>",
            "#include <unordered_map>",
            "#include <vector>",
            "",
            "static std::vector<std::string> split_csv(const std::string& line) {",
            "  std::vector<std::string> out;",
            "  std::string cur;",
            "  for (char c : line) {",
            "    if (c == ',') { out.push_back(cur); cur.clear(); }",
            "    else { cur.push_back(c); }",
            "  }",
            "  if (!cur.empty() && cur.back() == '\\r') cur.pop_back();",
            "  out.push_back(cur);",
            "  return out;",
            "}",
            "",
            "static uint64_t parse_bits64(const std::string& bits) {",
            "  uint64_t value = 0;",
            "  for (char c : bits) { value <<= 1; if (c == '1') value |= 1ULL; }",
            "  return value;",
            "}",
            "",
            "static void assign_wide(uint32_t* dest, int words, const std::string& bits) {",
            "  for (int i = 0; i < words; ++i) dest[i] = 0;",
            "  int bit = 0;",
            "  for (auto it = bits.rbegin(); it != bits.rend(); ++it, ++bit) {",
            "    if (*it == '1') dest[bit / 32] |= (1u << (bit % 32));",
            "  }",
            "}",
            "",
            "static std::string bits_from64(uint64_t value, int width) {",
            "  std::string bits(width, '0');",
            "  for (int i = 0; i < width; ++i) {",
            "    int shift = width - 1 - i;",
            "    bits[i] = ((value >> shift) & 1ULL) ? '1' : '0';",
            "  }",
            "  return bits;",
            "}",
            "",
            "static std::string bits_from_wide(const uint32_t* value, int words, int width) {",
            "  (void)words;",
            "  std::string bits(width, '0');",
            "  for (int i = 0; i < width; ++i) {",
            "    int bit = width - 1 - i;",
            "    bits[i] = ((value[bit / 32] >> (bit % 32)) & 1u) ? '1' : '0';",
            "  }",
            "  return bits;",
            "}",
            "",
            "static bool known01(const std::string& bits) {",
            "  for (char c : bits) if (c != '0' && c != '1') return false;",
            "  return true;",
            "}",
            "",
            "static void write_map_json(std::ofstream& out, const std::unordered_map<std::string, long long>& values, const std::vector<std::string>& names) {",
            "  out << \"{\";",
            "  bool first = true;",
            "  for (const auto& name : names) {",
            "    auto it = values.find(name);",
            "    if (it == values.end() || it->second == 0) continue;",
            "    if (!first) out << \", \";",
            "    first = false;",
            "    out << \"\\\"\" << name << \"\\\": \" << it->second;",
            "  }",
            "  out << \"}\";",
            "}",
            "",
            "static void apply_inputs(VGemmini* top, const std::vector<std::string>& row, const std::unordered_map<std::string, size_t>& idx) {",
        ]
    )
    for port in inputs:
        lines.extend(assign_lines(port, "row"))
    lines.extend(
        [
            "}",
            "",
            "int main(int argc, char** argv) {",
            "  Verilated::commandArgs(argc, argv);",
            "  if (argc < 6) { std::cerr << \"usage: sim vectors.csv compare.csv max_cycles max_mismatch_rows progress_interval\\n\"; return 2; }",
            "  const std::string vector_path = argv[1];",
            "  const std::string compare_path = argv[2];",
            "  const long long max_cycles = std::stoll(argv[3]);",
            "  const long long max_mismatch_rows = std::stoll(argv[4]);",
            "  const long long progress_interval = std::stoll(argv[5]);",
            "  std::ifstream vin(vector_path);",
            "  if (!vin) { std::cerr << \"failed to open vectors: \" << vector_path << \"\\n\"; return 2; }",
            "  std::ofstream cmp(compare_path);",
            "  if (!cmp) { std::cerr << \"failed to open compare: \" << compare_path << \"\\n\"; return 2; }",
            "  std::string header_line;",
            "  if (!std::getline(vin, header_line)) { std::cerr << \"empty vector file\\n\"; return 2; }",
            "  auto header = split_csv(header_line);",
            "  std::unordered_map<std::string, size_t> idx;",
            "  for (size_t i = 0; i < header.size(); ++i) idx[header[i]] = i;",
            "  std::vector<std::string> required_columns = {",
            "    \"cycle\", \"time_ps\",",
        ]
    )
    for port in inputs + outputs:
        if str(port["name"]) == "clock":
            continue
        lines.append(f'    "{port["name"]}",')
    lines.extend(
        [
            "  };",
            "  bool missing_required_column = false;",
            "  for (const auto& name : required_columns) {",
            "    if (idx.find(name) == idx.end()) { std::cerr << \"missing vector column: \" << name << \"\\n\"; missing_required_column = true; }",
            "  }",
            "  if (missing_required_column) return 2;",
            "  const std::vector<std::string> output_names = {",
        ]
    )
    for port in outputs:
        lines.append(f'    "{port["name"]}",')
    lines.extend(
        [
            "  };",
            "  VGemmini* top = new VGemmini;",
        ]
    )
    if args.emit_vcd:
        lines.extend(
            [
                "  Verilated::traceEverOn(true);",
                "  VerilatedVcdC* tfp = new VerilatedVcdC;",
                f"  top->trace(tfp, {args.trace_depth});",
                f"  tfp->open(\"{args.emit_vcd.resolve()}\");",
            ]
        )
    else:
        lines.append("  void* tfp = nullptr;")
    lines.extend(
        [
            "  cmp << \"cycle,time_ps,port,expected,actual,status,valid_port,valid_value\\n\";",
            "  std::string line;",
            "  if (!std::getline(vin, line)) { std::cerr << \"missing initial vector\\n\"; return 2; }",
            "  auto prev = split_csv(line);",
            "  if (prev.size() < header.size()) { std::cerr << \"initial vector has fewer columns than header\\n\"; return 2; }",
            "  uint64_t sim_time = 0;",
            "  long long cycles = 0;",
            "  long long compared = 0;",
            "  long long skipped_xz = 0;",
            "  long long skipped_invalid_payload = 0;",
            "  long long mismatches = 0;",
            "  long long mismatch_rows_written = 0;",
            "  long long mismatch_rows_suppressed = 0;",
            "  long long first_mismatch_cycle = -1;",
            "  std::unordered_map<std::string, long long> compared_by_port;",
            "  std::unordered_map<std::string, long long> skipped_xz_by_port;",
            "  std::unordered_map<std::string, long long> skipped_invalid_payload_by_port;",
            "  std::unordered_map<std::string, long long> mismatches_by_port;",
            "  const auto start_time = std::chrono::steady_clock::now();",
            "  auto record_mismatch = [&](const std::string& cycle, const std::string& time_ps, const std::string& port, const std::string& expected, const std::string& actual, const std::string& valid_port, const std::string& valid_value) {",
            "    ++mismatches;",
            "    ++mismatches_by_port[port];",
            "    if (first_mismatch_cycle < 0) first_mismatch_cycle = std::stoll(cycle);",
            "    if (max_mismatch_rows < 0 || mismatch_rows_written < max_mismatch_rows) {",
            "      cmp << cycle << \",\" << time_ps << \",\" << port << \",\" << expected << \",\" << actual << \",mismatch,\" << valid_port << \",\" << valid_value << \"\\n\";",
            "      ++mismatch_rows_written;",
            "    } else {",
            "      ++mismatch_rows_suppressed;",
            "    }",
            "  };",
            "  while (std::getline(vin, line)) {",
            "    if (max_cycles >= 0 && cycles >= max_cycles) break;",
            "    auto cur = split_csv(line);",
            "    if (cur.size() < header.size()) { std::cerr << \"cycle row has fewer columns than header at cycle \" << cycles << \"\\n\"; return 2; }",
            "    apply_inputs(top, prev, idx);",
            "    top->clock = 0; top->eval();",
        ]
    )
    if args.emit_vcd:
        lines.append("    tfp->dump(sim_time++);")
    else:
        lines.append("    sim_time++;")
    lines.extend(["    top->clock = 1; top->eval();"])
    if args.emit_vcd:
        lines.append("    tfp->dump(sim_time++);")
    else:
        lines.append("    sim_time++;")
    lines.extend(
        [
            "    const std::string cycle = cur[idx.at(\"cycle\")];",
            "    const std::string time_ps = cur[idx.at(\"time_ps\")];",
        ]
    )
    for port in outputs:
        name = str(port["name"])
        expr = output_expr(port)
        valid_name = payload_valid.get(name)
        lines.extend(
            [
                f"    {{ const std::string expected = cur[idx.at(\"{name}\")];",
                f"      const std::string actual = {expr};",
            ]
        )
        if valid_name:
            lines.extend(
                [
                    f"      const std::string valid_value = cur[idx.at(\"{valid_name}\")];",
                    f"      if (!known01(valid_value)) {{ ++skipped_xz; ++skipped_xz_by_port[\"{name}\"]; }}",
                    f"      else if (valid_value != \"1\") {{ ++skipped_invalid_payload; ++skipped_invalid_payload_by_port[\"{name}\"]; }}",
                    f"      else if (!known01(expected)) {{ ++skipped_xz; ++skipped_xz_by_port[\"{name}\"]; }}",
                    f"      else if (expected != actual) {{ ++compared; ++compared_by_port[\"{name}\"]; record_mismatch(cycle, time_ps, \"{name}\", expected, actual, \"{valid_name}\", valid_value); }}",
                    f"      else {{ ++compared; ++compared_by_port[\"{name}\"]; }} }}",
                ]
            )
        else:
            lines.extend(
                [
                    f"      if (!known01(expected)) {{ ++skipped_xz; ++skipped_xz_by_port[\"{name}\"]; }}",
                    f"      else if (expected != actual) {{ ++compared; ++compared_by_port[\"{name}\"]; record_mismatch(cycle, time_ps, \"{name}\", expected, actual, \"\", \"\"); }}",
                    f"      else {{ ++compared; ++compared_by_port[\"{name}\"]; }} }}",
                ]
            )
    lines.extend(["    top->clock = 0; top->eval();"])
    if args.emit_vcd:
        lines.append("    tfp->dump(sim_time++);")
    else:
        lines.append("    sim_time++;")
    lines.extend(
        [
            "    prev.swap(cur);",
            "    ++cycles;",
            "    if (progress_interval > 0 && (cycles % progress_interval) == 0) {",
            "      const auto now = std::chrono::steady_clock::now();",
            "      const double elapsed = std::chrono::duration<double>(now - start_time).count();",
            "      std::cerr << \"[progress] cycles=\" << cycles << \" compared=\" << compared << \" skipped_invalid_payload=\" << skipped_invalid_payload << \" skipped_xz=\" << skipped_xz << \" mismatches=\" << mismatches << \" elapsed_sec=\" << elapsed << \"\\n\";",
            "    }",
            "  }",
        ]
    )
    if args.emit_vcd:
        lines.extend(["  tfp->close();", "  delete tfp;"])
    lines.extend(
        [
            "  top->final();",
            "  delete top;",
            "  const auto end_time = std::chrono::steady_clock::now();",
            "  const double elapsed = std::chrono::duration<double>(end_time - start_time).count();",
            "  std::ofstream summary(\"replay_summary.json\");",
            "  summary << \"{\\n\";",
            "  summary << \"  \\\"cycles_run\\\": \" << cycles << \",\\n\";",
            "  summary << \"  \\\"elapsed_sec\\\": \" << elapsed << \",\\n\";",
            f"  summary << \"  \\\"output_ports_total\\\": {len(outputs)},\\n\";",
            f"  summary << \"  \\\"control_output_ports\\\": {len(control_outputs)},\\n\";",
            f"  summary << \"  \\\"payload_output_ports\\\": {len(payload_outputs)},\\n\";",
            "  summary << \"  \\\"compared_values\\\": \" << compared << \",\\n\";",
            "  summary << \"  \\\"skipped_xz_values\\\": \" << skipped_xz << \",\\n\";",
            "  summary << \"  \\\"skipped_invalid_payload_values\\\": \" << skipped_invalid_payload << \",\\n\";",
            "  summary << \"  \\\"mismatches\\\": \" << mismatches << \",\\n\";",
            "  summary << \"  \\\"mismatch_rows_written\\\": \" << mismatch_rows_written << \",\\n\";",
            "  summary << \"  \\\"mismatch_rows_suppressed\\\": \" << mismatch_rows_suppressed << \",\\n\";",
            "  summary << \"  \\\"first_mismatch_cycle\\\": \";",
            "  if (first_mismatch_cycle < 0) summary << \"null\"; else summary << first_mismatch_cycle;",
            "  summary << \",\\n\";",
            "  summary << \"  \\\"compared_by_port\\\": \"; write_map_json(summary, compared_by_port, output_names); summary << \",\\n\";",
            "  summary << \"  \\\"skipped_xz_by_port\\\": \"; write_map_json(summary, skipped_xz_by_port, output_names); summary << \",\\n\";",
            "  summary << \"  \\\"skipped_invalid_payload_by_port\\\": \"; write_map_json(summary, skipped_invalid_payload_by_port, output_names); summary << \",\\n\";",
            "  summary << \"  \\\"mismatches_by_port\\\": \"; write_map_json(summary, mismatches_by_port, output_names); summary << \"\\n\";",
            "  summary << \"}\\n\";",
            "  std::cout << \"cycles=\" << cycles << \" compared=\" << compared << \" skipped_invalid_payload=\" << skipped_invalid_payload << \" skipped_xz=\" << skipped_xz << \" mismatches=\" << mismatches << \" elapsed_sec=\" << elapsed << \"\\n\";",
            "  return mismatches == 0 ? 0 : 1;",
            "}",
        ]
    )
    cpp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "mode": "validity-aware output compare",
        "output_ports_total": len(outputs),
        "control_output_ports": control_outputs,
        "payload_output_valid": payload_valid,
        "payload_output_ports": payload_outputs,
        "max_mismatch_rows": args.max_mismatch_rows,
        "progress_interval_cycles": args.progress_interval_cycles,
    }


def run_command(cmd: list[str], cwd: Path, timeout: int, log: Path, append: bool = False) -> int:
    mode = "a" if append else "w"
    with log.open(mode, encoding="utf-8", errors="ignore") as f:
        if append:
            f.write("\n")
        f.write("$ " + " ".join(cmd) + "\n")
        f.flush()
        proc = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return proc.returncode


def collect_used_asap7_cells(gate_netlist: Path) -> set[str]:
    text = gate_netlist.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"^\s*([A-Za-z_][\w$]*ASAP7[\w$]*)\s+(?:\\[^\s]+|[A-Za-z_][\w$]*)\s*\(", text, re.MULTILINE))


def write_referenced_cell_library(gate_netlist: Path, asap7_dir: Path, out_dir: Path) -> list[Path]:
    used = collect_used_asap7_cells(gate_netlist)
    if not used:
        raise RuntimeError(f"no ASAP7 cell instantiations found in {gate_netlist}")

    primitive_re = re.compile(r"^primitive\s+([^\s(;]+).*?^endprimitive\s*", re.MULTILINE | re.DOTALL)
    module_re = re.compile(r"^module\s+([^\s(;]+).*?^endmodule\s*", re.MULTILINE | re.DOTALL)
    primitives: dict[str, str] = {}
    found: dict[str, str] = {}
    sources: dict[str, str] = {}
    for src in sorted(asap7_dir.glob("*.v")):
        text = src.read_text(encoding="utf-8", errors="ignore")
        for match in primitive_re.finditer(text):
            name = match.group(1)
            primitives.setdefault(name, match.group(0).rstrip() + "\n")
        for match in module_re.finditer(text):
            name = match.group(1)
            if name in used and name not in found:
                found[name] = match.group(0).rstrip() + "\n"
                sources[name] = str(src)

    missing = sorted(used - set(found))
    if missing:
        raise RuntimeError("missing ASAP7 Verilog modules: " + ", ".join(missing[:20]))

    lib_dir = out_dir / "asap7_referenced_cells"
    lib_dir.mkdir(parents=True, exist_ok=True)
    lib_path = lib_dir / "used_asap7_cells.v"
    with lib_path.open("w", encoding="utf-8") as f:
        f.write("// Auto-generated by phase1b_run_gate_boundary_replay.py from ASAP7 PDK Verilog.\n")
        f.write("// Contains only cell modules instantiated by the selected mapped netlist.\n\n")
        for name in sorted(primitives):
            f.write(primitives[name])
            f.write("\n")
        for name in sorted(found):
            f.write(found[name])
            f.write("\n")

    write_json(
        out_dir / "referenced_cell_library_manifest.json",
        {
            "gate_netlist": str(gate_netlist),
            "asap7_verilog_dir": str(asap7_dir),
            "used_cell_count": len(used),
            "primitive_count": len(primitives),
            "library": str(lib_path),
            "sources": {name: sources[name] for name in sorted(sources)},
        },
    )
    return [lib_path]


def make_build_command(args: argparse.Namespace, build_dir: Path) -> list[str]:
    cmd = ["make", "-C", str(build_dir.resolve()), "-f", f"V{args.module}.mk", "-j", str(args.jobs)]
    if args.make_cxx:
        cmd.append(f"CXX={args.make_cxx}")
    if args.make_link:
        cmd.append(f"LINK={args.make_link}")
    return cmd


def write_compare_report(
    path: Path,
    args: argparse.Namespace,
    compare_csv: Path,
    summary: dict[str, object],
    compare_policy: dict[str, object],
) -> None:
    first_mismatch = summary.get("first_mismatch_cycle")
    first_mismatch_text = "none" if first_mismatch is None else str(first_mismatch)
    path.write_text(
        "# Phase1b Gate Output Compare\n\n"
        f"- vectors: `{args.boundary_vectors}`\n"
        f"- cycles run: `{summary.get('cycles_run', 'unknown')}`\n"
        f"- elapsed sec: `{summary.get('elapsed_sec', 'unknown')}`\n"
        f"- output ports: `{summary.get('output_ports_total', compare_policy.get('output_ports_total', 'unknown'))}`\n"
        f"- control/valid/ready output ports: `{summary.get('control_output_ports', len(compare_policy.get('control_output_ports', [])))}`\n"
        f"- payload output ports gated by valid: `{summary.get('payload_output_ports', len(compare_policy.get('payload_output_ports', [])))}`\n"
        f"- compared deterministic valid values: `{summary.get('compared_values', 'unknown')}`\n"
        f"- skipped x/z expected or valid values: `{summary.get('skipped_xz_values', 'unknown')}`\n"
        f"- skipped invalid-payload values: `{summary.get('skipped_invalid_payload_values', 'unknown')}`\n"
        f"- mismatches: `{summary.get('mismatches', 'unknown')}`\n"
        f"- first mismatch cycle: `{first_mismatch_text}`\n"
        f"- mismatch CSV rows written: `{summary.get('mismatch_rows_written', 'unknown')}`\n"
        f"- mismatch CSV rows suppressed: `{summary.get('mismatch_rows_suppressed', 'unknown')}`\n"
        f"- mismatch CSV: `{compare_csv}`\n"
        f"- summary JSON: `{path.with_name('replay_summary.json')}`\n"
        f"- gate VCD: `{args.emit_vcd or ''}`\n\n"
        "Payload compare policy: output ports with names containing `_bits` are compared only when their same-channel "
        "RTL expected `_valid` output is known `1`. Ready, valid, busy, interrupt, and other non-payload outputs "
        "remain cycle-by-cycle compares when the RTL expected value is deterministic. Invalid payload and RTL x/z "
        "skips are counted separately and are not written as mismatch rows.\n\n"
        "This is Verilator zero-delay functional replay, not SDF timing simulation.\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    build_dir = args.out_dir / "verilator_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    cpp_path = args.out_dir / "tb_phase1b_gemmini.cpp"
    mapping = read_json(args.boundary_map)
    ports = list(mapping["ports"])
    compare_policy = generate_cpp(args, ports, cpp_path)

    if args.use_referenced_cells_only:
        cell_files = write_referenced_cell_library(args.gate_netlist, args.asap7_verilog_dir, args.out_dir)
    else:
        cell_files = sorted(args.asap7_verilog_dir.glob("*.v"))
    sram_files = [args.sram_model_dir / "mem_ext.sv", args.sram_model_dir / "mem_0_ext.sv"]
    for path in [args.gate_netlist, args.boundary_vectors, *cell_files, *sram_files]:
        if not Path(path).is_file():
            raise RuntimeError(f"missing input file: {path}")

    cmd = [
        "verilator",
        "--cc",
        "--exe",
        *( [] if args.manual_make else ["--build"] ),
        "--timing",
        *( [args.verilator_opt] if args.verilator_opt else [] ),
        *args.extra_verilator_flag,
        "--top-module",
        args.module,
        "--threads",
        str(args.verilator_threads),
        "--threads-dpi",
        "all",
        "--output-split",
        str(args.output_split),
        "--output-split-cfuncs",
        str(args.output_split_cfuncs),
        *( ["--output-groups", str(args.output_groups)] if args.output_groups is not None else [] ),
        "--Mdir",
        str(build_dir.resolve()),
        *( ["--verilate-jobs", str(args.jobs)] if args.manual_make else ["-j", str(args.jobs)] ),
        "-Wno-SPECIFYIGN",
        "-Wno-TIMESCALEMOD",
        "-Wno-MULTITOP",
        "-Wno-DECLFILENAME",
        "-Wno-PINCONNECTEMPTY",
        "-Wno-UNOPTFLAT",
        "-Wno-WIDTHEXPAND",
        "-Wno-WIDTHTRUNC",
        "--x-assign",
        "0",
        "--x-initial",
        "0",
    ]
    if args.cflags:
        cmd.extend(["-CFLAGS", args.cflags])
    if args.emit_vcd:
        cmd.extend(["--trace", "--trace-depth", str(args.trace_depth)])
    cmd.extend([str(args.gate_netlist.resolve()), *[str(path.resolve()) for path in sram_files], *[str(path.resolve()) for path in cell_files], str(cpp_path.resolve())])

    build_log = args.out_dir / "verilator_build.log"
    exe = build_dir / "VGemmini"
    build_skipped = False
    make_cmd = None
    try:
        if args.skip_build_if_exists and exe.is_file():
            build_rc = 0
            build_skipped = True
            if args.relink_if_build_exists:
                make_cmd = make_build_command(args, build_dir)
                build_rc = run_command(make_cmd, args.out_dir, args.build_timeout_sec, build_log, append=True)
                build_skipped = False
        else:
            build_rc = run_command(cmd, args.out_dir, args.build_timeout_sec, build_log)
            if build_rc == 0 and args.manual_make:
                make_cmd = make_build_command(args, build_dir)
                build_rc = run_command(make_cmd, args.out_dir, args.build_timeout_sec, build_log, append=True)
    except subprocess.TimeoutExpired:
        build_rc = 124
        build_log.write_text(build_log.read_text(encoding="utf-8", errors="ignore") + "\nTIMEOUT\n", encoding="utf-8")
    manifest = {
        "build_command": cmd,
        "make_command": make_cmd,
        "build_returncode": build_rc,
        "build_skipped": build_skipped,
        "relink_if_build_exists": args.relink_if_build_exists,
        "build_log": str(build_log),
        "cpp": str(cpp_path.resolve()),
        "compare_policy": compare_policy,
    }
    if build_rc != 0:
        write_json(args.out_dir / "gate_replay_manifest.json", manifest)
        raise SystemExit(build_rc)

    compare_csv = args.out_dir / "gate_output_compare.csv"
    run_cycles = args.max_cycles if args.max_cycles is not None else -1
    run_log = args.out_dir / "gate_replay_run.log"
    run_cmd = [
        str(exe.resolve()),
        str(args.boundary_vectors.resolve()),
        str(compare_csv.resolve()),
        str(run_cycles),
        str(args.max_mismatch_rows),
        str(args.progress_interval_cycles),
    ]
    try:
        run_rc = run_command(run_cmd, args.out_dir, args.run_timeout_sec, run_log)
    except subprocess.TimeoutExpired:
        run_rc = 124
        run_log.write_text(run_log.read_text(encoding="utf-8", errors="ignore") + "\nTIMEOUT\n", encoding="utf-8")

    summary_path = args.out_dir / "replay_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    manifest.update(
        {
            "run_command": run_cmd,
            "run_returncode": run_rc,
            "run_log": str(run_log),
            "compare_csv": str(compare_csv),
            "emit_vcd": str(args.emit_vcd.resolve()) if args.emit_vcd else None,
            "summary": summary,
            "jobs": args.jobs,
            "verilator_threads": args.verilator_threads,
            "output_split": args.output_split,
            "output_split_cfuncs": args.output_split_cfuncs,
            "output_groups": args.output_groups,
            "cflags": args.cflags,
            "verilator_opt": args.verilator_opt,
            "extra_verilator_flags": args.extra_verilator_flag,
            "skip_build_if_exists": args.skip_build_if_exists,
            "relink_if_build_exists": args.relink_if_build_exists,
            "max_mismatch_rows": args.max_mismatch_rows,
            "progress_interval_cycles": args.progress_interval_cycles,
            "compare_policy": compare_policy,
            "method": "previous sampled input vector drives next Verilator rising edge; current sampled output vector is expected output; payload outputs compare only when same-channel RTL expected valid is 1",
        }
    )
    write_json(args.out_dir / "gate_replay_manifest.json", manifest)
    report = args.out_dir / "gate_output_compare_report.md"
    summary_md = args.out_dir / "replay_summary.md"
    write_compare_report(report, args, compare_csv, summary, compare_policy)
    write_compare_report(summary_md, args, compare_csv, summary, compare_policy)
    print(json.dumps({"run_returncode": run_rc, "summary": summary}, indent=2))
    raise SystemExit(run_rc)


if __name__ == "__main__":
    main()
