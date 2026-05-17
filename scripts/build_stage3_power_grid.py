#!/usr/bin/env python3
"""Build Stage 3 proxy grid power data from target activity and Stage 2 DEF.

The model is a documented proxy: target RTL-window activity is distributed to
placed standard-cell instances by region and area, then normalized to a chosen
standard-cell total power for thermal-flow prototyping.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

FILLER_MASTER_RE = re.compile(r"(FILLER|DECAP|TAPCELL|TAPCELL|TIEHI|TIELO)", re.IGNORECASE)
PLACED_RE = re.compile(r"\+\s+(?:PLACED|FIXED)\s+\(\s+(-?\d+)\s+(-?\d+)\s+\)")
DIEAREA_RE = re.compile(r"DIEAREA\s+\(\s+(-?\d+)\s+(-?\d+)\s+\)\s+\(\s+(-?\d+)\s+(-?\d+)\s+\)")
CELL_RE = re.compile(r"^\s*cell\s*\(\s*([^\s\)]+)")
AREA_RE = re.compile(r"^\s*area\s*:\s*([0-9.eE+-]+)")
LEAK_RE = re.compile(r"^\s*cell_leakage_power\s*:\s*([0-9.eE+-]+)")

TARGET_REGIONS = ["pe_array", "controller", "scratchpad", "load_store_dma", "gemmini_other"]
REGION_ORDER = TARGET_REGIONS + ["clock_tree", "unmapped_standard_cell"]


@dataclass
class Component:
    instance: str
    master: str
    x: int
    y: int
    grid_x: int
    grid_y: int
    region: str
    area: float
    power_w: float = 0.0
    activity_weight: float = 0.0


def unescape_def_name(name: str) -> str:
    if name.startswith("\\"):
        return name[1:]
    return name


def classify_instance(name: str, master: str) -> str:
    lower = unescape_def_name(name).lower()
    if lower.startswith("clk") or "clock" in lower:
        return "clock_tree"
    if "load_controller" in lower or "store_controller" in lower or "streamreader" in lower or "streamwriter" in lower or "dma" in lower:
        return "load_store_dma"
    if "spad" in lower or "scratch" in lower or "sp_bank" in lower:
        return "scratchpad"
    if "mesh" in lower or "macunit" in lower or re.search(r"(^|[/_.])pe(_|[/_.]|$)", lower):
        return "pe_array"
    if "ex_controller" in lower or "reservation_station" in lower or "cmd" in lower or "rob" in lower or "unroller" in lower or "loopmatmul" in lower:
        return "controller"
    if "gemmini" in lower or lower.startswith("mod"):
        return "gemmini_other"
    return "unmapped_standard_cell"


def parse_liberty_areas(paths: list[Path]) -> tuple[dict[str, float], dict[str, float]]:
    areas: dict[str, float] = {}
    leakage: dict[str, float] = {}
    for path in paths:
        current: str | None = None
        with path.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = CELL_RE.match(line)
                if m:
                    current = m.group(1)
                    continue
                if current is None:
                    continue
                m = AREA_RE.match(line)
                if m:
                    areas[current] = float(m.group(1))
                    continue
                m = LEAK_RE.match(line)
                if m:
                    leakage[current] = float(m.group(1))
                    continue
    return areas, leakage


def median(values: list[float], default: float) -> float:
    clean = sorted(v for v in values if v > 0)
    if not clean:
        return default
    return clean[len(clean) // 2]


def parse_activity(path: Path) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    region = defaultdict(lambda: {"signals": 0.0, "toggles": 0.0, "activity_sum": 0.0, "width_sum": 0.0})
    meta: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("region", "gemmini_other") or "gemmini_other"
            toggles = float(row.get("toggle_count", "0") or 0)
            width = float(row.get("width", "1") or 1)
            activity = float(row.get("normalized_activity", "0") or 0)
            region[name]["signals"] += 1
            region[name]["toggles"] += toggles
            region[name]["activity_sum"] += activity
            region[name]["width_sum"] += width
            for key in ("candidate_start_ps", "candidate_end_ps", "refined_start_ps", "refined_end_ps", "time_steps", "last_time_ps"):
                if key in row and key not in meta:
                    meta[key] = row[key]
    return dict(region), meta


def parse_def_components(def_path: Path, grid: int, areas: dict[str, float], default_area: float, include_unmapped: bool = True) -> tuple[tuple[int, int, int, int], list[Component], dict[str, int]]:
    die = (0, 0, 1, 1)
    components: list[Component] = []
    counts = defaultdict(int)
    in_components = False
    with def_path.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            if die == (0, 0, 1, 1):
                m = DIEAREA_RE.search(line)
                if m:
                    die = tuple(int(m.group(i)) for i in range(1, 5))  # type: ignore[assignment]
            if line.startswith("COMPONENTS"):
                in_components = True
                continue
            if in_components and line.startswith("END COMPONENTS"):
                break
            if not in_components or not line.startswith("    - "):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            inst = parts[1]
            master = parts[2]
            counts["raw_components"] += 1
            if inst.startswith("FILLER_") or inst.startswith("PHY_") or FILLER_MASTER_RE.search(master):
                counts["skipped_physical_fill_tap_decap_tie"] += 1
                continue
            m = PLACED_RE.search(line)
            if not m:
                counts["skipped_unplaced"] += 1
                continue
            x = int(m.group(1))
            y = int(m.group(2))
            x0, y0, x1, y1 = die
            gx = min(grid - 1, max(0, int((x - x0) * grid / max(1, x1 - x0))))
            gy = min(grid - 1, max(0, int((y - y0) * grid / max(1, y1 - y0))))
            region = classify_instance(inst, master)
            if region == "unmapped_standard_cell" and not include_unmapped:
                counts["skipped_unmapped"] += 1
                continue
            area = areas.get(master, default_area)
            components.append(Component(inst, master, x, y, gx, gy, region, area))
            counts[f"region_{region}"] += 1
    return die, components, dict(counts)


def assign_power(components: list[Component], activity: dict[str, dict[str, float]], proxy_total_power_w: float) -> dict[str, float]:
    region_area = defaultdict(float)
    for comp in components:
        region_area[comp.region] += comp.area
    raw_region_weight: dict[str, float] = {}
    for region in REGION_ORDER:
        act = activity.get(region, {})
        avg_activity = act.get("activity_sum", 0.0) / max(1.0, act.get("signals", 0.0))
        toggles = act.get("toggles", 0.0)
        if region == "clock_tree":
            avg_activity = max(avg_activity, 0.02 * max((activity.get(r, {}).get("activity_sum", 0.0) / max(1.0, activity.get(r, {}).get("signals", 0.0))) for r in TARGET_REGIONS))
            toggles = 0.02 * sum(activity.get(r, {}).get("toggles", 0.0) for r in TARGET_REGIONS)
        if region == "unmapped_standard_cell":
            avg_activity = 0.05 * max((activity.get(r, {}).get("activity_sum", 0.0) / max(1.0, activity.get(r, {}).get("signals", 0.0))) for r in TARGET_REGIONS)
            toggles = 0.05 * sum(activity.get(r, {}).get("toggles", 0.0) for r in TARGET_REGIONS)
        raw_region_weight[region] = max(0.0, region_area.get(region, 0.0) * max(avg_activity, 1e-12) * max(1.0, math.log10(max(10.0, toggles))))
    total_weight = sum(raw_region_weight.values()) or 1.0
    region_power = {region: proxy_total_power_w * weight / total_weight for region, weight in raw_region_weight.items()}
    for comp in components:
        area_total = region_area.get(comp.region, 0.0) or 1.0
        comp.power_w = region_power.get(comp.region, 0.0) * comp.area / area_total
        comp.activity_weight = raw_region_weight.get(comp.region, 0.0) * comp.area / area_total
    return region_power


def write_instance_grid_map(path: Path, components: list[Component]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["instance", "master", "region", "x_dbu", "y_dbu", "grid_x", "grid_y", "cell_area", "proxy_power_w", "activity_weight"])
        writer.writeheader()
        for comp in components:
            writer.writerow({
                "instance": comp.instance,
                "master": comp.master,
                "region": comp.region,
                "x_dbu": comp.x,
                "y_dbu": comp.y,
                "grid_x": comp.grid_x,
                "grid_y": comp.grid_y,
                "cell_area": f"{comp.area:.8g}",
                "proxy_power_w": f"{comp.power_w:.12g}",
                "activity_weight": f"{comp.activity_weight:.12g}",
            })


def read_bin_scales(path: Path | None, default_time_ps: int) -> list[tuple[int, int, float, int]]:
    if path is None:
        return [(0, default_time_ps, 1.0, 0)]
    rows = []
    totals = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total = float(row.get("total_target_toggles", "0") or 0)
            rows.append((int(row.get("bin", len(rows))), int(float(row.get("start_ps", default_time_ps) or default_time_ps)), total))
            if total > 0:
                totals.append(total)
    if not rows:
        return [(0, default_time_ps, 1.0, 0)]
    peak_active = max(totals) if totals else 1.0
    return [(idx, start_ps, (total / peak_active if peak_active > 0 else 0.0), int(total)) for idx, start_ps, total in rows]


def write_grid_power(path: Path, ptrace_path: Path, components: list[Component], grid: int, bin_scales: list[tuple[int, int, float, int]]) -> None:
    base_grid_power = [[0.0 for _ in range(grid)] for _ in range(grid)]
    for comp in components:
        base_grid_power[comp.grid_y][comp.grid_x] += comp.power_w
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time_index", "time_ps", "grid_x", "grid_y", "power_w"])
        writer.writeheader()
        for time_index, time_ps, scale, _total in bin_scales:
            for gy in range(grid):
                for gx in range(grid):
                    writer.writerow({"time_index": time_index, "time_ps": time_ps, "grid_x": gx, "grid_y": gy, "power_w": f"{base_grid_power[gy][gx] * scale:.12g}"})
    with ptrace_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = [f"g{gx}_{gy}" for gy in range(grid) for gx in range(grid)]
        writer.writerow(["time_ps", *header])
        for _time_index, time_ps, scale, _total in bin_scales:
            writer.writerow([time_ps, *[f"{base_grid_power[gy][gx] * scale:.12g}" for gy in range(grid) for gx in range(grid)]])


def write_region_summary(path: Path, components: list[Component], activity: dict[str, dict[str, float]], region_power: dict[str, float]) -> None:
    summary = defaultdict(lambda: {"instances": 0, "area": 0.0, "power": 0.0})
    for comp in components:
        row = summary[comp.region]
        row["instances"] += 1
        row["area"] += comp.area
        row["power"] += comp.power_w
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["region", "instances", "cell_area", "activity_signals", "activity_toggles", "proxy_power_w", "power_share"])
        writer.writeheader()
        total_power = sum(row["power"] for row in summary.values()) or 1.0
        for region, row in sorted(summary.items(), key=lambda kv: kv[1]["power"], reverse=True):
            act = activity.get(region, {})
            writer.writerow({
                "region": region,
                "instances": int(row["instances"]),
                "cell_area": f"{row['area']:.8g}",
                "activity_signals": int(act.get("signals", 0)),
                "activity_toggles": int(act.get("toggles", 0)),
                "proxy_power_w": f"{row['power']:.12g}",
                "power_share": f"{row['power'] / total_power:.8g}",
            })


def write_top_reports(power_path: Path, toggle_path: Path, components: list[Component], activity_csv: Path) -> None:
    top_power = sorted(components, key=lambda c: c.power_w, reverse=True)[:50]
    with power_path.open("w", encoding="utf-8") as f:
        f.write("# Stage 3 Top Proxy Power Instances\n\n")
        f.write("| rank | instance | master | region | grid | proxy_power_w | cell_area |\n")
        f.write("| ---: | --- | --- | --- | --- | ---: | ---: |\n")
        for rank, comp in enumerate(top_power, 1):
            f.write(f"| {rank} | `{comp.instance}` | `{comp.master}` | `{comp.region}` | `{comp.grid_x},{comp.grid_y}` | {comp.power_w:.12g} | {comp.area:.8g} |\n")
    rows = []
    with activity_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    rows.sort(key=lambda r: int(float(r.get("toggle_count", "0") or 0)), reverse=True)
    with toggle_path.open("w", encoding="utf-8") as f:
        f.write("# Stage 3 Top Target Toggle Signals\n\n")
        f.write("| rank | region | toggles | changes | signal |\n")
        f.write("| ---: | --- | ---: | ---: | --- |\n")
        for rank, row in enumerate(rows[:50], 1):
            f.write(f"| {rank} | `{row.get('region','')}` | {row.get('toggle_count','0')} | {row.get('value_change_count','0')} | `{row.get('signal_path','')}` |\n")


def write_mapping_manifest(path: Path, components: list[Component], counts: dict[str, int], activity: dict[str, dict[str, float]], grid: int) -> None:
    region_counts = defaultdict(int)
    for comp in components:
        region_counts[comp.region] += 1
    mapped = sum(count for region, count in region_counts.items() if region not in {"unmapped_standard_cell"})
    total = sum(region_counts.values()) or 1
    with path.open("w", encoding="utf-8") as f:
        f.write("# Stage 3 Activity Mapping Manifest\n\n")
        f.write("## Mapping Strategy\n\n")
        f.write("- RTL source activity: Stage 1 target-scoped Gemmini VCD window refinement.\n")
        f.write("- Physical source: Stage 2 proxy `6_final.def`.\n")
        f.write("- Gate/physical mapping: DEF instance-name prefix classification.\n")
        f.write("- Grid: `%d x %d`.\n" % (grid, grid))
        f.write("- Filler, tap, decap, and tie cells are excluded from active standard-cell proxy power.\n")
        f.write("- Unmatched standard cells are kept as `unmapped_standard_cell` context and assigned low background proxy activity.\n\n")
        f.write("## Physical Mapping Counts\n\n")
        f.write(f"- raw_components: `{counts.get('raw_components', 0)}`\n")
        f.write(f"- active_components_written: `{total}`\n")
        f.write(f"- skipped_physical_fill_tap_decap_tie: `{counts.get('skipped_physical_fill_tap_decap_tie', 0)}`\n")
        f.write(f"- mapped_non_unmapped_components: `{mapped}`\n")
        f.write(f"- mapped_ratio: `{mapped / total:.6f}`\n")
        f.write("\n| region | instances | activity_signals | activity_toggles |\n")
        f.write("| --- | ---: | ---: | ---: |\n")
        for region, count in sorted(region_counts.items(), key=lambda kv: kv[1], reverse=True):
            act = activity.get(region, {})
            f.write(f"| `{region}` | {count} | {int(act.get('signals', 0))} | {int(act.get('toggles', 0))} |\n")
        f.write("\n## Blackbox / Proxy Boundary\n\n")
        f.write("Memory macro bodies remain proxy/blackbox context from Stage 2 and are not modeled as detailed SRAM thermal sources.\n")


def write_hotspot_traceback(path: Path, components: list[Component], grid: int) -> None:
    by_grid = defaultdict(lambda: {"power": 0.0, "components": []})
    for comp in components:
        key = (comp.grid_x, comp.grid_y)
        by_grid[key]["power"] += comp.power_w
        by_grid[key]["components"].append(comp)
    top_grids = sorted(by_grid.items(), key=lambda kv: kv[1]["power"], reverse=True)[:20]
    with path.open("w", encoding="utf-8") as f:
        f.write("# Stage 3 Hotspot Traceback\n\n")
        f.write("This report traces top proxy-power grid bins back to contributing placed instances.\n\n")
        for rank, ((gx, gy), row) in enumerate(top_grids, 1):
            f.write(f"## Grid {rank}: `{gx},{gy}`\n\n")
            f.write(f"- proxy_power_w: `{row['power']:.12g}`\n")
            comps = sorted(row["components"], key=lambda c: c.power_w, reverse=True)[:10]
            f.write("\n| rank | instance | master | region | proxy_power_w |\n")
            f.write("| ---: | --- | --- | --- | ---: |\n")
            for idx, comp in enumerate(comps, 1):
                f.write(f"| {idx} | `{comp.instance}` | `{comp.master}` | `{comp.region}` | {comp.power_w:.12g} |\n")
            f.write("\n")


def write_method_report(path: Path, args: argparse.Namespace, die: tuple[int, int, int, int], counts: dict[str, int], region_power: dict[str, float], activity_meta: dict[str, str], components: list[Component], default_area: float) -> None:
    total_power = sum(region_power.values())
    region_counts = defaultdict(int)
    for comp in components:
        region_counts[comp.region] += 1
    with path.open("w", encoding="utf-8") as f:
        f.write("# Stage 3 Power Trace Method\n\n")
        f.write("## Acceptance Level\n\n")
        f.write("Stage 3 output is a reproducible proxy grid-power waveform for Stage 4 thermal-flow prototyping. It is not signoff power.\n\n")
        f.write("## Inputs\n\n")
        f.write(f"- target_activity_csv: `{args.target_activity_csv}`\n")
        f.write(f"- target_bin_csv: `{args.target_bin_csv}`\n")
        f.write(f"- def: `{args.def_file}`\n")
        f.write(f"- netlist: `{args.netlist}`\n")
        f.write(f"- sdc: `{args.sdc}`\n")
        f.write(f"- spef: `{args.spef}`\n")
        f.write(f"- liberty_files: `{len(args.liberty)}`\n")
        f.write("- SDF: unavailable from Phase 2 proxy flow.\n")
        f.write("\n## Window\n\n")
        for key in ("candidate_start_ps", "candidate_end_ps", "refined_start_ps", "refined_end_ps", "time_steps"):
            f.write(f"- {key}: `{activity_meta.get(key, '')}`\n")
        f.write("\n## Grid And Geometry\n\n")
        f.write(f"- grid: `{args.grid} x {args.grid}`\n")
        f.write(f"- diearea_dbu: `{die}`\n")
        f.write(f"- active_components: `{len(components)}`\n")
        f.write(f"- raw_components: `{counts.get('raw_components', 0)}`\n")
        f.write(f"- skipped_fill_tap_decap_tie: `{counts.get('skipped_physical_fill_tap_decap_tie', 0)}`\n")
        f.write("\n## Power Model\n\n")
        f.write(f"- proxy_total_power_w: `{args.proxy_total_power_w}`\n")
        f.write(f"- normalized_output_power_w: `{total_power:.12g}`\n")
        f.write("- transient_bin_scaling: `max target bin = proxy_total_power_w`\n")
        f.write(f"- default_cell_area_for_missing_liberty_area: `{default_area:.8g}`\n")
        f.write("- Model: target-window RTL activity is aggregated by Gemmini region, then distributed over placed standard-cell area in the matching DEF region.\n")
        f.write("- `clock_tree` and `unmapped_standard_cell` receive low background proxy activity so their placed area remains visible without dominating target regions.\n")
        f.write("- `6_report.log` / `6_report.json` IR numbers are not used.\n")
        f.write("\n| region | instances | proxy_power_w | share |\n")
        f.write("| --- | ---: | ---: | ---: |\n")
        for region, power in sorted(region_power.items(), key=lambda kv: kv[1], reverse=True):
            f.write(f"| `{region}` | {region_counts.get(region, 0)} | {power:.12g} | {power / max(total_power, 1e-30):.8g} |\n")
        f.write("\n## Limitations\n\n")
        f.write("- No gate-level SAIF or SDF is available, so switching power is a calibrated proxy rather than OpenSTA signoff power.\n")
        f.write("- SPEF/SDC/netlist are recorded as Stage 2 electrical context, but this first Stage 3 artifact does not solve detailed net capacitance power per gate.\n")
        f.write("- Memory macro body power is not modeled as detailed SRAM thermal power.\n")


def write_preflight_manifest(path: Path, args: argparse.Namespace, die: tuple[int, int, int, int], counts: dict[str, int]) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("# Stage 3 Input Manifest\n\n")
        f.write("## Inputs\n\n")
        for label, value in [
            ("target_activity_csv", args.target_activity_csv),
            ("def", args.def_file),
            ("netlist", args.netlist),
            ("sdc", args.sdc),
            ("spef", args.spef),
        ]:
            p = Path(value)
            f.write(f"- {label}: `{p}` size_bytes=`{p.stat().st_size if p.exists() else 'missing'}`\n")
        f.write("\n## Stage 2 Caveats\n\n")
        f.write("- Phase 2 input is `proxy / non-signoff`.\n")
        f.write("- No SDF is available; Stage 3 records SDC/SPEF/netlist/DEF instead.\n")
        f.write("- Residual DRC and memory blackbox/proxy caveats remain inherited from Stage 2.\n")
        f.write("- ORFS final report JSON/log remain in the logs tree and were not moved.\n")
        f.write("\n## DEF Sanity\n\n")
        f.write(f"- diearea_dbu: `{die}`\n")
        f.write(f"- raw_components: `{counts.get('raw_components', 0)}`\n")
        f.write(f"- skipped_physical_fill_tap_decap_tie: `{counts.get('skipped_physical_fill_tap_decap_tie', 0)}`\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-activity-csv", required=True, type=Path)
    parser.add_argument("--def-file", required=True, type=Path)
    parser.add_argument("--netlist", required=True, type=Path)
    parser.add_argument("--sdc", required=True, type=Path)
    parser.add_argument("--spef", required=True, type=Path)
    parser.add_argument("--liberty", required=True, type=Path, action="append")
    parser.add_argument("--target-bin-csv", type=Path)
    parser.add_argument("--power-dir", required=True, type=Path)
    parser.add_argument("--reports-dir", required=True, type=Path)
    parser.add_argument("--grid", type=int, default=64)
    parser.add_argument("--proxy-total-power-w", type=float, default=1.0)
    args = parser.parse_args()
    if args.grid < 1:
        parser.error("--grid must be >= 1")
    if args.proxy_total_power_w <= 0:
        parser.error("--proxy-total-power-w must be > 0")
    return args


def main() -> int:
    args = parse_args()
    args.power_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    areas, _leakage = parse_liberty_areas(args.liberty)
    default_area = median(list(areas.values()), 1.0)
    activity, activity_meta = parse_activity(args.target_activity_csv)
    die, components, counts = parse_def_components(args.def_file, args.grid, areas, default_area)
    if not components:
        raise SystemExit("no active DEF components parsed")
    region_power = assign_power(components, activity, args.proxy_total_power_w)

    write_instance_grid_map(args.power_dir / "stage3_tiled_matmul_os_baseline_instance_grid_map.csv", components)
    time_ps = int(float(activity_meta.get("refined_start_ps", "0") or 0))
    bin_scales = read_bin_scales(args.target_bin_csv, time_ps)
    write_grid_power(args.power_dir / "stage3_tiled_matmul_os_baseline_grid_power.csv", args.power_dir / "stage3_tiled_matmul_os_baseline_transient_ptrace.csv", components, args.grid, bin_scales)
    write_region_summary(args.power_dir / "stage3_tiled_matmul_os_baseline_region_power_summary.csv", components, activity, region_power)
    write_top_reports(args.reports_dir / "stage3_tiled_matmul_os_baseline_top_power_instances.md", args.reports_dir / "stage3_tiled_matmul_os_baseline_top_toggle_instances.md", components, args.target_activity_csv)
    write_mapping_manifest(args.reports_dir / "stage3_tiled_matmul_os_baseline_activity_mapping_manifest.md", components, counts, activity, args.grid)
    write_hotspot_traceback(args.reports_dir / "stage3_tiled_matmul_os_baseline_hotspot_traceback.md", components, args.grid)
    write_method_report(args.reports_dir / "stage3_tiled_matmul_os_baseline_power_trace_method.md", args, die, counts, region_power, activity_meta, components, default_area)
    write_preflight_manifest(args.reports_dir / "stage3_tiled_matmul_os_baseline_input_manifest.md", args, die, counts)
    metadata = {
        "grid": args.grid,
        "proxy_total_power_w": args.proxy_total_power_w,
        "diearea_dbu": die,
        "active_components": len(components),
        "counts": counts,
        "region_power_w": region_power,
        "target_bin_csv": str(args.target_bin_csv) if args.target_bin_csv else None,
    }
    (args.power_dir / "stage3_tiled_matmul_os_baseline_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    print(f"active_components={len(components)} grid={args.grid} proxy_total_power_w={args.proxy_total_power_w}")
    print(f"power_dir={args.power_dir}")
    print(f"reports_dir={args.reports_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
