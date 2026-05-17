# Gemmini 阵列相关逻辑标准单元级热仿真执行计划（Codex 严格执行版）

> **Superseded reference notice (2026-04-29):** 本文件已被 `docs/phase0tophase4_signoff_multiworkload_plan.md` 取代。
> 本文件仅作为旧单 workload / proxy prototype 路线参考，不再作为 active 执行目标。
> **2026-05-03 Stage 4 errata:** 虽然本文件是历史 reference，旧 Stage 4 PACT 坐标说明仍必须按当前修复后的事实理解：PACT raw row `0` 对应物理 die top，主产物必须转换到 DEF physical grid，`grid_y=0` 在 die bottom。旧 raw hotspot `(22,47)` 不得作为物理坐标使用；修复后的 PACT steady layer0 physical hotspot 是 `(22,16)`。若生成 SVG 图表，必须同时生成同 basename PNG 便于 VS Code/远程预览。


## 0. 文档定位

本文件用于指导 Codex **严格按阶段** 执行阶段 0–4，不做阶段 5 及之后的优化工作。  
当前目标是：

> 以 **Gemmini 中“PE array + 控制 + 紧邻数据通路”** 为研究对象，完成一个 **单一 GEMM baseline** 的标准单元级热仿真闭环：  
> **阶段 0 研究定义 → 阶段 1 RTL 活动波形 → 阶段 2 ASAP7 标准单元实现 → 阶段 3 grid 级功耗波形 → 阶段 4 PACT 主线热仿真 + ATSim3D v1 独立热仿真 + HotSpot 粗对照**

本轮只要求先用 **一个样例** 跑通完整流程。后续再扩展不同 workload 和不同阵列配置。  
本计划范围聚焦在架构热仿真与热画像构建，暂时不做热优化。

---

## 1. 顶层目标

### 1.1 本轮唯一主目标
跑通一个 **持续高负载 GEMM** baseline 的完整阶段 0–4 流程，并输出：

1. 一批可直接用于展示的热图和曲线  
2. 一套可用于论文/开题/答辩的实验骨架  
3. 一份可复现流程记录  

优先级排序严格为：

1. **热图和曲线**
2. **实验骨架**
3. **可复现流程**

### 1.2 本轮明确不做
以下内容全部禁止纳入本轮：

- 热驱动综合
- 热驱动布局优化
- thermal-aware floorplanning / placement
- RTL 结构优化
- timing closure 优化
- 多 workload 批量对比
- 多阵列配置设计空间搜索
- SRAM 宏精细热建模
- 封装级 / TSV / 2.5D / 3D-IC 扩展研究

---

## 2. 固定边界与约束

## 2.1 研究对象边界
本轮研究对象固定为：

- **Gemmini 阵列相关逻辑的标准单元级热仿真**
- 具体范围：  
  - PE array  
  - 控制逻辑  
  - 紧邻数据通路  
- **SRAM 宏不做精细热建模**
- scratchpad / accumulator 的存储阵列本体不作为本轮主要研究对象；Stage 2-4 默认将内存阵列 blackbox、exclude 或以上下文区域粗略处理，只保留其周边控制、地址、DMA、load/store、execute 近邻数据通路标准单元作为研究重点。

### 2.2 工作负载边界
本轮只允许一个 baseline：

- **一个持续高负载 output-stationary GEMM workload**

baseline workload 一经在 Phase 0 锁定，后续 Stage 1-4 不再反复修改 workload 定义；允许修改或重写旧脚本以正确构建、运行和采集该 baseline，但不得通过缩短矩阵规模或替换 workload 来控制仿真时间。

允许后续在同一基础设施上扩展，但本轮执行中**禁止提前增加第二个 workload**。

### 2.3 工艺与实现边界
本轮固定：

- **ASAP7**
- 仓库中已预配好 ASAP7 (reduced版) 相关环境
- Codex 必须在读取仓库现状后，将本文档中的占位内容替换为仓库内真实路径、真实命令、真实脚本名称

### 2.4 热仿真边界
本轮固定：

- **PACT 作为主线**
- **ATSim3D v1 作为必须执行的独立 steady thermal solver 对照**
- **HotSpot 作为粗粒度对照**
- 粒度要求：
  - 主输出：**grid 级**
  - 实例级只做必要统计：
    - top-N power instances
    - top-N toggle instances

### 2.5 性能/时序边界
本轮固定：

- **不需要追求 timing closure**
- **不做 RTL 优化**
- **不改 Gemmini 功能结构以提升性能**
- 目标是“在合理范围内跑通并获得可信热结果”，不是做 PPA 优化

---

## 3. Codex 执行总原则

## 3.1 先检查、后修改、再运行
Codex 每个阶段必须遵循：

1. 先检查环境与仓库现状
2. 再确认本阶段输入是否齐备
3. 再进行最小范围修改
4. 再运行本阶段命令
5. 再做验收
6. 再写阶段报告

## 3.2 禁止擅自扩大范围
Codex 禁止自行把任务扩展为：

- 全 SoC 实现
- 多 workload sweep
- 多参数 sweep
- 热优化
- 复杂封装扩展
- SRAM 宏精细建模
- 额外引入新的研究问题

## 3.3 缺失依赖处理规则
用户已说明大部分工具已安装。项目 Python 命令必须使用 conda 环境 `thermal_placement`；如 Stage 0-4 脚本、数据处理或可视化确实需要新增 Python 包，允许安装到该 conda 环境中，并在 active 环境/工具文档中记录包名、版本、用途和验证命令。该授权不扩展到系统包、EDA 工具、编译器、`tools/` 或 `third_party/` 工具载荷。  
如果执行过程中发现非 Python 缺失依赖，或 Python 依赖无法安全安装到 `thermal_placement`：

- **立即停止**
- 明确报告：
  - 缺什么
  - 缺在哪一步
  - 需要用户补什么
- **不得自行继续安装并推进，除非用户明确允许；已授权的 Python 包仅限安装到 `thermal_placement` conda 环境并记录**

## 3.4 修改原则
Codex 只能做：

- 为跑通阶段 0–4 所必需的最小修改
- 明确记录每个修改的原因
- 修改或重写不符合阶段目标的旧脚本，但只能服务于当前阶段和固定 baseline
- 本轮文档与脚本修改中，**不要使用 `apply_patch`**

不得做：

- 无关重构
- 风格化清理
- 超出当前阶段的脚本开发
- 提前实现未来阶段需要的复杂基础设施

## 3.5 计划回读规则
以下情况一旦发生，Codex 必须立即回到本文档重新阅读，并以本文档为准确认当前阶段目标、边界和禁止事项：

- 记忆丢失
- 上下文压缩
- 对当前计划存在不确定性
- 无法确认下一步是否仍在阶段 0–4 范围内

不得在未重新核对本文档的情况下，凭模糊记忆继续推进。

## 3.6 失败与计划变化的文档先行规则

当某次尝试失败，或下一步计划/路线发生变化时，Codex 必须先更新相关 active 文档，记录：

- 已尝试的命令或方案
- 失败现象和关键证据
- 当前判定
- 下一步计划

完成上述记录后，才能开始下一次尝试。该规则适用于 Stage 0-4 的所有开发、脚本、实验和流程迭代；Stage 2 route / memory 只是已经验证过最容易出问题的例子。不得让实际开发状态领先 active 文档。

## 3.7 Route 阶段监看与中止规则

OpenROAD route 阶段可能长时间无终端输出，尤其是 full-design `global_route` 和 congestion iteration。确认 route 正在运行后，Codex 应放宽监看间隔，避免频繁刷新；不得主动砍断、kill 或中止 route 阶段，除非用户明确要求停止，或进程自行退出/失败。若需要把长运行改判为失败或改变路线，必须先获得用户确认并按 3.6 更新文档。

---

## 4. 启动时必须先做的环境检查

> 以下内容为“框架要求”，命令需由 Codex 结合仓库现状补全或替换。

### 4.1 必查项
Codex 在第一次接手时必须先输出并记录：

- 当前工作目录
- 仓库根目录
- 当前分支
- `git status --short`
- 关键 remote
- Python 版本
- Verilator 版本
- OpenROAD / ORFS 版本或可执行位置
- OpenSTA 可执行位置
- PACT 可执行位置
- HotSpot 可执行位置
- ASAP7 相关路径是否可见
- 关键环境变量是否已设置

### 4.2 必读内容（由 Codex 根据仓库实际填写）
以下栏目必须在第一次接手时补全：

- 仓库内与 Gemmini 相关的主文档：
  - `docs/gemmini_flow_reference.md`
  - `docs/gemmini_workload_reference.md`
  - `docs/gemmini_thermal_environment_setup.md`
  - `docs/gemmini_thermal_issue_log.md`
- 仓库内与 ASAP7 flow 相关的主文档：
  - `docs/tool_environment_inventory.md`
  - `configs/reduced_techlibs/README.md`
  - `configs/openroad/reduced_platforms/`
- 仓库内已有的 workload / test / script：
  - `workloads/small_gemm/`
  - `workloads/thermal_smoke/`
  - `scripts/build_gemmini_workloads.sh`
  - `scripts/run_gemmini_workload.sh`
  - `scripts/run_gemmini_rtl_generation.sh`
  - `scripts/run_small_gemm_thermal_flow.sh`
  - `scripts/run_thermal_smoke_flow.sh`
- 仓库内已有的 PACT / HotSpot / thermal 脚本：
  - `scripts/extract_vcd_activity.py`
  - `scripts/export_smoke_hotspot_inputs.py`
  - `scripts/report_small_gemm_flow.py`
  - `docs/pact_slang_sv2v_yosys_slang_install_report.md`
- 仓库内已有的计划文档：
  - `docs/phase0tophase4_plan.md`
  - `docs/README.md`
  - `docs/archive/gemmini_thermal_validation_2026-04-23/`

> Codex 不得跳过“先读仓库现状”这一步。
> 以上文档不是一次性阅读清单；执行过程中应按需反复回读。

### 4.3 2026-04-23 首次接手检查记录

已完成的轻量检查：

- 当前工作目录：`/home/lisihang/thermal_placement`
- 仓库根目录：`/home/lisihang/thermal_placement`
- 当前分支：`master`
- `git status --short`：干净
- remote：`origin https://github.com/tingtong02/thermal_placement.git`
- conda 环境：`CONDA_DEFAULT_ENV=thermal_placement`
- Python：`/home/lisihang/miniconda3/envs/thermal_placement/bin/python`，版本 `3.11.15`
- Verilator：`tools/verilator/bin/verilator`，版本 `5.047 devel`
- OpenROAD：`tools/openroad-prebuilt/root/usr/bin/openroad`，版本 `v2.0-17598-ga008522d8`
- OpenSTA：`tools/opensta/bin/sta`，版本 `3.1.0`
- PACT：`$PACT_ENTRY=/home/lisihang/thermal_placement/third_party/PACT/src/PACT.py`
- HotSpot：`$HOTSPOT_HOME=/home/lisihang/thermal_placement/third_party/HotSpot`，`hotspot` 可执行
- ASAP7 reduced techlib：`scripts/check_edahub_reduced_techlibs.py asap7` 通过，含 5 个 Liberty、5 个 DB、2 个 LEF
- 全环境 smoke：`scripts/check_environment.sh` 通过

注意：`third_party/` 与 `tools/` 是本地忽略载荷；上述结果记录当前机器状态，不代表 fresh clone 自动具备同样工具。

---

## 5. 目录与产物规范

## 5.1 建议目录
以当前仓库状态为准，本轮阶段 0-4 使用以下 active 目录，不在 `archive/` 或 `docs/archive/` 下继续开发：

| 目录 | 用途 | 当前状态 |
| --- | --- | --- |
| `workloads/` | 本地 bare-metal workload 源码。已有 `small_gemm/` 与 `thermal_smoke/`；本轮 baseline 固定来自 `gemmini-rocc-tests/bareMetalC/tiled_matmul_os.c`，不新增第二 workload 或派生 workload。 | active |
| `sim/binaries/GemminiRocketConfig/` | Stage 1 workload ELF/bare-metal binary 输出。 | active，当前为空或仅保留新运行产物 |
| `sim/waves/GemminiRocketConfig/` | Stage 1 RTL VCD 输出。active route 默认并要求使用 VCD；不把 FST 作为后续开发主格式。 | active，重新生成，不复用归档波形 |
| `sim/logs/GemminiRocketConfig/` | Stage 1 仿真 stdout/stderr/log。 | active |
| `sim/activity/` | Stage 1 活动统计 CSV。 | active |
| `rtl_exports/generated-verilog/GemminiRocketConfig/` | Stage 1 重新导出的 Gemmini/Chipyard RTL 与 hierarchy JSON。 | active，缺失时重新生成 |
| `configs/gemmini/hierarchy_map.yaml` | Stage 1 活动聚合用层级映射。 | 当前 active 路径未生成；历史版本在 archive 中，仅作参考 |
| `physical/stage2_tiled_matmul_os_baseline_asap7/` | Stage 2 ASAP7 标准单元实现输出目录。 | Stage 2 创建 |
| `power/` 或 `thermal/power/` | Stage 3 grid power map、transient power trace、HotSpot `.ptrace`。 | Stage 3 创建或补齐 |
| `thermal/pact/stage4_tiled_matmul_os_baseline/` | Stage 4 PACT lcf/config/modelParams、steady/transient 输出。 | Stage 4 创建 |
| `thermal/hotspot/stage4_tiled_matmul_os_baseline/` | Stage 4 HotSpot 粗对照 `.flp/.ptrace/.ttrace`。 | Stage 4 创建 |
| `artifacts/stage1/` 到 `artifacts/stage4/` | 对外展示图、阶段性压缩摘要和必要拷贝。大 VCD 不强制复制到 `artifacts/`，可在报告中引用 `sim/waves/` 原路径。 | 按阶段创建 |
| `reports/` | 阶段报告、manifest、方法说明、验收结论。 | active |

归档目录只读参考：

- `archive/gemmini_thermal_validation_2026-04-23/`
- `docs/archive/gemmini_thermal_validation_2026-04-23/`

## 5.2 阶段产物命名原则
所有阶段产物必须包含：

- 阶段号
- workload 名
- 日期或版本号
- 是否为 baseline

示例形式：

- `stage1_tiled_matmul_os_baseline_rtl_trace_summary.md`
- `stage2_tiled_matmul_os_baseline_impl_manifest.md`
- `stage3_tiled_matmul_os_baseline_power_grid.csv`
- `stage4_tiled_matmul_os_baseline_pact_thermal_report.md`

---

## 6. 阶段 0：研究定义与基线建立

## 6.1 阶段目标
把本轮问题严格收缩为一个可执行、可验收的 baseline 计划。

## 6.2 阶段 0 允许的工作
- 读取仓库内容
- 整理 Gemmini 目标模块范围
- 确定一个 GEMM baseline
- 确定阶段 1–4 所需输入输出
- 生成正式阶段计划文档
- 生成 workload 选择说明
- 生成阶段验收标准

## 6.3 阶段 0 禁止的工作
- 运行大规模实验
- 修改 Gemmini RTL
- 启动后端完整实现
- 启动热仿真
- 提前写复杂自动化脚本

## 6.4 阶段 0 必须回答的问题
Codex 必须基于仓库现状明确写清：

1. Gemmini 目标模块边界如何落地
2. 这个 baseline GEMM 的来源是什么
3. workload 程序/测试从哪里来
4. 阶段 1 采哪些波形
5. 阶段 2 顶层综合对象是什么
6. 阶段 3 功耗波形如何从活动映射到 grid
7. 阶段 4 PACT / ATSim3D v1 / HotSpot 的输入格式如何生成

## 6.5 阶段 0 产出
阶段 0 正式计划初版直接维护在本文档中，包含以下三部分。

### 文档 A：阶段总计划

| 阶段 | 目标 | 输入 | 命令入口 / 实现入口 | 输出 | 验收标准 |
| --- | --- | --- | --- | --- | --- |
| Stage 0 | 锁定单一 sustained GEMM baseline、目标模块边界、Stage 1-4 输入输出和停止条件。 | `AGENTS.md`、本文档、`docs/README.md`、Gemmini/环境/ASAP7/PACT 参考文档、仓库当前状态。 | 文档编辑；轻量检查 `source tools/env_gemmini_thermal.sh`、`scripts/check_environment.sh`、`scripts/check_edahub_reduced_techlibs.py asap7`。 | 更新后的本文档。 | 单一 baseline、模块边界、各阶段 I/O、已知缺失项均写清。 |
| Stage 1 | 构建并运行唯一 baseline，导出 RTL 活动 VCD，选择冷启动/稳态/收尾窗口。Stage 1 可以使用完整 SoC 仿真作为活动来源，但研究对象仍只限 Gemmini PE array + 控制 + 周边 datapath。 | `GemminiRocketConfig`、baseline workload、Verilator debug simulator、`configs/gemmini/hierarchy_map.yaml`。 | `scripts/run_gemmini_rtl_generation.sh`、`scripts/build_gemmini_workloads.sh tiled_matmul_os`、`RUN_TAG=stage1_tiled_matmul_os_baseline_20260423 scripts/run_gemmini_workload.sh tiled_matmul_os`。老脚本可按需要小改或重写。 | VCD、仿真日志、activity CSV、window 报告。 | workload 功能完成；PE array/control/datapath 活动清晰；选出稳态高负载窗口。 |
| Stage 2 | 将 Gemmini 阵列相关逻辑落到 ASAP7 reduced 标准单元实现。 | Stage 1 目标模块边界、重新导出的 RTL、ASAP7 reduced techlib、ORFS。 | Stage 2 创建/补齐 ORFS design config 后运行 `make -C "$FLOW_HOME" PLATFORM_HOME="$TP_ROOT/configs/openroad/reduced_platforms" DESIGN_CONFIG=<stage2_config.mk> synth floorplan place route`。 | netlist、DEF、SPEF、SDF、实例坐标、面积/时序报告。 | 输出非空可读；目标未扩展为全 SoC；timing 可报告但不优化。 |
| Stage 3 | 将 Stage 1 活动窗口和 Stage 2 物理实现映射成 grid 级功耗波形。 | RTL/gate activity、netlist、DEF、SPEF/SDF、Liberty、实例坐标。 | Stage 3 补齐 `scripts/build_stage3_power_grid.py` 或等价最小脚本；OpenSTA 用于读 Liberty/netlist/SPEF/SDF 并生成功耗/时序摘要。 | grid power CSV、transient power trace、Top-N power/toggle 报告。 | grid 连续完整；功耗高峰与 Stage 1 稳态窗口一致；PE array 邻近区域占主要热点。 |
| Stage 4 | 用 PACT 主线、ATSim3D v1 独立 steady solver 和 HotSpot 粗对照生成热图、曲线、热点统计。 | Stage 3 grid power、geometry/material assumptions、PACT/ATSim3D v1/HotSpot 模板。 | `python "$PACT_ENTRY" <lcf.csv> <config> <modelParams> --gridSteadyFile <out>`；`scripts/run_atsim3d.sh --lcfFile <lcf> --ConfigFile <config> --SimParamsFile <simparams>`；HotSpot `hotspot -c <config> -f <flp> -p <ptrace> -o <ttrace>`。 | PACT steady/transient、ATSim3D v1 `.res` 与 physical-grid 对比、HotSpot 对照、图表、阶段总结。 | PACT steady/transient 成功；ATSim3D v1 steady 成功并生成 `.res`；HotSpot 粗对照成功；报告解释热点位置和趋势差异。 |

主要风险点：

- `tiled_matmul_os` 运行和波形规模可能较大，但不得为了控制仿真时间而缩短或替换 baseline；active Stage 1 默认使用 VCD，优先通过 Verilator 线程、解析脚本优化、压缩存储或后处理脚本来管理成本，不把 FST 作为后续开发主格式。Verilator 仿真线程上限开放到 `128`，但默认线程数必须按当前机器、当前 workload 和当前 tracing 形式的实测结果选择，不能机械固定为吃满核心；当前官方 `mvin_mvout` VCD smoke 的已完成 run 中 `VERILATOR_THREADS=16` 最优。VCD parser 现已在主仓库中实现可选并行解析，`scripts/run_gemmini_workload.sh` 通过 `VCD_PARSER_WORKERS` 暴露线程数，上限同样为 `128`；默认仍为 `1`，后续开发必须按实际文件和机器实测选择。
- active `configs/gemmini/hierarchy_map.yaml` 当前未生成，Stage 1 必须重新生成，不直接复用 archive。
- Stage 2 目标不是完整 SoC；如果无法稳定抽取 Gemmini 阵列相关 synthesizable top，应停止报告，而不是转向全 SoC 实现。
- ASAP7 是 reduced techlib，不是 signoff PDK；后续结论只用于研究闭环和热画像，不声明 signoff 精度。
- Stage 3 当前缺少最终 grid power 构建脚本，需在 Stage 3 做最小实现。

阶段停止条件继承第 12 节；额外要求是：任何会引入第二个 workload、热优化、RTL 优化或完整 SoC 实现的动作都必须先停下并请求用户确认。

### 文档 B：baseline workload 说明

本轮唯一 baseline 定义为：

- baseline 名称：`tiled_matmul_os_baseline`
- workload 类型：持续高负载 output-stationary tiled GEMM
- 固定来源：`third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/tiled_matmul_os.c`
- 构建入口：`scripts/build_gemmini_workloads.sh tiled_matmul_os`
- 运行入口：`RUN_TAG=stage1_tiled_matmul_os_baseline_20260423 scripts/run_gemmini_workload.sh tiled_matmul_os`
- 设计规模：bare-metal 路径中 `MAT_DIM_I/K/J=64`，Gemmini 当前 `DIM=16`，预期会触发多 tile GEMM，比本地 `small_gemm` 的单个 `16 x 16 x 16` GEMM 更接近持续阵列高负载。
- 当前 Stage 1 配置不是 Gemmini-only 顶层，而是完整 `GemminiRocketConfig` SoC/TestHarness：`DefaultGemminiConfig + WithNHugeCores(1) + WithSystemBusWidth(128) + AbstractConfig`；因此 Stage 1 VCD 会包含完整 SoC 上下文，后续必须靠 hierarchy map 和模块边界聚焦 Gemmini 阵列相关逻辑。
- 研究边界约束：完整 SoC 仅作为 Stage 1 产生真实 Gemmini 活动的仿真载体，不改变研究对象；Stage 2-4 的实现、功耗和热分析目标仍固定为 `Gemmini`、`MeshWithDelays`、`Mesh`、`PE`、`ExecuteController`、`LoadController`、`StoreController` 及其周边 datapath，不转向全 SoC 物理实现。
- workload 计算内容：官方程序先在 CPU 上执行 `full_matmul()` 生成 golden，再调用 `tiled_matmul_auto(MAT_DIM_I, MAT_DIM_J, MAT_DIM_K, ..., OS)` 在 Gemmini 上执行 output-stationary tiled GEMM，并做结果比对；bare-metal 设置下 `MAT_DIM_I/K/J=64`、`NO_BIAS=1`、`CHECK_RESULT=1`。
- 数值语义：该 baseline 对应 `C = A x B + D` 的矩阵乘路径，其中当前 bare-metal 配置里 `D` 被置零，`A/B` 为 `elem_t=int8_t`，累加路径使用 `acc_t=int32_t`。
- 辅助 smoke workload：`mvin_mvout` 属于 Gemmini 官方基础搬运/读写测试，不是 GEMM baseline，只用于验证 simulator/trace/parser 成本，不参与后续 Stage 1-4 研究结论。
- 当前 Gemmini 硬件参数快照：`tileRows=1`、`tileColumns=1`、`meshRows=16`、`meshColumns=16`、软件头文件 `DIM=16`、`elem_t=int8_t`、`acc_t=int32_t`、`sp_capacity=256 KiB`、`acc_capacity=64 KiB`、`sp_banks=4`、`acc_banks=2`、`dma_maxbytes=64`、`dma_buswidth=128`；硬件默认支持 `Dataflow.BOTH`，但本轮固定 workload 使用 `tiled_matmul_auto(..., OS)`，即 output-stationary。
- 固定规则：后续 Stage 1-4 不再反复修改 workload 定义，不通过缩短矩阵规模、替换 workload 或增加第二 workload 控制仿真时间；如旧脚本不能满足构建、运行、run tag、波形格式或产物路径要求，可直接修改或重写脚本。

选择理由：

- `thermal_smoke` 只验证工具链，不触发 Gemmini GEMM。
- `small_gemm` 已历史验证可跑，但仅 `16 x 16 x 16`，更适合 smoke/下界参考，不足以默认代表持续高负载。
- `tiled_matmul_os` 使用 Gemmini 官方测试路径，矩阵规模更大，能够合理预期产生 PE array、execute controller、load/store datapath 的持续活动。

预期热行为：

- 稳态窗口中 PE array 及其邻近 execute datapath 维持较高 toggle / power。
- load/store 控制和 scratchpad/accumulator 周边逻辑在 mvin/mvout 与 tile 间切换阶段形成次级热点。
- scratchpad/accumulator 存储阵列本体不作为细粒度标准单元热建模对象；其粗略上下文可在 Stage 4 HotSpot 对照中作为 `scratchpad_accumulator_context` 聚合块记录。
- Stage 1 必须用实际 RTL 波形验证这一预期；如果实际活动不满足“持续高负载”，停止并回到 Phase 0 重新确认 baseline 定义，而不是自行更换 workload。

### 文档 C：仓库现状清点

已确认可复用路径：

- 环境入口：`tools/env_gemmini_thermal.sh`，已确认激活 conda 环境 `thermal_placement`，Python 为 `/home/lisihang/miniconda3/envs/thermal_placement/bin/python`。
- Gemmini RTL 生成：`scripts/run_gemmini_rtl_generation.sh`。
- Gemmini hierarchy 清点：`scripts/inspect_gemmini_hierarchy.py`。
- workload 构建：`scripts/build_gemmini_workloads.sh`、`scripts/build_small_gemm_binary.sh`。
- workload 运行：`scripts/run_gemmini_workload.sh`、`scripts/run_small_gemm_thermal_flow.sh`。
- 活动提取：`scripts/extract_vcd_activity.py`。
- HotSpot 最小输入导出参考：`scripts/export_smoke_hotspot_inputs.py`。
- ASAP7 reduced techlib：`configs/reduced_techlibs/asap7.mk`、`configs/reduced_techlibs/asap7.tcl`。
- ORFS ASAP7 overlay：`configs/openroad/reduced_platforms/asap7/`。
- PACT 入口：`python "$PACT_ENTRY"`，实际路径由环境变量指向 `third_party/PACT/src/PACT.py`。
- HotSpot 入口：`hotspot`，路径由 `HOTSPOT_HOME` 接入。

当前缺失或待生成项：

- active `configs/gemmini/hierarchy_map.yaml` 未生成；Stage 1 必须重新运行 RTL generation。
- Stage 2 的 Gemmini 相关 top wrapper、ORFS design config、SDC 尚未创建。
- Stage 3 的 final grid power 构建脚本尚未创建。
- Stage 4 的 PACT lcf/config/modelParams、ATSim3D v1 LCF/config/simparams/floorplan/power 与 HotSpot 粗对照输入尚未创建。
- 当前 archive 中存在旧 RTL、activity、thermal 结果，但不能作为当前主线验收结果。

上述 Stage 2-4 条目属于计划内待创建输入，不构成 Phase 0 阻塞；真正阻塞条件是：无法重新生成 active RTL/hierarchy、无法构建或运行固定 baseline、无法识别 Gemmini 阵列相关目标边界、或 ASAP7/PACT/ATSim3D v1/HotSpot 基础工具不可用。

## 6.6 阶段 0 测试
阶段 0 的测试不是程序测试，而是**定义完整性测试**：

- 目标范围是否已经收缩为单一 baseline
- 是否明确不做 SRAM 宏精细热建模
- 是否明确采用 ASAP7
- 是否明确 PACT 主线 + ATSim3D v1 独立 steady 对照 + HotSpot 粗对照
- 是否明确 grid 级输出为主
- 是否明确不做 timing 优化

## 6.7 阶段 0 验收标准
满足以下条件才允许进入阶段 1：

- 已生成正式计划文档
- 已锁定唯一 baseline workload
- 已锁定目标模块边界
- 已锁定阶段 1–4 的输入输出与验收标准
- 仓库现状中的阻塞项与计划内待创建项已区分；若存在真正阻塞项，必须显式列出并停止

---

## 7. 阶段 1：RTL 活动波形获取

## 7.1 阶段目标
在 **单一 GEMM baseline** 下，拿到代表性 RTL 活动波形，并确定后续门级分析用的关键时间窗。

## 7.2 阶段 1 允许的工作
- 编译并运行 baseline workload
- 使用 Verilator 或仓库内现有仿真入口
- 导出 RTL VCD
- 浏览关键层次波形
- 提取代表性时间窗
- 统计高活动模块

## 7.3 阶段 1 禁止的工作
- 添加第二个 workload
- 做参数 sweep
- 修改 Gemmini 结构
- 进入后端阶段
- 进入热仿真阶段

## 7.4 阶段 1 必须检查的内容
Codex 必须在仓库中明确：

- workload 运行入口：`source tools/env_gemmini_thermal.sh && scripts/build_gemmini_workloads.sh tiled_matmul_os && RUN_TAG=stage1_tiled_matmul_os_baseline_20260423 scripts/run_gemmini_workload.sh tiled_matmul_os`
- waveform 生成方式：`scripts/run_gemmini_workload.sh` 通过 Verilator debug simulator 的 `run-binary-debug` 导出 VCD；active flow 默认并要求使用 VCD，不通过切换到 FST 回避后续开发问题；Verilator 仿真线程上限开放到 `128`，但后续开发必须按机器实际情况和实测 walltime 选择线程数，不能默认写死为最大核心数；当前官方 `mvin_mvout` VCD smoke 的已完成 run 中 `16` 线程优于 `32/64/128`。若 VCD 过大，优先重新评估线程数、压缩存储、分段采集或重写后处理脚本，但不得通过缩短 workload 来控制仿真时间。
- VCD 解析方式：当前正式 parser `scripts/extract_vcd_activity.py` 已在主仓库中实现可选并行解析，方法是 header 预解析、body 分块和边界状态合并；默认 `--workers=1`，`scripts/run_gemmini_workload.sh` 通过 `VCD_PARSER_WORKERS` 透传该参数。VCD parser worker 上限开放到 `128`，但后续开发必须按实际文件和机器实测选择线程数，不能固定吃满线程；本轮对 `sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t16.vcd` 的实测结果为：`1 worker=210.65s`、`32 workers=10.77s`、`64 workers=7.28s`、`128 workers=6.34s`，且输出 CSV 经 `cmp` 完全一致。
- 关键模块层次路径：先运行 `scripts/run_gemmini_rtl_generation.sh` 重新生成 `rtl_exports/generated-verilog/GemminiRocketConfig/`、`configs/gemmini/hierarchy_map.yaml` 与 `reports/notes/gemmini_module_inventory.md`；重点模块包括 `Gemmini.sv`、`Mesh.sv`、`MeshWithDelays.sv`、`PE.sv`/`PE_256.sv`、`ExecuteController.sv`、`LoadController.sv`、`StoreController.sv`、`Scratchpad*.sv`、`Accumulator*.sv`。
- 关键信号或关键 busy/valid/ready/fsm：优先观察 mesh/PE `valid`/control/data 通路、execute controller command/preload/compute 相关 valid-ready、load/store controller request/response valid-ready、DMA/stream reader-writer 活动、`gemmini_fence` 前后的阵列忙闲切换；具体层次名以重新生成的 hierarchy map 和 VCD scope 为准。
- 时间窗精度规则：Stage 1 可以继续使用完整 `GemminiRocketConfig` SoC/TestHarness 作为真实软件执行和 RoCC/TL 上下文的活动来源；不要把研究对象扩大为完整 SoC。当前 `reports/stage1_tiled_matmul_os_baseline_windows.md` 中的 `steady_high_load` 是基于 marker 和全 trace 聚合的粗窗口。进入 Stage 3 前必须对 Gemmini 目标层次重新精化时间窗，至少用 Gemmini scope 下的 valid/ready/busy/toggle 密度确认 accelerator-active 子窗口；不得直接用全程序或 CPU reference 主导的平均 toggle 作为 grid power 输入。
- Gemmini-only 仿真规则：除非显式新增并验证一个能独立驱动 RoCC/DMA/memory 协议的 Gemmini test harness，否则 Stage 1 不切换到 Gemmini-only RTL 仿真。直接只仿 `Gemmini` 会丢失 CPU 发指令、TL/DMA、cache/memory backpressure、TLB/fence 等真实上下文，活动代表性不足；若未来确实建立 Gemmini-only harness，必须作为计划变更记录其驱动模型、内存模型和与 full-SoC baseline 的等价性检查。
- 时间窗精化实现要求：后续不重跑 Gemmini-only DUT；复用 full-SoC VCD、simulator log marker、hierarchy map 和现有 signal activity。若当前 `steady_high_load` 仍为 coarse marker window，Stage 3 前必须创建最小 windowed/scoped extractor 或等价脚本，只扫描 candidate tail interval 中 Gemmini 目标 scope，输出 `reports/stage1_tiled_matmul_os_baseline_target_windows.md` 和 `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`。报告至少记录 candidate interval、最终 accelerator-active start/end、PE/controller/load-store/spad-near toggle 密度、active duty factor、阈值/选择规则和未覆盖信号比例。若该报告不存在，Stage 3 不得把全程序平均 activity 当作正式 power 输入。

## 7.5 阶段 1 推荐观察对象
至少覆盖：

- PE array 活动相关层次
- 控制逻辑关键状态
- 紧邻数据通路
- load/execute/writeback 相关活动窗口
- 阵列忙闲切换

## 7.6 阶段 1 产出
必须形成：

### 产物 A：RTL 波形
- `artifacts/stage1/<...>.vcd`

### 产物 B：时间窗说明
- `reports/stage1_tiled_matmul_os_baseline_windows.md`

内容必须包含：
- 冷启动窗口
- 稳态高负载窗口
- 收尾窗口
- 窗口精度状态：标明是 coarse marker window 还是已经按 Gemmini 目标层次精化；若仍为 coarse，必须写明 Stage 3 前的精化要求

### 产物 C：活动摘要
- `reports/stage1_tiled_matmul_os_baseline_activity_summary.md`

内容至少包含：
- 总周期
- 高活动区间
- top 活跃层次
- 对后续门级分析最有价值的窗口

### 产物 D：目标层次窗口精化报告
- `reports/stage1_tiled_matmul_os_baseline_target_windows.md`
- `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`

该产物可在 Stage 1 后补，也可作为 Stage 3 前置步骤补齐；只要当前窗口仍是 coarse marker window，Stage 3 构建正式 grid power 前必须先补齐该产物。

## 7.7 阶段 1 测试
### 功能正确性
- baseline workload 正确完成
- 输出结果符合预期或现有测试标准

### 波形可用性
- VCD 能打开
- 关键层次能观测
- 稳态高负载区间清晰可定位

### 活动合理性
- PE array 相关区应在稳态阶段高活跃
- 活动应与“持续高负载 GEMM”预期一致

## 7.8 阶段 1 验收标准
满足以下条件才允许进入阶段 2：

- 成功拿到 RTL VCD
- 已定义后续门级分析的关键时间窗
- 已确认 baseline 的热行为确实偏“持续高负载”
- 已输出活动摘要报告

---

## 8. 阶段 2：ASAP7 标准单元实现

## 8.1 阶段目标
将目标模块落到 ASAP7 标准单元实现，导出后续阶段必须使用的实现与寄生文件。

## 8.2 阶段 2 允许的工作
- 确定综合/后端顶层
- 绑定 ASAP7
- 跑综合与基本后端流程
- 导出 netlist / DEF / SPEF / SDF
- 导出实例坐标信息
- 记录 timing 结果，但不要求优化

## 8.3 阶段 2 禁止的工作
- 为 timing 优化 RTL
- 修改 Gemmini 架构
- 做 placement/floorplan 热优化
- 引入多个实现版本对比

## 8.4 阶段 2 必须明确的内容
Codex 必须填写：

- 顶层对象：Gemmini 阵列相关标准单元实现 top，Stage 2 优先从重新导出的 `Gemmini`/compute-datapath 相关 RTL 中建立最小 synthesizable wrapper，覆盖 PE array、execute/control、load/store 近邻 datapath；不得退化为完整 `TestHarness` 或完整 SoC。
- 内存处理规则：scratchpad/accumulator 的 SRAM array 或推断大存储阵列不是主要研究重点，默认 blackbox、exclude 或以边界 stub 加物理/热上下文粗略处理；Stage 2 只保留其周边控制、地址、DMA、load/store 和 execute 近邻标准单元。当前 Phase 2 内存路线状态为：`PIN_THICKNESS=0.096` 的 generated memory macro LEF full-design route 已完成验证，memory `pin_access` 通过；Attempt 1 使用 `PLACE_PINS_ARGS='-min_distance 0.54'` 后 `global_route` congestion 已解除并生成 `5_1_grt.odb`；随后从已有 `5_1_grt.odb` 重新进入 `5_2_route detail_route`，并以 `DETAILED_ROUTE_END_ITERATION=8` 跑完 route，生成 `5_2_route.odb`、`5_3_fillcell.odb` 和 `5_route.odb`。`memory_boundary_stub + obstruction/thermal context` 仍只是可选后备方案，尚未开始；暂时不得自动进入 C 方案，也不得尝试纯 `FLOW_VARIANT=mem_boundary_stub`（无 obstruction/thermal context），除非用户再次明确更改计划。若综合工具把大存储阵列展开为大量标准单元且主导面积/功耗，必须停止并调整 blackbox/stub/context 策略。
- 当前 route 结果：在不进入 C 方案、不恢复高精度全量设置的前提下，已从已有 `5_1_grt.odb` 重新进入 `5_2_route detail_route`，并用 `DETAILED_ROUTE_END_ITERATION=8` 跑完 route，生成 `5_2_route.odb`、`5_3_fillcell.odb` 和 `5_route.odb`。8 轮后仍有 6988 个 detailed-route residual violations，因此该结果只能作为 Phase 2 routed proxy / non-signoff 输入；后续 finish/export 已生成 final DEF、netlist、SDC、SPEF、GDS 和报告，但无 SDF。
- Current finish/export status: `make ... finish` completed after a second no-clean run. Final proxy outputs exist and are non-empty: `6_final.odb`, `6_final.def`, `6_final.v`, `6_final.sdc`, `6_final.spef`, and `6_final.gds`. No SDF was generated; Stage 3 must use SDC+SPEF+routed netlist as the available proxy timing/parasitic package and record the SDF gap. The first `6_report` attempt left a GUI image-save error in `6_report.log` (`get_scenes` unsupported), but core final exports were written and the second finish run completed remaining SDC/GDS targets.
- top 选择流程：先用 Stage 1 重新生成的 hierarchy map 和 RTL module inventory 确认 `Gemmini`、`MeshWithDelays`、`Mesh`、`PE`、`ExecuteController`、`LoadController`、`StoreController` 依赖关系；再选择最小可综合 wrapper；如果无法在阵列相关范围内形成可综合 top，停止报告，不转向完整 SoC。
- ORFS / OpenROAD 入口：`make -j "$MAKE_JOBS" -C "$FLOW_HOME" PLATFORM_HOME="$TP_ROOT/configs/openroad/reduced_platforms" DESIGN_CONFIG="$TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/config.mk" YOSYS_EXE="$YOSYS_EXE" OPENROAD_EXE="$OPENROAD_EXE" OPENSTA_EXE="$OPENSTA_EXE" NUM_CORES="$NUM_CORES" synth floorplan place route`；推荐仓库脚本入口为 `scripts/run_stage2_openroad.sh`；`config.mk` 与必要 wrapper/SDC 在 Stage 2 创建。
- ASAP7 配置路径：`configs/reduced_techlibs/asap7.mk`、`configs/reduced_techlibs/asap7.tcl`、`configs/openroad/reduced_platforms/asap7/config.mk`。
- 输出目录：`physical/stage2_tiled_matmul_os_baseline_asap7/`，报告写入 `reports/stage2_tiled_matmul_os_baseline_impl_manifest.md` 与 `reports/stage2_tiled_matmul_os_baseline_impl_summary.md`。
- 初始 timing 目标：Stage 2 先以 `500 MHz` 为记录目标，对应 `2.000 ns` 时钟周期；记录 timing 结果，但当前阶段不要求为达标而修改 RTL 或做额外优化实验。
- 多线程规则：在 ORFS/后端语境中，`MAKE_JOBS` 表示外层并发的独立任务数量，不是单个 OpenROAD 调用的内部线程数。单个主线 baseline 默认 `MAKE_JOBS=1`，这是为了保持依赖执行确定、避免本地 ORFS 多输出规则触发重复综合；它不是表示只能使用一个 CPU 核。单任务 P&R 加速使用 `NUM_CORES`，正常单一任务下 `NUM_CORES` 上限为 `128`。
- 外层并发资源规则：只有多个独立 flow / 独立 block / 独立 `FLOW_VARIANT` 才允许提高 `MAKE_JOBS`，且 `MAKE_JOBS` 最大为 `4`。当 `MAKE_JOBS=2` 时，每个任务的 `NUM_CORES` 最多为 `128`；当 `MAKE_JOBS=3` 或 `4` 时，每个任务的 `NUM_CORES` 最多为 `64`。所有并发任务必须使用唯一输出目录或唯一 `FLOW_VARIANT`，并在 manifest 中记录总核数预算、内存/IO 假设和实际命令。
- 流程加速规则：`NUM_CORES` 只控制单次 OpenROAD 调用内部的 `-threads`；`make -j` 或后台并发主要用于多个独立配置的外层并行。对单个主线 baseline，优先采用分阶段运行（先 `synth`，再 `floorplan/place/route`），避免每次从 `all` 重跑；若综合耗时过长，优先缩小 top scope、收紧 filelist、保持 hierarchical synthesis 和最小 Gemmini wrapper，而不是先做大规模参数 sweep。
- 精度规则：除调试工具调用或一次性 smoke 排障外，正式 Stage 2 默认 config 不允许保留 `-noshare`、`SKIP_LAST_GASP` 或其他明确降低综合/布局布线质量的参数。`noaddermap`、`REMOVE_ABC_BUFFERS=1`、`GPL_TIMING_DRIVEN=0`、`SKIP_CTS_REPAIR_TIMING=1`、`SKIP_REPORT_METRICS=1` 等只能作为 bring-up/proxy variant 使用；若用于 Stage 3/4，报告必须标注为 thermal-flow prototype，不能描述为 signoff-quality P&R。正式质量路线应逐项恢复 timing-driven placement、CTS timing repair、metrics/report、默认 adder mapping 或等价可解释替代，并比较面积/单元数/层次保真度变化。
- Stage 2 fidelity 恢复规则：当前轮次优先目标是跑通 Stage 0-4 热仿真闭环，不强制在 Phase 2 立即恢复 strict P&R fidelity。当前 `noaddermap`/bring-up route 若生成 `5_route.odb`、routed DEF/SPEF/SDF，应先记录为 `proxy` 或 `strict candidate`；若仍保留 `noaddermap`、`REMOVE_ABC_BUFFERS=1`、`GPL_TIMING_DRIVEN=0`、`SKIP_CTS_REPAIR_TIMING=1`、`SKIP_REPORT_METRICS=1` 等设置，必须标注为 thermal-flow prototype / non-signoff，不得称为 strict signoff。高精度恢复改为 optional future work：未来若需要 strict Stage 2，再按最小增量逐项恢复 reports/metrics、CTS timing repair、timing-driven placement、默认 adder mapping 或等价可解释替代，并比较 route 完成情况、实例数/面积/关键模块层次/坐标分布/timing report。

## 8.5 阶段 2 最低成功标准
严格 Stage 2 成功标准必须成功拿到：

- gate-level netlist
- DEF
- SPEF
- SDF
- 实例坐标或可导出实例位置的信息
- 面积/单元统计
- timing 报告（仅记录，不优化）

当前 2026-04-26 Phase 2 只按 `proxy / non-signoff` 验收：已拿到 gate netlist、DEF、SDC、SPEF、GDS、ODB、实例位置和面积/单元统计；未生成 SDF。该无 SDF 状态不满足 strict Stage 2，但在用户确认的 thermal-flow prototype 目标下可作为 Stage 3 preflight 输入，必须在 Stage 3 方法报告中继续标注。

## 8.6 阶段 2 产出
### 产物 A：实现清单
- `reports/stage2_tiled_matmul_os_baseline_impl_manifest.md`

必须列出：
- 顶层
- 工艺库
- 关键脚本
- 输出文件路径

### 产物 B：后端输出
- netlist
- DEF
- SPEF
- SDF（strict 要求；当前 proxy 结果未生成，已记录为 caveat）

### 产物 C：实现摘要
- `reports/stage2_tiled_matmul_os_baseline_impl_summary.md`

内容至少包括：
- 单元数量
- 面积
- util
- 关键 warning
- timing 摘要
- 是否存在阻塞性实现问题

## 8.7 阶段 2 测试
### 流程测试
- 综合成功
- placement / routing 成功
- 输出文件存在且非空

### 数据可用性测试
- 网表可被后续工具读取
- SPEF 可用；SDF 若不可用，必须记录替代输入组合和精度限制
- 实例物理信息可用于阶段 3 grid 映射

### 合理性测试
- 设计规模合理
- 目标模块已被纳入实现对象
- 未意外扩展为全 SoC

## 8.8 阶段 2 验收标准
满足以下条件才允许进入阶段 3：

- 已得到完整的后端关键文件
- 已确认 ASAP7 流程跑通
- 已能把实例与物理位置关联起来
- timing 虽可不优，但结果必须可读、可报告
- 已明确 Stage 2 验收等级：`strict` 或 `proxy`

`strict` Stage 2 验收要求 routed 输出完整，并且没有未解释的 debug-only 降质 knob；若使用 `noaddermap` 或其他替代设置，必须有原因、影响和对面积/层次/可路由性的比较记录。`proxy` Stage 2 只允许作为 Stage 3/4 热流程原型输入，必须保留 caveat，不能作为最终物理实现质量结论。只要后续要做正式功耗/热结论、跨实现比较或未来热优化反馈，必须优先解除 proxy 限制并重跑对应 Stage 2 变体。

---

## 9. 阶段 3：grid 级功耗波形构建

## 9.1 阶段目标
将阶段 1 的活动时间窗与阶段 2 的后端实现结合，构建 **grid 级 transient power trace**，并辅以实例级 Top-N 统计。

## 9.2 阶段 3 允许的工作
- 门级仿真或活动提取
- 读取 VCD / SAIF / SDF / SPEF / Liberty
- 构建 grid 映射
- 导出 steady power map
- 导出 transient power trace
- 输出 top-N power / toggle instances

## 9.3 阶段 3 禁止的工作
- 全长程序无必要全时段门级分析
- 多 workload 同时分析
- 热仿真优化
- RTL 改动

## 9.4 阶段 3 固定策略
本轮必须采用：

- RTL VCD 用于**选时间窗**，且当前 `steady_high_load` 仍是 coarse marker window，正式功耗前必须做 Gemmini target-scoped refinement。
- 门级/功耗活动只对**关键时间窗**做重点提取，禁止把 CPU gold reference 主导的全程序平均 activity 当正式 grid power 输入。
- Stage 2 输入使用当前 Phase 2 `proxy / non-signoff` 包：`6_final.def + 6_final.v + 6_final.sdc + 6_final.spef`，无 SDF 状态必须记录。
- 主输出采用 **grid 级**。
- 实例级只做：
  - top-N power instances
  - top-N toggle instances
- 每次 Stage 3 脚本、映射策略、窗口选择、功耗模型或重试路线变化前，必须先更新 active 文档或 Stage 3 方法报告，记录失败证据、当前判定和下一步计划。

## 9.5 阶段 3 正式执行步骤
Stage 3 按以下顺序实施；除非用户确认，不跳步、不引入第二 workload、不启动热优化：

1. **Stage 3 preflight manifest**：读取并记录 Stage 1/2 输入状态，确认 `reports/stage3_tiled_matmul_os_baseline_preflight_plan.md`、Stage 2 proxy caveats、无 SDF、残留 DRC、memory blackbox/proxy 边界和 `6_report.json` 实际位置。若任一关键输入缺失，停止并更新文档。
2. **目标窗口精化**：复用完整 full-SoC Stage 1 VCD，不重跑 Gemmini-only DUT；实现最小 windowed/scoped extractor 或等价方法，只扫描 candidate tail interval 中 Gemmini 目标 scope，输出 `reports/stage1_tiled_matmul_os_baseline_target_windows.md` 和 `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`。
3. **activity mapping manifest**：生成 `reports/stage3_tiled_matmul_os_baseline_activity_mapping_manifest.md`，记录 RTL scope prefix、Stage 2 gate/module prefix、Yosys hierarchy/keep_hierarchy 状态、blackbox/stub 边界、可匹配比例和 fallback 比例。
4. **DEF/netlist physical inventory**：解析 `6_final.def` 和 `6_final.v`，确认 die/core bbox、component count、macro/blackbox 实例、目标模块实例名前缀和可用于 grid 的实例坐标；输出 instance/grid 前的轻量 sanity 摘要。
5. **grid 与 instance-to-grid map**：以 Stage 2 DEF die/core bbox 为几何范围，初始采用 `64 x 64` grid；若数据量或 PACT 成本不合适，可在方法报告中改为 `40 x 40` 或 `32 x 32`，但必须保持全芯片 grid 连续覆盖。输出 `power/stage3_tiled_matmul_os_baseline_instance_grid_map.csv`。
6. **power sanity / proxy model selection**：优先用 OpenSTA 读取 ASAP7 Liberty、`6_final.v`、`6_final.sdc`、`6_final.spef` 做 timing/power sanity。若 OpenSTA/SAIF 直接功耗链路失败，先更新方法报告，再采用可复现的 toggle-to-liberty/area/cell proxy；不得使用 `6_report.log` / `6_report.json` 的 VDD/VSS IR 数值作为功耗或热输入。
7. **grid power trace build**：生成 `power/stage3_tiled_matmul_os_baseline_grid_power.csv` 和 `power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv`；功耗统一 W，时间统一 ps，时间轴连续，grid bin 完整。
8. **Top-N 与反查报告**：输出 `reports/stage3_tiled_matmul_os_baseline_top_power_instances.md`、`reports/stage3_tiled_matmul_os_baseline_top_toggle_instances.md`、`power/stage3_tiled_matmul_os_baseline_region_power_summary.csv`、`reports/stage3_tiled_matmul_os_baseline_hotspot_traceback.md`。
9. **Stage 3 方法和验收报告**：输出 `reports/stage3_tiled_matmul_os_baseline_power_trace_method.md` 和阶段报告，明确窗口来源、grid 大小、映射规则、fallback 比例、proxy 限制、验证结果和 Stage 4 输入是否就绪。

## 9.6 阶段 3 必须明确的内容
Codex 必须写清：

- 门级活动入口：Stage 3 使用 Stage 1 选定并精化后的 VCD/SAIF 活动与 Stage 2 gate netlist 对齐；最终入口脚本在 Stage 3 补齐为 `scripts/build_stage3_power_grid.py` 或同等最小脚本，禁止分析第二个 workload。
- RTL-to-gate/physical 映射规则：Stage 3 必须先生成 activity mapping manifest。优先利用 Stage 2 hierarchical netlist 中保留的 `Gemmini.ex_controller...`、`spad...`、`load_controller...`、`store_controller...` 等实例路径做模块级/实例级前缀匹配；不能匹配到单个 gate 的 RTL toggle 必须聚合到最近可解释模块或 grid region，并在方法报告中列出 fallback 比例。
- OpenSTA 使用方式：读取 ASAP7 Liberty、Stage 2 gate netlist、SPEF/SDC，生成 timing 与 power sanity 摘要；当前 Phase 2 proxy 未生成 SDF，因此 Stage 3 使用 `6_final.v + 6_final.def + 6_final.sdc + 6_final.spef` 作为输入组合，并在方法报告中说明无 SDF 精度限制。
- grid 划分方案：以 Stage 2 DEF die/core bbox 为几何范围，初始采用 `64 x 64` grid；若设计面积或 PACT 运行成本不合适，可在 Stage 3 报告中改为 `40 x 40` 或 `32 x 32`，但必须保持全芯片 grid 连续覆盖。
- 实例到 grid 的映射脚本：Stage 3 创建最小 DEF/netlist/功耗聚合脚本，将实例中心点或 bbox 面积分摊到 grid bin；脚本输出路径记录在 `reports/stage3_tiled_matmul_os_baseline_power_trace_method.md`。
- 输出格式：`power/stage3_tiled_matmul_os_baseline_grid_power.csv` 含 `time_index,time_ps,grid_x,grid_y,power_w`；`power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv` 含连续时间轴和 grid power；Top-N 报告写入 `reports/stage3_tiled_matmul_os_baseline_top_power_instances.md` 与 `reports/stage3_tiled_matmul_os_baseline_top_toggle_instances.md`。
- 单位与 fallback：功耗统一用 W，时间统一用 ps；如果 OpenSTA/SAIF 直接功耗链路失败，Stage 3 可使用基于 Stage 1 target-window toggle、ASAP7 Liberty cell/internal/switching power 和 Stage 2 实例面积/坐标的可复现 proxy，但必须在 `reports/stage3_tiled_matmul_os_baseline_power_trace_method.md` 中标明非 signoff 功耗。
- 热优化适配元数据：虽然本轮不做热优化，Stage 3 仍必须保存可反查的数据接口，避免热图失去工程含义。至少输出 instance-to-grid 映射、RTL-scope-to-gate-region 映射、region tag、每个窗口的 region/grid power 汇总、top hotspot grid 到 instance/module 的候选反查表，以及 mapping/fallback 比例。该数据仅用于后续解释和未来扩展，不得在本轮自动触发 placement/floorplan/RTL 优化。
- Phase 2 proxy 输入建议：Stage 3 可参考 `reports/stage2_tiled_matmul_os_baseline_impl_summary.md` 的 closeout caveats。`6_report.log` 和 `6_report.json` 是 final report 证据；其中 VDD/VSS IR 数值来自不完整 PDN/proxy 上下文，只能作为无效 PDN signoff 的证据，不得作为功耗或热输入。

## 9.7 阶段 3 产出
### 产物 A：功耗网格
- `power/stage3_tiled_matmul_os_baseline_grid_power.csv`

### 产物 B：transient power trace
- `power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv`

### 产物 C：实例级 Top-N 统计
- `reports/stage3_tiled_matmul_os_baseline_top_power_instances.md`
- `reports/stage3_tiled_matmul_os_baseline_top_toggle_instances.md`

### 产物 D：功耗构建说明
- `reports/stage3_tiled_matmul_os_baseline_power_trace_method.md`

内容必须说明：
- 时间窗来源
- grid 大小
- 映射方式
- 聚合方式
- 输出字段定义

### 产物 E：热图反查与未来优化适配元数据
- `power/stage3_tiled_matmul_os_baseline_instance_grid_map.csv`
- `power/stage3_tiled_matmul_os_baseline_region_power_summary.csv`
- `reports/stage3_tiled_matmul_os_baseline_activity_mapping_manifest.md`
- `reports/stage3_tiled_matmul_os_baseline_hotspot_traceback.md`

这些文件只保存映射和解释能力，不表示本轮执行热优化。

## 9.8 阶段 3 测试
### 一致性测试
- 功耗峰值时间段应与 RTL 高活动窗口大体一致
- 持续高负载阶段应表现为持续高功耗

### 数据完整性测试
- 每个 grid bin 都有定义
- 时间轴连续
- 无明显异常负值/空值

### 统计合理性测试
- top-N power instances 不应全部来自无关逻辑
- PE array 邻近区域应占主要高功耗分布

## 9.9 阶段 3 验收标准
满足以下条件才允许进入阶段 4：

- 已生成可直接供 PACT 使用的功耗输入
- 已生成 HotSpot 粗粒度所需聚合输入
- 已产出 Top-N 实例统计
- 已确认功耗分布与 baseline workload 逻辑一致

---

## 10. 阶段 4：PACT 主线热仿真 + ATSim3D v1 独立热仿真 + HotSpot 粗对照

## 10.1 阶段目标
使用阶段 3 的功耗输入，完成：

- PACT 主线 steady-state 热仿真
- PACT 主线 transient 热仿真
- ATSim3D v1 steady-state 独立热仿真
- HotSpot 粗粒度对照
- 形成可展示的热图、曲线与结论摘要

## 10.2 阶段 4 允许的工作
- 构建 PACT 输入
- 运行 PACT steady-state / transient
- 构建并运行 ATSim3D v1 LCF/config/simparams/floorplan/power 输入
- 构建 HotSpot block-level 输入
- 运行 HotSpot 粗对照
- 输出热图、时间曲线、热点统计

## 10.3 阶段 4 禁止的工作
- 热优化
- floorplan 重排
- 反复改实现版本
- 引入第二个 workload
- 封装级复杂扩展

## 10.4 阶段 4 必须明确的内容
Codex 必须写清：

- PACT 配置模板：以 `third_party/PACT/Example/config_files/default_htc_1e4_10mm.config` 和 `third_party/PACT/Example/modelParams_files/` 为模板，在 Stage 4 生成与 Stage 3 grid/die 尺寸一致的 `thermal/pact/stage4_tiled_matmul_os_baseline/` 配置；示例模板中的 10mm/材料/边界参数只作为可运行 baseline，不声明封装级物理精度；入口命令为 `python "$PACT_ENTRY" <lcf.csv> <config> <modelParams> --gridSteadyFile <out>`。
- PACT 输入文件路径：Stage 4 从 `power/stage3_tiled_matmul_os_baseline_grid_power.csv` 与 `power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv` 生成 `thermal/pact/stage4_tiled_matmul_os_baseline/lcf_stage4_tiled_matmul_os_baseline.csv`、`config_stage4_tiled_matmul_os_baseline.config`、`modelParams_stage4_tiled_matmul_os_baseline.config`、`steady_temperature_stage4_tiled_matmul_os_baseline.csv`、`transient_temperature_stage4_tiled_matmul_os_baseline.csv`。
- PACT 坐标处理：主 thermal grid、rank、heatmap、standard-cell overlay 和跨工具对比必须使用 DEF physical grid，`grid_y=0` 是 die bottom。PACT raw result row `0` 对应物理 die top 时，后处理必须执行 `physical_grid_y = grid - 1 - pact_raw_row_y`。raw row-order 文件只能用 `_pact_raw_order` 等明确后缀保留为 audit，不得作为物理坐标报告。
- ATSim3D v1 输入和输出：Stage 4 必须从同一 Stage 3 grid power 与 Stage 2 die/floorplan geometry 生成 ATSim3D v1 LCF/config/simparams/floorplan/power/manifest，并运行 `scripts/run_atsim3d.sh` 得到 active layer `.res`。`.res` 是细网格温度样本，不包含标准单元实例名、master、面积或功耗字段；标准单元级解释必须把下采样后的 ATSim physical grid 与 Stage 3 placed instance grid map 叠加。
- ATSim3D v1 对比处理：主对比必须使用下采样到 DEF physical grid 的 ATSim 温度与修复后的 PACT physical-coordinate grid；PACT raw-order 对比只能保留为诊断。ATSim3.5D v2 `ATSim3_5D` 在 XML/config schema 未验证前不纳入本历史 proxy route 的强制验收。
- 图表可查看性：若 Stage 4 后处理生成 SVG 图表，必须同步生成同 basename PNG companion；SVG 用于矢量编辑/论文排版，PNG 用于 VS Code、远程环境和报告快速预览。
- HotSpot block 聚合规则：从 Stage 3 grid power 聚合为 coarse blocks：`pe_array`、`controller_execute`、`load_store_datapath`、`scratchpad_accumulator_context`、`other_context`；`scratchpad_accumulator_context` 只表示周边控制/上下文和粗粒度背景，不表示 SRAM array 细节；该聚合只作趋势对照，不作为主线细粒度结论。
- 边界条件与默认材料参数：Phase 0 固定采用 PACT/HotSpot 示例默认材料和对流边界作为 baseline；默认 `htc=1e4` 级别模板，环境温度和层参数按模板记录。任何材料/封装扩展都超出本轮范围。

## 10.4.1 2026-04-26 Phase 4 preflight 状态

当前 Phase 3 已按 `proxy / thermal-flow prototype` 验收，可作为 Phase 4 准备输入，但不能描述为 signoff power。Phase 4 正式执行尚未开始，需用户确认后再创建 Stage 4 输入脚本并运行求解器。

已确认的 Phase 4 输入和工具状态：

- Stage 3 交付物可用：`power/stage3_tiled_matmul_os_baseline_grid_power.csv`、`power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv`、metadata、region power summary、instance-grid map 和 Stage 3 方法/验收报告。
- Stage 3 grid 为 `64 x 64`，transient ptrace 为 `64` 个时间行，峰值目标 bin 的 proxy 总功耗归一化为 `1.0 W`。
- Stage 2 DEF 的 `UNITS DISTANCE MICRONS 4000` 和 `DIEAREA ( 0 0 ) ( 13495456 13495456 )` 对应 die side `0.003373864 m`；Stage 4 PACT、ATSim3D v1 和 HotSpot 的 floorplan/geometry 输入必须使用该尺寸，而不是沿用 PACT 示例中的 10 mm 物理尺寸声明。
- `python "$PACT_ENTRY" --help` 通过；PACT SuperLU 示例 steady smoke 在 `/tmp/tp_phase4_pact_smoke/` 生成两层 grid steady 输出。
- HotSpot 两 block tiny smoke 通过并生成 `.ttrace`。
- `Xyce -v` 为 `Xyce Release 7.4.0-opensource`；`mpirun -np 2 /bin/hostname` 通过，但当前 Xyce 是 serial 构建。PACT formal SPICE steady/transient 配置必须设置 `number_of_core = 1`，不得把 OpenMPI 可用误写为 PACT parallel 已验收。

Phase 4 开发步骤已记录在 `reports/stage4_tiled_matmul_os_baseline_preflight_plan.md`。下一步在用户确认后，从最小 Stage 4 输入生成脚本开始，而不是直接运行重型 thermal 求解。

2026-05-03 勘误：该历史 preflight 状态之后发现 PACT raw row-order 与 DEF physical `grid_y` 相反。后续阅读本历史计划时必须按 issue log item 78 和 `artifacts/stage4/README.md` 的修复规则解释 Stage 4 PACT 产物。

## 10.5 阶段 4 主输出
### PACT 主线
必须输出：

- steady-state 温度图
- transient 温度曲线
- hotspot 排名
- hotspot 持续时间统计
- center vs edge 温差分析
- PACT coordinate manifest：记录 raw row-order、physical-coordinate 修复公式、raw/fixed hotspot 位置
- raw row-order audit copy：仅用于复查，不作为物理坐标结论

### ATSim3D v1 独立对照
必须输出：

- LCF/config/simparams/floorplan/power/manifest 输入
- active layer `.res` 温度结果
- 下采样到 DEF physical grid 的温度表、热图和 hotspot rank
- 与修复后 PACT physical grid 的差值统计、相关系数和热图
- 标准单元数据来源说明：ATSim `.res` 不含标准单元实例数据，标准单元解释来自 Stage 3 placed instance map 的叠加

### HotSpot 对照
必须输出：

- block-level 温度分布
- 与 PACT/ATSim3D v1 的趋势对比摘要

## 10.6 阶段 4 产出
### 产物 A：PACT 报告
- `reports/stage4_tiled_matmul_os_baseline_pact_thermal_report.md`

### 产物 B：ATSim3D v1 报告
- `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/RESULTS.md`
- `artifacts/stage4/atsim3d_v1_proxy/README.md`

### 产物 C：HotSpot 对照报告
- `reports/stage4_tiled_matmul_os_baseline_hotspot_report.md`

### 产物 D：图表集合
- `artifacts/stage4/heatmap_steady_*.png`
- `artifacts/stage4/thermal_trace_*.png`
- `artifacts/stage4/hotspot_rank_*.csv`
- `artifacts/stage4/pact_coordinate_fix_manifest.{json,csv}`
- `artifacts/stage4/*_pact_raw_order.csv` audit files
- 标准单元上下文图表的 `.svg` 与同 basename `.png` companion

### 产物 E：阶段总结
- `reports/stage4_tiled_matmul_os_baseline_summary.md`

内容必须回答：
1. hotspot 在哪里
2. 持续高负载下温升行为如何
3. PACT、ATSim3D v1 与 HotSpot 在趋势上是否一致
4. 为什么细粒度热分析比粗粒度更有价值

## 10.7 阶段 4 测试
### 求解成功性
- PACT steady-state 成功
- PACT transient 成功
- ATSim3D v1 steady 成功并生成 `.res`
- HotSpot 对照成功

### 物理合理性
- 持续高负载应产生持续升温
- 热点应集中在阵列相关高活动区域
- 空间热分布与功耗 grid 分布应有合理相关性
- PACT 主 grid/rank/heatmap 必须是 DEF physical coordinates；raw row-order 坐标只允许作为 audit-only 证据
- ATSim3D v1 下采样结果必须和修复后的 PACT physical grid 对齐比较；标准单元级解释不得声称来自 ATSim `.res` 原生字段

### 对照合理性
- ATSim3D v1 与修复后 PACT physical grid 至少在主要热点形状上可解释
- HotSpot 与 PACT/ATSim3D v1 至少在粗趋势上可解释
- PACT 和 ATSim3D v1 应展现比 HotSpot 更细的局部不均匀

## 10.8 阶段 4 验收标准
满足以下条件视为阶段 0–4 完成：

- 已成功跑完 PACT steady-state + transient
- 已跑完 ATSim3D v1 steady 独立对照
- 已跑完 HotSpot 粗对照
- 已生成一批可展示热图和曲线
- PACT 主产物坐标已修复到 DEF physical grid，并保留 raw row-order audit copy
- 生成的 SVG 图表均有同 basename PNG companion
- 已形成可用于论文/开题/答辩的实验骨架
- 已形成阶段总结报告

## 10.8.1 2026-04-26 Phase 4 completion status

Phase 4 已按当前 `proxy / thermal-flow prototype` 路线完成，阶段 0-4 闭环产物已生成。当前结果不能升级为 signoff thermal/power 结论，但满足本轮“单一 GEMM baseline 跑通热仿真闭环、输出热图/曲线/实验骨架”的目标。

完成内容：

- Stage 4 输入生成脚本：`scripts/build_stage4_thermal_inputs.py`。
- PACT transient 生成 netlist 兼容修复脚本：`scripts/sanitize_stage4_pact_transient_cir.py`；只处理生成的 `.cir`，不修改 `third_party/PACT`。
- Stage 4 结果汇总脚本：`scripts/report_stage4_thermal_results.py`。
- PACT steady SuperLU 完成，layer0 温度范围 `322.050 K` 到 `333.720 K`。
- PACT transient serial Xyce 完成，`number_of_core=1`，sanitized netlist Xyce log 显示 `0` failed linear solves 和 `0` nonlinear convergence failures。
- ATSim3D v1 proxy rerun 完成，输出 active layer `.res`、64x64/256x256 下采样热图、hotspot rank、ATSim-vs-corrected-PACT 差值统计和 public 2DIC/Mono3D/TSV3D 示例对比图，详见 `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/RESULTS.md` 与 `artifacts/stage4/atsim3d_v1_proxy/README.md`。
- HotSpot coarse comparison 完成，输出 `64` 行 ttrace。
- 图表和表格已输出到 `artifacts/stage4/`，报告已输出到 `reports/stage4_tiled_matmul_os_baseline_{pact_thermal_report,hotspot_report,summary}.md`。
- 2026-05-03 已对历史 Stage 4 后处理产物执行 PACT y 坐标修复：主 PACT artifacts 改为 DEF physical grid，raw row-order copy 仅作为 audit，详见 `artifacts/stage4/README.md` 和 issue log item 78。
- 2026-05-03 标准单元上下文 SVG 图已补同 basename PNG companion，详见 issue log item 79。

已记录的兼容问题：

- PACT transient ptrace 首列必须名为 `Power`，见 issue log item 69。
- PACT 生成的 Xyce transient netlist 对当前 per-grid-cell floorplan 会产生 Si lateral `inf`，并且需要正确拼写的 `total_simulation_time`；当前用生成 netlist sanitizer 修复，见 issue log item 70。

主要结果（2026-05-03 坐标修复后）：

- PACT steady layer0 corrected physical hotspot 位于 DEF physical grid `(22, 16)`，峰值 `333.720 K`，相对 `318.15 K` ambient 的温升为 `15.570 K`。
- 旧 raw row-order hotspot 为 `(22, 47)`，这不是物理 `grid_y`，不得用于标准单元分布、ATSim 对比或报告图上物理位置。
- ATSim3D v1 proxy fine-grid hotspot 对应 64x64 source grid `(21, 14)`，与修复后的 PACT physical hotspot `(22, 16)` 接近；physical y-up alignment 的相关系数为 `0.972619`，raw-order alignment 的相关系数为 `-0.141279`。
- ATSim3D v1 `.res` 不包含标准单元实例信息；标准单元上下文来自 Stage 3 `power/stage3_tiled_matmul_os_baseline_instance_grid_map.csv` 与 thermal physical grid 的叠加。
- 短 transient 窗口内 PACT layer0 peak max 为 `318.180 K`；HotSpot coarse peak max 为 `318.230 K`。该差异反映 steady 长时解与短 transient 粗模型的用途不同。

保留 caveats：Stage 3 power 仍为 normalized proxy power，Stage 2 仍为 `proxy / non-signoff`，无 SDF，SRAM macro bodies 不作为精细热源。

---

## 11. 每阶段结束必须提交的报告模板

每阶段结束，Codex 必须输出一个阶段报告，至少包括：

### 11.1 本阶段完成内容
- 做了什么
- 改了哪些文件
- 生成了哪些产物

### 11.2 本阶段关键结果
- 最重要的 3–5 个结果
- 哪些结果符合预期
- 哪些结果不符合预期

### 11.3 本阶段验收结论
- 是否达到阶段验收标准
- 如果没有，卡在哪

### 11.4 下一阶段输入
- 下一阶段需要哪些文件
- 这些文件是否已就绪

---

## 12. 停止条件

以下任一情况出现，Codex 必须停止并报告，而不是自行扩展解决：

1. 关键依赖缺失
2. ASAP7 环境不可用
3. baseline workload 无法运行
4. 无法定位目标模块边界
5. 无法导出后端关键文件
6. 无法生成可用功耗 trace
7. PACT、ATSim3D v1 或 HotSpot 无法运行且原因不清楚
8. 需要超出当前范围的大规模重构

---

## 13. 最终交付要求

在阶段 0–4 全部完成后，Codex 必须至少提交：

### 13.1 图表
- 稳态热图
- 瞬态温度曲线
- 热点排名图或表
- ATSim3D v1 与 PACT physical-grid 对照图
- HotSpot 与 PACT/ATSim3D v1 对照图

### 13.2 文档
- 最终阶段总结
- 可复现流程说明
- 实验骨架说明
- 后续扩展建议（仅建议，不实现）

### 13.3 数据
- baseline workload 标识
- 实现文件清单
- power trace
- thermal result
- Top-N 实例统计

---

## 14. 本文档后续更新规则

本文档中的结构与约束不可随意删除。  

1. 将占位项替换为仓库真实内容
2. 在不扩大范围的前提下补充真实命令、真实路径、真实产物名
3. 在执行阶段0任务时，对本文档进行更新、丰富、将模糊要求写为具体的要求
4. 在向用户确认后可以不断优化本文档

不得擅自修改：

- 研究对象边界
- baseline 数量
- ASAP7 约束
- PACT 主线 + ATSim3D v1 独立 steady 对照 + HotSpot 粗对照
- 先跑通单一样例再扩展的总体策略
