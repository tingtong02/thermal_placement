#!/usr/bin/env python3
"""Gemmini Phase 2 startup entry for Cadence Genus/Innovus preparation."""

from __future__ import annotations

import argparse
import json
import os
import re
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
    config = {
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
        "droute_end_iteration": int(os.environ.get("TP_STAGE2_DROUTE_END_ITERATION", "20")),
        "droute_fix_antenna": os.environ.get("TP_STAGE2_DROUTE_FIX_ANTENNA", "true").lower() in {"1", "true", "yes", "on"},
        "droute_multicut_via_effort": os.environ.get("TP_STAGE2_DROUTE_MULTICUT_VIA_EFFORT", "medium"),
        "droute_min_slack_for_wire_optimization": float(os.environ.get("TP_STAGE2_DROUTE_MIN_SLACK", "0.1")),
        "place_global_timing_effort": os.environ.get("TP_STAGE2_PLACE_TIMING_EFFORT", "medium"),
        "place_global_cong_effort": os.environ.get("TP_STAGE2_PLACE_CONG_EFFORT", "auto"),
        "place_detail_wire_length_opt_effort": os.environ.get("TP_STAGE2_PLACE_DETAIL_WIRE_EFFORT", "medium"),
        "cts_command": os.environ.get("TP_STAGE2_CTS_COMMAND", "clock_opt_design"),
        **tech,
    }
    if "TP_STAGE2_STRIPE_WIDTH" in os.environ:
        config["stripe_width"] = float(os.environ["TP_STAGE2_STRIPE_WIDTH"])
    if "TP_STAGE2_STRIPE_SPACING" in os.environ:
        config["stripe_spacing"] = float(os.environ["TP_STAGE2_STRIPE_SPACING"])
    if "TP_STAGE2_STRIPE_DISTANCE" in os.environ:
        config["stripe_distance"] = float(os.environ["TP_STAGE2_STRIPE_DISTANCE"])
    if "TP_STAGE2_SROUTE_MIN_LAYER" in os.environ:
        config["sroute_min_layer"] = os.environ["TP_STAGE2_SROUTE_MIN_LAYER"]
    if "TP_STAGE2_SROUTE_MAX_LAYER" in os.environ:
        config["sroute_max_layer"] = os.environ["TP_STAGE2_SROUTE_MAX_LAYER"]
    if "TP_STAGE2_ROUTE_MIN_LAYER" in os.environ:
        config["route_min_layer"] = os.environ["TP_STAGE2_ROUTE_MIN_LAYER"]
    if "TP_STAGE2_ROUTE_MAX_LAYER" in os.environ:
        config["route_max_layer"] = os.environ["TP_STAGE2_ROUTE_MAX_LAYER"]
    if "TP_STAGE2_NDR_CTS_MIN_LAYER" in os.environ:
        config["ndr_cts_min_layer"] = os.environ["TP_STAGE2_NDR_CTS_MIN_LAYER"]
    if "TP_STAGE2_NDR_CTS_MAX_LAYER" in os.environ:
        config["ndr_cts_max_layer"] = os.environ["TP_STAGE2_NDR_CTS_MAX_LAYER"]
    if "TP_STAGE2_REQUIRE_PG_CLEAN" in os.environ:
        config["require_pg_clean"] = os.environ["TP_STAGE2_REQUIRE_PG_CLEAN"].lower() in {"1", "true", "yes", "on"}
    if "TP_STAGE2_EXPECTED_FAKE_SRAM_MACROS" in os.environ:
        config["expected_fake_sram_macro_instances"] = int(os.environ["TP_STAGE2_EXPECTED_FAKE_SRAM_MACROS"])
    return config


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


def stage2_required_artifacts(innovus_output: dict, innovus_rundir: Path) -> dict[str, str]:
    return {
        "cts_checkpoint": str(innovus_rundir / "data" / "cts.enc"),
        "routing_checkpoint": innovus_output["routing_checkpoint"],
        "routed_def": innovus_output["def_file"],
        "routed_verilog": innovus_output["routed_verilog_file"],
        "routed_sdf": innovus_output["sdf_file"],
        "routed_spef": innovus_output["spef_file"],
        "gds": innovus_output["gds_file"],
        "post_route_timing_dir": innovus_output["post_route_timing_dir"],
        "post_route_area_report": innovus_output["post_route_area_report"],
        "post_route_power_report": innovus_output["post_route_power_report"],
        "post_route_drc_report": innovus_output["post_route_drc_report"],
        "post_route_connectivity_report": innovus_output["post_route_connectivity_report"],
    }


def evaluate_artifact_gates(required_artifacts: dict[str, str]) -> dict[str, Any]:
    status = {name: Path(path).exists() for name, path in required_artifacts.items()}
    return {
        "ok": all(status.values()),
        "required_artifacts": required_artifacts,
        "artifact_status": status,
        "missing": [name for name, exists in status.items() if not exists],
    }


def write_prelaunch_summary(config: dict, profile: str) -> Path:
    startup_dir = Path(config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "profile": profile,
        "run_tag": Path(config["rundir"]).name,
        "rundir": config["rundir"],
        "clock": {
            "name": config["clk_name"],
            "port": config["clk_port_name"],
            "period_ns": config["clk_period_ns"],
            "period_ps": config["clk_period_ns"] * 1000.0,
            "frequency_mhz": 1000.0 / config["clk_period_ns"],
        },
        "route_layers": {
            "route_min_layer": config.get("route_min_layer"),
            "route_max_layer": config.get("route_max_layer"),
            "ndr_cts_min_layer": config.get("ndr_cts_min_layer"),
            "ndr_cts_max_layer": config.get("ndr_cts_max_layer"),
            "m10_policy": "classify ASAP7 M10 IMPTR messages separately; do not route through M10 in this plan",
        },
        "pg": {
            "stripe_width": config.get("stripe_width"),
            "stripe_spacing": config.get("stripe_spacing"),
            "stripe_distance": config.get("stripe_distance"),
            "stripe_v_layer": config.get("stripe_v_layer"),
            "stripe_h_layer": config.get("stripe_h_layer"),
            "sroute_min_layer": config.get("sroute_min_layer"),
            "sroute_max_layer": config.get("sroute_max_layer"),
            "require_pg_clean": config.get("require_pg_clean", True),
        },
        "macro_placement": {
            "policy": "explicit_grid_fixed_fake_sram_macros",
            "fake_sram_macro_cells": config.get("fake_sram_macro_cells"),
            "expected_instances": config.get("expected_fake_sram_macro_instances"),
            "cols": config.get("macro_placement_cols"),
            "halo_x": config.get("macro_halo_x"),
            "halo_y": config.get("macro_halo_y"),
        },
        "cadence_threads": {
            "genus": config.get("max_threads"),
            "innovus": config.get("innovus_threads"),
            "route": config.get("route_max_threads"),
            "route_si_aware": config.get("route_si_aware"),
        },
        "genus_synthesis": {
            "syn_generic_effort": config.get("syn_generic_effort", "medium"),
            "syn_map_effort": config.get("syn_map_effort", "high"),
            "syn_opt_effort": config.get("syn_opt_effort", "medium"),
            "syn_opt_mode": config.get("syn_opt_mode") or "bare",
            "syn_opt_warning_policy": "SYNTH-33 is classified as a non-fatal Cadence deprecation warning for the current compatibility route",
        },
        "artifact_gates": [
            "cts.enc",
            "routing.enc",
            "routed DEF",
            "routed Verilog",
            "routed SDF",
            "SPEF",
            "GDS",
            "post-route timing/area/power/DRC/connectivity reports",
        ],
        "clean_output_policy": {
            "real_genus_launch": "fail if genus/data or genus/log already contains files unless TP_STAGE2_ALLOW_EXISTING_RUN=1",
            "real_innovus_full_launch": "fail if innovus/data or innovus/log already contains files unless TP_STAGE2_ALLOW_EXISTING_RUN=1",
            "script_generation": "may create scripts/startup files only and does not launch Cadence",
        },
    }
    out = startup_dir / "prelaunch_config_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out


def ensure_clean_launch_area(config: dict, tool: str) -> None:
    if os.environ.get("TP_STAGE2_ALLOW_EXISTING_RUN", "false").lower() in {"1", "true", "yes", "on"}:
        return
    root = Path(config["rundir"]) / tool
    checked = [root / "data", root / "log"]
    existing = []
    for directory in checked:
        if directory.is_dir():
            existing.extend(path for path in directory.iterdir() if path.name != ".gitkeep")
    if existing:
        sample = ", ".join(str(path) for path in existing[:5])
        raise FileExistsError(f"refusing to launch into non-clean {tool} output area: {sample}")


def parse_def_macro_status(def_path: Path, macro_cells: list[str], expected_count: int) -> dict[str, Any]:
    if not def_path.is_file():
        return {"ok": False, "def_file": str(def_path), "error": "floorplan DEF missing"}
    text = def_path.read_text(encoding="utf-8", errors="replace")
    die_match = re.search(r"DIEAREA\s+\(\s+(-?\d+)\s+(-?\d+)\s+\)\s+\(\s+(-?\d+)\s+(-?\d+)\s+\)", text)
    die = tuple(int(v) for v in die_match.groups()) if die_match else None
    components: list[dict[str, Any]] = []
    in_components = False
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("COMPONENTS "):
            in_components = True
            continue
        if in_components and line.startswith("END COMPONENTS"):
            if current:
                components.append(_parse_def_component(current, die, macro_cells))
            break
        if not in_components:
            continue
        if line.startswith("- "):
            if current:
                components.append(_parse_def_component(current, die, macro_cells))
            current = [line]
        elif current:
            current.append(line)
    macros = [item for item in components if item.get("is_fake_sram_macro")]
    bad = [item for item in macros if not item.get("inside_die", False) or item.get("status") not in {"PLACED", "FIXED"}]
    return {
        "ok": len(macros) == expected_count and not bad,
        "def_file": str(def_path),
        "diearea": die,
        "macro_cells": macro_cells,
        "expected_count": expected_count,
        "macro_count": len(macros),
        "bad_macros": bad,
        "macros": macros,
    }


def _parse_def_component(lines: list[str], die: tuple[int, int, int, int] | None, macro_cells: list[str]) -> dict[str, Any]:
    body = " ".join(lines)
    head = lines[0].split()
    name = head[1] if len(head) > 1 else ""
    master = head[2] if len(head) > 2 else ""
    loc_match = re.search(r"\+\s+(PLACED|FIXED)\s+\(\s+(-?\d+)\s+(-?\d+)\s+\)", body)
    status = loc_match.group(1) if loc_match else "UNPLACED"
    x = int(loc_match.group(2)) if loc_match else None
    y = int(loc_match.group(3)) if loc_match else None
    inside_die = False
    if die and x is not None and y is not None:
        inside_die = die[0] <= x <= die[2] and die[1] <= y <= die[3]
    return {
        "name": name,
        "master": master,
        "is_fake_sram_macro": master in macro_cells,
        "status": status,
        "x": x,
        "y": y,
        "inside_die": inside_die,
    }


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
        "syn_opt_mode": "",
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
    setup_clean = genus_rundir / "data" / "constraint_setup_innovus.sdc"
    hold_clean = genus_rundir / "data" / "constraint_hold_innovus.sdc"
    setup_raw = genus_rundir / "data" / "constraint_setup.sdc"
    hold_raw = genus_rundir / "data" / "constraint_hold.sdc"
    output = {
        "verilog_file": str(genus_rundir / "data" / "Gemmini-mapped.v"),
        "top_module": TOP_MODULE,
        "setup_lib_files": config["setup_lib_files"],
        "hold_lib_files": config["hold_lib_files"],
        "lef_files": config["lef_files"],
        "qrc_techfiles": config["qrc_techfiles"],
        "cts_inv_cells": config.get("cts_inv_cells", []),
        "setup_sdc_file": str(setup_clean if setup_clean.is_file() else setup_raw),
        "hold_sdc_file": str(hold_clean if hold_clean.is_file() else hold_raw),
        "raw_setup_sdc_file": str(setup_raw),
        "raw_hold_sdc_file": str(hold_raw),
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
    ensure_clean_launch_area(config, "genus")
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


def build_pnr_smoke_config(config: dict) -> dict:
    smoke = dict(config)
    smoke["droute_end_iteration"] = int(os.environ.get("TP_STAGE2_DROUTE_END_ITERATION", "5"))
    smoke["place_global_timing_effort"] = os.environ.get("TP_STAGE2_PLACE_TIMING_EFFORT", "low")
    smoke["place_global_cong_effort"] = os.environ.get("TP_STAGE2_PLACE_CONG_EFFORT", "low")
    smoke["place_detail_wire_length_opt_effort"] = os.environ.get("TP_STAGE2_PLACE_DETAIL_WIRE_EFFORT", "none")
    smoke["stripe_width"] = float(os.environ.get("TP_STAGE2_STRIPE_WIDTH", str(smoke.get("stripe_width", 0.04))))
    smoke["stripe_spacing"] = float(os.environ.get("TP_STAGE2_STRIPE_SPACING", str(smoke.get("stripe_spacing", 0.40))))
    smoke["stripe_distance"] = float(os.environ.get("TP_STAGE2_STRIPE_DISTANCE", "20.0"))
    smoke["sroute_min_layer"] = os.environ.get("TP_STAGE2_SROUTE_MIN_LAYER", smoke.get("sroute_min_layer", "M1"))
    smoke["sroute_max_layer"] = os.environ.get("TP_STAGE2_SROUTE_MAX_LAYER", smoke.get("sroute_max_layer", "M8"))
    smoke["require_pg_clean"] = False
    return smoke


def build_full_innovus_config(config: dict) -> dict:
    full = dict(config)
    full["droute_end_iteration"] = int(os.environ.get("TP_STAGE2_DROUTE_END_ITERATION", str(full.get("droute_end_iteration", 20))))
    full["place_global_timing_effort"] = os.environ.get("TP_STAGE2_PLACE_TIMING_EFFORT", full.get("place_global_timing_effort", "medium"))
    full["place_global_cong_effort"] = os.environ.get("TP_STAGE2_PLACE_CONG_EFFORT", full.get("place_global_cong_effort", "auto"))
    full["place_detail_wire_length_opt_effort"] = os.environ.get("TP_STAGE2_PLACE_DETAIL_WIRE_EFFORT", full.get("place_detail_wire_length_opt_effort", "medium"))
    full["require_pg_clean"] = True
    return full


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


def run_innovus_cts_route_smoke(config: dict) -> Path:
    smoke_config = build_pnr_smoke_config(config)
    genus_rundir = find_genus_synthesis_run(smoke_config)
    genus_output = build_genus_output_from_run(smoke_config, genus_rundir)
    placement_checkpoint = Path(smoke_config["rundir"]) / "innovus" / "data" / "placement.enc"
    if not placement_checkpoint.is_file():
        raise FileNotFoundError(f"missing placement checkpoint for CTS/route resume: {placement_checkpoint}")

    innovus_config = build_innovus_config(
        smoke_config,
        genus_output,
        runmode="normal",
        steps=["cts", "routing"],
    )
    innovus_config["start_prev_checkpoint"] = "placement"
    innovus_manager = InnovusManager(innovus_config)
    innovus_output = innovus_manager.run()

    required_artifacts = {
        "cts_checkpoint": str(Path(innovus_manager.data_dir) / "cts.enc"),
        "routing_checkpoint": innovus_output["routing_checkpoint"],
        "routed_def": innovus_output["def_file"],
        "routed_verilog": innovus_output["routed_verilog_file"],
        "routed_sdf": innovus_output["sdf_file"],
        "routed_spef": innovus_output["spef_file"],
        "gds": innovus_output["gds_file"],
        "post_route_timing_dir": innovus_output["post_route_timing_dir"],
        "post_route_area_report": innovus_output["post_route_area_report"],
        "post_route_power_report": innovus_output["post_route_power_report"],
        "post_route_drc_report": innovus_output["post_route_drc_report"],
        "post_route_connectivity_report": innovus_output["post_route_connectivity_report"],
    }
    artifact_status = {name: Path(path).exists() for name, path in required_artifacts.items()}

    startup_dir = Path(smoke_config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_innovus_cts_route_resume_smoke",
        "ok": True,
        "notes": [
            "Cadence Innovus was resumed through the Python manager from placement.enc.",
            "This is a reduced-effort CTS/routing continuation smoke, not final Stage 2 signoff.",
            "Final Stage 2 acceptance still requires DRC/connectivity/timing/artifact classification and normal-quality settings.",
        ],
        "source_genus_rundir": str(genus_rundir),
        "placement_checkpoint": str(placement_checkpoint),
        "cts_command": smoke_config["cts_command"],
        "innovus_rundir": innovus_manager.rundir,
        "innovus_output": innovus_output,
        "artifact_status": artifact_status,
        "scripts": {
            "cts": str(Path(innovus_manager.script_dir) / "cts.tcl"),
            "routing": str(Path(innovus_manager.script_dir) / "routing.tcl"),
        },
        "logs": {
            "cts": str(Path(innovus_manager.log_dir) / "cts.log"),
            "routing": str(Path(innovus_manager.log_dir) / "routing.log"),
        },
    }
    out = startup_dir / "innovus_cts_route_smoke_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def run_innovus_pnr_smoke(config: dict) -> Path:
    smoke_config = build_pnr_smoke_config(config)
    genus_rundir = find_genus_synthesis_run(smoke_config)
    genus_output = build_genus_output_from_run(smoke_config, genus_rundir)
    innovus_manager = InnovusManager(
        build_innovus_config(
            smoke_config,
            genus_output,
            runmode="normal",
            steps=["init", "floorplan", "powerplan", "placement", "cts", "routing"],
        )
    )
    innovus_output = innovus_manager.run()

    floorplan_def = Path(innovus_manager.floorplan_def_path)
    pin_status = parse_def_pin_status(floorplan_def) if floorplan_def.is_file() else {
        "def_file": str(floorplan_def),
        "ok": False,
        "error": "floorplan DEF was not produced",
    }
    required_artifacts = {
        "routing_checkpoint": innovus_output["routing_checkpoint"],
        "routed_def": innovus_output["def_file"],
        "routed_verilog": innovus_output["routed_verilog_file"],
        "routed_sdf": innovus_output["sdf_file"],
        "routed_spef": innovus_output["spef_file"],
        "gds": innovus_output["gds_file"],
        "post_route_timing_dir": innovus_output["post_route_timing_dir"],
        "post_route_area_report": innovus_output["post_route_area_report"],
        "post_route_power_report": innovus_output["post_route_power_report"],
        "post_route_drc_report": innovus_output["post_route_drc_report"],
        "post_route_connectivity_report": innovus_output["post_route_connectivity_report"],
    }
    artifact_status = {name: Path(path).exists() for name, path in required_artifacts.items()}

    startup_dir = Path(smoke_config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_innovus_pnr_smoke",
        "ok": True,
        "notes": [
            "Cadence Innovus was launched through the Python manager.",
            "This is a reduced-effort run-through smoke, not final Stage 2 signoff.",
            "Final Stage 2 acceptance still requires DRC/connectivity/timing/artifact classification and normal-quality settings.",
        ],
        "source_genus_rundir": str(genus_rundir),
        "genus_output": genus_output,
        "innovus_rundir": innovus_manager.rundir,
        "innovus_output": innovus_output,
        "reduced_effort_knobs": {
            "droute_end_iteration": smoke_config["droute_end_iteration"],
            "route_max_threads": smoke_config["route_max_threads"],
            "route_si_aware": smoke_config["route_si_aware"],
            "place_global_timing_effort": smoke_config["place_global_timing_effort"],
            "place_global_cong_effort": smoke_config["place_global_cong_effort"],
            "place_detail_wire_length_opt_effort": smoke_config["place_detail_wire_length_opt_effort"],
        },
        "pin_status": pin_status,
        "artifact_status": artifact_status,
        "scripts": {
            "mmmc": innovus_manager.mmmc_script_path,
            "init": str(Path(innovus_manager.script_dir) / "init.tcl"),
            "floorplan": str(Path(innovus_manager.script_dir) / "floorplan.tcl"),
            "powerplan": str(Path(innovus_manager.script_dir) / "powerplan.tcl"),
            "placement": str(Path(innovus_manager.script_dir) / "placement.tcl"),
            "cts": str(Path(innovus_manager.script_dir) / "cts.tcl"),
            "routing": str(Path(innovus_manager.script_dir) / "routing.tcl"),
        },
        "logs": {
            "init": str(Path(innovus_manager.log_dir) / "init.log"),
            "floorplan": str(Path(innovus_manager.log_dir) / "floorplan.log"),
            "powerplan": str(Path(innovus_manager.log_dir) / "powerplan.log"),
            "placement": str(Path(innovus_manager.log_dir) / "placement.log"),
            "cts": str(Path(innovus_manager.log_dir) / "cts.log"),
            "routing": str(Path(innovus_manager.log_dir) / "routing.log"),
        },
    }
    out = startup_dir / "innovus_pnr_smoke_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def run_innovus_full(config: dict) -> Path:
    full_config = build_full_innovus_config(config)
    ensure_clean_launch_area(full_config, "innovus")
    genus_rundir = find_genus_synthesis_run(full_config)
    genus_output = build_genus_output_from_run(full_config, genus_rundir)
    innovus_manager = InnovusManager(
        build_innovus_config(
            full_config,
            genus_output,
            runmode="normal",
            steps=["init", "floorplan", "powerplan", "placement", "cts", "routing"],
        )
    )
    innovus_output = innovus_manager.run()

    floorplan_def = Path(innovus_manager.floorplan_def_path)
    pin_status = parse_def_pin_status(floorplan_def) if floorplan_def.is_file() else {
        "def_file": str(floorplan_def),
        "ok": False,
        "error": "floorplan DEF was not produced",
    }
    macro_status = parse_def_macro_status(
        floorplan_def,
        full_config.get("fake_sram_macro_cells", ["mem_ext", "mem_0_ext"]),
        full_config.get("expected_fake_sram_macro_instances", 6),
    )
    required_artifacts = stage2_required_artifacts(innovus_output, Path(innovus_manager.rundir))
    gate_status = evaluate_artifact_gates(required_artifacts)

    startup_dir = Path(full_config["rundir"]) / "startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "phase2_innovus_full",
        "ok": gate_status["ok"] and pin_status.get("ok", False) and macro_status.get("ok", False),
        "notes": [
            "Cadence Innovus full implementation was launched through the Python manager.",
            "This is the non-smoke Phase 2 route. Acceptance still depends on DRC/connectivity/timing classification in the final report.",
            "ASAP7 M10 IMPTR collateral messages must be classified separately from routed DRC.",
        ],
        "source_genus_rundir": str(genus_rundir),
        "genus_output": genus_output,
        "innovus_rundir": innovus_manager.rundir,
        "innovus_output": innovus_output,
        "pin_status": pin_status,
        "macro_status": macro_status,
        "gate_status": gate_status,
        "prelaunch_summary": str(startup_dir / "prelaunch_config_summary.json"),
        "scripts": {
            "mmmc": innovus_manager.mmmc_script_path,
            "init": str(Path(innovus_manager.script_dir) / "init.tcl"),
            "floorplan": str(Path(innovus_manager.script_dir) / "floorplan.tcl"),
            "powerplan": str(Path(innovus_manager.script_dir) / "powerplan.tcl"),
            "placement": str(Path(innovus_manager.script_dir) / "placement.tcl"),
            "cts": str(Path(innovus_manager.script_dir) / "cts.tcl"),
            "routing": str(Path(innovus_manager.script_dir) / "routing.tcl"),
        },
    }
    out = startup_dir / "innovus_full_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if not manifest["ok"]:
        raise RuntimeError(f"Innovus full artifact gate failed; see {out}")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GemminiRocketConfig mesh16x16 Phase 2 startup")
    parser.add_argument("--preflight", action="store_true", help="Validate inputs and paths without writing outputs")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and write a startup manifest under physical/<tag>/startup")
    parser.add_argument("--write-scripts", action="store_true", help="Generate Genus/Innovus Tcl through manager/ without launching commercial tools")
    parser.add_argument("--run-genus-elab", action="store_true", help="Launch a Python-managed Genus frontend/elaboration smoke without synthesis")
    parser.add_argument("--run-genus-syn", action="store_true", help="Launch Python-managed Genus synthesis and reports without Innovus")
    parser.add_argument("--run-innovus-floorplan-smoke", action="store_true", help="Launch Python-managed Innovus init/floorplan smoke from a completed Genus synthesis run")
    parser.add_argument("--run-innovus-pnr-smoke", action="store_true", help="Launch reduced-effort Python-managed Innovus powerplan/place/CTS/route smoke from a completed Genus synthesis run")
    parser.add_argument("--run-innovus-cts-route-smoke", action="store_true", help="Resume reduced-effort Innovus CTS/routing smoke from an existing placement.enc in the selected run tag")
    parser.add_argument("--run-innovus-full", action="store_true", help="Launch non-smoke Python-managed Innovus full implementation from a completed Genus synthesis run")
    parser.add_argument("--print-config", action="store_true", help="Print resolved startup config as JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = build_config()
    ok, errors = preflight(config)
    if args.print_config:
        print(json.dumps(config, indent=2))
    if args.preflight or args.dry_run or args.write_scripts or args.run_genus_elab or args.run_genus_syn or args.run_innovus_floorplan_smoke or args.run_innovus_pnr_smoke or args.run_innovus_cts_route_smoke or args.run_innovus_full:
        print_summary(config)
        if args.dry_run:
            print(f"manifest={write_dry_run(config, errors)}")
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        if args.write_scripts:
            print(f"prelaunch_summary={write_prelaunch_summary(config, 'script_generation')}")
            print(f"manager_manifest={write_manager_scripts(config)}")
        if args.run_genus_elab:
            print(f"genus_elab_manifest={run_genus_elab(config)}")
        if args.run_genus_syn:
            print(f"prelaunch_summary={write_prelaunch_summary(config, 'genus_synthesis')}")
            print(f"genus_syn_manifest={run_genus_syn(config)}")
        if args.run_innovus_floorplan_smoke:
            print(f"innovus_floorplan_manifest={run_innovus_floorplan_smoke(config)}")
        if args.run_innovus_pnr_smoke:
            print(f"innovus_pnr_smoke_manifest={run_innovus_pnr_smoke(config)}")
        if args.run_innovus_cts_route_smoke:
            print(f"innovus_cts_route_smoke_manifest={run_innovus_cts_route_smoke(config)}")
        if args.run_innovus_full:
            print(f"prelaunch_summary={write_prelaunch_summary(build_full_innovus_config(config), 'innovus_full')}")
            print(f"innovus_full_manifest={run_innovus_full(config)}")
        print("preflight_ok=True")
        return 0
    print("No action requested. Use --preflight, --dry-run, --write-scripts, --run-genus-elab, --run-genus-syn, --run-innovus-floorplan-smoke, --run-innovus-pnr-smoke, --run-innovus-cts-route-smoke, --run-innovus-full, or --print-config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
