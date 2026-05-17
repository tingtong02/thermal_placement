# PACT / slang / sv2v / yosys-slang 安装报告

日期：2026-04-22

## 环境入口

统一入口仍为：

```bash
source tools/env_gemmini_thermal.sh
```

本次只补充安装、构建、环境变量和最小可执行检查，没有修改既有 Gemmini / thermal 主流程逻辑，也没有配置商业工具。

新增或确认的环境变量：

| 变量 | 值 |
| --- | --- |
| `PACT_HOME` | `/home/lisihang/thermal_placement/third_party/PACT` |
| `PACT_ENTRY` | `/home/lisihang/thermal_placement/third_party/PACT/src/PACT.py` |
| `SLANG_HOME` | `/home/lisihang/thermal_placement/tools/slang` |
| `SV2V_HOME` | `/home/lisihang/thermal_placement/tools/sv2v` |
| `YOSYS_SLANG_PLUGIN` | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/share/yosys/plugins/slang.so` |
| `LIBTOOL_HOME` | `/home/lisihang/thermal_placement/tools/libtool` |
| `OPENMPI_HOME` | `/home/lisihang/thermal_placement/tools/openmpi-3.1.4` |
| `XYCE_HOME` | `/home/lisihang/thermal_placement/tools/xyce-7.4-build/install` |
| `XYCE_EXE` | `/home/lisihang/thermal_placement/tools/xyce-7.4-build/install/bin/Xyce` |
| `TP_APT_SYSROOT` | `/home/lisihang/thermal_placement/tools/apt-sysroot` |
| `GHCRTS` | 默认 `-N$MAKE_JOBS`，用于限制 Haskell RTS 并行度 |

`tools/env_gemmini_thermal.sh` 已将以下目录加入 `PATH`：

```bash
$TP_TOOLS_BIN
$LIBTOOL_HOME/bin
$OPENMPI_HOME/bin
$XYCE_HOME/bin
$SLANG_HOME/bin
$SV2V_HOME/bin
```

`tools/env_gemmini_thermal.sh` 也将本地 Xyce、OpenMPI、Libtool、APT sysroot 库目录加入 `LD_LIBRARY_PATH`。其中 `TP_APT_SYSROOT` 用于提供本项目局部安装的 `libgfortran.so.5` 和 LAPACK 运行库。

PACT 官方入口不是独立的 `pact` 二进制命令，而是 Python 主程序。因此本仓库不新增 `pact` 包装脚本，检查命令使用：

```bash
python "$PACT_ENTRY" --help
```

## 已成功安装或确认可用的工具

| 工具 | 版本 / commit | 安装路径 | 类型 | 构建方式 | 可执行检查命令 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- |
| PACT | git commit `bb7f05a` | `third_party/PACT` | 热仿真 | `git clone --depth 1 https://github.com/peaclab/PACT.git third_party/PACT`；Python 工具，无编译步骤；为兼容当前 pandas / NumPy 做了最小本地补丁 | `python "$PACT_ENTRY" --help`；PACT SuperLU / serial Xyce 实例验证 | 主入口可执行；SuperLU 实例和 serial Xyce 实例均已验证 |
| Xyce | `Release 7.4.0-opensource`；source commit `82f96bb` / `Public_Release-7.4.0-0-g82f96bb` | source: `third_party/Xyce`；install: `tools/xyce-7.4-build/install` | SPICE / PACT 后端依赖 | CMake SuperBuild + Ninja；`Xyce_USE_SUPERBUILD=ON`；`Xyce_USE_FFTW=OFF`；构建 SuiteSparse、Trilinos、ADMS、Xyce | `Xyce -v`；`Xyce /tmp/tp_xyce_smoke/smoke.cir` | 可执行；当前为 serial Xyce，未启用 MPI |
| OpenMPI | `3.1.4` | source: `third_party/openmpi-3.1.4`；install: `tools/openmpi-3.1.4` | MPI / PACT parallel Xyce 依赖 | 官方 release tarball；`./configure --disable-mpi-fortran --disable-static --enable-shared --without-verbs --without-cuda`；`make -j "$MAKE_JOBS"`；`make install` | `mpirun --version`；`mpicc --showme:version`；`mpicc /tmp/tp_mpi_smoke.c -o /tmp/tp_mpi_smoke && mpirun -np 2 /tmp/tp_mpi_smoke` | C MPI 可执行；未构建 MPI Fortran wrapper |
| GNU Libtool | `2.4.7` | source: `third_party/libtool-2.4.7`；install: `tools/libtool` | 构建工具 / OpenMPI 依赖 | GNU release tarball；`./configure --prefix=tools/libtool`；`make -j "$MAKE_JOBS"`；`make install` | `libtoolize --version` | 可执行 |
| local gfortran wrapper | GNU Fortran `11.4.0` | wrapper: `tools/bin/gfortran`；payload: `tools/apt-sysroot/usr/bin/gfortran-11` | 编译器 / Xyce-Trilinos 构建依赖 | 本地解包 Ubuntu `.deb` 到 `tools/apt-sysroot`，wrapper 补 `-B` 搜索路径 | `gfortran --version`；Fortran hello-world compile/run | 可执行 |
| slang | `v10.0`；commit `ace09c5`；`slang version 10.0.0+ace09c5` | source: `third_party/slang`；install: `tools/slang` | SystemVerilog 前端 / 编译器 | CMake + Ninja，`Release`，安装前缀 `tools/slang` | `slang --version`；`slang /tmp/tp_toolcheck.sv` | 可执行 |
| sv2v | `sv2v v0.0.13` | `tools/sv2v/bin/sv2v` | SystemVerilog 到 Verilog 转换器 | 下载官方 Linux 预编译包 `tools/downloads/sv2v-Linux-v0.0.13.zip` 并解压接入 | `sv2v --version`；`sv2v /tmp/tp_toolcheck.sv` | 可执行 |
| yosys-slang | 随 OSS CAD Suite 的 Yosys `0.64+68` 插件提供 | `tools/oss-cad-suite/oss-cad-suite/share/yosys/plugins/slang.so` | Yosys SystemVerilog 前端插件 | 已由现有 OSS CAD Suite vendored；本次确认/接入，不重复安装 | `yosys -m slang -p 'help read_slang'`；`yosys -m slang -p 'read_slang /tmp/tp_toolcheck.sv; hierarchy -top toolcheck; proc; stat'` | 可执行 |

## 实际检查证据

环境入口检查：

```text
Xyce=/home/lisihang/thermal_placement/tools/xyce-7.4-build/install/bin/Xyce
mpirun=/home/lisihang/thermal_placement/tools/openmpi-3.1.4/bin/mpirun
mpicc=/home/lisihang/thermal_placement/tools/openmpi-3.1.4/bin/mpicc
libtoolize=/home/lisihang/thermal_placement/tools/libtool/bin/libtoolize
gfortran=/home/lisihang/thermal_placement/tools/bin/gfortran
slang=/home/lisihang/thermal_placement/tools/slang/bin/slang
sv2v=/home/lisihang/thermal_placement/tools/sv2v/bin/sv2v
yosys=/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/yosys
python=/home/lisihang/miniconda3/envs/thermal_placement/bin/python
```

版本检查：

```text
Xyce Release 7.4.0-opensource
mpirun (Open MPI) 3.1.4
mpicc: Open MPI 3.1.4 (Language: C)
libtoolize (GNU libtool) 2.4.7
GNU Fortran (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
slang version 10.0.0+ace09c5
sv2v v0.0.13
Yosys 0.64+68 (git sha1 413169663, clang++ 18.1.8 -fPIC -O3)
```

Xyce 运行库解析检查：

```text
libxyce.so => /home/lisihang/thermal_placement/tools/xyce-7.4-build/install/lib/libxyce.so
liblapack.so.3 => /home/lisihang/thermal_placement/tools/apt-sysroot/usr/lib/x86_64-linux-gnu/lapack/liblapack.so.3
libgfortran.so.5 => /home/lisihang/thermal_placement/tools/apt-sysroot/usr/lib/x86_64-linux-gnu/libgfortran.so.5
```

最小 Xyce 电路：

```spice
* Xyce smoke
V1 1 0 DC 1
R1 1 0 1k
.OP
.PRINT DC V(1)
.END
```

Xyce 检查结果：

```text
***** Executing netlist smoke.cir
***** Solution Summary *****
        Number Successful Steps Taken:          1
        Number Failed Steps Attempted:          0
***** End of Xyce(TM) Simulation
```

OpenMPI C smoke test：

```text
rank 0 of 2
rank 1 of 2
```

PACT 主入口检查结果：

```text
usage: PACT [-h] [--init INITFILE] [--steady STEADYFILE]
            [--gridSteadyFile GRIDSTEADYFILE]
            lcfFile configFile modelParamsFile
```

PACT 与当前 Python 数值栈的兼容性补丁：

| 文件 | 变更 | 原因 |
| --- | --- | --- |
| `third_party/PACT/src/PACT.py` | 将 `DataFrame.append()` 改为 `pd.concat()` | 兼容 pandas 3.x |
| `third_party/PACT/src/Layer.py` | `ConfigFile` 列改为 object 后再 `fillna()` | 避免 pandas 3.x Copy-on-Write / dtype 错误 |
| `third_party/PACT/src/GridManager.py` | `np.select(..., default='')` | 兼容 NumPy 2.x 的字符串 dtype 选择 |

PACT Python 依赖检查：

```text
pandas: OK 3.0.2
scipy: OK 1.17.1
configparser: OK unknown
matplotlib: OK 3.10.8
cv2: OK 4.13.0
seaborn: OK 0.13.2
numpy: OK 2.4.4
```

最小 SystemVerilog 输入：

```systemverilog
module toolcheck(input logic a, output logic y); assign y = a; endmodule
```

slang 检查结果：

```text
Top level design units:
    toolcheck

Build succeeded: 0 errors, 0 warnings
```

sv2v 检查结果：

```verilog
module toolcheck (
	a,
	y
);
	input wire a;
	output wire y;
	assign y = a;
endmodule
```

yosys-slang 检查结果：

```text
1. Executing SLANG frontend.
Top level design units:
    toolcheck

Build succeeded: 0 errors, 0 warnings
...
=== toolcheck ===
        2 wires
        2 wire bits
        2 ports
        2 port bits
        1 cells
        1   $buf
```

## PACT 依赖状态

PACT README 中说明：

- SuperLU steady-state 路径只需要 Python 依赖。
- SPICE steady/transient 路径需要 Xyce。
- 并行 thermal simulation 需要 parallel Xyce 和 OpenMPI 3.1.4。

当前状态：

| 依赖 | 当前状态 | 影响 |
| --- | --- | --- |
| Python 依赖 | 已补齐并导入通过 | PACT 主入口和 SuperLU Python 路径具备继续验证条件 |
| Xyce | `Xyce` 已在环境入口中可执行，serial smoke test 通过 | PACT SPICE_steady / SPICE_transient 路径具备继续验证条件 |
| OpenMPI | `mpirun` / `mpicc` 已在环境入口中可执行，C MPI smoke test 通过 | MPI 基础工具链已补齐 |
| parallel Xyce | 暂缓 | 当前 Xyce SuperBuild 产物显示 Trilinos 未启用 MPI；按当前阶段要求暂不继续补 parallel mode |

## PACT 实例验证

### 1. SuperLU steady-state 示例

执行目录：

```bash
cd third_party/PACT/src
```

执行命令：

```bash
python PACT.py \
  ../Example/lcf_files/10mm_lcf_UniformPD_50Wcm2.csv \
  ../Example/config_files/default_htc_1e4_10mm.config \
  ../Example/modelParams_files/modelParams10mm.config_40x40 \
  --gridSteadyFile /home/lisihang/thermal_placement/reports/pact_validation/superlu_10mm.grid.steady
```

结果：

- 生成 [superlu_10mm.grid.steady.layer0](/home/lisihang/thermal_placement/reports/pact_validation/superlu_10mm.grid.steady.layer0)
- 生成 [superlu_10mm.grid.steady.layer1](/home/lisihang/thermal_placement/reports/pact_validation/superlu_10mm.grid.steady.layer1)
- 终端打印 block-level 温度

范围检查：

```text
superlu_layer0_min=368.540000
superlu_layer0_max=368.540000
superlu_layer1_min=368.150000
superlu_layer1_max=368.150000
```

说明：该用例使用 SuperLU + NoPackage，验证了 PACT 主入口、示例路径、SciPy 稀疏求解器和 grid 输出路径都可用。

### 2. serial Xyce / SPICE_steady 示例

为避免误触发 `mpirun`，新增了仅用于验证的串行配置：

- [modelParams20mm_spice_steady_serial_20x20.config](/home/lisihang/thermal_placement/reports/pact_validation/modelParams20mm_spice_steady_serial_20x20.config)

执行目录：

```bash
cd third_party/PACT/src
```

执行命令：

```bash
python PACT.py \
  ../Example/lcf_files/20mm_lcf_UniformPD_50Wcm2.csv \
  ../Example/config_files/default_htc_1e4_20mm.config \
  /home/lisihang/thermal_placement/reports/pact_validation/modelParams20mm_spice_steady_serial_20x20.config \
  --gridSteadyFile /home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.grid.steady
```

结果：

- 生成 [spice_20mm_serial.cir](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.cir)
- 生成 [spice_20mm_serial.log](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.log)
- 生成 [spice_20mm_serial.cir.csv](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.cir.csv)
- 生成 [spice_20mm_serial.cir.ic](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.cir.ic)
- 生成 [spice_20mm_serial.grid.steady.layer0](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.grid.steady.layer0)
- 生成 [spice_20mm_serial.grid.steady.layer1](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.grid.steady.layer1)

Xyce log 关键信息：

```text
This is version Xyce Release 7.4.0-opensource
Total Devices                          2721
Number of Unknowns = 802
```

范围检查：

```text
spice_layer0_min=367.250000
spice_layer0_max=375.780000
spice_layer1_min=366.880000
spice_layer1_max=375.330000
```

说明：该用例验证了 PACT 到 Xyce netlist 生成、Xyce 调用、`.cir.csv` 结果回读、`.ic` 保存和最终 grid 输出路径全部打通。

## 本次补齐过程中的关键处理

下载时沿用 issue log 中记录的代理规避方式：

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY <download-or-build-command>
```

OpenMPI 使用 release tarball，而不是 git 源码树。git 源码树需要 `autogen.pl` 和 Libtool 先生成 `configure`，tarball 已包含 `configure`，更适合本地闭环安装。

OpenMPI 当前使用：

```bash
./configure \
  --prefix=/home/lisihang/thermal_placement/tools/openmpi-3.1.4 \
  --disable-mpi-fortran \
  --disable-static \
  --enable-shared \
  --without-verbs \
  --without-cuda
```

说明：`--disable-mpi-fortran` 是为了在当前容器无系统 Fortran toolchain 的情况下先闭合 PACT 依赖中明确要求的 OpenMPI 3.1.4 C runtime。后续如果要构建 MPI-enabled Xyce/Trilinos，可能需要重建带 Fortran 支持的 OpenMPI，或确认 Trilinos/Xyce 的 MPI 构建不需要 MPI Fortran wrapper。

Xyce SuperBuild 配置使用：

```bash
cmake -G Ninja \
  -DXyce_USE_SUPERBUILD=ON \
  -DXyce_USE_FFTW=OFF \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_LIBRARY_PATH="/home/lisihang/thermal_placement/tools/apt-sysroot/usr/lib/x86_64-linux-gnu/lapack;/usr/lib/x86_64-linux-gnu" \
  -DBLAS_LIBRARIES=/usr/lib/x86_64-linux-gnu/libblas.so \
  -DLAPACK_LIBRARIES="/home/lisihang/thermal_placement/tools/apt-sysroot/usr/lib/x86_64-linux-gnu/lapack/liblapack.so;/usr/lib/x86_64-linux-gnu/libblas.so" \
  /home/lisihang/thermal_placement/third_party/Xyce
```

Xyce 构建中补齐了本地 `gfortran` wrapper 和 `libgfortran.so.5` runtime。最终可执行依赖通过 `tools/env_gemmini_thermal.sh` 的 `LD_LIBRARY_PATH` 接入。

## 未完成项及原因

| 项目 | 状态 | 原因 |
| --- | --- | --- |
| PACT `pact` 命令 | 不适用 | 官方入口就是 `src/PACT.py`；当前统一入口为 `python "$PACT_ENTRY" ...` |
| PACT parallel mode | 暂缓 | OpenMPI 已补齐，但当前 Xyce 是 serial 构建；按当前阶段要求不继续补 parallel mode |

## 快速复查命令

```bash
source tools/env_gemmini_thermal.sh
python "$PACT_ENTRY" --help
Xyce -v
mpirun --version
mpicc --showme:version
libtoolize --version
slang --version
sv2v --version
yosys -m slang -p 'help read_slang'
```
