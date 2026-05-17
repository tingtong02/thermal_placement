#!/usr/bin/env python3
"""Read-only Phase3 preflight for mvin_mvout r28 gate-SAIF bring-up."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUN_ROOT_DEFAULT = Path("runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff")
R28_TAG = "gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived"
PHASE1B_TAG = "phase1b_gate_saif_r28_20260515"
WORKLOAD = "mvin_mvout"


try:
    REPO_ROOT = Path(__file__).resolve().parents[1]
except NameError:
    REPO_ROOT = Path.cwd().resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=RUN_ROOT_DEFAULT)
    parser.add_argument("--phase2-run", type=Path, default=None)
    parser.add_argument("--phase1b-root", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--workload", default=WORKLOAD, choices=[WORKLOAD])
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def file_record(path: Path, required: bool = True) -> dict[str, Any]:
    exists = path.exists()
    record: dict[str, Any] = {
        "path": rel(path),
        "required": required,
        "exists": exists,
        "is_file": path.is_file() if exists else False,
        "is_dir": path.is_dir() if exists else False,
    }
    if exists and path.is_file():
        st = path.stat()
        record.update({"bytes": st.st_size, "mtime": st.st_mtime})
    return record


def require_file(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    record = file_record(path, required=True)
    if not record["exists"]:
        errors.append(f"missing required {label}: {rel(path)}")
    elif not record["is_file"]:
        errors.append(f"required {label} is not a file: {rel(path)}")
    elif int(record.get("bytes", 0)) <= 0:
        errors.append(f"required {label} is empty: {rel(path)}")
    return record


def optional_file(path: Path) -> dict[str, Any]:
    return file_record(path, required=False)


def source_snapshot(workload_dir: Path) -> dict[str, Any]:
    saif = workload_dir / f"{workload_dir.name}.gate.saif"
    summary = workload_dir / "replay_summary.json"
    manifest = workload_dir / "gate_activity_manifest.json"
    data = read_json(manifest)
    summary_data = read_json(summary)
    return {
        "workload": workload_dir.name,
        "directory": rel(workload_dir),
        "saif": file_record(saif, required=False),
        "replay_summary": file_record(summary, required=False),
        "gate_activity_manifest": file_record(manifest, required=False),
        "phase3_consumable": data.get("phase3_consumable") if data else None,
        "run_returncode": summary_data.get("run_returncode") if summary_data else None,
        "trace_enabled_cycles": summary_data.get("trace_enabled_cycles") if summary_data else None,
    }


def build_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    run_root = args.run_root
    phase2 = args.phase2_run or run_root / "physical" / R28_TAG
    phase1b = args.phase1b_root or run_root / "gate_activity" / PHASE1B_TAG
    out_dir = args.out_dir or run_root / "power" / WORKLOAD
    workload_dir = phase1b / WORKLOAD
    errors: list[str] = []
    warnings: list[str] = []

    stage2_files = {
        "routed_def": require_file(phase2 / "innovus" / "data" / "Gemmini.routed.def", "r28 routed DEF", errors),
        "routed_verilog": require_file(phase2 / "innovus" / "data" / "Gemmini.routed.v", "r28 routed Verilog", errors),
        "spef": require_file(phase2 / "innovus" / "data" / "Gemmini.routed.spef", "r28 SPEF", errors),
        "gds": require_file(phase2 / "innovus" / "data" / "Gemmini.gds", "r28 GDS", errors),
        "cts_checkpoint": require_file(phase2 / "innovus" / "data" / "cts.enc", "r28 cts.enc", errors),
        "routing_checkpoint": require_file(phase2 / "innovus" / "data" / "routing.enc", "r28 routing.enc", errors),
        "export_checkpoint": require_file(phase2 / "innovus" / "data" / "export_routing.enc", "r28 export_routing.enc", errors),
        "postroute_power_report": require_file(phase2 / "innovus" / "reports" / "postRoute_power.rpt", "post-route power report", errors),
        "postroute_area_report": require_file(phase2 / "innovus" / "reports" / "postRoute_area.rpt", "post-route area report", errors),
        "postroute_drc_report": require_file(phase2 / "innovus" / "reports" / "postRoute_drc.rpt", "post-route DRC report", errors),
        "postroute_connectivity_report": require_file(phase2 / "innovus" / "reports" / "postRoute_connectivity.rpt", "post-route connectivity report", errors),
        "postroute_timing_report": require_file(phase2 / "innovus" / "reports" / "postRoute_timing" / "timing.rpt", "post-route timing report", errors),
        "routed_sdf_waiver": require_file(phase2 / "innovus" / "reports" / "routed_sdf_waiver.md", "routed-SDF waiver", errors),
    }

    saif = workload_dir / f"{WORKLOAD}.gate.saif"
    phase1b_files = {
        "workload_dir": file_record(workload_dir, required=True),
        "saif": require_file(saif, "mainline mvin_mvout gate SAIF", errors),
        "replay_summary": require_file(workload_dir / "replay_summary.json", "mvin_mvout replay summary", errors),
        "gate_activity_manifest": require_file(workload_dir / "gate_activity_manifest.json", "mvin_mvout gate activity manifest", errors),
        "boundary_signal_map": require_file(workload_dir / "boundary_signal_map.json", "mvin_mvout boundary signal map", errors),
        "boundary_vectors_manifest": require_file(workload_dir / "boundary_vectors_manifest.json", "mvin_mvout boundary vectors manifest", errors),
        "global_handoff_manifest": optional_file(phase1b / "phase1b_gate_saif_handoff_manifest.json"),
        "method_report": optional_file(phase1b / "phase1b_gate_saif_method_report.md"),
    }

    activity_manifest = read_json(workload_dir / "gate_activity_manifest.json") or {}
    replay_summary = read_json(workload_dir / "replay_summary.json") or {}
    if activity_manifest.get("phase3_consumable") is not True:
        errors.append("mvin_mvout gate_activity_manifest.json is not phase3_consumable=true")
    if activity_manifest.get("run_kind") != "formal":
        errors.append("mvin_mvout gate_activity_manifest.json is not run_kind=formal")
    if replay_summary.get("run_returncode") != 0:
        errors.append("mvin_mvout replay_summary.json does not have run_returncode=0")
    if int(replay_summary.get("trace_enabled_cycles") or 0) <= 0:
        errors.append("mvin_mvout replay_summary.json has no trace-enabled cycles")
    if int(replay_summary.get("saif_bytes") or 0) != int(phase1b_files["saif"].get("bytes") or -1):
        warnings.append("mvin_mvout summary saif_bytes does not match current SAIF file size")

    global_handoff = read_json(phase1b / "phase1b_gate_saif_handoff_manifest.json")
    if global_handoff is not None:
        formal_workloads = global_handoff.get("formal_workloads", [])
        if not formal_workloads:
            warnings.append("global Phase1b handoff manifest has no formal_workloads; using per-workload mvin_mvout manifest for preflight")
    else:
        warnings.append("global Phase1b handoff manifest is absent; using per-workload mvin_mvout manifest for preflight")

    excluded_sources = {
        "smoke": source_snapshot(phase1b / "smoke_mvin_mvout_100cyc"),
        "mainline_tiled_matmul_ws": source_snapshot(phase1b / "tiled_matmul_ws"),
        "mainline_tiled_matmul_os": source_snapshot(phase1b / "tiled_matmul_os"),
        "accelerated_mvin_mvout": source_snapshot(phase1b / "accelerate" / "mvin_mvout"),
        "accelerated_tiled_matmul_ws": source_snapshot(phase1b / "accelerate" / "tiled_matmul_ws"),
        "accelerated_tiled_matmul_os": source_snapshot(phase1b / "accelerate" / "tiled_matmul_os"),
        "old_r2_compare_validation": {
            "directory": rel(run_root / "gate_activity" / "phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full"),
            "excluded_reason": "historical r2 compare validation only; not a Phase3 activity handoff",
        },
    }

    for name, snap in excluded_sources.items():
        if isinstance(snap, dict) and snap.get("phase3_consumable") is True and name != "smoke":
            warnings.append(f"excluded source {name} has phase3_consumable=true; current mvin-only policy still excludes it")

    expected_outputs = {
        "preflight_manifest": rel(out_dir / "phase3_mvin_mvout_preflight_manifest.json"),
        "preflight_report": rel(out_dir / "phase3_mvin_mvout_preflight_report.md"),
        "activity_handoff_manifest": rel(out_dir / "phase3_mvin_mvout_activity_handoff_manifest.json"),
        "cadence_power_dir": rel(out_dir / "cadence"),
        "saif_annotation_coverage_report": rel(out_dir / "reports" / "phase3_mvin_mvout_saif_annotation_coverage.rpt"),
        "instance_power_report": rel(out_dir / "reports" / "phase3_mvin_mvout_instance_power.rpt"),
        "instance_to_grid_map": rel(out_dir / "phase3_mvin_mvout_instance_to_grid_map.csv"),
        "grid_power_csv": rel(out_dir / "phase3_mvin_mvout_grid_power.csv"),
        "transient_power_trace": rel(out_dir / "phase3_mvin_mvout_transient_power_trace.csv"),
        "top_power_instances": rel(out_dir / "phase3_mvin_mvout_top_power_instances.csv"),
        "region_power_summary": rel(out_dir / "phase3_mvin_mvout_region_power_summary.csv"),
        "method_report": rel(out_dir / "phase3_mvin_mvout_method_report.md"),
    }

    tool_paths = {
        "python": shutil.which("python"),
        "innovus": shutil.which("innovus"),
    }
    if tool_paths["python"] != "/home/lisihang/miniconda3/envs/thermal_placement/bin/python":
        warnings.append("python is not the expected thermal_placement conda interpreter")
    if tool_paths["innovus"] is None:
        warnings.append("innovus is not on PATH; later Cadence power step will need Cadence environment")

    status = "fail" if errors else ("pass_with_warnings" if warnings else "pass")
    manifest: dict[str, Any] = {
        "schema": "phase3_mvin_mvout_preflight_manifest_v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "workload": WORKLOAD,
        "stage": "Stage 3 Cadence activity-aware power",
        "output_root": rel(out_dir),
        "policy": {
            "scope": "single-workload mvin_mvout bring-up",
            "non_signoff_label": "PG-open / DRC-open / routed-SDF-waived thermal proxy; Phase1b SAIF is Verilator zero-delay activity",
            "no_cadence_launched": True,
            "do_not_interrupt_running_replays": True,
            "phase3_activity_source_rule": "consume only completed non-empty formal mainline SAIF with phase3_consumable=true",
        },
        "inputs": {
            "run_root": rel(run_root),
            "phase2_r28_run": rel(phase2),
            "phase1b_root": rel(phase1b),
            "phase1b_mvin_mvout": phase1b_files,
            "phase2_artifacts": stage2_files,
            "activity_manifest_summary": {
                "phase3_consumable": activity_manifest.get("phase3_consumable"),
                "run_kind": activity_manifest.get("run_kind"),
                "method": activity_manifest.get("method"),
                "trace_start_ps": activity_manifest.get("trace_start_ps"),
                "trace_end_ps": activity_manifest.get("trace_end_ps"),
            },
            "replay_summary": {
                key: replay_summary.get(key)
                for key in [
                    "run_returncode",
                    "cycles_run",
                    "rows_seen",
                    "trace_enabled_cycles",
                    "first_trace_time_ps",
                    "last_trace_time_ps",
                    "elapsed_sec",
                    "saif_bytes",
                ]
            },
        },
        "excluded_sources": excluded_sources,
        "tools": tool_paths,
        "expected_outputs": expected_outputs,
        "errors": errors,
        "warnings": warnings,
        "next_step_if_passes": "Develop Cadence read_saif scope mapping and annotation coverage under the same output root.",
    }
    return manifest, errors, warnings


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Phase3 mvin_mvout Preflight Report",
        "",
        f"- status: `{manifest['status']}`",
        f"- generated at UTC: `{manifest['generated_at_utc']}`",
        f"- workload: `{manifest['workload']}`",
        f"- output root: `{manifest['output_root']}`",
        f"- non-signoff label: `{manifest['policy']['non_signoff_label']}`",
        "- Cadence launched: `no`",
        "- running Phase1b replays interrupted: `no`",
        "",
        "## Accepted Input",
        "",
        f"- mainline mvin SAIF: `{manifest['inputs']['phase1b_mvin_mvout']['saif']['path']}`",
        f"- SAIF bytes: `{manifest['inputs']['phase1b_mvin_mvout']['saif'].get('bytes')}`",
        f"- phase3 consumable: `{manifest['inputs']['activity_manifest_summary'].get('phase3_consumable')}`",
        f"- replay return code: `{manifest['inputs']['replay_summary'].get('run_returncode')}`",
        f"- trace enabled cycles: `{manifest['inputs']['replay_summary'].get('trace_enabled_cycles')}`",
        "",
        "## r28 Physical Handoff",
        "",
    ]
    for key, rec in manifest["inputs"]["phase2_artifacts"].items():
        lines.append(f"- {key}: `{rec['path']}` exists=`{rec['exists']}` bytes=`{rec.get('bytes')}`")
    lines.extend(["", "## Excluded Inputs", ""])
    for key, rec in manifest["excluded_sources"].items():
        if "excluded_reason" in rec:
            lines.append(f"- {key}: {rec['excluded_reason']}")
        else:
            lines.append(
                f"- {key}: saif_bytes=`{rec['saif'].get('bytes')}` summary_exists=`{rec['replay_summary']['exists']}` "
                f"manifest_exists=`{rec['gate_activity_manifest']['exists']}` phase3_consumable=`{rec.get('phase3_consumable')}`"
            )
    if manifest["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {w}" for w in manifest["warnings"])
    if manifest["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {e}" for e in manifest["errors"])
    lines.extend(["", "## Expected Outputs", ""])
    for key, value in manifest["expected_outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Next Step", "", manifest["next_step_if_passes"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.run_root / "power" / WORKLOAD
    manifest, errors, _warnings = build_manifest(args)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "phase3_mvin_mvout_preflight_manifest.json"
    report_path = out_dir / "phase3_mvin_mvout_preflight_report.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(report_path, manifest)
    print(json.dumps({"status": manifest["status"], "manifest": rel(manifest_path), "report": rel(report_path)}, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
