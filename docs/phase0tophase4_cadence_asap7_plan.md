# Gemmini 16x16 Cadence ASAP7 Stage 0-4 主计划

## 0. 文档定位

本文件是当前 active 主计划，替代以下 legacy OpenROAD/proxy 计划：

- `docs/references/legacy_openroad_proxy/phase0tophase4_plan.md`
- `docs/references/legacy_openroad_proxy/phase0tophase4_signoff_multiworkload_plan.md`

当前目标保持原研究边界，只替换综合、布局布线和功耗获取方法：

```text
Stage 0 研究定义
-> Stage 1 RTL activity waveform
-> Stage 2 Cadence Genus + Innovus full-ASAP7 standard-cell implementation
-> Stage 1b Gemmini-only r28 gate-level boundary replay SAIF handoff for Phase3; formal SAIFs are Verilator zero-delay activity, not SDF timing or commercial gate simulation
-> Stage 3 Cadence activity-aware grid-level power waveform
-> Stage 4 PACT thermal simulation + ATSim3D v1 steady comparison + HotSpot coarse comparison
```

本计划最初验收级别为 `commercial-flow project validation`，不是 foundry signoff。2026-05-12 经用户确认，Stage 2 因 ASAP7/Cadence PG special connectivity blocker 降级为 `PG-open thermal proxy`。2026-05-13 经用户确认，routed SDF 从 Stage 2 mandatory artifact 降级为 waived/best-effort artifact：当前研究可以直接跳过 routed SDF，使用 DEF、routed Verilog、SPEF、GDS、checkpoint 和 post-route reports 进入 Stage 3/4。该降级不得被描述为 routed-SDF-complete、timing-signoff 或 gate-level SDF simulation evidence。Calibre、完整 DRC/LVS、IR/EM、package/TSV/3D-IC 扩展不属于本计划范围。

## 1. 固定研究边界

本轮只允许一个 Gemmini 硬件配置：`GemminiRocketConfig` + `DefaultGemminiConfig`。

| 字段 | 固定值 |
| --- | --- |
| Chipyard config | `GemminiRocketConfig` |
| Gemmini config | `DefaultGemminiConfig` |
| `tileRows` / `tileColumns` | 1 / 1 |
| `meshRows` / `meshColumns` | 16 / 16 |
| effective `DIM` | 16 |
| input / weight type | int8 |
| accumulator type | int32 |
| dataflow support | `Dataflow.BOTH` |
| scratchpad capacity | 256 KiB |
| accumulator capacity | 64 KiB |
| scratchpad banks | 4 |
| accumulator banks | 2 |

固定 workload 集合：

| workload | 角色 |
| --- | --- |
| `tiled_matmul_os` | output-stationary GEMM，PE 阵列持续高负载 baseline |
| `tiled_matmul_ws` | weight-stationary GEMM，同规模 dataflow 对照 |
| `mvin_mvout` | 数据搬运、DMA、scratchpad 周边和控制路径对照 |

不得在本轮加入额外 workload、替换 workload、缩小 workload 规模、切换硬件配置、做配置 sweep 或引入 thermal-aware/RTL/timing 优化目标。若这些需求出现，必须先修改本计划。

## 2. Run 目录

当前 active run 根目录保持不变：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/
```

`__signoff` 后缀是 Stage 2 质量降级前保留下来的历史 run-root 名称，不代表当前 signoff-clean 质量，也不能因此删除或重命名该目录。当前接受的 Stage 2 handoff 是 r28，质量标签为 `PG-open / DRC-open / routed-SDF-waived thermal proxy`。

该目录内 Stage 0/1 已生成的 RTL、workload、simulation、activity 和报告可以继续作为当前输入。来自旧 OpenROAD/ORFS/reduced-ASAP7 的 Stage 2 产物不再是 active 结果，不得作为 Stage 3/4 handoff 输入；如需清理或重置，必须先确认不会误删当前保留的中间产物。

推荐目录结构：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/
  config/
  rtl/
  workloads/
  sim/
  activity/
  physical/
    <tag>/
      config/
      genus/
      innovus/
      reports/
      results/
      logs/
  gate_activity/
    phase1b_mvin_mvout_boundary_replay_<tag>/
  power/
  thermal/
  reports/
  artifacts/
```

## 3. 工具和 PDK

### 3.1 Cadence

Cadence 安装位置：

```text
/opt/eda/Cadence_DDI_23.14
```

已验证版本：

| 工具 | 版本 | 说明 |
| --- | --- | --- |
| Genus | `23.14-s090_1` | license checkout `Genus_Synthesis` 通过 |
| Innovus | `v23.14-s088_1` | license checkout 通过；当前 license banner 显示 8 CPU jobs |

环境变量以 `tools/env_gemmini_thermal.sh` 和 Cadence 检查脚本为准。Genus/Innovus 多线程参数不能沿用 OpenROAD `MAKE_JOBS` / `NUM_CORES` 语义：

- Genus 使用 flow Tcl 内的 CPU 设置，默认不超过 `TP_CADENCE_GENUS_CPUS`。
- Innovus 使用 `-cpus` 和 `setMultiCpuUsage`，默认不超过 `TP_CADENCE_INNOVUS_CPUS`。
- 当前 license 冒烟证据显示 Innovus 许可允许 8 CPU jobs；大规模 run 之前必须复查 license banner。

参考记录：`docs/references/cadence_genus_innovus_edahub_smoke_2026-05-04.md`。

### 3.2 Full ASAP7

完整 PDK 外部路径：

```text
ASAP7_HOME=/home/lisihang/asap7
```

主流程默认使用：

| 项目 | 默认值 |
| --- | --- |
| stdcell family | `asap7sc7p5t_28` |
| collateral scale | 1x |
| Liberty model | NLDM |
| VT classes | RVT, LVT, SLVT |
| primary corner | TT |
| tech LEF | `asap7sc7p5t_28/techlef_misc/asap7_tech_1x_201209.lef` |
| stdcell LEF | `asap7sc7p5t_28/LEF/*_1x_220121a.lef` |
| QRC | `asap7sc7p5t_28/qrc/qrcTechFile_typ03_unscaledV02` |

ASAP7 standard-cell Liberty 原始文件为 `.lib.7z`。不得把解压后的 Liberty 提交到仓库；由脚本生成到：

```text
.cache/asap7/
```

本轮使用 NLDM 完成 flow。CCS 作为后续可选增强记录，不进入当前验收。

### 3.3 Fake SRAM

当前 memory/SRAM 采用 fake SRAM policy。外部仓库只作为生成方法和 ASAP7 参数参考：

```text
FAKE_SRAM_HOME=/home/lisihang/fake_sram
```

目标是让 Genus/Innovus 能完成标准单元实现，同时保持热仿真研究目标聚焦于 PE array、control logic、nearby datapath 的标准单元热行为。fake SRAM 提供综合和布局所需的 timing/physical abstract，不作为详细 SRAM 热模型。

原则：

- 不延续旧 blackbox 阶段的假设；从当前 Gemmini RTL 和 Cadence 实现需求出发识别 memory shapes。
- 本仓库新增适配层，不直接修改 `/home/lisihang/fake_sram`，除非用户单独要求。
- 当前 active flow 不直接使用 `/home/lisihang/fake_sram/results/asap7` 中已有 design 类型。
- Cadence flow 使用本仓库从 Gemmini RTL 第一性原则生成的 fake SRAM cache：`.cache/fake_sram/asap7/Gemmini/`。
- 当前 Gemmini RTL 可达 external memory shapes 为 `mem_ext` 和 `mem_0_ext`：
  - `mem_ext`：wrapper `mem`，`1rw`，depth `4096`，width `128`。
  - `mem_0_ext`：wrapper `mem_0`，`1r1w`，depth `512`，width `512`。
- 生成器 `scripts/prepare_gemmini_fake_sram_collateral.py` 输出 Liberty、LEF、Verilog stub 和 manifest。Liberty 使用 ASAP7 TT `0.7V/25C`，LEF/面积按 fake_sram 生成方法参数估算。
- `/home/lisihang/asap7/asap7_sram_0p0` 只作为未来可选真实 SRAM macro 路线记录。

## 4. Stage 0

Stage 0 固定当前研究边界、输入目录、工具版本、PDK 路径和 run manifest。

必须输出：

- `config/run_manifest.json`
- `config/gemmini_config_snapshot.md`
- `config/workload_manifest.md`
- `config/environment_manifest.md`
- Cadence/full-ASAP7/fake-SRAM preflight report

Stage 0 不运行大规模 VCD、综合、P&R 或热仿真。

## 5. Stage 1

Stage 1 使用 Verilator 已跑通的 RTL simulation 和 VCD/SAIF 活动证据。当前主格式仍是 RTL VCD；SAIF 可以作为 Cadence power handoff 的转换格式。

每个 workload 必须保留：

- binary、stdout/stderr、functional pass/fail
- RTL VCD 或等价 activity source
- activity CSV、window report、method report

Stage 1 不引入商业 gate simulation。商业 gate activity simulation 不是当前 Stage 1 任务。

### 5.1 Stage 1b: Gemmini gate-level SAIF boundary replay handoff

2026-05-12 经用户确认，新增 Stage 1b 作为 Stage 1 的补充验证阶段。2026-05-14 曾将 Phase1b 临时收窄为 `mvin_mvout` Gemmini-only boundary replay compare feasibility；该旧验证计划已完成并归档为 historical validation only，不再作为正式 handoff。2026-05-15 经用户确认，正式 Phase1b 目标改为 **三个固定 workload 的 Gemmini-only gate-level SAIF generation for Phase3**。

Stage 1b 正式目标固定为 **Gemmini gate-level boundary replay with SAIF output**：

- 只仿真 `Gemmini` gate-level top，不做 full-SoC gate simulation。
- 三个 workload 均进入正式 Phase1b：`mvin_mvout`、`tiled_matmul_ws`、`tiled_matmul_os`。
- 正式执行顺序固定为 `mvin_mvout -> tiled_matmul_ws -> tiled_matmul_os`。
- 每个 workload 产出一个 gate-level SAIF，供 Phase3 消费；默认不生成 gate VCD。
- 正式 Phase1b 不做 output compare，不生成 mismatch CSV/report，不以功能 compare clean 作为成功标准。
- Phase1b success criteria 是 SAIF handoff completeness：shared executable build 完成、每个正式 workload replay 完成、SAIF 非空、trace window 有覆盖、manifest/report 完整。

正式 Phase1b primary gate netlist 固定为当前 accepted Stage2 r28 routed/export Verilog：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v
```

r28 是 `PG-open / DRC-open / routed-SDF-waived thermal proxy`，不是 PG-clean、DRC-clean、routed-SDF-complete、timing-signoff、IR/EM-clean、LVS/foundry/signoff-clean evidence。Phase1b SAIF 是 Verilator zero-delay gate activity，不是 SDF timing simulation，也不是 commercial gate simulation。若 r28 routed netlist 因技术原因不可推进，不得自动 fallback 到 r2；必须先向用户汇报并等待确认。

正式 Phase1b run 目录固定为：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/
```

若该目录已存在且非空，默认停止，不覆盖、不删除、不自动 resume，除非用户明确确认。目录结构约定：

```text
phase1b_gate_saif_r28_20260515/
  build/
    verilator_build/
    referenced_cell_library/
    build_manifest.json
    build.log
    split_manifest.json
  smoke_mvin_mvout_100cyc/
    boundary_vectors.csv
    boundary_vectors_manifest.json
    boundary_signal_map.json
    boundary_signal_map.csv
    trace_window.json
    gate_activity.saif
    replay_summary.json
    gate_activity_manifest.json
    smoke_report.md
  mvin_mvout/
    boundary_vectors.csv
    boundary_vectors_manifest.json
    boundary_signal_map.json
    boundary_signal_map.csv
    trace_window.json
    gate_activity.saif
    replay_summary.json
    gate_activity_manifest.json
  tiled_matmul_ws/
    ...
  tiled_matmul_os/
    ...
  phase1b_gate_saif_handoff_manifest.json
  phase1b_gate_saif_method_report.md
```

旧验证计划目录保留为 historical validation only：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/
```

该目录包含旧 `mvin_mvout` compare feasibility、validity-aware harness repair、mismatch triage、shifted compare 和旧报告 `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/phase1b_mvin_mvout_gate_boundary_replay_20260514.md`。它不进入新 Phase1b handoff manifest，不作为 Phase3 输入，不作为新 r28 build cache，也不阻塞新 SAIF flow。旧 `auto_spad_id_out_a_bits_address` mismatch 根因尚未完全清楚；用户已定性为因时间尺度占比极低，不会显著影响热仿真效果，后续默认不反复关注，除非出现更广泛 activity/functional 影响或用户明确要求重开。

正式 workload trace windows 固定沿用 Stage1 selected windows，不额外 refine：

| workload | Stage1 window | trace_start_ps | trace_end_ps |
| --- | --- | ---: | ---: |
| `mvin_mvout` | `data_movement_active` | 66875550 | 601879950 |
| `tiled_matmul_ws` | `steady_high_load` | 1072392550 | 3753373925 |
| `tiled_matmul_os` | `steady_high_load` | 9272956950 | 10303285500 |

Boundary extraction policy：

- 每个 workload 重新从对应 Stage1 RTL VCD 抽取正式 inputs-only boundary vectors，不复用旧验证目录中的 vectors。
- `start_ps=0`，`end_ps=trace_end_ps`。
- `boundary_vectors.csv` 只保存 `cycle`、`time_ps`、`clock`、`reset` 和 Gemmini input ports；不保存 expected output ports。
- `boundary_signal_map.json/csv` 仍记录 top ports，用于审计和 provenance。
- r28 `Gemmini.routed.v` top ports 与 RTL Gemmini VCD top-level scope 的硬 preflight 只要求使用 `mvin_mvout` VCD 做一次 mapping smoke；其他 workload extraction 若自然遇到 missing/width mismatch 仍必须停止。
- replay 保留 `clock` column 作为 provenance，但 clock 由 harness 生成，不直接由 CSV clock 驱动。
- replay 输入驱动语义沿用旧方法：对 replay cycle `N`，用 row `N-1` input vector 驱动下一拍；trace-on 判断使用 current sampled row `N` 的 `time_ps`。
- trace-on 半开区间为 `trace_start_ps <= time_ps < trace_end_ps`。

SAIF policy：

- 使用本机 Verilator direct SAIF trace：`--trace-saif`。
- 固定 `--trace-depth 9`，不反复调参。
- 每个正式 workload 输出一个 raw Verilator SAIF，rooted at Verilated `Gemmini` top，不在 Phase1b 中做 hierarchy/name remap。
- Phase3 必须负责 Cadence activity-file instance/scope mapping 和 annotation coverage report；本地 Innovus/Voltus 23.14 帮助显示 SAIF 入口应使用 `read_activity_file -format SAIF`，当前未找到可用 `read_saif` 帮助入口。若 coverage 不佳，默认在 Phase3 调整 mapping，而不是回改 Phase1b SAIF hierarchy。
- 使用 Verilator 默认 SAIF time output，不手工改 timescale；manifest 记录 RTL VCD `time_ps`、requested/actual trace coverage、Verilator version、flags 和 window provenance。
- 每个 workload 保留普通文本 `.saif`、`.csv`、`.json`、`.md` 产物，不默认压缩。


Acceleration attempt policy as of 2026-05-15:

- A harness-only acceleration attempt is being documented under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/accelerate/`.
- The attempt uses copied inputs-only boundary CSVs, converts them to fixed little-endian binary/preparsed vectors, compiles only a new binary-input harness, and relinks `accelerate/build/VGemmini_accelerate` against the existing r28 `VGemmini__ALL.a` and Verilator runtime objects.
- It must not rerun Verilator frontend, recompile generated `VGemmini*.o`, modify r28 netlist, modify Chipyard/Gemmini RTL, use `--hierarchical`, fallback to r2, reduce trace depth, reduce SAIF dump count, or perform output compare.
- The accelerated executable must be named `VGemmini_accelerate`, not `VGemmini`.
- Acceleration smoke must pass before formal accelerated replays. If smoke passes, the three formal accelerated workload replays may run in parallel; one failed workload must not terminate the others.
- This is not yet the default formal Phase1b route or Phase3 handoff method. After acceleration smoke/runtime evidence is available, ask the user before updating the main Phase1b method to use accelerated binary replay.
- Existing unoptimized `VGemmini` or mainline Phase1b processes may run concurrently and must not be interrupted by acceleration work.

Build policy：

- shared r28 executable 只 build/relink 一次；smoke 和三个 workload 共用同一个 executable。
- 三个 workload 单独启动 replay 进程，一个接一个完成，不共享 runtime state。
- 2026-05-15 user update: next formal replay launch is prepared to run the three workload replay processes simultaneously, each with separate runtime state and the already-built shared executable. This supersedes the earlier one-at-a-time launch policy for the next attempt only unless changed again.
- formal baseline uses non-hierarchical Verilator. Do not use `--hierarchical` by default; if non-hierarchical build fails or becomes impractical, stop and ask the user before trying `--hierarchical`.
- Verilator front-end jobs 固定使用 `--verilate-jobs 192`。
- Verilator model/runtime threads 固定使用 `--threads 16`。
- Make parallelism 固定使用 `make -j192`。
- 使用 `--compiler clang`、manual make with `CXX=clang++ LINK=clang++`、`--no-timing`、`-CFLAGS "-O0 -g0"`。
- split baseline 固定为 `--output-split 200 --output-split-cfuncs 20 --output-split-ctrace 20`。
- referenced-cell-only ASAP7 library 必须基于 r28 routed netlist 重新统计 actual referenced cells，并保留 required ASAP7 UDP primitives；不得复用旧 r2 referenced-cell set 假设。
- Verilator front-end 后扫描 generated C++。若单个 generated C++ file 超过 `128 MiB`，正式 policy 是在新 run 目录内拆成 32 个 helper C++ files，再执行 make。可自动拆；自动拆不安全时允许在新 run 目录内手动拆分并继续。不得修改 Chipyard/Gemmini RTL、r28 netlist、Stage2 physical run 产物或旧证据。
- 2026-05-15 actual r28 build status: Verilator frontend succeeded; generated objects were verified complete after repeated GNU make returncode 139 at the build tail; manual archive/index/link tail inside the formal build directory produced the shared `build/verilator_build/VGemmini` executable. This preserves r28/non-hierarchical/no-r2 policy and is documented in `build/manual_link_completion_20260515.json`.

Smoke policy：

- smoke 使用正式 shared r28 executable，不单独 build。
- smoke workload 固定为 `mvin_mvout`，产物目录为 `smoke_mvin_mvout_100cyc/`。
- smoke trace window 固定为 active window start 附近 100 cycles：`[66875550, 67075550)` ps。
- smoke replay 仍从 `time_ps=0` warmup 到 trace window；100 cycles 只限定 trace-on window，不限定全局 replay 前 100 cycles。
- smoke 不做 compare，不进入 Phase3 handoff manifest，只用于检查 harness、SAIF trace API、trace window gating 和 non-empty SAIF。

Monitoring policy：

- 启动阶段密集确认进程、日志和输出目录正常。
- 确认正常运行后，所有长时间 Verilator front-end、make 和 replay 任务约每 20 分钟检查一次。
- 检查进程状态、日志尾部和关键输出文件状态。
- 只要没有明确错误、进程退出、资源异常或用户新指令，不主动中断。
- 不设置磁盘空间 preflight gate；用户已确认磁盘空间足够。

Required formal outputs：

- r28 referenced-cell-only library and manifest, including UDP primitive inclusion evidence.
- shared Verilator build manifest, command lines, Verilator version and split manifest if splitting occurs.
- no-compare SAIF smoke report.
- per-workload `gate_activity.saif`、`trace_window.json`、`replay_summary.json`、`gate_activity_manifest.json`、inputs-only boundary vectors and manifests.
- global `phase1b_gate_saif_handoff_manifest.json` listing included formal workload SAIFs and excluded smoke/old-validation artifacts.
- global `phase1b_gate_saif_method_report.md` for human review.

正式 Phase1b 脚本和 collateral 只能新增/修改在仓库受控位置，例如 `scripts/` 与 `collateral/gate_sim/`。不得修改 Chipyard/Gemmini RTL，不得编辑 r28 `Gemmini.routed.v` 或 Cadence run 目录内的源产物。正式执行入口应是 new SAIF orchestration flow，而不是旧 compare replay script。

## 6. Stage 2: Genus + Innovus

Stage 2 针对固定硬件配置做一次可复用物理实现，三个 workload 共用。2026-05-12 起当前质量等级为用户批准的 `PG-open thermal proxy`，目标是为 Stage 3/4 提供标准单元 placement/routing/timing/power/geometry 证据，而不是 PG-clean signoff。

### 6.1 Genus 输入

- Gemmini target RTL/filelist
- full ASAP7 NLDM Liberty cache：RVT/LVT/SLVT TT
- fake SRAM Liberty/stub policy
- timing constraints
- synthesis top and module-boundary manifest

### 6.2 Genus 输出

- mapped gate-level netlist
- SDC
- Genus SDF if available, recorded only as handoff context; routed Innovus SDF is waived for the current thermal-proxy acceptance after the 2026-05-13 user decision
- timing report
- area report
- power report
- QoR/report summary
- Genus database/checkpoint

### 6.3 Innovus 输入

- Genus mapped netlist
- MMMC setup using ASAP7 NLDM libraries
- full ASAP7 1x tech/stdcell LEF
- fake SRAM LEF
- QRC tech file
- floorplan, power/ground nets, placement/CTS/route config

### 6.4 Innovus 输出

必须输出：

- placed/routed DEF
- SPEF
- routed SDF waiver report if no usable routed SDF exists
- routed Verilog
- GDS
- Innovus database/checkpoint
- timing report
- area/utilization report
- power report
- route/DRC summary

不要求 Calibre DRC/LVS。Innovus 内部 DRC/route checks 和 PG connectivity 必须记录。PG special-route opens 是已知降级项；若最终 run 仍有 PG opens，Stage 2 只能作为 `PG-open thermal proxy` 进入 Stage 3/4，报告必须显式标注 non-signoff。除已批准的 PG-open 和 routed-SDF waiver 限制外，若存在会阻止 DEF/Verilog/SPEF/GDS、checkpoint、post-route reports 或 power extraction 生成的 blocking violation，仍不能进入后续阶段。

### 6.5 Phase 2 implementation policy and dacs-lab lessons

Phase 2 正常开发必须优先使用 Python entry point / Python manager 生成 Genus 和 Innovus Tcl。Tcl 是工具执行层，不是长期维护入口。Gemmini 主线当前固定时序目标为 `200 MHz` / `5.000 ns`。2026-05-06 起，先前 run-local `physical/cadence/python_flow/` bring-up 架构已删除；新的启动基线是从 `third_party/dacs-lab` 完整复制得到的 `runs/cadence_startup/`。当前已建立 Gemmini-specific startup entry `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py`，输出根为 `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/`；`manager/` 已接入 same-env script-only Genus/Innovus Tcl 生成，后续真实商业工具运行必须在 review 生成 Tcl 后显式启动。只有以下情况允许直接运行或编辑 Tcl：

- 调试某个失败环节，例如从 `placement.enc` 或 `routing.enc` 恢复单步验证。
- 对 Innovus/Genus 命令做一次性诊断，例如确认 IO pin、DRC、streamOut、license 或 library path 问题。
- 导出补充证据，例如 routed DEF/GDS/PNG，而主 Python flow 暂时还没有产品化该输出。

任何 Tcl-only 修复如果被证明是正常流程所需，必须回收到 Python 配置或 Python 生成逻辑里，再作为 Phase 2 默认路线使用。

2026-05-05 `third_party/dacs-lab` full-ASAP7 PPAdder compatibility run 给 Phase 2 的直接经验：

- Run/result directory 必须有语义，至少包含 design/config、library/collateral、clock target、run purpose 和日期或 tag；禁止只用 hash 作为唯一目录名。
- Clock target 不能是 `0.0 ns`。当前小设计验证使用 `10.0 ns` / `100 MHz`，Gemmini 主线必须显式记录目标约束。
- IO pin placement 是 Gemmini Phase 2 必需项。Innovus floorplan 后必须验证 top-level pins 已在 DEF 中 `PLACED` 或 `FIXED`，并检查日志没有 unplaced terms。
- `assignIoPins -autoBusGroup` 已在 PPAdder 上验证为可用起点：`PINS 194` 且 `194/194` pins placed。Gemmini 可以先采用 Python-managed 自动分配，再根据拥塞/边界 pin 需求细化 layer/side/group 约束。
- Cadence threading 不能沿用 OpenROAD 变量语义。Genus/Innovus init/place 可以使用 license 允许的 8 CPU；route 阶段若触发 internal abort 或 SI-aware 问题，应先用 Python knob 降到 `localCpu=1` 且 SI-aware false 做恢复验证。
- Non-clean 原因要分类记录：route DRC、PG connectivity、tech-collateral warning/error、外部 DRC/LVS 未运行，不能只看 Python command exit code。
- 版图图片不等同于 GUI 截屏。可接受的 headless 证据路线是 Innovus `streamOut` 导出 GDS，再用 KLayout offscreen 渲染 PNG；若需要 Innovus 原生截图，必须有 GUI/X display。

### 6.6 Current Stage 2 quality downgrade: PG-open and routed-SDF-waived thermal proxy

2026-05-12 用户明确接受当前 Phase 2 从 PG-clean accepted flow 降级为 `PG-open thermal proxy`，并停止继续 PG repair attempts。2026-05-13 用户进一步确认可以直接跳过 routed SDF。PG-open 降级只放宽 PG special connectivity cleanliness；routed-SDF waiver 只放宽 routed SDF artifact。其他 Stage 2 handoff artifact 仍必须产出。

必须继续产出的 Stage 2 artifacts：

- routed DEF
- routed Verilog
- SPEF
- routed SDF waiver report if no usable routed SDF exists
- GDS
- `cts.enc`
- `routing.enc`
- post-route timing/area/power reports
- route/DRC/connectivity reports
- macro placement and top-level pin placement evidence

使用限制：

- 最终报告必须写明 `verifyConnectivity -type special` 的 VDD/VSS open 数量、`verify_PG_short` 结果、route/DRC 摘要和 ASAP7 collateral warnings。
- PG opens 不得描述为普通可忽略 DRC；它们意味着工具不能证明完整电源 special-net connectivity。
- Stage 3/4 可以消费该实现作为 thermal proxy，但结论必须限定为 placement/activity/power-driven thermal trend，不得声称 PG-clean signoff、IR/EM、电源完整性结论、routed-SDF-complete 或 SDF timing simulation。
- 旧 OpenROAD/reduced-ASAP7/proxy power 仍不是 active input；当前降级只针对 Cadence/full-ASAP7 run 的 PG connectivity、route/DRC cleanliness 和 routed-SDF artifact completeness。

## 7. Stage 3: Cadence activity-aware power

正式路径禁止旧式固定功率 proxy。旧 `build_stage3_power_grid.py` 和固定 1W normalization 只能作为历史 reference，不得作为当前输入。2026-05-12 后，Stage 3 可以消费用户批准的 Cadence `PG-open thermal proxy` Stage 2 实现，但必须保留 PG-open/non-signoff 标签。

当前 Stage 3 路线：

1. 优先消费正式 Phase1b r28 gate SAIF handoff 中已完成且 manifest 标记为 `phase3_consumable=true` 的 workload。Phase1b SAIF 是 Verilator zero-delay gate activity，不是 SDF timing simulation、commercial gate simulation 或 signoff activity。
2. 在 Cadence 中读取 activity，结合 Liberty、r28 routed netlist、SPEF 和 post-route timing/power evidence 生成 instance power；routed SDF 仅在可用时作为附加记录，不是当前 thermal-proxy 输入前提。
3. 将 Innovus placement/DEF 中的 instance 坐标与 instance power 对齐。
4. 聚合为 physical grid power CSV 和 transient power trace，服务 PACT、HotSpot 和 grid-level ATSim3D comparison。
5. 额外生成 ATSim3D v1 instance-level refinement handoff：完整 full-chip standard-cell instance geometry/power catalog，以及可用于 Phase4 从 hotspot ROI 切片生成 ATSim3D v1 floorplan/power/LCF/config/SimParams 的 manifest 和 method report。

2026-05-16 当前 Phase3 开发范围先限定为 `mvin_mvout` 单 workload bring-up，因为主线 `mvin_mvout` formal SAIF 已完成且可作为 Phase3 候选输入；主线 `tiled_matmul_ws`/`tiled_matmul_os` 和 accelerated `mvin_mvout`/`tiled_matmul_ws`/`tiled_matmul_os` replay 仍在运行或尚无完整 summary/manifest，不得作为 Phase3 handoff 输入，且不得打断这些运行。当前 `mvin_mvout` Phase3 bring-up 输出目录固定为 `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/`。 2026-05-16 已生成 script-only Cadence collateral 于 `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/`；该步骤未启动 Innovus，后续执行 runner 需用户单独确认。

每个 workload 必须输出：

- activity handoff manifest
- Cadence power command/log/report
- instance power report
- instance-to-grid map
- grid power CSV
- transient power trace
- top-N power instance report
- region power summary
- ATSim3D v1 full-chip standard-cell instance geometry/power catalog for hotspot ROI refinement
- method report

Stage 3 当前允许消费正式 Phase1b r28 gate SAIF handoff，但只消费已完成、非空且 manifest 标记为 `phase3_consumable=true` 的 formal workload SAIF。Smoke SAIF、旧 r2 compare validation、0 字节 SAIF、缺少 `replay_summary.json`/`gate_activity_manifest.json` 的目录、以及尚在运行中的 accelerated/mainline replay 产物都不得作为 Phase3 handoff 输入。Phase3 必须执行 Cadence `read_activity_file -format SAIF` scope/instance mapping 和 annotation coverage report；若 coverage 不佳，优先在 Phase3 调整 mapping，而不是回改 Phase1b SAIF hierarchy。

## 8. Stage 4: Thermal

Stage 4 保持原研究目标并新增 layout-object-level ATSim3D 路径：

- PACT steady thermal simulation from Stage3 grid power
- PACT transient thermal simulation, if Stage 3 transient power trace exists
- ATSim3D v1 grid-level independent steady comparison for continuity with existing grid flow
- ATSim3D v1 local instance-level hotspot refinement: Phase4 first identifies hotspot ROI from grid-level results, then slices Phase3 full-chip standard-cell instance catalog so every placed standard-cell instance in the ROI becomes one ATSim3D object
- HotSpot coarse comparison

输入必须来自 Stage 3 Cadence activity-aware power，不再使用旧式 fixed-power proxy grid。PACT、HotSpot 和 grid-level ATSim3D 消费 Stage3 physical grid power；新增 local instance-level ATSim3D v1 refinement 消费 Stage3 生成的完整 full-chip standard-cell instance geometry/power catalog，由 Phase4 根据 grid-level hotspot ROI 切片生成局部 ATSim3D floorplan/power/LCF/config/SimParams。若 Stage 3 输入来自 PG-open Stage 2 proxy，Stage 4 报告必须继承并说明该 non-signoff 限制。

坐标约定保持：

```text
grid_y=0 是 die bottom，grid_y 向上增加。
```

若 PACT raw row order 与 physical grid 相反，主产物必须转换：

```text
physical_grid_y = grid - 1 - pact_raw_row_y
```

raw row-order 文件只保留为 audit，文件名必须显式标注 `_pact_raw_order`。

ATSim3D v1 local instance-level refinement format must follow the local public examples in `third_party/ATSim3D_pub`: LCF columns `Layer,Main_compo,Thickness (m),FloorplanFile,PowerFile,Clip_num_x,Clip_num_y,Clip_num_z`; floorplan rows keyed by `UnitName` with meter-scale `X,Y,Length (m),Width (m)` and material `Label`; power rows keyed by the same `UnitName` with `Power_dyn` and `Power_leak`. Phase3 must provide a complete full-chip placed standard-cell instance geometry/power catalog; Phase4 selects a hotspot ROI after the grid-level thermal pass and emits a local ATSim3D case where each placed standard-cell instance in that ROI is one ATSim object. Do not treat the first mvin object-level input as time-resolved excitation; it remains `single_window_average`.

## 9. 文档和记录规则

任何以下变化必须同任务更新文档：

- active plan 或阶段边界
- Cadence/ASAP7/fake SRAM 路径或版本
- script entry point、output path、run directory convention
- Stage 2/3/4 方法变化
- failed attempt、retry、route change
- 工具 license/threading 观察

优先更新：

- `AGENTS.md`
- `docs/README.md`
- `docs/agent_onboarding.md`
- `docs/agent_task_checklist.md`
- `docs/agent_command_reference.md`
- `docs/gemmini_thermal_environment_setup.md`
- `docs/tool_environment_inventory.md`
- `docs/gemmini_thermal_issue_log.md`
- 本文件

## 10. 当前验证记录

2026-05-05 已完成轻量验证：

- Genus `23.14-s090_1` version/license smoke 通过。
- Innovus `v23.14-s088_1` version/license smoke 通过。
- Genus 可读取从 `/home/lisihang/asap7/asap7sc7p5t_28/LIB/NLDM` 解压的 RVT TT NLDM Liberty。
- Innovus 可读取 `/home/lisihang/asap7/asap7sc7p5t_28` 的 1x tech LEF 和 RVT 1x stdcell LEF。

下一步验收顺序：

1. Cadence/full-ASAP7/fake-SRAM environment checker。
2. ASAP7 NLDM cache generation for RVT/LVT/SLVT TT。
3. fake SRAM collateral shape/manifest check。
4. small-design Genus + Innovus smoke。
5. Gemmini Genus frontend read/elaboration smoke。
6. Gemmini Genus synthesis。
7. Stage 1b mvin_mvout Gemmini gate-level boundary replay functional-compare feasibility, after a mapped `Gemmini-mapped.v` exists。
8. Gemmini Innovus place/CTS/route/extract。
9. Stage 3 Cadence power grid。
10. Stage 4 thermal rerun from non-proxy power.
