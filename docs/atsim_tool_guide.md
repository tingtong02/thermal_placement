# ATSim Tool Guide

更新时间：2026-05-03

本文记录本仓库中 ATSim 相关工具的本地位置、论文来源、可执行入口、输入输出和使用方法。内容依据：

- `third_party/ATSim3D_pub/README.md`
- `docs/references/atsim/ATSim3D_ISEDA2024_Wang_arXiv2601.11050.pdf`
- `docs/references/atsim/ATSim3_5D_ISEDA2025_Wang_arXiv2601.11053.pdf`
- 本仓库安装路径、wrapper 和 smoke 验证记录

说明：本文只记录 ATSim 工具安装、论文对应关系、输入接口和验证命令。当前 Gemmini Stage 0-4 active 计划由 `docs/phase0tophase4_cadence_asap7_plan.md` 定义；本文件不改变 active 计划的阶段边界、工具主线或 workload 集合。

## 1. 本地文件位置

| 项目 | 路径 | 说明 |
| --- | --- | --- |
| ATSim3D public repo | `third_party/ATSim3D_pub` | GitHub repo `git@github.com:Brilight/ATSim3D_pub.git`，commit `8454f719409a6d0b1759602e89601f8ae18b95c2` |
| ATSim3D v1 wrapper | `scripts/run_atsim3d.sh` | 从项目根目录调用 v1 Python 入口，并自动使用专用 Python 3.8 运行时 |
| ATSim3D v1 runtime | `tools/atsim3d-py38` | Python `3.8.20`，用于加载 repo 发布的 Python 3.8 `.pyc` 核心模块 |
| ATSim3.5D v2 binary | `tools/atsim3d-bin/ATSim3_5D` | 用户提供的 v2 ELF x86-64 二进制，SHA256 `48322878d509432d8bff8799e1111c6347a174f01b9da454430a0bd80539f121` |
| ATSim3.5D v2 wrapper | `scripts/run_atsim3_5d.sh` | 从项目根目录调用 v2 binary，并在系统存在字体配置时设置 `FONTCONFIG_FILE` |
| ATSim papers | `docs/references/atsim` | 保存 ATSim3D 与 ATSim3.5D 论文 PDF |

## 2. 论文对应关系

| 工具 | 对应论文 | 论文中的目标系统 | 主要方法 |
| --- | --- | --- | --- |
| ATSim3D v1 | `ATSim3D: Towards Accurate Thermal Simulator for Heterogeneous 3D-IC Systems Considering Nonlinear Leakage and Conductivity` | 2D IC、monolithic 3D IC、TSV-based 3D IC | steady-state thermal simulation；global-local 求解；粗粒度全局 compact thermal model 加局部细粒度 finite volume method；支持非线性漏电和温度相关热导率 |
| ATSim3.5D v2 | `ATSim3.5D: A Multiscale Thermal Simulator for 3.5D-IC Systems based on Nonlinear Multigrid Method` | 3.5D IC、chiplet、interposer、package、heat sink 多尺度结构 | hybrid tree / multilevel grid generation；局部网格细化；nonlinear multigrid / FAS-MG 求解 |

## 3. ATSim3D v1

### 3.1 作用

ATSim3D v1 用于生成异构 3D IC 系统的稳态温度分布。README 和论文说明它处理的热效应包括：

- 非线性 thermal conductivity
- 温度相关 leakage power
- 多层 chip stack
- 2DIC、Mono3D、TSV3D 示例结构

论文中的典型流程是：读取功耗、材料属性、stack/floorplan/TSV 配置和仿真参数，构造热模型，迭代求解 steady-state temperature profile。

### 3.2 可执行入口

原始入口位于：

```bash
third_party/ATSim3D_pub/src/ATSim3D.py
```

本项目使用 wrapper：

```bash
scripts/run_atsim3d.sh --help
```

命令行参数：

```text
--lcfFile LCFFILE
--ConfigFile CONFIGFILE
--SimParamsFile SIMPARAMSFILE
```

Wrapper 会把相对路径转成绝对路径，进入 `third_party/ATSim3D_pub/src` 后使用：

```bash
tools/atsim3d-py38/bin/python ATSim3D.py ...
```

不要直接用项目主环境 Python 3.11 运行 v1；repo 中核心模块是 Python 3.8 `.pyc`，用 Python 3.11 会出现 bytecode magic number 不匹配。

### 3.3 输入文件

v1 README 给出的通用形态：

```bash
python ATSim3D.py \
  --lcfFile /path/to/lcf_file \
  --ConfigFile /path/to/config_file \
  --SimParamsFile /path/to/simulator_file
```

输入含义：

| 参数 | 作用 | 仓库示例 |
| --- | --- | --- |
| `--lcfFile` | layer stacking config，自底向上描述层结构；字段包含 layer id、材料、厚度、floorplan 文件、power 文件、x/y/z clip 数 | `third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.csv` |
| `--ConfigFile` | 材料热导率、环境温度、初始温度、package/NoPackage 参数、leakage 模型参数 | `third_party/ATSim3D_pub/2DIC/Intel.config` |
| `--SimParamsFile` | solver 参数、grid 分辨率、TSV 文件路径和 TSV 形状等 | `third_party/ATSim3D_pub/2DIC/SimParms.config` |

2DIC 示例 `lcf` 文件字段：

```text
Layer,Main_compo,Thickness (m),FloorplanFile,PowerFile,Clip_num_x,Clip_num_y,Clip_num_z
```

README 还说明：

- `_flp.csv` 描述 active layer 中 macros / blocks / standard cells 的位置。
- `_power.csv` 描述对应对象的 dynamic power 和 static power。
- TSV3D 示例中 TSV array 的形状由 TSV floorplan 文件描述。

### 3.4 仓库示例命令

2DIC：

```bash
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.csv \
  --ConfigFile third_party/ATSim3D_pub/2DIC/Intel.config \
  --SimParamsFile third_party/ATSim3D_pub/2DIC/SimParms.config
```

Mono3D：

```bash
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile third_party/ATSim3D_pub/Mono3D/Mono3D_lcf.csv \
  --ConfigFile third_party/ATSim3D_pub/Mono3D/Mono3D.config \
  --SimParamsFile third_party/ATSim3D_pub/Mono3D/SimParms.config
```

TSV3D：

```bash
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile third_party/ATSim3D_pub/TSV3D/TSV3D_lcf.csv \
  --ConfigFile third_party/ATSim3D_pub/TSV3D/TSV3D.config \
  --SimParamsFile third_party/ATSim3D_pub/TSV3D/SimParms.config
```

### 3.5 输出和验证状态

v1 示例会在输入目录附近生成按 layer 区分的 `.res` 温度结果文件，例如：

```text
third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.layer0.res
third_party/ATSim3D_pub/Mono3D/Mono3D_lcf.layer6.res
third_party/ATSim3D_pub/TSV3D/TSV3D_lcf.layer8.res
```

当前已完成 README 三个示例 smoke：2DIC、Mono3D、TSV3D。共生成 7 个 `.res` 文件，均可用 `numpy.loadtxt` 读取。TSV3D 示例运行时会打印 `Unifrom grids cannot be formed. Choose a multiple of 2 or 5 as rows&columns`，但流程继续完成并写出结果。

### 3.6 v1 repo 内部模块

`third_party/ATSim3D_pub/src` 中除 `ATSim3D.py` 外，核心实现以 `.pyc` 形式发布。它们是内部模块，不是独立命令行工具：

| 模块文件 | 从文件名和 v1 流程可见的职责 |
| --- | --- |
| `ATSimCore.pyc` | v1 主求解流程核心 |
| `ChipStack.pyc` | chip stack / 多层结构组织 |
| `Layer.pyc` | 单层结构和材料层表示 |
| `Grid.pyc` | 网格数据结构 |
| `GridManager.pyc` | 网格生成和管理 |
| `GridSolver.pyc` | 细粒度 grid 求解 |
| `CoarseSolver.pyc` | 粗粒度全局模型求解 |
| `ReadParser.pyc` | 输入文件解析 |
| `Solid.pyc` | 固体材料/热属性模型 |
| `TSVManager.pyc` | TSV 结构处理 |
| `utils.pyc` | 辅助函数 |

## 4. ATSim3.5D v2

### 4.1 作用

ATSim3.5D v2 用于 3.5D IC 系统的多尺度热仿真。论文描述的目标结构包括 chiplet、interposer、package 和 heat sink，重点是处理 3.5D 系统中尺寸跨度大、局部热点和非线性热效应共存的问题。

论文中的流程是：读取 input file 中的 geometry、power 和 configuration，生成 global grids，对局部区域 refine，再使用 nonlinear multigrid / FAS-MG solver 得到温度结果。论文提供的是方法和流程说明，没有给出完整 XML schema 或可直接运行的示例输入。

### 4.2 可执行入口

二进制位置：

```bash
tools/atsim3d-bin/ATSim3_5D
```

本项目 wrapper：

```bash
scripts/run_atsim3_5d.sh --help
```

当前 help 输出的参数：

```text
-xml XML
-config CONFIG
--output_path OUTPUT_PATH
--plot_flag PLOT_FLAG
--save_freq SAVE_FREQ
```

README 给出的使用形态：

```bash
./ATSim3_5D -xml <XmlFile> -config <ConfigFile> --output_path
```

本项目中从根目录调用：

```bash
scripts/run_atsim3_5d.sh \
  -xml <XmlFile> \
  -config <ConfigFile> \
  --output_path <OutputDir>
```

### 4.3 已确认的 v2 入口流程

从 `ATSim3_5D` 的内嵌入口和错误路径确认，v2 的主流程是：

1. `readFiles(xml_file, config_file)` 读取 XML、INI config 和 material library。
2. 读取 XML 中的 `PowerLib` 或 `Power` 功耗输入。
3. 读取 XML 中的 `Component` 结构，建立 `GridManagerSerial`。
4. 执行 `createGridSys()`、`generateGrids()`、`collectLayers()`、`collectNeibor()`、`initHTC()`、`setTemp()`、`calcProps()`。
5. `sim_mode = 0` 时执行 steady 求解，输出 `raw/steadytemp.txt`。
6. `sim_mode = 1` 时执行 transient 求解，输出 `raw/res_0.txt` 和按 `--save_freq` 保存的 `raw/res_<n>.txt`。

`--plot_flag 1` 会触发绘图/视频生成路径；transient run 应显式设置正整数 `--save_freq`，否则默认值不会产生期望的周期性保存结果。

### 4.4 输入文件格式

v2 使用三个主要输入面：XML 主输入、INI config、material library。当前 public repo 没有完整 v2 示例，因此下面只记录已经由二进制入口、错误路径和论文确认的字段。

XML 主输入中已确认的元素：

| 元素 | 已确认字段 | 作用 |
| --- | --- | --- |
| `MaterialLib` | `File` | 必需。指向 material library 文件；写成文本内容无效，必须是 `File="..."` 属性。 |
| `PowerLib` | `File` | `power_type = util` 或使用 YAML power library 时使用；多个 `PowerLib` 时二进制只使用第一个。 |
| `Power` | `File` | `power_type = value` 且没有 `PowerLib` 时读取；`File` 指向 power CSV。 |
| `Component` | `name` 或 `number`；`type`；`Length`、`Width`、`XYorigin` | 描述 3.5D 系统部件。`type` 已确认支持 `active`、`bulk`、`interposer`、`sink`、`substrate`、`pcb`；`XYorigin` 支持 `origin`、`center` 或坐标字符串。 |
| `Layer` / `Chiplet` | 作为 `Component` 子元素 | `Component` 子元素只接受 `Layer` 或 `Chiplet`。 |

material library 是 `configparser`/INI 风格文件。每个材料是一个 section，已确认字段包括：

```ini
[Si]
conductivity (w/(m-k)) = 150
volumetric heat capacity (j/(m3-k)) = 1650000
non_linear = False
```

材料热容也可以用 `density (kg/m3)` 和 `specific heat capacity (j/(kg-k))` 组合表达。`conductivity (w/(m-k))` 可给 1、2 或 3 个数，分别表示各向同性、x/y 相同且 z 不同、x/y/z 三向不同。

config 文件是 INI 风格。已确认必须包含 `[Simulation]` 和 `[MeshConfig]`，其中二进制已经读取到的字段包括：

```ini
[Simulation]
number_of_core = 1
sim_mode = 0
power_type = value
calc_leakage = 0
power_gran = unit
unit_agg_method = avg
calc_kappa_type = avg
init = 300
ambient = 300
cycles = 1

[MeshConfig]
max_depth = 1
min_depth = 0
max_thickness = 0.001
grid_expand_factor = 1
tol_zero = 1e-12
ratio_ignore = 0
fine_grid_num = 1
powerdens_th = 0
rows = 1
cols = 1
```

`sim_mode > 0` 时还会读取 `time_steps` 和 `step_size`。二进制在继续初始化时还会读取与 tier/chiplet/package/heat-sink 相关的额外字段；这些字段需要结合完整 XML/component 结构使用，当前没有 public sample 可直接确认完整组合。

power CSV 的简单 direct-value 表头已确认支持：

```text
UnitName,Power_dyn,Power_leak
```

另一个已确认路径是以 unit name 作为列名的 CSV 形式，用于按 step 读取功耗 trace。

### 4.5 最小探测结果

已执行的 v2 输入探测包括：

```bash
scripts/run_atsim3_5d.sh \
  -xml /tmp/nonexistent.xml \
  -config /tmp/nonexistent.config \
  --output_path /tmp/atsim_v2_probe_nonexistent
```

结果：返回状态 `1`，报 `XML file /tmp/nonexistent.xml not found`。

```xml
<root/>
```

配合空 config 运行时返回状态 `1`，报 `No MaterialLib element found in XML`。

```xml
<System>
  <MaterialLib>/tmp/atsim_v2_probe/material.ini</MaterialLib>
</System>
```

返回状态 `1`，报 `MaterialLib File attribute missing`，说明 `MaterialLib` 必须使用 `File` 属性。

补充一个带 `MaterialLib File`、基本 `[Simulation]` 和 `[MeshConfig]` 的探测输入后，程序已进入 `GridManager` 初始化，下一处缺失字段为 `tiers_active`。这说明上面的字段集合能通过 XML/material/config 的前置读取，但还不是完整可仿真的 v2 case。

### 4.6 验证状态

已执行的二进制 smoke：

```bash
bash -n scripts/run_atsim3_5d.sh
ldd tools/atsim3d-bin/ATSim3_5D
timeout 20 scripts/run_atsim3_5d.sh --help
timeout 20 scripts/run_atsim3_5d.sh \
  -xml /tmp/missing.xml \
  -config /tmp/missing.config \
  --output_path /tmp/atsim3_5d_missing
```

验证结果：

- `bash -n` 通过。
- `ldd` 未发现 missing shared library。
- `--help` 返回状态 `0`，参数解析正常。
- 缺失 XML 输入时返回状态 `1`，错误信息明确指出 XML 文件不存在。
- 当前 public repo 没有完整 v2 XML/config/material/power/floorplan 示例；端到端热仿真仍需要补齐匹配 v2 schema 的完整输入集。

## 5. 旧 proxy 数据的 ATSim3D v1 rerun

2026-05-03 已完成一次旧 `stage4_tiled_matmul_os_baseline` proxy 数据的 ATSim3D v1 steady rerun。该运行没有使用 ATSim3.5D v2。

| 项 | 路径 / 结果 |
| --- | --- |
| run dir | `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline` |
| plan | `docs/references/atsim_proxy_experiment_plan.md` |
| run README | `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/README.md` |
| detailed results | `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/RESULTS.md` |
| ATSim result | `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res` |
| summary CSV/JSON | `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/results/atsim_result_summary.csv`, `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/results/atsim_result_summary.json` |
| Stage4-style artifacts | `artifacts/stage4/atsim3d_v1_proxy/README.md` |

Run result:

- Stage4-style artifacts 已生成到 `artifacts/stage4/atsim3d_v1_proxy/`，包括 ATSim proxy heatmap、ATSim-PACT delta heatmap、温度分布图、public 2DIC/Mono3D/TSV3D 示例热图和 CSV summary。
- ATSim wrapper exit status: `0`.
- Coarse solve: 0.62 s; fine solve: 216.46 s; total: 265.10 s.
- Proxy ATSim layer0 result: min 324.900422 K, max 329.634972 K, mean 326.971203 K.
- Public 2DIC/Mono3D/TSV3D example `.res` files were also summarized in `RESULTS.md` to explain structural and output differences.

## 6. 支持数据目录

| 目录 | 内容 |
| --- | --- |
| `third_party/ATSim3D_pub/2DIC` | 2D IC 示例，包含 layer config、floorplan、power、config、solver 参数和结果 `.res` |
| `third_party/ATSim3D_pub/Mono3D` | monolithic 3D IC 示例，包含两个 active layer 的输入和结果 `.res` |
| `third_party/ATSim3D_pub/TSV3D` | TSV-based 3D IC 示例，包含 TSV 相关 solver/config 输入和结果 `.res` |
| `third_party/ATSim3D_pub/COMSOL` | COMSOL 对照数据文件 |
| `third_party/ATSim3D_pub/results` | repo 自带的 `.npy` 结果数据 |

## 7. 常用检查命令

```bash
git -C third_party/ATSim3D_pub rev-parse HEAD
bash -n scripts/run_atsim3d.sh
scripts/run_atsim3d.sh --help
bash -n scripts/run_atsim3_5d.sh
ldd tools/atsim3d-bin/ATSim3_5D
scripts/run_atsim3_5d.sh --help
```
