#!/usr/bin/env python3
"""Select coarse Stage 1 windows without rescanning a very large VCD.

The full aggregate activity is produced by extract_vcd_activity.py. This helper
uses that completed region CSV plus simulator log markers to write a practical
window report for Stage 1, avoiding extra full passes over tens of GiB of VCD.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def read_region_csv(path: Path) -> tuple[int, int, list[dict[str, str]]]:
    if not path.exists():
        return 0, 0, []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return 0, 0, []
    return int(float(rows[0].get("time_steps", "0") or 0)), int(float(rows[0].get("last_time_ps", "0") or 0)), rows


def infer_region_csv(window_csv: Path) -> Path:
    name = window_csv.name.replace("_window_activity.csv", "_region_activity.csv")
    return window_csv.with_name(name)


def infer_log_path(vcd: Path) -> Path:
    parts = list(vcd.parts)
    try:
        idx = parts.index("waves")
        parts[idx] = "logs"
        return Path(*parts).with_suffix(".log")
    except ValueError:
        return vcd.with_suffix(".log")


def parse_cycles(log_path: Path) -> tuple[list[int], bool, bool]:
    if not log_path.exists():
        return [], False, False
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    cycles = [int(match) for match in re.findall(r"Cycles taken:\s*(\d+)", text)]
    return cycles, "Starting slow CPU matmul" in text, "Starting gemmini matmul" in text


def workload_base(workload: str) -> str:
    for name in ("tiled_matmul_os", "tiled_matmul_ws", "mvin_mvout"):
        if name in workload:
            return name
    return workload


def write_window_csv(path: Path, workload: str, windows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["workload", "window", "start_ps", "end_ps", "selection", "notes"])
        writer.writeheader()
        for row in windows:
            out = dict(row)
            out["workload"] = workload
            writer.writerow(out)


def write_report(path: Path, workload: str, base: str, vcd: Path, region_csv: Path, log_path: Path, rows: list[dict[str, str]], windows: list[dict[str, object]], cycles: list[int], cpu_seen: bool, gemmini_seen: bool, time_steps: int, last_time: int) -> None:
    active_regions = sorted(rows, key=lambda row: int(float(row.get("toggle_count", "0") or 0)), reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Stage 1 {base} Windows\n\n")
        f.write("## Inputs\n\n")
        f.write(f"- workload: `{workload}`\n")
        f.write(f"- workload_base: `{base}`\n")
        f.write(f"- waveform: `{vcd}`\n")
        f.write(f"- region_activity: `{region_csv}`\n")
        f.write(f"- simulator_log: `{log_path}`\n")
        f.write(f"- time_steps: `{time_steps}`\n")
        f.write(f"- last_time_ps: `{last_time}`\n")
        f.write(f"- cpu_marker_seen: `{cpu_seen}`\n")
        f.write(f"- gemmini_marker_seen: `{gemmini_seen}`\n")
        if cycles:
            f.write(f"- cycle_markers: `{cycles}`\n")
        f.write("\n## Selected Windows\n\n")
        f.write("| window | start_ps | end_ps | selection |\n")
        f.write("| --- | ---: | ---: | --- |\n")
        for row in windows:
            f.write(f"| `{row['window']}` | {row['start_ps']} | {row['end_ps']} | {row['selection']} |\n")
        f.write("\n## Region Toggle Summary\n\n")
        f.write("| region | signals | toggles | avg_normalized_activity |\n")
        f.write("| --- | ---: | ---: | ---: |\n")
        for row in active_regions:
            f.write(
                f"| `{row.get('region', '')}` | {row.get('signal_count', '0')} | "
                f"{row.get('toggle_count', '0')} | {float(row.get('avg_normalized_activity', '0') or 0):.6e} |\n"
            )
        f.write("\n## Method Note\n\n")
        f.write("The full VCD is already parsed once for aggregate activity. To avoid repeated large VCD scans, ")
        f.write("this window report uses simulator phase markers and aggregate activity. ")
        if base == "tiled_matmul_os":
            f.write("For OS, Gemmini execution occurs after the CPU reference phase, so the coarse high-load window is the tail of the trace.\n")
        elif base == "tiled_matmul_ws":
            f.write("For WS, Gemmini execution occurs before the CPU reference phase, so the coarse high-load window is the early post-boot portion of the trace.\n")
        elif base == "mvin_mvout":
            f.write("For mvin_mvout, no matmul marker is expected; the coarse movement window covers the central active program interval.\n")
        else:
            f.write("Stage 3 may refine the exact gate-level interval after activity/netlist alignment.\n")


def choose_windows(base: str, last_time: int, gemmini_seen: bool) -> list[dict[str, object]]:
    cold_end = int(last_time * 0.10)
    if base == "tiled_matmul_os":
        steady_start = int(last_time * 0.90) if gemmini_seen else int(last_time * 0.50)
        return [
            {
                "window": "cold_start",
                "start_ps": 0,
                "end_ps": cold_end,
                "selection": "initial boot/program setup portion",
                "notes": "coarse fraction of full RTL trace",
            },
            {
                "window": "cpu_gold_reference",
                "start_ps": cold_end,
                "end_ps": steady_start,
                "selection": "CPU reference phase before OS Gemmini marker",
                "notes": "not the thermal target window",
            },
            {
                "window": "steady_high_load",
                "start_ps": steady_start,
                "end_ps": last_time,
                "selection": "tail interval containing OS Gemmini matmul and accelerator completion",
                "notes": "Stage 3 may refine this after gate/activity alignment",
            },
        ]
    if base == "tiled_matmul_ws":
        steady_start = cold_end
        steady_end = int(last_time * 0.35) if gemmini_seen else int(last_time * 0.50)
        return [
            {
                "window": "cold_start",
                "start_ps": 0,
                "end_ps": cold_end,
                "selection": "initial boot/program setup portion",
                "notes": "coarse fraction of full RTL trace",
            },
            {
                "window": "steady_high_load",
                "start_ps": steady_start,
                "end_ps": steady_end,
                "selection": "early post-boot interval containing WS Gemmini matmul before CPU reference",
                "notes": "Stage 3 may refine this after gate/activity alignment",
            },
            {
                "window": "cpu_gold_reference",
                "start_ps": steady_end,
                "end_ps": last_time,
                "selection": "CPU reference/check phase after WS Gemmini marker",
                "notes": "not the thermal target window",
            },
        ]
    if base == "mvin_mvout":
        movement_start = cold_end
        movement_end = int(last_time * 0.90)
        return [
            {
                "window": "cold_start",
                "start_ps": 0,
                "end_ps": cold_end,
                "selection": "initial boot/program setup portion",
                "notes": "coarse fraction of full RTL trace",
            },
            {
                "window": "data_movement_active",
                "start_ps": movement_start,
                "end_ps": movement_end,
                "selection": "central interval for mvin/mvout data movement and control activity",
                "notes": "no matmul marker is expected for this workload",
            },
            {
                "window": "program_completion",
                "start_ps": movement_end,
                "end_ps": last_time,
                "selection": "final program completion tail",
                "notes": "not the primary movement window",
            },
        ]
    return [
        {
            "window": "cold_start",
            "start_ps": 0,
            "end_ps": cold_end,
            "selection": "initial boot/program setup portion",
            "notes": "coarse fraction of full RTL trace",
        },
        {
            "window": "active_trace",
            "start_ps": cold_end,
            "end_ps": last_time,
            "selection": "remaining active trace interval",
            "notes": "workload-specific markers were not recognized",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcd", required=True, type=Path)
    parser.add_argument("--hierarchy-map", type=Path)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--window-csv", required=True, type=Path)
    parser.add_argument("--window-report", required=True, type=Path)
    parser.add_argument("--bins", type=int, default=200)
    args = parser.parse_args()

    region_csv = infer_region_csv(args.window_csv)
    log_path = infer_log_path(args.vcd)
    time_steps, last_time, rows = read_region_csv(region_csv)
    cycles, cpu_seen, gemmini_seen = parse_cycles(log_path)
    if last_time <= 0:
        last_time = 1

    base = workload_base(args.workload)
    windows = choose_windows(base, last_time, gemmini_seen)

    write_window_csv(args.window_csv, args.workload, windows)
    write_report(args.window_report, args.workload, base, args.vcd, region_csv, log_path, rows, windows, cycles, cpu_seen, gemmini_seen, time_steps, last_time)
    primary = next((row for row in windows if row["window"] in ("steady_high_load", "data_movement_active", "active_trace")), windows[-1])
    print(f"window_csv={args.window_csv}")
    print(f"window_report={args.window_report}")
    print(f"selected_primary_start_ps={primary['start_ps']} selected_primary_end_ps={primary['end_ps']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
