# ATSim3D v1 Proxy Stage4 Artifacts

更新时间：2026-05-03

本目录保存 `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/` 的 Stage4-style 图表和统计表。输入来自旧 `stage4_tiled_matmul_os_baseline` proxy 数据的 ATSim3D v1 rerun；ATSim3.5D v2 未参与本目录产物生成。

## 坐标说明

主对比已经改为使用 `artifacts/stage4/pact_steady_layer0_grid.csv`，也就是修复后的 PACT physical-coordinate grid。该 grid 使用 DEF 物理坐标：`grid_y=0` 是 die bottom，`grid_y` 向上增加。

PACT raw row-order 诊断只保留在 `*_raw_order_*` 文件中。**不要再把 raw-order 或旧 yflip 文件作为主结论使用。**

ATSim3D v1 原始 `.res` 是 fine-grid 温度输出，不包含标准单元实例或 master 信息。若需要标准单元级解释，应把本目录下采样后的 physical grid 与 Stage 3 placed instance grid map 叠加，而不是把 `.res` 当作标准单元级分析文件。

## 图表

| 文件 | 内容 |
| --- | --- |
| `heatmap_atsim_proxy_downsample_256.png` | ATSim3D v1 proxy layer0 4096x4096 细网格下采样到 256x256 的热图。 |
| `heatmap_atsim_proxy_downsample_64.png` | ATSim3D v1 proxy layer0 下采样到 64x64 的热图，用于和修复后 PACT steady layer0 对齐比较。 |
| `heatmap_atsim_minus_pact_64.png` | `ATSim - corrected PACT` 温差热图，physical y-up。 |
| `heatmap_atsim_minus_pact_raw_order_64.png` | `ATSim - PACT raw row order` 诊断热图，仅用于证明 raw order 错位。 |
| `atsim_pact_hotspot_temperature_distribution.png` | ATSim fine-grid 温度分布、修复后 PACT steady 64x64 分布和 HotSpot peak max 的对比。 |
| `atsim_pact_hotspot_summary_bar.png` | ATSim、修复后 PACT、HotSpot 的 max/mean summary bar。 |
| `atsim_public_examples_heatmaps.png` | ATSim3D public 2DIC、Mono3D、TSV3D 示例输出层热图总览。 |
| `atsim_public_examples_summary_bar.png` | public 示例各输出层 mean/max 温度柱状图。 |

## 统计表

| 文件 | 内容 |
| --- | --- |
| `atsim_proxy_downsample_256_grid.csv` | ATSim proxy 256x256 下采样温度矩阵。 |
| `atsim_proxy_downsample_64_grid.csv` | ATSim proxy 64x64 下采样温度矩阵。 |
| `atsim_minus_pact_64_grid.csv` | `ATSim - corrected PACT` 温差矩阵，physical y-up。 |
| `atsim_minus_pact_raw_order_64_grid.csv` | `ATSim - PACT raw row order` 诊断矩阵。 |
| `atsim_proxy_hotspot_rank.csv` | ATSim fine-grid top-20 热点坐标、对应 64x64 source grid 和温度。 |
| `atsim_proxy_histogram.csv` | ATSim fine-grid 温度直方图。 |
| `atsim_proxy_quantiles.csv` | ATSim fine-grid 温度分位数，基于 histogram midpoint 近似。 |
| `atsim_proxy_vs_pact_hotspot_summary.csv` | ATSim / 修复后 PACT / HotSpot summary 统计。 |
| `atsim_pact_delta_summary.csv` | `ATSim - corrected PACT` 64x64 差值统计。 |
| `atsim_pact_raw_order_delta_summary.csv` | `ATSim - PACT raw row order` 差值统计。 |
| `atsim_pact_coordinate_delta_comparison.csv` | corrected physical alignment 与 raw-order alignment 的 abs mean / RMS / corr 对比。 |
| `atsim_public_example_summary.csv` | 2DIC / Mono3D / TSV3D public 示例输出层统计。 |
| `manifest.json` | 本目录生成清单和 summary。 |

## 关键对比

| alignment | abs_mean_k | rms_k | corr |
| --- | ---: | ---: | ---: |
| physical_y_up | 1.326155691 | 1.679745032 | 0.972618931 |
| pact_raw_row_order | 2.771164102 | 3.371622051 | -0.141279496 |

## 生成命令

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python   thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/generate_atsim_stage4_artifacts.py
```
