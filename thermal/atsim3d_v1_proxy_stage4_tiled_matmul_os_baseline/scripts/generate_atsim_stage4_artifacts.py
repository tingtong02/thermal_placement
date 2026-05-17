#!/usr/bin/env python3
"""Generate Stage 4-style figures and tables for the ATSim3D v1 proxy rerun."""

from __future__ import annotations

import csv
import heapq
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "thermal" / "atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline"
INPUTS_DIR = RUN_DIR / "inputs"
RESULTS_DIR = RUN_DIR / "results"
ARTIFACTS_DIR = ROOT / "artifacts" / "stage4" / "atsim3d_v1_proxy"
PACT_GRID_PATH = ROOT / "artifacts" / "stage4" / "pact_steady_layer0_grid.csv"
PACT_RAW_GRID_PATH = ROOT / "artifacts" / "stage4" / "pact_steady_layer0_grid_pact_raw_order.csv"
HOTSPOT_STATS_PATH = ROOT / "artifacts" / "stage4" / "hotspot_transient_stats.csv"
HOTSPOT_RANK_PATH = ROOT / "artifacts" / "stage4" / "hotspot_block_rank.csv"
SUMMARY_JSON = RESULTS_DIR / "atsim_result_summary.json"
PROXY_RES = INPUTS_DIR / "proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res"
MANIFEST_PATH = INPUTS_DIR / "manifest.json"
AMBIENT_K = 318.15

PUBLIC_CASES = [
    ("2DIC layer0", "2DIC_active_layer", ROOT / "third_party" / "ATSim3D_pub" / "2DIC" / "Intel_ID1_lcf.layer0.res"),
    ("Mono3D layer6", "Mono3D_active_layer_top", ROOT / "third_party" / "ATSim3D_pub" / "Mono3D" / "Mono3D_lcf.layer6.res"),
    ("Mono3D layer11", "Mono3D_active_layer_bottom", ROOT / "third_party" / "ATSim3D_pub" / "Mono3D" / "Mono3D_lcf.layer11.res"),
    ("TSV3D layer2", "TSV3D_active_layer_top", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer2.res"),
    ("TSV3D layer7", "TSV3D_active_layer_bottom", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer7.res"),
    ("TSV3D layer3", "TSV3D_substrate_between_active_layers", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer3.res"),
    ("TSV3D layer8", "TSV3D_bottom_substrate", ROOT / "third_party" / "ATSim3D_pub" / "TSV3D" / "TSV3D_lcf.layer8.res"),
]


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing or empty required file: {path}")


def write_grid_csv(path: Path, grid_data: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["grid_y", *[f"x{x}" for x in range(grid_data.shape[1])]])
        for y, row in enumerate(grid_data):
            writer.writerow([y, *[f"{float(v):.6f}" for v in row]])


def load_grid_csv(path: Path) -> np.ndarray:
    require_file(path)
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if not header or header[0] not in {"grid_y", "pact_raw_row_y"}:
            raise SystemExit(f"unexpected grid CSV header: {path}")
        for row in reader:
            rows.append([float(v) for v in row[1:]])
    return np.asarray(rows, dtype=float)


def load_hotspot_summary() -> dict:
    require_file(HOTSPOT_STATS_PATH)
    require_file(HOTSPOT_RANK_PATH)
    stats_rows = list(csv.DictReader(HOTSPOT_STATS_PATH.open(newline="", encoding="utf-8")))
    rank_rows = list(csv.DictReader(HOTSPOT_RANK_PATH.open(newline="", encoding="utf-8")))
    peak = max(float(row["max_k"]) for row in stats_rows)
    final = float(stats_rows[-1]["max_k"])
    final_block = stats_rows[-1]["max_block"]
    peak_block = rank_rows[0]["block"]
    return {
        "samples": len(stats_rows),
        "peak_k": peak,
        "final_max_k": final,
        "final_max_block": final_block,
        "peak_block": peak_block,
    }


def approx_quantiles_from_hist(edges: np.ndarray, hist: np.ndarray, quantiles: list[float]) -> list[tuple[float, float]]:
    cdf = np.cumsum(hist)
    total = int(cdf[-1])
    out = []
    for q in quantiles:
        target = max(1, int(round(q * total)))
        idx = int(np.searchsorted(cdf, target, side="left"))
        idx = min(idx, len(hist) - 1)
        left = edges[idx]
        right = edges[idx + 1]
        out.append((q, float((left + right) / 2.0)))
    return out


def stream_proxy_result() -> dict:
    require_file(PROXY_RES)
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))["atsim_results"][0]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    min_k = float(summary["min_k"])
    max_k = float(summary["max_k"])
    n = int(summary["unique_x"])
    if n != 4096 or int(summary["unique_y"]) != 4096:
        raise SystemExit(f"unexpected proxy result shape in summary: {summary['unique_x']}x{summary['unique_y']}")

    sums64 = np.zeros((64, 64), dtype=np.float64)
    counts64 = np.zeros((64, 64), dtype=np.int32)
    sums256 = np.zeros((256, 256), dtype=np.float64)
    counts256 = np.zeros((256, 256), dtype=np.int32)
    bins = np.linspace(min_k, max_k, 81)
    hist = np.zeros(80, dtype=np.int64)
    top_heap: list[tuple[float, int, int, float, float]] = []
    total = 0.0
    total2 = 0.0
    count = 0

    with PROXY_RES.open(encoding="utf-8") as f:
        for idx, line in enumerate(f):
            parts = line.split()
            if len(parts) < 3:
                continue
            x_m = float(parts[0])
            y_m = float(parts[1])
            temp = float(parts[2])
            x_idx = idx // n
            y_idx = idx % n
            y64 = y_idx // 64
            x64 = x_idx // 64
            y256 = y_idx // 16
            x256 = x_idx // 16
            sums64[y64, x64] += temp
            counts64[y64, x64] += 1
            sums256[y256, x256] += temp
            counts256[y256, x256] += 1
            bin_idx = int(np.searchsorted(bins, temp, side="right") - 1)
            bin_idx = max(0, min(bin_idx, len(hist) - 1))
            hist[bin_idx] += 1
            item = (temp, x_idx, y_idx, x_m, y_m)
            if len(top_heap) < 20:
                heapq.heappush(top_heap, item)
            elif temp > top_heap[0][0]:
                heapq.heapreplace(top_heap, item)
            total += temp
            total2 += temp * temp
            count += 1

    if count != n * n:
        raise SystemExit(f"unexpected proxy point count: {count}")
    grid64 = sums64 / counts64
    grid256 = sums256 / counts256
    top = sorted(top_heap, reverse=True)
    std = (total2 / count - (total / count) ** 2) ** 0.5
    return {
        "grid64": grid64,
        "grid256": grid256,
        "hist_edges": bins,
        "hist": hist,
        "top": top,
        "mean_k": total / count,
        "std_k": std,
        "min_k": min_k,
        "max_k": max_k,
        "points": count,
        "cell_side_m": float(manifest["cell_side_m"]),
    }


def summarize_delta(delta: np.ndarray, reference: np.ndarray, candidate: np.ndarray) -> dict:
    return {
        "min_k": float(delta.min()),
        "max_k": float(delta.max()),
        "mean_k": float(delta.mean()),
        "std_k": float(delta.std()),
        "abs_mean_k": float(np.abs(delta).mean()),
        "rms_k": float(np.sqrt(np.mean(delta * delta))),
        "corr": float(np.corrcoef(candidate.reshape(-1), reference.reshape(-1))[0, 1]),
    }


def write_metric_csv(path: Path, rows: dict) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["metric", "value"])
        for key, value in rows.items():
            if isinstance(value, float):
                writer.writerow([key, f"{value:.9f}"])
            else:
                writer.writerow([key, value])


def write_proxy_tables(proxy: dict, pact_phys: np.ndarray, pact_raw: np.ndarray, hotspot: dict) -> dict:
    write_grid_csv(ARTIFACTS_DIR / "atsim_proxy_downsample_64_grid.csv", proxy["grid64"])
    write_grid_csv(ARTIFACTS_DIR / "atsim_proxy_downsample_256_grid.csv", proxy["grid256"])

    delta_phys = proxy["grid64"] - pact_phys
    delta_raw = proxy["grid64"] - pact_raw
    write_grid_csv(ARTIFACTS_DIR / "atsim_minus_pact_64_grid.csv", delta_phys)
    write_grid_csv(ARTIFACTS_DIR / "atsim_minus_pact_raw_order_64_grid.csv", delta_raw)

    with (ARTIFACTS_DIR / "atsim_proxy_histogram.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["bin_min_k", "bin_max_k", "count"])
        for lo, hi, count in zip(proxy["hist_edges"][:-1], proxy["hist_edges"][1:], proxy["hist"]):
            writer.writerow([f"{lo:.9f}", f"{hi:.9f}", int(count)])

    quantiles = approx_quantiles_from_hist(proxy["hist_edges"], proxy["hist"], [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    with (ARTIFACTS_DIR / "atsim_proxy_quantiles.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["quantile", "temperature_k", "method"])
        for q, temp in quantiles:
            writer.writerow([f"{q:.2f}", f"{temp:.6f}", "histogram_midpoint_approx"])

    with (ARTIFACTS_DIR / "atsim_proxy_hotspot_rank.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["rank", "fine_x", "fine_y", "source_grid_x", "source_grid_y", "x_m", "y_m", "temperature_k", "delta_over_ambient_k"])
        for rank, (temp, x_idx, y_idx, x_m, y_m) in enumerate(proxy["top"], start=1):
            writer.writerow([rank, x_idx, y_idx, x_idx // 64, y_idx // 64, f"{x_m:.12g}", f"{y_m:.12g}", f"{temp:.6f}", f"{temp - AMBIENT_K:.6f}"])

    pact_summary = {
        "min_k": float(pact_phys.min()),
        "max_k": float(pact_phys.max()),
        "mean_k": float(pact_phys.mean()),
        "std_k": float(pact_phys.std()),
        "delta_k": float(pact_phys.max() - pact_phys.min()),
    }
    atsim_summary = {
        "min_k": float(proxy["min_k"]),
        "max_k": float(proxy["max_k"]),
        "mean_k": float(proxy["mean_k"]),
        "std_k": float(proxy["std_k"]),
        "delta_k": float(proxy["max_k"] - proxy["min_k"]),
    }
    delta_summary = summarize_delta(delta_phys, pact_phys, proxy["grid64"])
    raw_order_delta_summary = summarize_delta(delta_raw, pact_raw, proxy["grid64"])
    rows = [
        ("ATSim3D_v1_proxy_layer0", atsim_summary),
        ("PACT_steady_layer0_physical_y_up", pact_summary),
        ("HotSpot_coarse_ttrace", {"min_k": None, "max_k": hotspot["peak_k"], "mean_k": None, "std_k": None, "delta_k": hotspot["peak_k"] - AMBIENT_K}),
    ]
    with (ARTIFACTS_DIR / "atsim_proxy_vs_pact_hotspot_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["source", "min_k", "max_k", "mean_k", "std_k", "max_minus_min_or_ambient_k"])
        for source, stats in rows:
            writer.writerow([source, stats["min_k"], stats["max_k"], stats["mean_k"], stats["std_k"], stats["delta_k"]])
    write_metric_csv(ARTIFACTS_DIR / "atsim_pact_delta_summary.csv", delta_summary)
    write_metric_csv(ARTIFACTS_DIR / "atsim_pact_raw_order_delta_summary.csv", raw_order_delta_summary)
    with (ARTIFACTS_DIR / "atsim_pact_coordinate_delta_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["alignment", "abs_mean_k", "rms_k", "corr"])
        writer.writerow(["physical_y_up", f"{delta_summary['abs_mean_k']:.9f}", f"{delta_summary['rms_k']:.9f}", f"{delta_summary['corr']:.9f}"])
        writer.writerow(["pact_raw_row_order", f"{raw_order_delta_summary['abs_mean_k']:.9f}", f"{raw_order_delta_summary['rms_k']:.9f}", f"{raw_order_delta_summary['corr']:.9f}"])
    return {"atsim": atsim_summary, "pact": pact_summary, "delta": delta_summary, "delta_raw_order": raw_order_delta_summary, "hotspot": hotspot}


def load_public_grid(path: Path, nx: int, ny: int) -> np.ndarray:
    require_file(path)
    data = np.empty((ny, nx), dtype=np.float64)
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f):
            parts = line.split()
            if len(parts) < 3:
                continue
            x_idx = idx // ny
            y_idx = idx % ny
            data[y_idx, x_idx] = float(parts[2])
    return data


def write_public_tables(summary_data: dict) -> list[tuple[str, str, np.ndarray, dict]]:
    summary_by_path = {item["path"]: item for item in summary_data["atsim_results"]}
    rows = []
    grids = []
    with (ARTIFACTS_DIR / "atsim_public_example_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["case", "role", "points", "unique_x", "unique_y", "min_k", "max_k", "mean_k", "delta_k"])
        for case, role, path in PUBLIC_CASES:
            rel_path = str(path.relative_to(ROOT))
            item = summary_by_path[rel_path]
            writer.writerow([case, role, item["points"], item["unique_x"], item["unique_y"], f"{item['min_k']:.6f}", f"{item['max_k']:.6f}", f"{item['mean_k']:.6f}", f"{item['delta_k']:.6f}"])
            grid = load_public_grid(path, int(item["unique_x"]), int(item["unique_y"]))
            grids.append((case, role, grid, item))
    return grids


def save_heatmap(path: Path, data: np.ndarray, title: str, xlabel: str = "grid x", ylabel: str = "grid y") -> None:
    plt.figure(figsize=(7.0, 5.8))
    im = plt.imshow(data, origin="lower", cmap="inferno", aspect="equal")
    plt.colorbar(im, label="Temperature (K)")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def save_delta_heatmap(path: Path, data: np.ndarray, title: str) -> None:
    vmax = float(np.max(np.abs(data)))
    plt.figure(figsize=(7.0, 5.8))
    im = plt.imshow(data, origin="lower", cmap="coolwarm", aspect="equal", vmin=-vmax, vmax=vmax)
    plt.colorbar(im, label="ATSim - PACT (K)")
    plt.xlabel("grid x")
    plt.ylabel("grid y")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def save_distribution(path: Path, proxy: dict, pact: np.ndarray, hotspot: dict) -> None:
    edges = proxy["hist_edges"]
    centers = (edges[:-1] + edges[1:]) / 2.0
    plt.figure(figsize=(7.2, 4.8))
    plt.plot(centers, proxy["hist"] / proxy["hist"].sum(), label="ATSim proxy fine-grid", linewidth=1.8)
    plt.hist(pact.reshape(-1), bins=30, density=True, alpha=0.35, label="PACT steady 64x64")
    plt.axvline(hotspot["peak_k"], color="tab:green", linestyle="--", linewidth=1.5, label="HotSpot peak max")
    plt.xlabel("Temperature (K)")
    plt.ylabel("Normalized density")
    plt.title("Temperature distribution comparison")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def save_summary_bar(path: Path, stats: dict) -> None:
    labels = ["ATSim\nproxy", "PACT\nsteady", "HotSpot\npeak"]
    max_vals = [stats["atsim"]["max_k"], stats["pact"]["max_k"], stats["hotspot"]["peak_k"]]
    mean_vals = [stats["atsim"]["mean_k"], stats["pact"]["mean_k"], np.nan]
    x = np.arange(len(labels))
    width = 0.35
    plt.figure(figsize=(7.2, 4.6))
    plt.bar(x - width / 2, max_vals, width, label="max")
    plt.bar(x + width / 2, mean_vals, width, label="mean")
    plt.xticks(x, labels)
    plt.ylabel("Temperature (K)")
    plt.title("ATSim vs PACT vs HotSpot summary")
    plt.ylim(317.5, max(max_vals) + 1.0)
    plt.grid(axis="y", alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def save_public_heatmaps(path: Path, grids: list[tuple[str, str, np.ndarray, dict]]) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(14.0, 7.2))
    axes_flat = axes.reshape(-1)
    for ax, (case, role, grid, item) in zip(axes_flat, grids):
        im = ax.imshow(grid, origin="lower", cmap="inferno", aspect="equal")
        ax.set_title(f"{case}\nmax {item['max_k']:.1f} K", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    axes_flat[-1].axis("off")
    fig.suptitle("ATSim3D public examples: 2DIC, Mono3D, TSV3D", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_public_summary_bar(path: Path, grids: list[tuple[str, str, np.ndarray, dict]]) -> None:
    cases = [case for case, _, _, _ in grids]
    means = [item["mean_k"] for _, _, _, item in grids]
    maxes = [item["max_k"] for _, _, _, item in grids]
    x = np.arange(len(cases))
    width = 0.35
    plt.figure(figsize=(10.5, 4.8))
    plt.bar(x - width / 2, means, width, label="mean")
    plt.bar(x + width / 2, maxes, width, label="max")
    plt.xticks(x, cases, rotation=25, ha="right")
    plt.ylabel("Temperature (K)")
    plt.title("ATSim3D public example layer temperatures")
    plt.grid(axis="y", alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def write_manifest(stats: dict) -> None:
    manifest = {
        "created": "2026-05-03",
        "source_run_dir": str(RUN_DIR.relative_to(ROOT)),
        "output_dir": str(ARTIFACTS_DIR.relative_to(ROOT)),
        "proxy_result": str(PROXY_RES.relative_to(ROOT)),
        "pact_grid": str(PACT_GRID_PATH.relative_to(ROOT)),
        "pact_raw_grid": str(PACT_RAW_GRID_PATH.relative_to(ROOT)),
        "coordinate_view": "PACT main comparison uses DEF physical y-up grid; raw-order comparison is diagnostic only",
        "hotspot_stats": str(HOTSPOT_STATS_PATH.relative_to(ROOT)),
        "generated_files": sorted(str(p.relative_to(ROOT)) for p in ARTIFACTS_DIR.iterdir() if p.is_file()),
        "summary": stats,
    }
    (ARTIFACTS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    for path in [PROXY_RES, SUMMARY_JSON, MANIFEST_PATH, PACT_GRID_PATH, PACT_RAW_GRID_PATH, HOTSPOT_STATS_PATH, HOTSPOT_RANK_PATH]:
        require_file(path)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_data = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    proxy = stream_proxy_result()
    pact = load_grid_csv(PACT_GRID_PATH)
    pact_raw = load_grid_csv(PACT_RAW_GRID_PATH)
    hotspot = load_hotspot_summary()
    stats = write_proxy_tables(proxy, pact, pact_raw, hotspot)
    public_grids = write_public_tables(summary_data)

    save_heatmap(ARTIFACTS_DIR / "heatmap_atsim_proxy_downsample_256.png", proxy["grid256"], "ATSim3D v1 proxy layer0, 256x256 downsample")
    save_heatmap(ARTIFACTS_DIR / "heatmap_atsim_proxy_downsample_64.png", proxy["grid64"], "ATSim3D v1 proxy layer0, 64x64 downsample")
    save_delta_heatmap(ARTIFACTS_DIR / "heatmap_atsim_minus_pact_64.png", proxy["grid64"] - pact, "ATSim3D v1 proxy minus corrected PACT, physical y-up")
    save_delta_heatmap(ARTIFACTS_DIR / "heatmap_atsim_minus_pact_raw_order_64.png", proxy["grid64"] - pact_raw, "ATSim3D v1 proxy minus PACT raw row order")
    save_distribution(ARTIFACTS_DIR / "atsim_pact_hotspot_temperature_distribution.png", proxy, pact, hotspot)
    save_summary_bar(ARTIFACTS_DIR / "atsim_pact_hotspot_summary_bar.png", stats)
    save_public_heatmaps(ARTIFACTS_DIR / "atsim_public_examples_heatmaps.png", public_grids)
    save_public_summary_bar(ARTIFACTS_DIR / "atsim_public_examples_summary_bar.png", public_grids)
    write_manifest(stats)
    print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
