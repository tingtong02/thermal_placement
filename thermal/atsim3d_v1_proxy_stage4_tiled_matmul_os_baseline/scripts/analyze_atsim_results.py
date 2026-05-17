#!/usr/bin/env python3
"""Summarize ATSim3D v1 proxy and public example result files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "thermal" / "atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline"
RESULTS_DIR = RUN_DIR / "results"
INPUTS_DIR = RUN_DIR / "inputs"

RESULT_FILES = [
    ("proxy_stage4_tiled_matmul_os_baseline", "proxy_2d_style", INPUTS_DIR / "proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res"),
    ("ATSim3D_pub_2DIC", "2DIC_active_layer", ROOT / "third_party" / "ATSim3D_pub" / "2DIC" / "Intel_ID1_lcf.layer0.res"),
    ("ATSim3D_pub_Mono3D_layer6", "Mono3D_active_layer_top", ROOT / "third_party" / "ATSim3D_pub" / "Mono3D" / "Mono3D_lcf.layer6.res"),
    ("ATSim3D_pub_Mono3D_layer11", "Mono3D_active_layer_bottom", ROOT / "third_party" / "ATSim3D_pub" / "Mono3D" / "Mono3D_lcf.layer11.res"),
    ("ATSim3D_pub_TSV3D_layer2", "TSV3D_active_layer_top", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer2.res"),
    ("ATSim3D_pub_TSV3D_layer7", "TSV3D_active_layer_bottom", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer7.res"),
    ("ATSim3D_pub_TSV3D_layer3", "TSV3D_substrate_between_active_layers", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer3.res"),
    ("ATSim3D_pub_TSV3D_layer8", "TSV3D_bottom_substrate", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer8.res"),
]


def summarize_xyz(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing result file: {path}")
    count = 0
    total = 0.0
    min_t = float("inf")
    max_t = float("-inf")
    min_xy = [None, None]
    max_xy = [None, None]
    unique_x = set()
    unique_y = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) < 3:
                raise SystemExit(f"bad result line in {path}: {line[:120]}")
            x = float(parts[0])
            y = float(parts[1])
            temp = float(parts[2])
            count += 1
            total += temp
            unique_x.add(x)
            unique_y.add(y)
            if temp < min_t:
                min_t = temp
                min_xy = [x, y]
            if temp > max_t:
                max_t = temp
                max_xy = [x, y]
    if count == 0:
        raise SystemExit(f"empty result file: {path}")
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "points": count,
        "unique_x": len(unique_x),
        "unique_y": len(unique_y),
        "min_k": min_t,
        "max_k": max_t,
        "mean_k": total / count,
        "delta_k": max_t - min_t,
        "min_x_m": min_xy[0],
        "min_y_m": min_xy[1],
        "max_x_m": max_xy[0],
        "max_y_m": max_xy[1],
    }


def summarize_pact(path: Path) -> dict:
    vals = [float(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    return {
        "path": str(path.relative_to(ROOT)),
        "points": len(vals),
        "min_k": min(vals),
        "max_k": max(vals),
        "mean_k": sum(vals) / len(vals),
        "delta_k": max(vals) - min(vals),
    }


def summarize_hotspot(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        values = []
        for row in reader:
            if not row:
                continue
            values.extend(float(x) for x in row if x)
    return {
        "path": str(path.relative_to(ROOT)),
        "samples_times_blocks": len(values),
        "min_k": min(values),
        "max_k": max(values),
        "mean_k": sum(values) / len(values),
        "delta_k": max(values) - min(values),
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    details = []
    for case, role, path in RESULT_FILES:
        stats = summarize_xyz(path)
        stats["case"] = case
        stats["role"] = role
        details.append(stats)
        rows.append(stats)

    pact = summarize_pact(ROOT / "thermal" / "pact" / "stage4_tiled_matmul_os_baseline" / "steady_temperature_stage4_tiled_matmul_os_baseline.grid.steady.layer0")
    hotspot = summarize_hotspot(ROOT / "thermal" / "hotspot" / "stage4_tiled_matmul_os_baseline" / "stage4_tiled_matmul_os_baseline.ttrace")
    comparison = {"atsim_results": details, "pact_stage4_layer0": pact, "hotspot_stage4_ttrace": hotspot}

    summary_csv = RESULTS_DIR / "atsim_result_summary.csv"
    fieldnames = ["case", "role", "path", "bytes", "points", "unique_x", "unique_y", "min_k", "max_k", "mean_k", "delta_k", "min_x_m", "min_y_m", "max_x_m", "max_y_m"]
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    (RESULTS_DIR / "atsim_result_summary.json").write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(comparison, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
