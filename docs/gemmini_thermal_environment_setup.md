# Gemmini Thermal Validation Environment

更新时间：2026-05-05

项目根目录：`/home/lisihang/thermal_placement`

## 使用方式

每次进入项目后先执行：

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

该脚本会激活 conda 环境 `thermal_placement`，并配置 Verilator、HotSpot、PACT/ATSim、Cadence Genus/Innovus、full ASAP7、fake SRAM、sbt、Chipyard/Gemmini 相关路径。OpenROAD/Yosys/OpenSTA 仍保留为 legacy/reference 工具，不是当前 active Stage 2 backend。

2026-05-05 起，active Stage 2 backend 改为 Cadence Genus + Innovus：

| 变量 | 值 |
| --- | --- |
| `CADENCE_HOME` | `/opt/eda/Cadence_DDI_23.14` |
| `CDS_LIC_FILE` | `/opt/eda/Cadence_DDI_23.14/license/license.dat` |
| `CDS_SKIP_OS_CHECK_ON_STARTUP` | `1` |
| `TP_CADENCE_GENUS_CPUS` | 默认 `8` |
| `TP_CADENCE_INNOVUS_CPUS` | 默认 `8` |

当前 Cadence smoke 证据：

- Genus `23.14-s090_1` 可运行并 checkout license。
- Innovus `v23.14-s088_1` 可运行并 checkout license；license banner 显示 8 CPU jobs。
- 多线程参数参考 `docs/references/cadence_genus_innovus_edahub_smoke_2026-05-04.md`，不得沿用 OpenROAD `MAKE_JOBS` / `NUM_CORES` 语义。

Full ASAP7 外部 PDK：

| 变量 | 值 |
| --- | --- |
| `ASAP7_HOME` | `/home/lisihang/asap7` |
| `ASAP7_STDCELL_VERSION` | `asap7sc7p5t_28` |
| `ASAP7_LIB_CACHE` | `/home/lisihang/thermal_placement/.cache/asap7/asap7sc7p5t_28/NLDM` |
| `ASAP7_FULL_CONFIG` | `/home/lisihang/thermal_placement/configs/asap7_full/asap7_full.tcl` |

本轮使用 `asap7sc7p5t_28` 1x collateral、unscaled QRC、NLDM RVT/LVT/SLVT TT Liberty。原始 Liberty 是 `.lib.7z`，由 `scripts/prepare_asap7_liberty_cache.py` 解压到 `.cache/asap7/`，不提交解压后的 `.lib`。CCS 只作为后续可选增强记录。

2026-05-05 起，该脚本还配置本仓库内 fake SRAM collateral 路径：

| 变量 | 值 |
| --- | --- |
| `FAKE_SRAM_HOME` | `/home/lisihang/fake_sram` |
| `FAKE_SRAM_ASAP7_ROOT` | `/home/lisihang/fake_sram/results/asap7` |
| `FAKE_SRAM_CADENCE_CACHE` | `/home/lisihang/thermal_placement/.cache/fake_sram/asap7` |
| `FAKE_SRAM_DESIGN` | `Gemmini` |
| `FAKE_SRAM_ASAP7_CONFIG` | `/home/lisihang/thermal_placement/configs/fake_sram/asap7_fake_sram.tcl` |

Cadence flow 不直接使用外部 fake SRAM 仓库中已有的 RISCY/Vortex/NVDLA 等 macro 类型。当前 active 路线从 Gemmini RTL 第一性原则识别本轮需要的 external memory shapes，并生成本仓库 cache：

```bash
python scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini
```

该脚本生成 `.cache/fake_sram/asap7/Gemmini/`，输出 Liberty、LEF、Verilog stub 和 manifest。当前检测到的 Gemmini external memory macros 为：

| macro | wrapper | 类型 | depth | width |
| --- | --- | --- | --- | --- |
| `mem_ext` | `mem` | `1rw` | 4096 | 128 |
| `mem_0_ext` | `mem_0` | `1r1w` | 512 | 512 |

Liberty 适配到 ASAP7 TT `0.7V/25C`。LEF 尺寸和面积按 `/home/lisihang/fake_sram` 生成方法参数估算；外部仓库只作为方法参考，不作为 active macro 类型来源。

## Git 忽略策略

`.gitignore` 只保留少量必要规则，避免误忽略实验结果和记录类文件。核心规则：

- `third_party/` 被忽略：Chipyard、Gemmini 子模块、OpenROAD/OpenSTA/HotSpot/Verilator 源码树不入库。
- `tools/*` 被忽略：本地安装的工具、预编译包、下载缓存不入库。
- `tools/env_gemmini_thermal.sh` 例外保留：这是项目环境入口脚本，不是工具载荷。
- `/home/lisihang/fake_sram/` 是用户提供的 external SRAM collateral，不在 `third_party/` 或 `tools/` 下；当前保留为项目输入资产。
- Python 缓存 `__pycache__/`、`*.pyc` 被忽略。
- 本地临时/中间目录 `.tmp/`、`.cache/`、`tmp/`、`obj_dir/` 被忽略。
- `sim/`、`rtl_exports/`、`physical/`、`thermal/`、`reports/` 下的实验结果和记录文件不忽略，需要按实验价值正常纳入版本管理或单独归档。
- 日志、VCD、CSV、DEF、SDC、report、HotSpot `.flp/.ptrace/.ttrace` 等结果/记录文件不按扩展名全局忽略。

如果后续确实修改了被 `.gitignore` 忽略的内容，需要在提交或交接前报告，至少写明：

| 日期 | 忽略路径 | 修改原因 | 验证方式 | 后续处理 |
| --- | --- | --- | --- | --- |
| 2026-04-20 | `third_party/`、`tools/` | 初次环境搭建，安装/拉取工具链 | `scripts/check_environment.sh` | 仅记录路径和版本，不提交工具载荷 |

## Conda 环境

Python 环境按要求使用 `/home/lisihang/miniconda3/bin/conda` 新建：

- 环境名：`thermal_placement`
- 环境路径：`/home/lisihang/miniconda3/envs/thermal_placement`
- Python：`3.11.15`
- 项目 Python 规则：所有仓库脚本、数据处理和图表生成默认使用该环境；不要使用 base conda Python 或系统 Python。
- 已验证 Python 包：`numpy 2.4.4`、`pandas 3.0.2`、`matplotlib 3.10.8`、`Pillow 12.1.1`、`seaborn 0.13.2`、`pyyaml 6.0.3`、`loguru 0.7.3`、`networkx 3.4.1`、`pytest 9.0.3`、`pytest-cov 7.1.0`、`pytest-xdist 3.8.0`、`pre-commit 4.6.0`、`flake8 7.3.0`、`scipy 1.17.1`、`pyvcd`、`vcdvcd`

如项目脚本、数据处理、可视化或测试确实需要新增 Python 包，允许安装到 `thermal_placement`，并在本文件或 `docs/tool_environment_inventory.md` 中记录包名、版本、用途和验证命令。优先使用 conda；若包只在 PyPI 可用，可使用该环境内的 pip。不要安装到 base 环境或系统 Python。示例：

```bash
/home/lisihang/miniconda3/bin/conda install -n thermal_placement <package>
/home/lisihang/miniconda3/bin/conda run -n thermal_placement python -m pip install <package>
```

`third_party/edahub` 复用该环境，不创建单独的 `edahub` conda 环境。edahub 如需新增 Python 包，直接安装到 `thermal_placement`：

```bash
/home/lisihang/miniconda3/bin/conda run -n thermal_placement python -m pip install -r third_party/edahub/requirements.txt
```

当前已将 `third_party/edahub/requirements.txt` 安装到 `thermal_placement`，覆盖 edahub 的开发、lint 与测试依赖。

验证命令：

```bash
/home/lisihang/miniconda3/bin/conda run -n thermal_placement python -c "import numpy,pandas,matplotlib,PIL,seaborn,yaml,loguru,networkx,pytest,scipy,vcd,vcdvcd; print('python ok')"
```

## 工具清单

| 工具 | 状态 | 路径 | 已验证版本或 commit |
| --- | --- | --- | --- |
| Chipyard | 已拉取，Gemmini 主路径依赖已补齐 | `third_party/chipyard` | `63c1506` |
| Gemmini | 已对齐到 Chipyard 记录的 commit | `third_party/chipyard/generators/gemmini` | `6ad65b9` |
| gemmini-rocc-tests | 已拉取，`riscv-tests/env`、`rocc-software` 已补齐 | `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests` | `7c540b3` |
| sbt | 本地安装；Chipyard 项目可启动 | `tools/sbt/sbt/bin/sbt` | launcher `1.12.9`，Chipyard 使用 sbt `1.8.2` |
| Java | 系统已有 | `/usr/bin/java` | OpenJDK `11.0.30` |
| Verilator | 已源码构建并本地安装 | `tools/verilator/bin/verilator` | `5.047 devel`，source `e82bd52` |
| OpenSTA | 已源码构建并本地安装 | `tools/opensta/bin/sta` | `3.1.0` |
| HotSpot | 已源码构建 | `third_party/HotSpot/hotspot` | source `f18831e` |
| ATSim3D v1 | 已拉取并配置专用 Python 3.8 运行时 | `third_party/ATSim3D_pub`; wrapper: `scripts/run_atsim3d.sh`; runtime: `tools/atsim3d-py38` | source `8454f719409a6d0b1759602e89601f8ae18b95c2`; Python `3.8.20` |
| ATSim3D v2 binary | 已放入本地工具载荷目录 | `tools/atsim3d-bin/ATSim3_5D`; wrapper: `scripts/run_atsim3_5d.sh` | SHA256 `48322878d509432d8bff8799e1111c6347a174f01b9da454430a0bd80539f121` |
| OpenROAD-flow-scripts | 已下载源码包 | `third_party/OpenROAD-flow-scripts` | archive `bdb262792fef3797730e1b8341b946426272dcdc` |
| OpenROAD | 预编译本地安装可运行；源码也已拉取 | `tools/openroad-prebuilt/root/usr/bin/openroad`，`third_party/OpenROAD` | binary `v2.0-17598-ga008522d8`，source `48d687f` |
| Yosys / yosys-slang | 通过 oss-cad-suite 本地安装 | `tools/oss-cad-suite/oss-cad-suite/bin/yosys` | Yosys `0.64+68`，suite `2026-04-19` |
| CUDD | 已源码构建，供 OpenSTA 使用 | `tools/cudd` | `3.0.0` |
| Eigen | 已安装，供 OpenSTA 使用 | `tools/eigen` | `3.4.0` |

## Fake SRAM collateral（2026-05-05）

用户提供的 `/home/lisihang/sram_gen.zip` 已解压到外部路径并命名为：

```text
/home/lisihang/fake_sram/
```

压缩包原顶层目录为 `sram_designs_yuxiang/`。外部 fake_sram Git 分支已切到 `thermal_placement`。外部副本保留其 `.git` 元数据并保持在 `thermal_placement` 分支；源码、配置、压缩包自带 Python cache 和生成结果均按原包保留。ASAP7 结果位于：

```text
/home/lisihang/fake_sram/results/asap7/
```

项目接入文件：

- `configs/fake_sram/asap7_fake_sram.mk`：Make-based flow 使用。
- `configs/fake_sram/asap7_fake_sram.tcl`：Genus/Innovus Tcl flow 使用。
- `scripts/prepare_gemmini_fake_sram_collateral.py`：从当前 Gemmini RTL 可达 memory externs 生成 active Cadence fake SRAM collateral。
- `scripts/check_fake_sram_collateral.py`：只用于检查外部仓库已有结果完整性；不是当前 active flow 的必需入口。

当前验证结果：

- `scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini` 通过，生成 `mem_ext` 和 `mem_0_ext` 两个 macro。
- Genus 可读取 15 个 full-ASAP7 NLDM Liberty 加 2 个 Gemmini fake SRAM Liberty。
- Genus 可综合一个实例化 `mem_ext` 的 tiny top smoke。
- Innovus 可读取完整 ASAP7 1x tech/stdcell LEF 加 2 个 Gemmini fake SRAM LEF。

验证命令：

```bash
source tools/env_gemmini_thermal.sh
python scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini
```

## 验证命令

执行：

```bash
source tools/env_gemmini_thermal.sh
python -c "import numpy,pandas,matplotlib,yaml,loguru,pytest,scipy,vcd,vcdvcd; print('python ok')"
scripts/check_edahub_reduced_techlibs.py
sbt --script-version
cd "$CHIPYARD_HOME" && sbt -batch -Dsbt.log.noformat=true 'show version'
verilator --version
sta -version
hotspot -h | head -1
yosys -V
openroad -version
make -C "$FLOW_HOME" check-yosys check-openroad
```

也可以直接运行自检脚本：

```bash
scripts/check_environment.sh
```

本次已验证结果：

- Python 包导入正常，包含 edahub 所需的 `loguru 0.7.3`。
- edahub requirements 已安装到 `thermal_placement`，包含 `pytest 9.0.3`、`pytest-cov 7.1.0`、`pytest-xdist 3.8.0`、`pre-commit 4.6.0`、`flake8 7.3.0`。
- edahub reduced techlib 检查脚本 `scripts/check_edahub_reduced_techlibs.py` 可验证 `asap7`、`nangate45`、`sky130hd` 的 Liberty/DB/LEF 与主仓库适配配置。
- `sbt --script-version` 输出 `1.12.9`。
- Chipyard `sbt 'show version'` 正常完成，输出项目版本 `0.1.0-SNAPSHOT`。
- Verilator 输出 `Verilator 5.047 devel rev vUNKNOWN-built20260420-e82bd52`。
- OpenSTA 输出 `3.1.0`。
- HotSpot 可打印命令行帮助。
- Yosys 输出 `Yosys 0.64+68`。
- OpenROAD 输出 `v2.0-17598-ga008522d8`。
- ORFS `check-yosys check-openroad` 正常通过。
- 2026-04-20 运行 `scripts/check_environment.sh` 通过；其中 OpenROAD Tcl 初始化曾缺 `tclreadlineInit.tcl` 搜索路径，已通过在 `tools/env_gemmini_thermal.sh` 中设置 `TCLLIBPATH` 修复。

## 对照验证计划的环境完备性

对照已归档的 Gemmini 历史计划 [gemmini_thermal_validation_plan.md](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_thermal_validation_plan.md) 第 2 节和第 14 节 Step 1，本阶段属于“环境就绪”，必须工具已配置如下：

| 计划要求 | 当前状态 | 说明 |
| --- | --- | --- |
| Chipyard + Gemmini | 已配置 | `third_party/chipyard` 已拉取；Gemmini、Rocket-Chip、Hardfloat、Diplomacy、TestChipIP、gemmini-rocc-tests 主路径依赖已补齐。 |
| Verilator | 已配置 | 本地源码构建安装到 `tools/verilator`，可执行 `verilator --version` 和 lint smoke test。 |
| gemmini-rocc-tests | 已配置 | `software/gemmini-rocc-tests`、`riscv-tests/env`、`rocc-software` 已补齐。 |
| Python 3 + VCD/数据处理库 | 已配置 | conda env `thermal_placement`，已验证 `pyvcd`、`vcdvcd`、`numpy`、`pandas`、`matplotlib`、`scipy`、`pyyaml`、`loguru`；edahub 的 `pytest/pre-commit/flake8` 开发依赖也安装在同一环境。 |
| OpenROAD-flow-scripts | 已配置 | `third_party/OpenROAD-flow-scripts/flow` 存在，`make check-yosys check-openroad` 通过。 |
| OpenROAD | 已配置 | 本地预编译 OpenROAD 可运行，供 ORFS 使用。 |
| OpenSTA | 已配置 | 本地源码构建安装到 `tools/opensta`，可运行 Tcl smoke test。 |
| HotSpot | 已配置 | 源码构建完成，example1 steady/transient 输出 smoke test 通过。 |
| Make + Python + Bash | 已配置 | 系统 `make`、`bash` 可用，Python 通过 conda 环境提供。 |

暂不拉取的非主路径组件：

- `generators/ara/ara/toolchain/riscv-llvm`：Ara vector toolchain，不属于当前 Gemmini 热验证主线。
- `generators/gemmini/software/onnxruntime-riscv`：Gemmini ONNX Runtime 移植，体量较大；当前第一轮使用 `gemmini-rocc-tests` 即可覆盖基础/compute-heavy/memory-heavy/boundary-heavy workload 的准备工作。

## 目录结构

已按验证计划建立以下工作目录：

```text
third_party/
configs/gemmini/
configs/reduced_techlibs/
configs/openroad/reduced_platforms/
configs/hotspot/
scripts/
rtl_exports/generated-verilog/
rtl_exports/top_wrappers/
sim/binaries/
sim/waves/
sim/logs/
sim/activity/
physical/
thermal/floorplans/
thermal/power/
thermal/steady/
thermal/transient/
reports/figures/
reports/tables/
reports/notes/
```

## 网络和安装说明

当前 shell 中曾存在 `http_proxy=http://127.0.0.1:17890` 和 `https_proxy=http://127.0.0.1:17890`。GitHub、PyPI、部分 conda/apt 下载在该代理下出现 TLS EOF 或 502 错误，因此 GitHub/PyPI/apt 下载主要使用了 `env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY ...` 直接访问。

OpenROAD 的官方 GitHub latest release 已提示后续发布迁移到 `https://vaultlink.precisioninno.com/`。本次采用 GitHub 上仍可直接下载的 Ubuntu 22.04 预编译包 `2024-12-14 / v2.0-17598-ga008522d8`，并用 `dpkg -x` 解包到项目目录。缺失的运行库 `libtclreadline-2.3.8.so` 和 `libQt5Charts.so.5` 已通过 `apt download` 解包到 `tools/openroad-prebuilt/root/usr/lib/x86_64-linux-gnu`，无需 sudo。

## 剩余可选项

Chipyard 全仓库仍有两个未初始化的大型可选子模块：

- `generators/ara/ara/toolchain/riscv-llvm`
- `generators/gemmini/software/onnxruntime-riscv`

这两个不属于当前 Gemmini RTL 生成、VCD 活动提取、OpenROAD 物理实现、OpenSTA 时序分析、HotSpot 热仿真的主路径。本次已补齐 Gemmini 主仓库、`gemmini-rocc-tests`、Rocket-Chip、Hardfloat、Diplomacy、TestChipIP 以及相关嵌套依赖。

如后续确实需要完整 Ara LLVM 或 Gemmini ONNX Runtime，可以在网络稳定时执行：

```bash
cd /home/lisihang/thermal_placement/third_party/chipyard
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY git submodule update --init --depth 1 --force --checkout generators/ara/ara/toolchain/riscv-llvm
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY git -C generators/gemmini submodule update --init --depth 1 --force --checkout software/onnxruntime-riscv
```


## 后端默认工具与调用规则（2026-05-05）

当前 active 后端工具固定如下：

- 综合：Cadence Genus -> `/opt/eda/Cadence_DDI_23.14/bin/genus`
- 布局布线：Cadence Innovus -> `/opt/eda/Cadence_DDI_23.14/bin/innovus`
- PDK：full ASAP7 -> `/home/lisihang/asap7/asap7sc7p5t_28`
- fake SRAM：`/home/lisihang/fake_sram`

Legacy/reference 后端工具仍保留如下，但不得作为 active Stage 2/3 handoff 输入：

- 综合：`$YOSYS_EXE` -> `tools/oss-cad-suite/oss-cad-suite/bin/yosys`
- SystemVerilog 前端：`yosys-slang` plugin (`$YOSYS_SLANG_PLUGIN`)
- 布局布线：`$OPENROAD_EXE` -> `tools/openroad-prebuilt/root/usr/bin/openroad`
- STA：`$OPENSTA_EXE` -> `tools/opensta/bin/sta`
- ORFS：`$FLOW_HOME` -> `third_party/OpenROAD-flow-scripts/flow`
- ASAP7 reduced techlib：`third_party/edahub/edahub/technology/asap7`

重复路径处理规则：

- `sta` 虽然在 `tools/opensta/bin/sta` 和 `tools/openroad-prebuilt/root/usr/bin/sta` 都存在，但默认只能使用前者。
- `OpenROAD` 源码目录 `third_party/OpenROAD` 不是默认运行入口。
- 独立 `slang` 二进制不是 Stage 2 默认综合入口；Stage 2 默认通过 Yosys plugin 读 SystemVerilog。

## 后端多线程默认策略（2026-05-05）

Cadence active flow:

- Genus 默认 `TP_CADENCE_GENUS_CPUS=8`。
- Innovus 默认 `TP_CADENCE_INNOVUS_CPUS=8`。
- 当前 Innovus license smoke 显示 8 CPU jobs；每次重型 Innovus run 前必须保留 license banner 作为报告证据。
- `MAKE_JOBS` / `NUM_CORES` 只对 legacy OpenROAD/ORFS 或通用构建有意义，不是 Genus/Innovus CPU 语义。

Legacy OpenROAD/ORFS 环境脚本仍会导出：

- `MAKE_JOBS`
- `NUM_CORES`
- `TP_MAX_JOBS`

默认规则：

- 环境脚本会为通用构建任务提供历史默认值；实际 ORFS/后端命令必须显式设置 `MAKE_JOBS` 和 `NUM_CORES`，不要依赖旧 shell 默认值。
- `MAKE_JOBS` 表示外层独立任务数量；单个可复用实现或单条依赖链使用 `MAKE_JOBS=1`。
- `MAKE_JOBS` 最大为 `4`，仅用于多个独立 flow / block / `FLOW_VARIANT` 且输出完全隔离的场景。
- `NUM_CORES` 供 OpenROAD `-threads` 使用；正常单一任务最多 `128`。
- 当 `MAKE_JOBS=2` 时，每个任务 `NUM_CORES` 最多 `128`；当 `MAKE_JOBS=3` 或 `4` 时，每个任务 `NUM_CORES` 最多 `64`。

Legacy OpenROAD/ORFS Stage 2 entry shape retained for historical reference only. It is not the active Phase2 route and must not be used as the current handoff recipe：

```bash
source tools/env_gemmini_thermal.sh
MAKE_JOBS=1 NUM_CORES=16 scripts/run_stage2_openroad.sh synth
```

当前验证结论：

- OpenROAD 多线程接口有效，日志可见 `[INFO ORD-0030] Using 8 thread(s).`
- 当前 Yosys/ORFS 综合主链路没有确认到同等级的内部多线程接口；不要默认把 `NUM_CORES` 视为综合线程数。
- 2026-04-24 的线程对比仅代表这次测试样例和这次环境下没有看到性能收益，不代表后续正式开发不应使用多线程

## Stage 2 开发提速规则（2026-04-24）

- 区分三层并行：
  - `NUM_CORES` 只控制单次 `openroad -threads`。
  - `MAKE_JOBS` / `make -j` 主要控制多个独立 make target 或多个独立 flow 的外层并发。
  - 单个 Yosys 综合流程当前不要假设存在等效内部多线程加速。
- 对单个可复用实现，优先分阶段运行：先 `synth`，确认 netlist 出来后再推进 `floorplan`、`place`、`route`，不要默认每次重跑完整 `all`。
- 如果 Stage 2 过慢，优先使用以下杠杆，而不是直接扩大 sweep：
  1. 缩小 Gemmini top scope
  2. 收紧 RTL filelist
  3. 保持 hierarchical synthesis
  4. 只保留 PE array、control、nearby datapath
  5. 将 scratchpad/accumulator memory array 继续 blackbox/stub 化
- 只有在需要比较多个独立配置时才做外层并行，并且：
  - 为每个 job 设置唯一 `FLOW_VARIANT` 或唯一输出目录
  - 明确总核数预算、内存/IO 假设和日志路径
  - `MAKE_JOBS=2` 时每个 job 最多 `NUM_CORES=128`
  - `MAKE_JOBS=3` 或 `4` 时每个 job 最多 `NUM_CORES=64`
  - `MAKE_JOBS` 不得超过 `4`

## Stage 2 精度与时序规则（2026-04-24 legacy; updated by Cadence r28 handoff）

- 当前 accepted Stage 2 handoff 是 Cadence/full-ASAP7 r28 `PG-open / DRC-open / routed-SDF-waived thermal proxy`，时序目标仍为 `200 MHz`，对应 `5.000 ns` 时钟周期。旧 `500 MHz` / `2.000 ns` 仅作为历史默认记录，不用于本轮执行。
- 默认 SDC 不再固定为旧 `physical/stage2_tiled_matmul_os_baseline_asap7/constraint.sdc`；Cadence Stage 2 约束和 handoff evidence 以 r28 run folder 及 reports/stage2_cadence_asap7_phase2_handoff_20260513.md 为准。
- 除调试工具调用、一次性 smoke 排障外，正式开发默认配置中不允许保留以下降质参数：
  - `-noshare`
  - `SKIP_LAST_GASP`
  - 以及其他明确以“加速 smoke / 降低综合或布局布线质量”为目的的参数
- 如果为了调试临时使用这些参数，必须：
  1. 不写入正式默认 config
  2. 在问题记录中写明原因、命令和影响

## 线程探索隔离规则（2026-04-24）

为避免污染主仓库，综合/布局布线线程探索默认使用 `/tmp` 下的 ORFS 临时副本，例如：

```bash
rm -rf /tmp/orfs_mt_sandbox
cp -a third_party/OpenROAD-flow-scripts/flow /tmp/orfs_mt_sandbox/flow
```

实验 logs / results / reports / objects 统一留在 `/tmp/orfs_mt_sandbox/flow`，主仓库只回写文档结论，不保留临时 flow 产物。

## 多线程实测补充（2026-04-24）

已完成的隔离实测包括：

- `nangate45/aes synth`:
  - `NUM_CORES=1` 总耗时 `42.42s`
  - `NUM_CORES=8` 总耗时 `42.53s`
  - 这只代表本次测试没有观察到综合侧性能收益
- `nangate45/aes 3_3_place_gp`:
  - `NUM_CORES=1` 日志记录 `Using 1 thread(s).`，`global_placement` 用时 `66s`
  - `NUM_CORES=8` 日志记录 `Using 8 thread(s).`，`global_placement` 用时 `70s`
  - 这只代表本次测试没有观察到 placement wall time 收益

因此当前工程建议是：

- 实际开发仍优先使用多线程
- 默认从 `16` 线程开始尝试
- 如果耗时仍特别长，再按 stage 和设计逐步提高线程数，最高 `128`
- 不要假设综合天然支持多线程收益
- 不要假设 OpenROAD `-threads` 在所有 stage 都自动提速
- 重要 stage 仍应优先做隔离对比

## ATSim3D 本地安装记录（2026-05-03）

按用户要求已将 ATSim3D public repo 安装为本地第三方工具：

- 源码路径：`third_party/ATSim3D_pub`
- 远端：`git@github.com:Brilight/ATSim3D_pub.git`
- commit：`8454f719409a6d0b1759602e89601f8ae18b95c2`
- 项目入口脚本：`scripts/run_atsim3d.sh`
- 专用运行时：`tools/atsim3d-py38`

ATSim3D 发布包中 `src/ATSim3D.py` 是源码，但核心模块以 Python 3.8 `.pyc` 发布。项目主环境 `thermal_placement` 当前为 Python 3.11.15，直接运行会报 `ImportError: bad magic number in 'ATSimCore': b'U\r\r\n'`。为避免降级或破坏主项目环境，本工具使用隔离的本地 conda prefix `tools/atsim3d-py38`，仅用于 ATSim3D。常规项目 Python 脚本仍必须使用 `thermal_placement` 环境。

已安装到 `tools/atsim3d-py38` 的 Python 包：

| 包 | 版本 | 用途 |
| --- | --- | --- |
| Python | `3.8.20` | 匹配 ATSim3D `.pyc` bytecode |
| numpy | `1.24.4` | 数值数组 |
| pandas | `2.0.3` | CSV/config 数据处理 |
| scipy | `1.10.1` | 稀疏矩阵/求解相关依赖 |
| tqdm | `4.67.3` | 进度显示 |
| matplotlib | `3.7.5` | 图形依赖 |
| psutil | `7.2.2` | ATSim3D 隐含运行依赖，README 未列出 |

安装命令记录：

```bash
rm -rf tools/atsim3d-py38
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  /home/lisihang/miniconda3/bin/conda create -y \
  -p /home/lisihang/thermal_placement/tools/atsim3d-py38 python=3.8 pip

env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  tools/atsim3d-py38/bin/python -m pip install \
  'numpy<2' 'pandas<2.1' 'scipy<1.11' tqdm 'matplotlib<3.8' psutil
```

验证命令：

```bash
scripts/run_atsim3d.sh --help

timeout 600 scripts/run_atsim3d.sh \
  --lcfFile third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.csv \
  --ConfigFile third_party/ATSim3D_pub/2DIC/Intel.config \
  --SimParamsFile third_party/ATSim3D_pub/2DIC/SimParms.config
```

验证结果：`--help` 正常；2DIC、Mono3D、TSV3D 三个 README 示例均完成，生成 7 个 `.res` 文件。示例运行时 TSV3D 会打印 `Unifrom grids cannot be formed. Choose a multiple of 2 or 5 as rows&columns`，但流程继续完成并写出结果。

工具作用、输入输出和论文对应关系详见 `docs/atsim_tool_guide.md`。

## ATSim3D v2 二进制安装记录（2026-05-03）

用户提供的根目录二进制 `ATSim3_5D` 来源于 `third_party/ATSim3D_pub/README.md` 中的 v2 下载说明：

```text
Binary Download from https://disk.pku.edu.cn/link/AAAF77D1F3BA234AF5BD049F6AE5D02843
Name: ATSim3_5D
Usage: ./ATSim3_5D -xml <XmlFile> -config <ConfigFile> --output_path
```

当前已移动到本地工具载荷目录：

- 二进制路径：`tools/atsim3d-bin/ATSim3_5D`
- 项目入口脚本：`scripts/run_atsim3_5d.sh`
- 文件类型：ELF 64-bit x86-64 executable, dynamically linked
- SHA256：`48322878d509432d8bff8799e1111c6347a174f01b9da454430a0bd80539f121`

`ldd tools/atsim3d-bin/ATSim3_5D` 当前只依赖系统基础库：`libdl.so.2`、`libz.so.1`、`libpthread.so.0`、`libc.so.6` 和 loader `/lib64/ld-linux-x86-64.so.2`，没有发现 missing shared library。

Wrapper 会在系统存在 `/etc/fonts/fonts.conf` 时设置 `FONTCONFIG_FILE`，避免二进制启动时打印 `Fontconfig error: Cannot load default config file`。

验证命令：

```bash
bash -n scripts/run_atsim3_5d.sh
ldd tools/atsim3d-bin/ATSim3_5D
timeout 20 scripts/run_atsim3_5d.sh --help
timeout 20 scripts/run_atsim3_5d.sh \
  -xml /tmp/missing.xml \
  -config /tmp/missing.config \
  --output_path /tmp/atsim3_5d_missing
```

验证结果：`--help` 返回状态 `0`，打印参数 `-xml`、`-config`、`--output_path`、`--plot_flag`、`--save_freq`；缺失 XML 输入时返回状态 `1` 并明确报 `XML file /tmp/missing.xml not found`。2026-05-03 进一步从二进制内嵌入口和错误路径确认：XML 至少需要 `MaterialLib File="..."`，`power_type = value` 可通过 XML `Power File="..."` 读取 `UnitName,Power_dyn,Power_leak` CSV，config 至少包含 `[Simulation]` 和 `[MeshConfig]`。当前 public repo 未提供完整 v2 XML/config/material/power/floorplan 示例，端到端 ATSim3_5D 热仿真仍需要补齐匹配 v2 schema 的完整输入集；已确认字段见 `docs/atsim_tool_guide.md`。
