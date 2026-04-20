# Gemmini Thermal 问题与解决记录

更新时间：2026-04-20

本文记录目前推进 Gemmini 热验证过程中遇到的关键问题、根因、解决方式和验证方法，目的是降低后续重复试错成本。

## 1. sbt / coursier / ivy 默认写到 `$HOME`，在当前环境下不稳定

### 现象

- Chipyard 的 sbt 过程偶发失败
- 会尝试写入默认 `~/.ivy2`、`~/.sbt`、`~/.cache/coursier`
- 在受限环境下容易碰到锁文件、权限或缓存脏状态问题

### 根因

- Chipyard / sbt 默认使用用户目录缓存
- 当前项目更适合将缓存收敛到仓库内，方便复现和清理

### 解决方法

在 [env_gemmini_thermal.sh](/home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh) 中重定向缓存到仓库本地：

- `TP_CACHE_ROOT`
- `SBT_GLOBAL_BASE`
- `SBT_BOOT_DIR`
- `SBT_IVY_HOME`
- `COURSIER_CACHE`
- `COURSIER_CONFIG_DIR`
- `MPLCONFIGDIR`

### 验证

- `source tools/env_gemmini_thermal.sh`
- `cd "$CHIPYARD_HOME" && sbt -batch -Dsbt.log.noformat=true 'show version'`

## 2. 代理导致 GitHub / curl / launcher 下载不稳定

### 现象

- GitHub 下载 CIRCT、子模块时出现 TLS EOF、502、连接异常
- sbt launcher / 某些网络拉取行为不稳定

### 根因

- shell 中存在本地代理环境变量
- 某些目标站点在当前代理链路下不稳定

### 解决方法

对关键下载命令显式去掉代理环境：

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY ...
```

### 验证

- CIRCT 压缩包能成功下载并解包
- 子模块 update 能成功完成

## 3. Chipyard 多个子模块处于“gitlink 在，但工作树文件被删空”的损坏状态

### 现象

- 子模块目录里只剩 `.git` 或少量 `target/` 产物
- `git status --short` 显示大量 tracked file 为 `D`
- 构建时出现大量看似“代码缺失”的错误

### 根因

- 本地工作树曾被破坏或清理不完整
- 子模块 commit 还在，但工作区内容不在了

### 解决方法

对这类子模块，直接从子模块自身 `HEAD` 恢复 tracked 文件：

```bash
git -C <submodule> archive HEAD | tar -x -C <submodule>
git -C <submodule> add -A
```

已实际处理过的典型路径包括：

- `third_party/chipyard/tools/cde`
- `third_party/chipyard/generators/rerocc`
- `third_party/chipyard/generators/bar-fetchers`
- `third_party/chipyard/generators/rocc-acc-utils`
- `third_party/chipyard/tools/firrtl2`
- `third_party/chipyard/tools/rocket-dsp-utils`
- `third_party/chipyard/tools/install-circt`
- `third_party/chipyard/tools/DRAMSim2`

### 验证

```bash
git -C <submodule> status --short
```

如果恢复正确，不应再看到大批量 `D` 的 tracked 文件。

## 4. 嵌套子模块没拉全，导致 Scala / FIRRTL / DSP 依赖缺失

### 现象

- 构建时缺少 `cde`、`hardfloat`、`torture/env`、`dsptools`、`constellation/espresso` 等
- sbt 可以启动，但编译会在某些工程引用处失败

### 根因

- `third_party/chipyard` 顶层子模块存在
- 但更深层的 nested submodule 并未初始化

### 解决方法

针对缺失路径做定点 `git submodule update --init`，而不是盲目全仓库递归拉取。

这次已补齐的代表路径包括：

- `third_party/chipyard/generators/constellation/espresso`
- `third_party/chipyard/generators/saturn/riscv-vector-tests`
- `third_party/chipyard/tools/rocket-dsp-utils/tools/rocket-chip`
- `third_party/chipyard/tools/rocket-dsp-utils/tools/dsptools`
- 以及其下若干 nested dependency

### 验证

- Chipyard sbt 项目可以正常解析并进入编译阶段
- `scripts/run_gemmini_rtl_generation.sh` 能成功跑通

## 5. 主机没有 `jq`，但 Chipyard 生成流程会调用

### 现象

- RTL 生成流程中断
- `*.appended.anno.json` 初次生成异常

### 根因

- Chipyard make 过程中依赖 `jq`
- 当前环境未安装系统 `jq`

### 解决方法

添加本地轻量 shim：

- [tools/bin/jq](/home/lisihang/thermal_placement/tools/bin/jq)

当前支持的最小子集已经覆盖实际用到的场景：

- `jq -s '[.[][]]' ...`
- `jq -r .version`

### 验证

- 重新生成 `*.appended.anno.json`
- `scripts/run_gemmini_rtl_generation.sh` 成功完成

## 6. 没有 `firtool` 时，FIRRTL 已生成，但无法完成 Verilog lower

### 现象

- `.fir`、`.anno.json` 已经能生成
- 但 split Verilog / hierarchy 导出停在 FIRRTL 后端阶段

### 根因

- Chipyard 当前流程实际依赖 CIRCT `firtool`
- 旧版 `firrtl2` jar 无法可靠替代这条主路径

### 解决方法

安装本地 CIRCT/firtool：

- `tools/circt`

并在环境脚本中暴露：

- `CIRCT_HOME`
- `FIRTOOL_BIN`

### 验证

```bash
firtool --version
scripts/run_gemmini_rtl_generation.sh
```

结果：RTL 导出成功，split Verilog 与 hierarchy json 已生成。

## 7. `firrtl2` fallback 不适合当前产物版本

### 现象

- 尝试用 `firrtl2` assembly jar 作为 fallback 时失败

### 根因

- 当前 emitted FIRRTL 版本为 `3.3.0`
- 该 fallback 驱动无法稳定兼容当前流程

### 解决方法

- 不再把 `firrtl2` 作为主方案
- 统一以 `firtool` 为准

### 验证

- 使用 `firtool` 的正式流程已成功

## 8. Verilator debug simulator 构建时，`DRAMSim2` 暴露出损坏工作树

### 现象

- `make -C third_party/chipyard/sims/verilator CONFIG=GemminiRocketConfig debug`
- 报错：`No rule to make target 'libdramsim.a'`

### 根因

- `third_party/chipyard/tools/DRAMSim2` 目录存在
- 但 tracked 文件被删空，只剩 `.git`

### 解决方法

按“损坏子模块恢复”方法，从子模块 `HEAD` 恢复源码后重新编译。

### 验证

- `make -C third_party/chipyard/tools/DRAMSim2 libdramsim.a` 成功

## 9. 当前真正阻塞 Phase B 的不是 Verilator，而是 RISC-V toolchain

### 现象

- `gemmini-rocc-tests` 无法编译 bare-metal binary
- Chipyard debug simulator 构建在后续阶段报 `RISCV is unset`

### 根因

当前机器上没有发现可直接使用的：

- `riscv64-unknown-elf-gcc`
- 对应的 `RISCV` prefix

### 当前结论

如果要沿用 Chipyard 官方 `run-binary-debug` 路线，RISC-V toolchain 目前仍是关键前提。

这不代表后续研究一定要长期依赖完整软件栈，但至少在：

- bare-metal workload 构建
- 使用官方仿真入口加载 ELF

这两步上，当前流程仍要求它存在。

### 后续建议

先确认主机上是否已有现成 prefix；如果没有，再决定：

1. 安装 / 构建一套最小 RISC-V toolchain
2. 或改走更底层的“直接加载已有 ELF / memory image”路线

## 10. 后续构建建议默认开多核，但最多 128

### 原因

- RTL 生成、Verilator 编译、后续综合/实现都能显著受益于多核
- 当前机器 `nproc` 可返回远超必要的核数，直接无限使用会造成内存、IO 和调度压力

### 当前处理

环境脚本已统一限制：

- `TP_MAX_JOBS` 默认值为 `128`
- `MAKE_JOBS` 未设置时取 `nproc`，但会被钳制到 `TP_MAX_JOBS`
- 用户显式设置 `MAKE_JOBS>128` 时，也会被钳制到 `128`

涉及脚本：

- [run_gemmini_rtl_generation.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_rtl_generation.sh)
- [build_gemmini_workloads.sh](/home/lisihang/thermal_placement/scripts/build_gemmini_workloads.sh)
- [run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh)

### 推荐用法

```bash
source tools/env_gemmini_thermal.sh
echo "$MAKE_JOBS"
```

再执行各阶段脚本。

## 11. 项目本地 bare-metal toolchain 解包后，交叉 GCC 找不到正确的 `as/ld`

### 现象

- `riscv64-unknown-elf-gcc -c` 初始会调用宿主 `as`
- 或者为了让它找到 RISC-V `as`，把 `$RISCV/lib/riscv64-unknown-elf/bin` 放到全局 PATH 后，宿主 `gcc` 又会误用 RISC-V `as`
- `riscv-isa-sim/configure` 报：`C compiler cannot create executables`

### 根因

- Debian 包里的 `gcc-riscv64-unknown-elf` 是按 `/usr` 布局构建的
- 项目本地解包到 `tools/riscv` 后，GCC 程序搜索路径需要重定位
- `COMPILER_PATH` 如果放在全局环境里，会同时影响宿主 `gcc`

### 解决方法

- 只在 [riscv64-unknown-elf-gcc](/home/lisihang/thermal_placement/tools/bin/riscv64-unknown-elf-gcc) 和 [riscv64-unknown-elf-g++](/home/lisihang/thermal_placement/tools/bin/riscv64-unknown-elf-g++) 包装器里设置：
  `COMPILER_PATH=$TP_ROOT/tools/riscv/lib/riscv64-unknown-elf/bin`
- 不再把 generic `as/ld` 所在目录放入全局 PATH

### 验证

- 宿主 `gcc` 使用 `/usr/bin/as`
- 交叉 `riscv64-unknown-elf-gcc -c` 使用 `tools/riscv/lib/riscv64-unknown-elf/bin/as`

## 12. `libgloss` 自举依赖和 multilib 组合会导致本地构建失败

### 现象

- `libgloss/configure` 报 `cannot find -lgloss`
- 放置空 `libgloss.a` 后，又遇到 picolibc 默认 `crt0.o` 缺少 `__stack`、`__data_start` 等 linker symbol
- 默认 multilib 构建进入 `rv32e/rv32ea` 后，`crt0.S` 因使用 `x16-x31` 报 illegal operands

### 根因

- 当前交叉 GCC 默认 specs 会带 `-lgloss`，但 `libgloss` 还没构建
- picolibc 默认启动文件不适合 `libgloss` configure 的普通链接探测
- Gemmini 当前目标是 RV64，不需要构建全量 RV32E multilib

### 解决方法

- configure 前先放置临时空 `libgloss.a`
- configure 阶段使用：

```bash
CC='riscv64-unknown-elf-gcc -nostartfiles' \
../configure --prefix="$RISCV/riscv64-unknown-elf" \
  --host=riscv64-unknown-elf \
  --disable-multilib
```

- 安装后将 `libgloss.a` 指向真实 `libgloss_htif.a`

### 验证

- `tools/riscv/riscv64-unknown-elf/lib/libgloss_htif.a` 存在
- `riscv64-unknown-elf-gcc -specs=htif.specs hello.c -o hello.elf` 成功生成 RV64 ELF

## 13. `htif_nano.specs` 不适合当前最小本地前缀，优先使用 `htif.specs`

### 现象

- `riscv64-unknown-elf-gcc -specs=htif_nano.specs ...` 报缺少 `nano.specs`
- 将 `nano.specs` 指向 `picolibc.specs` 后，又会遇到 `picolibc.ld` 搜索问题

### 根因

- 当前本地工具链由 Ubuntu/Debian `gcc-riscv64-unknown-elf`、`binutils-riscv64-unknown-elf`、`picolibc-riscv64-unknown-elf` 解包组合而来
- 它不是完整 newlib/newlib-nano 布局
- `htif_nano.specs` 假设存在 newlib nano specs

### 当前处理

- 对当前 Gemmini workload 构建，`gemmini-rocc-tests/bareMetalC` 本身使用 `-nostdlib -nostartfiles -T test.ld`，不依赖 `htif_nano.specs`
- 对通用 HTIF smoke test，使用 `htif.specs` 而不是 `htif_nano.specs`

### 验证

```bash
riscv64-unknown-elf-gcc -specs=htif.specs /tmp/hello_htif.c -o /tmp/hello_htif.elf
```

结果：生成静态 RV64 ELF，包含 `.htif` section。

## 14. `gemmini-rocc-tests` 顶层 Makefile 不支持直接构建单个 bareMetalC target

### 现象

执行：

```bash
scripts/build_gemmini_workloads.sh mvin_mvout
```

初始失败：`No rule to make target 'mvin_mvout-baremetal'`

### 根因

- `gemmini-rocc-tests/build/Makefile` 顶层只暴露目录级 target
- `mvin_mvout-baremetal` 这类规则定义在 `build/bareMetalC` 子目录对应 Makefile 中

### 解决方法

更新 [build_gemmini_workloads.sh](/home/lisihang/thermal_placement/scripts/build_gemmini_workloads.sh)：

- 无参数时仍走顶层 `make BAREMETAL_ONLY=1`
- 有单个或多个 workload 参数时，进入 `build/bareMetalC` 调子目录 Makefile

### 验证

```bash
scripts/build_gemmini_workloads.sh mvin_mvout
```

结果：生成 [mvin_mvout-baremetal](/home/lisihang/thermal_placement/sim/binaries/GemminiRocketConfig/mvin_mvout-baremetal)。

## 15. Verilator debug simulator 可能缓存空 `RISCV` 路径

### 现象

- 初次 debug simulator 构建失败：
  `fatal error: fesvr/memif.h: No such file or directory`
- 编译命令里出现 `-I/include`，而不是 `-I$RISCV/include`

### 根因

- 之前在 `RISCV` 未设置或路径不完整时生成过 `VTestDriver.mk`
- 后续直接 `make debug` 会复用旧生成目录

### 解决方法

先清掉 debug simulator 生成目录，再重新构建：

```bash
source tools/env_gemmini_thermal.sh
make -C third_party/chipyard/sims/verilator CONFIG=GemminiRocketConfig clean-sim-debug
make -C third_party/chipyard/sims/verilator CONFIG=GemminiRocketConfig -j "$MAKE_JOBS" debug
```

### 验证

- 新编译命令包含 `-I/home/lisihang/thermal_placement/tools/riscv/include`
- `simulator-chipyard.harness-GemminiRocketConfig-debug` 构建成功

## 16. `set -u` 下 source 环境脚本会因 `RISCV` 未定义失败

### 现象

从干净 shell 直接执行：

```bash
scripts/run_thermal_smoke_flow.sh
```

失败：

```text
/home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh: line 66: RISCV: unbound variable
```

### 根因

- `run_thermal_smoke_flow.sh` 使用 `set -euo pipefail`
- [env_gemmini_thermal.sh](/home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh) 中 RISC-V prefix 候选列表直接引用了 `$RISCV`
- 在 `set -u` 环境下，未定义变量会立即触发 shell 错误

### 解决方法

将候选列表里的 `$RISCV` 改成 `${RISCV:-}`：

```bash
for riscv_candidate in \
  "${RISCV:-}" \
  "$TP_ROOT/tools/riscv" \
  ...
```

### 验证

从干净 shell 直接执行：

```bash
scripts/run_thermal_smoke_flow.sh
```

不再因 `RISCV` 未定义退出，并能自动发现 [tools/riscv](/home/lisihang/thermal_placement/tools/riscv)。

## 17. Verilator debug + VCD 的 smoke 超时参数不能过紧

### 现象

最初使用：

- `SMOKE_MAX_CYCLES=10000`
- `SMOKE_TIMEOUT_SECS=20`

运行 [run_thermal_smoke_flow.sh](/home/lisihang/thermal_placement/scripts/run_thermal_smoke_flow.sh) 时，外层 `timeout` 返回 `124`，且没有生成 `thermal_smoke.vcd`：

```text
smoke VCD was not generated: /home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/thermal_smoke.vcd
```

### 根因

- `GemminiRocketConfig` debug simulator 带 VCD 时开销较大
- 外层 `timeout` 杀进程时，VCD/stdout/stderr 可能还没有完成落盘
- 当前 smoke 目标是验证工具链端到端连通性，不需要 10000 cycle

### 解决方法

将 smoke 默认参数改为：

```bash
SMOKE_MAX_CYCLES=1000
SMOKE_TIMEOUT_SECS=60
```

并在 VCD 未生成时额外打印：

- simulator status
- stdout log path
- stderr log path

### 验证

执行：

```bash
scripts/run_thermal_smoke_flow.sh
```

结果：

- Verilator debug simulator 生成 [thermal_smoke.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/thermal_smoke.vcd)
- [extract_vcd_activity.py](/home/lisihang/thermal_placement/scripts/extract_vcd_activity.py) 解析到 `32687` 个信号
- 生成 [thermal_smoke_region_activity.csv](/home/lisihang/thermal_placement/sim/activity/thermal_smoke_region_activity.csv)
- HotSpot 生成 [thermal_smoke.ttrace](/home/lisihang/thermal_placement/thermal/steady/thermal_smoke.ttrace)

当前 `sim_status=1` 是 `+max-cycles=1000` 触发 TestDriver timeout 的预期结果；对 smoke flow 来说，判断标准是 VCD、activity CSV 和 HotSpot 输出是否成功生成。

## 18. Smoke flow 中 0-activity 区域也需要保留到 HotSpot 输入

### 现象

第一版 smoke 活动提取可以生成 region CSV，但只输出当前 VCD 中实际匹配到信号的区域。随后 [export_smoke_hotspot_inputs.py](/home/lisihang/thermal_placement/scripts/export_smoke_hotspot_inputs.py) 又过滤了 `signal_count=0` 的行。

结果是 `.flp` / `.ptrace` 中只有：

- `controller`
- `load_store_dma`
- `non_gemmini_context`
- `pe_array`
- `tl_soc_glue`

缺少 `accumulator`、`scratchpad`、`gemmini_other` 等核心 bucket。

### 根因

- 当前 `thermal_smoke.c` 只是最小 bare-metal 程序，没有发 Gemmini 指令
- 很短的 VCD 中不一定能命中所有 Gemmini 子模块信号
- 如果 HotSpot 输入列随 workload 改变，后续比较不同 workload 时会增加额外对齐成本

### 解决方法

- [extract_vcd_activity.py](/home/lisihang/thermal_placement/scripts/extract_vcd_activity.py) 现在会预先初始化 hierarchy map 中的所有 category
- [export_smoke_hotspot_inputs.py](/home/lisihang/thermal_placement/scripts/export_smoke_hotspot_inputs.py) 不再过滤 `signal_count=0` 的区域
- 0-activity 区域仍保留 `base-power`，默认 `0.05`

### 验证

重新执行：

```bash
scripts/run_thermal_smoke_flow.sh
```

当前 [thermal_smoke.flp](/home/lisihang/thermal_placement/thermal/floorplans/thermal_smoke.flp)、[thermal_smoke.ptrace](/home/lisihang/thermal_placement/thermal/power/thermal_smoke.ptrace)、[thermal_smoke.ttrace](/home/lisihang/thermal_placement/thermal/steady/thermal_smoke.ttrace) 都包含 8 个稳定 bucket：

- `accumulator`
- `controller`
- `gemmini_other`
- `load_store_dma`
- `non_gemmini_context`
- `pe_array`
- `scratchpad`
- `tl_soc_glue`
