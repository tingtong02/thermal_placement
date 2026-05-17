#!/usr/bin/env python3
"""Build and run a no-compare Gemmini gate boundary replay SAIF harness."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from phase1b_gate_replay_common import read_json, write_json
from phase1b_run_gate_boundary_replay import collect_used_asap7_cells

DEFAULT_MODULE = "Gemmini"
SPLIT_THRESHOLD_BYTES = 128 * 1024 * 1024
SPLIT_PARTS = 32


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary-map", required=True, type=Path)
    parser.add_argument("--boundary-vectors", required=True, type=Path)
    parser.add_argument("--gate-netlist", required=True, type=Path)
    parser.add_argument("--asap7-verilog-dir", required=True, type=Path)
    parser.add_argument("--sram-model-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--build-root", required=True, type=Path)
    parser.add_argument("--emit-saif", required=True, type=Path)
    parser.add_argument("--trace-start-ps", required=True, type=int)
    parser.add_argument("--trace-end-ps", required=True, type=int)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--run-kind", default="formal")
    parser.add_argument("--max-cycles", type=int, default=None)
    parser.add_argument("--skip-build-if-exists", action="store_true")
    parser.add_argument("--module", default=DEFAULT_MODULE)
    parser.add_argument("--trace-depth", type=int, default=9)
    parser.add_argument("--verilate-jobs", type=int, default=192)
    parser.add_argument("--jobs", type=int, default=192)
    parser.add_argument("--verilator-threads", type=int, default=16)
    parser.add_argument("--output-split", type=int, default=200)
    parser.add_argument("--output-split-cfuncs", type=int, default=20)
    parser.add_argument("--output-split-ctrace", type=int, default=20)
    parser.add_argument("--cflags", default="-O0 -g0")
    parser.add_argument("--make-cxx", default="clang++")
    parser.add_argument("--make-link", default="clang++")
    parser.add_argument("--extra-verilator-flag", action="append", default=[])
    parser.add_argument("--no-auto-split", action="store_true")
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


def generate_cpp(args: argparse.Namespace, ports: list[dict[str, object]], cpp_path: Path) -> dict[str, object]:
    inputs = [p for p in ports if p["direction"] == "input" and p["name"] != "clock"]

    def assign_lines(port: dict[str, object], row_name: str) -> list[str]:
        name = str(port["name"])
        width = int(port["width"])
        idx = f'idx.at("{name}")'
        token = f'{row_name}[{idx}]'
        if width <= 64:
            return [f'    top->{name} = static_cast<{cpp_type(width)}>(parse_bits64({token}));']
        words = (width + 31) // 32
        return [f'    assign_wide(top->{name}, {words}, {token});']

    lines: list[str] = []
    lines.extend(
        [
            '#include "VGemmini.h"',
            '#include "verilated.h"',
            '#include "verilated_saif_c.h"',
            '#include <chrono>',
            '#include <cstdint>',
            '#include <fstream>',
            '#include <iostream>',
            '#include <sstream>',
            '#include <string>',
            '#include <unordered_map>',
            '#include <vector>',
            '',
            'static std::vector<std::string> split_csv(const std::string& line) {',
            '  std::vector<std::string> out;',
            '  std::string cur;',
            '  for (char c : line) {',
            "    if (c == ',') { out.push_back(cur); cur.clear(); }",
            '    else { cur.push_back(c); }',
            '  }',
            "  if (!cur.empty() && cur.back() == '\\r') cur.pop_back();",
            '  out.push_back(cur);',
            '  return out;',
            '}',
            '',
            'static uint64_t parse_bits64(const std::string& bits) {',
            '  uint64_t value = 0;',
            "  for (char c : bits) { value <<= 1; if (c == '1') value |= 1ULL; }",
            '  return value;',
            '}',
            '',
            'static void assign_wide(uint32_t* dest, int words, const std::string& bits) {',
            '  for (int i = 0; i < words; ++i) dest[i] = 0;',
            '  int bit = 0;',
            '  for (auto it = bits.rbegin(); it != bits.rend(); ++it, ++bit) {',
            "    if (*it == '1') dest[bit / 32] |= (1u << (bit % 32));",
            '  }',
            '}',
            '',
            'static std::string json_escape(const std::string& value) {',
            '  std::string out;',
            '  for (char c : value) {',
            "    if (c == '\\\\') out += \"\\\\\\\\\";",
            "    else if (c == '\"') out += \"\\\\\\\"\";",
            "    else if (c == '\\n') out += \"\\\\n\";",
            '    else out += c;',
            '  }',
            '  return out;',
            '}',
            '',
            'static void apply_inputs(VGemmini* top, const std::vector<std::string>& row, const std::unordered_map<std::string, size_t>& idx) {',
        ]
    )
    for port in inputs:
        lines.extend(assign_lines(port, "row"))
    lines.extend(
        [
            '}',
            '',
            'int main(int argc, char** argv) {',
            '  Verilated::commandArgs(argc, argv);',
            '  if (argc < 8) {',
            '    std::cerr << "usage: sim vectors.csv saif trace_start_ps trace_end_ps max_cycles summary.json workload\\n";',
            '    return 2;',
            '  }',
            '  const std::string vector_path = argv[1];',
            '  const std::string saif_path = argv[2];',
            '  const long long trace_start_ps = std::stoll(argv[3]);',
            '  const long long trace_end_ps = std::stoll(argv[4]);',
            '  const long long max_cycles = std::stoll(argv[5]);',
            '  const std::string summary_path = argv[6];',
            '  const std::string workload = argv[7];',
            '  if (trace_end_ps <= trace_start_ps) { std::cerr << "invalid trace window\\n"; return 2; }',
            '  std::ifstream vin(vector_path);',
            '  if (!vin) { std::cerr << "failed to open vectors: " << vector_path << "\\n"; return 2; }',
            '  std::string header_line;',
            '  if (!std::getline(vin, header_line)) { std::cerr << "empty vector file\\n"; return 2; }',
            '  auto header = split_csv(header_line);',
            '  std::unordered_map<std::string, size_t> idx;',
            '  for (size_t i = 0; i < header.size(); ++i) idx[header[i]] = i;',
            '  std::vector<std::string> required_columns = {',
            '    "cycle", "time_ps", "clock",',
        ]
    )
    for port in inputs:
        lines.append(f'    "{port["name"]}",')
    lines.extend(
        [
            '  };',
            '  bool missing_required_column = false;',
            '  for (const auto& name : required_columns) {',
            '    if (idx.find(name) == idx.end()) { std::cerr << "missing vector column: " << name << "\\n"; missing_required_column = true; }',
            '  }',
            '  if (missing_required_column) return 2;',
            '  std::string line;',
            '  if (!std::getline(vin, line)) { std::cerr << "missing initial vector\\n"; return 2; }',
            '  auto prev = split_csv(line);',
            '  if (prev.size() < header.size()) { std::cerr << "initial vector has fewer columns than header\\n"; return 2; }',
            '  VGemmini* top = new VGemmini;',
            '  Verilated::traceEverOn(true);',
            '  VerilatedSaifC* tfp = new VerilatedSaifC;',
            f'  top->trace(tfp, {args.trace_depth});',
            '  tfp->open(saif_path.c_str());',
            '  std::cerr << "[start] workload=" << workload << " vectors=" << vector_path << " saif=" << saif_path',
            '            << " trace_start_ps=" << trace_start_ps << " trace_end_ps=" << trace_end_ps << "\\n";',
            '  long long cycles = 0;',
            '  long long rows_seen = 1;',
            '  long long trace_enabled_cycles = 0;',
            '  long long first_trace_cycle = -1;',
            '  long long last_trace_cycle = -1;',
            '  long long first_trace_time_ps = -1;',
            '  long long last_trace_time_ps = -1;',
            '  long long last_time_ps = -1;',
            '  bool trace_start_logged = false;',
            '  const auto start_time = std::chrono::steady_clock::now();',
            '  while (std::getline(vin, line)) {',
            '    if (max_cycles >= 0 && cycles >= max_cycles) break;',
            '    auto cur = split_csv(line);',
            '    if (cur.size() < header.size()) { std::cerr << "cycle row has fewer columns than header at cycle " << cycles << "\\n"; return 2; }',
            '    const long long row_cycle = std::stoll(cur[idx.at("cycle")]);',
            '    const long long time_ps = std::stoll(cur[idx.at("time_ps")]);',
            '    const bool trace_on = (time_ps >= trace_start_ps && time_ps < trace_end_ps);',
            '    apply_inputs(top, prev, idx);',
            '    top->clock = 0; top->eval();',
            '    if (trace_on) { long long t = time_ps > 0 ? time_ps - 1 : time_ps; tfp->dump(static_cast<uint64_t>(t)); }',
            '    top->clock = 1; top->eval();',
            '    if (trace_on) {',
            '      tfp->dump(static_cast<uint64_t>(time_ps));',
            '      if (!trace_start_logged) {',
            '        std::cerr << "[trace] first_enabled_cycle=" << row_cycle << " first_enabled_time_ps=" << time_ps << "\\n";',
            '        trace_start_logged = true;',
            '      }',
            '    }',
            '    top->clock = 0; top->eval();',
            '    if (trace_on) { tfp->dump(static_cast<uint64_t>(time_ps + 1)); }',
            '    if (trace_on) {',
            '      if (first_trace_cycle < 0) { first_trace_cycle = row_cycle; first_trace_time_ps = time_ps; }',
            '      last_trace_cycle = row_cycle;',
            '      last_trace_time_ps = time_ps;',
            '      ++trace_enabled_cycles;',
            '    }',
            '    last_time_ps = time_ps;',
            '    prev.swap(cur);',
            '    ++cycles;',
            '    ++rows_seen;',
            '  }',
            '  top->final();',
            '  tfp->close();',
            '  delete tfp;',
            '  delete top;',
            '  const auto end_time = std::chrono::steady_clock::now();',
            '  const double elapsed = std::chrono::duration<double>(end_time - start_time).count();',
            '  std::ofstream summary(summary_path);',
            '  summary << "{\\n";',
            '  summary << "  \\\"workload\\\": \\\"" << json_escape(workload) << "\\\",\\n";',
            '  summary << "  \\\"vector_path\\\": \\\"" << json_escape(vector_path) << "\\\",\\n";',
            '  summary << "  \\\"saif_path\\\": \\\"" << json_escape(saif_path) << "\\\",\\n";',
            '  summary << "  \\\"trace_start_ps\\\": " << trace_start_ps << ",\\n";',
            '  summary << "  \\\"trace_end_ps\\\": " << trace_end_ps << ",\\n";',
            '  summary << "  \\\"cycles_run\\\": " << cycles << ",\\n";',
            '  summary << "  \\\"rows_seen\\\": " << rows_seen << ",\\n";',
            '  summary << "  \\\"last_time_ps\\\": " << last_time_ps << ",\\n";',
            '  summary << "  \\\"trace_enabled_cycles\\\": " << trace_enabled_cycles << ",\\n";',
            '  summary << "  \\\"first_trace_cycle\\\": "; if (first_trace_cycle < 0) summary << "null"; else summary << first_trace_cycle; summary << ",\\n";',
            '  summary << "  \\\"first_trace_time_ps\\\": "; if (first_trace_time_ps < 0) summary << "null"; else summary << first_trace_time_ps; summary << ",\\n";',
            '  summary << "  \\\"last_trace_cycle\\\": "; if (last_trace_cycle < 0) summary << "null"; else summary << last_trace_cycle; summary << ",\\n";',
            '  summary << "  \\\"last_trace_time_ps\\\": "; if (last_trace_time_ps < 0) summary << "null"; else summary << last_trace_time_ps; summary << ",\\n";',
            '  summary << "  \\\"elapsed_sec\\\": " << elapsed << "\\n";',
            '  summary << "}\\n";',
            '  std::cerr << "[finish] cycles=" << cycles << " trace_enabled_cycles=" << trace_enabled_cycles << " elapsed_sec=" << elapsed << "\\n";',
            '  return trace_enabled_cycles > 0 ? 0 : 3;',
            '}',
        ]
    )
    cpp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "mode": "no-compare gate SAIF replay",
        "input_ports": [str(p["name"]) for p in inputs],
        "input_ports_total": len(inputs),
        "trace_depth": args.trace_depth,
        "input_drive_policy": "row N-1 input vector drives replay cycle N; trace decision uses row N time_ps",
    }


def write_referenced_cell_library(gate_netlist: Path, asap7_dir: Path, build_root: Path) -> list[Path]:
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
        raise RuntimeError("missing ASAP7 Verilog modules: " + ", ".join(missing[:40]))
    lib_dir = build_root / "referenced_cell_library"
    lib_dir.mkdir(parents=True, exist_ok=True)
    lib_path = lib_dir / "used_asap7_cells_r28.v"
    with lib_path.open("w", encoding="utf-8") as f:
        f.write("// Auto-generated for formal Phase1b r28 gate-SAIF replay.\n")
        f.write("// Contains r28 referenced ASAP7 cell modules plus ASAP7 UDP primitives.\n\n")
        for name in sorted(primitives):
            f.write(primitives[name])
            f.write("\n")
        for name in sorted(found):
            f.write(found[name])
            f.write("\n")
    write_json(
        build_root / "referenced_cell_library_manifest.json",
        {
            "gate_netlist": str(gate_netlist.resolve()),
            "asap7_verilog_dir": str(asap7_dir.resolve()),
            "used_cell_count": len(used),
            "used_cells": sorted(used),
            "resolved_cell_count": len(found),
            "included_udp_primitive_count": len(primitives),
            "included_udp_primitives": sorted(primitives),
            "missing_modules": missing,
            "library": str(lib_path.resolve()),
            "sources": {name: sources[name] for name in sorted(sources)},
        },
    )
    return [lib_path]


def run_logged(cmd: list[str], cwd: Path, log: Path, append: bool = False) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with log.open(mode, encoding="utf-8", errors="ignore") as f:
        if append:
            f.write("\n")
        f.write("$ " + " ".join(cmd) + "\n")
        f.flush()
        proc = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True)
        return proc.returncode


def function_spans(lines: list[str]) -> list[dict[str, object]]:
    spans = []
    start_re = re.compile(r"^(?:VL_ATTR_\w+\s+)*void\s+([A-Za-z_][\w:]*)\s*\(([^;]*?)\)\s*\{")
    i = 0
    while i < len(lines):
        m = start_re.match(lines[i])
        if not m:
            i += 1
            continue
        depth = lines[i].count("{") - lines[i].count("}")
        j = i + 1
        while j < len(lines) and depth > 0:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
        if depth == 0:
            signature = lines[i].strip()
            signature = signature.rsplit("{", 1)[0].strip()
            signature = re.sub(r"^VL_ATTR_\w+\s+", "", signature)
            spans.append({"name": m.group(1), "signature": signature, "start": i, "end": j})
            i = j
        else:
            i += 1
    return spans


def split_large_cpp_file(cpp: Path, build_dir: Path, parts: int = SPLIT_PARTS) -> dict[str, object] | None:
    size = cpp.stat().st_size
    if size <= SPLIT_THRESHOLD_BYTES or cpp.name.endswith(".phase1b_orig") or "_split_" in cpp.name:
        return None
    lines = cpp.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    spans = function_spans(lines)
    if len(spans) < 2:
        return {
            "source_cpp": str(cpp),
            "source_bytes": size,
            "status": "not_split",
            "reason": "fewer than two whole function spans found; manual single-function split may be required",
        }
    backup = cpp.with_suffix(cpp.suffix + ".phase1b_orig")
    if not backup.exists():
        shutil.copy2(cpp, backup)
    # Keep small files practical: chunk functions by total source bytes.
    funcs = []
    for span in spans:
        start = int(span["start"])
        end = int(span["end"])
        b = sum(len(x.encode("utf-8", errors="ignore")) for x in lines[start:end])
        funcs.append((span, b))
    target = max(1, sum(b for _, b in funcs) // parts)
    chunks: list[list[dict[str, object]]] = []
    cur: list[dict[str, object]] = []
    cur_bytes = 0
    for span, b in funcs:
        if cur and len(chunks) < parts - 1 and cur_bytes + b > target:
            chunks.append(cur)
            cur = []
            cur_bytes = 0
        cur.append(span)
        cur_bytes += b
    if cur:
        chunks.append(cur)
    moved_ids = {(int(s["start"]), int(s["end"])) for chunk in chunks for s in chunk}
    prototypes = [str(s["signature"]).rstrip() + ";\n" for chunk in chunks for s in chunk]
    base = cpp.stem
    helper_bases = []
    helper_files = []
    header = ["// Verilated -*- C++ -*-\n", "// DESCRIPTION: Phase1b whole-function split helper.\n", '#include "VGemmini__pch.h"\n', "\n", *prototypes, "\n"]
    for idx, chunk in enumerate(chunks):
        helper = cpp.with_name(f"{base}_split_{idx:03d}.cpp")
        helper_bases.append(helper.stem)
        helper_files.append(str(helper))
        body: list[str] = list(header)
        for span in chunk:
            body.extend(lines[int(span["start"]):int(span["end"])])
            body.append("\n")
        helper.write_text("".join(body), encoding="utf-8")
    # Rewrite original with moved function declarations and non-moved content.
    out: list[str] = []
    out.extend(lines[: int(spans[0]["start"])])
    out.append("\n// Phase1b split helper declarations.\n")
    out.extend(prototypes)
    out.append("\n")
    cursor = int(spans[0]["start"])
    for span in spans:
        start = int(span["start"])
        end = int(span["end"])
        if cursor < start:
            out.extend(lines[cursor:start])
        if (start, end) not in moved_ids:
            out.extend(lines[start:end])
        cursor = end
    out.extend(lines[cursor:])
    cpp.write_text("".join(out), encoding="utf-8")
    classes = build_dir / "VGemmini_classes.mk"
    classes_backup = classes.with_suffix(classes.suffix + ".phase1b_orig")
    if classes.exists():
        if not classes_backup.exists():
            shutil.copy2(classes, classes_backup)
        text = classes.read_text(encoding="utf-8", errors="ignore")
        needle = f"  {base} \\\n"
        repl = needle + "".join(f"  {hb} \\\n" for hb in helper_bases)
        if needle in text:
            text = text.replace(needle, repl, 1)
        else:
            text += "\nVM_CLASSES_FAST += \\\n" + "".join(f"  {hb} \\\n" for hb in helper_bases) + "\n"
        classes.write_text(text, encoding="utf-8")
    return {
        "source_cpp": str(cpp),
        "source_bytes": size,
        "backup_cpp": str(backup),
        "status": "split_whole_functions",
        "function_count": len(spans),
        "chunk_count": len(chunks),
        "helper_bases": helper_bases,
        "helper_files": helper_files,
        "classes_mk": str(classes),
    }


def split_large_cpp_files(build_dir: Path) -> list[dict[str, object]]:
    records = []
    for cpp in sorted(build_dir.glob("*.cpp")):
        record = split_large_cpp_file(cpp, build_dir)
        if record:
            records.append(record)
    if records:
        write_json(build_dir.parent / "split_manifest.json", {"threshold_bytes": SPLIT_THRESHOLD_BYTES, "records": records})
    return records


def make_cmd(args: argparse.Namespace, build_dir: Path) -> list[str]:
    return ["make", "-C", str(build_dir.resolve()), "-f", f"V{args.module}.mk", "-j", str(args.jobs), f"CXX={args.make_cxx}", f"LINK={args.make_link}"]


def build_if_needed(args: argparse.Namespace, ports: list[dict[str, object]], cpp_path: Path) -> dict[str, object]:
    build_root = args.build_root
    build_root.mkdir(parents=True, exist_ok=True)
    build_dir = build_root / "verilator_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    exe = build_dir / f"V{args.module}"
    build_log = build_root / "build.log"
    if args.skip_build_if_exists and exe.exists():
        inputs = [p for p in ports if p["direction"] == "input" and p["name"] != "clock"]
        cpp_policy = {
            "mode": "no-compare gate SAIF replay",
            "input_ports": [str(p["name"]) for p in inputs],
            "input_ports_total": len(inputs),
            "trace_depth": args.trace_depth,
            "input_drive_policy": "row N-1 input vector drives replay cycle N; trace decision uses row N time_ps",
        }
        return {"build_skipped": True, "executable": str(exe.resolve()), "cpp_policy": cpp_policy}
    cpp_policy = generate_cpp(args, ports, cpp_path)
    cell_files = write_referenced_cell_library(args.gate_netlist, args.asap7_verilog_dir, build_root)
    sram_files = [args.sram_model_dir / "mem_ext.sv", args.sram_model_dir / "mem_0_ext.sv"]
    for path in [args.gate_netlist, *cell_files, *sram_files, cpp_path]:
        if not Path(path).is_file():
            raise RuntimeError(f"missing input file: {path}")
    cmd = [
        "verilator",
        "--cc",
        "--exe",
        "--top-module",
        args.module,
        "--threads",
        str(args.verilator_threads),
        "--threads-dpi",
        "all",
        "--compiler",
        "clang",
        "--no-timing",
        "--trace-saif",
        "--trace-depth",
        str(args.trace_depth),
        "--output-split",
        str(args.output_split),
        "--output-split-cfuncs",
        str(args.output_split_cfuncs),
        "--output-split-ctrace",
        str(args.output_split_ctrace),
        "--Mdir",
        str(build_dir.resolve()),
        "--verilate-jobs",
        str(args.verilate_jobs),
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
    for flag in args.extra_verilator_flag:
        cmd.append(flag)
    if args.cflags:
        cmd.extend(["-CFLAGS", args.cflags])
    cmd.extend([str(args.gate_netlist.resolve()), *[str(path.resolve()) for path in sram_files], *[str(path.resolve()) for path in cell_files], str(cpp_path.resolve())])
    rc = run_logged(cmd, build_root, build_log)
    if rc != 0:
        write_json(build_root / "build_manifest.json", {"verilator_command": cmd, "verilator_returncode": rc, "build_log": str(build_log)})
        raise SystemExit(rc)
    split_records = [] if args.no_auto_split else split_large_cpp_files(build_dir)
    mcmd = make_cmd(args, build_dir)
    rc = run_logged(mcmd, build_root, build_log, append=True)
    manifest = {
        "verilator_command": cmd,
        "make_command": mcmd,
        "make_returncode": rc,
        "build_log": str(build_log),
        "executable": str(exe.resolve()),
        "cpp": str(cpp_path.resolve()),
        "cpp_policy": cpp_policy,
        "split_records": split_records,
        "parameters": {
            "verilate_jobs": args.verilate_jobs,
            "jobs": args.jobs,
            "verilator_threads": args.verilator_threads,
            "trace_depth": args.trace_depth,
            "output_split": args.output_split,
            "output_split_cfuncs": args.output_split_cfuncs,
            "output_split_ctrace": args.output_split_ctrace,
            "cflags": args.cflags,
            "compiler": "clang",
            "no_timing": True,
            "trace_saif": True,
            "hierarchical": False,
        },
    }
    write_json(build_root / "build_manifest.json", manifest)
    if rc != 0:
        raise SystemExit(rc)
    return {"build_skipped": False, **manifest}


def run_replay(args: argparse.Namespace) -> dict[str, object]:
    exe = args.build_root / "verilator_build" / f"V{args.module}"
    if not exe.is_file():
        raise RuntimeError(f"missing executable: {exe}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.out_dir / "replay_summary.json"
    run_log = args.out_dir / "replay_run.log"
    max_cycles = args.max_cycles if args.max_cycles is not None else -1
    cmd = [
        str(exe.resolve()),
        str(args.boundary_vectors.resolve()),
        str(args.emit_saif.resolve()),
        str(args.trace_start_ps),
        str(args.trace_end_ps),
        str(max_cycles),
        str(summary_path.resolve()),
        args.workload,
    ]
    rc = run_logged(cmd, args.out_dir, run_log)
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    saif_bytes = args.emit_saif.stat().st_size if args.emit_saif.exists() else 0
    summary["run_returncode"] = rc
    summary["run_log"] = str(run_log)
    summary["saif_bytes"] = saif_bytes
    summary["run_kind"] = args.run_kind
    write_json(summary_path, summary)
    manifest = {
        "workload": args.workload,
        "run_kind": args.run_kind,
        "gate_netlist": str(args.gate_netlist.resolve()),
        "boundary_map": str(args.boundary_map.resolve()),
        "boundary_vectors": str(args.boundary_vectors.resolve()),
        "saif": str(args.emit_saif.resolve()),
        "trace_start_ps": args.trace_start_ps,
        "trace_end_ps": args.trace_end_ps,
        "trace_interval": "trace_start_ps <= time_ps < trace_end_ps",
        "summary": summary,
        "phase3_consumable": args.run_kind == "formal" and rc == 0 and saif_bytes > 0 and int(summary.get("trace_enabled_cycles", 0)) > 0,
        "method": "no-compare Verilator zero-delay Gemmini boundary replay with direct SAIF trace",
    }
    write_json(args.out_dir / "gate_activity_manifest.json", manifest)
    report = args.out_dir / ("smoke_report.md" if args.run_kind == "smoke" else "replay_summary.md")
    report.write_text(
        f"# Phase1b Gate SAIF Replay: {args.workload}\n\n"
        f"- run kind: `{args.run_kind}`\n"
        f"- vectors: `{args.boundary_vectors}`\n"
        f"- SAIF: `{args.emit_saif}`\n"
        f"- trace window ps: `[{args.trace_start_ps}, {args.trace_end_ps})`\n"
        f"- cycles run: `{summary.get('cycles_run', 'unknown')}`\n"
        f"- trace enabled cycles: `{summary.get('trace_enabled_cycles', 'unknown')}`\n"
        f"- first trace time ps: `{summary.get('first_trace_time_ps', 'unknown')}`\n"
        f"- last trace time ps: `{summary.get('last_trace_time_ps', 'unknown')}`\n"
        f"- elapsed sec: `{summary.get('elapsed_sec', 'unknown')}`\n"
        f"- SAIF bytes: `{saif_bytes}`\n"
        f"- return code: `{rc}`\n\n"
        "This run does not perform output compare. It is Verilator zero-delay gate activity generation, not SDF timing simulation.\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    args = parse_args()
    mapping = read_json(args.boundary_map)
    ports = list(mapping["ports"])
    cpp_path = args.build_root / "tb_phase1b_gate_saif.cpp"
    build = build_if_needed(args, ports, cpp_path)
    run = run_replay(args)
    top_manifest = {"build": build, "run": run}
    write_json(args.out_dir / "phase1b_gate_saif_replay_manifest.json", top_manifest)
    print(json.dumps({"run_returncode": run["summary"].get("run_returncode"), "saif": run["saif"], "saif_bytes": run["summary"].get("saif_bytes")}, indent=2))
    raise SystemExit(int(run["summary"].get("run_returncode", 1)))


if __name__ == "__main__":
    main()
