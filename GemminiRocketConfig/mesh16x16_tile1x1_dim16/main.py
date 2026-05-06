#!/usr/bin/env python3
"""Gemmini Phase 2 startup entry for Cadence Genus/Innovus preparation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
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


def build_genus_config(config: dict) -> dict:
    return {
        **config,
        "rundir": str(Path(config["rundir"]) / "genus"),
        "runmode": "script_only",
        "steps": ["syn", "report"],
        "hdl_error_on_blackbox": True,
        "hdl_resolve_instance_with_libcell": True,
        "syn_generic_effort": "medium",
        "syn_map_effort": "high",
        "syn_opt_effort": "medium",
    }


def build_innovus_config(config: dict, genus_output: dict) -> dict:
    return {
        **config,
        **genus_output,
        "rundir": str(Path(config["rundir"]) / "innovus"),
        "runmode": "script_only",
        "steps": ["init", "floorplan", "powerplan", "placement", "cts", "routing"],
        "max_threads": config["innovus_threads"],
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GemminiRocketConfig mesh16x16 Phase 2 startup")
    parser.add_argument("--preflight", action="store_true", help="Validate inputs and paths without writing outputs")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and write a startup manifest under physical/<tag>/startup")
    parser.add_argument("--write-scripts", action="store_true", help="Generate Genus/Innovus Tcl through manager/ without launching commercial tools")
    parser.add_argument("--print-config", action="store_true", help="Print resolved startup config as JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = build_config()
    ok, errors = preflight(config)
    if args.print_config:
        print(json.dumps(config, indent=2))
    if args.preflight or args.dry_run or args.write_scripts:
        print_summary(config)
        if args.dry_run:
            print(f"manifest={write_dry_run(config, errors)}")
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        if args.write_scripts:
            print(f"manager_manifest={write_manager_scripts(config)}")
        print("preflight_ok=True")
        return 0
    print("No action requested. Use --preflight, --dry-run, --write-scripts, or --print-config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
