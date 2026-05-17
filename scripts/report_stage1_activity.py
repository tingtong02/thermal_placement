#!/usr/bin/env python3
"""Write Stage 1 activity summaries for signoff workloads."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

TARGET_REGION_ORDER = [
    ("pe_array", "PE array"),
    ("controller", "Gemmini controller"),
    ("load_store_dma", "Load/store DMA"),
    ("scratchpad", "Scratchpad-side datapath/context"),
    ("gemmini_other", "Other Gemmini datapath/control"),
]
NOISE_TOKENS = (
    "watchdog",
    "plusarg_reader",
)
WORKLOAD_METADATA = {
    "tiled_matmul_os": {
        "title": "Stage 1 tiled_matmul_os Activity Summary",
        "kind": "gemm",
        "role": "output-stationary GEMM compute baseline",
        "dataflow": "output-stationary via tiled_matmul_auto(..., OS)",
        "input_shape": "MAT_DIM_I=64, MAT_DIM_K=64, MAT_DIM_J=64 in bare-metal tiled_matmul_os.c",
        "required_regions": ("pe_array", "controller", "scratchpad", "gemmini_other"),
    },
    "tiled_matmul_ws": {
        "title": "Stage 1 tiled_matmul_ws Activity Summary",
        "kind": "gemm",
        "role": "weight-stationary GEMM dataflow contrast",
        "dataflow": "weight-stationary via tiled_matmul_auto(..., WS)",
        "input_shape": "MAT_DIM_I=64, MAT_DIM_K=64, MAT_DIM_J=64 in bare-metal tiled_matmul_ws.c",
        "required_regions": ("pe_array", "controller", "scratchpad", "gemmini_other"),
    },
    "mvin_mvout": {
        "title": "Stage 1 mvin_mvout Activity Summary",
        "kind": "movement",
        "role": "memory/control movement contrast, not a PE compute-heavy GEMM",
        "dataflow": "Gemmini mvin/mvout data movement; no tiled_matmul_auto dataflow marker expected",
        "input_shape": "N=8 DIM x DIM matrices; effective matrix shape is 16 x 16 for this config",
        "required_regions": ("controller", "load_store_dma", "scratchpad", "gemmini_other"),
    },
}


def metadata_for(workload: str) -> dict[str, object]:
    return WORKLOAD_METADATA.get(
        workload,
        {
            "title": f"Stage 1 {workload} Activity Summary",
            "kind": "unknown",
            "role": "unspecified workload",
            "dataflow": "not inferred by report script",
            "input_shape": "not inferred by report script",
            "required_regions": tuple(region for region, _ in TARGET_REGION_ORDER),
        },
    )


def size_text(path: Path) -> str:
    if not path.exists():
        return "missing"
    size = path.stat().st_size
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{size} B"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_int(value: str | None) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def parse_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def shorten_signal(signal: str, limit: int = 140) -> str:
    if len(signal) <= limit:
        return signal
    return "..." + signal[-(limit - 3) :]


def log_markers(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    cycles = [line.strip() for line in text.splitlines() if "Cycles taken:" in line]
    lower_text = text.lower()
    return {
        "starting_cpu_matmul": "Starting slow CPU matmul" in text,
        "starting_gemmini_matmul": "Starting gemmini matmul" in text,
        "verilator_finish": "Verilog $finish" in text or "$finish" in text,
        "failure_seen": any(token in lower_text for token in ["fail", "error", "assert"]),
        "cycles": cycles,
    }


def sort_signal_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: (
            parse_int(row.get("toggle_count")),
            parse_int(row.get("value_change_count")),
            row.get("signal_path", ""),
        ),
        reverse=True,
    )


def targeted_rows(signals: list[dict[str, str]], region: str, limit: int = 5) -> list[dict[str, str]]:
    picked: list[dict[str, str]] = []
    for row in signals:
        if row.get("region") != region:
            continue
        signal = row.get("signal_path", "")
        if "gemmini" not in signal:
            continue
        if any(token in signal for token in NOISE_TOKENS):
            continue
        picked.append(row)
    return sort_signal_rows(picked)[:limit]


def region_toggles(active_regions: list[dict[str, str]], region: str) -> int:
    row = next((item for item in active_regions if item.get("region") == region), None)
    return parse_int(row.get("toggle_count")) if row else 0


def stage1_accepted(meta: dict[str, object], active_regions: list[dict[str, str]], markers: dict[str, object], sim_status: str) -> bool:
    if sim_status != "0" or not active_regions or markers["failure_seen"] or not markers["verilator_finish"]:
        return False
    if meta["kind"] == "gemm" and not markers["starting_gemmini_matmul"]:
        return False
    required_regions = tuple(meta["required_regions"])
    return all(region_toggles(active_regions, region) > 0 for region in required_regions)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-tag", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--wave", required=True, type=Path)
    parser.add_argument("--signal-csv", required=True, type=Path)
    parser.add_argument("--region-csv", required=True, type=Path)
    parser.add_argument("--window-csv", required=True, type=Path)
    parser.add_argument("--window-report", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--sim-status", default="0")
    args = parser.parse_args()

    meta = metadata_for(args.workload)
    regions = read_csv(args.region_csv)
    signals = read_csv(args.signal_csv)
    markers = log_markers(args.log)
    active_regions = sorted(regions, key=lambda row: parse_int(row.get("toggle_count")), reverse=True)
    top_signals = sort_signal_rows(signals)[:10]
    time_steps = regions[0].get("time_steps", "unknown") if regions else "unknown"
    last_time = regions[0].get("last_time_ps", "unknown") if regions else "unknown"
    total_toggles = sum(parse_int(row.get("toggle_count")) for row in active_regions)
    target_region_names = {name for name, _ in TARGET_REGION_ORDER}
    target_toggles = sum(
        parse_int(row.get("toggle_count")) for row in active_regions if row.get("region") in target_region_names
    )
    target_share = (target_toggles / total_toggles) if total_toggles else 0.0
    accepted = stage1_accepted(meta, active_regions, markers, str(args.sim_status))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as f:
        f.write(f"# {meta['title']}\n\n")
        f.write("## Scope\n\n")
        f.write("- stage: `1`\n")
        f.write(f"- workload: `{args.workload}`\n")
        f.write(f"- run_tag: `{args.run_tag}`\n")
        f.write(f"- config: `{args.config}`\n")
        f.write(f"- role: `{meta['role']}`\n")
        f.write(f"- dataflow_or_behavior: `{meta['dataflow']}`\n")
        f.write(f"- input_shape: `{meta['input_shape']}`\n\n")

        f.write("## Functional Run\n\n")
        f.write(f"- sim_status: `{args.sim_status}`\n")
        f.write(f"- verilator_finish_seen: `{markers['verilator_finish']}`\n")
        f.write(f"- cpu_matmul_marker_seen: `{markers['starting_cpu_matmul']}`\n")
        f.write(f"- gemmini_matmul_marker_seen: `{markers['starting_gemmini_matmul']}`\n")
        f.write(f"- failure_marker_seen: `{markers['failure_seen']}`\n")
        for idx, line in enumerate(markers["cycles"], start=1):
            f.write(f"- cycles_line_{idx}: `{line}`\n")

        f.write("\n## Artifacts\n\n")
        f.write(f"- binary: `{args.binary}` ({size_text(args.binary)})\n")
        f.write(f"- stdout log: `{args.log}` ({size_text(args.log)})\n")
        f.write(f"- disassembly/out log: `{args.out}` ({size_text(args.out)})\n")
        f.write(f"- waveform: `{args.wave}` ({size_text(args.wave)})\n")
        f.write(f"- signal activity CSV: `{args.signal_csv}` ({size_text(args.signal_csv)})\n")
        f.write(f"- region activity CSV: `{args.region_csv}` ({size_text(args.region_csv)})\n")
        f.write(f"- window CSV: `{args.window_csv}` ({size_text(args.window_csv)})\n")
        f.write(f"- window report: `{args.window_report}`\n\n")

        f.write("## Activity Parse\n\n")
        f.write(f"- parsed_time_steps: `{time_steps}`\n")
        f.write(f"- last_time_ps: `{last_time}`\n")
        f.write(f"- total_region_toggles: `{total_toggles}`\n")
        f.write(f"- gemmini_target_region_toggles: `{target_toggles}`\n")
        f.write(f"- gemmini_target_region_toggle_share: `{target_share:.6%}`\n\n")

        f.write("## Region Activity\n\n")
        f.write("| region | signals | toggles | avg_normalized_activity |\n")
        f.write("| --- | ---: | ---: | ---: |\n")
        for row in active_regions:
            f.write(
                f"| `{row.get('region', '')}` | {row.get('signal_count', '0')} | "
                f"{row.get('toggle_count', '0')} | {parse_float(row.get('avg_normalized_activity')):.6e} |\n"
            )

        f.write("\n## Research Boundary Check\n\n")
        f.write("- The Stage 1 trace is a full `GemminiRocketConfig` SoC/TestHarness waveform, so whole-trace top toggles are expected to include Rocket core, cache, and TileLink context.\n")
        f.write("- For the active research target, the relevant check is whether Gemmini PE/control/datapath buckets required for this workload are non-zero and internally plausible.\n")
        for region, label in TARGET_REGION_ORDER:
            row = next((item for item in active_regions if item.get("region") == region), None)
            toggles = parse_int(row.get("toggle_count")) if row else 0
            signals_in_region = parse_int(row.get("signal_count")) if row else 0
            f.write(f"- {label}: `signals={signals_in_region}` `toggles={toggles}`\n")
        f.write("- `accumulator` remains zero in the current bucket summary, which is acceptable for this stage because memory arrays are not the detailed thermal target in the active plan.\n")

        f.write("\n## Targeted Gemmini Region Highlights\n\n")
        for region, label in TARGET_REGION_ORDER:
            rows = targeted_rows(signals, region)
            f.write(f"### {label}\n\n")
            if not rows:
                f.write("No Gemmini-scoped signal rows were found after filtering.\n\n")
                continue
            f.write("| rank | toggles | changes | signal |\n")
            f.write("| ---: | ---: | ---: | --- |\n")
            for idx, row in enumerate(rows, start=1):
                signal = shorten_signal(row.get("signal_path", ""))
                f.write(
                    f"| {idx} | {row.get('toggle_count', '0')} | {row.get('value_change_count', '0')} | `{signal}` |\n"
                )
            f.write("\n")

        f.write("## Global Top Toggle Signals (Full Trace Context)\n\n")
        f.write("| rank | region | toggles | changes | signal |\n")
        f.write("| ---: | --- | ---: | ---: | --- |\n")
        for idx, row in enumerate(top_signals, start=1):
            signal = shorten_signal(row.get("signal_path", ""))
            f.write(
                f"| {idx} | `{row.get('region', '')}` | {row.get('toggle_count', '0')} | "
                f"{row.get('value_change_count', '0')} | `{signal}` |\n"
            )

        f.write("\n## Stage 1 Conclusion\n\n")
        if accepted:
            if meta["kind"] == "movement":
                f.write("The run completed normally and produced parseable RTL activity for the mvin/mvout data movement workload. ")
                f.write("This is accepted as the Stage 1 memory/control movement contrast because controller, load/store DMA, scratchpad, and other Gemmini datapath buckets are non-zero. ")
            else:
                f.write("The run reached the Gemmini tiled matmul section and produced parseable RTL activity data. ")
                f.write("This is accepted for Stage 1 because Gemmini PE/control/datapath buckets required for the GEMM workload are non-zero. ")
            f.write("Selected windows are documented in the Stage 1 window report. Interpret global whole-trace rankings only as SoC context, not as the Stage 2 implementation boundary.\n")
        else:
            f.write("The run did not satisfy the workload-specific Stage 1 acceptance checks. Treat this as a Stage 1 blocker until inspected.\n")

    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
