#!/usr/bin/env python3
"""Validate Stage 1b gate replay inputs before dynamic Verilator replay."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from phase1b_gate_replay_common import parse_module_ports, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-netlist", required=True, type=Path)
    parser.add_argument("--asap7-verilog-dir", required=True, type=Path)
    parser.add_argument("--sram-model-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--module", default="Gemmini")
    parser.add_argument("--skip-verilator-lint", action="store_true")
    parser.add_argument("--lint-timeout-sec", type=int, default=900)
    return parser.parse_args()


def find_files(args: argparse.Namespace) -> tuple[list[Path], list[Path]]:
    cell_files = sorted(args.asap7_verilog_dir.glob("*.v"))
    sram_files = [args.sram_model_dir / "mem_ext.sv", args.sram_model_dir / "mem_0_ext.sv"]
    missing = [path for path in [args.gate_netlist, *sram_files] if not path.is_file()]
    if missing:
        raise RuntimeError("missing required gate replay input(s): " + ", ".join(str(path) for path in missing))
    if not cell_files:
        raise RuntimeError(f"no ASAP7 Verilog files found under {args.asap7_verilog_dir}")
    return cell_files, sram_files


def run_lint(args: argparse.Namespace, cell_files: list[Path], sram_files: list[Path]) -> dict[str, object]:
    lint_log = args.out_dir / "verilator_lint.log"
    cmd = [
        "verilator",
        "--lint-only",
        "--timing",
        "--top-module",
        args.module,
        "-Wno-SPECIFYIGN",
        "-Wno-TIMESCALEMOD",
        "-Wno-MULTITOP",
        "-Wno-DECLFILENAME",
        "-Wno-PINCONNECTEMPTY",
        "-Wno-UNOPTFLAT",
        "-Wno-WIDTHEXPAND",
        "-Wno-WIDTHTRUNC",
        str(args.gate_netlist.resolve()),
        *[str(path.resolve()) for path in sram_files],
        *[str(path.resolve()) for path in cell_files],
    ]
    try:
        proc = subprocess.run(cmd, cwd=args.out_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=args.lint_timeout_sec)
        output = proc.stdout
        timed_out = False
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        timed_out = True
        returncode = 124
    lint_log.write_text(output, encoding="utf-8", errors="ignore")
    return {"command": cmd, "returncode": returncode, "timed_out": timed_out, "log": str(lint_log)}


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ports = parse_module_ports(args.gate_netlist, args.module)
    cell_files, sram_files = find_files(args)
    lint = {"skipped": True}
    if not args.skip_verilator_lint:
        lint = run_lint(args, cell_files, sram_files)

    manifest = {
        "module": args.module,
        "gate_netlist": str(args.gate_netlist.resolve()),
        "asap7_verilog_dir": str(args.asap7_verilog_dir),
        "asap7_verilog_files": [str(path.resolve()) for path in cell_files],
        "sram_model_files": [str(path.resolve()) for path in sram_files],
        "ports": len(ports),
        "input_ports": sum(1 for port in ports if port.direction == "input"),
        "output_ports": sum(1 for port in ports if port.direction == "output"),
        "max_port_width": max(port.width for port in ports),
        "verilator_lint": lint,
        "method_limitations": [
            "Verilator lint/replay is zero-delay functional validation.",
            "SDF and specify timing are not consumed by Verilator for Phase1b.",
            "The SRAM models in collateral/gate_sim/fake_sram are simulation-only and deterministic zero-init.",
        ],
    }
    write_json(args.out_dir / "gate_sim_input_manifest.json", manifest)
    status = "skipped" if lint.get("skipped") else ("pass" if lint.get("returncode") == 0 else "fail")
    report = args.out_dir / "gate_sim_input_validation_report.md"
    report.write_text(
        "# Phase1b Gate Simulation Input Validation\n\n"
        f"- gate netlist: `{args.gate_netlist}`\n"
        f"- ASAP7 Verilog files: `{len(cell_files)}`\n"
        f"- SRAM behavioral models: `{len(sram_files)}`\n"
        f"- Gemmini ports: `{len(ports)}`\n"
        f"- Verilator lint: `{status}`\n"
        f"- lint log: `{lint.get('log', '')}`\n\n"
        "Limitations: Verilator does not provide SDF timing simulation here; this is zero-delay functional replay only.\n",
        encoding="utf-8",
    )
    print(json.dumps({"verilator_lint": status, "manifest": str(args.out_dir / "gate_sim_input_manifest.json")}, indent=2))
    if lint.get("returncode", 0) != 0 and not lint.get("skipped"):
        raise SystemExit(int(lint.get("returncode", 1)))


if __name__ == "__main__":
    main()
