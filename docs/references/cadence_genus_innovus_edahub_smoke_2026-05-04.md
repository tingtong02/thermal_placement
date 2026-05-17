# Cadence Genus / Innovus and edahub Validation Report

测试日期：2026-05-04

仓库：`/home/lisihang/thermal_placement`

测试性质：本报告是 Cadence Genus / Innovus 本机安装与 `third_party/edahub` Cadence 相关脚本的 reference smoke 记录，不属于当前 Gemmini Stage 0-4 active flow 验收结果。

运行边界：所有 Cadence 自动输出、edahub smoke 输出和并发/线程测试输出均写入 `/tmp`，没有修改 `third_party/edahub`、`tools/`、active plan 或主项目 run 目录。本次只维护本文档。

## 1. 总结结论

| 项目 | 结论 | 关键边界 |
| --- | --- | --- |
| Genus 本体 | 可用 | 版本检查、batch Tcl、license checkout 均通过。 |
| Innovus 本体 | 可用 | 版本检查、batch Tcl、license checkout 均通过。 |
| 推荐环境变量 | 可用 | `LD_LIBRARY_PATH` 应追加，不应覆盖。推荐使用 `${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}...` 写法。 |
| edahub Genus 脚本 | 部分可用 | `Nangate45Library` 和 `Sky130hdLibrary` adder synthesis 通过；`MiniAsap7Library` 失败。 |
| edahub Innovus 脚本 | 当前不存在 | 当前 checkout 未发现 Innovus manager/Tcl/PNR 脚本入口；因此只能测试 Innovus 本体。 |
| Genus 外层并发 | 至少 4 任务通过 | 未压测 5 个以上，不声明最大并发任务数。 |
| Innovus 外层并发 | 至少 4 session 通过 | 未压测 5 个以上，不声明最大并发 session 数。 |
| Genus 单任务线程 | `128` smoke 通过 | 接受 `max_cpus_per_server=128`，但小型 synthesis 的 mapping 阶段实际报告 `8 threads, 8 of 512 CPUs usable`；未测试 128 以上。 |
| Innovus 单任务 CPU | `-cpus 128` 最小 session 通过 | 命令被接受，但启动 license banner 仍明确显示当前 license 允许 `8 CPU jobs`；真实 P&R 默认仍建议从 `8` 起步。 |
| `lmutil` | 不可直接运行 | 缺 `/lib64/ld-lsb-x86-64.so.3`；影响 license 查询/诊断，不影响本次 Genus/Innovus 本体运行。 |

## 2. 测试输出目录

| 目录 | 用途 |
| --- | --- |
| `/tmp/tp_cadence_edahub_20260504_fGy47A` | 初始环境检查、Genus/Innovus 基础 batch smoke、edahub GenusManager smoke。 |
| `/tmp/tp_cadence_parallel_20260504_GrI2lB` | Genus/Innovus 外层并发测试，以及早期单任务 16/8/16 CPU smoke。 |
| `/tmp/tp_cadence_thread_limit_20260504_M5Cg2U` | 按 `128 -> 64 -> 32` 顺序执行的单任务线程/CPU 上限 smoke。 |
| `/tmp/tp_cadence_parallel8_20260504_ULzUxY` | 追加复测：4 个 Genus synthesis 并发任务，每任务 `max_threads=8`；4 个 Innovus batch session 并发任务，每 session `-cpus 8` / `setMultiCpuUsage -localCpu 8`。 |

这些目录是临时证据目录，不属于主仓库产物。若系统清理 `/tmp`，本文档中的结论仍保留，但原始日志可能不存在。

## 3. 环境变量

推荐环境入口：

```bash
export PATH="$PATH:/opt/eda/Cadence_DDI_23.14/bin"
export CDS_LIC_FILE=/opt/eda/Cadence_DDI_23.14/license/license.dat
export CDS_SKIP_OS_CHECK_ON_STARTUP=1
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9"
```

逐项确认：

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| Cadence 根目录 | 通过 | `/opt/eda/Cadence_DDI_23.14` 存在。 |
| `PATH` | 通过 | `genus` 和 `innovus` 均解析到 `/opt/eda/Cadence_DDI_23.14/bin/`。 |
| `CDS_LIC_FILE` | 通过 | `/opt/eda/Cadence_DDI_23.14/license/license.dat` 存在且可读；Genus/Innovus 日志均使用该 license path。 |
| `CDS_SKIP_OS_CHECK_ON_STARTUP=1` | 通过 | Genus/Innovus 在 Ubuntu 22.04 / Linux 6.8 上可 batch 启动。 |
| `LD_LIBRARY_PATH` | 通过 | RHEL9 Cadence runtime lib 路径存在并已追加到变量中。 |

### 3.1 `LD_LIBRARY_PATH` 写法说明

覆盖式写法，不推荐：

```bash
export LD_LIBRARY_PATH="/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9"
```

问题：会丢掉原有 `LD_LIBRARY_PATH`，可能影响 conda、OpenROAD、Xyce 或其它工具的动态库查找。

普通追加写法，可以临时使用：

```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:"/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9"
```

优点是保留原路径。缺点是原变量为空时会产生开头空路径项，形如 `:/opt/...`。

本文推荐写法：

```bash
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9"
```

这个写法只在原变量非空时添加冒号，既保留原路径，也避免无意义的开头空路径项。

## 4. Genus 验证

### 4.1 本体基础 smoke

执行内容：

```bash
timeout 60 genus -version
cat > genus_hello.tcl <<'TCL'
puts "TP_GENUS_SMOKE_OK"
exit 0
TCL
timeout 120 genus -no_gui -abort_on_error -overwrite -files genus_hello.tcl -log genus_hello.log
```

结果：通过。

关键证据：

- `genus -version` 返回码 `0`。
- 版本：`Genus(TM) Synthesis Solution, Version: 23.14-s090_1`。
- batch smoke 返回码 `0`。
- 日志显示 `Checking out license: Genus_Synthesis` 和 `Periodic Lic check successful`。
- Tcl 输出 `TP_GENUS_SMOKE_OK`。
- stderr 中有 `No LSB modules are available.`，但不影响 Genus batch 执行。
- 版本 banner 打印过 `This build will expire on 6/3/2025`。尽管该提示日期早于本次测试日期，工具在本次测试中仍可启动并 checkout license；后续若遇到启动或 license 问题，应重新向管理员确认 Cadence 安装和 license 状态。

### 4.2 edahub GenusManager smoke

为避免污染 `third_party/edahub/tests/tool/genus/temp`，本次没有直接跑 pytest，而是在 `/tmp` 下写最小 Python driver 调用：

- `edahub.tool.genus.genus_manager.GenusManager`
- `edahub/tool/genus/script/syn.tcl`
- `edahub/tool/genus/script/mmmc.tcl`
- `edahub/tool/genus/script/constraint.sdc`

测试环境：

```bash
export PYTHONPATH=/home/lisihang/thermal_placement/third_party/edahub
/home/lisihang/miniconda3/envs/thermal_placement/bin/python run_edahub_genus_smoke.py
```

测试结果：

| case | PDK class | design | 结果 | 输出 |
| --- | --- | --- | --- | --- |
| `adder_nangate45` | `Nangate45Library()` | `edahub/design/example/adder.v` | 通过 | `Adder.mapped.v` 4591 bytes，另有 SDF 和 timing/power/area/drc/qor reports。 |
| `adder_sky130hd` | `Sky130hdLibrary()` | 同上 | 通过 | `Adder.mapped.v` 5273 bytes，另有 SDF 和 timing/power/area/drc/qor reports。 |
| `adder_mini_asap7` | `MiniAsap7Library()` | 同上 | 失败 | Genus `read_mmmc` 阶段报 `TUI-24`，多个 ASAP7 Liberty 文件列表不能作为 `library` attribute 值。 |

结论：当前 edahub Genus flow 对 Nangate45/Sky130HD 可用于小型 smoke；`MiniAsap7Library` 与 edahub 自带 pytest skip 注释一致，当前不应作为 Genus 可通过路径。

### 4.3 Genus 并发和线程

外层并发测试：

| 并发数 | 每任务配置 | 结果 | 说明 |
| --- | --- | --- | --- |
| 2 | edahub Nangate45 adder synthesis，`max_threads=8` | 通过 | 两个任务均返回 `0`，wall time 约 23 s。 |
| 4 | edahub Nangate45 adder synthesis，`max_threads=8` | 通过 | 初测四个任务均返回 `0`，`GENUS_PARALLEL4_RC_ALL=0`，wall time 约 21 s；追加复测四个任务均返回 `0`，wall time 20.99 s。 |

追加复测证据：`/tmp/tp_cadence_parallel8_20260504_ULzUxY` 中 4 个 Genus 任务全部成功。每个任务日志均显示 `Checking out license: Genus_Synthesis`、`max_cpus_per_server = 8`、多处 `Number of threads: 8 * 1`、mapping 阶段 `8 of 512 CPUs usable` 和 `Normal exit`；每个任务均输出 `Adder.mapped.v`，大小 4591 bytes。

单任务线程测试：

| 测试顺序 | 配置 | 结果 | 说明 |
| --- | --- | --- | --- |
| 1 | `max_threads=128` | 通过 | 返回 `0`，wall time 约 21 s，日志记录 `max_cpus_per_server = 128`。 |
| 2 | `max_threads=64` | 未运行 | 因 128 已成功，按用户要求停止降测。 |
| 3 | `max_threads=32` | 未运行 | 因 128 已成功，按用户要求停止降测。 |

结论：Genus 当前已实测至少可同时运行 4 个独立 synthesis 任务，并且追加复测确认这 4 个任务可以同时各自配置并实际记录 `8` 线程相关日志。单任务在小型 edahub synthesis 中可接受 `max_cpus_per_server=128`。追加核查 128 线程日志后，Genus 没有出现 Innovus 那种 `8 CPU jobs allowed with the current license(s)` license banner；日志只显示 checkout `Genus_Synthesis`。但该小型 synthesis 的实际 mapping 阶段报告 `Multi-threaded Virtual Mapping (8 threads, 8 of 512 CPUs usable)` 和 `Multi-threaded Technology Mapping (8 threads, 8 of 512 CPUs usable)`，说明“接受 128”不等于每个综合阶段都会实际使用 128 线程。本报告未测试 128 以上，也未用大型真实设计验证 128 对 runtime 的实际收益。

## 5. Innovus 验证

### 5.1 本体基础 smoke

执行内容：

```bash
timeout 60 innovus -version
cat > innovus_hello.tcl <<'TCL'
puts "TP_INNOVUS_SMOKE_OK"
exit 0
TCL
timeout 120 innovus -no_gui -batch -abort_on_error -overwrite -files innovus_hello.tcl -log innovus_hello
```

结果：通过。

关键证据：

- `innovus -version` 返回码 `0`。
- 版本：`Innovus v23.14-s088_1`。
- batch smoke 返回码 `0`。
- 日志显示 `invs Innovus Implementation System 23.1 checkout succeeded`。
- 日志显示 `8 CPU jobs allowed with the current license(s)`。
- Tcl 输出 `TP_INNOVUS_SMOKE_OK`。
- 结束摘要显示 `0 warning(s), 0 error(s)`。

### 5.2 edahub Innovus 脚本状态

当前 `third_party/edahub` 中只发现 Genus 相关脚本：

```text
third_party/edahub/edahub/tool/genus/genus_manager.py
third_party/edahub/edahub/tool/genus/script/syn.tcl
third_party/edahub/edahub/tool/genus/script/mmmc.tcl
third_party/edahub/edahub/tool/genus/script/constraint.sdc
third_party/edahub/tests/tool/genus/test_synthesis.py
```

没有发现独立 Innovus manager、Innovus Tcl、floorplan/place/route/PNR 脚本入口。因此本次无法运行“edahub 的 Innovus flow”。但 Innovus 本体已经通过单独 batch smoke、并发 smoke 和 CPU 参数 smoke。

### 5.3 Innovus 并发和 CPU

外层并发测试：

| 并发数 | 每 session 配置 | 结果 | 说明 |
| --- | --- | --- | --- |
| 2 | `innovus -no_gui -batch -cpus 8` + 最小 Tcl | 通过 | 两个 session 均返回 `0`，wall time 约 20 s。 |
| 4 | `innovus -no_gui -batch -cpus 8` + 最小 Tcl | 通过 | 初测四个 session 均返回 `0`，`INNOVUS_PARALLEL4_RC_ALL=0`，wall time 约 20 s；追加复测四个 session 均返回 `0`，wall time 20.08 s。 |

追加复测证据：`/tmp/tp_cadence_parallel8_20260504_ULzUxY` 中 4 个 Innovus session 全部成功。每个 session 日志均显示 `Options: -no_gui -batch -cpus 8`、`checkout succeeded`、`8 CPU jobs allowed with the current license(s)`、`setMultiCpuUsage -localCpu 8` 和 `0 warning(s), 0 error(s)`。

每个 session 日志均显示：

- `invs Innovus Implementation System 23.1 checkout succeeded`
- `8 CPU jobs allowed with the current license(s)`
- `setMultiCpuUsage -localCpu 8`
- `0 warning(s), 0 error(s)`

单任务 CPU 参数测试：

| 测试顺序 | 配置 | 结果 | 说明 |
| --- | --- | --- | --- |
| 1 | `innovus -no_gui -batch -cpus 128`，Tcl 内 `setMultiCpuUsage -localCpu 128` | 通过 | 返回 `0`，wall time 约 21 s，结束摘要 `0 warning(s), 0 error(s)`。 |
| 2 | `-cpus 64` | 未运行 | 因 128 已成功，按用户要求停止降测。 |
| 3 | `-cpus 32` | 未运行 | 因 128 已成功，按用户要求停止降测。 |

重要边界：虽然 `-cpus 128` 和 `setMultiCpuUsage -localCpu 128` 在最小 batch session 中被接受，启动 license banner 仍明确显示 `8 CPU jobs allowed with the current license(s). Use setMultiCpuUsage to set your required CPU count.` 这里的 `8 CPU jobs` 是 Innovus 当前 checkout 到的 license 对该 session 可用 CPU job 数提示，不是服务器物理核心数；在更重的 place/route 阶段，超过该数量的请求可能被限制、降级、需要额外 CPU license，或只在具体命令执行时体现。因此本文不把 128 解释为真实 P&R 阶段已授权或一定有效使用 128 个 CPU job。

结论：Innovus 当前已实测至少可同时运行 4 个独立 batch session，并且追加复测确认这 4 个 session 可以同时各自配置 `-cpus 8` / `setMultiCpuUsage -localCpu 8`。单任务最小 session 接受 `-cpus 128`。正式 place/route 任务建议保守从 `-cpus 8` / `setMultiCpuUsage -localCpu 8` 起步；若尝试 128，必须在真实 flow 日志中确认没有 license warning、自动降级或 runtime 异常。

## 6. FlexNet / FlexLM / `lmutil`

FlexNet Publisher，旧称 FlexLM，是很多商业 EDA 工具使用的浮动 license 管理系统。工具启动时会向 license file 或 license server 请求某个 feature；请求成功后，对应功能才可使用。

`lmutil` 是 FlexNet/FlexLM 的通用 license utility，不是 Genus 或 Innovus 主程序。常见功能包括：

| 命令 | 用途 |
| --- | --- |
| `lmstat` | 查看 license server 状态、feature 总量、已用量和用户占用。 |
| `lmdiag` | 诊断 feature checkout 失败原因，如 server 不通、feature 不存在、版本不匹配或数量不足。 |
| `lmhostid` | 查看本机 hostid，用于 node-locked license 或 license server 绑定。 |
| `lmver` | 查看 FlexNet 工具版本。 |
| `lmreread` | 让 license server 重新读取 license file，通常需要管理员权限。 |
| `lmremove` | 移除异常残留的 license 占用，通常需要管理员权限且需谨慎。 |
| `lmborrow` / `lmpath` | 借用 license，或查看/设置 license path。 |

本机 license 文件形态：

- `CDS_LIC_FILE` 指向本地文件 `/opt/eda/Cadence_DDI_23.14/license/license.dat`。该文件没有 `SERVER` / `USE_SERVER` 记录，当前工具日志也把它显示为 license path，而不是远程 license server。
- 相关 feature 包括 `Genus_Synthesis`、`Genus_CPU_Opt`、`Innovus_Impl_System`、`Innovus_CPU_Opt`、`Innovus_MCPU_Opt` 和 `invs`，非敏感字段显示为 `permanent uncounted`，并带 `HOSTID=ANY`。本文不记录签名串、issuer 原文或序列号。
- 因此这份文件不像传统“license server 上有 N 个浮动 token”的 counted floating pool；更接近本地 uncounted feature license。它可以让工具 checkout 对应功能，但工具内部仍可能根据 feature/option 组合限制多 CPU job 数。
- Innovus 日志中的 `8 CPU jobs allowed with the current license(s)` 是工具在成功 checkout `invs` 后报告的当前 session 多 CPU job 配额。只允许 8 个 CPU job 对这种 license/feature 组合是正常表现，不表示机器只有 8 核，也不表示不能开多个独立 session；本次已验证 4 个 `-cpus 8` session 可并发启动。若要确认是否可超过 8，需要管理员提供更高并行度的 Cadence CPU/multi-CPU option，或在真实 P&R 中检查是否有降级/额外 checkout。

本机现状：

- `/opt/eda/Cadence_DDI_23.14/bin/lmutil` wrapper 会报：`exec: /opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/bin/lmutil: not found`。
- 真实 `lmutil/lmstat/lmdiag` 文件存在于 `INNOVUS231/tools.lnx86/bin/` 等目录。
- 这些真实二进制的 ELF interpreter 是 `/lib64/ld-lsb-x86-64.so.3`，而本机没有该路径。

影响：

- 受影响：不能直接用 `lmutil/lmstat/lmdiag` 做 license server 查询、feature 占用统计或 checkout 失败诊断。
- 不受影响：本次 Genus 和 Innovus 本体均能启动、执行 batch Tcl，并在各自日志中完成 license checkout。
- 若后续必须使用 `lmutil` 做 license 统计，需要由用户或管理员确认是否安装/补齐 LSB loader 或相应兼容包。本次没有修复系统/EDA 运行时依赖。

## 7. 推荐使用方法

### 7.1 Genus 基础 batch

```bash
cd /tmp
export PATH="$PATH:/opt/eda/Cadence_DDI_23.14/bin"
export CDS_LIC_FILE=/opt/eda/Cadence_DDI_23.14/license/license.dat
export CDS_SKIP_OS_CHECK_ON_STARTUP=1
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9"

cat > genus_hello.tcl <<'TCL'
puts "TP_GENUS_SMOKE_OK"
exit 0
TCL

genus -no_gui -abort_on_error -overwrite -files genus_hello.tcl -log genus_hello.log
```

### 7.2 Innovus 基础 batch

```bash
cd /tmp
export PATH="$PATH:/opt/eda/Cadence_DDI_23.14/bin"
export CDS_LIC_FILE=/opt/eda/Cadence_DDI_23.14/license/license.dat
export CDS_SKIP_OS_CHECK_ON_STARTUP=1
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9"

cat > innovus_hello.tcl <<'TCL'
puts "TP_INNOVUS_SMOKE_OK"
setMultiCpuUsage -localCpu 8
exit 0
TCL

innovus -no_gui -batch -cpus 8 -abort_on_error -overwrite -files innovus_hello.tcl -log innovus_hello
```

### 7.3 edahub GenusManager smoke

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
export PATH="$PATH:/opt/eda/Cadence_DDI_23.14/bin"
export CDS_LIC_FILE=/opt/eda/Cadence_DDI_23.14/license/license.dat
export CDS_SKIP_OS_CHECK_ON_STARTUP=1
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9"
export PYTHONPATH=/home/lisihang/thermal_placement/third_party/edahub
```

调用要求：

- 使用 `/home/lisihang/miniconda3/envs/thermal_placement/bin/python`。
- `rundir` 放在 `/tmp` 或明确的非 `third_party` 输出目录。
- 优先使用 `Nangate45Library()` 或 `Sky130hdLibrary()` 做 smoke。
- 不要把 `MiniAsap7Library()` 视为当前 Genus 可通过路径。

## 8. 后续建议

- 若要把 Cadence Genus/Innovus 纳入正式 Gemmini Stage 2 路线，需要先明确是否改变 active plan。目前 active plan 仍以 OpenROAD/ORFS + reduced ASAP7 为主线。
- 若要评估 Innovus `-cpus 128` 的真实价值，应使用非主仓库污染的独立 P&R smoke，并检查是否出现 license warning、CPU 降级、内存异常或 runtime 反而变差。
- 若需要 license 使用统计，应先修复 `lmutil` 运行时依赖，或请管理员在 license server 侧提供 feature 使用情况。
