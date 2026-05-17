#!/usr/bin/env python3
"""Summarize Phase 4 PACT and HotSpot thermal results.

PACT writes grid arrays in its internal row order, where row 0 is the physical
TOP of the die. The Stage 3 DEF/grid convention uses grid_y=0 at the physical
BOTTOM. All user-facing PACT artifacts written by this script are therefore
converted to the DEF physical coordinate convention with a y-axis flip. Raw PACT
row-order grids are retained with *_pact_raw_order filenames for auditability.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = "stage4_tiled_matmul_os_baseline"
AMBIENT_K = 318.15


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pact-dir", type=Path, default=Path("thermal/pact") / BASE)
    parser.add_argument("--hotspot-dir", type=Path, default=Path("thermal/hotspot") / BASE)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts/stage4"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing or empty required file: {path}")


def load_layer(path: Path, grid: int) -> np.ndarray:
    require_file(path)
    vals = np.loadtxt(path, delimiter=",")
    vals = vals.reshape(-1)
    if vals.size != grid * grid:
        raise SystemExit(f"unexpected layer size in {path}: {vals.size}")
    return vals.reshape((grid, grid))


def physical_from_pact_raw(raw_grid: np.ndarray) -> np.ndarray:
    """Convert PACT internal raw row order to DEF physical grid_y order.

    Stage 3 and DEF use grid_y=0 at the physical bottom. PACT's GridManager maps
    physical y=0 to the bottom of its internal array, but steady/transient result
    files are emitted in numpy row-major order, so raw row 0 is physical top.
    """
    return raw_grid[::-1, :].copy()


def physical_transient_from_pact_raw(raw_transient: np.ndarray) -> np.ndarray:
    return raw_transient[:, :, ::-1, :].copy()


def load_xyce_csv(path: Path, grid: int) -> tuple[np.ndarray, np.ndarray]:
    require_file(path)
    data = np.genfromtxt(path, delimiter=",", names=True)
    names = data.dtype.names
    if names is None or names[0].upper() != "TIME":
        raise SystemExit(f"unexpected Xyce CSV header in {path}")
    time = np.asarray(data[names[0]], dtype=float)
    cols = [np.asarray(data[name], dtype=float) for name in names[1:]]
    arr = np.vstack(cols).T
    expected = 2 * grid * grid
    if arr.shape[1] != expected:
        raise SystemExit(f"unexpected transient column count: {arr.shape[1]} != {expected}")
    arr = arr.reshape((arr.shape[0], 2, grid, grid))
    return time, arr


def load_hotspot(path: Path) -> tuple[list[str], np.ndarray]:
    require_file(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        rows = [[float(x) for x in row] for row in reader if row]
    return header, np.asarray(rows, dtype=float)


def write_grid_csv(path: Path, grid_data: np.ndarray, y_name: str = "grid_y") -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow([y_name, *[f"x{x}" for x in range(grid_data.shape[1])]])
        for y, row in enumerate(grid_data):
            writer.writerow([y, *[f"{v:.6f}" for v in row]])


def write_stats_csv(path: Path, time_s: np.ndarray, transient: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["step", "time_s", "layer0_min_k", "layer0_mean_k", "layer0_max_k", "layer1_min_k", "layer1_mean_k", "layer1_max_k"])
        for i, t in enumerate(time_s):
            l0 = transient[i, 0]
            l1 = transient[i, 1]
            writer.writerow([i, f"{t:.9g}", f"{l0.min():.6f}", f"{l0.mean():.6f}", f"{l0.max():.6f}", f"{l1.min():.6f}", f"{l1.mean():.6f}", f"{l1.max():.6f}"])


def write_pact_rank(path: Path, grid_data: np.ndarray, top_n: int = 20) -> None:
    flat = grid_data.reshape(-1)
    order = np.argsort(flat)[::-1][:top_n]
    grid = grid_data.shape[0]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["rank", "grid_x", "grid_y", "temperature_k", "delta_over_ambient_k"])
        for rank, idx in enumerate(order, start=1):
            y, x = divmod(int(idx), grid)
            temp = float(flat[idx])
            writer.writerow([rank, x, y, f"{temp:.6f}", f"{temp - AMBIENT_K:.6f}"])


def write_hotspot_stats(path: Path, names: list[str], temps: np.ndarray, sample_s: float) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["step", "time_s", "min_k", "mean_k", "max_k", "max_block"])
        for i, row in enumerate(temps):
            max_idx = int(np.argmax(row))
            writer.writerow([i, f"{i * sample_s:.9g}", f"{row.min():.6f}", f"{row.mean():.6f}", f"{row.max():.6f}", names[max_idx]])


def write_hotspot_rank(path: Path, names: list[str], temps: np.ndarray) -> None:
    final = temps[-1]
    peak = temps.max(axis=0)
    order = np.argsort(peak)[::-1]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["rank", "block", "peak_temperature_k", "final_temperature_k", "peak_delta_over_ambient_k"])
        for rank, idx in enumerate(order, start=1):
            writer.writerow([rank, names[int(idx)], f"{peak[idx]:.6f}", f"{final[idx]:.6f}", f"{peak[idx] - AMBIENT_K:.6f}"])


def save_heatmap(path: Path, data: np.ndarray, title: str) -> None:
    plt.figure(figsize=(7.0, 5.8))
    im = plt.imshow(data, origin="lower", cmap="inferno", aspect="equal")
    plt.colorbar(im, label="Temperature (K)")
    plt.xlabel("grid x")
    plt.ylabel("grid y, DEF physical y-up")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def save_trace(path: Path, pact_time: np.ndarray, pact_stats: np.ndarray, hotspot_time: np.ndarray, hotspot_temps: np.ndarray) -> None:
    pact_l0_max = pact_stats[:, 0].reshape((pact_stats.shape[0], -1)).max(axis=1)
    pact_l0_mean = pact_stats[:, 0].reshape((pact_stats.shape[0], -1)).mean(axis=1)
    hot_max = hotspot_temps.max(axis=1)
    hot_mean = hotspot_temps.mean(axis=1)
    plt.figure(figsize=(7.2, 4.6))
    plt.plot(pact_time * 1e6, pact_l0_max, label="PACT layer0 max", linewidth=1.8)
    plt.plot(pact_time * 1e6, pact_l0_mean, label="PACT layer0 mean", linewidth=1.5)
    plt.plot(hotspot_time * 1e6, hot_max, label="HotSpot max", linewidth=1.5)
    plt.plot(hotspot_time * 1e6, hot_mean, label="HotSpot mean", linewidth=1.5)
    plt.xlabel("time (us)")
    plt.ylabel("Temperature (K)")
    plt.title("Phase 4 transient thermal trend")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def save_bar(path: Path, names: list[str], temps: np.ndarray) -> None:
    final = temps[-1]
    y_min = max(300.0, float(final.min()) - 0.02)
    y_max = float(final.max()) + 0.02
    plt.figure(figsize=(7.2, 4.2))
    plt.bar(names, final)
    plt.ylim(y_min, y_max)
    plt.xticks(rotation=25, ha="right")
    plt.ylabel("Temperature (K)")
    plt.title("HotSpot final coarse-block temperatures, zoomed y-axis")
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def hot_xy(grid_data: np.ndarray) -> tuple[int, int, float]:
    idx = int(np.argmax(grid_data.reshape(-1)))
    y, x = divmod(idx, grid_data.shape[1])
    return x, y, float(grid_data[y, x])


def write_coordinate_fix(path: Path, grid: int, steady_l0_raw: np.ndarray, steady_l0_phys: np.ndarray,
                         transient_raw: np.ndarray, transient_phys: np.ndarray) -> dict:
    raw_x, raw_y, raw_t = hot_xy(steady_l0_raw)
    phys_x, phys_y, phys_t = hot_xy(steady_l0_phys)
    final_raw_x, final_raw_y, final_raw_t = hot_xy(transient_raw[-1, 0])
    final_phys_x, final_phys_y, final_phys_t = hot_xy(transient_phys[-1, 0])
    fix = {
        "coordinate_convention": "DEF physical coordinates, grid_y=0 at die bottom and grid_y increases upward",
        "pact_raw_output_order": "PACT raw row 0 is physical die top; row index is not DEF grid_y",
        "fix_applied_to_user_facing_pact_artifacts": "physical_grid_y = grid - 1 - pact_raw_row_y",
        "grid": grid,
        "steady_raw_hot_x": raw_x,
        "steady_raw_hot_row_y": raw_y,
        "steady_raw_hot_temperature_k": raw_t,
        "steady_physical_hot_x": phys_x,
        "steady_physical_hot_y": phys_y,
        "steady_physical_hot_temperature_k": phys_t,
        "transient_final_raw_hot_x": final_raw_x,
        "transient_final_raw_hot_row_y": final_raw_y,
        "transient_final_raw_hot_temperature_k": final_raw_t,
        "transient_final_physical_hot_x": final_phys_x,
        "transient_final_physical_hot_y": final_phys_y,
        "transient_final_physical_hot_temperature_k": final_phys_t,
        "raw_artifacts_retained_with_suffix": "*_pact_raw_order.*",
    }
    path.write_text(json.dumps(fix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv_path = path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["metric", "value"])
        for key, value in fix.items():
            writer.writerow([key, value])
    return fix


def rel(path: Path) -> str:
    return str(path)


def write_reports(args: argparse.Namespace, manifest: dict, summary: dict) -> None:
    reports = args.reports_dir
    reports.mkdir(parents=True, exist_ok=True)
    pact_report = reports / f"{BASE}_pact_thermal_report.md"
    hot_report = reports / f"{BASE}_hotspot_report.md"
    final_report = reports / f"{BASE}_summary.md"

    pact_report.write_text(f"""# Stage 4 PACT Thermal Report: tiled_matmul_os Baseline

Date: 2026-05-03

## Scope

This report covers the PACT mainline thermal result for `tiled_matmul_os_baseline`. Inputs are derived from Stage 3 normalized proxy grid power, so the result remains a thermal-flow prototype and not signoff thermal analysis.

## Coordinate Correction

**Important:** PACT raw grid result files are not in DEF physical `grid_y` order. PACT raw row `0` corresponds to the physical top of the die, while Stage 3 DEF/grid artifacts use `grid_y=0` at the physical bottom. All user-facing PACT artifacts in `artifacts/stage4/` now apply:

```text
physical_grid_y = {manifest['grid']} - 1 - pact_raw_row_y
```

Raw PACT row-order CSVs are retained only as audit artifacts with `_pact_raw_order` in the filename. The main PACT grid/rank/heatmap files are the corrected physical-coordinate versions.

## Inputs

- Stage 3 grid: `{manifest['grid']} x {manifest['grid']}`
- Die side: `{manifest['die_side_m']} m`
- Time rows: `{manifest['time_rows']}`
- Peak proxy power: `{manifest['peak_total_power_w']:.6f} W` at Stage 3 time index `{manifest['peak_time_index']}`
- PACT steady solver: SuperLU
- PACT transient solver: generated PACT SPICE transient netlist solved by serial Xyce with `number_of_core = 1`

## Compatibility Notes

The local PACT transient path required two compatibility repairs recorded in `docs/gemmini_thermal_issue_log.md` items 69 and 70. The coordinate correction recorded here is a post-processing orientation fix only; it does not change the PACT solver inputs or vendored PACT source.

## Results, DEF Physical Coordinates

- Steady layer0 min/mean/max: `{summary['pact_steady_l0_min']:.3f}` / `{summary['pact_steady_l0_mean']:.3f}` / `{summary['pact_steady_l0_max']:.3f}` K
- Steady layer1 min/mean/max: `{summary['pact_steady_l1_min']:.3f}` / `{summary['pact_steady_l1_mean']:.3f}` / `{summary['pact_steady_l1_max']:.3f}` K
- Steady layer0 hotspot: physical grid `({summary['pact_steady_hot_x']}, {summary['pact_steady_hot_y']})`, raw PACT row-order location `({summary['pact_steady_raw_hot_x']}, {summary['pact_steady_raw_hot_y']})`
- Transient layer0 final max: `{summary['pact_transient_l0_final_max']:.3f}` K
- Transient layer0 peak max: `{summary['pact_transient_l0_peak_max']:.3f}` K
- Transient solved rows: `{summary['pact_transient_rows']}`

## Artifacts

- `{rel(args.artifacts_dir / 'pact_coordinate_fix_manifest.json')}`
- `{rel(args.artifacts_dir / 'pact_coordinate_fix_manifest.csv')}`
- `{rel(args.artifacts_dir / 'pact_steady_layer0_grid.csv')}`
- `{rel(args.artifacts_dir / 'pact_steady_layer0_grid_pact_raw_order.csv')}`
- `{rel(args.artifacts_dir / 'heatmap_steady_pact_layer0.png')}`
- `{rel(args.artifacts_dir / 'heatmap_transient_final_pact_layer0.png')}`
- `{rel(args.artifacts_dir / 'thermal_trace_pact_vs_hotspot.png')}`
- `{rel(args.artifacts_dir / 'pact_transient_stats.csv')}`
- `{rel(args.artifacts_dir / 'pact_hotspot_rank.csv')}`
""", encoding="utf-8")

    hot_report.write_text(f"""# Stage 4 HotSpot Coarse Comparison Report: tiled_matmul_os Baseline

Date: 2026-05-03

## Scope

HotSpot is used only as a coarse block-level trend comparison. It is not the fine-grained result. Power is aggregated into the five coarse blocks: `pe_array`, `controller_execute`, `load_store_datapath`, `scratchpad_accumulator_context`, and `other_context`.

## Results

- HotSpot rows: `{summary['hotspot_rows']}`
- Final max block: `{summary['hotspot_final_max_block']}`
- Final max temperature: `{summary['hotspot_final_max']:.3f}` K
- Peak max temperature: `{summary['hotspot_peak_max']:.3f}` K

HotSpot block coordinates are hand-authored coarse regions and are not a placed-standard-cell physical distribution. Use corrected PACT artifacts for fine-grid physical-coordinate inspection.

## Artifacts

- `{rel(args.artifacts_dir / 'hotspot_transient_stats.csv')}`
- `{rel(args.artifacts_dir / 'hotspot_block_rank.csv')}`
- `{rel(args.artifacts_dir / 'hotspot_block_final.png')}`
- `{rel(args.artifacts_dir / 'thermal_trace_pact_vs_hotspot.png')}`
""", encoding="utf-8")

    final_report.write_text(f"""# Stage 4 Summary: tiled_matmul_os Baseline

Date: 2026-05-03

## Acceptance Status

Stage 4 completed for the historical baseline route as a `proxy / thermal-flow prototype`: PACT steady, PACT transient serial-Xyce, HotSpot coarse comparison, figures, tables, and reports were generated.

## Coordinate Correction

**Important:** PACT raw row order was found to be vertically inverted relative to the Stage 3 DEF physical grid convention. All main PACT artifacts under `artifacts/stage4/` have been regenerated in DEF physical coordinates with `grid_y=0` at the die bottom. Raw PACT row-order grids are retained only with `_pact_raw_order` filenames.

## Key Answers, Corrected Physical Coordinates

1. Hotspot location: PACT steady layer0 peaks at physical grid `({summary['pact_steady_hot_x']}, {summary['pact_steady_hot_y']})` with `{summary['pact_steady_l0_max']:.3f}` K. The old raw row-order coordinate was `({summary['pact_steady_raw_hot_x']}, {summary['pact_steady_raw_hot_y']})` and must not be used as a physical location.
2. Sustained high-load behavior: PACT steady reaches a peak delta of `{summary['pact_steady_l0_max'] - AMBIENT_K:.3f}` K over ambient under the normalized `1 W` peak proxy-power condition; the short transient window remains near ambient and peaks at `{summary['pact_transient_l0_peak_max']:.3f}` K.
3. PACT vs HotSpot trend: both flows run successfully on the same Stage 3 proxy power source. HotSpot is only a five-block coarse trend comparison; corrected PACT provides the fine-grid physical hotspot pattern.
4. Standard-cell interpretation: use `standard_cell_context/` after this regeneration because it now overlays standard-cell power/density against corrected PACT physical coordinates.

## Caveats

- Stage 3 power is normalized proxy power, not signoff power.
- Stage 2 remains `proxy / non-signoff`, has residual DRC, and has no SDF.
- SRAM macro bodies are not detailed thermal sources.
- The coordinate fix is a post-processing orientation fix. It does not rerun or alter PACT solver inputs.

## Main Artifacts

- `{rel(args.artifacts_dir / 'pact_coordinate_fix_manifest.json')}`
- `{rel(args.artifacts_dir / 'heatmap_steady_pact_layer0.png')}`
- `{rel(args.artifacts_dir / 'heatmap_transient_final_pact_layer0.png')}`
- `{rel(args.artifacts_dir / 'thermal_trace_pact_vs_hotspot.png')}`
- `{rel(args.artifacts_dir / 'temperature_comparison_summary.csv')}`
""", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.artifacts_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.pact_dir / f"manifest_{BASE}_inputs.json"
    require_file(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    grid = int(manifest["grid"])
    sample_s = float(manifest["hotspot_sampling_interval_s"])

    steady_l0_raw = load_layer(args.pact_dir / f"steady_temperature_{BASE}.grid.steady.layer0", grid)
    steady_l1_raw = load_layer(args.pact_dir / f"steady_temperature_{BASE}.grid.steady.layer1", grid)
    time_s, transient_raw = load_xyce_csv(args.pact_dir / f"transient_temperature_{BASE}.sanitized.cir.csv", grid)
    steady_l0 = physical_from_pact_raw(steady_l0_raw)
    steady_l1 = physical_from_pact_raw(steady_l1_raw)
    transient = physical_transient_from_pact_raw(transient_raw)

    hot_names, hot_temps = load_hotspot(args.hotspot_dir / f"{BASE}.ttrace")
    hotspot_time = np.arange(hot_temps.shape[0]) * sample_s

    write_grid_csv(args.artifacts_dir / "pact_steady_layer0_grid.csv", steady_l0)
    write_grid_csv(args.artifacts_dir / "pact_steady_layer1_grid.csv", steady_l1)
    write_grid_csv(args.artifacts_dir / "pact_transient_final_layer0_grid.csv", transient[-1, 0])
    write_grid_csv(args.artifacts_dir / "pact_steady_layer0_grid_pact_raw_order.csv", steady_l0_raw, y_name="pact_raw_row_y")
    write_grid_csv(args.artifacts_dir / "pact_steady_layer1_grid_pact_raw_order.csv", steady_l1_raw, y_name="pact_raw_row_y")
    write_grid_csv(args.artifacts_dir / "pact_transient_final_layer0_grid_pact_raw_order.csv", transient_raw[-1, 0], y_name="pact_raw_row_y")
    write_stats_csv(args.artifacts_dir / "pact_transient_stats.csv", time_s, transient)
    write_pact_rank(args.artifacts_dir / "pact_hotspot_rank.csv", steady_l0)
    write_hotspot_stats(args.artifacts_dir / "hotspot_transient_stats.csv", hot_names, hot_temps, sample_s)
    write_hotspot_rank(args.artifacts_dir / "hotspot_block_rank.csv", hot_names, hot_temps)

    fix = write_coordinate_fix(
        args.artifacts_dir / "pact_coordinate_fix_manifest.json",
        grid,
        steady_l0_raw,
        steady_l0,
        transient_raw,
        transient,
    )

    save_heatmap(args.artifacts_dir / "heatmap_steady_pact_layer0.png", steady_l0, "PACT steady layer0 temperature, physical coordinates")
    save_heatmap(args.artifacts_dir / "heatmap_transient_final_pact_layer0.png", transient[-1, 0], "PACT transient final layer0 temperature, physical coordinates")
    save_trace(args.artifacts_dir / "thermal_trace_pact_vs_hotspot.png", time_s, transient, hotspot_time, hot_temps)
    save_bar(args.artifacts_dir / "hotspot_block_final.png", hot_names, hot_temps)

    hot_final_idx = int(np.argmax(hot_temps[-1]))
    hot_x, hot_y, _hot_temp = hot_xy(steady_l0)
    raw_hot_x, raw_hot_y, _raw_hot_temp = hot_xy(steady_l0_raw)
    summary = {
        "coordinate_view": "DEF physical grid_y, y=0 at die bottom",
        "pact_yflip_applied": True,
        "pact_raw_output_order": "row 0 is physical die top",
        "pact_steady_l0_min": float(steady_l0.min()),
        "pact_steady_l0_mean": float(steady_l0.mean()),
        "pact_steady_l0_max": float(steady_l0.max()),
        "pact_steady_l1_min": float(steady_l1.min()),
        "pact_steady_l1_mean": float(steady_l1.mean()),
        "pact_steady_l1_max": float(steady_l1.max()),
        "pact_steady_hot_x": int(hot_x),
        "pact_steady_hot_y": int(hot_y),
        "pact_steady_raw_hot_x": int(raw_hot_x),
        "pact_steady_raw_hot_y": int(raw_hot_y),
        "pact_transient_rows": int(transient.shape[0]),
        "pact_transient_l0_final_max": float(transient[-1, 0].max()),
        "pact_transient_l0_peak_max": float(transient[:, 0].reshape((transient.shape[0], -1)).max()),
        "hotspot_rows": int(hot_temps.shape[0]),
        "hotspot_final_max_block": hot_names[hot_final_idx],
        "hotspot_final_max": float(hot_temps[-1].max()),
        "hotspot_peak_max": float(hot_temps.max()),
    }
    with (args.artifacts_dir / "temperature_comparison_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["metric", "value"])
        for key, value in summary.items():
            writer.writerow([key, value])
    write_reports(args, manifest, summary)
    out = dict(summary)
    out["coordinate_fix"] = fix
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
