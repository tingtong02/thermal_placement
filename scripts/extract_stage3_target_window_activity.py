#!/usr/bin/env python3
"""Extract Stage 3 target-scoped activity from the Stage 1 VCD.

This is intentionally narrower than the full Stage 1 parser: it keeps the
full-SoC VCD as the activity source, but only counts Gemmini target scopes
inside the coarse steady_high_load candidate window.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_vcd_activity import (  # noqa: E402
    Signal,
    build_body_chunks,
    classify,
    load_category_terms,
    parse_value_change,
    parse_vcd_header,
    value_toggle_delta,
)

TARGET_REGIONS = {"pe_array", "controller", "scratchpad", "load_store_dma", "gemmini_other"}
CLOCK_RE = re.compile(r"(^|[._])(clock|clk|reset)([._]|$)", re.IGNORECASE)


@dataclass
class TargetMeta:
    path: str
    width: int
    region: str


@dataclass
class SignalStats:
    first: str | None = None
    last: str | None = None
    toggles: int = 0
    changes: int = 0


def read_candidate_window(path: Path, window_name: str) -> tuple[int, int]:
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("window") == window_name:
                return int(float(row["start_ps"])), int(float(row["end_ps"]))
    raise SystemExit(f"window {window_name!r} not found in {path}")


def is_target_signal(signal: Signal, terms: dict[str, list[str]], include_clocks: bool) -> str | None:
    lower = signal.path.lower()
    if ".gemmini" not in lower and not lower.startswith("gemmini"):
        return None
    if "monitor" in lower or "watchdog" in lower:
        return None
    if not include_clocks and CLOCK_RE.search(signal.path.rsplit(".", 1)[-1]):
        return None
    region = classify(signal.path, terms)
    if region in TARGET_REGIONS:
        return region
    return None


def parse_target_chunk(
    path_str: str,
    start: int,
    end: int,
    target_meta: dict[str, TargetMeta],
    candidate_start: int,
    candidate_end: int,
    bins: int,
    max_body_bytes: int,
) -> tuple[int, int, dict[str, SignalStats], list[dict[str, int]]]:
    path = Path(path_str)
    stats: dict[str, SignalStats] = {}
    bin_regions = [defaultdict(int) for _ in range(bins)]
    time_steps = 0
    last_time = 0
    current_time = -1
    effective_end = end
    if max_body_bytes > 0:
        effective_end = min(end, start + max_body_bytes)
    span = max(1, candidate_end - candidate_start)

    with path.open("rb") as f:
        f.seek(start)
        while True:
            pos = f.tell()
            if pos >= effective_end:
                break
            raw = f.readline()
            if not raw:
                break
            line = raw.decode("ascii", errors="ignore").strip()
            if not line:
                continue
            if line.startswith("#"):
                try:
                    current_time = int(line[1:])
                except ValueError:
                    continue
                if candidate_start <= current_time <= candidate_end:
                    time_steps += 1
                    last_time = current_time
                if current_time > candidate_end:
                    break
                continue
            if current_time < candidate_start or current_time > candidate_end:
                continue
            parsed = parse_value_change(line)
            if parsed is None:
                continue
            code, value = parsed
            meta = target_meta.get(code)
            if meta is None:
                continue
            item = stats.get(code)
            if item is None:
                stats[code] = SignalStats(first=value, last=value)
                continue
            delta = value_toggle_delta(item.last or value, value, meta.width)
            if delta:
                item.toggles += delta
                item.changes += 1
                idx = min(bins - 1, max(0, int((current_time - candidate_start) * bins / span)))
                bin_regions[idx][meta.region] += delta
            item.last = value

    return time_steps, last_time, stats, [dict(row) for row in bin_regions]


def merge_results(
    results: list[tuple[int, int, dict[str, SignalStats], list[dict[str, int]]]],
    target_meta: dict[str, TargetMeta],
    bins: int,
) -> tuple[int, int, dict[str, SignalStats], list[dict[str, int]]]:
    total_steps = 0
    last_time = 0
    merged: dict[str, SignalStats] = {}
    merged_bins = [defaultdict(int) for _ in range(bins)]
    for time_steps, chunk_last_time, chunk_stats, chunk_bins in results:
        total_steps += time_steps
        if chunk_last_time:
            last_time = chunk_last_time
        for code, item in chunk_stats.items():
            meta = target_meta[code]
            dest = merged.get(code)
            if dest is None:
                merged[code] = SignalStats(first=item.first, last=item.last, toggles=item.toggles, changes=item.changes)
                continue
            if dest.last is not None and item.first is not None:
                delta = value_toggle_delta(dest.last, item.first, meta.width)
                if delta:
                    dest.toggles += delta
                    dest.changes += 1
            dest.toggles += item.toggles
            dest.changes += item.changes
            dest.last = item.last
        for idx, row in enumerate(chunk_bins):
            for region, toggles in row.items():
                merged_bins[idx][region] += int(toggles)
    return total_steps, last_time, merged, [dict(row) for row in merged_bins]


def choose_refined_window(bin_rows: list[dict[str, int]], candidate_start: int, candidate_end: int) -> tuple[int, int, int, int]:
    totals = [sum(row.get(region, 0) for region in TARGET_REGIONS) for row in bin_rows]
    if not totals or max(totals) <= 0:
        return candidate_start, candidate_end, 0, 0
    threshold = max(1, int(max(totals) * 0.05))
    active = [idx for idx, value in enumerate(totals) if value >= threshold]
    if not active:
        active = [idx for idx, value in enumerate(totals) if value > 0]
    first = min(active)
    last = max(active)
    span = candidate_end - candidate_start
    bins = len(totals)
    refined_start = candidate_start + int(span * first / bins)
    refined_end = candidate_start + int(span * (last + 1) / bins)
    return refined_start, refined_end, threshold, max(totals)



def write_bin_csv(path: Path, workload: str, candidate_start: int, candidate_end: int, bin_rows: list[dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    span = candidate_end - candidate_start
    bins = len(bin_rows)
    fields = ["workload", "bin", "start_ps", "end_ps", "total_target_toggles", "pe_array", "controller", "scratchpad", "load_store_dma", "gemmini_other"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for idx, row in enumerate(bin_rows):
            out = {
                "workload": workload,
                "bin": idx,
                "start_ps": candidate_start + int(span * idx / bins),
                "end_ps": candidate_start + int(span * (idx + 1) / bins),
            }
            total = sum(row.get(region_name, 0) for region_name in TARGET_REGIONS)
            out["total_target_toggles"] = total
            for region_name in TARGET_REGIONS:
                out[region_name] = row.get(region_name, 0)
            writer.writerow(out)

def write_activity_csv(
    path: Path,
    workload: str,
    target_meta: dict[str, TargetMeta],
    stats: dict[str, SignalStats],
    time_steps: int,
    last_time: int,
    candidate_start: int,
    candidate_end: int,
    refined_start: int,
    refined_end: int,
) -> None:
    rows = []
    denom = max(1, time_steps)
    for code, item in stats.items():
        meta = target_meta[code]
        if item.toggles <= 0:
            continue
        rows.append(
            {
                "workload": workload,
                "signal_path": meta.path,
                "region": meta.region,
                "width": meta.width,
                "toggle_count": item.toggles,
                "value_change_count": item.changes,
                "candidate_start_ps": candidate_start,
                "candidate_end_ps": candidate_end,
                "refined_start_ps": refined_start,
                "refined_end_ps": refined_end,
                "time_steps": time_steps,
                "last_time_ps": last_time,
                "normalized_activity": item.toggles / float(denom * max(1, meta.width)),
            }
        )
    rows.sort(key=lambda row: int(row["toggle_count"]), reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "workload", "signal_path", "region", "width", "toggle_count", "value_change_count",
            "candidate_start_ps", "candidate_end_ps", "refined_start_ps", "refined_end_ps", "time_steps",
            "last_time_ps", "normalized_activity",
        ])
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    workload: str,
    vcd: Path,
    candidate_start: int,
    candidate_end: int,
    refined_start: int,
    refined_end: int,
    workers: int,
    target_count: int,
    active_count: int,
    time_steps: int,
    threshold: int,
    max_bin: int,
    bin_rows: list[dict[str, int]],
    stats: dict[str, SignalStats],
    target_meta: dict[str, TargetMeta],
) -> None:
    region = defaultdict(lambda: {"signals": 0, "toggles": 0, "changes": 0})
    for code, item in stats.items():
        if item.toggles <= 0:
            continue
        meta = target_meta[code]
        region[meta.region]["signals"] += 1
        region[meta.region]["toggles"] += item.toggles
        region[meta.region]["changes"] += item.changes
    top = sorted(((code, item) for code, item in stats.items() if item.toggles > 0), key=lambda kv: kv[1].toggles, reverse=True)[:20]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Stage 1 Target-Scoped Window Refinement For Stage 3\n\n")
        f.write("## Inputs\n\n")
        f.write(f"- workload: `{workload}`\n")
        f.write(f"- source_vcd: `{vcd}`\n")
        f.write(f"- candidate_window_ps: `{candidate_start}` to `{candidate_end}`\n")
        f.write(f"- workers: `{workers}`\n")
        f.write(f"- target_signal_count_from_header: `{target_count}`\n")
        f.write("\n## Refined Window\n\n")
        f.write(f"- refined_start_ps: `{refined_start}`\n")
        f.write(f"- refined_end_ps: `{refined_end}`\n")
        f.write(f"- active_target_signal_count: `{active_count}`\n")
        f.write(f"- time_steps_seen_in_candidate: `{time_steps}`\n")
        f.write(f"- active_bin_threshold_toggles: `{threshold}`\n")
        f.write(f"- max_bin_toggles: `{max_bin}`\n")
        f.write("\n## Region Toggle Summary\n\n")
        f.write("| region | active_signals | toggles | value_changes |\n")
        f.write("| --- | ---: | ---: | ---: |\n")
        for name, row in sorted(region.items(), key=lambda kv: kv[1]["toggles"], reverse=True):
            f.write(f"| `{name}` | {row['signals']} | {row['toggles']} | {row['changes']} |\n")
        f.write("\n## Top Target Signals\n\n")
        f.write("| rank | region | toggles | changes | signal |\n")
        f.write("| ---: | --- | ---: | ---: | --- |\n")
        for rank, (code, item) in enumerate(top, 1):
            meta = target_meta[code]
            f.write(f"| {rank} | `{meta.region}` | {item.toggles} | {item.changes} | `{meta.path}` |\n")
        f.write("\n## Bin Totals\n\n")
        f.write("| bin | start_ps | end_ps | total_target_toggles | pe_array | controller | scratchpad | load_store_dma | gemmini_other |\n")
        f.write("| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        span = candidate_end - candidate_start
        bins = len(bin_rows)
        for idx, row in enumerate(bin_rows):
            start = candidate_start + int(span * idx / bins)
            end = candidate_start + int(span * (idx + 1) / bins)
            total = sum(row.get(region_name, 0) for region_name in TARGET_REGIONS)
            f.write(
                f"| {idx} | {start} | {end} | {total} | {row.get('pe_array', 0)} | {row.get('controller', 0)} | "
                f"{row.get('scratchpad', 0)} | {row.get('load_store_dma', 0)} | {row.get('gemmini_other', 0)} |\n"
            )
        f.write("\n## Method Note\n\n")
        f.write("This refinement scans the full-SoC VCD source but counts only Gemmini target scopes in the coarse steady_high_load candidate interval. ")
        f.write("It is target-scoped RTL activity for the Stage 3 proxy power model, not gate-level SAIF signoff activity.\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcd", required=True, type=Path)
    parser.add_argument("--window-csv", required=True, type=Path)
    parser.add_argument("--hierarchy-map", type=Path, default=Path("configs/gemmini/hierarchy_map.yaml"))
    parser.add_argument("--workload", default="stage1_tiled_matmul_os_baseline_20260423")
    parser.add_argument("--candidate-window", default="steady_high_load")
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    parser.add_argument("--bin-csv", type=Path)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--bins", type=int, default=64)
    parser.add_argument("--include-clocks", action="store_true")
    parser.add_argument("--max-body-bytes", type=int, default=0, help="debug/smoke only: cap bytes parsed per chunk")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 128:
        parser.error("--workers must be between 1 and 128")
    if args.bins < 1:
        parser.error("--bins must be >= 1")
    return args


def main() -> int:
    args = parse_args()
    candidate_start, candidate_end = read_candidate_window(args.window_csv, args.candidate_window)
    terms = load_category_terms(args.hierarchy_map)
    signals, body_offset = parse_vcd_header(args.vcd)
    target_meta: dict[str, TargetMeta] = {}
    for code, signal in signals.items():
        region = is_target_signal(signal, terms, args.include_clocks)
        if region is None:
            continue
        target_meta[code] = TargetMeta(path=signal.path, width=signal.width, region=region)
    if not target_meta:
        raise SystemExit("no target Gemmini signals found in VCD header")

    chunks = build_body_chunks(args.vcd, body_offset, args.workers)
    if args.max_body_bytes > 0:
        chunks = chunks[:1]
    if len(chunks) == 1:
        results = [parse_target_chunk(str(args.vcd), chunks[0][0], chunks[0][1], target_meta, candidate_start, candidate_end, args.bins, args.max_body_bytes)]
    else:
        with ProcessPoolExecutor(max_workers=len(chunks)) as executor:
            futures = [
                executor.submit(parse_target_chunk, str(args.vcd), start, end, target_meta, candidate_start, candidate_end, args.bins, args.max_body_bytes)
                for start, end in chunks
            ]
            results = [future.result() for future in futures]
    time_steps, last_time, stats, bin_rows = merge_results(results, target_meta, args.bins)
    refined_start, refined_end, threshold, max_bin = choose_refined_window(bin_rows, candidate_start, candidate_end)
    active_count = sum(1 for item in stats.values() if item.toggles > 0)
    write_activity_csv(args.output_csv, args.workload, target_meta, stats, time_steps, last_time, candidate_start, candidate_end, refined_start, refined_end)
    if args.bin_csv is not None:
        write_bin_csv(args.bin_csv, args.workload, candidate_start, candidate_end, bin_rows)
    write_report(args.output_report, args.workload, args.vcd, candidate_start, candidate_end, refined_start, refined_end, len(chunks), len(target_meta), active_count, time_steps, threshold, max_bin, bin_rows, stats, target_meta)
    print(f"target_signals={len(target_meta)} active_signals={active_count} time_steps={time_steps}")
    print(f"candidate_window={candidate_start}:{candidate_end} refined_window={refined_start}:{refined_end}")
    print(f"output_csv={args.output_csv}")
    if args.bin_csv is not None:
        print(f"bin_csv={args.bin_csv}")
    print(f"output_report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
