# Tool and Environment Inventory

更新时间：2026-05-15

盘点根目录：`/home/lisihang/thermal_placement`

本文件基于仓库内目录、脚本、环境入口和实际命令输出整理。没有证据的项目标为“未确认”或“未发现”。

2026-05-15 更新：本机 active Verilator 为 `5.047 devel rev vUNKNOWN-built20260420-e82bd52`，已通过 `source tools/env_gemmini_thermal.sh && verilator --help` 确认支持正式 Phase1b gate-SAIF handoff 所需的 `--trace-saif`、`--verilate-jobs`、`--output-split-ctrace`、`--output-split`、`--output-split-cfuncs`、`--threads`、`--trace-depth`、`--compiler` 和 `--no-timing`。正式 Phase1b 默认不使用 `--hierarchical`。


2026-04-27 更新：项目 Python 命令统一使用 conda 环境 `thermal_placement`。若项目脚本、数据处理、可视化或测试需要新增 Python 包，允许安装到该环境，并记录包名、版本、用途和验证命令；不要安装到 base 或系统 Python。

2026-04-23 更新：2026-04-22 已补齐 PACT、serial Xyce、OpenMPI、slang、sv2v 和 yosys-slang，详见 [pact_slang_sv2v_yosys_slang_install_report.md](/home/lisihang/thermal_placement/docs/pact_slang_sv2v_yosys_slang_install_report.md) 与归档 handoff [repository_handoff_2026-04-23.md](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23/repository_handoff_2026-04-23.md)。本文件原 2026-04-20 记录中“未发现”的相关项目已经按下面摘要修正。

## 1. 实际运行的检查命令

已执行的安全检查包括：

```bash
pwd
ls -la
find third_party tools -maxdepth 3 -mindepth 1 -type d
find . -maxdepth 3 \( -iname 'env*.sh' -o -iname 'README*' -o -iname 'Makefile' -o -iname 'CMakeLists.txt' -o -iname '*build*.sh' -o -iname '*.mk' \) -type f
source tools/env_gemmini_thermal.sh
command -v <tool>
<tool> --version / -version / -V / -h
git -C <repo> rev-parse --short HEAD
rg -n <tool-name> tools scripts docs README.md third_party
```

## 2. 环境脚本配置

入口脚本：

- [env_gemmini_thermal.sh](/home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh)

`source tools/env_gemmini_thermal.sh` 后确认：

| 变量 | 当前值 |
| --- | --- |
| `TP_ROOT` | `/home/lisihang/thermal_placement` |
| `CHIPYARD_HOME` | `/home/lisihang/thermal_placement/third_party/chipyard` |
| `GEMMINI_HOME` | `/home/lisihang/thermal_placement/third_party/chipyard/generators/gemmini` |
| `HOTSPOT_HOME` | `/home/lisihang/thermal_placement/third_party/HotSpot` |
| `FLOW_HOME` | `/home/lisihang/thermal_placement/third_party/OpenROAD-flow-scripts/flow` |
| `CADENCE_HOME` | `/opt/eda/Cadence_DDI_23.14` |
| `CDS_LIC_FILE` | `/opt/eda/Cadence_DDI_23.14/license/license.dat` |
| `ASAP7_HOME` | `/home/lisihang/asap7` |
| `ASAP7_STDCELL_VERSION` | `asap7sc7p5t_28` |
| `ASAP7_LIB_CACHE` | `/home/lisihang/thermal_placement/.cache/asap7/asap7sc7p5t_28/NLDM` |
| `ASAP7_FULL_CONFIG` | `/home/lisihang/thermal_placement/configs/asap7_full/asap7_full.tcl` |
| `CIRCT_HOME` | `/home/lisihang/thermal_placement/tools/circt` |
| `RISCV` | `/home/lisihang/thermal_placement/tools/riscv` |
| `VERILATOR_PREFIX` | `/home/lisihang/thermal_placement/tools/verilator` |
| `OPENSTA_HOME` | `/home/lisihang/thermal_placement/tools/opensta` |
| `OSS_CAD_SUITE` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite` |
| `OPENROAD_PREBUILT_ROOT` | `/home/lisihang/thermal_placement/tools/openroad-prebuilt/root` |
| `SBT_HOME` | `/home/lisihang/thermal_placement/tools/sbt/sbt` |
| `FAKE_SRAM_HOME` | `/home/lisihang/fake_sram` |
| `FAKE_SRAM_ASAP7_ROOT` | `/home/lisihang/fake_sram/results/asap7` |
| `FAKE_SRAM_CADENCE_CACHE` | `/home/lisihang/thermal_placement/.cache/fake_sram/asap7` |
| `FAKE_SRAM_DESIGN` | `Gemmini` |
| `FAKE_SRAM_ASAP7_CONFIG` | `/home/lisihang/thermal_placement/configs/fake_sram/asap7_fake_sram.tcl` |
| `TP_CADENCE_GENUS_CPUS` | default `8` |
| `TP_CADENCE_INNOVUS_CPUS` | default `8` |
| `MAKE_JOBS` | `128` legacy generic build default; explicitly override to `<=4` for ORFS/backend tasks |

Notes:

- The environment script still records a legacy generic build default for `MAKE_JOBS`. For ORFS/backend Stage 2/3 work, do not use that default directly; set `MAKE_JOBS` explicitly according to the backend policy below.
- Active Cadence Stage 2 uses `TP_CADENCE_GENUS_CPUS` and `TP_CADENCE_INNOVUS_CPUS`; do not map OpenROAD `MAKE_JOBS` / `NUM_CORES` semantics onto Genus/Innovus.

PATH 已包含：

- `tools/bin`
- `tools/circt/bin`
- `tools/sbt/sbt/bin`
- `tools/verilator/bin`
- `tools/opensta/bin`
- `third_party/HotSpot`
- `tools/oss-cad-suite/oss-cad-suite/bin`
- `tools/openroad-prebuilt/root/usr/bin`
- `tools/riscv/bin`
- conda env `thermal_placement/bin`

## 3. 已确认可执行的工具

| 工具名 | 版本 / commit | 路径 | 类型 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- |
| Python | `3.11.15` | `/home/lisihang/miniconda3/envs/thermal_placement/bin/python` | 脚本环境 | 确认可执行 | `python --version` |
| pip | `26.0.1` | `/home/lisihang/miniconda3/envs/thermal_placement/bin/pip` | 脚本环境 | 确认可执行 | `pip --version` |
| conda | `26.1.1` | conda shell function / miniconda | 脚本环境 | 确认可执行 | `conda --version` |
| numpy | `2.4.4` | conda env | Python 依赖库 | 确认可导入 | `python -c 'import numpy'` |
| pandas | `3.0.2` | conda env | Python 依赖库 | 确认可导入 | `python -c 'import pandas'` |
| matplotlib | `3.10.8` | conda env | Python 依赖库 | 确认可导入 | `python -c 'import matplotlib'` |
| Pillow | `12.1.1` | conda env `thermal_placement` | Python 图像依赖库 | 确认可导入 | `python -c 'import PIL'` |
| seaborn | `0.13.2` | conda env `thermal_placement` | Python 可视化依赖库 | 确认可导入 | `python -c 'import seaborn'` |
| pyyaml | `6.0.3` | conda env | Python 依赖库 | 确认可导入 | `python -c 'import yaml'` |
| loguru | `0.7.3` | conda env `thermal_placement` | edahub Python 依赖库 | 确认可导入 | `python -c 'import loguru'` |
| networkx | `3.4.1` | conda env `thermal_placement` | dacs-lab 设计生成依赖 | 确认可导入 | `python -c 'import networkx'` |
| pytest | `9.0.3` | conda env `thermal_placement` | edahub 测试依赖 | 定向测试通过 | `python -m pytest tests/technology/test_pdk.py -k ...` |
| pytest-cov | `7.1.0` | conda env `thermal_placement` | edahub 测试依赖 | pytest plugin 可加载 | `pytest --version` |
| pytest-xdist | `3.8.0` | conda env `thermal_placement` | edahub 并行测试依赖 | pytest plugin 可加载 | `pytest --version` |
| pre-commit | `4.6.0` | conda env `thermal_placement` | edahub 开发依赖 | 已安装 | `pre-commit --version` |
| flake8 | `7.3.0` | conda env `thermal_placement` | edahub lint 依赖 | 已安装 | `flake8 --version` |
| scipy | `1.17.1` | conda env | Python 依赖库 | 确认可导入 | `python -c 'import scipy'` |
| pyvcd | version 未确认 | conda env | VCD 解析依赖 | 确认可导入 | `python -c 'import vcd'` |
| vcdvcd | version 未确认 | conda env | VCD 解析依赖 | 确认可导入 | `python -c 'import vcdvcd'` |
| sbt launcher | `1.12.9` | `/home/lisihang/thermal_placement/tools/sbt/sbt/bin/sbt` | 构建工具 | 确认可执行 | `sbt --script-version` |
| Java | OpenJDK `11.0.30` | `/usr/bin/java` | 构建工具 | 确认可执行 | `java -version` |
| Verilator | `5.047 devel`, source `e82bd52` | `/home/lisihang/thermal_placement/tools/verilator/bin/verilator` | 仿真 | 确认可执行 | `verilator --version` |
| verilator_coverage | 同 Verilator 安装 | `/home/lisihang/thermal_placement/tools/verilator/bin/verilator_coverage` | 仿真/覆盖率 | 确认可执行 | `command -v verilator_coverage` |
| CIRCT firtool | `firtool-1.75.0`, LLVM `19.0.0git` | `/home/lisihang/thermal_placement/tools/circt/bin/firtool` | RTL lowering / FIRRTL | 确认可执行 | `firtool --version` |
| circt-opt | `firtool-1.75.0`, LLVM `19.0.0git` | `/home/lisihang/thermal_placement/tools/circt/bin/circt-opt` | RTL/MLIR 工具 | 确认可执行 | `circt-opt --version` |
| Yosys | `0.64+68`, git `413169663` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/yosys` | 综合 | 确认可执行 | `yosys -V` |
| OpenROAD | `v2.0-17598-ga008522d8` | `/home/lisihang/thermal_placement/tools/openroad-prebuilt/root/usr/bin/openroad` | P&R | 确认可执行 | `openroad -version` |
| OpenSTA | `3.1.0` | `/home/lisihang/thermal_placement/tools/opensta/bin/sta` | STA | 确认可执行 | `sta -version` |
| Cadence Genus | `23.14-s090_1` | `/opt/eda/Cadence_DDI_23.14/bin/genus` | 商业综合 | 确认可执行 | `genus -version` and license smoke |
| Cadence Innovus | `v23.14-s088_1` | `/opt/eda/Cadence_DDI_23.14/bin/innovus` | 商业布局布线 | 确认可执行 | `innovus -version` and license smoke |
| HotSpot | version 未打印；source `f18831e` | `/home/lisihang/thermal_placement/third_party/HotSpot/hotspot` | 热仿真 | 确认可执行 | `hotspot -h` |
| hotfloorplan | version 未确认 | `/home/lisihang/thermal_placement/third_party/HotSpot/hotfloorplan` | 热/平面图辅助 | 确认存在可执行 | `find third_party/HotSpot -perm -111` |
| RISC-V GCC | `10.2.0` | wrapper: `/home/lisihang/thermal_placement/tools/bin/riscv64-unknown-elf-gcc`; real: `/home/lisihang/thermal_placement/tools/riscv/bin/riscv64-unknown-elf-gcc` | 编译器 | 确认可执行 | `riscv64-unknown-elf-gcc --version` |
| RISC-V G++ | `10.2.0` | wrapper: `/home/lisihang/thermal_placement/tools/bin/riscv64-unknown-elf-g++`; real: `/home/lisihang/thermal_placement/tools/riscv/bin/riscv64-unknown-elf-g++` | 编译器 | 确认可执行 | `riscv64-unknown-elf-g++ --version` |
| RISC-V binutils | version 未逐项确认 | `/home/lisihang/thermal_placement/tools/riscv/bin/riscv64-unknown-elf-{as,ld,objdump,readelf,...}` | 编译器/工具链 | 确认存在可执行 | `find tools/riscv/bin -perm -111` |
| Spike | `1.1.1-dev` | `/home/lisihang/thermal_placement/tools/riscv/bin/spike` | RISC-V ISA 仿真 | 确认可执行 | `spike --help` |
| spike-dasm | version 未确认 | wrapper: `/home/lisihang/thermal_placement/tools/bin/spike-dasm` | RISC-V 反汇编辅助 | 确认可执行 | `command -v spike-dasm` |
| jq wrapper | version 未确认 | `/home/lisihang/thermal_placement/tools/bin/jq` | 脚本依赖 | 确认可执行 | `file tools/bin/jq` |
| Icarus Verilog | `14.0 devel` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/iverilog` | 仿真 | 确认可执行 | `iverilog -V` |
| GTKWave | version 未确认；启动时尝试写 `$HOME/.config` 失败 | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/gtkwave` | 波形查看 | 发现可执行但运行有 HOME 写入警告 | `gtkwave --version` 输出 mkdir 错误 |
| fst2vcd | version 未确认 | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/fst2vcd` | 波形转换 | 确认可执行 | `fst2vcd --help` |
| vcd2fst | version 未确认 | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/vcd2fst` | 波形转换 | 确认可执行 | `command -v vcd2fst` |
| nextpnr-ice40 | version 未确认；运行时尝试写 `$HOME/.config` 失败 | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/nextpnr-ice40` | FPGA P&R | 发现可执行但运行有 HOME 写入警告 | `nextpnr-ice40 --version` |
| nextpnr-ecp5 | version 未确认 | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/nextpnr-ecp5` | FPGA P&R | 确认存在可执行 | `command -v nextpnr-ecp5` |
| cvc5 | `1.0.1-dev.2.77d0bec48` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/cvc5` | SMT/formal | 确认可执行 | `cvc5 --version` |
| bitwuzla | `1.0-prerelease` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/bitwuzla` | SMT/formal | 确认可执行 | `bitwuzla --version` |
| z3 | `4.15.5` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/z3` | SMT/formal | 确认可执行 | `z3 --version` |
| GNU Make | `4.3` | `/usr/bin/make` | 构建工具 | 确认可执行 | `make --version` |
| CMake | `3.22.1` | `/usr/bin/cmake` | 构建工具 | 确认可执行 | `cmake --version` |
| Ninja | `1.10.1` | `/usr/bin/ninja` | 构建工具 | 确认可执行 | `ninja --version` |
| GCC | `11.4.0` | `/usr/bin/gcc` | 编译器 | 确认可执行 | `gcc --version` |
| G++ | `11.4.0` | `/usr/bin/g++` | 编译器 | 确认可执行 | `g++ --version` |
| Git | `2.34.1` | `/usr/bin/git` | 构建/版本管理 | 确认可执行 | `git --version` |
| Bash | `5.1.16` | shell | 脚本环境 | 确认可执行 | `bash --version` |
| ripgrep | `15.1.0` | system PATH | 脚本/搜索工具 | 确认可执行 | `rg --version` |
| GNU findutils | `4.8.0` | system PATH | 脚本/搜索工具 | 确认可执行 | `find --version` |
| GNU coreutils timeout | `8.32` | system PATH | 脚本工具 | 确认可执行 | `timeout --version` |

## 4. 已 vendored 或已发现目录的工具 / 软件

| 工具 / 软件 | 版本 / commit | 路径 | 类型 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- |
| Chipyard | commit `63c1506` | `/home/lisihang/thermal_placement/third_party/chipyard` | SoC/RTL 生成框架 | 已 vendored，非单一可执行 | `git -C third_party/chipyard rev-parse --short HEAD` |
| Gemmini | commit `6ad65b9` | `/home/lisihang/thermal_placement/third_party/chipyard/generators/gemmini` | Tensor accelerator generator | 已 vendored，脚本引用 | `GEMMINI_HOME`、`git rev-parse` |
| gemmini-rocc-tests | commit 见 Chipyard 子模块；文档记录 `7c540b3`，本次未单独查询 | `/home/lisihang/thermal_placement/third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests` | Gemmini 软件测试 | 已 vendored，构建脚本引用 | `scripts/build_gemmini_workloads.sh` |
| Rocket Chip / Chisel deps | version 未逐项确认 | `/home/lisihang/thermal_placement/third_party/chipyard/generators/rocket-chip` | RTL generator 依赖 | 已 vendored，Chipyard 依赖 | `scripts/check_environment.sh` required paths |
| DRAMSim2 | version 未确认 | `/home/lisihang/thermal_placement/third_party/chipyard/tools/DRAMSim2` | 仿真内存模型 | 已 vendored，仿真脚本引用 ini | `+dramsim_ini_dir=.../dramsim2_ini` |
| OpenROAD source | commit `48d687f` | `/home/lisihang/thermal_placement/third_party/OpenROAD` | P&R 源码 | 仅发现源码目录；实际执行使用 prebuilt | `git -C third_party/OpenROAD rev-parse --short HEAD` |
| OpenROAD-flow-scripts | archive/源码目录；docs 记录 `bdb262792fef3797730e1b8341b946426272dcdc` | `/home/lisihang/thermal_placement/third_party/OpenROAD-flow-scripts` | P&R flow | 已发现目录，Makefile flow 存在 | `FLOW_HOME`、`third_party/OpenROAD-flow-scripts/env.sh` |
| edahub reduced techlibs | `thermal-placement-mini-pdks` 分支 | `/home/lisihang/thermal_placement/third_party/edahub`，适配入口 `/home/lisihang/thermal_placement/configs/reduced_techlibs`、`/home/lisihang/thermal_placement/configs/openroad/reduced_platforms` | reduced PDK/标准单元库适配 | asap7、nangate45、sky130hd 已验证文件存在；非完整 PDK | `scripts/check_edahub_reduced_techlibs.py` |
| Full ASAP7 PDK | external checkout | `/home/lisihang/asap7` | active Cadence PDK source | `asap7sc7p5t_28` 1x LEF/QRC and `.lib.7z` NLDM archives confirmed | `scripts/prepare_asap7_liberty_cache.py --check-only` |
| OpenSTA source | version `3.1.0` 从可执行确认 | `/home/lisihang/thermal_placement/third_party/OpenSTA` | STA 源码 | 仅发现源码目录；实际执行使用 `tools/opensta/bin/sta` | `ls -ld third_party/OpenSTA` |
| Verilator source | commit `e82bd52` | `/home/lisihang/thermal_placement/third_party/verilator` | 仿真器源码 | 已 vendored；实际执行使用 `tools/verilator/bin/verilator` | `git -C third_party/verilator rev-parse --short HEAD` |
| HotSpot source/build | commit `f18831e` | `/home/lisihang/thermal_placement/third_party/HotSpot` | 热仿真 | 源码目录且已构建可执行 | `hotspot -h`、`git rev-parse` |
| ATSim3D public repo | commit `8454f719409a6d0b1759602e89601f8ae18b95c2` | `/home/lisihang/thermal_placement/third_party/ATSim3D_pub` | 热仿真/3D IC steady-state simulator | 已 vendored；核心模块为 Python 3.8 `.pyc` | `git -C third_party/ATSim3D_pub rev-parse HEAD`; `scripts/run_atsim3d.sh --help` |
| ATSim3D v2 binary `ATSim3_5D` | SHA256 `48322878d509432d8bff8799e1111c6347a174f01b9da454430a0bd80539f121` | `/home/lisihang/thermal_placement/tools/atsim3d-bin/ATSim3_5D` | ATSim3D v2 binary thermal simulator | 已安装为本地二进制工具载荷；XML/config interface | `ldd tools/atsim3d-bin/ATSim3_5D`; `scripts/run_atsim3_5d.sh --help` |
| CUDD source mirror | commit `c8d587e` | `/home/lisihang/thermal_placement/third_party/cudd` | 依赖库 | 已 vendored | `git -C third_party/cudd rev-parse --short HEAD` |
| CUDD release tree | `3.0.0` | `/home/lisihang/thermal_placement/third_party/cudd-3.0.0` | 依赖库 | 已发现目录；构建产物另在 `tools/cudd` | 目录名、`third_party/cudd-3.0.0/Makefile` |
| CUDD installed lib | `3.0.0` 未命令确认 | `/home/lisihang/thermal_placement/tools/cudd` | 依赖库 | 已安装目录 | `tools/cudd/include`、`tools/cudd/lib` |
| Eigen source | `3.4.0` | `/home/lisihang/thermal_placement/third_party/eigen-3.4.0` | 依赖库 | 已 vendored | `Eigen/src/Core/util/Macros.h` |
| Eigen installed | `3.4.0` | `/home/lisihang/thermal_placement/tools/eigen` | 依赖库 | 已安装目录 | `tools/eigen/include`、version macros |
| CIRCT/LLVM tool bundle | `firtool-1.75.0`, LLVM `19.0.0git` | `/home/lisihang/thermal_placement/tools/circt` | RTL/MLIR 工具 | 已安装可执行 bundle | `firtool --version` |
| OSS CAD Suite | suite `20260419` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite` | EDA 工具 bundle | 已安装可执行 bundle | `tools/oss-cad-suite/oss-cad-suite/VERSION` |
| RISC-V bare-metal prefix | GCC `10.2.0`; Spike `1.1.1-dev` | `/home/lisihang/thermal_placement/tools/riscv` | 编译器/ISA 仿真 | 已安装可执行 bundle | `riscv64-unknown-elf-gcc --version`、`spike --help` |
| OpenROAD prebuilt root | OpenROAD `v2.0-17598-ga008522d8` | `/home/lisihang/thermal_placement/tools/openroad-prebuilt/root` | P&R/运行库 bundle | 已安装可执行 | `openroad -version` |
| Download cache | version 不适用 | `/home/lisihang/thermal_placement/tools/downloads` | 下载缓存 | 仅发现目录 | `find tools -maxdepth 2` |
| ATSim3D Python 3.8 runtime | Python `3.8.20`; numpy `1.24.4`; pandas `2.0.3`; scipy `1.10.1`; tqdm `4.67.3`; matplotlib `3.7.5`; psutil `7.2.2` | `/home/lisihang/thermal_placement/tools/atsim3d-py38` | ATSim3D 专用 Python 运行时 | 已安装并通过示例 smoke | `tools/atsim3d-py38/bin/python -c ...`; `scripts/run_atsim3d.sh ...` |

## 4.1 Fake SRAM collateral

2026-05-05 added external fake SRAM collateral from `/home/lisihang/sram_gen.zip`. For the active Cadence/Gemmini route, `/home/lisihang/fake_sram` is used as a generation-method reference only; the flow does not directly consume the old generated RISCY/Vortex/NVDLA macro types.

| 项目 | 状态 | 路径 / 入口 | 验证 |
| --- | --- | --- | --- |
| Fake SRAM source tree | 已解压到外部路径并切到 thermal_placement 分支；active route 只参考其生成方法 | `/home/lisihang/fake_sram/` | source tree exists |
| External ASAP7 fake SRAM results | 仅作为 legacy/input inventory，不是 active Gemmini macro 来源 | `/home/lisihang/fake_sram/results/asap7` | optional `scripts/check_fake_sram_collateral.py` |
| Gemmini fake SRAM generator | 已添加；从当前 RTL 可达 memory externs 生成 active collateral | `scripts/prepare_gemmini_fake_sram_collateral.py` | generated `mem_ext`, `mem_0_ext` |
| Gemmini fake SRAM cache | 已生成 | `.cache/fake_sram/asap7/Gemmini` | Liberty/LEF/Verilog stub/manifest exist |
| Bash env vars | 已加入环境入口 | `FAKE_SRAM_HOME`, `FAKE_SRAM_ASAP7_ROOT`, `FAKE_SRAM_ASAP7_CONFIG` | `source tools/env_gemmini_thermal.sh` |
| Make manifest | 已添加 | `configs/fake_sram/asap7_fake_sram.mk` | `make -f configs/fake_sram/asap7_fake_sram.mk FAKE_SRAM_DESIGN=Gemmini print-fake-sram-asap7` |
| Cadence Tcl manifest | 已添加 | `configs/fake_sram/asap7_fake_sram.tcl` | Genus `read_libs`; Innovus `read_physical -lef` |
| Legacy Cadence cache adapter | 保留为历史辅助脚本，不是 active route | `scripts/prepare_fake_sram_cadence_cache.py` | copies old design LEF/DB and patches Liberty |

The external fake_sram Git branch is `thermal_placement`. The ZIP contained a nested `.git` directory and Python bytecode caches. The extracted external copy preserves its `.git` metadata so it can stay on branch `thermal_placement`; source, config, Python caches from the ZIP, and generated SRAM collateral are kept as provided. Current ASAP7 fake SRAM generated files are LEF, Liberty, and DB only; no GDS files were present in the ZIP.

Validation command:

```bash
source tools/env_gemmini_thermal.sh
python scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini
```

Active Gemmini fake SRAM shapes:

| macro | wrapper | 类型 | depth | width | generated size |
| --- | --- | --- | --- | --- | --- |
| `mem_ext` | `mem` | `1rw` | 4096 | 128 | 109.890 x 220.050 um |
| `mem_0_ext` | `mem_0` | `1r1w` | 512 | 512 | 108.702 x 217.620 um |

## 4.2 Cadence/full-ASAP7 collateral

2026-05-05 active backend changed from OpenROAD/ORFS/reduced-ASAP7 to Cadence Genus + Innovus with external full ASAP7.

| 项目 | 状态 | 路径 / 入口 | 验证 |
| --- | --- | --- | --- |
| Cadence install | 已确认可运行 | `/opt/eda/Cadence_DDI_23.14` | `genus -version`, `innovus -version` |
| License file | 已确认 smoke 可 checkout | `/opt/eda/Cadence_DDI_23.14/license/license.dat` | Genus/Innovus smoke |
| Full ASAP7 external PDK | 已确认存在 | `/home/lisihang/asap7` | `asap7sc7p5t_28` files inspected |
| Full ASAP7 Tcl manifest | 已添加 | `configs/asap7_full/asap7_full.tcl` | Tcl source helper path check |
| Full ASAP7 Make manifest | 已添加 | `configs/asap7_full/asap7_full.mk` | path manifest |
| NLDM Liberty cache script | 已添加 | `scripts/prepare_asap7_liberty_cache.py` | checks/extracts RVT/LVT/SLVT TT |
| Cadence/ASAP7 environment check | 已添加 | `scripts/check_cadence_asap7_environment.sh` | version/path/fake-SRAM preflight |

Active ASAP7 settings:

- `ASAP7_STDCELL_VERSION=asap7sc7p5t_28`
- 1x tech/stdcell LEF
- `qrcTechFile_typ03_unscaledV02`
- NLDM RVT/LVT/SLVT TT
- Liberty extraction cache under `.cache/asap7/`
- CCS is deferred for a later optional route.

Cadence smoke status:

- Genus `23.14-s090_1` successfully read 15 ASAP7 NLDM Liberty files plus generated Gemmini fake SRAM Liberty files for `mem_ext` and `mem_0_ext`.
- Genus tiny synthesis smoke with a top instantiating `mem_ext` completed through `syn_generic` and `write_hdl`.
- Innovus `v23.14-s088_1` successfully read ASAP7 1x tech/stdcell LEF plus generated Gemmini fake SRAM LEF files for `mem_ext` and `mem_0_ext`.

## 5. 当前脚本引用关系

| 脚本 | 引用工具 / 软件 | 证据 |
| --- | --- | --- |
| [check_environment.sh](/home/lisihang/thermal_placement/scripts/check_environment.sh) | Python, sbt, Chipyard, Verilator, Yosys, OpenSTA, OpenROAD, ORFS, HotSpot | `scripts/check_environment.sh` lines invoking each tool |
| [run_atsim3_5d.sh](/home/lisihang/thermal_placement/scripts/run_atsim3_5d.sh) | ATSim3D v2 binary | wraps `tools/atsim3d-bin/ATSim3_5D` and sets `FONTCONFIG_FILE` when available |
| [run_gemmini_rtl_generation.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_rtl_generation.sh) | Chipyard make/sbt, firtool output, Python hierarchy inspection | `SBT_CMD`, `SIM_DIR`, `RUN_ROOT`, `firtool.log`, `inspect_gemmini_hierarchy.py` |
| [inspect_gemmini_hierarchy.py](/home/lisihang/thermal_placement/scripts/inspect_gemmini_hierarchy.py) | Python stdlib, PyYAML, exported RTL collateral | generates narrowed Gemmini PE/control/load-store/scratchpad hierarchy buckets |
| [build_gemmini_workloads.sh](/home/lisihang/thermal_placement/scripts/build_gemmini_workloads.sh) | gemmini-rocc-tests, RISC-V GCC, make | `TEST_ROOT`, `RUN_ROOT`, `riscv64-unknown-elf-gcc` checks |
| [run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh) | Verilator debug simulator, DRAMSim2 ini, Gemmini bare-metal binaries, VCD activity/window/report helpers | `SIM_DIR`, `RUN_ROOT`, `HIERARCHY_MAP`, `TIMEOUT_CYCLES`, `EXTRACT_ACTIVITY`, `analyze_vcd_windows.py`, `report_stage1_activity.py` |
| [build_thermal_smoke_binary.sh](/home/lisihang/thermal_placement/scripts/build_thermal_smoke_binary.sh) | RISC-V GCC, gemmini-rocc-tests common crt/syscalls/linker script | `COMMON`, `riscv64-unknown-elf-gcc` |
| [run_thermal_smoke_flow.sh](/home/lisihang/thermal_placement/scripts/run_thermal_smoke_flow.sh) | Verilator, DRAMSim2, VCD parser, HotSpot | `+vcdfile`, `extract_vcd_activity.py`, `hotspot` |
| [build_small_gemm_binary.sh](/home/lisihang/thermal_placement/scripts/build_small_gemm_binary.sh) | RISC-V GCC, Gemmini headers, bare-metal crt/syscalls | `-I"$TEST_ROOT"`, `riscv64-unknown-elf-gcc` |
| [run_small_gemm_thermal_flow.sh](/home/lisihang/thermal_placement/scripts/run_small_gemm_thermal_flow.sh) | Verilator, DRAMSim2, VCD parser, HotSpot, report script | `+vcdfile`, `extract_vcd_activity.py`, `hotspot` |
| [extract_vcd_activity.py](/home/lisihang/thermal_placement/scripts/extract_vcd_activity.py) | Python stdlib, optional PyYAML | `import yaml`; narrowed Gemmini category priority and short-token classifier |
| [reclassify_vcd_activity.py](/home/lisihang/thermal_placement/scripts/reclassify_vcd_activity.py) | Python stdlib, optional PyYAML through `extract_vcd_activity.py` | reclassifies an existing full signal activity CSV after hierarchy-map/category edits |
| [analyze_vcd_windows.py](/home/lisihang/thermal_placement/scripts/analyze_vcd_windows.py) | Python stdlib CSV/log parsing | writes Stage 1 coarse windows without rescanning huge VCDs |
| [report_stage1_activity.py](/home/lisihang/thermal_placement/scripts/report_stage1_activity.py) | Python stdlib CSV/pathlib | writes per-workload Stage 1 activity report |
| [export_smoke_hotspot_inputs.py](/home/lisihang/thermal_placement/scripts/export_smoke_hotspot_inputs.py) | Python stdlib CSV | `import csv` |
| [report_small_gemm_flow.py](/home/lisihang/thermal_placement/scripts/report_small_gemm_flow.py) | Python stdlib CSV/pathlib | `import csv`, `Path` |

## 6. 关键工具专项检查

| 项目 | 配置状态 | 证据 |
| --- | --- | --- |
| chipyard | 已配置 | `CHIPYARD_HOME=/home/lisihang/thermal_placement/third_party/chipyard`; commit `63c1506` |
| gemmini 相关依赖 | 已配置主路径 | `GEMMINI_HOME=.../generators/gemmini`; `gemmini-rocc-tests` 被 build scripts 引用 |
| verilator | 已配置并可执行 | `command -v verilator`; `Verilator 5.047 devel` |
| yosys | 已配置并可执行 | `command -v yosys`; `Yosys 0.64+68` |
| yosys-slang | 已配置为 Yosys plugin | `yosys -m slang -p 'help read_slang'` 与最小 SystemVerilog smoke 通过；plugin 位于 `$YOSYS_SLANG_PLUGIN` |
| openroad | 已配置并可执行 | `command -v openroad`; `v2.0-17598-ga008522d8` |
| opensta | 已配置并可执行 | `command -v sta`; `3.1.0` |
| hotspot | 已配置并可执行 | `command -v hotspot`; `hotspot -h` 打印 Usage |
| pact | 已配置；无独立 `pact` 命令 | 官方入口为 `python "$PACT_ENTRY" ...`；`--help` 与 PACT SuperLU 示例通过 |
| comsol | 未发现 | `command -v comsol` / `command -v comsolbatch` 无输出；针对 `tools scripts docs README.md third_party` 的 `rg` 无命中 |
| python 环境 | 已配置 | conda env `thermal_placement`; Python `3.11.15`;主要包可导入 |

## 7. 2026-04-23 新增确认的关键工具

| 工具 | 状态 | 证据 | 备注 |
| --- | --- | --- | --- |
| PACT | 已配置 | `python "$PACT_ENTRY" --help`；PACT SuperLU 10 mm 示例输出 layer grid | 官方入口是 Python 脚本，不是 `pact` 二进制 |
| Xyce | 已配置 | `Xyce -v`；最小两器件 SPICE netlist 通过 | 当前为 serial Xyce |
| OpenMPI | 已配置 | `mpirun --version`；`mpirun -np 2 /bin/hostname` 通过 | MPI runtime 可用；PACT parallel mode 仍待 MPI-enabled Xyce |
| slang | 已配置 | `slang --version`；最小 SystemVerilog smoke 通过 | `$SLANG_HOME/bin/slang` |
| sv2v | 已配置 | `sv2v --version`；最小 SystemVerilog 转换通过 | `$SV2V_HOME/bin/sv2v` |
| yosys-slang | 已配置 | `yosys -m slang -p 'help read_slang'`；最小 SystemVerilog synthesis smoke 通过 | plugin file: `$YOSYS_SLANG_PLUGIN` |

## 7.1 仍未发现或暂未纳入当前主流程的工具

| 工具 | 状态 | 证据 | 备注 |
| --- | --- | --- | --- |
| COMSOL | 未发现 | `command -v comsol`、`command -v comsolbatch` 无输出；仓库脚本/docs 未命中 | 当前流程未引用 |
| PACT parallel mode | 暂缓 | serial Xyce 已验证；未构建 MPI-enabled Xyce/Trilinos | 不影响当前 serial PACT 与 HotSpot 主线 |

## 7.2 2026-04-26 Stage 4 thermal tool recheck

Phase 4 preflight rechecked the thermal tools in the active environment after `source tools/env_gemmini_thermal.sh`:

| Tool/check | Result | Current Phase 4 interpretation |
| --- | --- | --- |
| `python "$PACT_ENTRY" --help` | Passed | PACT entry supports positional `lcfFile configFile modelParamsFile` plus `--init`, `--steady`, and `--gridSteadyFile`. |
| PACT SuperLU example | Passed | Example steady run generated `/tmp/tp_phase4_pact_smoke/superlu_10mm.grid.steady.layer0` and `.layer1`, each with `1600` numeric grid entries. |
| `hotspot -h` and tiny two-block run | Passed | HotSpot executable works and can generate `.ttrace` from minimal `.flp/.ptrace`. |
| `Xyce -v` | Passed | Reports `Xyce Release 7.4.0-opensource`; current build is serial. |
| `mpirun -np 2 /bin/hostname` | Passed | OpenMPI runtime works, but PACT parallel mode is not accepted because Xyce is serial. |

Stage 4 threading decision: PACT SPICE modelParams must use `number_of_core = 1` for the current formal route. `MAKE_JOBS` / `NUM_CORES` environment defaults are not PACT solver-thread controls. HotSpot is treated as single-process for the coarse comparison.

## 8. 总结表

### 8.1 已安装并确认可执行

| 类别 | 工具 |
| --- | --- |
| RTL/SoC 生成 | Chipyard via sbt/make, Gemmini source, CIRCT `firtool` |
| 仿真 | Verilator, Verilator debug simulator binary, Icarus Verilog, Spike |
| 综合 | Yosys |
| P&R | OpenROAD, nextpnr-ice40, nextpnr-ecp5 |
| STA | OpenSTA `sta` |
| 热仿真 | HotSpot `hotspot`, `hotfloorplan`, PACT via `python "$PACT_ENTRY"`, serial Xyce |
| 编译器 | RISC-V GCC/G++, RISC-V binutils, system GCC/G++ |
| 构建工具 | sbt, Java, Make, CMake, Ninja, Git, Bash, OpenMPI `mpirun`/`mpicc`, libtool |
| Python/数据处理 | Python 3.11.15, numpy, pandas, matplotlib, Pillow, seaborn, scipy, pyyaml, pyvcd, vcdvcd |
| 波形/形式化辅助 | fst2vcd, vcd2fst, slang, sv2v, yosys-slang, GTKWave executable present with HOME warning, cvc5, bitwuzla, z3 |

### 8.2 仅发现目录或源码，未作为当前 PATH 主可执行确认

| 工具 / 软件 | 路径 | 说明 |
| --- | --- | --- |
| OpenROAD source | `/home/lisihang/thermal_placement/third_party/OpenROAD` | 源码目录存在；执行使用 prebuilt OpenROAD |
| OpenSTA source | `/home/lisihang/thermal_placement/third_party/OpenSTA` | 源码目录存在；执行使用 `tools/opensta/bin/sta` |
| OpenROAD-flow-scripts source | `/home/lisihang/thermal_placement/third_party/OpenROAD-flow-scripts` | Makefile flow 存在；不是单一命令 |
| CUDD source/release | `/home/lisihang/thermal_placement/third_party/cudd`, `/home/lisihang/thermal_placement/third_party/cudd-3.0.0` | 依赖库；安装目录在 `tools/cudd` |
| Eigen source/release | `/home/lisihang/thermal_placement/third_party/eigen-3.4.0` | 头文件库；安装目录在 `tools/eigen` |
| Chipyard generators | `/home/lisihang/thermal_placement/third_party/chipyard/generators/*` | 多个 RTL generator 已 vendored，未逐项验证 |
| Chipyard simulators dirs | `/home/lisihang/thermal_placement/third_party/chipyard/sims/{verilator,vcs,xcelium,firesim}` | 当前只确认 Verilator 路径可用 |

### 8.3 当前仓库中未发现或未完成

| 工具 | 结论 |
| --- | --- |
| COMSOL / comsolbatch | 未发现命令、未发现脚本/docs 引用 |
| PACT parallel mode | OpenMPI 已可用，但当前 Xyce 是 serial 构建；未完成 parallel PACT 路径 |

## 9. 注意事项

- `tools/` 与 `third_party/` 被 `.gitignore` 忽略；本清单记录的是当前工作区本地状态，不代表这些工具载荷会被 git 提交。
- `gtkwave --version`、`nextpnr-ice40 --version` 在当前 sandbox 中尝试写 `$HOME/.config/yosyshq` / `$HOME/.cache/yosyshq` 并报只读错误；因此标为“发现可执行但运行有 HOME 写入警告”。
- 当前 `PATH` 中 `sta` 优先来自 `tools/opensta/bin/sta`；`tools/openroad-prebuilt/root/usr/bin` 里也有 `sta`，未作为主路径使用。
- 对 OSS CAD Suite 的工具未逐一完整验证，只对当前可能相关的 Yosys、Icarus、波形转换、nextpnr、SMT 工具做了命令级检查。


## 10. 后端默认工具与重复路径结论（2026-04-24）

### 默认使用工具

当前后端主链路推荐固定为：

- 综合：`tools/oss-cad-suite/oss-cad-suite/bin/yosys`
- SystemVerilog 前端：通过 `yosys-slang` plugin 的 `read_slang`，不把独立 `slang` 二进制作为 Stage 2 默认入口
- 布局布线：`tools/openroad-prebuilt/root/usr/bin/openroad`
- STA：`tools/opensta/bin/sta`
- 流程编排：`third_party/OpenROAD-flow-scripts/flow`
- ASAP7 reduced techlib：`third_party/edahub/edahub/technology/asap7`

### 已确认的重复或易混淆点

- `sta` 存在两个可执行路径：
  - 默认推荐：`tools/opensta/bin/sta`
  - 备选但不推荐作为主入口：`tools/openroad-prebuilt/root/usr/bin/sta`
- `OpenROAD` 同时存在：
  - 默认运行入口：`tools/openroad-prebuilt/root/usr/bin/openroad`
  - 源码目录：`third_party/OpenROAD`
- `slang` 相关入口有两种：
  - 独立 `slang` 可执行
  - `yosys-slang` plugin
  当前 Stage 2 默认使用后者

### 当前调用规则

为了避免 ORFS 回落到它自己的 `tools/install/...` 默认路径，后端流程必须显式传递：

- `YOSYS_EXE`
- `OPENROAD_EXE`
- `OPENSTA_EXE`

仓库当前默认入口脚本：

- `scripts/run_stage2_openroad.sh`

### 当前顺畅度结论

- 工具本身大多可执行，路径也已经明确。
- 当前真正不顺畅的点不是“工具缺失”，而是：
  1. ORFS 默认工具路径假设与仓库本地安装不一致
  2. `sta` 存在双路径，需要显式指定默认版本
  3. `slang` 有独立二进制和 Yosys plugin 两种入口，若不写清楚容易混用
  4. 当前 Phase 2 主阻塞已经进入 Yosys/ORFS 后段综合，而不是环境缺失

## 11. 后端多线程接口检查结论（2026-04-24）

### 已确认存在的接口

- ORFS / OpenROAD：
  - `NUM_CORES`
  - `OPENROAD_ARGS = -no_init -threads $(NUM_CORES)`
- 顶层 make：
  - `make -j <N>`

### 已完成的轻量实测

- `make print-OPENROAD_ARGS` 在 `NUM_CORES=1/8` 下分别输出：
  - `-threads 1`
  - `-threads 8`
- `nangate45/gcd` 的 `synth` 小设计 smoke 在 `NUM_CORES=8` 下，OpenROAD 日志明确打印：
  - `[INFO ORD-0030] Using 8 thread(s).`
- 同一 smoke 中，Yosys 综合日志的 CPU 利用率约为 `100%`，没有观察到当前 flow 下可控且有效的综合内部多线程接口。

### 当前结论

- 布局布线侧：当前可依赖 `NUM_CORES` 驱动 OpenROAD 多线程。正常单一任务最多 `NUM_CORES=128`。
- 综合侧：当前 ORFS + Yosys 主链路没有确认到可稳定、可控、可复现的内部多线程接口；不要把 `NUM_CORES` 误解为 Yosys 会同步多线程。
- `MAKE_JOBS` 在 ORFS/后端语境中是外层独立任务数量。单个可复用 Stage 2 实现的正式外层 make 调度默认使用 `MAKE_JOBS=1`，这是确定性执行设置，不是限制 CPU 核数；P&R 加速使用 `NUM_CORES`。
- 因此当前正式推荐是：
  - 单个可复用实现：`MAKE_JOBS=1`，按阶段显式推进 `synth` / `floorplan` / `place` / `route`
  - 单任务 P&R 阶段从 `NUM_CORES=16` 起步，必要时逐步提高到当前机器已用过的 `128`
  - 只有多个独立 `FLOW_VARIANT`/block/config 并行时才提高外层 job 数；`MAKE_JOBS` 最大为 `4`
  - `MAKE_JOBS=2` 时每个任务最多 `NUM_CORES=128`；`MAKE_JOBS=3` 或 `4` 时每个任务最多 `NUM_CORES=64`
  - OpenROAD `NUM_CORES="$NUM_CORES"`
  - 不宣称 Yosys 已具备同等级别的有效多线程综合能力，除非后续另有专门验证

### ORFS 完整 flow 与 `NUM_CORES` 的区别

- `make ... all` 或 `synth floorplan place route`：表示按依赖顺序驱动一条完整后端主线。
- `NUM_CORES=<N>`：只控制每次 `openroad` 调用内部的 `-threads <N>`，不会把 Yosys 自动变成等效多线程综合，也不会把整个 ORFS 主线改造成大规模并行流水线。
- `make -j <N>` / `MAKE_JOBS=<N>`：更适合并发多个独立目标、多个 block 或多个独立配置；对单个常规 ORFS 主线通常帮助有限。本项目后端外层并发上限为 `4`。

### 当前项目的加速优先级

1. 先减少单次 run 的工作量：缩小 Gemmini top scope、收紧 filelist、保持 hierarchical synthesis、优先运行最小 stage。
2. 单个 baseline run 使用 `MAKE_JOBS=1` 作为外层 make 调度；P&R 阶段从 `NUM_CORES=16` 起步，必要时逐步提高到 `128`。多个独立任务并发时，`MAKE_JOBS` 最大为 `4`，并按 `MAKE_JOBS=2 -> NUM_CORES<=128/task`、`MAKE_JOBS=3/4 -> NUM_CORES<=64/task` 控制资源。
3. 不要每次从完整 `all` 重跑；优先 `synth`、`floorplan`、`place`、`route` 分阶段推进。
4. 只有在多个独立配置必须比较时，再做外层并行，并且为每个 job 设置唯一 `FLOW_VARIANT`，同时控制总核数预算，避免 overprovision。

## 12. 线程探索补充结论（2026-04-24）

### 综合线程探索

为避免污染主仓库，2026-04-24 的综合线程探索全部在 `/tmp/orfs_mt_sandbox/flow` 的 ORFS 临时副本中完成，并使用内置样例 `nangate45/aes` 做对比。

`synth` 实测：

- `NUM_CORES=1`:
  - 总耗时 `42.42s`
  - Yosys 主综合阶段 `40.10s`
  - Yosys CPU 约 `100%`
- `NUM_CORES=8`:
  - 总耗时 `42.53s`
  - Yosys 主综合阶段 `40.21s`
  - Yosys CPU 约 `101%`

当前可得结论：

- 在当前 ORFS + Yosys + `abc_new` 主链路下，这次测试没有观察到 `NUM_CORES` 带来综合 wall time 收益。
- 当前没有证据表明 Yosys 主综合链路在这次测试对应的样例和环境下具备可稳定、可控、可复现的内部多线程性能收益。
- `NUM_CORES` 仍主要应理解为 OpenROAD 参数，而不是综合线程参数。这里记录的只是本次测试结论；正式开发仍建议优先使用多线程，从 `16` 线程开始尝试，必要时逐步提高到 `128`。

### 布局布线线程探索

同样在 `/tmp/orfs_mt_sandbox/flow` 中，对 `nangate45/aes` 的 `3_3_place_gp` 单独做了 placement 核心阶段对比：

- `NUM_CORES=1`:
  - 日志打印 `[INFO ORD-0030] Using 1 thread(s).`
  - `global_placement` 用时 `66s`
- `NUM_CORES=8`:
  - 日志打印 `[INFO ORD-0030] Using 8 thread(s).`
  - `global_placement` 用时 `70s`

当前可得结论：

- OpenROAD 的线程参数确实被接收并记录到日志。
- 但在当前这套 OpenROAD prebuilt + ORFS + `nangate45/aes` 的 placement 实测中，这次测试里 `NUM_CORES=8` 没有带来 wall time 改善，反而比 `NUM_CORES=1` 慢约 `6%`。
- 因此目前不能把“能传 `-threads`”直接等同于“对当前研究流程一定有实际提速”。这里记录的只是本次测试没有性能收益；实际开发仍建议优先使用多线程，并从 `16` 线程开始尝试，必要时逐步提高到 `128`。线程数仍需要按具体 stage 和具体设计单独验证。

### 当前方法学结论

- 探索综合/布局布线线程行为时，优先在 `/tmp` 的独立 ORFS 副本中做，不把临时 logs/results/objects 写回主仓库。
- 当前更可靠的工程结论是：
  - 综合：当前未确认稳定可复现的多线程性能收益
  - P&R：接口存在，这次测试未见收益，但正式开发仍推荐优先使用多线程并按 stage 实测

## 13. 2026-05-03 ATSim3D 安装与验证

用户要求安装 `git@github.com:Brilight/ATSim3D_pub.git`。当前状态：

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| ATSim3D source | 已拉取到 `third_party/ATSim3D_pub` | commit `8454f719409a6d0b1759602e89601f8ae18b95c2` |
| 运行入口 | 已添加 `scripts/run_atsim3d.sh` | `bash -n scripts/run_atsim3d.sh` 和 `scripts/run_atsim3d.sh --help` 通过 |
| Python runtime | 使用隔离 prefix `tools/atsim3d-py38` | Python `3.8.20`；用于匹配 ATSim3D 发布的 Python 3.8 `.pyc` |
| Python deps | 已安装 | numpy `1.24.4`、pandas `2.0.3`、scipy `1.10.1`、tqdm `4.67.3`、matplotlib `3.7.5`、psutil `7.2.2` |
| README examples | 已完成 smoke | 2DIC 总耗时约 `2.24 s`；Mono3D 约 `6.60 s`；TSV3D 约 `10.12 s` |
| Result sanity | 已读取 `.res` 文件 | 共 7 个 `.res` 文件，`numpy.loadtxt` 可读取，温度最大值约 `342.63 K` 到 `392.52 K` |

工具作用、论文对应关系、输入输出和示例命令详见 `docs/atsim_tool_guide.md`。

## 14. 2026-05-03 ATSim3D v2 binary placement and smoke

用户提供的 `ATSim3_5D` 是 `third_party/ATSim3D_pub/README.md` v2 段落中说明的下载二进制。当前状态：

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| Binary location | 已移动到 `tools/atsim3d-bin/ATSim3_5D` | 根目录不再保留 `ATSim3_5D` |
| Wrapper | 已添加 `scripts/run_atsim3_5d.sh` | `bash -n scripts/run_atsim3_5d.sh` 通过 |
| File identity | ELF 64-bit x86-64 dynamically linked executable | `file tools/atsim3d-bin/ATSim3_5D` |
| SHA256 | `48322878d509432d8bff8799e1111c6347a174f01b9da454430a0bd80539f121` | `sha256sum tools/atsim3d-bin/ATSim3_5D` |
| Shared libraries | 无 missing shared library | `ldd tools/atsim3d-bin/ATSim3_5D` |
| CLI smoke | 通过 | `timeout 20 scripts/run_atsim3_5d.sh --help` 返回 `0`，无 stderr |
| Missing-input smoke | 通过错误路径检查 | 缺 `/tmp/missing.xml` 时返回 `1` 并报告 XML file not found |

当前 public repo 没有完整 v2 XML/config/material/power/floorplan 示例；`third_party/ATSim3D_pub` 只提供 v1 CSV/config 示例。2026-05-03 已从 v2 二进制入口和错误路径确认部分输入接口：XML 至少需要 `MaterialLib File="..."`，`power_type = value` 可通过 XML `Power File="..."` 读取 `UnitName,Power_dyn,Power_leak` CSV，config 至少包含 `[Simulation]` 和 `[MeshConfig]`。完整 ATSim3_5D 热仿真仍需要补齐匹配 v2 schema 的完整输入集，字段记录见 `docs/atsim_tool_guide.md`。
