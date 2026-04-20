# Gemmini Thermal Validation Environment

更新时间：2026-04-20

项目根目录：`/home/lisihang/thermal_placement`

## 使用方式

每次进入项目后先执行：

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

该脚本会激活 conda 环境 `thermal_placement`，并配置 Verilator、OpenSTA、HotSpot、OpenROAD、Yosys、sbt、Chipyard/Gemmini 相关路径。

## Git 忽略策略

`.gitignore` 只保留少量必要规则，避免误忽略实验结果和记录类文件。核心规则：

- `third_party/` 被忽略：Chipyard、Gemmini 子模块、OpenROAD/OpenSTA/HotSpot/Verilator 源码树不入库。
- `tools/*` 被忽略：本地安装的工具、预编译包、下载缓存不入库。
- `tools/env_gemmini_thermal.sh` 例外保留：这是项目环境入口脚本，不是工具载荷。
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
- 已验证 Python 包：`numpy 2.4.4`、`pandas 3.0.2`、`matplotlib 3.10.8`、`pyyaml 6.0.3`、`scipy 1.17.1`、`pyvcd`、`vcdvcd`

验证命令：

```bash
/home/lisihang/miniconda3/bin/conda run -n thermal_placement python -c "import numpy,pandas,matplotlib,yaml,scipy,vcd,vcdvcd; print('python ok')"
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
| OpenROAD-flow-scripts | 已下载源码包 | `third_party/OpenROAD-flow-scripts` | archive `bdb262792fef3797730e1b8341b946426272dcdc` |
| OpenROAD | 预编译本地安装可运行；源码也已拉取 | `tools/openroad-prebuilt/root/usr/bin/openroad`，`third_party/OpenROAD` | binary `v2.0-17598-ga008522d8`，source `48d687f` |
| Yosys / yosys-slang | 通过 oss-cad-suite 本地安装 | `tools/oss-cad-suite/oss-cad-suite/bin/yosys` | Yosys `0.64+68`，suite `2026-04-19` |
| CUDD | 已源码构建，供 OpenSTA 使用 | `tools/cudd` | `3.0.0` |
| Eigen | 已安装，供 OpenSTA 使用 | `tools/eigen` | `3.4.0` |

## 验证命令

执行：

```bash
source tools/env_gemmini_thermal.sh
python -c "import numpy,pandas,matplotlib,yaml,scipy,vcd,vcdvcd; print('python ok')"
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

- Python 包导入正常。
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

对照 `docs/gemmini_thermal_validation_plan.md` 第 2 节和第 14 节 Step 1，本阶段属于“环境就绪”，必须工具已配置如下：

| 计划要求 | 当前状态 | 说明 |
| --- | --- | --- |
| Chipyard + Gemmini | 已配置 | `third_party/chipyard` 已拉取；Gemmini、Rocket-Chip、Hardfloat、Diplomacy、TestChipIP、gemmini-rocc-tests 主路径依赖已补齐。 |
| Verilator | 已配置 | 本地源码构建安装到 `tools/verilator`，可执行 `verilator --version` 和 lint smoke test。 |
| gemmini-rocc-tests | 已配置 | `software/gemmini-rocc-tests`、`riscv-tests/env`、`rocc-software` 已补齐。 |
| Python 3 + VCD/数据处理库 | 已配置 | conda env `thermal_placement`，已验证 `pyvcd`、`vcdvcd`、`numpy`、`pandas`、`matplotlib`、`scipy`、`pyyaml`。 |
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
configs/openroad/
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
