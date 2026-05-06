#!/usr/bin/env python3
"""Gemmini Phase 2 startup entry for Cadence Genus/Innovus preparation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
CADENCE_STARTUP_ROOT = THIS_DIR.parents[1]
if str(CADENCE_STARTUP_ROOT) not in sys.path:
    sys.path.insert(0, str(CADENCE_STARTUP_ROOT))

from env import ASAP7_HOME, FAKE_SRAM_CACHE, GENUS_BIN, INNOVUS_BIN, RESULT_ROOT, RTL_FILELIST, RUN_ROOT, TP_ROOT
from manager.genus import GenusManager
from manager.innovus import InnovusManager
from tech.gemmini_asap7 import GemminiAsap7Library

TOP_MODULE = "Gemmini"
CLOCK_NAME = "clock"
CLOCK_PORT = "clock"
CLOCK_PERIOD_NS = 5.0
CONFIG_NAME = "GemminiRocketConfig"
SHAPE_NAME = "mesh16x16_tile1x1_dim16"
EXPECTED_PYTHON = Path(os.environ.get("CONDA_PREFIX", "/home/lisihang/miniconda3/envs/thermal_placement")) / "bin" / "python"
ENV_SETUP_SCRIPT = TP_ROOT / "tools" / "env_gemmini_thermal.sh"


def read_rtl_filelist(filelist: Path) -> list[str]:
    files: list[str] = []
    for raw in filelist.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith((".sv", ".v")) and Path(line).is_file():
            files.append(line)
    return files


def run_tag() -> str:
    explicit = os.environ.get("TP_STAGE2_RUN_TAG")
    if explicit:
        return explicit
    date_tag = os.environ.get("TP_STAGE2_RUN_DATE") or datetime.now().strftime("%Y%m%d")
    return f"gemmini_{SHAPE_NAME}_asap7sc7p5t28_fake_sram_200mhz_startup_{date_tag}"


def build_config() -> dict:
    tech = GemminiAsap7Library(
        pdk_dir=str(ASAP7_HOME),
        repo_root=TP_ROOT,
        fake_sram_cache=FAKE_SRAM_CACHE,
    ).to_dict()
    rtl_files = read_rtl_filelist(RTL_FILELIST)
    verilog_files = rtl_files + tech["fake_sram_stub_files"]
    tag = run_tag()
    rundir = RESULT_ROOT / tag
    return {
        "config_name": CONFIG_NAME,
        "shape_name": SHAPE_NAME,
        "top_module": TOP_MODULE,
        "clk_name": CLOCK_NAME,
        "clk_port_name": CLOCK_PORT,
        "clk_period_ns": CLOCK_PERIOD_NS,
        "run_root": str(RUN_ROOT),
        "rundir": str(rundir),
        "rtl_filelist": str(RTL_FILELIST),
        "rtl_file_count": len(rtl_files),
        "verilog_files": verilog_files,
        "genus_bin": str(GENUS_BIN),
        "innovus_bin": str(INNOVUS_BIN),
        "python_executable": sys.executable,
        "expected_python": str(EXPECTED_PYTHON),
        "env_setup_script": str(ENV_SETUP_SCRIPT),
        "max_threads": int(os.environ.get("TP_CADENCE_GENUS_CPUS", "8")),
        "innovus_threads": int(os.environ.get("TP_CADENCE_INNOVUS_CPUS", "8")),
        "route_max_threads": int(os.environ.get("TP_STAGE2_ROUTE_CPUS", "1")),
        "route_si_aware": os.environ.get("TP_STAGE2_ROUTE_SI_AWARE", "false").lower() in {"1", "true", "yes", "on"},
        **tech,
    }


def preflight(config: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required_files = [
        ("rtl_filelist", RTL_FILELIST),
        ("genus_bin", GENUS_BIN),
        ("innovus_bin", INNOVUS_BIN),
        ("env_setup_script", ENV_SETUP_SCRIPT),
    ]
    for key, path in required_files:
        if not Path(path).is_file():
            errors.append(f"missing {key}: {path}")
    if Path(sys.executable).resolve() != EXPECTED_PYTHON.resolve():
        errors.append(f"wrong python: {sys.executable}; expected {EXPECTED_PYTHON}")
    if config["rtl_file_count"] <= 0:
        errors.append(f"no RTL files resolved from {RTL_FILELIST}")
    for key in ("setup_lib_files", "hold_lib_files", "lef_files", "fake_sram_lib_files", "fake_sram_lef_files", "fake_sram_stub_files", "gds_files"):
        for path in config[key]:
            if not Path(path).is_file():
                errors.append(f"missing {key}: {path}")
    for key in ("qrc_techfiles",):
        for path in config[key]:
            if not Path(path).is_file():
                errors.append(f"missing {key}: {path}")
    if not Path(config["stream_layer_map"]).is_file():
        errors.append(f"missing stream_layer_map: {config['stream_layer_map']}")
    if abs(config["clk_period_ns"] - 5.0) > 1e-9:
        errors.append(f"unexpected clock period: {config['clk_period_ns']}")
    return not errors, errors


def print_summary(config: dict) -> None:
    print(f"python={config['python_executable']}")
    print(f"run_root={config['run_root']}")
    print(f"rundir={config['rundir']}")
    print(f"rtl_file_count={config['rtl_file_count']}")
    print(f"setup_lib_count={len(config['setup_lib_files'])}")
    print(f"lef_count={len(config['lef_files'])}")
    print(f"fake_sram_lib_count={len(config['fake_sram_lib_files'])}")
    print(f"fake_sram_lef_count={len(config['fake_sram_lef_files'])}")
    print(f"fake_sram_stub_count={len(config['fake_sram_stub_files'])}")
    print(f"gds_count={len(config['gds_files'])}")


def write_dry_run(config: dict, errors: list[str]) -> Path:
    rundir = Path(config["rundir"])
    startup_dir = rundir / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_startup_dry_run",
        "ok": not errors,
        "errors": errors,
        "config": config,
        "notes": [
            "No Cadence commercial tool was launched.",
            "Stage 2 results are staged under physical/<tag>/.",
            "Use --write-scripts to exercise the Python manager script-generation path without launching Genus or Innovus.",
        ],
    }
    out = startup_dir / "startup_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def build_genus_config(config: dict, runmode: str = "script_only", steps: list[str] | None = None) -> dict:
    return {
        **config,
        "rundir": str(Path(config["rundir"]) / "genus"),
        "runmode": runmode,
        "steps": steps or ["syn", "report"],
        "hdl_error_on_blackbox": True,
        "hdl_resolve_instance_with_libcell": True,
        "syn_generic_effort": "medium",
        "syn_map_effort": "high",
        "syn_opt_effort": "medium",
    }


def build_innovus_config(
    config: dict,
    genus_output: dict,
    runmode: str = "script_only",
    steps: list[str] | None = None,
) -> dict:
    return {
        **config,
        **genus_output,
        "rundir": str(Path(config["rundir"]) / "innovus"),
        "runmode": runmode,
        "steps": steps or ["init", "floorplan", "powerplan", "placement", "cts", "routing"],
        "max_threads": config["innovus_threads"],
    }


def find_genus_synthesis_run(config: dict) -> Path:
    explicit = os.environ.get("TP_STAGE2_GENUS_RUN_TAG")
    if explicit:
        candidate = RESULT_ROOT / explicit / "genus"
        return candidate

    candidates = []
    for netlist in RESULT_ROOT.glob("*/genus/data/Gemmini-mapped.v"):
        rundir = netlist.parents[1]
        setup_sdc = rundir / "data" / "constraint_setup.sdc"
        hold_sdc = rundir / "data" / "constraint_hold.sdc"
        if setup_sdc.is_file() and hold_sdc.is_file():
            candidates.append(rundir)
    if not candidates:
        raise FileNotFoundError("no completed Genus synthesis run found under physical/*/genus")
    return max(candidates, key=lambda path: (path / "data" / "Gemmini-mapped.v").stat().st_mtime)


def build_genus_output_from_run(config: dict, genus_rundir: Path) -> dict:
    genus_rundir = genus_rundir.resolve()
    output = {
        "verilog_file": str(genus_rundir / "data" / "Gemmini-mapped.v"),
        "top_module": TOP_MODULE,
        "setup_lib_files": config["setup_lib_files"],
        "hold_lib_files": config["hold_lib_files"],
        "lef_files": config["lef_files"],
        "qrc_techfiles": config["qrc_techfiles"],
        "cts_inv_cells": config.get("cts_inv_cells", []),
        "setup_sdc_file": str(genus_rundir / "data" / "constraint_setup.sdc"),
        "hold_sdc_file": str(genus_rundir / "data" / "constraint_hold.sdc"),
        "path_groups": [],
    }
    missing = [path for path in (output["verilog_file"], output["setup_sdc_file"], output["hold_sdc_file"]) if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError("missing Genus synthesis output(s): " + ", ".join(missing))
    return output


def parse_def_pin_status(def_path: Path) -> dict[str, Any]:
    in_pins = False
    total = 0
    placed = 0
    fixed = 0
    unplaced = 0
    examples: list[str] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush_pin() -> None:
        nonlocal total, placed, fixed, unplaced, current_name, current_lines
        if current_name is None:
            return
        total += 1
        body = " ".join(current_lines)
        if " + FIXED " in body:
            fixed += 1
        elif " + PLACED " in body:
            placed += 1
        else:
            unplaced += 1
            if len(examples) < 10:
                examples.append(current_name)
        current_name = None
        current_lines = []

    for raw in def_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("PINS "):
            in_pins = True
            continue
        if in_pins and line.startswith("END PINS"):
            flush_pin()
            break
        if not in_pins:
            continue
        if line.startswith("- "):
            flush_pin()
            parts = line.split()
            current_name = parts[1] if len(parts) > 1 else line
            current_lines = [f" {line} "]
        elif current_name is not None:
            current_lines.append(f" {line} ")
    return {
        "def_file": str(def_path),
        "total_pins": total,
        "placed_pins": placed,
        "fixed_pins": fixed,
        "unplaced_pins": unplaced,
        "unplaced_examples": examples,
        "ok": total > 0 and unplaced == 0,
    }


def write_manager_scripts(config: dict) -> Path:
    genus_manager = GenusManager(build_genus_config(config))
    genus_output = genus_manager.run()

    innovus_manager = InnovusManager(build_innovus_config(config, genus_output))
    innovus_output = innovus_manager.run()

    startup_dir = Path(config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_manager_script_generation",
        "ok": True,
        "notes": [
            "No Cadence commercial tool was launched.",
            "Genus and Innovus Tcl scripts were generated through the copied dacs-style managers.",
            "Commercial-tool launch remains a separate explicit step.",
        ],
        "genus_rundir": genus_manager.rundir,
        "innovus_rundir": innovus_manager.rundir,
        "genus_scripts": {
            "sdc": genus_manager.sdc_script_path,
            "mmmc": genus_manager.mmmc_script_path,
            "fused_syn": genus_manager.fused_syn_script_path,
        },
        "innovus_scripts": {
            "mmmc": innovus_manager.mmmc_script_path,
            "init": str(Path(innovus_manager.script_dir) / "init.tcl"),
            "floorplan": str(Path(innovus_manager.script_dir) / "floorplan.tcl"),
            "powerplan": str(Path(innovus_manager.script_dir) / "powerplan.tcl"),
            "placement": str(Path(innovus_manager.script_dir) / "placement.tcl"),
            "cts": str(Path(innovus_manager.script_dir) / "cts.tcl"),
            "routing": str(Path(innovus_manager.script_dir) / "routing.tcl"),
        },
        "expected_genus_output": genus_output,
        "expected_innovus_output": innovus_output,
    }
    out = startup_dir / "manager_script_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out



def run_genus_elab(config: dict) -> Path:
    genus_manager = GenusManager(build_genus_config(config, runmode="normal", steps=["elab"]))
    genus_output = genus_manager.run()

    startup_dir = Path(config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_genus_elaboration_smoke",
        "ok": True,
        "notes": [
            "Cadence Genus was launched through the Python manager.",
            "This frontend/elaboration smoke does not run synthesis.",
        ],
        "genus_rundir": genus_manager.rundir,
        "genus_output": genus_output,
        "check_design_report": genus_manager.check_design_report_path,
        "elab_qor_report": genus_manager.elab_qor_report_path,
    }
    out = startup_dir / "genus_elab_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def run_genus_syn(config: dict) -> Path:
    genus_manager = GenusManager(build_genus_config(config, runmode="normal", steps=["syn", "report"]))
    genus_output = genus_manager.run()

    startup_dir = Path(config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_genus_synthesis",
        "ok": True,
        "notes": [
            "Cadence Genus synthesis and reporting were launched through the Python manager.",
            "This step does not launch Innovus.",
        ],
        "genus_rundir": genus_manager.rundir,
        "genus_output": genus_output,
        "reports": {
            "timing": genus_manager.timing_report_path,
            "power": str(Path(genus_manager.report_dir) / "power.rpt"),
            "area": str(Path(genus_manager.report_dir) / "area.rpt"),
            "drc": str(Path(genus_manager.report_dir) / "drc.rpt"),
            "qor": str(Path(genus_manager.report_dir) / "qor.rpt"),
        },
        "scripts": {
            "sdc": genus_manager.sdc_script_path,
            "mmmc": genus_manager.mmmc_script_path,
            "syn": genus_manager.syn_script_path,
            "report": genus_manager.report_script_path,
        },
    }
    out = startup_dir / "genus_syn_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def run_innovus_floorplan_smoke(config: dict) -> Path:
    genus_rundir = find_genus_synthesis_run(config)
    genus_output = build_genus_output_from_run(config, genus_rundir)
    innovus_manager = InnovusManager(
        build_innovus_config(
            config,
            genus_output,
            runmode="normal",
            steps=["init", "floorplan"],
        )
    )
    innovus_output = innovus_manager.run()

    floorplan_def = Path(innovus_manager.floorplan_def_path)
    pin_status = parse_def_pin_status(floorplan_def) if floorplan_def.is_file() else {
        "def_file": str(floorplan_def),
        "ok": False,
        "error": "floorplan DEF was not produced",
    }
    if not pin_status.get("ok", False):
        raise RuntimeError(f"Innovus floorplan pin placement check failed: {pin_status}")

    startup_dir = Path(config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_innovus_floorplan_smoke",
        "ok": True,
        "notes": [
            "Cadence Innovus was launched through the Python manager.",
            "This smoke runs init and floorplan only; it does not run powerplan, placement, CTS, routing, extraction, or streamOut.",
            "Pin placement is checked by parsing the generated floorplan DEF PINS section.",
        ],
        "source_genus_rundir": str(genus_rundir),
        "genus_output": genus_output,
        "innovus_rundir": innovus_manager.rundir,
        "innovus_output": innovus_output,
        "pin_status": pin_status,
        "scripts": {
            "mmmc": innovus_manager.mmmc_script_path,
            "init": str(Path(innovus_manager.script_dir) / "init.tcl"),
            "floorplan": str(Path(innovus_manager.script_dir) / "floorplan.tcl"),
        },
        "logs": {
            "init": str(Path(innovus_manager.log_dir) / "init.log"),
            "floorplan": str(Path(innovus_manager.log_dir) / "floorplan.log"),
        },
    }
    out = startup_dir / "innovus_floorplan_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GemminiRocketConfig mesh16x16 Phase 2 startup")
    parser.add_argument("--preflight", action="store_true", help="Validate inputs and paths without writing outputs")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and write a startup manifest under physical/<tag>/startup")
    parser.add_argument("--write-scripts", action="store_true", help="Generate Genus/Innovus Tcl through manager/ without launching commercial tools")
    parser.add_argument("--run-genus-elab", action="store_true", help="Launch a Python-managed Genus frontend/elaboration smoke without synthesis")
    parser.add_argument("--run-genus-syn", action="store_true", help="Launch Python-managed Genus synthesis and reports without Innovus")
    parser.add_argument("--run-innovus-floorplan-smoke", action="store_true", help="Launch Python-managed Innovus init/floorplan smoke from a completed Genus synthesis run")
    parser.add_argument("--print-config", action="store_true", help="Print resolved startup config as JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = build_config()
    ok, errors = preflight(config)
    if args.print_config:
        print(json.dumps(config, indent=2))
    if args.preflight or args.dry_run or args.write_scripts or args.run_genus_elab or args.run_genus_syn or args.run_innovus_floorplan_smoke:
        print_summary(config)
        if args.dry_run:
            print(f"manifest={write_dry_run(config, errors)}")
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        if args.write_scripts:
            print(f"manager_manifest={write_manager_scripts(config)}")
        if args.run_genus_elab:
            print(f"genus_elab_manifest={run_genus_elab(config)}")
        if args.run_genus_syn:
            print(f"genus_syn_manifest={run_genus_syn(config)}")
        if args.run_innovus_floorplan_smoke:
            print(f"innovus_floorplan_manifest={run_innovus_floorplan_smoke(config)}")
        print("preflight_ok=True")
        return 0
    print("No action requested. Use --preflight, --dry-run, --write-scripts, --run-genus-elab, --run-genus-syn, --run-innovus-floorplan-smoke, or --print-config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
