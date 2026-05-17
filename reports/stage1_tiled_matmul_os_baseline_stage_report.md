# Stage 1 Tiled Matmul OS Baseline Stage Report

## 11.1 本阶段完成内容

- 重新核对 active 计划、Stage 1 相关文档、线程 smoke 归档和当前产物状态。
- 确认 `tiled_matmul_os` baseline 的功能运行已通过，且 active VCD 仍是当前 Stage 1 正式输入：
  - `sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd`
- 基于修复后的 `scripts/extract_vcd_activity.py`，对现有 `40.83 GiB` VCD 重新执行 activity 提取，而不是重跑完整仿真。
- 更新 `scripts/report_stage1_activity.py`，让 summary 同时保留全局视角和 Gemmini 目标区域高亮。
- 刷新 Stage 1 报告：
  - `reports/stage1_tiled_matmul_os_baseline_windows.md`
  - `reports/stage1_tiled_matmul_os_baseline_activity_summary.md`
- 补充 Stage 1 当前问题与修复记录到 `docs/gemmini_thermal_issue_log.md`。

## 11.2 本阶段关键结果

- 功能运行状态正常：log 中同时出现 `Starting slow CPU matmul` 和 `Starting gemmini matmul`，并记录 `Cycles taken: 2967084` 与 `Cycles taken: 3779`。
- Stage 1 active VCD 可被稳定解析：`parsed_signals=32687`、`time_steps=20606655`、`last_time_ps=10303285500`。
- 重新提取后的 Gemmini 目标 bucket 已全部非零，不再是旧 summary 中的失真状态：
  - `pe_array`: `6558` signals / `2390594` toggles
  - `controller`: `142` signals / `37074715` toggles
  - `load_store_dma`: `393` signals / `20424` toggles
  - `scratchpad`: `6837` signals / `104515396` toggles
  - `gemmini_other`: `3939` signals / `10543973` toggles
- 当前整条 trace 的全局 toggle 排名仍主要由 Rocket/core/cache/TileLink 背景占据，这是因为 Stage 1 输入是完整 `GemminiRocketConfig` SoC 波形，并且大部分时间处于 CPU gold reference 阶段；这不是 Stage 1 失败，而是解释口径必须收束到 Gemmini 目标区域。
- 多线程的当前正确用法已经明确：
  - 若只是刷新 activity / report，优先复用现有 `tiled_matmul_os` VCD，直接运行 parser 多进程。
  - 本轮对该 `40.83 GiB` VCD 使用 `--workers 128` 的实测结果为 `elapsed=0:49.53 cpu=10221% maxrss_kb=94208`。
  - Verilator 仿真线程数不能直接照搬 `128`；当前只有官方 `mvin_mvout` VCD smoke 证明 `VERILATOR_THREADS=16` 在这台机器上更合适，正式大 workload 若必须重跑，应重新按 workload+trace 形式实测选择。

## 11.3 本阶段验收结论

- 结论：**Stage 1 达到验收标准，可以收尾并进入 Stage 2。**
- 验收依据：
  - baseline workload 功能完成；
  - waveform 存在且可读；
  - 冷启动 / CPU reference / steady high-load 窗口已写入 `reports/stage1_tiled_matmul_os_baseline_windows.md`；
  - Gemmini PE array + 控制 + 邻近 datapath 的 activity 已在 summary 中单独呈现。
- 本阶段不符合直觉但并不构成 blocker 的点：
  - whole-trace top toggles 不是 Gemmini 主导；
  - `accumulator` bucket 仍为 `0`。
- 这些现象与当前研究边界一致：Stage 1 使用完整 SoC 作为活动载体，Stage 2-4 才在实现与热分析层面收窄到 Gemmini 阵列相关逻辑；内存阵列本体也不是本轮主要热目标。

## 11.4 下一阶段输入

Stage 2 需要的输入及当前状态：

- `configs/gemmini/hierarchy_map.yaml`：已就绪。
- Stage 1 active VCD：已就绪。
- Stage 1 activity CSV：已就绪。
- Stage 1 windows report：已就绪。
- Gemmini/Chipyard 导出 RTL：需再次检查 `rtl_exports/generated-verilog/GemminiRocketConfig/` 是否完整可直接作为 Stage 2 缩边界的输入；若缺失则先补跑 RTL generation，而不是直接启动 ORFS。
- ASAP7 reduced techlib / OpenROAD / OpenSTA：文档和环境检查显示已就绪。

进入 Stage 2 时的执行建议：

- 不做全 SoC 实现，先用 Stage 1 已确认的模块边界收缩实现 top。
- 多线程优先用于两个地方：
  - Gemmini/Chipyard 仿真构建可按当时环境使用构建并行；但 Stage 2/3 ORFS/后端 `MAKE_JOBS` 表示外层独立任务数，当前上限为 `4`，单条主线使用 `MAKE_JOBS=1`；
  - 如果需要再次处理大 VCD，优先使用 parser `--workers`，不要默认先重跑仿真。
- 只有在 Stage 2 真正需要新的波形或新的 simulator 配置时，才重新考虑 `VERILATOR_THREADS`；届时先做最小 smoke，再决定是否重建 debug simulator。
