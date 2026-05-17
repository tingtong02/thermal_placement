#!/usr/bin/env python3
"""Build standard-cell context figures from the completed Stage 3/4 artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RUN_TAG = "tiled_matmul_os_baseline"
GRID_N = 64
AMBIENT_K = 318.15


def save_figure(fig, out: Path) -> None:
    fig.savefig(out)
    if out.suffix.lower() == ".svg":
        text = out.read_text(encoding="utf-8")
        cleaned = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
        out.write_text(cleaned, encoding="utf-8")
        fig.savefig(out.with_suffix(".png"), dpi=180)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-map", default=f"power/stage3_{RUN_TAG}_instance_grid_map.csv")
    parser.add_argument("--region-summary", default=f"power/stage3_{RUN_TAG}_region_power_summary.csv")
    parser.add_argument("--pact-steady", default="artifacts/stage4/pact_steady_layer0_grid.csv")
    parser.add_argument("--pact-rank", default="artifacts/stage4/pact_hotspot_rank.csv")
    parser.add_argument("--out-dir", default="artifacts/stage4/standard_cell_context")
    parser.add_argument("--report", default=f"reports/stage4_{RUN_TAG}_standard_cell_context.md")
    parser.add_argument("--chunksize", type=int, default=250000)
    parser.add_argument("--top-cells", type=int, default=800)
    return parser.parse_args()


def read_temperature_grid(path: Path) -> np.ndarray:
    df = pd.read_csv(path)
    x_cols = sorted([c for c in df.columns if c.startswith("x")], key=lambda c: int(c[1:]))
    df = df.sort_values("grid_y")
    arr = df[x_cols].to_numpy(dtype=float)
    if arr.shape != (GRID_N, GRID_N):
        raise ValueError(f"expected {GRID_N}x{GRID_N} grid in {path}, got {arr.shape}")
    return arr


def read_pact_rank(path: Path, n: int = 20) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df.head(n).copy()


def add_top_rows(existing: pd.DataFrame | None, chunk: pd.DataFrame, n: int) -> pd.DataFrame:
    chunk_top = chunk.loc[chunk["proxy_power_w"] > 0].nlargest(n, "proxy_power_w")
    if existing is None or existing.empty:
        merged = chunk_top
    else:
        merged = pd.concat([existing, chunk_top], ignore_index=True)
    return merged.nlargest(n, "proxy_power_w").reset_index(drop=True)


def aggregate_instance_map(path: Path, top_grids: set[tuple[int, int]], chunksize: int, top_cells: int):
    count_grid = np.zeros((GRID_N, GRID_N), dtype=np.int64)
    area_grid = np.zeros((GRID_N, GRID_N), dtype=float)
    power_grid = np.zeros((GRID_N, GRID_N), dtype=float)

    region = defaultdict(lambda: {"instances": 0, "cell_area": 0.0, "proxy_power_w": 0.0})
    master = defaultdict(lambda: {"instances": 0, "cell_area": 0.0, "proxy_power_w": 0.0})
    grid_region_power = defaultdict(float)
    top_exact = {grid: [] for grid in top_grids}
    top_df = None

    dtype = {
        "instance": "string",
        "master": "string",
        "region": "string",
        "grid_x": "int16",
        "grid_y": "int16",
        "cell_area": "float64",
        "proxy_power_w": "float64",
    }
    usecols = ["instance", "master", "region", "grid_x", "grid_y", "cell_area", "proxy_power_w"]
    for chunk in pd.read_csv(path, usecols=usecols, dtype=dtype, chunksize=chunksize):
        gx = chunk["grid_x"].to_numpy(dtype=np.int64)
        gy = chunk["grid_y"].to_numpy(dtype=np.int64)
        area = chunk["cell_area"].fillna(0).to_numpy(dtype=float)
        power = chunk["proxy_power_w"].fillna(0).to_numpy(dtype=float)
        valid = (gx >= 0) & (gx < GRID_N) & (gy >= 0) & (gy < GRID_N)
        np.add.at(count_grid, (gy[valid], gx[valid]), 1)
        np.add.at(area_grid, (gy[valid], gx[valid]), area[valid])
        np.add.at(power_grid, (gy[valid], gx[valid]), power[valid])

        for name, sub in chunk.groupby("region", dropna=False):
            key = str(name)
            region[key]["instances"] += int(len(sub))
            region[key]["cell_area"] += float(sub["cell_area"].sum())
            region[key]["proxy_power_w"] += float(sub["proxy_power_w"].sum())

        for name, sub in chunk.groupby("master", dropna=False):
            key = str(name)
            master[key]["instances"] += int(len(sub))
            master[key]["cell_area"] += float(sub["cell_area"].sum())
            master[key]["proxy_power_w"] += float(sub["proxy_power_w"].sum())

        grp = chunk.groupby(["grid_x", "grid_y", "region"], dropna=False)["proxy_power_w"].sum()
        for (x, y, reg), val in grp.items():
            if 0 <= int(x) < GRID_N and 0 <= int(y) < GRID_N:
                grid_region_power[(int(x), int(y), str(reg))] += float(val)

        mask = chunk.apply(lambda r: (int(r["grid_x"]), int(r["grid_y"])) in top_grids, axis=1)
        if mask.any():
            for grid, sub in chunk.loc[mask].groupby(["grid_x", "grid_y"]):
                key = (int(grid[0]), int(grid[1]))
                top_exact[key].extend(sub.nlargest(8, "proxy_power_w").to_dict("records"))
                top_exact[key] = sorted(top_exact[key], key=lambda r: float(r["proxy_power_w"]), reverse=True)[:8]

        top_df = add_top_rows(top_df, chunk, top_cells)

    region_df = pd.DataFrame.from_dict(region, orient="index").reset_index(names="region")
    master_df = pd.DataFrame.from_dict(master, orient="index").reset_index(names="master")
    return count_grid, area_grid, power_grid, region_df, master_df, grid_region_power, top_exact, top_df


def save_region_share(region_df: pd.DataFrame, out: Path) -> None:
    df = region_df.copy().sort_values("proxy_power_w", ascending=True)
    for col in ["instances", "cell_area", "proxy_power_w"]:
        df[col + "_share"] = df[col] / df[col].sum() * 100.0
    y = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    ax.barh(y - 0.24, df["proxy_power_w_share"], height=0.22, label="Proxy power share", color="#d1495b")
    ax.barh(y, df["cell_area_share"], height=0.22, label="Cell area share", color="#00798c")
    ax.barh(y + 0.24, df["instances_share"], height=0.22, label="Instance share", color="#edae49")
    ax.set_yticks(y)
    ax.set_yticklabels(df["region"])
    ax.set_xlabel("Share of Stage 3 standard-cell aggregate (%)")
    ax.set_title("Standard-cell region composition")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(loc="lower right")
    fig.tight_layout()
    save_figure(fig, out)
    plt.close(fig)


def save_master_power(master_df: pd.DataFrame, out: Path) -> pd.DataFrame:
    df = master_df.sort_values("proxy_power_w", ascending=False).head(18).sort_values("proxy_power_w")
    fig, ax = plt.subplots(figsize=(9.4, 5.8))
    ax.barh(np.arange(len(df)), df["proxy_power_w"] * 1e3, color="#4c78a8")
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels(df["master"])
    ax.set_xlabel("Proxy power contribution (mW, normalized peak total = 1 W)")
    ax.set_title("Top standard-cell master types by proxy power")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    save_figure(fig, out)
    plt.close(fig)
    return df.sort_values("proxy_power_w", ascending=False)


def annotate_points(ax, pact_hot: tuple[int, int], power_hot: tuple[int, int]) -> None:
    ax.scatter([pact_hot[0]], [pact_hot[1]], marker="*", s=150, color="white", edgecolor="black", linewidth=0.8, label="PACT steady hotspot")
    ax.scatter([power_hot[0]], [power_hot[1]], marker="X", s=95, color="#00ffff", edgecolor="black", linewidth=0.7, label="Peak proxy-power grid")


def save_grid_context(temp: np.ndarray, count: np.ndarray, area: np.ndarray, power: np.ndarray, out: Path) -> None:
    pact_hot = tuple(np.unravel_index(np.argmax(temp), temp.shape)[::-1])
    power_hot = tuple(np.unravel_index(np.argmax(power), power.shape)[::-1])
    density = np.divide(power, area, out=np.zeros_like(power), where=area > 0)
    panels = [
        (temp, "PACT steady temperature, layer0", "K", "inferno"),
        (power * 1e3, "Aggregated standard-cell proxy power", "mW", "magma"),
        (np.log10(count + 1), "Placed standard-cell density", "log10(count+1)", "viridis"),
        (density * 1e6, "Proxy power per reported cell area", "uW / area", "cividis"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 9.0), constrained_layout=True)
    for ax, (arr, title, cbar, cmap) in zip(axes.flat, panels):
        im = ax.imshow(arr, origin="lower", cmap=cmap, interpolation="nearest")
        annotate_points(ax, pact_hot, power_hot)
        ax.set_title(title)
        ax.set_xlabel("grid_x")
        ax.set_ylabel("grid_y")
        fig.colorbar(im, ax=ax, fraction=0.045, pad=0.02, label=cbar)
    axes.flat[0].legend(loc="upper left", fontsize=8, framealpha=0.85)
    save_figure(fig, out)
    plt.close(fig)


def save_hotspot_overlay(temp: np.ndarray, top_df: pd.DataFrame, power: np.ndarray, out: Path) -> None:
    pact_hot = tuple(np.unravel_index(np.argmax(temp), temp.shape)[::-1])
    power_hot = tuple(np.unravel_index(np.argmax(power), power.shape)[::-1])
    df = top_df.copy()
    max_power = df["proxy_power_w"].max()
    sizes = 12 + 110 * np.sqrt(df["proxy_power_w"] / max_power)
    fig, ax = plt.subplots(figsize=(8.2, 7.2))
    im = ax.imshow(temp, origin="lower", cmap="inferno", interpolation="nearest")
    sc = ax.scatter(df["grid_x"] + 0.5, df["grid_y"] + 0.5, s=sizes, c=df["proxy_power_w"] * 1e6,
                    cmap="winter", alpha=0.72, edgecolor="black", linewidth=0.25, label="Top standard cells")
    annotate_points(ax, pact_hot, power_hot)
    ax.set_title("High-power standard cells over PACT steady temperature")
    ax.set_xlabel("grid_x")
    ax.set_ylabel("grid_y")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02, label="Temperature (K)")
    fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.10, label="Cell proxy power (uW)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.85)
    fig.tight_layout()
    save_figure(fig, out)
    plt.close(fig)


def write_grid_csv(count: np.ndarray, area: np.ndarray, power: np.ndarray, temp: np.ndarray, out: Path) -> pd.DataFrame:
    rows = []
    flat_power = power.ravel()
    power_order = np.argsort(-flat_power)
    power_rank = np.empty_like(power_order)
    power_rank[power_order] = np.arange(1, len(power_order) + 1)
    for y in range(GRID_N):
        for x in range(GRID_N):
            rows.append({
                "grid_x": x,
                "grid_y": y,
                "instance_count": int(count[y, x]),
                "cell_area": float(area[y, x]),
                "proxy_power_w": float(power[y, x]),
                "power_rank": int(power_rank[y * GRID_N + x]),
                "steady_temp_k": float(temp[y, x]),
                "delta_over_ambient_k": float(temp[y, x] - AMBIENT_K),
            })
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    return df


def write_hotspot_context(pact_rank: pd.DataFrame, grid_df: pd.DataFrame, power: np.ndarray, count: np.ndarray,
                          area: np.ndarray, grid_region_power, top_exact, out: Path) -> pd.DataFrame:
    rows = []
    for _, r in pact_rank.head(15).iterrows():
        x = int(r["grid_x"])
        y = int(r["grid_y"])
        x0, x1 = max(0, x - 2), min(GRID_N, x + 3)
        y0, y1 = max(0, y - 2), min(GRID_N, y + 3)
        region_items = [((gx, gy, reg), val) for (gx, gy, reg), val in grid_region_power.items() if gx == x and gy == y]
        if region_items:
            top_region = max(region_items, key=lambda item: item[1])[0][2]
            top_region_power = max(region_items, key=lambda item: item[1])[1]
        else:
            top_region = "none"
            top_region_power = 0.0
        exact = top_exact.get((x, y), [])[:3]
        top_instances = "; ".join(
            f"{str(e['instance'])}:{str(e['master'])}:{float(e['proxy_power_w']):.3e}" for e in exact
        )
        row = grid_df[(grid_df["grid_x"] == x) & (grid_df["grid_y"] == y)].iloc[0]
        rows.append({
            "pact_temp_rank": int(r["rank"]),
            "grid_x": x,
            "grid_y": y,
            "steady_temp_k": float(r["temperature_k"]),
            "delta_over_ambient_k": float(r["delta_over_ambient_k"]),
            "exact_grid_proxy_power_w": float(power[y, x]),
            "exact_grid_power_rank": int(row["power_rank"]),
            "exact_grid_instances": int(count[y, x]),
            "exact_grid_cell_area": float(area[y, x]),
            "exact_grid_top_region": top_region,
            "exact_grid_top_region_power_w": float(top_region_power),
            "local_r2_proxy_power_w": float(power[y0:y1, x0:x1].sum()),
            "local_r2_instances": int(count[y0:y1, x0:x1].sum()),
            "local_r2_cell_area": float(area[y0:y1, x0:x1].sum()),
            "top_exact_grid_instances": top_instances,
        })
    out_df = pd.DataFrame(rows)
    out_df.to_csv(out, index=False)
    return out_df


def write_report(report: Path, out_dir: Path, region_df: pd.DataFrame, master_top: pd.DataFrame,
                 hotspot_ctx: pd.DataFrame, temp: np.ndarray, power: np.ndarray, count: np.ndarray) -> None:
    total_instances = int(region_df["instances"].sum())
    total_power = float(region_df["proxy_power_w"].sum())
    top_region = region_df.sort_values("proxy_power_w", ascending=False).iloc[0]
    top_master = master_top.iloc[0]
    pact_hot = tuple(np.unravel_index(np.argmax(temp), temp.shape)[::-1])
    power_hot = tuple(np.unravel_index(np.argmax(power), power.shape)[::-1])
    pact_peak = float(temp.max())
    mean_temp = float(temp.mean())
    peak_power = float(power.max())
    power_hot_count = int(count[power_hot[1], power_hot[0]])
    first_hot = hotspot_ctx.iloc[0]

    text = f"""# Stage 4 Standard-Cell Context Visualization

Date: 2026-05-03

## Scope

本报告只基于已经完成的 Stage 2-4 baseline 结果，说明当前成果里“标准单元”与 grid 级热结果的关系。这里没有进行热优化、没有新增 workload，也没有重跑 PACT 或 HotSpot。

## Data Chain

1. Stage 2 生成 ASAP7 标准单元实现，得到 placed standard-cell instances 和 DEF 坐标。
2. Stage 3 将 `{total_instances:,}` 个 active standard-cell components 映射到 `64 x 64` grid，并把目标 GEMM 窗口 RTL activity 按区域分配为 normalized proxy power。
3. Stage 4 在同一 grid 上运行 PACT steady/transient 和 HotSpot coarse comparison；本报告把 Stage 3 的 cell/grid 聚合结果与 PACT layer0 稳态温度叠加展示。
4. 2026-05-03 后处理修复后，本报告读取的是已经转换到 DEF 物理坐标的 PACT grid：`grid_y=0` 是 die bottom，`grid_y` 向上增加。PACT 原始 row-order 只保留在 `_pact_raw_order` 产物中，不再用于标准单元叠加。

## Main Findings

- 标准单元功耗来源不是随机 grid：每个 grid bin 的 power 来自落在该 bin 内的 placed standard-cell instances 聚合。
- 当前 peak-normalized proxy power 总量为 `{total_power:.6f}` W；最大贡献区域是 `{top_region['region']}`，占 `{float(top_region['proxy_power_w']) / total_power * 100:.2f}%`。
- **坐标已修复**：PACT steady layer0 热点在 DEF 物理 grid `({pact_hot[0]}, {pact_hot[1]})`，温度 `{pact_peak:.3f}` K，平均温度 `{mean_temp:.3f}` K。这里的 `grid_y=0` 是 die bottom，和 Stage 3 标准单元 `grid_y` 一致。
- Stage 3 标准单元 proxy power 最大 grid 在 `({power_hot[0]}, {power_hot[1]})`，该 grid 聚合功耗 `{peak_power:.6e}` W，包含 `{power_hot_count}` 个 active standard-cell components。
- 温度热点和瞬时/局部功耗最高 grid 不完全重合，这是正常现象：稳态热扩散会把周围区域、边界条件和材料热传导共同反映到温度场中。
- 当前按 master 类型汇总的 top 类型为 `{top_master['master']}`；结合单实例 Top-N 中的 `INVx13/INVx11/INVx8` 等单元，可以看到 inverter/buffer 类标准单元在当前 proxy 功耗归因中较突出。

## Figures and How to Read Them

- `{out_dir}/standard_cell_region_share.svg` / `.png`: 比较每个逻辑区域的标准单元实例数、cell area 和 proxy power share。SVG 保留矢量版本，PNG 用于 VS Code 和报告快速预览。
- `{out_dir}/standard_cell_grid_context.svg` / `.png`: 四联图。左上是修复后的 PACT 物理坐标稳态温度；右上是标准单元聚合 proxy power；左下是标准单元密度；右下是 proxy power / cell area。白色星号是 PACT 稳态热点，青色 X 是 proxy power 最高 grid。
- `{out_dir}/standard_cell_hotspot_overlay.svg` / `.png`: 在 PACT 温度图上叠加 top standard-cell instances。点越大代表单元 proxy power 越高，底图颜色代表温度。
- `{out_dir}/standard_cell_master_power.svg` / `.png`: 展示 proxy power 贡献最高的标准单元 master 类型，可用于描述哪些门级单元族在当前 proxy 模型中更突出。

## Tables

- `{out_dir}/standard_cell_grid_context.csv`: 每个 `64 x 64` grid 的标准单元数量、cell area、proxy power、power rank 和 PACT steady temperature。
- `{out_dir}/standard_cell_hotspot_context.csv`: 修复后的 PACT top temperature physical grids 与同 grid / 邻域标准单元聚合信息的反查表。
- `{out_dir}/standard_cell_top_instances.csv`: 当前 proxy power Top standard-cell instances，用于从图回到具体实例名和 master 类型。
- `{out_dir}/standard_cell_master_power_top.csv`: proxy power 贡献最高的 master 类型。

## Caveats

- 这些结果是 `proxy / thermal-flow prototype`，不是 signoff power 或 timing-closed implementation。
- Stage 3 功耗为 normalized proxy power，尚未使用 gate-level SAIF/SPEF/Liberty 做严格门级功耗。
- 当前热图仍是 grid 级温度，不是每个标准单元单独一个温度节点；标准单元研究体现在“实例级物理映射、区域/单元功耗归因、grid 热点反查”。
- **严禁把 PACT raw row-order 坐标当作物理坐标解读**；标准单元上下文只应使用 `artifacts/stage4/pact_steady_layer0_grid.csv` 这类已修复的 physical-coordinate 产物。
- SRAM macro body 没有做精细热源建模，当前展示主要覆盖 PE array、控制和近邻 datapath 的标准单元逻辑。

## Recommended Group-Meeting Description

目前已经完成从 Gemmini GEMM workload activity 到 ASAP7 标准单元实现、再到标准单元聚合功耗 grid 和 PACT/HotSpot 热仿真的闭环。新增展示把 grid 级热图反向连接到 placed standard-cell instances：可以看到不同逻辑区域的标准单元功耗占比、局部标准单元密度和 PACT 稳态热点之间的关系。当前还没有进行热优化，因此这些图主要作为 baseline 热画像和后续优化/sweep 的输入依据。
"""
    report.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    instance_map = Path(args.instance_map)
    pact_steady = Path(args.pact_steady)
    pact_rank_path = Path(args.pact_rank)
    out_dir = Path(args.out_dir)
    report = Path(args.report)
    out_dir.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)

    for path in [instance_map, pact_steady, pact_rank_path, Path(args.region_summary)]:
        if not path.exists():
            raise FileNotFoundError(path)

    temp = read_temperature_grid(pact_steady)
    pact_rank = read_pact_rank(pact_rank_path)
    top_grids = {(int(r.grid_x), int(r.grid_y)) for r in pact_rank.head(15).itertuples()}

    count, area, power, region_df, master_df, grid_region_power, top_exact, top_df = aggregate_instance_map(
        instance_map, top_grids, args.chunksize, args.top_cells
    )
    region_df = region_df.sort_values("proxy_power_w", ascending=False)
    master_df = master_df.sort_values("proxy_power_w", ascending=False)

    region_df.to_csv(out_dir / "standard_cell_region_summary.csv", index=False)
    top_df.to_csv(out_dir / "standard_cell_top_instances.csv", index=False)
    grid_df = write_grid_csv(count, area, power, temp, out_dir / "standard_cell_grid_context.csv")
    hotspot_ctx = write_hotspot_context(
        pact_rank, grid_df, power, count, area, grid_region_power, top_exact,
        out_dir / "standard_cell_hotspot_context.csv"
    )

    save_region_share(region_df, out_dir / "standard_cell_region_share.svg")
    master_top = save_master_power(master_df, out_dir / "standard_cell_master_power.svg")
    master_top.to_csv(out_dir / "standard_cell_master_power_top.csv", index=False)
    save_grid_context(temp, count, area, power, out_dir / "standard_cell_grid_context.svg")
    save_hotspot_overlay(temp, top_df, power, out_dir / "standard_cell_hotspot_overlay.svg")
    write_report(report, out_dir, region_df, master_top, hotspot_ctx, temp, power, count)

    print(f"wrote {out_dir}")
    print(f"wrote {report}")


if __name__ == "__main__":
    main()
