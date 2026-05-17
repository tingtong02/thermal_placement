#!/usr/bin/env python3
"""Harness-only binary Phase1b gate-SAIF replay acceleration.

This script does not run the Verilator frontend and does not compile generated
VGemmini*.o files. It compiles a new binary-input harness and relinks it with
existing r28 generated objects/archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

FORMAT = "phase1b_binary_boundary_vectors_acceleration"
VERSION = 1
DEFAULT_MAIN_ROOT = Path("runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515")
DEFAULT_ACCEL_ROOT = DEFAULT_MAIN_ROOT / "accelerate"
DEFAULT_MODULE = "Gemmini"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-root", type=Path, default=DEFAULT_MAIN_ROOT)
    parser.add_argument("--accelerate-root", type=Path, default=DEFAULT_ACCEL_ROOT)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--run-kind", choices=["smoke", "formal"], required=True)
    parser.add_argument("--trace-start-ps", required=True, type=int)
    parser.add_argument("--trace-end-ps", required=True, type=int)
    parser.add_argument("--max-cycles", type=int, default=None)
    parser.add_argument("--module", default=DEFAULT_MODULE)
    parser.add_argument("--trace-depth", type=int, default=9)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--run-only", action="store_true")
    parser.add_argument("--skip-relink-if-exists", action="store_true")
    parser.add_argument("--cxx", default="clang++")
    parser.add_argument("--cflags", default="-O0 -g0")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def file_info(path: Path) -> dict[str, object]:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    st = path.stat()
    return {"path": str(path.resolve()), "bytes": st.st_size, "mtime": st.st_mtime, "sha256": h.hexdigest()}


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


def c_string(value: str) -> str:
    return json.dumps(value)


def load_ports(accel_root: Path, workload: str) -> list[dict[str, object]]:
    layout_path = accel_root / workload / "boundary_vectors_binary_layout.json"
    if layout_path.is_file():
        layout = read_json(layout_path)
        return list(layout["ports"])
    map_path = accel_root / workload / "boundary_signal_map.json"
    data = read_json(map_path)
    ports = []
    offset = 16
    for csv_col, p in enumerate([x for x in data["ports"] if x.get("direction") == "input" and x.get("name") != "clock"], start=4):
        width = int(p["width"])
        if width <= 64:
            storage = "uint64"
            word_count = 1
            size = 8
        else:
            storage = "uint32_words_lsb_first"
            word_count = (width + 31) // 32
            size = 4 * word_count
        ports.append({"name": str(p["name"]), "width": width, "csv_column": csv_col, "storage": storage, "word_count": word_count, "offset": offset})
        offset += size
    return ports


def generate_cpp(cpp_path: Path, ports: list[dict[str, object]], trace_depth: int) -> None:
    row_bytes = max(int(p["offset"]) + (8 if p["storage"] == "uint64" else 4 * int(p["word_count"])) for p in ports) if ports else 16
    lines: list[str] = []
    lines.extend([
        '#include "VGemmini.h"',
        '#include "verilated.h"',
        '#include "verilated_saif_c.h"',
        '#include <algorithm>',
        '#include <chrono>',
        '#include <cstdint>',
        '#include <cstring>',
        '#include <fstream>',
        '#include <iomanip>',
        '#include <iostream>',
        '#include <sstream>',
        '#include <string>',
        '#include <vector>',
        '',
        'static constexpr const char* kFormat = "phase1b_binary_boundary_vectors_acceleration";',
        'static constexpr uint32_t kVersion = 1;',
        'static constexpr uint32_t kHeaderBytes = 48;',
        f'static constexpr uint32_t kPortCount = {len(ports)};',
        f'static constexpr uint32_t kRowBytes = {row_bytes};',
        'static constexpr char kMagic[16] = {\'T\',\'P\',\'P\',\'1\',\'B\',\'_\',\'B\',\'I\',\'N\',\'V\',\'E\',\'C\',0,0,0,0};',
        '',
        'struct PortLayout { const char* name; uint32_t width; const char* storage; uint32_t word_count; uint32_t offset; };',
        'static const PortLayout kPorts[] = {',
    ])
    for p in ports:
        lines.append(f'  {{{c_string(str(p["name"]))}, {int(p["width"])}, {c_string(str(p["storage"]))}, {int(p["word_count"])}, {int(p["offset"])} }},')
    lines.extend([
        '};',
        '',
        'static uint32_t load_le32(const char* p) {',
        '  const unsigned char* b = reinterpret_cast<const unsigned char*>(p);',
        '  return (uint32_t)b[0] | ((uint32_t)b[1] << 8) | ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);',
        '}',
        'static uint64_t load_le64(const char* p) {',
        '  uint64_t lo = load_le32(p);',
        '  uint64_t hi = load_le32(p + 4);',
        '  return lo | (hi << 32);',
        '}',
        'static int64_t load_le_i64(const char* p) { return static_cast<int64_t>(load_le64(p)); }',
        '',
        'static bool contains(const std::string& haystack, const std::string& needle) { return haystack.find(needle) != std::string::npos; }',
        'static std::string json_pair_str(const std::string& key, const std::string& value) { return "\\\"" + key + "\\\": \\\"" + value + "\\\""; }',
        'static std::string json_pair_num(const std::string& key, uint64_t value) { return "\\\"" + key + "\\\": " + std::to_string(value); }',
        'static bool validate_layout_json(const std::string& path, uint64_t header_row_count) {',
        '  std::ifstream in(path);',
        '  if (!in) { std::cerr << "failed to open layout JSON: " << path << "\\n"; return false; }',
        '  std::ostringstream ss; ss << in.rdbuf();',
        '  const std::string text = ss.str();',
        '  if (!contains(text, json_pair_str("format", kFormat))) { std::cerr << "layout format mismatch\\n"; return false; }',
        '  if (!contains(text, json_pair_num("version", kVersion))) { std::cerr << "layout version mismatch\\n"; return false; }',
        '  if (!contains(text, json_pair_str("endianness", "little"))) { std::cerr << "layout endianness mismatch\\n"; return false; }',
        '  if (!contains(text, json_pair_num("row_bytes", kRowBytes))) { std::cerr << "layout row_bytes mismatch\\n"; return false; }',
        '  if (!contains(text, json_pair_num("port_count", kPortCount))) { std::cerr << "layout port_count mismatch\\n"; return false; }',
        '  if (!contains(text, json_pair_num("row_count", header_row_count))) { std::cerr << "layout row_count mismatch with binary header\\n"; return false; }',
        '  for (uint32_t i = 0; i < kPortCount; ++i) {',
        '    const PortLayout& p = kPorts[i];',
        '    if (!contains(text, json_pair_str("name", p.name))) { std::cerr << "layout missing port name: " << p.name << "\\n"; return false; }',
        '    if (!contains(text, json_pair_num("width", p.width))) { std::cerr << "layout width mismatch near port: " << p.name << "\\n"; return false; }',
        '    if (!contains(text, json_pair_str("storage", p.storage))) { std::cerr << "layout storage mismatch near port: " << p.name << "\\n"; return false; }',
        '    if (!contains(text, json_pair_num("word_count", p.word_count))) { std::cerr << "layout word_count mismatch near port: " << p.name << "\\n"; return false; }',
        '    if (!contains(text, json_pair_num("offset", p.offset))) { std::cerr << "layout offset mismatch near port: " << p.name << "\\n"; return false; }',
        '  }',
        '  return true;',
        '}',
        '',
        'static std::string json_escape(const std::string& value) {',
        '  std::string out;',
        '  for (char c : value) {',
        '    if (c == \'\\\\\') out += "\\\\\\\\";',
        '    else if (c == \'"\') out += "\\\\\\\"";',
        '    else if (c == \'\\n\') out += "\\\\n";',
        '    else out += c;',
        '  }',
        '  return out;',
        '}',
        '',
        'static void assign_wide(uint32_t* dest, const char* src, uint32_t words) {',
        '  for (uint32_t i = 0; i < words; ++i) dest[i] = load_le32(src + 4 * i);',
        '}',
        '',
        'static void apply_inputs(VGemmini* top, const std::vector<char>& row) {',
    ])
    for p in ports:
        name = str(p["name"])
        width = int(p["width"])
        off = int(p["offset"])
        if width <= 64:
            lines.append(f'  top->{name} = static_cast<{cpp_type(width)}>(load_le64(row.data() + {off}));')
        else:
            lines.append(f'  assign_wide(top->{name}, row.data() + {off}, {int(p["word_count"])});')
    lines.extend([
        '}',
        '',
        'int main(int argc, char** argv) {',
        '  Verilated::commandArgs(argc, argv);',
        '  if (argc < 9) {',
        '    std::cerr << "usage: sim vectors.bin layout.json saif trace_start_ps trace_end_ps max_cycles summary.json workload\\n";',
        '    return 2;',
        '  }',
        '  const std::string vector_path = argv[1];',
        '  const std::string layout_path = argv[2];',
        '  const std::string saif_path = argv[3];',
        '  const long long trace_start_ps = std::stoll(argv[4]);',
        '  const long long trace_end_ps = std::stoll(argv[5]);',
        '  const long long max_cycles = std::stoll(argv[6]);',
        '  const std::string summary_path = argv[7];',
        '  const std::string workload = argv[8];',
        '  if (trace_end_ps <= trace_start_ps) { std::cerr << "invalid trace window\\n"; return 2; }',
        '  std::ifstream vin(vector_path, std::ios::binary);',
        '  if (!vin) { std::cerr << "failed to open binary vectors: " << vector_path << "\\n"; return 2; }',
        '  char header[48];',
        '  if (!vin.read(header, 48)) { std::cerr << "failed to read binary header\\n"; return 2; }',
        '  if (std::memcmp(header, kMagic, 16) != 0) { std::cerr << "binary magic mismatch\\n"; return 2; }',
        '  const uint32_t version = load_le32(header + 16);',
        '  const uint32_t header_bytes = load_le32(header + 20);',
        '  const uint64_t row_count_header = load_le64(header + 24);',
        '  const uint32_t port_count_header = load_le32(header + 32);',
        '  const uint32_t row_bytes_header = load_le32(header + 36);',
        '  if (version != kVersion || header_bytes != kHeaderBytes || port_count_header != kPortCount || row_bytes_header != kRowBytes) {',
        '    std::cerr << "binary header mismatch version/header_bytes/port_count/row_bytes"',
        '              << " version=" << version << " header_bytes=" << header_bytes',
        '              << " port_count=" << port_count_header << " row_bytes=" << row_bytes_header << "\\n";',
        '    return 2;',
        '  }',
        '  if (!validate_layout_json(layout_path, row_count_header)) return 2;',
        '  std::vector<char> prev(kRowBytes);',
        '  std::vector<char> cur(kRowBytes);',
        '  if (row_count_header < 2) { std::cerr << "binary row_count < 2\\n"; return 2; }',
        '  if (!vin.read(prev.data(), kRowBytes)) { std::cerr << "missing initial binary row\\n"; return 2; }',
        '  VGemmini* top = new VGemmini;',
        '  Verilated::traceEverOn(true);',
        '  VerilatedSaifC* tfp = new VerilatedSaifC;',
        f'  top->trace(tfp, {trace_depth});',
        '  tfp->open(saif_path.c_str());',
        '  std::cerr << "[start] workload=" << workload << " vectors=" << vector_path << " layout=" << layout_path << " saif=" << saif_path',
        '            << " trace_start_ps=" << trace_start_ps << " trace_end_ps=" << trace_end_ps',
        '            << " rows=" << row_count_header << " row_bytes=" << kRowBytes << "\\n";',
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
        '  auto last_progress_time = start_time;',
        '  for (uint64_t row_index = 1; row_index < row_count_header; ++row_index) {',
        '    if (max_cycles >= 0 && cycles >= max_cycles) break;',
        '    if (!vin.read(cur.data(), kRowBytes)) { std::cerr << "truncated binary row at index " << row_index << "\\n"; return 2; }',
        '    const long long row_cycle = static_cast<long long>(load_le64(cur.data()));',
        '    const long long time_ps = load_le_i64(cur.data() + 8);',
        '    const bool trace_on = (time_ps >= trace_start_ps && time_ps < trace_end_ps);',
        '    apply_inputs(top, prev);',
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
        '    const auto now = std::chrono::steady_clock::now();',
        '    const double since_progress = std::chrono::duration<double>(now - last_progress_time).count();',
        '    if (since_progress >= 60.0) {',
        '      const double elapsed = std::chrono::duration<double>(now - start_time).count();',
        '      const double cps = elapsed > 0 ? cycles / elapsed : 0.0;',
        '      double progress = 0.0;',
        '      if (time_ps >= trace_start_ps) progress = static_cast<double>(time_ps - trace_start_ps) / static_cast<double>(trace_end_ps - trace_start_ps);',
        '      if (progress < 0.0) progress = 0.0; if (progress > 1.0) progress = 1.0;',
        '      std::cerr << "[progress] workload=" << workload << " cycles_run=" << cycles << " row_cycle=" << row_cycle',
        '                << " time_ps=" << time_ps << " trace_enabled_cycles=" << trace_enabled_cycles',
        '                << " elapsed_sec=" << elapsed << " cycles_per_sec=" << cps',
        '                << " trace_window_progress=" << progress << "\\n";',
        '      last_progress_time = now;',
        '    }',
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
        '  summary << "  \\\"layout_path\\\": \\\"" << json_escape(layout_path) << "\\\",\\n";',
        '  summary << "  \\\"saif_path\\\": \\\"" << json_escape(saif_path) << "\\\",\\n";',
        '  summary << "  \\\"trace_start_ps\\\": " << trace_start_ps << ",\\n";',
        '  summary << "  \\\"trace_end_ps\\\": " << trace_end_ps << ",\\n";',
        '  summary << "  \\\"binary_row_count\\\": " << row_count_header << ",\\n";',
        '  summary << "  \\\"binary_row_bytes\\\": " << kRowBytes << ",\\n";',
        '  summary << "  \\\"cycles_run\\\": " << cycles << ",\\n";',
        '  summary << "  \\\"rows_seen\\\": " << rows_seen << ",\\n";',
        '  summary << "  \\\"last_time_ps\\\": " << last_time_ps << ",\\n";',
        '  summary << "  \\\"trace_enabled_cycles\\\": " << trace_enabled_cycles << ",\\n";',
        '  summary << "  \\\"first_trace_cycle\\\": "; if (first_trace_cycle < 0) summary << "null"; else summary << first_trace_cycle; summary << ",\\n";',
        '  summary << "  \\\"first_trace_time_ps\\\": "; if (first_trace_time_ps < 0) summary << "null"; else summary << first_trace_time_ps; summary << ",\\n";',
        '  summary << "  \\\"last_trace_cycle\\\": "; if (last_trace_cycle < 0) summary << "null"; else summary << last_trace_cycle; summary << ",\\n";',
        '  summary << "  \\\"last_trace_time_ps\\\": "; if (last_trace_time_ps < 0) summary << "null"; else summary << last_trace_time_ps; summary << ",\\n";',
        '  summary << "  \\\"elapsed_sec\\\": " << elapsed << ",\\n";',
        '  summary << "  \\\"cycles_per_sec\\\": " << (elapsed > 0 ? cycles / elapsed : 0.0) << "\\n";',
        '  summary << "}\\n";',
        '  std::cerr << "[finish] cycles=" << cycles << " trace_enabled_cycles=" << trace_enabled_cycles << " elapsed_sec=" << elapsed << "\\n";',
        '  return trace_enabled_cycles > 0 ? 0 : 3;',
        '}',
    ])
    cpp_path.parent.mkdir(parents=True, exist_ok=True)
    cpp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_logged(cmd: list[str], cwd: Path, log: Path, append: bool = False) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with log.open(mode, encoding="utf-8", errors="ignore") as f:
        if append:
            f.write("\n")
        f.write("$ " + " ".join(cmd) + "\n")
        f.flush()
        proc = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True)
        f.write(f"\n[returncode] {proc.returncode}\n")
        return proc.returncode


def build(args: argparse.Namespace) -> dict[str, object]:
    accel_root = args.accelerate_root.resolve()
    build_dir = accel_root / "build"
    main_build = args.main_root.resolve() / "build" / "verilator_build"
    exe = build_dir / "VGemmini_accelerate"
    cpp = build_dir / "tb_phase1b_gate_saif_binary.cpp"
    obj = build_dir / "tb_phase1b_gate_saif_binary.o"
    log = build_dir / "harness_build.log"
    archive = main_build / "VGemmini__ALL.a"
    runtime_objs = [main_build / "verilated.o", main_build / "verilated_saif_c.o", main_build / "verilated_threads.o"]
    for path in [archive, *runtime_objs, main_build / "VGemmini.h"]:
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"missing required build input: {path}")
    ports = load_ports(accel_root, args.workload)
    generate_cpp(cpp, ports, args.trace_depth)
    if args.skip_relink_if_exists and exe.is_file() and exe.stat().st_size > 0:
        manifest = {"status": "skipped_existing", "accelerated_executable": str(exe), "frontend_rerun": False, "generated_objects_recompiled": False, "harness_only_relink": True}
        write_json(build_dir / "harness_relink_manifest.json", manifest)
        return manifest
    cflags = args.cflags.split() if args.cflags else []
    verilator_root = Path(os.environ.get("VERILATOR_ROOT", "/home/lisihang/thermal_placement/tools/verilator/share/verilator"))
    include_dir = verilator_root / "include"
    compile_cmd = [args.cxx, "-I", str(main_build), "-I", str(include_dir), *cflags, "-c", str(cpp), "-o", str(obj)]
    rc_compile = run_logged(compile_cmd, Path.cwd(), log)
    if rc_compile != 0:
        manifest = {"status": "compile_failed", "compile_command": compile_cmd, "compile_returncode": rc_compile, "frontend_rerun": False, "generated_objects_recompiled": False, "harness_only_relink": True}
        write_json(build_dir / "harness_relink_manifest.json", manifest)
        raise SystemExit(rc_compile)
    link_cmd = [args.cxx, str(obj), *[str(p) for p in runtime_objs], str(archive), "-pthread", "-lpthread", "-latomic", "-o", str(exe)]
    rc_link = run_logged(link_cmd, Path.cwd(), log, append=True)
    status = "ok" if rc_link == 0 else "link_failed"
    manifest = {
        "status": status,
        "created_utc": utc_now(),
        "frontend_rerun": False,
        "generated_objects_recompiled": False,
        "harness_only_relink": True,
        "base_generated_archive": file_info(archive),
        "base_verilator_runtime_objects": [file_info(p) for p in runtime_objs],
        "source_harness": file_info(cpp),
        "harness_object": file_info(obj) if obj.is_file() else None,
        "accelerated_executable": file_info(exe) if exe.is_file() else {"path": str(exe.resolve()), "bytes": 0},
        "compile_command": compile_cmd,
        "compile_returncode": rc_compile,
        "link_command": link_cmd,
        "link_returncode": rc_link,
        "trace_depth": args.trace_depth,
        "port_count": len(ports),
        "build_log": str(log.resolve()),
    }
    write_json(build_dir / "harness_relink_manifest.json", manifest)
    if rc_link != 0:
        raise SystemExit(rc_link)
    return manifest


def run_replay(args: argparse.Namespace) -> dict[str, object]:
    accel_root = args.accelerate_root.resolve()
    run_dir = accel_root / args.workload
    exe = accel_root / "build" / "VGemmini_accelerate"
    vectors = run_dir / "boundary_vectors.bin"
    layout = run_dir / "boundary_vectors_binary_layout.json"
    summary_path = run_dir / "replay_summary.json"
    run_log = run_dir / "replay_run.log"
    saif = run_dir / ("mvin_mvout.gate.saif" if args.workload == "smoke_mvin_mvout_100cyc" else f"{args.workload}.gate.saif")
    for path in [exe, vectors, layout]:
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"missing run input: {path}")
    max_cycles = args.max_cycles if args.max_cycles is not None else -1
    cmd = [str(exe), str(vectors), str(layout), str(saif), str(args.trace_start_ps), str(args.trace_end_ps), str(max_cycles), str(summary_path), args.workload]
    started = time.time()
    rc = run_logged(cmd, Path.cwd(), run_log)
    elapsed_driver = time.time() - started
    summary = read_json(summary_path) if summary_path.is_file() else {}
    saif_bytes = saif.stat().st_size if saif.exists() else 0
    summary.update({
        "run_returncode": rc,
        "run_kind": args.run_kind,
        "run_log": str(run_log.resolve()),
        "saif_bytes": saif_bytes,
        "driver_elapsed_sec": elapsed_driver,
        "accelerated_executable": str(exe.resolve()),
    })
    write_json(summary_path, summary)
    manifest = {
        "workload": args.workload,
        "run_kind": args.run_kind,
        "method": "harness-only binary/preparsed Verilator zero-delay Gemmini boundary replay with direct SAIF trace",
        "compare": False,
        "phase3_consumable": args.run_kind == "formal" and rc == 0 and saif_bytes > 0 and int(summary.get("trace_enabled_cycles", 0)) > 0,
        "binary_vectors": str(vectors.resolve()),
        "binary_layout": str(layout.resolve()),
        "binary_manifest": str((run_dir / "boundary_vectors_binary_manifest.json").resolve()),
        "saif": str(saif.resolve()),
        "summary": summary,
        "trace_start_ps": args.trace_start_ps,
        "trace_end_ps": args.trace_end_ps,
        "executable": str(exe.resolve()),
    }
    write_json(run_dir / "gate_activity_manifest.json", manifest)
    report = run_dir / ("smoke_report.md" if args.run_kind == "smoke" else "replay_summary.md")
    report.write_text(
        f"# Phase1b Accelerated Gate SAIF Replay: {args.workload}\n\n"
        f"- run kind: `{args.run_kind}`\n"
        f"- executable: `{exe}`\n"
        f"- binary vectors: `{vectors}`\n"
        f"- SAIF: `{saif}`\n"
        f"- trace window ps: `[{args.trace_start_ps}, {args.trace_end_ps})`\n"
        f"- cycles run: `{summary.get('cycles_run', 'unknown')}`\n"
        f"- trace enabled cycles: `{summary.get('trace_enabled_cycles', 'unknown')}`\n"
        f"- elapsed sec: `{summary.get('elapsed_sec', 'unknown')}`\n"
        f"- cycles/sec: `{summary.get('cycles_per_sec', 'unknown')}`\n"
        f"- SAIF bytes: `{saif_bytes}`\n"
        f"- return code: `{rc}`\n\n"
        "This accelerated run uses binary/preparsed inputs only. It does not perform output compare and is not SDF timing simulation.\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_returncode": rc, "saif": str(saif), "saif_bytes": saif_bytes, "trace_enabled_cycles": summary.get("trace_enabled_cycles")}, indent=2), flush=True)
    if rc != 0:
        raise SystemExit(rc)
    if int(summary.get("trace_enabled_cycles", 0)) <= 0 or saif_bytes <= 0:
        raise SystemExit(3)
    return manifest


def main() -> None:
    args = parse_args()
    if args.build_only and args.run_only:
        raise SystemExit("--build-only and --run-only are mutually exclusive")
    build_manifest = None
    run_manifest = None
    if not args.run_only:
        build_manifest = build(args)
    if not args.build_only:
        run_manifest = run_replay(args)
    if build_manifest is not None or run_manifest is not None:
        write_json(args.accelerate_root / "phase1b_gate_saif_accelerated_run_plan.json", {
            "updated_utc": utc_now(),
            "last_workload": args.workload,
            "last_run_kind": args.run_kind,
            "build": build_manifest,
            "run": run_manifest,
            "adoption_status": "acceleration_attempt_only_not_default",
        })


if __name__ == "__main__":
    main()
