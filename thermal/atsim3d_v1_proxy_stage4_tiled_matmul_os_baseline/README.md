# ATSim3D v1 Proxy Rerun: stage4_tiled_matmul_os_baseline

更新时间：2026-05-03

## 定位

本目录保存一次独立的 ATSim3D v1 运行记录：把旧 `stage4_tiled_matmul_os_baseline` proxy thermal 输入转换为 ATSim3D v1 输入，并运行 v1 steady-state 求解。

本 run 不属于当前 active multi-workload signoff 结果，不改变 `docs/phase0tophase4_signoff_multiworkload_plan.md`。ATSim3.5D v2 的输入 schema 仍未完整确认，本 run 没有使用 v2。

如果后续上下文压缩或记忆丢失，继续本 run 前先重读：

- `AGENTS.md`
- `docs/phase0tophase4_signoff_multiworkload_plan.md`
- `docs/README.md`
- `docs/atsim_proxy_experiment_plan.md`
- `docs/atsim_tool_guide.md`
- 本文件和 `RESULTS.md`

## 目录结构

```text
thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/
  ATTEMPTS.md
  README.md
  RESULTS.md
  inputs/
  logs/
  results/
  scripts/
```

## 输入来源

- `thermal/pact/stage4_tiled_matmul_os_baseline/flp_stage4_tiled_matmul_os_baseline.csv`
- `thermal/pact/stage4_tiled_matmul_os_baseline/ptrace_stage4_tiled_matmul_os_baseline_steady.csv`
- `thermal/pact/stage4_tiled_matmul_os_baseline/config_stage4_tiled_matmul_os_baseline.config`
- `power/stage3_tiled_matmul_os_baseline_metadata.json`

转换后的 ATSim 输入在 `inputs/` 下：

- `proxy_stage4_tiled_matmul_os_baseline_lcf.csv`
- `proxy_stage4_tiled_matmul_os_baseline_flp.csv`
- `proxy_stage4_tiled_matmul_os_baseline_power.csv`
- `proxy_stage4_tiled_matmul_os_baseline.config`
- `proxy_stage4_tiled_matmul_os_baseline_simparams.config`
- `manifest.json`

## 转换方法

转换脚本：

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python \
  thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/prepare_atsim_v1_proxy_inputs.py
```

关键设置：

| 项 | 值 |
| --- | --- |
| ATSim 模型 | v1 steady-state, single active Si layer, NoPackage boundary |
| grid units | 64 x 64, 4096 proxy units |
| fine result grid | 4096 x 4096 output points |
| power | `Power_dyn = Stage 4 steady proxy Power`, `Power_leak = 0` |
| total proxy power | 1.0000000000003046 W |
| Si thickness | 0.0001 m |
| Si conductivity | 129.87012987012986 W/(m-K), from `1 / 0.0077` |
| ambient/init | 318.15 K |

## 运行命令

```bash
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.csv \
  --ConfigFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline.config \
  --SimParamsFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_simparams.config
```

本次运行已通过，exit status 为 `0`。stdout/stderr 和 attempt 记录见：

- `logs/run_atsim3d_stdout.log`
- `logs/run_atsim3d_stderr.log`
- `logs/run_atsim3d.status`
- `ATTEMPTS.md`

## 输出

ATSim 写出的主结果：

```text
inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res
```

`results/proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res` 是指向上述文件的 symlink。

统计文件：

- `results/atsim_result_summary.csv`
- `results/atsim_result_summary.json`

详细分析见 `RESULTS.md`。

## Stage4-style artifacts

已生成和 `artifacts/stage4` 同风格的图表和统计：

```text
artifacts/stage4/atsim3d_v1_proxy/
```

入口文档：

- `artifacts/stage4/atsim3d_v1_proxy/README.md`
- `artifacts/stage4/atsim3d_v1_proxy/manifest.json`

代表性输出：

- `heatmap_atsim_proxy_downsample_256.png`
- `heatmap_atsim_proxy_downsample_64.png`
- `heatmap_atsim_minus_pact_64.png`
- `heatmap_atsim_minus_pact_raw_order_64.png`
- `atsim_pact_coordinate_delta_comparison.csv`
- `atsim_pact_hotspot_temperature_distribution.png`
- `atsim_pact_hotspot_summary_bar.png`
- `atsim_public_examples_heatmaps.png`
- `atsim_public_examples_summary_bar.png`

详细解释、论文背景和修复后 PACT/HotSpot 对比见 `RESULTS.md` 第 6-8 节。
