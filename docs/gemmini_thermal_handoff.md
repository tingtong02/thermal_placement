# Gemmini Thermal Handoff

更新时间：2026-04-20

## 1. 当前阶段结论

当前工作已经完成验证计划中的 Phase A，具体状态如下：

- 已阅读并对齐 [docs/gemmini_thermal_validation_plan.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_validation_plan.md) 与 [docs/gemmini_thermal_environment_setup.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_environment_setup.md)。
- 已浏览仓库主干和 `third_party/chipyard` 相关路径，确认主流程依赖集中在 Chipyard/Gemmini。
- 已成功生成 `GemminiRocketConfig` 对应 RTL，并导出到 [rtl_exports/generated-verilog/GemminiRocketConfig](/home/lisihang/thermal_placement/rtl_exports/generated-verilog/GemminiRocketConfig)。
- 已生成 Gemmini 模块分桶清单和初版层级映射：
  - [gemmini_module_inventory.md](/home/lisihang/thermal_placement/reports/notes/gemmini_module_inventory.md)
  - [hierarchy_map.yaml](/home/lisihang/thermal_placement/configs/gemmini/hierarchy_map.yaml)
- 已在项目目录 [tools/riscv](/home/lisihang/thermal_placement/tools/riscv) 补齐最小 RISC-V bare-metal toolchain、`fesvr`、`spike`、`spike-dasm`、`libgloss_htif`。
- 已成功构建 `mvin_mvout-baremetal`，并成功构建 `GemminiRocketConfig` 的 Verilator debug simulator。
- 仿真入口已能启动到 UART / DRAMSim 初始化；完整 workload 波形仍需要后续按更合适的 runtime / max-cycle 策略继续跑完。

## 2. 当前生成的 Gemmini 配置

本次已实际生成并验证的配置是 `GemminiRocketConfig`。

该配置定义见 [GemminiConfigs.scala](/home/lisihang/thermal_placement/third_party/chipyard/generators/gemmini/chipyard/GemminiConfigs.scala)，其组合方式为：

- `new gemmini.DefaultGemminiConfig`
- `new freechips.rocketchip.rocket.WithNHugeCores(1)`
- `new chipyard.config.WithSystemBusWidth(128)`
- `new chipyard.config.AbstractConfig`

也就是说，当前不是一个“纯 Gemmini 顶层”，而是：

- 1 个 Rocket huge core
- 1 个通过 RoCC 挂接的 Gemmini accelerator
- 128-bit system bus
- 完整 Chipyard SoC / TestHarness 仿真上下文

Gemmini 自身参数来自 `DefaultGemminiConfig` 对应的 `GemminiConfigs.defaultConfig`，以及生成后的 [gemmini_params.h](/home/lisihang/thermal_placement/third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/include/gemmini_params.h)。当前关键参数如下：

| 项目 | 当前值 | 说明 |
| --- | --- | --- |
| `CONFIG` | `GemminiRocketConfig` | 本次 RTL 导出配置名 |
| Rocket core 数 | 1 | `WithNHugeCores(1)` |
| System bus width | 128-bit | 为默认 16x16 8-bit Gemmini 提供带宽 |
| `DIM` | 16 | Systolic array 维度 |
| `tileRows` / `tileColumns` | 1 / 1 | 每个 tile 为 1x1 |
| `meshRows` / `meshColumns` | 16 / 16 | 总阵列为 16x16 PE |
| `dataflow` | `BOTH` | 同时支持 OS / WS |
| `inputType` | `SInt(8)` | `elem_t = int8_t` |
| `weightType` | `SInt(8)` | 权重 8-bit |
| `accType` | `SInt(32)` | `acc_t = int32_t` |
| `sp_capacity` | 256 KiB | scratchpad 总容量 |
| `acc_capacity` | 64 KiB | accumulator 总容量 |
| `sp_banks` | 4 | scratchpad bank 数 |
| `acc_banks` | 2 | accumulator bank 数 |
| `BANK_ROWS` | 4096 | 由生成头文件可见 |
| `ACC_ROWS` | 1024 | 由生成头文件可见 |
| `dma_maxbytes` | 64 | 每次 DMA 最大片段 |
| `dma_buswidth` | 128 | DMA 总线宽度 |
| `ld/st/ex queue` | 8 / 2 / 8 | 指令队列长度 |
| `reservation station` | 8 / 4 / 16 | ld/st/ex entries |
| `max_in_flight_mem_reqs` | 16 | 并发内存请求数 |
| `tlb_size` | 4 | Gemmini TLB 项数 |
| `mvin_scale` | enabled | 生成头文件含 `HAS_MVIN_SCALE` |
| `acc_read_small_width` | enabled | 生成头文件可见 |
| `acc_read_full_width` | enabled | 生成头文件可见 |
| first-layer opt | enabled | 生成头文件含 `HAS_FIRST_LAYER_OPTIMIZATIONS` |

从热分析角度看，当前配置可理解为：

- 计算阵列：`16 x 16 = 256` 个 PE
- 本地数据存储：4-bank scratchpad
- 部分和存储：2-bank accumulator
- 数据搬运：Load/Store controller + StreamReader/Writer
- 上层上下文：Rocket core、TL/SoC glue、cache、harness 等仍然存在于完整生成 RTL 中

## 3. 已生成的 RTL / 元数据

主输出目录：

- [rtl_exports/generated-verilog/GemminiRocketConfig](/home/lisihang/thermal_placement/rtl_exports/generated-verilog/GemminiRocketConfig)

其中包括：

- `gen-collateral/*.sv`：split Verilog
- `*.fir`：FIRRTL
- `*.anno.json`：注解
- `*.firtool.log`：firtool 日志
- `*.all.f` / `*.top.f` / `*.model.f` / `*.bb.f`：filelists
- `manifest.txt`：本次导出元信息

本次生成元信息记录在 [manifest.txt](/home/lisihang/thermal_placement/rtl_exports/generated-verilog/GemminiRocketConfig/manifest.txt)：

- Chipyard commit: `63c1506`
- Gemmini commit: `6ad65b9`
- generated at: `2026-04-20T04:02:45Z`

## 4. 当前模块分层结果

Gemmini 模块清点脚本已完成首轮分类，结果在 [gemmini_module_inventory.md](/home/lisihang/thermal_placement/reports/notes/gemmini_module_inventory.md)。

当前统计：

- RTL modules found: `648`
- Hierarchy names found: `1783`

首轮热研究 bucket：

| Bucket | Module Count | 当前处理 |
| --- | ---: | --- |
| `pe_array` | 71 | 纳入热研究 |
| `scratchpad` | 13 | 纳入热研究 |
| `accumulator` | 3 | 纳入热研究 |
| `load_store_dma` | 5 | 纳入热研究 |
| `controller` | 10 | 纳入热研究 |
| `gemmini_other` | 1 | 纳入热研究 |
| `tl_soc_glue` | 229 | 暂缓 |
| `non_gemmini_context` | 316 | 暂缓 |

这个分类已经足够支撑后续：

- 波形信号筛选
- 活动率聚合
- block power 建模
- macro grouping 初稿

## 5. 已新增脚本

### 5.1 RTL 生成

- [run_gemmini_rtl_generation.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_rtl_generation.sh)

用途：

- 生成 `GemminiRocketConfig` Verilog
- 导出到 `rtl_exports/generated-verilog`
- 运行层级清点脚本

并行参数：

- `MAKE_JOBS`，由环境脚本限制为最多 `128`

### 5.2 模块层级清点

- [inspect_gemmini_hierarchy.py](/home/lisihang/thermal_placement/scripts/inspect_gemmini_hierarchy.py)

用途：

- 扫描 split Verilog
- 结合 hierarchy json
- 输出 bucket 化模块清单和 yaml 映射

### 5.3 构建 Gemmini bare-metal workload

- [build_gemmini_workloads.sh](/home/lisihang/thermal_placement/scripts/build_gemmini_workloads.sh)

用途：

- 构建 `gemmini-rocc-tests` bare-metal workload
- 导出到 `sim/binaries/<CONFIG>/`

并行参数：

- `MAKE_JOBS`，由环境脚本限制为最多 `128`

### 5.4 运行 workload + 导出波形

- [run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh)

用途：

- 构建 Verilator debug simulator
- 运行指定 bare-metal workload
- 导出 `log/out/vcd|fst` 到 `sim/logs` 和 `sim/waves`

并行参数：

- `MAKE_JOBS`，由环境脚本限制为最多 `128`

## 6. 当前环境状态

当前 RTL 生成、workload 构建、debug simulator 构建已经具备本地闭环：

- `RISCV=/home/lisihang/thermal_placement/tools/riscv`
- `riscv64-unknown-elf-gcc` 通过 [tools/bin](/home/lisihang/thermal_placement/tools/bin) 包装器调用本地真实编译器
- `libfesvr.a`、`spike`、`spike-dasm` 已安装到本地 prefix
- `libgloss_htif.a` 已安装，`htif.specs` smoke test 通过
- [mvin_mvout-baremetal](/home/lisihang/thermal_placement/sim/binaries/GemminiRocketConfig/mvin_mvout-baremetal) 已构建成功
- `simulator-chipyard.harness-GemminiRocketConfig-debug` 已构建成功

仍需注意：

- `htif_nano.specs` 不适合当前最小 picolibc/newlib 混合前缀，通用 smoke test 使用 `htif.specs`
- 带 VCD 的 `mvin_mvout` debug run 较重，当前只确认启动到 UART / DRAMSim 初始化，完整波形需继续优化运行参数

## 7. 后续建议执行顺序

建议后续按以下顺序继续：

1. 选择更小或更短的 workload / max-cycle 策略，跑出第一条可控 VCD/FST
2. 写 `extract_vcd_activity.py`
3. 从 bucket 级活动率过渡到 block power
4. 进入 macro grouping 和 OpenROAD/HotSpot

## 8. 并行与多核使用建议

根据当前仓库里的脚本，后续统一通过 `MAKE_JOBS` 控制并行度，且最多使用 128：

```bash
source tools/env_gemmini_thermal.sh
echo "$MAKE_JOBS"
```

然后运行：

```bash
scripts/run_gemmini_rtl_generation.sh
scripts/build_gemmini_workloads.sh mvin_mvout
scripts/run_gemmini_workload.sh mvin_mvout
```

对后续综合/物理流程，也建议默认优先打开多核：

- Verilator / make：`-j "$MAKE_JOBS"`
- ORFS / OpenROAD 外层 make：优先显式传 `-j`
- Python 批处理：后续按任务粒度再决定是否并行

注意：并行度增加后，日志更容易交错，建议继续把关键结果复制回 `sim/`、`reports/`、`thermal/` 等可追溯目录。
