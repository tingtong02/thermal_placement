#!/usr/bin/env python3
"""Orchestrate formal Phase1b r28 Gemmini gate SAIF replay workloads."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN_ROOT_DEFAULT = Path("runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff")
R28_NETLIST_DEFAULT = RUN_ROOT_DEFAULT / "physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v"
ASAP7_VERILOG_DEFAULT = Path("/home/lisihang/asap7/asap7sc7p5t_28/Verilog")
SRAM_MODEL_DEFAULT = Path("collateral/gate_sim/fake_sram")
OUT_DIR_DEFAULT = RUN_ROOT_DEFAULT / "gate_activity/phase1b_gate_saif_r28_20260515"

WORKLOADS = [
    {
        "name": "mvin_mvout",
        "rtl_vcd": RUN_ROOT_DEFAULT / "sim/mvin_mvout/waves/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.vcd",
        "trace_start_ps": 66875550,
        "trace_end_ps": 601879950,
    },
    {
        "name": "tiled_matmul_ws",
        "rtl_vcd": RUN_ROOT_DEFAULT / "sim/tiled_matmul_ws/waves/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.vcd",
        "trace_start_ps": 1072392550,
        "trace_end_ps": 3753373925,
    },
    {
        "name": "tiled_matmul_os",
        "rtl_vcd": RUN_ROOT_DEFAULT / "sim/tiled_matmul_os/waves/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.vcd",
        "trace_start_ps": 9272956950,
        "trace_end_ps": 10303285500,
    },
]

SMOKE = {
    "name": "smoke_mvin_mvout_100cyc",
    "workload": "mvin_mvout",
    "rtl_vcd": WORKLOADS[0]["rtl_vcd"],
    "trace_start_ps": 66875550,
    "trace_end_ps": 67075550,
    "max_cycles": None,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=RUN_ROOT_DEFAULT)
    parser.add_argument("--gate-netlist", type=Path, default=R28_NETLIST_DEFAULT)
    parser.add_argument("--asap7-verilog-dir", type=Path, default=ASAP7_VERILOG_DEFAULT)
    parser.add_argument("--sram-model-dir", type=Path, default=SRAM_MODEL_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    parser.add_argument("--allow-nonempty-out-dir", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--stop-after-smoke", action="store_true")
    parser.add_argument("--workload", choices=[w["name"] for w in WORKLOADS], action="append", help="formal workload(s) to run; default is all in fixed order")
    parser.add_argument("--module", default="Gemmini")
    parser.add_argument("--trace-depth", type=int, default=9)
    parser.add_argument("--verilate-jobs", type=int, default=192)
    parser.add_argument("--jobs", type=int, default=192)
    parser.add_argument("--verilator-threads", type=int, default=16)
    parser.add_argument("--output-split", type=int, default=200)
    parser.add_argument("--output-split-cfuncs", type=int, default=20)
    parser.add_argument("--output-split-ctrace", type=int, default=20)
    parser.add_argument("--cflags", default="-O0 -g0")
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())




def jsonable(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [jsonable(v) for v in value]
    return value


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_string(cmd: list[str]) -> str:
    return " ".join(cmd)


def run_logged(cmd: list[str], cwd: Path, log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    print(f"[cmd] {command_string(cmd)}", flush=True)
    with log.open("w", encoding="utf-8", errors="ignore") as f:
        f.write("$ " + command_string(cmd) + "\n")
        f.flush()
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert proc.stdout is not None
        for line in proc.stdout:
            f.write(line)
            if line.startswith(("[start]", "[trace]", "[finish]")) or "error" in line.lower() or "Error" in line:
                print(line.rstrip(), flush=True)
        rc = proc.wait()
        f.write(f"\n[returncode] {rc}\n")
    if rc != 0:
        raise subprocess.CalledProcessError(rc, cmd)


def ensure_inputs(args: argparse.Namespace) -> None:
    checks = [args.gate_netlist, args.asap7_verilog_dir, args.sram_model_dir / "mem_ext.sv", args.sram_model_dir / "mem_0_ext.sv"]
    checks.extend(Path(w["rtl_vcd"]) for w in WORKLOADS)
    missing = [str(p) for p in checks if not p.exists()]
    if missing:
        raise SystemExit("missing required inputs:\n" + "\n".join(missing))
    if args.out_dir.exists() and any(args.out_dir.iterdir()) and not args.allow_nonempty_out_dir:
        raise SystemExit(f"output directory is non-empty; use --allow-nonempty-out-dir only for intentional resume: {args.out_dir}")


def extract_vectors(args: argparse.Namespace, run_dir: Path, workload: str, rtl_vcd: Path, end_ps: int, max_cycles: int | None = None) -> Path:
    cmd = [
        sys.executable,
        "scripts/phase1b_extract_gemmini_boundary_vectors.py",
        "--rtl-vcd",
        str(rtl_vcd),
        "--gate-netlist",
        str(args.gate_netlist),
        "--workload",
        workload,
        "--out-dir",
        str(run_dir),
        "--start-ps",
        "0",
        "--end-ps",
        str(end_ps),
        "--module",
        args.module,
        "--vectors-inputs-only",
    ]
    if max_cycles is not None:
        cmd.extend(["--max-cycles", str(max_cycles + 1)])
    run_logged(cmd, Path.cwd(), run_dir / "extract_command.log")
    vector_path = run_dir / "boundary_vectors.csv"
    if not vector_path.is_file() or vector_path.stat().st_size == 0:
        raise RuntimeError(f"vector extraction did not produce a non-empty file: {vector_path}")
    return vector_path


def replay(args: argparse.Namespace, run_dir: Path, workload: str, run_kind: str, vectors: Path, trace_start_ps: int, trace_end_ps: int, max_cycles: int | None, skip_build: bool) -> dict[str, object]:
    saif = run_dir / f"{workload}.gate.saif"
    cmd = [
        sys.executable,
        "scripts/phase1b_run_gate_saif_replay.py",
        "--boundary-map",
        str(run_dir / "boundary_signal_map.json"),
        "--boundary-vectors",
        str(vectors),
        "--gate-netlist",
        str(args.gate_netlist),
        "--asap7-verilog-dir",
        str(args.asap7_verilog_dir),
        "--sram-model-dir",
        str(args.sram_model_dir),
        "--out-dir",
        str(run_dir),
        "--build-root",
        str(args.out_dir / "build"),
        "--emit-saif",
        str(saif),
        "--trace-start-ps",
        str(trace_start_ps),
        "--trace-end-ps",
        str(trace_end_ps),
        "--workload",
        workload,
        "--run-kind",
        run_kind,
        "--module",
        args.module,
        "--trace-depth",
        str(args.trace_depth),
        "--verilate-jobs",
        str(args.verilate_jobs),
        "--jobs",
        str(args.jobs),
        "--verilator-threads",
        str(args.verilator_threads),
        "--output-split",
        str(args.output_split),
        "--output-split-cfuncs",
        str(args.output_split_cfuncs),
        "--output-split-ctrace",
        str(args.output_split_ctrace),
        "--cflags",
        args.cflags,
    ]
    if max_cycles is not None:
        cmd.extend(["--max-cycles", str(max_cycles)])
    if skip_build:
        cmd.append("--skip-build-if-exists")
    run_logged(cmd, Path.cwd(), run_dir / "replay_command.log")
    manifest = json.loads((run_dir / "gate_activity_manifest.json").read_text(encoding="utf-8"))
    if manifest["summary"].get("run_returncode") != 0:
        raise RuntimeError(f"replay failed for {workload}: {run_dir}")
    if int(manifest["summary"].get("trace_enabled_cycles", 0)) <= 0:
        raise RuntimeError(f"replay had zero trace-enabled cycles for {workload}: {run_dir}")
    if int(manifest["summary"].get("saif_bytes", 0)) <= 0:
        raise RuntimeError(f"replay produced empty SAIF for {workload}: {run_dir}")
    return manifest


def selected_workloads(args: argparse.Namespace) -> list[dict[str, object]]:
    if not args.workload:
        return WORKLOADS
    names = set(args.workload)
    return [w for w in WORKLOADS if w["name"] in names]


def write_method_report(args: argparse.Namespace, smoke_manifest: dict[str, object] | None, formal_manifests: list[dict[str, object]], status: str) -> None:
    lines = [
        "# Phase1b r28 Gate SAIF Method Report",
        "",
        f"- status: `{status}`",
        f"- generated at UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- gate netlist: `{rel(args.gate_netlist)}`",
        f"- output root: `{rel(args.out_dir)}`",
        "- method: Verilator zero-delay Gemmini boundary replay with direct SAIF tracing",
        "- compare: disabled for formal Phase1b",
        "- timing: no SDF; not commercial gate simulation or timing signoff",
        f"- trace depth: `{args.trace_depth}`",
        f"- Verilator threads: `{args.verilator_threads}`",
        f"- Verilator frontend jobs: `{args.verilate_jobs}`",
        f"- make jobs: `{args.jobs}`",
        f"- output split: `{args.output_split}`",
        f"- output split cfuncs: `{args.output_split_cfuncs}`",
        f"- output split ctrace: `{args.output_split_ctrace}`",
        "",
        "## Smoke",
        "",
    ]
    if smoke_manifest is None:
        lines.append("- skipped")
    else:
        s = smoke_manifest["summary"]
        lines.extend([
            f"- workload: `{smoke_manifest['workload']}`",
            f"- SAIF: `{rel(Path(smoke_manifest['saif']))}`",
            f"- trace cycles: `{s.get('trace_enabled_cycles')}`",
            f"- SAIF bytes: `{s.get('saif_bytes')}`",
            "- Phase3 handoff: excluded",
        ])
    lines.extend(["", "## Formal Handoff", ""])
    for manifest in formal_manifests:
        s = manifest["summary"]
        lines.extend([
            f"### {manifest['workload']}",
            "",
            f"- SAIF: `{rel(Path(manifest['saif']))}`",
            f"- trace window ps: `[{manifest['trace_start_ps']}, {manifest['trace_end_ps']})`",
            f"- cycles run: `{s.get('cycles_run')}`",
            f"- trace cycles: `{s.get('trace_enabled_cycles')}`",
            f"- first trace ps: `{s.get('first_trace_time_ps')}`",
            f"- last trace ps: `{s.get('last_trace_time_ps')}`",
            f"- elapsed sec: `{s.get('elapsed_sec')}`",
            f"- SAIF bytes: `{s.get('saif_bytes')}`",
            f"- Phase3 consumable: `{manifest.get('phase3_consumable')}`",
            "",
        ])
    lines.extend([
        "## Phase3 Requirement",
        "",
        "These SAIF files are rooted at the Verilated `Gemmini` top. Stage 3 must perform Cadence `read_saif` scope/instance mapping to the r28 physical design and report annotation coverage before using activity for power.",
        "",
        "Historical old compare results under `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/` remain validation evidence only and are excluded from this handoff.",
    ])
    (args.out_dir / "phase1b_gate_saif_method_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    ensure_inputs(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if shutil.which("verilator") is None:
        raise SystemExit("missing verilator in PATH")
    formal_manifests: list[dict[str, object]] = []
    smoke_manifest: dict[str, object] | None = None
    build_started = False
    existing_exe = args.out_dir / "build" / "verilator_build" / f"V{args.module}"
    if existing_exe.is_file():
        build_started = True

    run_plan = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "gate_netlist": str(args.gate_netlist.resolve()),
        "out_dir": str(args.out_dir.resolve()),
        "smoke": SMOKE,
        "formal_workloads": selected_workloads(args),
        "fixed_policy": {
            "verilate_jobs": args.verilate_jobs,
            "jobs": args.jobs,
            "verilator_threads": args.verilator_threads,
            "trace_depth": args.trace_depth,
            "output_split": args.output_split,
            "output_split_cfuncs": args.output_split_cfuncs,
            "output_split_ctrace": args.output_split_ctrace,
            "cflags": args.cflags,
            "compare": False,
            "trace_saif": True,
            "no_timing": True,
            "hierarchical": False,
        },
    }
    write_json(args.out_dir / "phase1b_gate_saif_run_plan.json", run_plan)

    if not args.skip_smoke:
        smoke_dir = args.out_dir / SMOKE["name"]
        print(f"[phase1b] extract smoke vectors: {SMOKE['name']}", flush=True)
        smoke_max_cycles = SMOKE.get("max_cycles")
        vectors = extract_vectors(args, smoke_dir, SMOKE["workload"], Path(SMOKE["rtl_vcd"]), int(SMOKE["trace_end_ps"]), int(smoke_max_cycles) if smoke_max_cycles is not None else None)
        print(f"[phase1b] run smoke replay/build: {SMOKE['name']}", flush=True)
        smoke_manifest = replay(args, smoke_dir, SMOKE["workload"], "smoke", vectors, int(SMOKE["trace_start_ps"]), int(SMOKE["trace_end_ps"]), int(smoke_max_cycles) if smoke_max_cycles is not None else None, skip_build=build_started)
        build_started = True
        write_method_report(args, smoke_manifest, formal_manifests, "smoke-complete")
    if args.stop_after_smoke:
        write_json(args.out_dir / "phase1b_gate_saif_handoff_manifest.json", {"status": "stopped_after_smoke", "smoke": smoke_manifest, "formal_workloads": []})
        return

    for workload in selected_workloads(args):
        name = str(workload["name"])
        run_dir = args.out_dir / name
        print(f"[phase1b] extract formal vectors: {name}", flush=True)
        vectors = extract_vectors(args, run_dir, name, Path(workload["rtl_vcd"]), int(workload["trace_end_ps"]))
        print(f"[phase1b] run formal replay: {name}", flush=True)
        manifest = replay(
            args,
            run_dir,
            name,
            "formal",
            vectors,
            int(workload["trace_start_ps"]),
            int(workload["trace_end_ps"]),
            None,
            skip_build=build_started,
        )
        build_started = True
        formal_manifests.append(manifest)
        write_method_report(args, smoke_manifest, formal_manifests, f"completed-through-{name}")
        write_json(
            args.out_dir / "phase1b_gate_saif_handoff_manifest.json",
            {
                "status": f"completed-through-{name}",
                "method": "Verilator zero-delay Gemmini boundary replay with direct SAIF trace",
                "phase3_handoff": formal_manifests,
                "smoke_excluded_from_phase3": smoke_manifest,
                "old_validation_excluded": str((args.run_root / "gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full").resolve()),
                "phase3_requirement": "Cadence read_saif scope/instance mapping and annotation coverage report required before power use.",
            },
        )

    write_method_report(args, smoke_manifest, formal_manifests, "complete")
    write_json(
        args.out_dir / "phase1b_gate_saif_handoff_manifest.json",
        {
            "status": "complete",
            "method": "Verilator zero-delay Gemmini boundary replay with direct SAIF trace",
            "phase3_handoff": formal_manifests,
            "smoke_excluded_from_phase3": smoke_manifest,
            "old_validation_excluded": str((args.run_root / "gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full").resolve()),
            "phase3_requirement": "Cadence read_saif scope/instance mapping and annotation coverage report required before power use.",
        },
    )
    print(json.dumps({"status": "complete", "phase3_saifs": [m["saif"] for m in formal_manifests]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
