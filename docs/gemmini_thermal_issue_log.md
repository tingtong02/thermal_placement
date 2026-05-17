# Gemmini Thermal 问题与解决记录

更新时间：2026-05-12

本文记录目前推进 Gemmini 热验证过程中遇到的关键问题、根因、解决方式和验证方法，目的是降低后续重复试错成本。

## 0. 2026-05-05 active backend 切换记录

当前 active plan 已从 OpenROAD/ORFS/reduced-ASAP7/proxy 路线切换到 Cadence Genus + Innovus/full-ASAP7 路线：

- active plan: `docs/phase0tophase4_cadence_asap7_plan.md`
- legacy docs: `docs/references/legacy_openroad_proxy/`
- full ASAP7: `/home/lisihang/asap7`, default `asap7sc7p5t_28` 1x collateral
- Liberty cache: `.cache/asap7/asap7sc7p5t_28/NLDM`
- fake SRAM source: `/home/lisihang/fake_sram`

旧 OpenROAD/ORFS/reduced-ASAP7 Stage 2 结果不得作为当前 Stage 3/4 正式输入。

## 0.1 Full ASAP7 Liberty 是 `.lib.7z`，不能直接被现有 edahub adapter 发现

### 现象

- `/home/lisihang/asap7/asap7sc7p5t_28/LIB/NLDM` 内 standard-cell Liberty 为 `.lib.7z`。
- 旧 edahub `Asap7Library` adapter 查找的文件模式与当前 full PDK 不匹配，发现 `lib_files=0`。

### 解决方法

新增 `scripts/prepare_asap7_liberty_cache.py`，从 `.lib.7z` 解压 RVT/LVT/SLVT TT NLDM Liberty 到 `.cache/asap7/asap7sc7p5t_28/NLDM`。解压产物是 derived cache，不提交。

### 验证

```bash
source tools/env_gemmini_thermal.sh
python scripts/prepare_asap7_liberty_cache.py --check-only
python scripts/prepare_asap7_liberty_cache.py
```

## 0.2 Innovus 读取 full ASAP7 LEF 应使用 Cadence 命令 `read_physical -lef`

### 现象

Innovus smoke 中尝试 `read_lef` 失败，报 invalid command。

### 解决方法

使用：

```tcl
read_physical -lef $lefs
```

### 验证

2026-05-05 已验证 Innovus `v23.14-s088_1` 可读取：

- `/home/lisihang/asap7/asap7sc7p5t_28/techlef_misc/asap7_tech_1x_201209.lef`
- `/home/lisihang/asap7/asap7sc7p5t_28/LEF/asap7sc7p5t_28_R_1x_220121a.lef`

## 0.3 fake_sram 外部仓库当前 dirty，不直接修改

### 现象

`/home/lisihang/fake_sram` 是用户提供的外部 fake SRAM source/collateral。当前 worktree 有未提交改动和未跟踪文件。

### 当前策略

本仓库只新增适配层和检查脚本，默认不修改外部 fake_sram 仓库。若后续必须调整 generator，应先报告改动边界，再由用户确认是否修改外部仓库。

## 0.4 ASAP7 Liberty cache 初次生成失败：thermal_placement PATH 缺少 extractor

### 现象

2026-05-05 运行：

```bash
source tools/env_gemmini_thermal.sh
python scripts/prepare_asap7_liberty_cache.py
```

失败输出：

```text
missing extractor: install or expose bsdtar or 7z
```

### 根因

`bsdtar` 存在于 `/home/lisihang/miniconda3/bin/bsdtar`，但激活 `thermal_placement` conda 环境后该路径不在 active PATH 中。`7z` 未发现。

### 处理计划

更新 `scripts/prepare_asap7_liberty_cache.py`，除 PATH 外显式检查 `/home/lisihang/miniconda3/bin/bsdtar`。这不安装新依赖，也不修改非仓库工具载荷。

### 验证

修复后重跑通过：

```text
ASAP7 Liberty cache ready: cache=/home/lisihang/thermal_placement/.cache/asap7/asap7sc7p5t_28/NLDM libs=15 extracted=15 vt=RVT,LVT,SLVT corner=TT
```

## 0.5 fake SRAM Liberty 可读但 PVT/area 需要适配

### 现象

2026-05-05 早期 Genus manifest smoke 成功读取 15 个 full-ASAP7 NLDM Liberty 和外部 `RISCY` fake SRAM Liberty，但报告：

- fake SRAM nominal PVT 与 ASAP7 stdcell PVT 不一致：fake SRAM `0.9V/125C`，ASAP7 stdcell TT libs 为 `0.7V/25C`。
- fake SRAM cell 无 `area` attribute，Genus 默认面积为 0。

### 当前判断

这不是 read-lib blocker，但会影响后续综合/面积/功耗可信度。用户已要求 fake SRAM 从当前 Gemmini 需求出发，不直接使用外部仓库已有 macro 类型。因此 active 处理方式已改为：

- `scripts/prepare_gemmini_fake_sram_collateral.py` 解析 active Gemmini RTL filelist 和 `Gemmini` top 的可达模块。
- 当前可达 external memory macros 为 `mem_ext` 和 `mem_0_ext`。
- 生成 `.cache/fake_sram/asap7/Gemmini/` 下的 Liberty、LEF、Verilog stub 和 manifest。
- Liberty 使用 ASAP7 TT `0.7V/25C`。
- LEF 尺寸和面积按 `/home/lisihang/fake_sram` 的生成方法参数估算。
- 外部 `/home/lisihang/fake_sram/results/asap7` 只作为 legacy inventory 或方法参考，不作为 active macro 类型来源。

不要直接修改 `/home/lisihang/fake_sram` 外部仓库，除非用户单独批准。

### 验证

当前生成结果：

```text
mem_ext: wrapper=mem depth=4096 width=128 kind=1rw size=109.89x220.05um
mem_0_ext: wrapper=mem_0 depth=512 width=512 kind=1r1w size=108.702x217.62um
```

已重跑：

- Genus read-lib smoke：读取 15 个 ASAP7 NLDM libs 加 2 个 Gemmini fake SRAM libs，0 error。
- Genus tiny synthesis smoke：实例化 `mem_ext` 的 top 可完成 `syn_generic` 和 `write_hdl`，0 error。
- Innovus read-physical smoke：读取 full ASAP7 tech/stdcell LEF 加 2 个 Gemmini fake SRAM LEF，0 error。

保留 caveat：当前 fake SRAM Liberty 是 abstract timing model，Genus 会报告部分 output pin 缺少 `function`/timing arc，以及 Verilog stub 的 `black_box` attribute warning。该状态足够用于本轮 standard-cell 热仿真 flow bring-up；正式 synthesis 前需要在 Stage 2 报告中记录这些 warning。

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

## 19. 小 GEMM 的完整功能验证需要明显高于 200k cycles

### 现象

第一次运行 [run_small_gemm_thermal_flow.sh](/home/lisihang/thermal_placement/scripts/run_small_gemm_thermal_flow.sh) 时使用：

```bash
GEMM_MAX_CYCLES=200000
```

结果可以生成 VCD、activity CSV 和 HotSpot 输出，但 stdout 只有 UART 初始化，没有 `small-gemm-start` / `small-gemm-ok`。

自动报告显示：

```text
functional_ok_seen: False
sim_status: 1
```

### 根因

- `GemminiRocketConfig` debug simulator 启动到 bare-metal main 需要较长仿真时间
- 200k cycles 只能覆盖早期启动和部分 SoC 活动，不足以完成 small GEMM
- 带 VCD 的运行会显著放大文件大小和 walltime

### 解决方法

先用无 VCD 长运行确认功能完成点：

```bash
source tools/env_gemmini_thermal.sh
timeout 180s third_party/chipyard/sims/verilator/simulator-chipyard.harness-GemminiRocketConfig-debug \
  +permissive +dramsim \
  +dramsim_ini_dir="$CHIPYARD_HOME/generators/testchipip/src/main/resources/dramsim2_ini" \
  +max-cycles=5000000 \
  +permissive-off sim/binaries/GemminiRocketConfig/small_gemm-baremetal
```

观察到：

- `small-gemm-start`
- `small-gemm-ok`
- Verilator `$finish` 约 `566us`

随后用完整 VCD 流程重跑：

```bash
GEMM_MAX_CYCLES=800000 GEMM_TIMEOUT_SECS=600 scripts/run_small_gemm_thermal_flow.sh
```

### 验证

最终结果：

- `sim_status=0`
- stdout 出现 `small-gemm-ok`
- [small_gemm.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/small_gemm.vcd) 生成，约 `1.6GB`
- [small_gemm_region_activity.csv](/home/lisihang/thermal_placement/sim/activity/small_gemm_region_activity.csv) 生成
- [small_gemm.ttrace](/home/lisihang/thermal_placement/thermal/steady/small_gemm.ttrace) 生成
- [small_gemm_report.md](/home/lisihang/thermal_placement/reports/small_gemm/small_gemm_report.md) 生成

后续建议：多 workload 实验不宜直接保存全程 VCD；应优先评估 FST、VCD 截窗或分阶段 trace。

## 20. PACT 依赖闭环：Xyce / OpenMPI / Libtool 本地安装

### 现象

PACT 的 SuperLU Python 路径已能启动，但 SPICE 路径和 parallel thermal simulation 仍缺少外部依赖：

```bash
command -v Xyce
command -v mpirun
command -v mpicc
command -v libtoolize
```

初始检查均未发现可执行命令。OpenMPI git 源码树还需要先运行 `autogen.pl`，而当前容器缺 `libtoolize`，因此直接从 git 源码构建 OpenMPI 会卡住。

### 根因

- 当前容器没有系统级 `Xyce`、`OpenMPI 3.1.4`、GNU Libtool。
- 无 passwordless sudo，不能依赖 `apt install` 修改系统环境。
- 代理环境变量会导致部分 release tarball 下载出现 TLS EOF 或 502。
- Xyce SuperBuild 需要 Fortran 编译器、LAPACK 和 `libgfortran.so.5` runtime；这些也不能假设系统中已经完整提供。

### 解决方法

所有依赖均安装到当前仓库内：

| 工具 | 安装路径 | 说明 |
| --- | --- | --- |
| GNU Libtool | `tools/libtool` | 从 `libtool-2.4.7.tar.gz` 构建 |
| OpenMPI | `tools/openmpi-3.1.4` | 从 OpenMPI 3.1.4 release tarball 构建，启用 C MPI，禁用 MPI Fortran |
| Xyce | `tools/xyce-7.4-build/install` | 从 `third_party/Xyce` 的 `Release-7.4.0` SuperBuild 构建 |
| local apt sysroot | `tools/apt-sysroot` | 局部解包 LAPACK、gfortran、libgfortran runtime |
| gfortran wrapper | `tools/bin/gfortran` | 为局部 `gfortran-11` 补 `-B` 搜索路径，避免 `liblto_plugin.so` 找不到 |

下载时使用不带代理的命令绕过当前代理问题：

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY <command>
```

OpenMPI 使用 release tarball，而不是 git 源码树：

```bash
./configure \
  --prefix=/home/lisihang/thermal_placement/tools/openmpi-3.1.4 \
  --disable-mpi-fortran \
  --disable-static \
  --enable-shared \
  --without-verbs \
  --without-cuda
make -j "$MAKE_JOBS"
make install
```

Xyce SuperBuild 使用 Ninja 和本地 LAPACK：

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

如果 Xyce 最终链接阶段报 `libgfortran.so.5` 找不到，需要在 `tools/xyce-7.4-build/Xyce-prefix/src/Xyce-build` 中补一次 linker flags 后继续构建：

```bash
cmake \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath,/home/lisihang/thermal_placement/tools/apt-sysroot/usr/lib/x86_64-linux-gnu -Wl,-rpath-link,/home/lisihang/thermal_placement/tools/apt-sysroot/usr/lib/x86_64-linux-gnu -L/home/lisihang/thermal_placement/tools/apt-sysroot/usr/lib/x86_64-linux-gnu" \
  .
```

随后继续：

```bash
source tools/env_gemmini_thermal.sh
cd tools/xyce-7.4-build
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY FC=gfortran cmake --build . -j "$MAKE_JOBS"
```

### 验证

环境入口 [env_gemmini_thermal.sh](/home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh) 已接入：

```bash
source tools/env_gemmini_thermal.sh
command -v Xyce mpirun mpicc libtoolize gfortran
```

结果：

```text
/home/lisihang/thermal_placement/tools/xyce-7.4-build/install/bin/Xyce
/home/lisihang/thermal_placement/tools/openmpi-3.1.4/bin/mpirun
/home/lisihang/thermal_placement/tools/openmpi-3.1.4/bin/mpicc
/home/lisihang/thermal_placement/tools/libtool/bin/libtoolize
/home/lisihang/thermal_placement/tools/bin/gfortran
```

版本检查：

```text
Xyce Release 7.4.0-opensource
mpirun (Open MPI) 3.1.4
mpicc: Open MPI 3.1.4 (Language: C)
libtoolize (GNU libtool) 2.4.7
GNU Fortran 11.4.0
```

OpenMPI C smoke test：

```text
rank 0 of 2
rank 1 of 2
```

Xyce 最小 `.OP` 电路 smoke test 完成：

```text
***** Solution Summary *****
        Number Successful Steps Taken:          1
        Number Failed Steps Attempted:          0
***** End of Xyce(TM) Simulation
```

### 当前限制

当前 Xyce 是 serial 构建。Xyce SuperBuild 日志显示 Trilinos 未启用 MPI，因此：

- PACT 的 SPICE_steady / SPICE_transient 路径具备继续验证条件。
- PACT parallel Xyce 路径还没有闭合；后续需要重新构建 MPI-enabled Trilinos/Xyce，并重新评估是否需要带 Fortran 支持的 OpenMPI。

详细安装状态记录见 [pact_slang_sv2v_yosys_slang_install_report.md](/home/lisihang/thermal_placement/docs/pact_slang_sv2v_yosys_slang_install_report.md)。

## 21. PACT 在 pandas 3 / NumPy 2 环境下需要最小兼容性补丁

### 现象

第一次运行 PACT SuperLU 示例时，主入口直接在 pandas 处报错：

```text
AttributeError: 'DataFrame' object has no attribute 'append'
```

修完这一处后，又在 floorplan 处理和 grid label 映射处继续失败：

```text
TypeError: Invalid value '../Example/config_files/default_htc_1e4_10mm.config' for dtype 'float64'
```

```text
TypeError: Choicelist and default value do not have a common dtype
```

### 根因

- PACT 源码是按旧 pandas / NumPy API 编写的。
- 当前环境里是 `pandas 3.0.2`、`numpy 2.4.4`。
- `DataFrame.append()` 已移除。
- 全空字符串列会被 pandas 推成 `float64`，后续再填路径字符串会失败。
- `np.select()` 默认值是数字 `0`，而 choice 是字符串 label，NumPy 2.x 不再自动宽松提升 dtype。

### 解决方法

仅做最小兼容性补丁，不改 PACT 主流程逻辑：

- [PACT.py](/home/lisihang/thermal_placement/third_party/PACT/src/PACT.py)
  - 将 `DataFrame.append()` 改为 `pd.concat()`
- [Layer.py](/home/lisihang/thermal_placement/third_party/PACT/src/Layer.py)
  - `ConfigFile` 列先转成 `object`，再 `fillna(defaultConfigFile)`
- [GridManager.py](/home/lisihang/thermal_placement/third_party/PACT/src/GridManager.py)
  - `np.select(..., default='')`

### 验证

应用补丁后：

- PACT SuperLU steady-state 示例可运行
- PACT serial Xyce / SPICE_steady 示例可运行
- 相关输出已生成在 [reports/pact_validation](/home/lisihang/thermal_placement/reports/pact_validation)

## 22. PACT SuperLU 与 serial Xyce 示例已跑通

### 现象

此前报告中仍有两项未闭环：

- PACT + SuperLU 实例验证
- PACT + Xyce SPICE 实例验证

### 解决方法

1. SuperLU 示例：

```bash
source tools/env_gemmini_thermal.sh
cd third_party/PACT/src
python PACT.py \
  ../Example/lcf_files/10mm_lcf_UniformPD_50Wcm2.csv \
  ../Example/config_files/default_htc_1e4_10mm.config \
  ../Example/modelParams_files/modelParams10mm.config_40x40 \
  --gridSteadyFile /home/lisihang/thermal_placement/reports/pact_validation/superlu_10mm.grid.steady
```

2. serial Xyce / SPICE_steady 示例：

为避免误触发 `mpirun`，新增串行配置
[modelParams20mm_spice_steady_serial_20x20.config](/home/lisihang/thermal_placement/reports/pact_validation/modelParams20mm_spice_steady_serial_20x20.config)，其中：

```ini
number_of_core = 1
name = SPICE_steady
rows = 20
cols = 20
```

执行：

```bash
source tools/env_gemmini_thermal.sh
cd third_party/PACT/src
python PACT.py \
  ../Example/lcf_files/20mm_lcf_UniformPD_50Wcm2.csv \
  ../Example/config_files/default_htc_1e4_20mm.config \
  /home/lisihang/thermal_placement/reports/pact_validation/modelParams20mm_spice_steady_serial_20x20.config \
  --gridSteadyFile /home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.grid.steady
```

### 验证

SuperLU 产物：

- [superlu_10mm.grid.steady.layer0](/home/lisihang/thermal_placement/reports/pact_validation/superlu_10mm.grid.steady.layer0)
- [superlu_10mm.grid.steady.layer1](/home/lisihang/thermal_placement/reports/pact_validation/superlu_10mm.grid.steady.layer1)

范围：

```text
superlu_layer0_min=368.540000
superlu_layer0_max=368.540000
superlu_layer1_min=368.150000
superlu_layer1_max=368.150000
```

serial Xyce 产物：

- [spice_20mm_serial.cir](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.cir)
- [spice_20mm_serial.log](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.log)
- [spice_20mm_serial.cir.csv](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.cir.csv)
- [spice_20mm_serial.cir.ic](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.cir.ic)
- [spice_20mm_serial.grid.steady.layer0](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.grid.steady.layer0)
- [spice_20mm_serial.grid.steady.layer1](/home/lisihang/thermal_placement/reports/pact_validation/spice_20mm_serial.grid.steady.layer1)

Xyce log 关键信息：

```text
This is version Xyce Release 7.4.0-opensource
Total Devices                          2721
Number of Unknowns = 802
```

范围：

```text
spice_layer0_min=367.250000
spice_layer0_max=375.780000
spice_layer1_min=366.880000
spice_layer1_max=375.330000
```

### 当前结论

- PACT 主入口可用
- PACT SuperLU steady-state 示例已跑通
- PACT serial Xyce / SPICE_steady 示例已跑通
- PACT parallel mode 仍暂缓，不在当前阶段继续补

## 23. Stage 1 `tiled_matmul_os` 全 VCD run 暴露的脚本与成本问题

### 现象

首次按 Stage 1 固定 baseline 运行：

```bash
RUN_TAG=stage1_tiled_matmul_os_baseline_20260423 \
TIMEOUT_CYCLES=100000000 \
scripts/run_gemmini_workload.sh tiled_matmul_os
```

发现以下问题：

- 旧 `run_gemmini_workload.sh` 按去掉 `-baremetal` 的 basename 查找 simulator 输出，和 Chipyard 实际输出 `tiled_matmul_os-baremetal.<RUN_TAG>.*` 不一致。
- `TIMEOUT_CYCLES` 没有显式传给 Chipyard `make`，第一次运行仍使用默认 `+max-cycles=10000000`，在 CPU reference matmul 阶段触发 TestDriver fatal。
- 官方 `tiled_matmul_os` bare-metal 路径保持 `MAT_DIM_I/K/J=64` 和 `CHECK_RESULT=1` 时，CPU gold 阶段明显长于历史 `small_gemm`。
- 完整 VCD 约 `41 GiB`，`extract_vcd_activity.py` 对该 VCD 的单 pass 解析接近一小时量级。

### 解决方法

- 更新 [run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh)：
  - 使用包含 `-baremetal` 的 basename 收集 `.log/.out/.vcd`。
  - 显式传递 `TIMEOUT_CYCLES` 给 Chipyard `make`。
  - 成功后生成 Stage 1 manifest、activity CSV、window report 和 activity summary。
  - 失败时只记录日志和 manifest，不复制 partial VCD。
- 新增 [analyze_vcd_windows.py](/home/lisihang/thermal_placement/scripts/analyze_vcd_windows.py)：
  - 复用 `extract_vcd_activity.py` 已生成的 region CSV 和 simulator log marker，避免再次扫描 41 GiB VCD。
- 新增 [report_stage1_activity.py](/home/lisihang/thermal_placement/scripts/report_stage1_activity.py)：
  - 汇总固定 baseline 的功能 marker、cycle marker、产物路径、region activity 和 top toggle signals。

### 验证

- `TIMEOUT_CYCLES=100000000` 时，`tiled_matmul_os` 完成：
  - `Starting slow CPU matmul`
  - CPU reference `Cycles taken: 2967084`
  - `Starting gemmini matmul`
  - Gemmini matmul `Cycles taken: 3779`
  - Verilator `$finish`
- 生成 active VCD：
  - `sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd`
- 生成 Stage 1 报告：
  - `reports/stage1_tiled_matmul_os_baseline_windows.md`
  - `reports/stage1_tiled_matmul_os_baseline_activity_summary.md`

## 24. Stage 1 activity 分类中短 token 与宽泛 hierarchy bucket 容易误分类 SoC 信号

### 现象

初版 activity summary 中，`pe_array` top toggle signals 出现大量非 Gemmini PE 信号，例如 SoC wrapper / monitor watchdog。根因有三部分：`extract_vcd_activity.py` 把短字符串 `pe` 当普通 substring，导致 `wrapper` 等路径被误判；`inspect_gemmini_hierarchy.py` 的 `pe_array` bucket 使用了过宽的 `tile`/`pe` 匹配，曾把 `RocketTile`、`PeripheryBus`、wrapper、cache array 等 SoC context 放入 `pe_array`；VCD header 中同一 code 存在多个 alias，旧 parser 用 `setdefault` 保留第一个 SoC alias，导致真实 `gemmini.mesh` scope 被丢弃；同时 clock/reset 过滤曾在整条 path 上匹配 `reset`，会把 `element_reset_domain_rockettile.gemmini...` 下的 Gemmini 内部信号全部排除。

### 解决方法

更新 [extract_vcd_activity.py](/home/lisihang/thermal_placement/scripts/extract_vcd_activity.py)：

- 增加 `term_matches()`。
- 对 `pe` 只匹配独立 component 或 `pe_` 前缀。
- 移除默认 `pe_array` 中过宽的 `gemmini`/`tile`，并将 scratchpad、accumulator、load/store、controller 放在 PE array 前优先匹配。
- 对重复 VCD code alias 增加 `alias_priority()`，优先保留 `gemmini`/`mesh`/execute/load/store/scratchpad/accumulator 等目标路径，避免 SoC alias 覆盖真实 Gemmini scope。
- clock/reset 过滤改为只检查叶子信号名，不再因为父级 `element_reset_domain_*` scope 排除整个 Gemmini 子树。
- Stage 1 运行脚本默认 `--top-signals 0`，保留完整信号 activity CSV，方便后续重分类和审查。

更新 [inspect_gemmini_hierarchy.py](/home/lisihang/thermal_placement/scripts/inspect_gemmini_hierarchy.py)：

- 收窄 `pe_array` bucket 到 `Mesh`、`MeshWithDelays`、`PE`、`PE_256`、`MacUnit`、`AccPipe`、`AccPipeShared`、`ScalePipe` 等核心计算 datapath。
- 将 `Tile`/`RocketTile`/`PeripheryBus`/wrapper/cache array 类模块归回 SoC context 或 TL glue。
- 重新生成 `configs/gemmini/hierarchy_map.yaml` 和 `reports/notes/gemmini_module_inventory.md`。
- 新增 [reclassify_vcd_activity.py](/home/lisihang/thermal_placement/scripts/reclassify_vcd_activity.py)，用于在完整 signal CSV 已存在时快速重分类，避免重新扫描大 VCD；若 CSV 曾被 top-N 截断，则仍必须重新扫描 VCD。

### 验证

- `python -m py_compile scripts/extract_vcd_activity.py scripts/analyze_vcd_windows.py scripts/report_stage1_activity.py` 通过。
- `bash -n scripts/run_gemmini_workload.sh` 通过。
- 新的 module inventory 中 `pe_array` 从 71 个模块收敛为 8 个核心计算相关模块。
- 已基于同一个 Stage 1 VCD 重新运行 activity extraction，以刷新分类结果。


## 25. Verilator 线程数切换需要重建 debug simulator；线程上限开放到 128，但默认值必须按实测选择

### 现象

在已有 `simulator-chipyard.harness-GemminiRocketConfig-debug` 的前提下，直接改：

```bash
make -C third_party/chipyard/sims/verilator -j "$MAKE_JOBS" \
  CONFIG=GemminiRocketConfig VERILATOR_THREADS=16 debug
```

`make` 会直接返回 `Nothing to be done for 'debug'`，不会因为线程参数变化自动重建 simulator。

### 根因

- `VERILATOR_THREADS` 和 `USE_FST` 影响的是 Verilator 生成 debug simulator 时的编译选项。
- 现有 Make 依赖关系不会把这些变量变化视为重建触发条件。
- 因此如果不先清理 `model_dir_debug` 和 `sim_debug`，后续运行仍然沿用旧线程数/旧 tracing 选项。

### 解决方法

- 切换 `VERILATOR_THREADS` 或 `USE_FST` 时，先执行：

```bash
make -C third_party/chipyard/sims/verilator CONFIG=GemminiRocketConfig clean-sim-debug
```

- 当前 [run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh) 已增加：
  - `VERILATOR_THREADS`
  - `NUMACTL`
  - `CLEAN_DEBUG_SIM`
- 推荐在切换线程数或 FST/VCD 模式时使用 `CLEAN_DEBUG_SIM=1`。

### 实测结果（官方 `mvin_mvout` bare-metal）

测试入口：

```bash
source tools/env_gemmini_thermal.sh
scripts/build_gemmini_workloads.sh mvin_mvout
```

说明：`mvin_mvout` 是 Gemmini 官方基础搬运/读写测试，不是后续 Stage 1-4 的 GEMM baseline；这里只把它作为 simulator/threading 辅助 smoke。

对比结果：

- 1 线程 VCD：
  - Verilator walltime `143.129 s`
  - 外层 `/usr/bin/time`：`elapsed=145.53`
  - 波形大小：`1.8G`
- 16 线程 VCD：
  - Verilator walltime `61.168 s`
  - 外层 `/usr/bin/time`：`elapsed=63.69`
  - 波形大小：`1.8G`
- 32 线程 VCD：
  - Verilator walltime `92.657 s`
  - 外层 `/usr/bin/time`：`elapsed=150.96`
  - 波形大小：`1.8G`
- 64 线程 VCD：
  - Verilator walltime `247.615 s`
  - 外层 `/usr/bin/time`：`elapsed=602.30`
  - 波形大小：`1.8G`
- 128 线程 VCD：
  - Verilator walltime `415.556 s`
  - 仍可完成，但比 `16/32/64` 更慢
  - 本轮只作为上限压力测试，不作为默认推荐配置
- 16 线程 FST：
  - Verilator walltime `80.039 s`
  - 外层 `/usr/bin/time`：`elapsed=81.28`
  - 波形大小：`32M`

### 当前结论

- 当前 active flow 默认并要求使用 VCD，不把 FST 作为后续开发主格式。
- 对这台机器和当前官方 smoke 来说，线程数不是越高越好；已完成 run 中 `VERILATOR_THREADS=16` 最优。
- `VERILATOR_THREADS=32` 已经比 16 慢，`64` 明显恶化，`128` 也继续恶化。
- 因此 Verilator 仿真线程上限虽然开放到最多 `128`，但后续开发默认线程数必须按当前机器、当前 workload、当前 tracing 形式的实测结果选择，不能直接写死为最大核心数。
- 当前 `analyze_vcd_windows.py` 已避免为窗口报告再次扫描超大 VCD；真正仍然昂贵的是第一次 `extract_vcd_activity.py` 全量解析。
- 这个 parser 现已在主仓库中完成并行化实现，方式是 header 预解析、body 分块和边界状态合并；默认仍是 `1` worker，但可通过 `--workers` 或 `VCD_PARSER_WORKERS` 提升到最多 `128`。
- 当前主仓库实现对 `sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t16.vcd`（约 `1.8G`）的实测结果为：`1 worker=210.65s`、`32 workers=10.77s`、`64 workers=7.28s`、`128 workers=6.34s`。
- `1/32/64/128` 的 signal CSV 与 region CSV 都已分别用 `cmp` 验证完全一致。
- 在这台机器和这个测试文件上，当前主仓库 parser 的已测最佳点是 `128`；但后续开发仍必须按实际文件和机器选择 worker 数，而不是把 `128` 写死成不变默认值。

## 26. `tiled_matmul_os` Stage 1 已有有效 VCD，但旧 summary/report 可能仍停留在修复前的 activity 输出

### 现象

- `sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd` 已存在，大小约 `40.83 GiB`。
- 功能日志已显示：
  - `Starting slow CPU matmul`
  - `Starting gemmini matmul`
  - `Cycles taken: 2967084`
  - `Cycles taken: 3779`
- 但旧版 `reports/stage1_tiled_matmul_os_baseline_activity_summary.md` 曾出现 `pe_array=0` 或 top signal 完全被全 SoC 背景淹没的情况，容易误判为 Stage 1 还没有有效 Gemmini 活动。

### 根因

- 早期 activity CSV 是在 classifier / alias / reset-filter 修复前生成的旧结果。
- 后续虽然 parser 已修好，但如果不对已有大 VCD 重新提取，summary 仍然引用旧 CSV，自然会保留错误结论。
- 对 `tiled_matmul_os` 这类 `40+ GiB` VCD，误以为必须重跑整次仿真，容易导致无谓重复成本。

### 解决方法

优先复用现有 Stage 1 VCD，只重跑 activity 提取和报告生成，而不是先重跑仿真：

```bash
source tools/env_gemmini_thermal.sh
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss_kb=%M' \
python scripts/extract_vcd_activity.py \
  --vcd sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd \
  --hierarchy-map configs/gemmini/hierarchy_map.yaml \
  --workload stage1_tiled_matmul_os_baseline_20260423 \
  --signal-csv sim/activity/stage1_tiled_matmul_os_baseline_20260423_signal_activity.csv \
  --region-csv sim/activity/stage1_tiled_matmul_os_baseline_20260423_region_activity.csv \
  --top-signals 0 \
  --workers 128
```

随后重建：

- `reports/stage1_tiled_matmul_os_baseline_windows.md`
- `reports/stage1_tiled_matmul_os_baseline_activity_summary.md`
- Stage 1 阶段报告

### 验证

- 本轮对现有 `tiled_matmul_os` VCD 的重新解析结果：`elapsed=0:49.53 cpu=10221% maxrss_kb=94208`。
- parser 输出：`parsed_signals=32687`、`time_steps=20606655`、`last_time_ps=10303285500`。
- 刷新后的 region CSV 显示 Gemmini 目标 bucket 已全部非零：
  - `pe_array=2390594`
  - `controller=37074715`
  - `load_store_dma=20424`
  - `scratchpad=104515396`
  - `gemmini_other=10543973`
- 因此当前 `tiled_matmul_os` Stage 1 的正确推进方式是：
  - 若只需刷新活动统计或阶段报告，直接复用已有 VCD 并使用 parser 多进程；
  - 不要把“更新 summary”误做成“重新跑一次完整 Verilator 大仿真”。

## 27. Stage 2 初版 ORFS 配置若直接把 600+ 个 RTL 文件展开到 `VERILOG_FILES`，会在 make/exec 边界触发 `Argument list too long`

### 现象

- Stage 2 初版 `config.mk` 直接用 `wildcard` 展开 `rtl_exports/generated-verilog/GemminiRocketConfig/gen-collateral/*.sv/*.v`。
- 在执行 `make print-*` 或 synth 入口时，ORFS 会把超长 `VERILOG_FILES` 作为导出变量与依赖集处理。
- 当前环境下很快触发：`/usr/bin/env: Argument list too long`。

### 根因

- ORFS 的 `YOSYS_DEPENDENCIES` 会直接包含 `$(VERILOG_FILES)`。
- Gemmini 导出 collateral 数量较大，直接把所有路径展开成环境变量和 make 依赖，超过了当前 shell/exec 边界的实用长度。

### 解决方法

- 不再用 `wildcard` 展开完整文件列表。
- 改为复用导出的 `chipyard.harness.TestHarness.GemminiRocketConfig.top.f`，在 Stage 2 本地生成过滤后的 filelist：
  - `physical/stage2_tiled_matmul_os_baseline_asap7/src/gemmini_stage2_sources_top.f`
- `VERILOG_FILES` 只保留本地 blackbox stub：
  - `physical/stage2_tiled_matmul_os_baseline_asap7/src/gemmini_stage2_memory_blackboxes.sv`
- filelist 通过：
  - `SYNTH_SLANG_ARGS = -f $(DESIGN_HOME)/src/gemmini_stage2_sources_top.f`

### 验证

- `make print-VERILOG_FILES print-SYNTH_SLANG_ARGS` 可正常输出。
- `synth_canonicalize.tcl` 已可在该入口下成功完成，顶层识别为 `Gemmini`。

## 28. ORFS make 允许的 `VERILOG_FILES` 不能直接写成 `-f <filelist>`

### 现象

- 尝试把 `VERILOG_FILES = -f <filelist>` 直接交给 ORFS。
- make 失败：`No rule to make target '-f'`。

### 根因

- ORFS 的 `YOSYS_DEPENDENCIES` 会把 `VERILOG_FILES` 当成普通文件依赖。
- `-f` 在 Yosys/slang 语义里是参数，但在 make 依赖里会被当成一个待构建目标。

### 解决方法

- 不在 `VERILOG_FILES` 中放命令行参数。
- `VERILOG_FILES` 只保留真实文件；filelist 参数放到 `SYNTH_SLANG_ARGS`。

### 验证

- 修改后 ORFS synth 能进入 Yosys，不再在 make 依赖阶段失败。

## 29. ORFS hierarchical keep-hierarchy 默认 `min_cost` 会对 blackbox memory 报 `Missing cost information`

### 现象

- Stage 2 为避免默认 flatten/memory 路径问题，切换到：
  - `SYNTH_HIERARCHICAL = 1`
- synth 在 `KEEP_HIERARCHY` 阶段失败：
  - `ERROR: Missing cost information on instanced blackbox mem_0_ext`

### 根因

- reduced ASAP7 平台 overlay 默认给出：`SYNTH_MINIMUM_KEEP_SIZE ?= 1000`
- ORFS 在 hierarchical 分支里会执行 `keep_hierarchy -min_cost`。
- 被刻意 blackbox 的 `mem_ext` / `mem_0_ext` / `mem_1_ext` 没有面积/成本信息，因此该路径报错。

### 解决方法

在 Stage 2 `config.mk` 中显式清空：

```make
export SYNTH_MINIMUM_KEEP_SIZE =
```

使 ORFS 走普通 `keep_hierarchy`，而不是 `-min_cost` 版本。

### 验证

- 修改后 synth 已能越过 `KEEP_HIERARCHY`，继续进入第二次 synth、`MEMORY_MAP` 和后续 techmap 阶段。

## 30. Stage 2 当前综合主阻塞已从入口问题收缩到 Yosys 后段 mapped-netlist 生成耗时过长

### 现象

- 当前 Stage 2 入口已确认：
  - top = `Gemmini`
  - techlib = `third_party/edahub/edahub/technology/asap7` reduced ASAP7
  - memory policy = `mem_ext` / `mem_0_ext` / `mem_1_ext` blackbox
- `synth_canonicalize.tcl` 可以稳定成功。
- `synth.tcl` 经过配置修正后，已能走到：
  - `MEMORY_COLLECT`
  - `KEEP_HIERARCHY`
  - 第二次 synth
  - `MEMORY_MAP`
  - `TECHMAP`
  - `EXTRACT_FA`
- 但在当前 run 中，长时间未产出 `1_2_yosys.v`，需要人工终止以避免无限等待。

### 根因

- 当前已经不是 ASAP7 路径、filelist、blackbox cost 或最初 flatten assert 的问题。
- 主阻塞已收缩到 Yosys/ORFS 默认后段映射流程本身，对当前 Gemmini 规模设计的耗时/稳定性还需继续收敛。

### 当前证据

- `mem.json` 已生成，大小约 `87,442,931` bytes。
- canonicalize 成功，顶层为 `Gemmini`。
- 当前尚未生成：
  - `results/.../1_2_yosys.v`
- 被人工终止的最近一次 run 统计：
  - `Elapsed time: 11:59.89`
  - `CPU time: user 740.67 sys 30.39`
  - `Peak memory: 5340140KB`

### 下一步建议

优先从以下最小方向继续收敛，而不是回退到全 SoC：

1. 为 Stage 2 单独复制一份最小 `synth.tcl`，跳过当前对 Gemmini 价值不高但耗时显著的后段步骤。
2. 评估是否显式清空 `ADDER_MAP_FILE`，避免 `EXTRACT_FA`/adder 映射成为当前第一阻塞。
3. 若仍不稳定，再进一步收缩 top/filelist 到 `Gemmini` 相关最小可综合子集，而不是重新回到完整 collateral wildcard。


## 31. 后端默认工具路径若不显式固定，容易出现 ORFS 与仓库本地安装的混用

### 现象

- `sta` 在当前环境中有两个可执行路径：
  - `tools/opensta/bin/sta`
  - `tools/openroad-prebuilt/root/usr/bin/sta`
- ORFS 默认还可能回落到自己的 `tools/install/...` 目录查找工具。
- 如果不显式传递可执行路径，容易让综合/后端结果依赖 PATH 顺序或 ORFS 默认值。

### 解决方法

- 环境脚本显式导出：
  - `OPENROAD_EXE`
  - `OPENSTA_EXE`
  - `YOSYS_EXE`
- Stage 2 wrapper 显式把这三个变量传给 ORFS。
- 当前默认规则：
  - `OpenROAD` 使用 `tools/openroad-prebuilt/root/usr/bin/openroad`
  - `OpenSTA` 使用 `tools/opensta/bin/sta`
  - `Yosys` 使用 `tools/oss-cad-suite/oss-cad-suite/bin/yosys`

## 32. 当前后端多线程接口结论：OpenROAD 明确可用，Yosys 综合未确认存在同等级有效接口

### 现象

- ORFS `variables.mk` 已明确把 `NUM_CORES` 传给：
  - `OPENROAD_ARGS = -no_init -threads $(NUM_CORES)`
- `nangate45/gcd` 小设计 `synth` smoke 在 `NUM_CORES=8` 时，OpenROAD 日志打印：
  - `[INFO ORD-0030] Using 8 thread(s).`
- 同一 smoke 中，Yosys 综合 CPU 利用率约为 `100%`，未看到当前 flow 下可控且有效的综合内部多线程证据。

### 当前结论

- OpenROAD 多线程接口已确认可用。
- 不能把 `NUM_CORES` 直接等同于“综合线程数”。
- 当前正式建议是：
  - `make -j "$MAKE_JOBS"`
  - `NUM_CORES="$NUM_CORES"` 供 OpenROAD 使用
  - 不对 Yosys 内部多线程做未经验证的承诺

## 33. ORFS 自带 `nangate45/gcd` floorplan smoke 在当前 OpenROAD 版本下暴露 Tcl 兼容性问题

### 现象

- 2026-04-24 为验证 P&R 多线程接口，尝试运行：
  - `make ... DESIGN_CONFIG=.../designs/nangate45/gcd/config.mk NUM_CORES=8 place`
- floorplan 阶段失败：
  - `repair_timing -sequence is not a known keyword or flag`

### 根因

- 当前仓库使用的 OpenROAD prebuilt 版本与当前 ORFS 某些 Tcl/repair_timing 参数之间存在兼容性偏差。
- 这不是线程接口问题，但会让 ORFS 自带示例 design 的完整 place smoke 不够顺畅。

### 当前处理

- 先把该问题记录为工具链兼容性问题，不把它误判为多线程失效。
- 当前多线程接口有效性的依据仍采用：
  - `OPENROAD_ARGS` 的显式 `-threads N`
  - OpenROAD 日志中的 `[INFO ORD-0030] Using N thread(s).`
- 后续若要把 ORFS 自带示例 design 作为正式回归 smoke，需要单独收敛这类 Tcl 兼容问题。

## 34. 综合线程探索本次测试没有观察到性能收益

### 现象

- 2026-04-24 在 `/tmp/orfs_mt_sandbox/flow` 中，用 `nangate45/aes` 对 `synth` 做隔离对比：
  - `NUM_CORES=1` 总耗时 `42.42s`
  - `NUM_CORES=8` 总耗时 `42.53s`
- 两次 run 中，Yosys 主综合阶段都约 `40.1s`，CPU 利用率约 `100%`。

### 结论

- 当前 ORFS + Yosys + `abc_new` 主链路在这次测试中没有表现出综合多线程性能收益。
- 目前不能把 `NUM_CORES` 解释为“综合线程数”。
- 这只代表本次样例和本次环境下没有观察到收益，不代表正式开发不应优先使用多线程；正式开发仍建议从 `16` 线程开始尝试，必要时逐步提高到 `128`。

## 35. OpenROAD placement 接受 `-threads` 参数，但本次样例未观察到提速

### 现象

- 同样在 `/tmp/orfs_mt_sandbox/flow` 中，对 `nangate45/aes` 的 `3_3_place_gp` 单独做对比：
  - `NUM_CORES=1`:
    - 日志打印 `[INFO ORD-0030] Using 1 thread(s).`
    - `global_placement` 用时 `66s`
  - `NUM_CORES=8`:
    - 日志打印 `[INFO ORD-0030] Using 8 thread(s).`
    - `global_placement` 用时 `70s`

### 结论

- 当前 OpenROAD 线程参数确实生效到命令入口层。
- 但在当前 OpenROAD prebuilt + ORFS + `nangate45/aes` 的 placement 实测中，这次测试里 `8` 线程没有比 `1` 线程更快。
- 因此 Phase 2 正式流程中，线程数必须按 stage 和设计单独验证。这里记录的只是本次测试没有性能收益；正式开发仍建议优先使用多线程，从 `16` 线程开始尝试，如果耗时特别长再逐步提高，最高 `128`。

## 36. 为了做不污染主仓库的线程探索，ORFS 临时副本需要若干兼容性补丁

### 现象

- 在 `/tmp/orfs_mt_sandbox/flow` 上继续跑 ORFS 样例时，当前 OpenROAD prebuilt 与 ORFS Tcl 存在多处接口不兼容。
- 已在临时副本中暴露/绕过的问题包括：
  - `repair_timing -sequence ...` 不支持
  - `report_layer_rc` 不支持
  - `report_metrics` 依赖的 `report_fmax_metric` 不支持
  - `all_pins_placed` 不支持
  - `global_placement -force_center_initial_place` 不支持
  - `replace_arith_modules` 不支持

### 处理范围

- 这些补丁只用于 `/tmp` 的临时线程探索，不回写主仓库 flow。
- 主仓库当前仍应把它们视为“OpenROAD prebuilt 与 ORFS Tcl 存在兼容性漂移”的证据，而不是正式 flow 已收敛。

## 37. ORFS 完整 flow、`NUM_CORES` 和外层并行是三种不同杠杆，不能混为一谈

### 现象

- 项目推进中容易把以下三件事混成同一个“多线程开关”：
  - `make ... synth floorplan place route` 或 `make ... all`
  - `NUM_CORES=<N>`
  - `make -j <N>` 或后台并发多个 job
- 这会导致错误预期，例如把 `NUM_CORES=32` 理解为“整个 ORFS 完整 flow 自动 32 线程加速”，或者把 `make -j32` 理解为“单个 baseline 主线一定显著提速”。

### 澄清

- `NUM_CORES` 只控制单次 `openroad -threads <N>` 的内部线程数。
- `make -j` 更适合多个独立 target / 多个独立配置 / hierarchical block 的外层并发。
- 单个常规 ORFS 主线是依赖链：`synth -> floorplan -> place -> cts -> route -> finish`，因此不能把它当成天然可大规模并行的流水线。
- 当前 Yosys 综合主链路也没有确认到与 `NUM_CORES` 对应的等效内部多线程收益。

### 当前工程建议

- 单个 baseline：优先分阶段运行，外层 make 使用 `MAKE_JOBS=1`；P&R 阶段从 `NUM_CORES=16` 起步，必要时提高到当前机器允许的 `128`。
- 如果运行仍然过慢，优先缩小 top scope、收紧 filelist、保持 hierarchical synthesis，而不是立即扩大参数 sweep。
- 多配置比较时，才做外层并行，并为每个 job 使用唯一 `FLOW_VARIANT`，同时控制总核数预算。

## 38. Stage 2 缩减 filelist 后，综合主阻塞已推进到 `EXTRACT_FA` 之后的长静默映射阶段

### 现象

- `gemmini_stage2_sources_top.f` 为 `575` 行时，Stage 2 入口虽然能跑，但后段综合收敛很差。
- 使用 `scripts/build_stage2_gemmini_filelist.py` 生成 `gemmini_stage2_sources_reduced.f` 后，filelist 收缩到 `135` 行。
- 独立 `yosys-slang` 前端检查可通过：`read_slang ...; hierarchy -check -top Gemmini`。
- `MAKE_JOBS=16 NUM_CORES=16 scripts/run_stage2_openroad.sh synth` 可稳定走到 `MEMORY_MAP`、`TECHMAP`、`EXTRACT_FA`。
- 但 `EXTRACT_FA` 之后日志超过 `13` 分钟无更新，且未生成 `1_2_yosys.v`，因此本次 run 被人工中止。

### 根因判断

- 当前主问题已经不是 Stage 2 输入边界错误，也不是 ASAP7 / ORFS 入口配置错误。
- 现阶段瓶颈更像是 Gemmini 规模下的 Yosys 后段映射成本，尤其是 adder / arithmetic 相关提取与映射步骤。
- reduced filelist 明显改善了前端和层次综合阶段，但还没有把 mapped-netlist 生成时间收敛到可接受范围。

### 解决方法（当时采用，线程默认已被第 40/41 条更新）

- 保留 `Gemmini` 作为 implementation top。
- 保留 `SYNTH_HIERARCHICAL = 1` 与 memory blackbox 边界。
- 将默认 Stage 2 filelist 切换到 `physical/stage2_tiled_matmul_os_baseline_asap7/src/gemmini_stage2_sources_reduced.f`。
- 当时将 synth smoke 起跑线程试为 `MAKE_JOBS=16 NUM_CORES=16`；当前单 baseline 外层 make 规则已改为 `MAKE_JOBS=1`，见第 40/41 条。
- 下一轮优先检查最小 `synth.tcl` 与 `EXTRACT_FA` / adder mapping 设置，而不是回退到更宽的 SoC 风格 filelist。

### 验证

- `python -m py_compile scripts/build_stage2_gemmini_filelist.py`
- `yosys -m "$YOSYS_SLANG_PLUGIN" -Q -p "read_slang ... -f gemmini_stage2_sources_reduced.f ...; hierarchy -check -top Gemmini"`
- `MAKE_JOBS=16 NUM_CORES=16 scripts/run_stage2_openroad.sh synth`（本次人工中止前已推进到 `EXTRACT_FA`）

## 39. `ADDER_MAP_FILE=` 的 one-off synth smoke 证明默认 Stage 2 主阻塞高度集中在 `EXTRACT_FA` / adder mapping 路径

### 现象

- 在默认 Stage 2 配置下，`synth` 稳定推进到 `EXTRACT_FA`，随后长时间静默。
- 使用单次实验命令 `FLOW_VARIANT=noaddermap ADDER_MAP_FILE= MAKE_JOBS=16 NUM_CORES=16 scripts/run_stage2_openroad.sh synth` 后，日志中不再出现 `EXTRACT_FA`。
- 同一轮实验继续推进到了 `DFFLIBMAP` 和 `ABC`，并开始按 module 粒度执行 ABC 映射。
- 该实验仍未完成到 `1_2_yosys.v`，但已经明显越过默认路径的原始阻塞点。

### 根因判断

- `EXTRACT_FA` / `techmap -map $::env(ADDER_MAP_FILE)` 很可能是当前 Gemmini 规模下的主要长耗时步骤之一。
- 这说明默认 Stage 2 的核心问题不是 filelist 前端失败，也不是 hierarchical 综合入口错误，而是 adder mapping 路径在该设计规模上的成本。
- 后续如果要继续收敛 Stage 2，应优先围绕 adder mapping 做最小可重复实验，而不是回退到更宽的 RTL 范围。

### 当前处理原则

- 不把 `ADDER_MAP_FILE=` 写回默认 formal config。
- 把它仅作为定位实验，用于证明瓶颈位置。
- 后续若要保留该分支，应通过独立 `FLOW_VARIANT` 或单独 wrapper / 最小 `synth.tcl` 管理，避免污染正式 Stage 2 默认入口。

### 验证

- 默认路径：`MAKE_JOBS=16 NUM_CORES=16 scripts/run_stage2_openroad.sh synth` -> 停在 `EXTRACT_FA` 之后长静默。
- 实验路径：`FLOW_VARIANT=noaddermap ADDER_MAP_FILE= MAKE_JOBS=16 NUM_CORES=16 scripts/run_stage2_openroad.sh synth` -> 推进到 `DFFLIBMAP` / `ABC`。


## 40. 单个 Stage 2 baseline 的 ORFS `synth` 默认使用 `MAKE_JOBS=1`，避免多输出规则触发重复综合

### 现象

- 在 `FLOW_VARIANT=noaddermap ADDER_MAP_FILE=` 路径下，曾使用：
  - `MAKE_JOBS=16 NUM_CORES=16 scripts/run_stage2_openroad_noaddermap.sh synth`
- 终端输出中出现两次相同的 `synth.sh ... 1_2_yosys.log` 调用。
- `1_2_yosys.log` 中的阶段输出成对交织，`ABC` 被重复执行。

### 根因

- ORFS Makefile 中：
  - `$(RESULTS_DIR)/1_2_yosys.v $(RESULTS_DIR)/1_2_yosys.sdc: $(RESULTS_DIR)/1_1_yosys_canonicalize.rtlil`
- 这两个输出由同一 recipe 生成。
- 对单个 baseline 使用 `make -j > 1` 时，GNU make 会对多输出目标触发重复 recipe，导致同一轮 synth 被并发执行两次。

### 解决方法

- 单个 Stage 2 baseline 的 synth / floorplan / place / route 默认使用：
  - `MAKE_JOBS=1`
- 仅将 `NUM_CORES=<N>` 用作单次 OpenROAD 的内部线程数。
- 只有在多个独立配置并行时，才允许把 `MAKE_JOBS` 或后台 job 数开大，并且每个 job 必须使用唯一 `FLOW_VARIANT`。

### 验证

- 改为 `MAKE_JOBS=1 NUM_CORES=16 scripts/run_stage2_openroad_noaddermap.sh synth` 后，综合只执行一次，并稳定生成：
  - `1_2_yosys.v`
  - `1_2_yosys.sdc`
  - `1_synth.odb`

## 41. Stage 2 的线程策略应拆成两层：单 baseline 外层默认 `MAKE_JOBS=1`，P&R 阶段优先提高 `NUM_CORES`，最高可尝试 `128`

### 现象

- Stage 2 中最容易混淆的是：
  - `MAKE_JOBS`
  - `NUM_CORES`
  - 后台并发多个独立 flow
- 实际开发中，单 baseline 继续增大 `MAKE_JOBS` 不会带来正确的整体加速，反而可能破坏单步可重复性。
- 布局布线侧的真正线程入口是 `openroad -threads <NUM_CORES>`。

### 当前经验

- synth 阶段：
  - `MAKE_JOBS=1`
  - `NUM_CORES` 不是主收益来源，当前主要瓶颈在 Yosys/ABC 而不是 OpenROAD。
- P&R 阶段：
  - 保持外层 `MAKE_JOBS=1`
  - `NUM_CORES` 可以按机器上限逐步提高，当前允许尝试到 `128`
  - 若只是单 baseline 依赖链，不通过提高 `MAKE_JOBS` 加速

### 当前建议

- 单 baseline synth：
  - `MAKE_JOBS=1 NUM_CORES=16`
- 单 baseline P&R：
  - `MAKE_JOBS=1 NUM_CORES=128`
- 多配置并行：
  - 每个 job 各自 `MAKE_JOBS=1`
  - 再通过 shell 后台并发多个 `FLOW_VARIANT=<tag>` 任务控制总核数预算

## 42. Stage 2 memory blackbox 仅有 Verilog stub 不够，进入 P&R 前还必须补 LEF macro stub

### 现象

- synth 已生成 `1_2_yosys.v` 和 `1_synth.odb` 后，OpenROAD 报：
  - `LEF master mem_ext not found`
  - `LEF master mem_0_ext not found`
- 这会阻断 floorplan / macro placement。

### 根因

- `mem_ext` / `mem_0_ext` / `mem_1_ext` 虽然在综合中被 blackbox 处理，但进入物理数据库时仍需要合法的 LEF master、macro 外形和 pin 几何。

### 解决方法

- 新增 LEF stub 生成脚本：
  - `physical/stage2_tiled_matmul_os_baseline_asap7/tools/generate_memory_stub_lef.py`
- 生成的 LEF：
  - `physical/stage2_tiled_matmul_os_baseline_asap7/lef/gemmini_stage2_memory_macros.lef`
- 在 Stage 2 `config.mk` 中加入：
  - `ADDITIONAL_LEFS = $(DESIGN_HOME)/lef/gemmini_stage2_memory_macros.lef`

### 验证

- 重新生成 `1_synth.odb` 后，`LEF master ... not found` 消失。
- 当前只剩：
  - `LEF master mem_ext/mem_0_ext has no liberty cell`
- 这对 blackbox memory 属于当前可接受状态。

## 43. 当前 OpenROAD prebuilt 与 ORFS Tcl 存在多处兼容性差异，必须在 flow 脚本层做最小 guard

### 现象

- `2_1_floorplan` 过程中连续暴露以下兼容性问题：
  - `repair_timing -sequence is not a known keyword or flag`
  - `invalid command name "report_layer_rc"`
  - `invalid command name "report_fmax_metric"`

### 根因

- 当前 OpenROAD 二进制版本是：
  - `v2.0-17598-ga008522d8`
- ORFS 自带 Tcl 假定了更新或不同接口集合。
- 因此需要对不存在的命令做条件调用，不能直接照搬上游脚本。

### 解决方法

- 修改 `third_party/OpenROAD-flow-scripts/flow/scripts/floorplan.tcl`：
  - 去掉硬编码 `-sequence "unbuffer,sizeup,swap,vt_swap"`
  - 对 `report_layer_rc` 加 `info commands` guard
- 修改 `third_party/OpenROAD-flow-scripts/flow/scripts/report_metrics.tcl`：
  - 对 `report_fmax_metric` 加 `info commands` guard

### 验证

- 修补后，`2_1_floorplan` 已能越过上述 Tcl 兼容点，成功写出：
  - `2_1_floorplan.odb`
  - `2_1_floorplan.sdc`

## 44. 当前 Gemmini 规模下，floorplan 阶段默认 setup repair 过重；开发阶段应跳过该步骤并优先保留物理产物

### 现象

- 默认 `2_1_floorplan` 在 `repair_timing -setup ... -repair_tns 100` 下持续数百轮迭代，长时间停留在 `spad/acc_scale_unit` 周边路径修复。
- 将 `TNS_END_PERCENT` 降到 `5` 后，仍然会进入很长的 setup repair。

### 根因

- 对当前约 `1.26M` 实例规模的 `Gemmini` top，floorplan 阶段的 setup repair 不是 Phase 2 的主要价值点，但会显著拖慢开发。
- Phase 2 当前目标是尽快拿到可继续用于 place/route 的 floorplan 产物，而不是在 floorplan 阶段做深度时序优化。

### 当前开发做法

- floorplan 开发阶段使用：
  - `REMOVE_ABC_BUFFERS=1`
  - `SKIP_REPORT_METRICS=1`
- 这样会：
  - 跳过最重的 floorplan setup repair
  - 直接保留必要的 floorplan 数据库和 SDC
  - 避免在当前 OpenROAD 版本下把时间耗在非关键报告路径上

### 当前结果

- 在上述开发模式下，已成功拿到：
  - `2_1_floorplan.odb`
  - `2_1_floorplan.sdc`
- 后续新的阻塞已推进到：
  - `2_2_floorplan_macro`
  - `rtl_macro_placer` 报 `Pin location error for auto_spad_id_out_a_bits_address[0]`

## 45. 当前 OpenROAD prebuilt 缺少 `all_pins_placed` 命令，`3_1_place_gp_skip_io` 需要在 ORFS Tcl 中加 guard

### 现象

- `MAKE_JOBS=1 NUM_CORES=128 SKIP_REPORT_METRICS=1 scripts/run_stage2_openroad_noaddermap.sh place` 首次进入 `3_1_place_gp_skip_io` 时，直接报：
  - `invalid command name "all_pins_placed"`

### 根因

- 当前 OpenROAD 预编译版本不提供 `all_pins_placed` 这一 Tcl 命令。
- ORFS 的 `global_place_skip_io.tcl` 默认假定该命令存在。

### 解决方法

- 修改 `third_party/OpenROAD-flow-scripts/flow/scripts/global_place_skip_io.tcl`：
  - 将 `elseif { [all_pins_placed] }` 改为
  - `elseif { [llength [info commands all_pins_placed]] > 0 && [all_pins_placed] }`
- 当命令不存在时，流程直接回落到：
  - `global_placement -skip_io ...`

### 验证

- 修补后，`3_1_place_gp_skip_io` 已成功完成。
- 当前实际结果：
  - `3_1_place_gp_skip_io.odb` 已生成
  - 运行统计约 `703 s`，峰值内存约 `4.49 GB`

## 46. 当前 OpenROAD prebuilt 不支持 `global_placement -force_center_initial_place`，`3_3_place_gp` 需要改为按能力启用

### 现象

- `3_3_place_gp` 首次运行时，在端口 buffer 插入后立即报：
  - `global_placement -force_center_initial_place is not a known keyword or flag`

### 根因

- ORFS 的 `global_place.tcl` 无条件加入：
  - `-force_center_initial_place`
- 当前 OpenROAD 版本：
  - `v2.0-17598-ga008522d8`
  不支持该参数。

### 解决方法

- 修改 `third_party/OpenROAD-flow-scripts/flow/scripts/global_place.tcl`：
  - 默认不再无条件追加 `-force_center_initial_place`
  - 仅在显式设置 `PLACE_FORCE_CENTER_INITIAL_PLACE=1` 时才启用
- 这样保持对更高版本 OpenROAD 的可选兼容，同时不阻断当前仓库主线。

### 当前经验

- `3_3_place_gp` 在修补后已成功越过启动错误，并进入 timing-driven/routability-driven 全局布局长跑。
- 该阶段日志会出现明显的长静默区间，尤其是在：
  - `Timing-driven iteration <n>/6`
  - `virtual: false`
  之后的内部优化阶段。
- 当前观察说明这类长静默不应立即判定为卡死；需要结合进程存活状态与 `*.tmp.log` 后续更新时间一起判断。

### 验证

- 修补后，`3_3_place_gp` 已推进到至少：
  - `Timing-driven iteration 5/6`
  - `overflow` 降到约 `0.190`
- 当前主线结论：`place` 的新阻塞已经从 Tcl 兼容错误转为正常的长耗时优化过程。


## 47. Stage 2 已推进到 CTS 后的 global-route pin access；当前不再卡在 synthesis/floorplan

### 与最近提交的对应关系

最近几次提交的状态演进与当前文档应保持一致：

- `88b667a phase 2 attempt, blocked in yosys`：默认路径主要卡在 Yosys 后段 / `EXTRACT_FA`。
- `cbe48c9 phase 2 attempt, broken in floorplan`：`noaddermap` 后生成 mapped netlist，继续推进到 floorplan / macro placement 问题。
- `3b1df56 phase 2 attempt, broken in route`：manual macro placement、place、CTS 均推进，route 首次卡在 memory macro pin access/offgrid/access 问题。
- `a0f7668 phase 2 another attempt, broken in 5_1`：继续围绕 `5_1_grt` 和 memory LEF pin geometry 调整，仍未得到 `5_route.odb`。


### 当前状态

截至 2026-04-25，`FLOW_VARIANT=noaddermap` 主线已经生成：

- `1_2_yosys.v`
- `1_synth.odb`
- `2_floorplan.odb`
- `3_place.odb`
- `4_cts.odb`

当前未生成：

- `5_route.odb`
- routed DEF / SPEF / SDF

当前阻塞点是 `5_1_grt` 的 `pin_access`：

- `DRT-0073 No access point for spad/spad_mems_0/mem/mem_ext/RW0_addr[0]`
- `DRT-0073 No access point for spad/spad_mems_1/mem/mem_ext/RW0_addr[0]`
- `DRT-0073 No access point for spad/acc_mems_0/mem/mem/mem_0_ext/R0_addr[0]`

### 结论

当前不是 synthesis 阻塞，也不是 floorplan 阻塞；route 之前的关键数据库已经能生成。Phase 2 仍未完成，因为 route 产物和后续 DEF/SPEF/SDF 尚未生成。

## 48. Stage 2 反复重跑综合/布局布线的根因是 LEF 变更会使已有 ODB 过期

### 现象

修改 `physical/stage2_tiled_matmul_os_baseline_asap7/lef/gemmini_stage2_memory_macros.lef` 后，再请求 `5_route.odb`，ORFS/make 会重新生成 `1_synth.odb`、floorplan、place、CTS 等前置 ODB。

### 根因

OpenROAD ODB 内部保存了 LEF macro master、pin 形状和相关物理几何。memory stub LEF 的任何变化都会使旧 ODB 中的 macro pin access 信息过期。直接复用旧 `4_cts.odb` 会继续使用旧 pin 几何，无法验证新 LEF。

### 当前规则

- 改 RTL/filelist/blackbox Verilog：通常需要重新综合。
- 改 LEF macro geometry：至少需要从 `1_synth.odb` 及之后重建物理数据库。
- 只改 route Tcl 或 route runtime knob：可以优先从 `4_cts.odb` 之后尝试。
- 单 baseline 始终 `make -j 1`，P&R 加速使用 `NUM_CORES`。

## 49. memory stub LEF pin-access 修复尝试记录

### `pin_access` 的含义

这里的 `pin_access` 不是 memory RTL 功能错误，而是 route 阶段在检查“每个 pin 是否有合法布线接入点”。标准单元 pin 来自标准单元 LEF；当前失败 pin 来自我们自己生成的 `mem_ext` / `mem_0_ext` blackbox macro LEF。综合阶段只需要 Verilog blackbox，P&R 阶段还需要 macro 的 SIZE、LAYER、RECT pin shape、track 对齐和可放置/可布线接入点。

因此 `DRT-0073 No access point` 的直接含义是：OpenROAD 看到了 memory macro 上的地址 pin，但在当前宏位置、pin shape、routing tracks、附近 obstruction/PDN/标准单元环境下，找不到可用的布线起点。它和 memory 相关，是因为本轮 Stage 2 把大 memory array blackbox 成 macro；不是因为要研究 memory 热模型，也不是 memory 行为仿真失败。

### 已尝试

1. 增加 memory macro LEF stub，解决 `LEF master ... not found`。
2. 将 pin rectangle 坐标 snap 到 `GRID=0.004`，解决 `DRT-0416 offgrid pin shape`。
3. 使用 `MARGIN=1.0` 避免第一个 pin 落在 macro corner；完整设计仍在 0.024um pin width 下失败于 `DRT-0073`。
4. 将 `PIN_THICKNESS` 从 `0.024` 改为 `0.096`，与 reduced ASAP7 M4/M5 min-width 约束一致。
5. 单独构造一个 `mem_ext` macro 的 OpenROAD `pin_access` smoke，0.096um LEF 下通过，报告 `macroNoAp=0`。
6. 2026-04-25 追加轻量 smoke：同一小设计中放置 `mem_ext`、`mem_0_ext`、`mem_1_ext` 三类 macro，`pin_access` 通过，`macroNoAp=0`。
7. 2026-04-25 追加 PDN-enabled 小设计 smoke：在同一三 macro 小设计中 source 当前 `pdn_stage2.tcl` 并运行 `pdngen` 后再 `pin_access`，仍通过，`macroNoAp=0`。

### 尚未验证

2026-04-25 最新 A 方案 full-design route 已完成到 `5_1_grt` 并自行退出。结果：0.096um memory pin width 在完整设计中通过 `pin_access`，报告 `macroNoAp=0`；原 `DRT-0073` memory macro access blocker 已解除。当前失败转为 `GRT-0116 Global routing finished with congestion`，未生成 `5_route.odb`。

## 50. 当前 Stage 2 妥协配置必须显式标注为 bring-up/proxy 设置

当前主线命令使用以下妥协项：

- `FLOW_VARIANT=noaddermap`
- `REMOVE_ABC_BUFFERS=1`
- `SKIP_REPORT_METRICS=1`
- `GPL_TIMING_DRIVEN=0`
- `MAX_PLACE_STEP_COEF=1.05`
- `SKIP_CTS_REPAIR_TIMING=1`
- `NUM_CORES=128`
- `MAKE_JOBS=1`

其中 `MAKE_JOBS=1` 是单 baseline 的确定性外层 make 设置，用于避免本地 ORFS 多输出规则触发重复综合；它不是内部并行加速旋钮。`NUM_CORES=128` 是 OpenROAD 内部并行；其余项属于 Stage 2 bring-up 加速/避坑设置。它们可以用于跑通热仿真原型，但不能被描述为 signoff-quality P&R 设置。

## 51. 200 MHz timing 目标对当前 blocker 的预期影响

将 `constraint.sdc` 从 `2.000 ns` 放宽到 `5.000 ns` 可能降低 synthesis/resize/CTS 的 timing repair 压力，但不会直接解决当前 `GRT-0116` global-route congestion，因为当前 blocker 是局部 routing capacity/overflow；memory `pin_access` 已通过。

若后续 blocker 变成 timing repair、buffer explosion 或 CTS repair，200 MHz 可能节省时间。若 blocker 是当前局部 routing congestion，改时钟周期只能通过间接改变 sizing/buffering 帮助，不能作为第一修复。

## 52. Stage 2 DRC / 精度策略

严格 Stage 2 完成仍要求 gate netlist、DEF、SPEF、SDF、实例坐标、面积统计和 timing 报告。

对 Stage 3/4 热仿真而言，少量非阻塞 DRC 不一定致命，前提是：

- 工具仍能写出可读 DEF/SPEF/SDF；
- 实例坐标可用于 grid 映射；
- 功耗估计路径可复现；
- 报告中明确标注 DRC 和非 signoff 限制。

如果 route 因 `pin_access` 或 `global_route` congestion 直接失败并且无法写出 route 产物，则不是“少量 DRC 可忽略”的问题，而是正常 Stage 2 路径未完成。当前 A 方案属于此类：已写出 `5_1_grt-failed.odb`，但未写出 `5_route.odb`、routed DEF/SPEF/SDF。若要用 place/CTS 或 failed-GRT 坐标进入 Stage 3，只能显式标注为 downgraded proxy / thermal-flow prototype。

## 53. 候选后备：memory array 不作为 routed hard macro target

### 状态

截至 2026-04-25，该方向只是可选后备方案，尚未执行，不能描述为已验证修复。当前已验证状态是：`noaddermap` 主线达到 CTS 和 `5_1_grt`；0.096um generated memory macro LEF 已在 full design 中通过 `pin_access`，但 `global_route` 因 `GRT-0116` congestion 失败并写出 `5_1_grt-failed.odb`。

### 方案定义

该方向不改变当前 Stage 2 的研究主轴：implementation top 仍优先保持 `Gemmini`，研究重点仍是 PE array、execute/control、load/store 近邻数据通路和 memory 周边标准单元。

变化点是：不再把 scratchpad / accumulator memory array 作为需要 route 接入的 hard macro。也就是说，不继续把 `mem_ext` / `mem_0_ext` / `mem_1_ext` 表达为“blackbox Verilog + fake hard macro LEF pins”的 route 目标，而是改成可综合的 memory-boundary stub / wrapper boundary，并在当前计划中配套 obstruction/thermal context 来保留粗略物理与热上下文。

### 预期实现方式

- 使用新的独立 variant（建议命名 `mem_boundary_stub_context`），避免覆盖当前 `noaddermap` 结果。
- 为 `mem_ext` / `mem_0_ext` / `mem_1_ext` 提供可综合边界 stub，或在 Stage 2 wrapper 中替换这些实例。
- stub 需要消费 address/write/control/wdata/wmask/clock 等输入，避免上游 memory-near 逻辑被优化掉。
- stub 需要产生非平凡 read data/state，避免下游 datapath 被常量传播吞掉。
- 必要时使用 `keep` / `dont_touch`，但只保护边界和关键近邻逻辑，不扩大为 RTL 优化任务。
- 该 variant 中应移除或绕过带信号 pin 的 `gemmini_stage2_memory_macros.lef`，因为 memory array 本体已经不是 route 目标。
- 同时保留 memory footprint 的 coarse obstruction / placement blockage / thermal-context region，避免标准单元填入原 memory 区域，并让 Stage 3/4 能解释 scratchpad/accumulator 的粗略物理热上下文。
- 综合后必须检查 hierarchy、instance count、PE/control/load-store 相关实例和 Stage 1 activity 名称映射，确认研究对象仍存在。

### 与“更小 Stage 2 wrapper”方案的区别

Fallback C 比更小 wrapper 更保守：尽量保留 `Gemmini` 顶层和原有上下文，只把 memory array route boundary 抽象掉。它减少的是 fake memory macro pin-access 风险，而不是重定义整个 Stage 2 研究对象。

更小 wrapper 方案会主动切掉更多 scratchpad/accumulator interface 和上层控制上下文，只保留 PE array、execute/control、load/store 近邻 datapath 的子集。它可能更容易跑通后端，但 Stage 1 activity 对齐、功耗解释和“是否仍代表 Gemmini sustained GEMM 热热点”的论证成本更高。

### 后续影响

Fallback C 如果跑通，Stage 3/4 可以继续分析 PE/control/load-store nearby standard-cell 热分布，但必须明确：SRAM array body 的面积、引脚、内部功耗和热扩散不是 routed macro 级结果，而是 memory-boundary/proxy 假设。

它仍可作为后续可选路线，但当前不得自动开始。是否进入该路线需要用户再次确认；在此之前应优先分析 A 方案的 global-route congestion 失败和可接受的参数/布局修正空间。


## 54. Stage 1 activity window precision and Stage 3 refinement rule

### 现象

当前 Stage 1 的 `steady_high_load` 是基于 simulator marker 和全 trace 聚合的粗窗口。完整 trace 来自 `GemminiRocketConfig` SoC/TestHarness，CPU golden reference 阶段远长于 Gemmini accelerator 阶段；因此 whole-program toggle 或全窗口平均不能直接作为 Stage 3 grid power 的输入。

### 规则

- Stage 1 仍可以使用完整 SoC 仿真作为真实 RoCC/DMA/memory 上下文来源。
- 不建议直接切到 `Gemmini`-only RTL 仿真，除非先建立并验证独立 harness，能够等价驱动 RoCC command、DMA/TL、TLB、memory backpressure 和 fence/busy 行为。
- Stage 3 前必须对 Gemmini 目标层次重新精化活动窗口，至少用 `gemmini.ex_controller`、`mesh`、load/store controller、valid/ready/busy/toggle 密度确认 accelerator-active 子窗口。
- 如果暂时只能用粗窗口，Stage 3 输出必须标注为 proxy，不得称为精确门级功耗波形。

## 55. RTL-to-gate/physical activity mapping rule

### 问题

Stage 1 activity 来自 RTL VCD；Stage 2 输出是 Yosys/OpenROAD gate netlist 和 physical DEF/ODB。Yosys 会优化、重命名、保留部分 hierarchy、blackbox/stub memory 边界，因此不能假设 RTL signal 名能逐一映射到 gate instance。

### 处理规则

- Stage 3 首先生成 activity mapping manifest，记录 RTL scope prefix、Stage 2 gate instance/module prefix、blackbox/stub 边界、可匹配比例和 fallback 比例。
- 优先做层次/模块级映射：例如 `Gemmini.ex_controller.*`、`Gemmini.ex_controller.mesh.*`、`Gemmini.load_controller.*`、`Gemmini.store_controller.*`、`Gemmini.spad.*`。
- 对无法单 gate 匹配的 RTL toggle，聚合到最近可解释模块或 grid region，再按该 region 的标准单元面积、cell count 或可匹配实例权重分配。
- 若 OpenSTA/SAIF 直接功耗链路失败，允许用 toggle-to-liberty proxy，但必须在 Stage 3 method report 中写明非 signoff 和 fallback 比例。


## 56. Stage 2 strict/proxy fidelity acceptance rule

### 背景

当前 Stage 2 为了越过工具兼容、adder mapping 和 route bring-up 阻塞，使用了 `noaddermap`、`REMOVE_ABC_BUFFERS=1`、`SKIP_REPORT_METRICS=1`、`GPL_TIMING_DRIVEN=0`、`SKIP_CTS_REPAIR_TIMING=1` 等设置。这些设置可以帮助形成热流程原型，但不能自动视为严格物理实现质量。

### 规则

- route blocker 清除并生成 routed 输出后，先把结果标为 `strict` candidate 或 `proxy`。
- 若要 strict Stage 2 closure，按最小增量恢复 fidelity：reports/metrics -> CTS timing repair -> timing-driven placement -> default/validated adder mapping。
- 每次恢复只改变一个主要 knob，并比较 route 完成情况、实例数、面积、目标模块层次、坐标分布和 timing report。
- 若恢复失败但 thermal prototype 需要继续，可经用户确认以 `proxy` 输入 Stage 3；报告必须写明 proxy 限制，不能用于严格物理质量或未来优化反馈结论。

## 57. Full-SoC Stage 1 source with target-scoped window refinement

### 规则

Stage 1 活动来源继续使用完整 `GemminiRocketConfig` full-SoC 仿真，以保留 CPU/RoCC/TL/DMA/memory/TLB/fence 上下文。后续不得用未验证的 Gemmini-only DUT run 代替该 baseline。

在 Stage 3 前，若 `steady_high_load` 仍是 coarse marker window，必须补一个 target-scoped refinement：只在 candidate tail interval 中扫描 Gemmini 目标 scope，输出 target window report 和 target-window activity CSV，再用该窗口构建 power grid。

## 58. Stage 3 optimization-readiness metadata without doing optimization

### 规则

本轮仍不做热优化，但 Stage 3/4 必须保存足够反查数据，以免热图只能展示、不能解释。需要保留 instance-to-grid、RTL scope 到 gate/region、region power summary、hotspot grid 到 instance/module traceback、mapping fallback ratio。该数据只用于解释和未来扩展，不触发 placement/floorplan/RTL 修改。

## 59. 2026-04-25 Stage 2 memory route order and documentation-first constraint

用户已确认当前 Phase 2 内存路线：

1. 已尝试 `PIN_THICKNESS=0.096` generated memory macro LEF 的 full-design route。
2. full-design `pin_access` 已通过；当前失败是 `GRT-0116` global-route congestion，不是原 memory `DRT-0073`。
3. `memory_boundary_stub + obstruction/thermal context` 现在记录为 optional fallback，尚未开始；暂时不自动进入 C 方案。
4. 当前不尝试纯 `mem_boundary_stub`（没有 obstruction/thermal context）的方案，除非用户再次明确更改计划。

执行约束：每次尝试失败或计划更新时，必须先更新相关 active 文档，记录尝试情况、失败证据、当前判定和下一步计划，再开始下一次尝试。该规则适用于 Stage 2 route 迭代，也适用于后续多次尝试的阶段任务。

## 60. 2026-04-25 Stage 2 0.096um full-route A result

### Attempt

A route attempt used the `PIN_THICKNESS=0.096` generated memory macro LEF and the existing `FLOW_VARIANT=noaddermap` Stage 2 command to rebuild stale downstream ODBs and target `5_route.odb`. The route was allowed to run to natural completion after the conversation was interrupted; no agent-side route termination is part of the recorded result.

Observed result:

- stale floorplan/place/CTS ODBs were regenerated from the updated 0.096um memory LEF path;
- `pin_access` completed without the previous memory macro `DRT-0073` blocker;
- reported `macroNoAp=0`, so the generated memory LEF is accessible in full-design context;
- `global_route` ran for 1:44:08 elapsed and then failed with `GRT-0116 Global routing finished with congestion`;
- final global-route summary reported total overflow 1261 and routed nets 1,327,547;
- final `congestion.rpt` retained 4 local overflow regions, mostly left-boundary `io_ptw_*` / `io_resp_bits_data*` nets near y=1715-1725um;
- `3_2_place_iop.tcl` places the implicated `io_ptw_*` / `io_resp_bits_data*` pins on the left die boundary (`x=0`) on M4 near the same y range;
- OpenROAD wrote `5_1_grt-failed.odb`; no `5_route.odb`, final routed DEF, SPEF, SDF, or detailed-route result was generated.

### Current judgment

The 0.096um memory macro LEF fix is stage-valid for pin access: the original memory macro `DRT-0073` blocker is no longer active. Stage 2 is still not complete because global route fails on residual congestion before detailed route. This is a stage-progress result, not strict Stage 2 success.

### Next plan

Do not enter C automatically. `memory_boundary_stub + obstruction/thermal context` remains optional and not started. Next work should first analyze the A-route congestion source and decide whether a small A-side adjustment is preferable. Because the residual overflow aligns with left-boundary IO pins, prioritize IO pin placement/boundary spreading and route-capacity/congestion settings before considering larger memory-strategy changes. Pure `mem_boundary_stub` remains out of scope unless the user explicitly changes the plan.

### Route monitoring rule

Route-stage OpenROAD runs may be silent for long periods. After progress is confirmed, use relaxed monitoring intervals and never proactively kill or interrupt route; only the user may request an active route termination, or the process may end/fail on its own.

## 61. 2026-04-25 Stage 2 route repair budget and proxy-fidelity policy

### User decision

The current `GRT-0116` A-route congestion may receive a few small repair attempts, but this work must remain scoped. Do not enter C automatically. Do not restore strict fidelity settings in that historical round unless the user changed the plan.

### Current proxy settings to keep documented

The then-active ORFS bring-up route still used non-signoff/proxy settings:

- `FLOW_VARIANT=noaddermap`
- `REMOVE_ABC_BUFFERS=1`
- `SKIP_REPORT_METRICS=1`
- `GPL_TIMING_DRIVEN=0`
- `MAX_PLACE_STEP_COEF=1.05`
- `SKIP_CTS_REPAIR_TIMING=1`
- `NUM_CORES=128`
- `MAKE_JOBS=1`

These are acceptable for clearing the route blocker and building a Stage 0-4 thermal-flow prototype, but any output produced with them must be labeled non-signoff / proxy. It cannot be used as strict P&R evidence.

### Fidelity policy

High-fidelity recovery is optional future work for the current project phase. The priority is to run the complete thermal flow first. If strict Stage 2 is later required, restore fidelity one knob at a time in this order: reports/metrics, CTS timing repair, timing-driven placement, default or otherwise validated adder mapping. Each recovery step must compare route completion, instance count, area, hierarchy preservation, coordinate distribution, and timing reports.

### Route repair plan

Attempt at most three small A-side fixes before reassessing. Current preferred sequence:

1. IO pin spreading / left-boundary congestion relief for the `io_ptw_*` and `io_resp_bits_data*` region.
2. Route capacity or global-route adjustment if IO spreading is insufficient.
3. Placement density or congestion knob adjustment if local overflow persists.

After each failed attempt or route-plan change, update this issue log and the Stage 2 summary before starting the next attempt.

### Attempt 1 planned before execution

Attempt 1 is an IO-placement-only A-side fix. It keeps the current bring-up/proxy knobs and does not enter C or restore strict fidelity. Planned change: rerun place/CTS/route with `PLACE_PINS_ARGS='-min_distance 0.54'` so `place_pins` spreads IO pins more aggressively than the default 2-track spacing. Because this variable affects `3_2_place_iop`, downstream place/CTS/route artifacts must be regenerated rather than reusing old `4_cts.odb`.

Expected evidence to compare after the run:

- `3_2_place_iop.log` should show the new `place_pins ... -min_distance 0.54` command.
- `5_1_grt.log` should either proceed beyond the previous `GRT-0116` or report a new/fewer congestion profile.
- Final outputs remain proxy/non-signoff if route succeeds, because the current bring-up knobs remain active.

### 2026-04-26 update: Attempt 1 reached detail route, then was externally interrupted

Attempt 1 is now partially successful relative to the previous `GRT-0116` blocker. With `PLACE_PINS_ARGS='-min_distance 0.54'`, the run regenerated placement/CTS/route state, passed full-design memory `pin_access` (`macroNoAp=0`), completed global route with zero final congestion overflow, and wrote `5_1_grt.odb` plus `route.guide`.

The active incomplete point is `5_2_route detail_route`. The process was externally killed/interrupted around the 4th optimization iteration at about 70%; the log shows violations decreasing from 49276 after iteration 3 to about 29949 at iteration 4/70%. This is not recorded as an OpenROAD fatal failure. No `5_2_route.odb`, `5_route.odb`, routed DEF, SPEF, or SDF was produced.

Next plan before any other Stage 2 route change: resume from existing `5_1_grt.odb` into `5_2_route` by targeting final `5_route.odb`, keeping current proxy knobs and adding `DETAILED_ROUTE_END_ITERATION=8`. If ORFS cannot start from `5_1_grt.odb`, stop and report the failure evidence and solution options. During the rerun, monitor normally until detailed-route iteration 1 completes, then reduce checks to about once per hour.

### 2026-04-26 route completion result

The resumed route run started from the existing `5_1_grt.odb`, entered `5_2_route` directly, and used `DETAILED_ROUTE_END_ITERATION=8` as planned. ORFS did not rerun synthesis, floorplan, placement, CTS, or `5_1_grt`.

Result:

- `5_2_route detail_route` completed all 8 optimization iterations and wrote `5_2_route.odb`.
- `5_3_fillcell` completed and wrote `5_3_fillcell.odb`.
- ORFS copied `5_3_fillcell.odb` to `5_route.odb`.
- Antenna check reported 0 net violations and 0 pin violations.
- Design area after detailed route: 3,115,146 um^2, 28% utilization; after filler: 3,442,900 um^2, 31% utilization.
- Final detailed-route violation count after the capped 8th iteration: 6,988. Dominant residual categories are M8/M9 min-step/min-width, M1 metal spacing/eolKeepOut, and M8 shorts.

This is a routed proxy result, not a DRC-clean or signoff result. It is suitable for continuing Phase 2 proxy export and Stage 3 thermal-flow prototyping only if the final export files are generated and the DRC caveat is kept in downstream reports.

This finish/export plan was executed later: final proxy outputs were generated, no SDF was emitted, and the SDF gap is now a documented Stage 3 caveat.

### 2026-04-26 finish/export attempt: core outputs generated, GUI image save failed

`make ... finish` continued from `5_route.odb`, completed `6_1_fill`, and entered `6_report final_report`. It wrote the key final Stage 2 proxy outputs: `6_final.odb`, `6_final.def`, `6_final.v`, and `6_final.spef`. It also produced `6_report.log`, `6_report.json`, and final image files up to `final_clocks.webp.png`.

The command exited with code 2 only at the final GUI image-save step:

- `[ERROR GUI-0070] Error: save_images.tcl, 77 invalid command name "get_scenes"`
- `Error: final_report.tcl, 72 GUI-0070`

Current judgment: this is a tool/script compatibility issue between this OpenROAD GUI build and ORFS `save_images.tcl`, not a route, DEF, Verilog, or SPEF export failure. Do not modify ignored ORFS scripts yet.

Caveats to keep with this proxy result:

- No SDF was produced by the current finish path.
- `mem_ext`, `mem_0_ext`, `mem_1_ext`, and several `ICG*` masters have no Liberty cell in the final report.
- VDD/VSS static IR numbers are non-physical and are not signoff evidence.

This intermediate plan was completed by the later no-clean `make ... finish` rerun recorded below.

### 2026-04-26 finish/export final result: Phase 2 proxy accepted

A second `make ... finish` was run without cleaning after the GUI image-save failure. Make did not re-enter `6_report`; it generated `6_final.sdc`, ran KLayout merge, wrote `6_1_merged.gds`, copied it to `6_final.gds`, and exited successfully.

Final Stage 2 proxy outputs now exist and are non-empty:

- `6_final.odb`
- `6_final.def`
- `6_final.v`
- `6_final.sdc`
- `6_final.spef`
- `6_final.gds`
- `6_report.log` / `6_report.json`
- `5_route_drc.rpt` and `drt_antennas.log`

Acceptance level: `proxy / non-signoff`. This is sufficient to start Stage 3 preflight, not sufficient for strict P&R, DRC-clean, timing-closed, or PDN-signoff claims.

Required downstream caveats: 6,988 residual detailed-route violations, no SDF output, active bring-up knobs, memory blackbox/proxy treatment, non-physical VDD/VSS static IR values, and KLayout `GDS_ALLOW_EMPTY=.*` behavior.


## 62. 2026-04-26 Phase 2 closeout: proxy acceptance, GUI image issue, and Phase 3 caveats

### Objective closeout result

Current Phase 2 is accepted only as `proxy / non-signoff`. The current run produced non-empty final outputs: `6_final.odb`, `6_final.def`, `6_final.v`, `6_final.sdc`, `6_final.spef`, and `6_final.gds`. These outputs are sufficient for Stage 3 preflight and thermal-flow prototyping.

This result is not strict P&R closure. It is not DRC-clean, timing-closed, PDN-signoff, or SRAM detailed thermal modeling.

### Remaining acceptance caveats

- Detail route completed only up to the capped `DETAILED_ROUTE_END_ITERATION=8` and ended with 6,988 residual violations.
- No SDF file was emitted.
- Bring-up/proxy knobs remain active: `noaddermap`, `REMOVE_ABC_BUFFERS=1`, `SKIP_REPORT_METRICS=1`, `GPL_TIMING_DRIVEN=0`, `SKIP_CTS_REPAIR_TIMING=1`, `MAX_PLACE_STEP_COEF=1.05`, and `PLACE_PINS_ARGS='-min_distance 0.54'`.
- `mem_ext`, `mem_0_ext`, `mem_1_ext`, and several `ICG*` masters have no Liberty cell in `6_report.log`.
- VDD/VSS static IR values are non-physical and must not be used as PDN evidence, power input, or thermal input.
- KLayout merge uses `GDS_ALLOW_EMPTY=.*`; this is acceptable as a proxy export but not a strict GDS/mask signoff claim.

### GUI image issue and solution options

Existing final images were generated through `final_clocks.webp.png`. The first `6_report` attempt then failed at `save_images.tcl` line 77 because the current OpenROAD GUI Tcl does not provide `get_scenes`.

Default handling: do not chase GUI screenshots. If final reporting must be rerun, prefer a non-GUI OpenROAD final-report path so `final_report.tcl` skips `gui::show save_images.tcl`; this avoids touching ignored ORFS scripts and keeps the accepted artifacts focused on DEF/netlist/SDC/SPEF/GDS/ODB.

Other options, only if GUI screenshots later become explicitly required:

1. Use a newer or compatible OpenROAD GUI build that supports `get_scenes` and the clock-tree image Tcl commands.
2. Add a documented local compatibility patch to ORFS `save_images.tcl`, guarding the clock-tree scene loop with `info commands get_scenes` and skipping only unsupported image types. Because ORFS is under ignored `third_party/`, this should be handled as an explicit environment compatibility repair before use.

The GUI issue does not block Stage 3 because Stage 3 does not consume screenshots.

### Reference suggestions for Stage 3

These are recommendations, not requirements:

- Start with a Stage 3 input manifest that records `6_final.def`, `6_final.v`, `6_final.sdc`, `6_final.spef`, and the no-SDF caveat.
- Build an activity mapping manifest before power-grid generation; record RTL prefix, gate prefix, blackbox/stub boundaries, matched ratio, fallback ratio, and region assignment.
- Do not use VDD/VSS IR report values in power or thermal inputs.
- Use activity + Liberty + SPEF + DEF as the proxy power basis, then aggregate by grid.
- Keep memory array body power as proxy/out-of-scope context; focus heat interpretation on PE/control/load-store nearby standard cells.
- Preserve instance-to-grid and RTL-to-region mappings for future hotspot explanation and possible later optimization work, but do not trigger optimization in Stage 3.

## 63. Stage 3 startup documentation, ORFS report path split, and backend resource policy clarified

Date: 2026-04-26

Scope:

- Stage 3 preparation before grid-level power waveform generation.
- Stage 2 proxy handoff documentation.
- Agent execution and retry rules for all Stage 0-4 work.

Findings:

- `6_report.log` and `6_report.json` are generated under the ORFS `logs/.../noaddermap/` tree, while route/report artifacts such as `5_route_drc.rpt` remain under the ORFS `reports/.../noaddermap/` tree.
- This ORFS output-class split is expected and should not be normalized by moving files.
- `MAKE_JOBS` in the ORFS/backend context is an outer independent-task count. It is not the OpenROAD internal thread count for one dependent flow. Existing environment defaults may still expose a larger generic build value, so ORFS/backend commands must override it explicitly.
- The current single-task backend cap is `NUM_CORES<=128`. If `MAKE_JOBS=2`, each task may use at most `NUM_CORES=128`. If `MAKE_JOBS=3` or `MAKE_JOBS=4`, each task may use at most `NUM_CORES=64`. Do not use `MAKE_JOBS>4` for this project.
- The documentation-first retry rule now applies to every Stage 0-4 failed attempt, planned method change, script route change, or retry, not only Stage 2 route iterations.

Resolution:

- Added `reports/stage3_tiled_matmul_os_baseline_preflight_plan.md` as the Phase 3 startup plan.
- Updated active plan, command reference, environment setup, task checklist, onboarding, report indexes, and Stage 2 reports to use the corrected path/resource wording.
- No Stage 3 scripts, heavy parsers, or experiments were started during this documentation-preparation task.

## 64. Stage 3 target-window extraction must exclude simulation monitor/watchdog signals

Date: 2026-04-26

Scope:

- Stage 3 target-scoped VCD activity refinement.

Finding:

- The first target-window extraction completed, but the top toggle signals were dominated by `monitor.watchdog` paths under Gemmini scratchpad-related scopes.
- These monitor/watchdog signals are simulator/debug monitoring context, not PE-array/control/nearby-datapath thermal target activity.

Resolution before retry:

- Update `scripts/extract_stage3_target_window_activity.py` to exclude signal paths containing `monitor` or `watchdog` from Stage 3 target activity.
- Regenerate the target activity CSV, bin CSV, and target-window report before building the power grid.

## 65. Stage 3 transient grid scaling uses max-bin normalization

Date: 2026-04-26

Scope:

- Stage 3 grid-power transient trace generation.

Finding:

- The first grid build used non-zero-bin mean normalization for bin scaling.
- The candidate steady window contains many low background bins and one true target-active bin, so mean normalization inflated the peak bin to about 50x the requested proxy total power.

Resolution before retry:

- Update `scripts/build_stage3_power_grid.py` to normalize transient bin scaling by the maximum target-activity bin.
- Regenerate grid power, transient ptrace, region summary, metadata, and reports so `proxy_total_power_w` corresponds to the selected peak/refined target-active bin.

## 66. Stage 3 OpenSTA sanity uses supported local commands only

Date: 2026-04-26

Scope:

- Stage 3 OpenSTA lightweight sanity check.

Finding:

- `sta` read the ASAP7 Liberty files and Stage 2 proxy netlist far enough to create black boxes for `mem_0_ext` and `mem_ext`.
- The first Tcl then failed because the local OpenSTA build does not support `report_design_area`.

Resolution before retry:

- Remove `report_design_area` from the Stage 3 OpenSTA sanity Tcl.
- Retry with read Liberty, read Verilog, link `Gemmini`, read SDC, and `report_checks` only.
- Keep SPEF as a recorded Stage 3 input; do not treat this lightweight sanity as signoff timing or power.

## 67. Stage 3 proxy grid power completed for tiled_matmul_os baseline

Date: 2026-04-26

Scope:

- Stage 3 grid-level power waveform for the active single `tiled_matmul_os_baseline` workload.

Result:

- Target-scoped VCD refinement generated `reports/stage1_tiled_matmul_os_baseline_target_windows.md` and `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`.
- The refined target-active window is `10222791082` to `10238889965 ps` inside the coarse `steady_high_load` candidate interval.
- Stage 3 power outputs were generated under `power/` with stable `stage3_tiled_matmul_os_baseline_*` names.
- The grid is `64 x 64`, has 64 time rows, covers all grid bins at every time row, and contains no negative or non-finite power values.
- OpenSTA lightweight sanity passed after using supported local commands; SPEF remains recorded as an input but is not read in the first proxy power model.

Acceptance:

- Stage 3 is accepted as `proxy / thermal-flow prototype` input for Stage 4 preparation.
- It is not signoff power because there is no gate-level SAIF/SDF, Stage 2 is non-signoff, memory bodies are proxy/blackbox, and the power model uses normalized region/area/activity proxy scaling.

## 68. Stage 4 PACT/HotSpot preflight and threading status

Date: 2026-04-26

Scope:

- Phase 3 acceptance review for Stage 4 handoff.
- Minimal PACT, HotSpot, Xyce, and OpenMPI readiness checks before starting Phase 4.
- Documentation update before formal Phase 4 implementation.

Findings:

- Stage 3 is accepted as `proxy / thermal-flow prototype` input for Phase 4 preparation. The grid is `64 x 64`, transient ptrace has `64` time rows, and peak target-bin total proxy power is normalized to `1.0 W`.
- Stage 2 DEF geometry gives die side `0.003373864 m`; Stage 4 floorplans must use this active design size rather than inheriting the PACT example 10 mm size.
- `python "$PACT_ENTRY" --help` works. PACT SuperLU example smoke generated two grid steady output layers under `/tmp/tp_phase4_pact_smoke/`.
- HotSpot tiny two-block smoke generated a valid `.ttrace`.
- OpenMPI runtime works for `mpirun -np 2`, but the current Xyce build is serial. PACT parallel mode is therefore not accepted for the current Stage 4 route.

Resolution / current plan:

- Documented Phase 4 preflight and development steps in `reports/stage4_tiled_matmul_os_baseline_preflight_plan.md`.
- Formal PACT SPICE steady/transient runs must set `number_of_core = 1` in modelParams unless the user explicitly authorizes a separate MPI-enabled Xyce rebuild and validation.
- Next Phase 4 work should start by generating PACT/HotSpot inputs from the existing Stage 3 artifacts, including `power/stage3_tiled_matmul_os_baseline_region_power_summary.csv`, then run PACT steady, PACT transient serial, and HotSpot coarse comparison in that order.
- No Phase 4 solver run has been started yet.

## 69. Stage 4 PACT transient ptrace requires a literal Power column

Date: 2026-04-26

Scope:

- First formal PACT SPICE transient attempt for `stage4_tiled_matmul_os_baseline`.

Failure evidence:

- Command: `python PACT.py ... lcf_stage4_tiled_matmul_os_baseline_transient.csv ... modelParams_stage4_tiled_matmul_os_baseline_transient_spice_serial.config --gridSteadyFile ...transient...`.
- PACT exited before Xyce launch with `KeyError: 'Power'` in `GridManager.py` while evaluating `flp_df['Power']`.
- The generated transient ptrace used columns `UnitName,Power0,Power1,...`, which matches the later `filter(regex='^Power')` path but not the earlier hard-coded `Power` access.

Current judgment:

- This is a Stage 4 input-format compatibility issue, not a solver failure and not a reason to lower Phase 4 standards.
- PACT expects the first transient power column to be named exactly `Power`; remaining time columns can use the `Power*` prefix.

Retry plan before the next attempt:

- Update `scripts/build_stage4_thermal_inputs.py` so transient ptrace columns are `UnitName,Power,Power1,...,Power63`, where `Power` is the first Stage 3 time row.
- Regenerate Phase 4 inputs, re-check ptrace shape, and retry PACT SPICE transient serial with `number_of_core = 1`.

## 70. Stage 4 PACT transient Xyce netlist needs local compatibility sanitization

Date: 2026-04-26

Scope:

- Second formal PACT SPICE transient attempt after fixing the transient ptrace `Power` column.

Failure evidence:

- PACT reached the Xyce launch step and generated `thermal/pact/stage4_tiled_matmul_os_baseline/transient_temperature_stage4_tiled_matmul_os_baseline.cir`.
- Xyce aborted during netlist parsing with `8064 MSG_ERROR errors` and no `.cir.csv` output.
- The Xyce log reports repeated `Illegal value found ... R value = INF` for Si layer lateral resistors.
- The generated netlist also contains `.TRAN 16.098884us None`, because the local PACT transient solver reads `total_simulation_time` while the initial generated modelParams file only had the misspelled example key `total_simualation_time`.

Current judgment:

- This is a local PACT/Xyce netlist compatibility issue, not a need to reduce grid size, skip transient, or change the research target.
- The `inf` values are caused by the local PACT floorplan/grid exact-float path for one-block-per-grid-cell input. The intended Si lateral resistance is finite and computable from the same config and grid geometry: `ro * length / (height * thickness)`, which is `77.0 ohm-equivalent` for the current square Si grid cells and `0.0001 m` Si layer thickness.

Retry plan before the next attempt:

- Update generated modelParams to include both `total_simualation_time` and the correctly spelled `total_simulation_time`.
- Add a Stage 4 netlist sanitizer for generated PACT transient `.cir` files only. It must not edit `third_party/PACT` source. It will replace Si-layer lateral `inf` resistors in the generated `.cir` with the computed finite Si lateral resistance and replace transient `None` total-time fields with the configured total time.
- Re-run Xyce serial on the sanitized generated netlist, then parse the Xyce CSV into Stage 4 transient grid statistics and final layer outputs.
- This is treated as a compatibility repair preserving the intended PACT RC model, not as a lowered-standard route.

## 71. Stage 4 completed for tiled_matmul_os proxy thermal-flow prototype

Date: 2026-04-26

Scope:

- Completion of Phase 4 PACT mainline thermal simulation and HotSpot coarse comparison for the active single baseline.

Result:

- `scripts/build_stage4_thermal_inputs.py` generated PACT and HotSpot inputs from Stage 3 proxy artifacts.
- PACT steady SuperLU completed and generated two layer output files.
- PACT transient was solved through the generated sanitized Xyce netlist path documented in items 69 and 70; `transient_temperature_stage4_tiled_matmul_os_baseline.sanitized.log` reports `0` failed linear solves and `0` nonlinear convergence failures.
- HotSpot coarse comparison completed and generated `thermal/hotspot/stage4_tiled_matmul_os_baseline/stage4_tiled_matmul_os_baseline.ttrace`.
- Figures and tables were generated under `artifacts/stage4/`.
- Final reports were generated under `reports/`: PACT report, HotSpot report, and Stage 4 summary.

Acceptance:

- Stage 4 is accepted as `proxy / thermal-flow prototype`, completing the active Stage 0-4 route.
- The result remains non-signoff because Stage 2 is proxy/non-signoff, Stage 3 power is normalized proxy power, there is no SDF, and SRAM macro bodies are not detailed thermal sources.


## 72. 2026-04-29 Stage 1 signoff run parameter correction: NUMACTL disabled

Scope:

- Then-active Stage 1 run for `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`.

Evidence:

- The interrupted `tiled_matmul_os` attempt used `NUMACTL=1`.
- Chipyard `scripts/numa_prefix` attempted to run `numactl -H` and raised `FileNotFoundError: [Errno 2] No such file or directory: 'numactl'`.
- `command -v numactl` returns no path on this host.
- The attempt was interrupted by the user before completion; partial simulator output is not accepted as Stage 1 evidence.

Current judgment:

- `numactl` is an optional host-affinity helper, not a required Gemmini functional dependency.
- Disabling `NUMACTL` does not downgrade the RTL waveform or activity extraction methodology.
- Historical threading records still support `VERILATOR_THREADS=16` as the default simulator-thread setting for this host, and `VCD_PARSER_WORKERS=128` as the parser setting for large VCD parsing.

Next-step plan:

- Continue active Stage 1 with `NUMACTL=0`, `VERILATOR_THREADS=16`, `VCD_PARSER_WORKERS=128`.
- Reuse the already built debug simulator with `BUILD_DEBUG_SIM=0` unless simulator settings change.
- Keep `MAKE_JOBS` conservative when no simulator build is requested; only use higher `MAKE_JOBS` for build parallelism, not as a simulation-thread setting.


## 73. Stage 2 signoff filelist migration must not duplicate memory blackboxes

Date: 2026-04-29.

During the then-active Stage 2 preflight for `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`, the first Yosys/slang hierarchy smoke failed before any heavy ORFS run. The migrated reduced filelist retained the old `physical/stage2_tiled_matmul_os_baseline_asap7/src/gemmini_stage2_memory_blackboxes.sv`, while the new run-root config also provided `runs/.../physical/config/src/gemmini_stage2_memory_blackboxes.sv` through `VERILOG_FILES`. Slang reported duplicate definitions of `mem_ext`, `mem_0_ext`, and `mem_1_ext`.

Resolution: keep memory blackboxes out of `gemmini_stage2_sources_reduced.f`; provide them exactly once through the active run-root `VERILOG_FILES` entry. This is a filelist hygiene fix, not a proxy fallback or methodology downgrade.

## 74. Stage 2 signoff floorplan can pass while carrying severe early timing and PDN caveats

- Date: 2026-04-29.
- Context: active run `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`, Stage 2 `floorplan` target.
- Evidence: `2_1_floorplan` exited successfully, but early repair timing reported `Unable to repair all setup violations`; metrics showed `period_min = 5464.04 ps`, `fmax = 183.01 MHz`, below the 200 MHz target. PDN logs reported memory macro blackboxes not connected to power/ground nets and many M5/M6 no-via/floating-shape warnings.
- Current judgment: not a confirmed flow failure at floorplan because required floorplan ODB/SDC outputs were produced and downstream placement/CTS/route may change timing. These caveats must be carried into Stage 2 final signoff judgment; final Stage 2 cannot claim timing/physical high-confidence unless downstream reports support it.
- Next step: continue to `place` with the then-active route and no proxy fallback; stop if a command exits failed or final required outputs/quality are insufficient.

## 75. Stage 2 signoff placement can complete while far below the 200 MHz target

Date: 2026-04-29.

Scope:

- Active run `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`, Stage 2 `place` target.

Evidence:

- `scripts/run_stage2_signoff_openroad.sh place` exited 0 and generated `3_place.odb`, `3_place.sdc`, `3_global_place.rpt`, `3_resizer.rpt`, and `3_detailed_place.rpt`.
- No prohibited fallback knob (`FLOW_VARIANT=noaddermap`, `REMOVE_ABC_BUFFERS`, `GPL_TIMING_DRIVEN=0`, `SKIP_CTS_REPAIR_TIMING`, `SKIP_REPORT_METRICS`, or `SKIP_LAST_GASP` env fallback) was enabled by the run.
- Global placement ran to 5000 iterations with final overflow about `0.368`; metrics reported `period_min = 1334724.00 ps`, `fmax = 0.75 MHz`.
- Resizer completed but reported `240637` slew violations, `10903` capacitance violations, `17125` long wires, `105857` inserted buffers, and `631594` resized instances; metrics remained below target at `period_min = 11041.19 ps`, `fmax = 90.57 MHz`.
- Detailed placement reported zero placement legality violations, but final metrics were still `period_min = 11502.83 ps`, `fmax = 86.94 MHz`, with `81915` setup violations and setup TNS `-1.82834e+08`.

Current judgment:

- This is not a confirmed OpenROAD execution failure: required placement outputs exist and the command exited successfully.
- It is a severe Stage 2 quality failure risk. The then-current placement state could not support a 200 MHz strict/high-confidence claim.
- CTS/route may change timing, but continuing automatically would spend substantial runtime on a run that is already far from the target; pause and report before proceeding.

Next-step plan:

- Do not auto-switch to `noaddermap` or other proxy knobs.
- Do not launch CTS until the user confirms whether to continue the strict route for evidence gathering, stop Stage 2 as failed at placement quality, or revise the active Stage 2 plan.

## 76. ATSim3D public repo ships Python 3.8 `.pyc` modules

### 现象

- 使用项目主环境 `thermal_placement` 的 Python 3.11 运行 `third_party/ATSim3D_pub/src/ATSim3D.py --help` 失败。
- 报错：`ImportError: bad magic number in 'ATSimCore': b'U\r\r\n'`。
- README 列出了 numpy、pandas、scipy、tqdm、matplotlib，但实际还需要 `psutil`。

### 根因

ATSim3D public repo 只公开了 `ATSim3D.py` 和部分核心模块的 `.pyc`，这些 `.pyc` 是 Python 3.8 bytecode，不能由 Python 3.11 加载。

### 解决方法

- 源码放置在 `third_party/ATSim3D_pub`，commit `8454f719409a6d0b1759602e89601f8ae18b95c2`。
- 创建隔离运行时 `tools/atsim3d-py38`，Python `3.8.20`。
- 安装 Python 依赖：numpy `1.24.4`、pandas `2.0.3`、scipy `1.10.1`、tqdm `4.67.3`、matplotlib `3.7.5`、psutil `7.2.2`。
- 添加 wrapper：`scripts/run_atsim3d.sh`。

第一次尝试用 conda 一次性安装 Python 3.8 与全部数值库时，`scipy-1.10.1` 下载发生 `ReadTimeoutError` / `IncompleteRead`。后续改为 conda 只创建 Python 3.8 + pip 的轻量环境，再用 PyPI wheel 安装 Python 包，验证通过。

### 验证

```bash
bash -n scripts/run_atsim3d.sh
scripts/run_atsim3d.sh --help

timeout 600 scripts/run_atsim3d.sh \
  --lcfFile third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.csv \
  --ConfigFile third_party/ATSim3D_pub/2DIC/Intel.config \
  --SimParamsFile third_party/ATSim3D_pub/2DIC/SimParms.config
```

2DIC、Mono3D、TSV3D 三个 README 示例均完成，并生成可由 `numpy.loadtxt` 读取的 `.res` 结果文件。

## 77. ATSim3D v2 binary needs XML/config/material/power inputs for full validation

### 现象

- 用户提供的 `ATSim3_5D` 是 README v2 下载二进制，不是 v1 Python `.pyc` route。
- `third_party/ATSim3D_pub` 当前只包含 v1 CSV/config 示例，未发现完整 v2 XML/config/material/power/floorplan 示例。
- `scripts/run_atsim3_5d.sh --help` 可正常打印参数；缺失 XML/config 时只能做启动、参数和错误路径 smoke。

### 根因

ATSim3D v2 使用 `-xml <XmlFile> -config <ConfigFile> --output_path <OutputDir>` 接口。仓库 README 只给出入口形态；论文描述 geometry/power/configuration 输入和 multiscale grid/FAS-MG 求解流程，但没有提供完整 XML schema 或可运行 case。

### 已确认接口

- XML 至少需要 `MaterialLib File="..."`；`<MaterialLib>path</MaterialLib>` 会报 `MaterialLib File attribute missing`。
- material library 是 INI/configparser 风格，每个 material section 至少需要 `conductivity (w/(m-k))`，并需要 `volumetric heat capacity (j/(m3-k))` 或 `density (kg/m3)` + `specific heat capacity (j/(kg-k))`。
- `power_type = value` 时，XML 中的 `Power File="..."` 可读取 direct-value CSV；已确认简单表头为 `UnitName,Power_dyn,Power_leak`。
- config 至少包含 `[Simulation]` 和 `[MeshConfig]`；已确认读取 `number_of_core`、`sim_mode`、`power_type`、`calc_leakage`、`power_gran`、`unit_agg_method`、`calc_kappa_type`、`init`、`ambient`、`max_depth`、`min_depth`、`max_thickness`、`grid_expand_factor`、`tol_zero`、`ratio_ignore`、`fine_grid_num`、`powerdens_th`、`rows`、`cols` 等字段。
- 带 `MaterialLib File`、基本 `[Simulation]` 和 `[MeshConfig]` 的探测输入已进入 `GridManager` 初始化，下一处缺失字段为 `tiers_active`；这说明仍缺完整 tier/chiplet/package 相关 schema。

### 解决方法

- 将根目录 `ATSim3_5D` 移动到本地工具载荷目录：`tools/atsim3d-bin/ATSim3_5D`。
- 设置执行权限，并添加 wrapper：`scripts/run_atsim3_5d.sh`。
- wrapper 在 `/etc/fonts/fonts.conf` 存在时设置 `FONTCONFIG_FILE`，消除启动时的 Fontconfig 警告。
- 将已确认接口、论文对应关系和探测结果记录到 `docs/atsim_tool_guide.md`。

### 验证

```bash
bash -n scripts/run_atsim3_5d.sh
ldd tools/atsim3d-bin/ATSim3_5D
timeout 20 scripts/run_atsim3_5d.sh --help
timeout 20 scripts/run_atsim3_5d.sh \
  -xml /tmp/missing.xml \
  -config /tmp/missing.config \
  --output_path /tmp/atsim3_5d_missing
```

结果：`--help` 返回状态 `0`，无 stderr；缺 XML 输入返回状态 `1` 并报告 `XML file /tmp/missing.xml not found`。完整热仿真仍需要匹配 v2 的 XML/config/material/power/floorplan 输入集。

## 78. Stage 4 PACT raw grid row order is not DEF physical `grid_y`

Date: 2026-05-03.

Scope:

- Historical Stage 4 baseline artifacts under `artifacts/stage4/` and `thermal/pact/stage4_tiled_matmul_os_baseline/`.
- Post-processing only; PACT, HotSpot, and ATSim solver inputs were not rerun or changed.

Phenomenon:

- Stage 3 standard-cell placement uses DEF physical coordinates: `grid_y=0` is the die bottom and `grid_y` increases upward.
- PACT raw steady/transient result files are emitted in internal numpy row-major order. In that raw order, row `0` corresponds to the physical top of the die, not DEF `grid_y=0`.
- Treating PACT raw row index as physical `grid_y` put the reported steady layer0 hotspot at `(22,47)`, which mismatched the standard-cell power field and ATSim result.

Root cause:

- PACT's grid construction maps physical y=0 to the bottom of its internal array, but output flattening writes row-major array order. The row index in the emitted file is therefore an internal row, not the project's DEF physical `grid_y`.

Mandatory fix method:

```text
physical_grid_y = 64 - 1 - pact_raw_row_y
```

This y-flip must be applied to every user-facing PACT grid/rank/heatmap and to any standard-cell overlay using PACT temperatures. Raw PACT row-order data may be kept only as audit evidence with `_pact_raw_order` in the filename. Do not report `_pact_raw_order` coordinates as physical coordinates.

Applied repair:

- Updated `scripts/report_stage4_thermal_results.py` so main PACT artifacts are written in DEF physical y-up coordinates and raw-order copies are retained as `*_pact_raw_order.csv`.
- Updated `scripts/report_stage4_standard_cell_context.py` report text and regenerated `artifacts/stage4/standard_cell_context/` against corrected PACT grids.
- Updated `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/generate_atsim_stage4_artifacts.py` so the primary ATSim/PACT comparison uses corrected physical PACT; raw-order comparison is diagnostic only.
- Removed stale `*_yflip_*` ATSim artifacts from the main artifact set and replaced them with explicit `*_raw_order_*` diagnostics.
- Added `artifacts/stage4/README.md` and updated related ATSim artifact documentation.

Validation evidence:

- Corrected PACT steady layer0 hotspot: physical grid `(22,16)`, 333.720 K.
- Old raw row-order hotspot: raw `(22,47)`, 333.720 K; this is not a physical grid location.
- ATSim vs corrected PACT: correlation `0.972618931`, abs mean delta `1.326155691 K`, RMS `1.679745032 K`.
- ATSim vs PACT raw row order: correlation `-0.141279496`, abs mean delta `2.771164102 K`, RMS `3.371622051 K`.
- Standard-cell hotspot context now queries physical grid `(22,16)` for the PACT top location; the same grid has Stage 3 proxy power rank 38 rather than the misleading raw-location rank 1452.

Regeneration commands:

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python scripts/report_stage4_thermal_results.py
/home/lisihang/miniconda3/envs/thermal_placement/bin/python scripts/report_stage4_standard_cell_context.py
/home/lisihang/miniconda3/envs/thermal_placement/bin/python thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/generate_atsim_stage4_artifacts.py
```

## 79. Standard-cell context SVG figures need PNG companions for VS Code preview

Date: 2026-05-03.

Scope:

- Stage 4 standard-cell context artifacts under `artifacts/stage4/standard_cell_context/`.
- Post-processing/reporting only; no PACT, HotSpot, ATSim, Stage 2, or Stage 3 solver input was changed.

Phenomenon:

- VS Code remote/workspace viewing does not reliably preview the generated Matplotlib `.svg` figures directly. The SVG files are still useful as vector artifacts, but daily inspection needs bitmap companions.

Applied repair:

- Updated `scripts/report_stage4_standard_cell_context.py` so every saved standard-cell `.svg` figure also writes a same-basename `.png` file.
- Kept the existing SVG trailing-whitespace cleanup so `git diff --check` remains clean.
- Regenerated `artifacts/stage4/standard_cell_context/` and `reports/stage4_tiled_matmul_os_baseline_standard_cell_context.md`.
- Updated `artifacts/stage4/README.md` and `docs/README.md` to record the SVG/PNG artifact convention.

Generated PNG companions:

- `artifacts/stage4/standard_cell_context/standard_cell_region_share.png`
- `artifacts/stage4/standard_cell_context/standard_cell_grid_context.png`
- `artifacts/stage4/standard_cell_context/standard_cell_hotspot_overlay.png`
- `artifacts/stage4/standard_cell_context/standard_cell_master_power.png`

Validation command:

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python scripts/report_stage4_standard_cell_context.py
```

## 80. Active documentation synchronized for PACT coordinate and SVG/PNG artifact rules

Date: 2026-05-03.

Scope:

- Documentation-only update after the Stage 4 PACT coordinate fix and standard-cell SVG/PNG companion change.
- No scripts or simulation artifacts were regenerated in this documentation pass.

Applied documentation update:

- Updated then-active `docs/phase0tophase4_signoff_multiworkload_plan.md` so Stage 4 explicitly required DEF physical grid coordinates for main thermal artifacts, PACT raw row-order audit handling, a coordinate manifest, standard-cell physical-context overlays, and same-basename PNG companions for generated SVG figures. As of 2026-05-05 this file is legacy under `docs/references/legacy_openroad_proxy/`.
- Updated `docs/agent_task_checklist.md` so Stage 4 preflight/output/exit criteria check PACT coordinate conversion and SVG/PNG companions.
- Updated `docs/agent_command_reference.md` so the Stage 4 report commands state that PACT main outputs are corrected physical-coordinate views and standard-cell context figures emit SVG plus PNG.
- Updated `docs/README.md` so the docs index points to the current active-plan and artifact conventions.

Key rule now reflected in the active plan:

```text
physical_grid_y = grid - 1 - pact_raw_row_y
```

PACT raw row-order files are audit-only; generated SVG figures must have same-basename PNG companions for VS Code/remote preview.

## 81. Historical single-workload plan updated with Stage 4 coordinate and PNG errata

Date: 2026-05-03.

Scope:

- Documentation-only update to `docs/phase0tophase4_plan.md`, the old single-workload/proxy reference plan.
- This did not reactivate the old plan. As of 2026-05-05 both old plans live under `docs/references/legacy_openroad_proxy/`, and `docs/phase0tophase4_cadence_asap7_plan.md` is active.

Applied documentation update:

- Added a superseded-plan errata note stating that PACT raw row `0` maps to physical die top and that main PACT artifacts must be interpreted in DEF physical grid coordinates.
- Replaced the old physical hotspot statement `grid (22,47)` with the corrected physical hotspot `grid (22,16)` and explicitly labeled `(22,47)` as raw row-order only.
- Added the mandatory correction formula `physical_grid_y = grid - 1 - pact_raw_row_y` to the historical Stage 4 section.
- Added the SVG plus same-basename PNG companion convention for standard-cell context figures.
- Updated `docs/README.md` so the historical plan entry mentions the 2026-05-03 errata.

## 82. Fake SRAM collateral added as external input asset

Date: 2026-05-05.

Status update: this entry is historical. The active Cadence/Gemmini flow was later changed to first-principles generation with `scripts/prepare_gemmini_fake_sram_collateral.py`; see Section 0.5. The external design groups below are retained only as inventory/method reference.

Scope:

- Local SRAM collateral unpacking and path configuration only.
- No Gemmini RTL, memory wrapper, Genus synthesis, Innovus floorplan, Stage 3 power, or Stage 4 thermal flow was changed.

Applied update:

- Unpacked `/home/lisihang/sram_gen.zip` into `/home/lisihang/fake_sram/` and checked out branch `thermal_placement` in that external repo.
- Preserved the external repo `.git` metadata so `/home/lisihang/fake_sram` can stay on branch `thermal_placement`; ZIP-provided source, config, caches, and generated SRAM collateral remain available.
- Added `FAKE_SRAM_HOME`, `FAKE_SRAM_ASAP7_ROOT`, and `FAKE_SRAM_ASAP7_CONFIG` to `tools/env_gemmini_thermal.sh`.
- Added Make and Cadence Tcl manifests under `configs/fake_sram/`.
- Added `scripts/check_fake_sram_collateral.py` to verify ASAP7 fake SRAM LEF/Liberty/DB consistency.

Validation:

```bash
source tools/env_gemmini_thermal.sh
python scripts/check_fake_sram_collateral.py
```

Result:

- The checker reports 8 ASAP7 fake SRAM design groups and 254 macros with matching LEF/Liberty/DB basenames.
- Genus `23.14-s090_1` read one fake SRAM Liberty through `configs/fake_sram/asap7_fake_sram.tcl`.
- Innovus `v23.14-s088_1` read the ASAP7 1x tech/stdcell LEF plus one fake SRAM LEF through the same Tcl manifest.

Current limitation:

- The fake SRAM collateral is now path-configured and tool-readable, but it is not yet mapped into Gemmini memory wrappers. Replacing `mem_ext`, `mem_0_ext`, or `mem_1_ext` still requires explicit wrapper/interface work and a new Stage 2 plan decision.

## 15. 2026-05-05 dacs-lab full ASAP7 1x Genus/Innovus trial

用户要求拉取 `git@github.com:pku-gsun/dacs-lab.git` 到 ignored 路径 `third_party/dacs-lab`，并使用其已有脚本配合当前 full ASAP7 做一次综合和布局布线，不影响主仓库 Git。

当前外部仓库状态：

- 路径：`third_party/dacs-lab`
- commit：`27242a9`
- 主仓库 `.gitignore` 已忽略 `third_party/`，外部源码和运行结果不进入主仓库 Git。
- `thermal_placement` conda 环境新增 Python 包 `networkx 3.4.1`，原因是 `dacs-lab` 的 prefix-adder 设计生成依赖该包；验证命令为 `python -c "import networkx"`。

### Attempt 1

运行目录：`third_party/dacs-lab/runs/tp_asap7_1x_ppadder_64_20260505_102556/`。

输入配置：

- design：`dacs-lab` 自带 `PPAdder` 64-bit Sklansky prefix adder 示例。
- Genus/Innovus entry：`dacs-lab.flow.genus_innovus.GenusInnovusFlow` 和其已有 `GenusManager` / `InnovusManager`。
- ASAP7：当前 active full-ASAP7 `asap7sc7p5t_28` 1x collateral。
- Liberty：`.cache/asap7/asap7sc7p5t_28/NLDM` 中 15 个 TT NLDM `.lib`，用于 setup/hold library set。
- LEF：`/home/lisihang/asap7/asap7sc7p5t_28/techlef_misc/asap7_tech_1x_201209.lef` 加 `LEF/*_1x_220121a.lef`。
- QRC：`qrc/qrcTechFile_typ03_unscaledV02`。
- CPU：Genus/Innovus 均按 `8` 配置。

结果：Genus 本体成功完成综合和报告，输出 `PPAdder-mapped.v`、`PPAdder.sdf`、setup/hold SDC、timing/power/area/DRC/QoR reports。随后 Python 侧失败，未进入 Innovus：

```text
ValueError: too many values to unpack (expected 5)
```

失败点在 `third_party/dacs-lab/manager/genus/parser/area.py`，其 `GenusAreaReportParser` 假设 Genus area report root 行只有 5 列；当前 Genus `23.14-s090_1` 报告格式包含更多字段。

当前判断：这不是 Cadence 或 ASAP7 blocker，而是 `dacs-lab` 结果 parser 与当前 Genus report 格式不兼容。下一步不修改主仓库，不修改 active Gemmini flow；改为直接复用 Attempt 1 已生成的 `GenusManager` 输出，调用 `dacs-lab.manager.innovus.InnovusManager` 继续 Innovus init/floorplan/powerplan/place/route，绕过 `GenusInnovusFlow.run()` 中的 parser 汇总阶段。

### Attempt 2

执行方式：绕过 `GenusInnovusFlow.run()` 的 Python report parser，直接调用 `dacs-lab.manager.innovus.InnovusManager`，输入 Attempt 1 的 Genus mapped netlist 和 SDC。

结果：

- Innovus `init` 完成并写出 `init.enc`。
- `floorplan` 完成并写出 `floorplan.def` / `floorplan.enc`。
- `powerplan` 完成并写出 `powerplan.enc`。
- `placement` 完成并写出 `placement.enc`，preCTS timing WNS 约 `0.007 ns`、TNS `0.000 ns`，routing overflow `0.00% H + 0.00% V`。
- `routing` 进入 `routeDesign -globalDetail`，global route overflow 为 `0.00% H + 0.00% V`，track assignment 和 RC extraction 已执行；随后在 post-route hold delay calculation 的 AAE 内部崩溃，未写出 `routing.enc`。

关键失败证据：

```text
innovus: ../../include/peThreadUtils.hpp:262: ... Assertion `m_numThreads < m_maxThreads' failed.
Innovus terminated by internal (ABORT) error/signal...
Crashed in AAE on net n_246.
utils.exceptions.RoutineCheckError: Routine check failed.
```

其它 caveat：

- 多个 stage 读入 full ASAP7 1x LEF 时报告 `IMPTR-2101`：`Layer M10: Pitch=720x9 is still less than min width=2000 + min spacing=40`。当前 route 限制为 `M2` 到 `M8`，但该 tech LEF/route extraction warning 仍被计入 error summary。
- `powerplan` 的 special-wire connectivity 检查报告 `14 Viols`，PG short 为 `0 Short Viols`。
- 示例设计没有显式 IO pin assignment，placement/route 阶段报告大量 unplaced top-level terms；这影响当前 `dacs-lab` 示例 route 质量，不是 active Gemmini flow 的 signoff 结果。

当前判断：Attempt 2 已证明 `dacs-lab` 的 Genus、Innovus init/floorplan/powerplan/place 脚本可配合当前 full-ASAP7 1x/NLDM 输入运行，但 route 阶段在 post-route timing/AAE 处遇到 Cadence internal abort。下一步做一个最小 route-only retry：从 `placement.enc` 继续，仅修改本次 generated routing Tcl，使 `setMultiCpuUsage -localCpu 1` 且 `setDelayCalMode -engine default -siAware false`，用于判断是否为 SI-aware/threading 组合触发的内部崩溃。该 retry 仍只改 ignored run directory，不改主仓库 flow。

### Attempt 3

执行方式：从 Attempt 2 已完成的 `placement.enc` 做 route-only retry，只修改 ignored run directory 内的 generated Tcl：

- `setMultiCpuUsage -localCpu 1`
- `setDelayCalMode -engine default -siAware false`

命令入口：`innovus -no_gui -batch -abort_on_error -overwrite -file innovus-rundir/scripts/routing_retry_si_off_cpu1.tcl`。

结果：retry 进程返回码为 `0`，完成 global/detail route、post-route opt、post-route timing/power/area reports，并写出 routed Innovus database：

- `innovus-rundir/data/routing.enc`
- `innovus-rundir/reports/postRoute_timing/timing.rpt`
- `innovus-rundir/reports/postRoute_area.rpt`
- `innovus-rundir/reports/postRoute_power.rpt`

Post-route 摘要：

- global route overflow：`0.00% H + 0.00% V`
- setup WNS：`0.010 ns`
- setup TNS：`0.000 ns`
- density：`59.233%`
- stdcell instances：`359`
- total area：`32.878`
- total power：`0.12241223 mW`，其中 internal `0.06455852 mW`，switching `0.05459741 mW`，leakage `0.00325630 mW`

Remaining caveat：

- Innovus final message summary 仍保留 `2 error(s)`，来源是 full-ASAP7 1x LEF/route-track 检查的 `IMPTR-2101`：`Layer M10: Pitch=720x9 is still less than min width=2000 + min spacing=40`。流程实际 route 限制为 `M2` 到 `M8`，且 database 已保存，但该 error summary 不能视为 clean signoff。
- `powerplan` special-wire connectivity 仍为 `14 Viols`，PG short 为 `0 Short Viols`。
- `dacs-lab` 示例没有显式 IO pin assignment，post-route RC extraction 报告多条 top-level input/output pin driver/route 完整性 warning。
- 本结果只是 `dacs-lab` 自带 PPAdder 示例对当前 full-ASAP7 1x/NLDM + Cadence Genus/Innovus 路径的兼容性试跑，不是 active Gemmini Stage 2 signoff。

当前判断：用户要求的 clone、使用 `dacs-lab` 既有 manager/script 机制配合当前 full-ASAP7 做一次完整综合和布局布线已完成；主仓库 Git 未纳入 `third_party/dacs-lab` 源码或 run outputs。为满足环境/结果记录规则，本次仅更新 active docs 中的环境包和尝试记录。

### Layout preview artifact

应用户后续要求，额外从 routed Innovus database 导出 routed DEF，并生成两个静态 PNG 预览。该操作只读取 `routing.enc` 并导出/绘图，没有重新运行布局布线。

- DEF export Tcl：`innovus-rundir/scripts/export_routed_def.tcl`
- routed DEF：`innovus-rundir/data/routing.def`
- routed preview：`innovus-rundir/reports/layout_preview_routed.png`
- placement preview：`innovus-rundir/reports/layout_preview_placement.png`

导出 DEF 时仍复现 `IMPTR-2101` M10 track pitch error summary，和前述 non-clean caveat 一致。

### Follow-up issue record before fixes

Date: 2026-05-05.

用户要求在继续修复前先记录当前问题，再解决并记录尝试结果。当前待处理项：

1. 多线程配置需要确认是否应由 `dacs-lab` Python manager/main 统一生成 Tcl，而不是手工改 generated Tcl。当前判断：Genus/Innovus 线程数确实由 Python 配置写入 Tcl；但 route retry 为规避 Innovus AAE internal abort 手工在 ignored run directory 中改为 `localCpu 1` 和 `SIAware false`，还没有回写成可复用 Python 配置。
2. `third_party/dacs-lab/manager/genus/parser/area.py` 与当前 Genus `23.14-s090_1` area report 格式不兼容，导致 `ValueError: too many values to unpack (expected 5)`，应修复 parser 而不是长期绕过 `GenusInnovusFlow.run()`。
3. non-clean 结果是否由 `main.py`/flow script 未配置完整导致需要确认。当前判断：一部分问题来自 flow 配置不足，例如 IO pin assignment、PG connectivity、route retry 参数没有产品化；但 `IMPTR-2101` 是 ASAP7 1x M10/Pad track/tech LEF 检查问题，不能简单归因于 `main.py`。
4. Innovus 原生截图需要寻找可用命令或 GUI/显示环境；当前已有 DEF-based PNG preview，但不是 Innovus native screenshot。
5. 修复完成后需要记录：代码修改、验证命令、是否重新跑通 Genus->Innovus，以及仍未解决的 clean signoff blocker。

### Follow-up issue record before 100 MHz retry

Date: 2026-05-05.

The interrupted Lab1 `main.py` validation showed that the Python flow now reaches Innovus detailed routing with reusable Python-level thread/SI settings, but `experiment/dacs2024/lab1/main.py` still sets `clk_period_ns` to `0.0`. This generates a zero-period clock and invalid timing target in both Genus and Innovus. Before rerunning, set the Lab1 default timing target to 100 MHz (`10.0 ns`) at the Python config layer, preferably with an environment-variable override, so generated Tcl/SDC is reproducible without manual run-directory edits.

No residual Genus/Innovus/Lab1 `main.py` process was found before this retry. The route quality and native screenshot status still need to be rechecked after the 100 MHz rerun.

### Follow-up fix and 100 MHz retry result

Date: 2026-05-05.

Files changed under ignored `third_party/dacs-lab` for this compatibility trial:

- `experiment/dacs2024/lab1/env.py`: replaced stale hardcoded `/root/asap7` and old Cadence binary paths with environment-overridable local defaults (`ASAP7_HOME`, `GENUS_BIN`, `INNOVUS_BIN`).
- `experiment/dacs2024/lab1/main.py`: moved Genus/Innovus thread counts to Python config defaults of 8 with `TP_CADENCE_GENUS_CPUS` / `TP_CADENCE_INNOVUS_CPUS` overrides; added Python-level route retry knobs `TP_DACS_ROUTE_CPUS` and `TP_DACS_ROUTE_SI_AWARE`; changed the default timing target from invalid `0.0 ns` to 100 MHz (`10.0 ns`) with `TP_DACS_CLK_PERIOD_NS` override.
- `manager/genus/parser/area.py`: fixed Genus 23.14 area report parsing. The parser now accepts current 6-column lines (`Instance Module Cell-Count Cell-Area Net-Area Total-Area`) and older 5-column lines, treats `NA` module values as the top module name, and skips blank lines.
- `manager/innovus/innovus_manager.py`: made the route-stage `setMultiCpuUsage` and `setDelayCalMode` lines generated from Python config instead of manual run-directory edits.
- `tech/asap7.py`: updated the default ASAP7 collateral to local full-ASAP7 `asap7sc7p5t_28` 1x LEF/QRC and optional `.cache/asap7/.../NLDM` TT Liberty cache; adjusted route minimum layer and stripe dimensions for micron-scale 1x collateral.

Light validation before heavy rerun:

- `python -m compileall` passed for the touched Python files.
- Config probe returned `clk_period_ns=10.0`, Genus threads `8`, Innovus threads `8`, route threads `1`, route SI-aware `False`.
- Required inputs existed: `/home/lisihang/asap7/asap7sc7p5t_28`, `.cache/asap7/asap7sc7p5t_28/NLDM`, `/opt/eda/Cadence_DDI_23.14/bin/genus`, and `/opt/eda/Cadence_DDI_23.14/bin/innovus`.

Full rerun command:

```bash
source /home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh
cd /home/lisihang/thermal_placement/third_party/dacs-lab/experiment/dacs2024/lab1
TP_DACS_CLK_PERIOD_NS=10.0 TP_DACS_ROUTE_CPUS=1 TP_DACS_ROUTE_SI_AWARE=false timeout 2400 /home/lisihang/miniconda3/envs/thermal_placement/bin/python main.py
```

The previous partially-run same-hash result directory was preserved as:

```text
third_party/dacs-lab/experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540_before_100mhz_20260505
```

100 MHz rerun result directory:

```text
third_party/dacs-lab/experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540
```

Result summary:

- `main.py` completed with return code `0` and wrote `result.json`.
- Genus completed normally. Evidence: generated SDC has `set clk_period_ps 10000.0`; Genus log has `set_db max_cpus_per_server 8` and repeated `Number of threads: 8 * 1` records. The fixed area parser did not block `GenusInnovusFlow.run()`.
- Innovus completed init, floorplan, powerplan, placement, routing, post-route optimization, post-route timing/power/area reports, and saved `routing.enc`.
- Innovus threading evidence: license banner allowed `8 CPU jobs`; library loading used `Multi-threaded flow` with `8` threads; pre-place and pre-route delay calculation used `8 T`; placement reported `Enabling multi-CPU acceleration with 8 CPU(s)` and `GigaOpt running with 8 threads`; generated route Tcl switched route stage to `setMultiCpuUsage -localCpu 1` and `setDelayCalMode -engine default -siAware false`; post-route timing ran with `1 T`, matching the route-stage workaround.
- Timing target is now valid: Innovus route log reports `clk period 10.000 (ns)`; post-route WNS is about `7.300 ns` and TNS is `0.000 ns`.
- Detail route converged: final route DRC summary reports `Total number of DRC violations = 0`.
- `result.json`: post-syn timing `832`, post-place timing `1707.299`, post-route timing `1700.3`, post-route power `8.828e-06`, post-route area `32.572`.
- Post-route area report: `352` instances, total area `32.572 um^2`.
- Post-route power report: internal `0.00319022`, switching `0.00252399`, leakage `0.00311407`, total `0.00882828` in report units.

Current outputs:

- `genus-rundir/data/PPAdder-mapped.v`
- `genus-rundir/data/PPAdder.sdf`
- `genus-rundir/data/constraint_setup.sdc`
- `innovus-rundir/data/routing.enc`
- `innovus-rundir/reports/postRoute_timing/timing.rpt`
- `innovus-rundir/reports/postRoute_area.rpt`
- `innovus-rundir/reports/postRoute_power.rpt`
- `innovus-rundir/data/routing.def`
- `innovus-rundir/reports/layout_preview_routed_100mhz.png`

Why this is still not clean signoff:

1. Innovus final message summary is still `1057 warning(s), 2 error(s)`. The blocking errors are the recurring full-ASAP7 1x M10/Pad track check issue:

   ```text
   IMPTR-2101: Layer M10: Pitch=720x9 is still less than min width=2000 + min spacing=40.
   ```

   The routed design is constrained to M2-M8 and route DRC reaches zero, but Innovus still checks/extracts standard-cell pins/blockages across the full tech LEF stack and records M10 as an error. Therefore this run cannot be called clean signoff even though `main.py` returns successfully.

2. PG connectivity is not clean. The powerplan check reports `Verification Complete : 10 Viols`; PG short check reports `0 Short Viols`. This is improved from earlier attempts but still not clean.

3. The `dacs-lab` PPAdder example has no explicit top-level IO pin placement. Innovus reports `192 nets have unplaced terms`, and RC extraction emits `NREX-80` warnings for many top-level input nets that do not have driver pins. Timing and route DRC are usable for this compatibility trial, but this is not a clean physical signoff setup.

4. This is only a `dacs-lab` PPAdder compatibility run using full ASAP7 1x/NLDM and Cadence Genus/Innovus. It is not the active Gemmini Stage 2 signoff result.

Innovus native screenshot status:

- Current shell has no `DISPLAY`, and `xvfb-run` is not installed.
- Innovus `-no_gui` command help did not expose `hardcopy`, `saveImage`, `savePicture`, `write_snapshot`, `dumpDisplay`, `saveFPlanImage`, `guiSaveImage`, `save_image`, `write_image`, or `writeFPlanImage` commands. `win`, `fit`, and `getDrawView` exist but are GUI/window commands and need an X display.
- Therefore a true Innovus GUI-native screenshot could not be produced in this headless environment without providing a display server. The practical command route is to launch Innovus GUI with a valid `DISPLAY`, source `routing.enc`, run `fit`, then capture the window with an X screenshot tool such as `xwd` or the desktop screenshot utility. For this run, a DEF-derived PNG preview was generated instead: `innovus-rundir/reports/layout_preview_routed_100mhz.png`.

### Follow-up Python-first policy, GDS stream-out, and dacs-lab branch commit

Date: 2026-05-05.

User preference recorded for future normal Lab1-style flow runs: use the Python entry points and Python manager configuration first. Generated Tcl should be treated as implementation detail. Tcl edits are reserved for debugging, emergency step recovery, or one-off diagnosis, and any Tcl-only fix that proves necessary should then be moved back into Python-managed configuration before it is treated as the normal route.

A controlled real-layout export was attempted from the completed 100 MHz routed Innovus database. Inputs used:

- Routed database: `third_party/dacs-lab/experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540/innovus-rundir/data/routing.enc`
- Layermap: `/home/lisihang/asap7/asap7_pdk_r1p7/cdslib/asap7_TechLib_10/asap7_fromAPR_08b.layermap`
- Merged ASAP7 stdcell GDS files: `/home/lisihang/asap7/asap7sc7p5t_28/GDS/asap7sc7p5t_28_{L,R,SL,SRAM}_220121a.gds`

The first `streamOut` attempt with `-units 1000` completed but warned that merged stdcell GDS files use 4000 DBU/um and that `-units 20000` avoids rounding. The second attempt used `-units 20000` and completed successfully:

- GDS: `third_party/dacs-lab/experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540/innovus-rundir/data/routing_units20000.gds`
- Stream-out report: `third_party/dacs-lab/experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540/innovus-rundir/reports/streamout_100mhz_units20000.rpt`
- KLayout-rendered GDS PNG: `third_party/dacs-lab/experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540/innovus-rundir/reports/layout_gds_klayout_100mhz.png`
- Export Tcl used for this diagnosis: `third_party/dacs-lab/experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540/innovus-rundir/scripts/export_gds_100mhz_units20000.tcl`

KLayout is available at `/usr/bin/klayout`. A normal `klayout -z` screenshot failed first because Qt could not initialize `xcb` in the headless shell. Retrying with `QT_QPA_PLATFORM=offscreen` produced the PNG above. This PNG is a direct GDS render, unlike the earlier DEF-derived preview.

Detailed clean-signoff analysis for the current PPAdder run:

1. The adder can produce a routed Innovus database, routed DEF, merged-stream GDS, post-route timing, post-route power, and post-route area reports. It can therefore produce a project-level routed-result bundle for compatibility and flow debugging.
2. It still cannot be called clean signoff. Innovus continues to report `IMPTR-2101` on M10/Pad track legality while loading the full ASAP7 1x collateral. The actual route is limited to M2-M8 and final detail-route DRC reports zero violations, but the Innovus message summary still includes the M10 issue as an error.
3. PG connectivity is still not clean: `verifyConnectivity -type special` reports 10 violations, although PG short checking reports zero shorts. The power grid script needs a proper ASAP7-compatible rail/stripe/via strategy before this can be considered clean.
4. Top-level IO handling is incomplete. The example has no explicit IO pin placement, so Innovus reports 192 unplaced top-level terms and RC extraction reports NREX warnings for many top-level input nets without driver pins.
5. No external signoff DRC/LVS engine was run. The active project plan targets Cadence Genus/Innovus validation with full ASAP7 collateral, not foundry-level Calibre/Pegasus signoff. Without signoff rule decks and an LVS/DRC-clean flow, the result should be called routed evidence, not clean signoff.
6. The remaining non-clean causes are not simply because `main.py` had not been modified. `main.py` fixes were needed for the invalid zero clock, Python-level threading, route SI/threading controls, and local ASAP7 paths. The remaining blockers are mainly tech-collateral consistency/M10 checking, incomplete IO pin placement, incomplete PG connectivity, and missing external DRC/LVS signoff.

To get closer to a true clean result for this adder within controlled scope, the next fixes should be moved into Python-managed flow generation rather than edited only in generated Tcl:

- Add Python-managed IO pin assignment after floorplan, using legal ASAP7 pin layers/tracks.
- Replace the minimal PPAdder PG script with an ASAP7-compatible rail/stripe/connect-via plan and keep `verifyConnectivity -type special` at zero violations.
- Decide how to handle the recurring M10/Pad `IMPTR-2101` full-collateral issue without silently modifying the PDK. A clean answer needs consistent tech LEF, route layer constraints, layermap, QRC, and stdcell GDS collateral.
- Add Python-managed export steps for routed DEF, GDS stream-out with `-units 20000`, routed netlist, SDF, and RC output if these are required artifacts.
- Treat external DRC/LVS as a separate dependency and scope decision, because it requires proper signoff decks/tools beyond this Lab1 compatibility run.

The `third_party/dacs-lab` repository was switched from `dacs2024_lab1` to a local branch named `thermal_placement`. Source/config changes were committed there while run artifacts were left untracked/ignored:

```text
branch: thermal_placement
commit: 4e4d8f9 Adapt Lab1 Cadence flow for local ASAP7
```

Committed files in `third_party/dacs-lab`:

- `experiment/dacs2024/lab1/env.py`
- `experiment/dacs2024/lab1/main.py`
- `manager/genus/parser/area.py`
- `manager/innovus/innovus_manager.py`
- `tech/asap7.py`

The untracked `third_party/dacs-lab/runs/` artifact directory was not committed. Lab result artifacts under `experiment/dacs2024/lab1/results/` remain tool outputs and are not part of the source commit.

### dacs-lab IO pin placement diagnostic before retry

Date: 2026-05-05.

User requested cleanup, meaningful result names, and IO pin placement validation before deciding whether to start mainline Phase 2. A first non-source diagnostic was run on the existing PPAdder routed database using `editPin -pin [all_inputs]` and `editPin -pin [all_outputs]`. The attempt failed because `all_inputs`/`all_outputs` returned Innovus collection handles such as `0x1`, while `editPin -pin` in this context expects explicit pin names or a Tcl list of pin names. Error evidence:

```text
IMPPTN-1235: Cannot find pin 0x1 on partition PPAdder
IMPPTN-963: Either specified pin name for the selected partition does not exist or has status 'cover'.
```

Next retry: generate explicit port-name lists through Innovus Tcl collection conversion or database queries, then move the validated command sequence back into Python-generated floorplan code rather than keeping it as run-directory Tcl.

### dacs-lab cleanup, meaningful result names, and IO pin placement validation

Date: 2026-05-05.

User requested cleanup of obsolete `third_party/dacs-lab` attempts, validation of IO pin placement because Gemmini requires explicit top-level pins, meaningful result directory names, and a conclusion on whether mainline Phase 2 can start.

Cleanup performed under ignored `third_party/dacs-lab`:

- Removed old hash-only Lab1 result directory `experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540`.
- Removed old backup result directory `experiment/dacs2024/lab1/results/0c1697af26c1e8faa240f24afd7513600c929411e5583f8d7d4a35d6eb0b0540_before_100mhz_20260505`.
- Removed old top-level attempt directory `third_party/dacs-lab/runs/`.
- Removed ignored Python `__pycache__` directories and stray top-level `innovus.log1` / `innovus.logv1` files after validation.

Source changes committed in the embedded `dacs-lab` repository:

```text
branch: thermal_placement
commit: 4f5d0d8 Add meaningful runs and IO pin assignment
```

Committed files:

- `experiment/dacs2024/lab1/main.py`
- `manager/innovus/innovus_manager.py`
- `tech/asap7.py`

Behavioral changes:

- Normal Lab1 flow remains Python-first through `main.py` and the manager classes.
- Default clock period is `10.0 ns` (`100 MHz`) through `TP_DACS_CLK_PERIOD_NS`, instead of the invalid zero-period target.
- Result directories now include design, bit width, ASAP7 cell family, target frequency, timestamp or explicit tag, and short design hash. The validation run used explicit tag `ppadder_sklansky_64b_asap7sc7p5t28_100mhz_iopins_20260505`.
- Innovus floorplan generation now defaults to `assignIoPins -autoBusGroup`, controlled by Python option `assign_io_pins` / environment variable `TP_DACS_ASSIGN_IO_PINS`.

Validation command:

```bash
source /home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh
cd /home/lisihang/thermal_placement/third_party/dacs-lab/experiment/dacs2024/lab1
TP_DACS_RUN_TAG=ppadder_sklansky_64b_asap7sc7p5t28_100mhz_iopins_20260505 \
TP_DACS_CLK_PERIOD_NS=10.0 \
TP_DACS_ROUTE_CPUS=1 \
TP_DACS_ROUTE_SI_AWARE=false \
timeout 2400 /home/lisihang/miniconda3/envs/thermal_placement/bin/python main.py
```

Current validation output directory:

```text
third_party/dacs-lab/experiment/dacs2024/lab1/results/ppadder_sklansky_64b_asap7sc7p5t28_100mhz_iopins_20260505
```

IO pin placement result:

- `innovus-rundir/log/fused_pnr.log` reports `Completed IO pin assignment`.
- `innovus-rundir/data/floorplan.def` has `PINS 194 ;`.
- DEF inspection shows `194` pins with `PLACED` or `FIXED` geometry.
- Innovus floorplan status reports `194 physical pins: 0 unplaced, 194 placed, 0 fixed`.
- The previous no-IO-placement issue (`192 nets have unplaced terms`) is not present in this run; RC extraction reports `0 net(s) have incomplete routes`.

Flow result:

- Genus completed normally and used `set_db max_cpus_per_server 8`; Genus log contains repeated `Number of threads: 8 * 1` records.
- Innovus completed init, floorplan, powerplan, placement, route, post-route optimization, post-route timing/power/area, and saved `routing.enc` / `routing.enc.dat`.
- Innovus used 8 local CPUs for init/place/timing stages, then the Python-controlled route workaround switched route/post-route stages to 1 CPU and SI-aware false.
- Final `result.json`: post-syn timing `832`, post-place timing `1785.5`, post-route timing `1782.899`, post-route power `9.472e-06`, post-route area `32.572`.
- Post-route timing meets the 100 MHz target: final WNS about `7.217 ns`, TNS `0.000 ns`.

Why this is still not clean signoff:

1. Routing finished but final route DRC is not zero. Innovus reports `Total number of DRC violations = 2`, both short violations on M8.
2. Full ASAP7 1x M10/Pad track checking still reports `IMPTR-2101` / `IMPTR-2104` / `IMPTR-2108` during floorplan and route. The design is constrained to M2-M8 routing, but Innovus still records M10 pitch/spacing as an error in the message summary.
3. PG connectivity remains incomplete. `verifyConnectivity -type special` reports `Verification Complete : 10 Viols`, while PG short checking reports `0 Short Viols`.
4. No external signoff DRC/LVS was run. This remains a Cadence Genus/Innovus full-ASAP7 compatibility validation, not foundry-clean signoff.

Current judgment for mainline Phase 2:

- Mainline Phase 2 development can start now. The needed preconditions for starting development are satisfied: Python-first Genus-to-Innovus flow works, result directory naming is meaningful, IO pin placement has a validated Python-managed mechanism, and non-clean blockers are documented.
- Mainline Phase 2 must not treat this PPAdder result as a clean signoff template. It should start with explicit validation gates: all top-level pins placed/fixed in DEF, no unplaced terms, route DRC trend recorded, PG connectivity checked, M10/Pad tech-collateral issue tracked, and output directories named by design/config/library/clock/run purpose.
- For Gemmini specifically, IO pin placement is not optional. The Phase 2 Gemmini flow should carry forward a Python-managed IO assignment step early in floorplan and verify the resulting DEF before placement/route-heavy runs.

GDS/PNG export follow-up in the meaningful result directory:

- First export retry command called Innovus directly without the normal shell initialization and failed before loading the design with `libicudata.so.50: cannot open shared object file`.
- Next retry uses the same environment entry style as the Lab1 managers (`source ~/.bashrc`) before launching Innovus.

- Second export retry with `source ~/.bashrc` still failed with the same missing `libicudata.so.50`, so the exported-layout retry is an environment-launch issue rather than a design database issue. Next retry will locate the missing runtime library and set `LD_LIBRARY_PATH` explicitly for this one-off export.

- Third export retry with explicit Innovus ICU library path started Innovus but failed license initialization with `LMC-01902` because the license server environment was not present. Next retry will source `tools/env_gemmini_thermal.sh` and keep the explicit library path.

- Fourth export retry entered Innovus successfully and checked out the license, but the export Tcl used the wrong relative path (`../data/routing.enc`) from `innovus-rundir`. Next retry changes the script to use `data/routing.enc`, `data/routing_iopins_units20000.gds`, and `reports/streamout_iopins_units20000.rpt`.

- Fifth export retry succeeded after sourcing `tools/env_gemmini_thermal.sh`, setting the Innovus ICU library path explicitly, and fixing result-relative paths in the Tcl. Generated artifacts in the meaningful result directory:
  - `innovus-rundir/data/routing_iopins_units20000.gds`
  - `innovus-rundir/reports/streamout_iopins_units20000.rpt`
  - `innovus-rundir/reports/layout_gds_iopins_100mhz.png`
- The PNG was rendered with `QT_QPA_PLATFORM=offscreen klayout -z`; it was opened and visually checked as nonblank, showing routed metal and placed edge IO labels.

Documentation follow-up for Phase 2 development:

- Added Python-first Stage 2 policy and dacs-lab lessons to `docs/phase0tophase4_cadence_asap7_plan.md`.
- Added Stage 2 checklist gates for Python-managed flow, meaningful result names, IO pin placement validation, and separate non-clean signoff cause recording to `docs/agent_task_checklist.md`.
- Added command-reference snippets for IO pin placement evidence and headless GDS-to-PNG layout rendering to `docs/agent_command_reference.md`.
- Updated `docs/README.md` so future agents know the command reference contains Phase 2 IO/GDS diagnostics.


## 0.6 Gemmini Phase 2 starts as run-local Python-first Cadence flow

### Decision

Date: 2026-05-05.

User confirmed that mainline Phase 2 development may start, with a fixed Gemmini timing target of `200 MHz` / `5.000 ns`. Before launching heavy Genus/Innovus work, the active run documentation and manifest were updated to remove stale OpenROAD Stage 2 assumptions and record the Cadence Python-first route.

### Current route

- Run-local Python flow directory: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/python_flow/`.
- Plan record: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/config/stage2_cadence_python_flow_plan.md`.
- Existing low-level shell/Tcl wrappers remain preflight references, but normal Gemmini Phase 2 control should go through the Python entry point and generated Tcl.

### Required gates before heavy run acceptance

- Preflight must confirm RTL filelist, `Gemmini` top, full ASAP7 NLDM cache, fake SRAM collateral, Cadence tool paths, and 5.000 ns clock constraint.
- Genus frontend/elaboration smoke should precede full synthesis.
- Innovus floorplan must prove all top-level pins are `PLACED` or `FIXED`; this carries forward the validated dacs-lab `assignIoPins -autoBusGroup` lesson.
- Non-clean causes must be recorded separately: route DRC, PG connectivity, M10/Pad collateral messages, missing SDF/SPEF/GDS, and external DRC/LVS status.


### Dry-run validation after Python flow skeleton creation

The run-local Python flow skeleton was created and validated without launching Genus/Innovus implementation:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_docstart_20260505 \
  python runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/python_flow/run_stage2_cadence.py --dry-run
```

Result: passed. The generated manifest reports `preflight_ok=True`, `200 MHz` / `5.000 ns`, 15 ASAP7 Liberty files, 5 ASAP7 LEF files, and 2/2/2 Gemmini fake SRAM Liberty/LEF/stub files. Generated Tcl and SDC were written under `physical/cadence/runs/gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_docstart_20260505/`. No heavy Cadence run was launched in this step.


## 0.7 Stage 2 Python codegen promoted from dry-run skeleton to launchable Cadence flow

Date: 2026-05-05

Before launching real Cadence work, the run-local Python flow under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/python_flow/` was extended to generate a Genus frontend smoke Tcl, Genus mapped outputs including SDF, Innovus PG connect/stripe/sroute commands, routed DEF/Verilog/SDF/SPEF, GDS streamOut with ASAP7 `asap7_fromAPR_08b.layermap`, and output-status checks.

Validation command:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_phase2_codegen_20260505   python runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/python_flow/run_stage2_cadence.py --dry-run
```

Result: passed with `preflight_ok=True`, `asap7_gds_count=4`, and a valid streamOut layer map. Next planned attempt is Genus frontend/elaboration smoke with run tag `gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_genus_elab_20260505`.


## 0.8 Genus frontend smoke passed; libcell resolution policy adjusted

Date: 2026-05-05

Genus frontend/elaboration smoke for `Gemmini` passed with run tag `gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_genus_elab_20260505`. The run read 15 ASAP7 TT NLDM Liberty files, 2 Gemmini fake SRAM Liberty files, RTL plus fake SRAM stubs, elaborated `Gemmini`, read the generated 5.000 ns SDC, and exited normally. `genus_check_design.rpt` reports no unresolved references.

Observed non-blocking warnings include fake SRAM output pins without Liberty function attributes, expected RTL unused-port/unused-register messages, and `CDFG-556` for `mem_ext`/`mem_0_ext` because library cells and user stub modules share names. The Python Tcl generator now sets `hdl_resolve_instance_with_libcell=true`; the next attempt will rerun Genus frontend smoke with run tag `gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_genus_elab_libcell_20260505` before full synthesis.


## 0.9 Genus frontend smoke rerun passed with libcell resolution attribute

Date: 2026-05-05

Run tag `gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_genus_elab_libcell_20260505` passed. The generated Tcl now sets `hdl_resolve_instance_with_libcell=true`; Genus still emits the generic `CDFG-556` warning text for `mem_ext` and `mem_0_ext`, but the message says it is linking the technology library cell. `genus_check_design.rpt` reports no unresolved references. Next attempt is full Genus synthesis with run tag `gemmini_mesh16x16_asap7sc7p5t28_fake_sram_200mhz_genus_syn_20260505`.

## 0.10 Reset deleted run-local Python flow and copied dacs-lab startup tree

Date: 2026-05-06.

The previous Gemmini Phase 2 run-local Python flow was removed after review because its structure was less clear than the dacs-lab manager-based flow and its full Genus synthesis attempt used an ambiguous SDC time unit. The Genus command itself exited normally, but the report showed ps-scale timing behavior from `create_clock -period 5.000`, so that result must not be used as a valid 200 MHz synthesis result.

Deleted paths:

- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/python_flow/`
- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/runs/`
- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/genus/`

Copied startup base:

- Source: `third_party/dacs-lab/`
- Destination: `runs/cadence_startup/`
- Adaptation analysis: deleted per 2026-05-06 user request; use the concise reset request and future confirmed plan instead.

Current judgment: continue Phase 2 by adapting the dacs-style `main.py -> GenusInnovusFlow -> GenusManager/InnovusManager -> tech/asap7.py` structure. Preserve dacs' explicit ps-based SDC generation (`set_units -time 1.0ps`, `clk_period_ps=5000.0`) and add Gemmini-specific RTL filelist parsing, fake SRAM Liberty/LEF/stubs, preflight, Genus libcell resolution, Innovus final output export, IO pin checks, and DRC/connectivity classification.

## 0.11 cadence_startup concise reset request

Date: 2026-05-06.

User requested that `runs/cadence_startup/genus.cmd`, `runs/cadence_startup/innovus.cmd`, and `runs/cadence_startup/README.md` be restored to their original copied dacs-lab content because the prior rewrite was too verbose and too Gemmini-specific for those top-level startup files. The temporary `runs/cadence_startup/THERMAL_PLACEMENT_ADAPTATION.md` report was also deleted. Active docs were adjusted to avoid pointing at that deleted report.

Next structural changes to `runs/cadence_startup` should be proposed before editing: remove/replace `design/`, create a Gemmini-specific experiment tree, and keep reusable managers/tech/utils minimal and config-driven.

## 0.12 cadence_startup Gemmini entry and physical tag root

Date: 2026-05-06.

User confirmed the dacs-style startup restructuring. The active Stage 2 output convention changed from `physical/cadence/runs/<tag>/` to `physical/<tag>/`. The copied `runs/cadence_startup` tree now uses branch `GemminiRocketConfig_collection0506`, removes the copied teaching `design/` and `experiment/` trees, and adds:

- temporary `runs/cadence_startup/GEMMINI_PHASE2_RESTRUCTURE_PLAN.md` (removed after the durable notes were moved into `runs/cadence_startup/README.md`)
- `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py`
- `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/env.py`
- `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/README.md`
- `runs/cadence_startup/tech/gemmini_asap7.py`

At this point, `manager/` was intentionally kept unchanged and recorded as the next adaptation area; this was superseded by the manager script-only adaptation recorded in section 0.14. `tech/asap7.py` now defaults to this project's `.cache/asap7/asap7sc7p5t_28/NLDM` cache when `ASAP7_LIB_CACHE` is unset, and the Gemmini tech wrapper adds fake SRAM Liberty, LEF, and Verilog stubs from `.cache/fake_sram/asap7/Gemmini`.

Lightweight validation, without launching Genus or Innovus:

```bash
source tools/env_gemmini_thermal.sh
python -m py_compile runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py runs/cadence_startup/tech/asap7.py runs/cadence_startup/tech/gemmini_asap7.py
rg -n "from design|import design" runs/cadence_startup --glob '!.git/**' --glob '!__pycache__/**'
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --dry-run
```

Result: syntax check passed; no code imports the deleted `design/` tree; preflight and dry-run passed. The preflight resolved 575 RTL files, 17 setup Liberty files including fake SRAM, 7 LEF files including fake SRAM, 2 fake SRAM Verilog stubs, 4 ASAP7 GDS files, and wrote the dry-run manifest under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_startup_20260506/startup/`.

## 0.13 cadence_startup manager script-only adaptation preflight path fix

Date: 2026-05-06.

During the `runs/cadence_startup` manager adaptation check, `main.py --preflight` initially failed because the startup entry derived the expected Python path from `THERMAL_PLACEMENT_ROOT`, producing `/home/lisihang/thermal_placement/miniconda3/envs/thermal_placement/bin/python`. The correct project conda path is `/home/lisihang/miniconda3/envs/thermal_placement/bin/python` after `source tools/env_gemmini_thermal.sh`.

Planned fix before retry: derive the expected Python from `CONDA_PREFIX` when available, falling back to `/home/lisihang/miniconda3/envs/thermal_placement/bin/python`, then rerun syntax, preflight, and manager script-only generation.

## 0.14 cadence_startup manager script-only path passed

Date: 2026-05-06.

The `runs/cadence_startup` repository now records two local rules in `AGENTS.md` and `README.md`: use the parent repository's `thermal_placement` conda environment for all Python commands, and commit every modification inside the nested startup repository before handing work back.

A concrete review showed that `manager/` adaptation is required now, not merely later, because Phase 2 must stay Python-manager-first and the copied DACS managers still launched tools through `source ~/.bashrc`, had no non-launching script-generation mode, and did not export final Innovus artifacts. The startup repository commit `bb0057f` adapts the managers and Gemmini entry as follows:

- `GenusManager` and `InnovusManager` accept `env_setup_script` and build launch commands through the parent repo environment script.
- Both managers support `runmode: script_only`, which writes Tcl/YAML but does not launch Genus or Innovus.
- `GenusManager` can emit `hdl_resolve_instance_with_libcell` for fake-SRAM library-cell resolution.
- `InnovusManager` emits IO pin assignment and routed DEF, routed Verilog, SDF, SPEF, DRC/connectivity, and GDS streamOut commands.
- `GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py` now supports `--write-scripts` to exercise this manager path.
- The temporary restructure plan file was deleted after durable information was moved into `runs/cadence_startup/README.md`.

Validation commands:

```bash
source tools/env_gemmini_thermal.sh
python -m py_compile runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py runs/cadence_startup/manager/genus/genus_manager.py runs/cadence_startup/manager/innovus/innovus_manager.py runs/cadence_startup/tech/asap7.py runs/cadence_startup/tech/gemmini_asap7.py
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-scripts
rg -n "from design|import design" runs/cadence_startup --glob '!.git/**' --glob '!__pycache__/**'
```

Result: syntax, preflight, and manager script-only generation passed under `/home/lisihang/miniconda3/envs/thermal_placement/bin/python`; no code imports the deleted `design/` tree. Generated scripts include Genus `set_units -time 1.0ps`, `set_db hdl_resolve_instance_with_libcell true`, 5.000 ns / 5000 ps clock, Innovus `assignIoPins -autoBusGroup`, and routed DEF/Verilog/SDF/SPEF/GDS export commands. No Cadence commercial tool was launched.

## 0.15 Genus full synthesis and Innovus floorplan smoke passed; non-blocking Innovus ERROR classes classified

Date: 2026-05-06.

Genus full synthesis/report passed for run tag `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_genus_syn_20260506`. The accepted outputs include mapped Verilog, SDF, setup/hold SDC, Genus DBs, and timing/QoR/power/area/DRC reports. Genus QoR reports a 5.000 ns setup clock, WNS 9.3 ps, TNS 0, and 0 violating paths.

A limited Innovus init/floorplan smoke then passed for run tag `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_innovus_floorplan_20260506`. It read the Genus mapped netlist/SDC, full ASAP7 + fake SRAM timing/LEF collateral, produced `init.enc`, `floorplan.enc`, `Gemmini.floorplan.def`, and placed all top-level pins (`1327/1327`, 0 unplaced). It did not run powerplan, placement, CTS, routing, extraction, or streamOut.

Non-blocking issues carried forward before larger Innovus runs:

- `TECHLIB-1173`: Innovus reports missing fake SRAM Liberty library-level `pulling_resistance_unit`. Current judgment: acceptable for the floorplan smoke because Innovus completed and read the macro cells, but should be fixed in `scripts/prepare_gemmini_fake_sram_collateral.py` output or explicitly waived before final route/signoff-style evidence.
- `IMPTR-2101` / `IMPTR-2104` / `IMPTR-2108`: ASAP7 M10 pitch/min-width/min-spacing track messages. Current judgment: not blocking floorplan, but route-stage work must keep M10/Pad collateral classification separate from route DRC/PG connectivity.
- `TCLCMD-1461`: Innovus skips Genus-exported `set_units` lines in setup/hold SDC. Current judgment: timing was still interpreted plausibly in pre-place timing, but SDC handoff should be cleaned or documented before larger P&R acceptance.
- `IMPREPO-*` / `IMPDB-2136`: floating top ports, floating instance terminals, tied-input terms, high-fanout nets, and fake SRAM cells marked `dont_use`. Current judgment: accepted for import/floorplan only; review before powerplan/place/CTS/route acceptance.


## 0.16 Phase 2 handoff after Genus/Innovus floorplan smoke: required fixes and remaining P&R plan

Date: 2026-05-06.

The current active Phase 2 state is now explicitly classified after reviewing the generated scripts, logs, manifests, and active run docs. No new Cadence run was launched for this handoff review.

Current completed evidence:

- Genus full synthesis/report for `Gemmini` passed at 200 MHz / `5.000 ns`; QoR reports WNS `9.3 ps`, TNS `0.0`, and `0` violating paths.
- Innovus init/floorplan smoke passed from the accepted Genus run. The floorplan DEF reports `1327/1327` top-level pins placed and `0` unplaced pins.
- The floorplan smoke did not run powerplan, placement, CTS, routing, extraction, streamOut, or post-route reports.

Required fixes before signoff-style Stage 2 acceptance:

1. Change generated Genus synthesis Tcl from bare `syn_opt` to explicit `syn_opt -logical`. The current warning is `SYNTH-33`; it is a deprecation warning, not a failure, but it should be fixed before more accepted synthesis evidence is produced.
2. Fix generated fake SRAM Liberty. Innovus reports `TECHLIB-1173` because `.cache/fake_sram/asap7/Gemmini/lib/mem_ext.lib` and `mem_0_ext.lib` omit library-level `pulling_resistance_unit`. Add that attribute and common threshold defaults in `scripts/prepare_gemmini_fake_sram_collateral.py`, regenerate the fake SRAM cache, and rerun the smallest Genus/Innovus input smoke.
3. Fix or consciously classify fake SRAM LEF signal pin directions. The current generator writes signal pins as `DIRECTION INOUT`; the generated LEF should prefer `INPUT`/`OUTPUT` based on RTL/Liberty port direction where accepted by Innovus.
4. Clean or waive Innovus SDC handoff. Innovus skips Genus-exported `set_units` with `TCLCMD-1461`; before larger P&R acceptance, either generate Innovus-clean setup/hold SDC or record a timing-unit check and waiver.
5. Keep ASAP7 M10/Pad `IMPTR-2101` / `IMPTR-2104` / `IMPTR-2108` separate from route DRC and PG connectivity. They are full-collateral consistency messages seen before routing; do not treat them as route DRC, and do not silently modify the external ASAP7 PDK.

Script status as of this review:

- `runs/cadence_startup/manager/innovus/innovus_manager.py` already contains code for `powerplan`, `placement`, `cts`, and `routing`, including routed DEF/Verilog/SDF/SPEF/GDS export commands.
- `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py` currently exposes only `--run-innovus-floorplan-smoke` for real Innovus launch. There is not yet a Python-managed entry to run the remaining Innovus stages.
- Routing currently hardcodes `setNanoRouteMode -quiet -drouteEndIteration 20`; a reduced bring-up should expose this as a Python/env knob such as `TP_STAGE2_DROUTE_END_ITERATION`.
- Existing route recovery defaults are already conservative: route CPU defaults to `1`, and SI-aware delay defaults to `false` via `TP_STAGE2_ROUTE_CPUS` and `TP_STAGE2_ROUTE_SI_AWARE`.

Remaining Stage 2 work:

- Run powerplan and verify special-net connectivity/PG shorts.
- Run placement and collect pre-CTS timing, area, and power reports.
- Run CTS and post-CTS timing.
- Run routing/post-route optimization and export routed DEF, routed Verilog, routed SDF, SPEF, and GDS.
- Record post-route timing, area, power, DRC, and connectivity reports.
- Write the Stage 2 final acceptance report before Stage 3 uses any physical/power output.

A reduced-iteration Innovus run-through is allowed as bring-up evidence if it is clearly tagged as smoke/run-through and not used as final signoff. The recommended next route is to add a Python-managed `--run-innovus-pnr-smoke` entry with reduced `drouteEndIteration`, run preflight/script checks first, then run the remaining Innovus stages from the accepted Genus output. Any failure must be documented here before changing knobs or retrying.

## 0.17 Stage 2 reduced P&R smoke entry implemented; fake SRAM generator repaired pending commercial-tool revalidation

Date: 2026-05-06.

The required pre-run fixes from section 0.16 have been partially implemented in code before launching a larger Innovus run:

- `runs/cadence_startup/manager/genus/genus_manager.py` now generates explicit `syn_opt -logical` for the current non-physical Genus synthesis route. This fixes the `SYNTH-33` deprecation warning for newly generated synthesis scripts. The accepted Genus synthesis run from earlier still used the old script; a future accepted Genus rerun should use the new command.
- `scripts/prepare_gemmini_fake_sram_collateral.py` now emits library-level `pulling_resistance_unit : "1kohm";` and common Liberty threshold attributes for generated fake SRAM Liberty. The `.cache/fake_sram/asap7/Gemmini/` cache was regenerated. This should address Innovus `TECHLIB-1173`, but it still needs confirmation in a real Innovus read/init or P&R run.
- The same fake SRAM generator now emits signal-pin LEF directions from the derived port direction (`INPUT`/`OUTPUT`) while keeping `VDD`/`VSS` PG pins as `INOUT`.
- `runs/cadence_startup/manager/innovus/innovus_manager.py` now exposes detailed-route knobs through Python config instead of hardcoding `drouteEndIteration 20`.
- `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py` now exposes `--run-innovus-pnr-smoke`, which runs Innovus `init`, `floorplan`, `powerplan`, `placement`, `cts`, and `routing` from a completed Genus synthesis run. This entry is deliberately labeled as a reduced-effort run-through smoke, not final Stage 2 signoff.

Validation completed before any larger Cadence launch:

```bash
source tools/env_gemmini_thermal.sh
python -m py_compile scripts/prepare_gemmini_fake_sram_collateral.py \
  runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py \
  runs/cadence_startup/manager/genus/genus_manager.py \
  runs/cadence_startup/manager/innovus/innovus_manager.py
python scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_pnr_smoke_codegen_20260506 \
TP_STAGE2_GENUS_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_genus_syn_20260506 \
TP_STAGE2_DROUTE_END_ITERATION=5 \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_pnr_smoke_codegen_20260506 \
TP_STAGE2_GENUS_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_genus_syn_20260506 \
TP_STAGE2_DROUTE_END_ITERATION=5 \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-scripts
```

Result: syntax, fake SRAM regeneration, preflight, and non-commercial script generation all passed. Generated evidence confirms `syn_opt -logical` in `genus/scripts/fused_syn.tcl`, `setNanoRouteMode -quiet -drouteEndIteration 5` in `innovus/scripts/routing.tcl`, regenerated fake SRAM Liberty includes `pulling_resistance_unit`, and regenerated fake SRAM LEF uses signal `INPUT`/`OUTPUT` directions.

Planned reduced P&R smoke command:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_innovus_pnr_smoke_droute5_20260506 \
TP_STAGE2_GENUS_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_genus_syn_20260506 \
TP_STAGE2_DROUTE_END_ITERATION=5 \
TP_STAGE2_ROUTE_CPUS=1 \
TP_STAGE2_ROUTE_SI_AWARE=false \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-pnr-smoke
```

Acceptance limit: this run can expose remaining powerplan/place/CTS/route/export blockers and check whether the fake SRAM Liberty repair removes `TECHLIB-1173`. It is not final Stage 2 signoff because routing effort is intentionally reduced and the post-route DRC/connectivity/timing/artifact reports still need classification.

## 0.18 Reduced P&R smoke first launch stopped in powerplan; sparse PG smoke knob added

Date: 2026-05-06.

Run tag `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_innovus_pnr_smoke_droute5_20260506` was launched with `TP_STAGE2_DROUTE_END_ITERATION=5`. It passed Innovus `init` and `floorplan` again, with the regenerated fake SRAM Liberty read successfully and no recurrence of `TECHLIB-1173` in the observed init/floorplan output. The flow was then stopped manually during `powerplan` after about 6.5 minutes in `addStripe` via generation.

Failure evidence:

- `innovus/log/powerplan.log` ended in M8/M9 stripe via generation with repeated `IMPPP-4500` runtime warnings.
- The default ASAP7 startup PG settings used `stripe_distance=0.4um` on a roughly `574um x 574um` die, creating about 1430 vertical stripes and 1430 horizontal stripes. That is too dense for a bring-up smoke and creates an excessive M8/M9 via-generation workload.
- `IMPPP-354` and `IMPPP-385` also indicate the current stripe width/spacing/distance choices are not clean for the loaded ASAP7 constraints.
- This stopped attempt did not reach placement, CTS, routing, extraction/export, or post-route reports.

Implemented fix for the next smoke:

- `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py` now lets PG stripe and sroute settings be overridden through `TP_STAGE2_STRIPE_WIDTH`, `TP_STAGE2_STRIPE_SPACING`, `TP_STAGE2_STRIPE_DISTANCE`, `TP_STAGE2_SROUTE_MIN_LAYER`, and `TP_STAGE2_SROUTE_MAX_LAYER`.
- The `--run-innovus-pnr-smoke` path defaults `TP_STAGE2_STRIPE_DISTANCE` behavior to a sparse `20.0um` unless overridden, while the base full-flow tech default remains available.
- Script-only validation with `TP_STAGE2_STRIPE_DISTANCE=20.0` generated `powerplan.tcl` containing `set stripe_distance 20.000000`, `routing.tcl` containing `drouteEndIteration 5`, and Genus `fused_syn.tcl` containing `syn_opt -logical`.
- Nested `runs/cadence_startup` commits: `8e01c45` for the reduced PNR smoke controls and `7d00fec` for sparse PG smoke knobs.

Next retry should use a new run tag, for example:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_innovus_pnr_smoke_droute5_sparsepg20_20260506 TP_STAGE2_GENUS_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_genus_syn_20260506 TP_STAGE2_DROUTE_END_ITERATION=5 TP_STAGE2_STRIPE_DISTANCE=20.0 TP_STAGE2_ROUTE_CPUS=1 TP_STAGE2_ROUTE_SI_AWARE=false   python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-pnr-smoke
```

Acceptance limit remains unchanged: this is still a run-through smoke only. The sparse PG grid is a bring-up setting to expose later flow blockers, not final power integrity or signoff-quality PG planning.

## 0.19 Sparse-PG reduced P&R smoke reached placement; CTS blocked by PODv2 command

Date: 2026-05-06.

Run tag `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_innovus_pnr_smoke_droute5_sparsepg20_20260506` was launched after the dense-PG stop, using `TP_STAGE2_DROUTE_END_ITERATION=5`, `TP_STAGE2_STRIPE_DISTANCE=20.0`, `TP_STAGE2_ROUTE_CPUS=1`, and `TP_STAGE2_ROUTE_SI_AWARE=false`. This is still a reduced run-through smoke, not final Stage 2 signoff.

Result so far:

- Innovus `init`, `floorplan`, `powerplan`, and `placement` completed and produced `init.enc`, `floorplan.enc`, `powerplan.enc`, and `placement.enc`.
- Sparse PG avoided the previous dense stripe explosion. `addStripe` created 58 M8 wires and 58 M9 wires; `sroute` completed.
- `verify_PG_short` reported 0 PG shorts, but `verifyConnectivity -type special` reported 539 VDD/VSS special-wire opens. This is a real follow-up item before acceptance, even though it did not block the smoke.
- The regenerated fake SRAM Liberty was read without the earlier `TECHLIB-1173` missing `pulling_resistance_unit` warning in the observed new Innovus logs. The fake SRAM generator repair is therefore revalidated for Innovus import, while SRAM macro placement/PG details still need work.
- Placement ran for about 1 hour 16 minutes. The early placement timing was very negative (`WNS -18.778 ns`, `TNS -79423.3 ns`), then `place_opt_design` improved the reported final setup picture to near-zero/clean slack in the placement log. This shows normal placement timing optimization is active, but current smoke knobs do not meaningfully cap placement runtime.

Blocking failure:

- CTS failed immediately at `ccopt_design -cts` with `IMPCCOPT-2440`: the input database is PODv2 and Innovus asks to use `clock_opt_design`. The follow-on `IMPSYT-6692` is the script abort caused by that command failure.
- No `cts.enc`, `routing.enc`, routed DEF, routed Verilog, routed SDF, SPEF, GDS, post-route timing, post-route area, post-route power, post-route DRC, or post-route connectivity report was generated.

Required next script fixes before retry:

1. Change generated CTS Tcl to use a config/env-controlled command, defaulting to `clock_opt_design` for this Innovus PODv2 flow. Keep an override available for older flows if needed.
2. Add a Python-managed resume path that can source existing `placement.enc` and run only `cts` and `routing`, so the next test does not rerun the 1+ hour placement step.
3. Document any retry result before changing further route, CTS, or PG knobs.


Script repair prepared after the failure:

- `InnovusManager.generate_cts_code()` now defaults to `clock_opt_design` through `TP_STAGE2_CTS_COMMAND` / `cts_command`, with override support.
- `InnovusManager.run_impl()` now supports `start_prev_checkpoint`, allowing a selected step list to source an earlier checkpoint.
- `main.py` now exposes `--run-innovus-cts-route-smoke`, which requires the selected run tag to already contain `innovus/data/placement.enc` and then runs only `cts` and `routing`.
- Script-only validation regenerated `cts.tcl` with `source .../placement.enc` and `clock_opt_design`, and `routing.tcl` still contains `drouteEndIteration 5`.

Remaining known follow-up items after the CTS command repair:

- PG special-wire opens: 539 VDD/VSS opens after sparse `sroute`; final flow needs better macro/rail/stripe connection strategy.
- Fake SRAM macro placement: placement warns that six fake SRAM macro instances are not within the core boundary. Final floorplan needs explicit macro placement or a larger/better floorplan.
- ASAP7 M10 `IMPTR-2101` remains a technology-collateral consistency message to classify separately from route DRC.
- Innovus SDC `TCLCMD-1461` on `set_units` remains open for clean handoff or waiver.
- Placement runtime is too high for repeated smoke iteration; add stronger skip/resume/debug controls rather than relying only on low placement effort settings.

## 0.20 Reduced P&R smoke stopped after partial CTS resume; full Phase 2 preparation gate

Date: 2026-05-11.

User direction: stop further smoke attempts and prepare documentation for starting the full Phase 2 flow. A process check on 2026-05-11 found no active `innovus`, `genus`, or `cadence_startup` implementation process. The last smoke artifact is therefore treated as interrupted, not still running.

Final smoke state to carry forward:

- Accepted Genus baseline remains `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_genus_syn_20260506`. It produced mapped netlist, SDC/SDF, DB, and reports. QoR reports `setup_view` clock period `5000.0 ps`, WNS `9.3 ps`, TNS `0.0`, and 0 violating paths.
- The old accepted Genus run still contains the bare `syn_opt` deprecation warning (`SYNTH-33`). The startup script has already been changed to emit `syn_opt -logical`, but the accepted Genus evidence has not yet been rerun with that repaired script.
- `timing_in_to_out.rpt` says `No paths found`; this came from the extra input-to-output timing report and should be classified as an interface/constraint coverage warning, not as Genus synthesis failure.
- Innovus floorplan smoke passed with `Gemmini.floorplan.def` containing 1327/1327 top-level pins placed and 0 unplaced pins.
- Dense-PG reduced P&R smoke was manually stopped in `powerplan` because `stripe_distance=0.4um` created an excessive M8/M9 stripe/via workload and repeated `IMPPP-4500` warnings.
- Sparse-PG reduced P&R smoke reached `placement.enc`. It generated `init.enc`, `floorplan.enc`, `powerplan.enc`, `placement.enc`, `prePlace_timing`, `preCTS_timing`, `preCTS_area.rpt`, and `preCTS_power.rpt`.
- Sparse-PG powerplan is not acceptance-clean: `verify_PG_short` reports 0 shorts, but `verifyConnectivity -type special` reports 539 VDD/VSS special-wire opens.
- Placement is not acceptance-clean: six fake SRAM macro instances are reported as not placed within the core boundary.
- The first CTS attempt failed at `ccopt_design -cts` with `IMPCCOPT-2440` because the Innovus input DB is PODv2 and the flow must use `clock_opt_design`.
- The script repair for CTS was implemented in `runs/cadence_startup` commit `73d1da7`: generated CTS now defaults to `clock_opt_design`, and `--run-innovus-cts-route-smoke` can resume from `placement.enc`.
- The CTS resume confirmed that `clock_opt_design` fixes the immediate PODv2 command blocker and completed the main CTS phase, but the run was interrupted before saving `cts.enc` or starting/finishing the normal routing/export step. Only `placement.enc` exists; no `cts.enc`, `routing.enc`, routed DEF/Verilog/SDF/SPEF/GDS, or post-route reports exist.
- The partial CTS resume exposed quality/configuration issues: clock route detail routing still had 4874 DRC violations after 20 iterations, CTS reported 96 remaining clock slew violations, skew target was not met (`24.5 ps` achieved versus `19.2 ps` target), and CTS/NanoRoute layer settings were inconsistent (`IMPCCOPT-5067`, `IMPCCOPT-1361`, `IMPPSP-1102`) because preferred M8-M9 clock routing was outside the configured route range M2-M8.
- The same Innovus logs continue to show ASAP7 M10 track pitch/min-width/min-spacing messages (`IMPTR-2101`, `IMPTR-2104`, `IMPTR-2108`). Treat these as ASAP7 technology-collateral classification items, not as routed-design DRC.

Must fix before an accepted full Phase 2 run:

1. Regenerate and rerun Genus from the repaired startup script so the accepted synthesis evidence uses `syn_opt -logical` and no longer depends on the deprecated bare `syn_opt` behavior.
2. Keep the repaired fake SRAM Liberty/LEF generator output as the baseline. `pulling_resistance_unit` and signal-pin direction fixes are already implemented and revalidated by Innovus import, but full Phase 2 still needs SRAM macro placement and PG connectivity handling.
3. Replace smoke-only sparse PG assumptions with a deliberate Phase 2 PG/floorplan strategy: explicit macro placement or core/floorplan adjustment, stdcell rail/stripe/sroute settings that eliminate special-net opens, and documented PG checks.
4. Align CTS route-layer/NDR settings with NanoRoute route limits before full CTS: either allow the intended top clock layer consistently or keep CTS route types inside the M2-M8 route range. Do not silently pull M10 into the route stack until the M10 ASAP7 collateral messages are classified.
5. Classify or repair the Innovus SDC handoff warning on `set_units` (`TCLCMD-1461`) so full-flow timing reports are cleanly explainable.
6. Add full-flow artifact gates to the Python entry: fail or mark incomplete unless `cts.enc`, `routing.enc`, routed DEF, routed Verilog, routed SDF, SPEF, GDS, post-route timing/area/power, route/DRC, and connectivity reports are all present.
7. Treat `timing_in_to_out.rpt` / `TIM-11` as a constraints-interface review item. Decide whether the design intentionally has no input-to-output paths or whether IO delay/path groups need clearer reporting.

Recommended script/process improvements before launching the full run:

- Add an explicit `--run-innovus-full` or equivalent non-smoke entry with full-effort defaults separated from `--run-innovus-pnr-smoke` and `--run-innovus-cts-route-smoke`.
- Add a pre-launch config summary that prints clock period, route layer range, CTS route type, PG stripe settings, macro placement policy, route CPU/SI settings, and artifact gates.
- Add a post-step manifest writer after every Innovus stage so interrupted runs can be classified from files without relying on terminal history.
- Keep smoke knobs (`drouteEndIteration=5`, sparse PG, `route_cpu=1`, `route_si_aware=false`) available only as diagnostic overrides; do not use them as final Phase 2 defaults.
- For repeated debug, resume from checkpoints. For accepted full Phase 2 evidence, start from a clean semantic run tag after the required fixes are in place.

## 0.21 Phase 2 attempt artifacts deleted from runs

Date: 2026-05-11.

Per user request, Phase 2 attempt-stage files under `runs/` were cleaned after the smoke stop review. Deleted scope:

- All generated Phase 2 run-tag directories under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/`, including codegen, Genus elaboration/synthesis, Innovus floorplan, dense-PG smoke, sparse-PG smoke, and partial CTS resume artifacts.
- Run-local Phase 2 attempt reports under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/config/`: `stage2_cadence_asap7_migration_preflight.md` and `stage2_cadence_python_flow_plan.md`.

Preserved scope:

- Stage 0/1 run inputs and evidence under `rtl/`, `workloads/`, `sim/`, `activity/`, and workload reports.
- `runs/cadence_startup/` source scripts, because this is the Phase 2 startup codebase rather than a generated attempt artifact.
- Repository-level documentation of the Phase 2 smoke findings in this issue log, `docs/README.md`, and `docs/agent_command_reference.md`.

Current consequence: no Genus/Innovus generated Stage 2 artifact remains under `runs/.../physical/`. A future accepted full Phase 2 run must regenerate Genus and Innovus outputs from a clean semantic run tag.

## 0.22 Phase 2 full-flow Python gates implemented; commercial run not launched

Date: 2026-05-11.

Per user confirmation, the next Phase 2 route remains Python-manager-first and keeps `runs/cadence_startup` as a nested Git repository. The top-level repository still does not track the whole startup tree.

Implemented script changes in the nested startup repository before launching any full Cadence run:

- Added non-smoke `--run-innovus-full` to `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py`.
- Added `prelaunch_config_summary.json` generation with clock, route layers, CTS/NDR layers, PG settings, macro placement policy, thread settings, clean-output policy, and artifact gates.
- Added clean launch checks for real Genus/Innovus runs: real launches refuse non-empty `data/` or `log/` areas unless `TP_STAGE2_ALLOW_EXISTING_RUN=1` is set.
- Added full-flow artifact gates requiring `cts.enc`, `routing.enc`, routed DEF, routed Verilog, routed SDF, SPEF, GDS, and post-route timing/area/power/DRC/connectivity reports.
- Added per-step Innovus JSON manifests under `innovus/reports/<step>_manifest.json` after each real Innovus step, including expected artifact status and failure classification.
- Added explicit fake SRAM macro placement in generated floorplan Tcl: collect `mem_ext` / `mem_0_ext` instances, require 6 instances, place them in a fixed grid, and emit `floorplan_macro_placement.rpt`; Python also has DEF parsing support for macro-status evidence after floorplan.
- Changed acceptance PG behavior so generated full-flow powerplan Tcl uses `sroute -connect { corePin blockPin }` and fails if `verifyConnectivity -type special` does not report `0 Viols`. Smoke paths keep `require_pg_clean=false`.
- Kept route stack at `M2-M8`; CTS NDR now uses `M2-M8` and `create_route_type` sets top preferred layer to M8 and bottom preferred layer to M2. M10 IMPTR messages remain technology-collateral classification items, not a workaround route layer.
- Added Innovus-clean SDC handoff: Genus still writes raw SDC, then writes `constraint_setup_innovus.sdc` and `constraint_hold_innovus.sdc` with `set_units` filtered and a timing-unit evidence comment preserving `5000 ps = 5.000 ns = 200 MHz`.

Validation run before any commercial full flow:

```bash
source tools/env_gemmini_thermal.sh
python -m py_compile runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py \
  runs/cadence_startup/manager/genus/genus_manager.py \
  runs/cadence_startup/manager/innovus/innovus_manager.py \
  runs/cadence_startup/tech/asap7.py \
  runs/cadence_startup/tech/gemmini_asap7.py
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_full_codegen_20260511 \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python scripts/prepare_asap7_liberty_cache.py --check-only
python scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_full_codegen_20260511 \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-scripts
```

Result: all checks passed. Script-only generation wrote full-flow Tcl and manifests under:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_full_codegen_20260511/
```

Generated Tcl evidence checked:

- `genus/scripts/fused_syn.tcl` contains `syn_opt -logical` and writes Innovus-clean SDC files.
- `innovus/scripts/floorplan.tcl` contains `assignIoPins -autoBusGroup`, explicit fake SRAM macro collection, expected macro count `6`, `placeInstance`, and halo attempt/reporting.
- `innovus/scripts/powerplan.tcl` uses stripe distance `10.0`, connects `{ corePin blockPin }`, and has a required `0 Viols` PG special-connectivity gate.
- `innovus/scripts/cts.tcl` uses `clock_opt_design` and CTS NDR `M2-M8`.
- `innovus/scripts/routing.tcl` sets routing range `M2-M8`, keeps `drouteEndIteration 20`, and exports routed DEF, routed Verilog, SDF, SPEF, DRC/connectivity reports, and GDS.

Planned real full run tag after user confirmation:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r1
```

Do not start the real Genus/Innovus full flow until the user confirms the generated content and planned run tag.



## 0.23 Phase 2 full Genus r1 blocked by missing syn_opt -logical license

Date: 2026-05-11.

Attempted real Phase 2 Genus synthesis after script-only validation, using run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r1
```

Command class:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r1 \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-genus-syn
```

Observed progress before failure:

- Genus launched from the `thermal_placement` environment and checked out the normal `Genus_Synthesis` license.
- Full ASAP7 Liberty/LEF read completed.
- Gemmini elaboration completed with no unresolved references and the fake SRAM instances linked to library cells.
- `syn_generic` completed successfully (`SYNTH-2`) with PBS generic optimization.
- `syn_map` completed successfully (`SYNTH-5`) with PBS mapping; no mapped netlist was exported because the next `syn_opt -logical` command failed before writeout.

Failure evidence from `genus/log/syn.log`:

```text
@file(syn.tcl) 167: syn_opt -logical
Checking out license: GEN_ENG100
License 'GEN_ENG100' (version: 1.0) checkout failed.
Warning : Limited access feature unavailable. [LIC-5]
        : Limited access feature 'syn_opt_logical' is unavailable.
Use of 'syn_opt -logical' requires a GEN_ENG100 license.
```

Run consequence:

- The Python manager raised `utils.exceptions.RoutineCheckError` after Genus exited abnormally.
- `genus/data/` and `genus/reports/` remain empty for this run tag.
- Innovus full flow was not launched because there is no accepted mapped Verilog/SDC/SDF handoff.

Classification and current judgment:

- This is an external Cadence license blocker for the active accepted synthesis route, not an RTL, ASAP7, fake SRAM, timing constraint, or Python flow bug.
- The previous issue-log requirement to use `syn_opt -logical` was honored by the generated Tcl, but this environment cannot execute it without the limited-access `GEN_ENG100` feature.
- Falling back to bare `syn_opt` would avoid the immediate license check, but it would reintroduce the old `SYNTH-33` deprecated-command condition and would not satisfy the currently confirmed accepted Phase 2 synthesis requirement.

Required resolution before accepted Phase 2 can continue:

1. Provide/enable the Cadence `GEN_ENG100` license feature required by `syn_opt -logical`, then rerun from a clean run tag.
2. Or explicitly change the accepted synthesis requirement to allow a different Genus optimization command; that would be a plan/route change and must be documented before retry.


## 0.24 Local syn_opt license probe for Phase 2 route selection

Date: 2026-05-11.

After the r1 full Genus run failed at `syn_opt -logical`, a non-polluting local probe was run entirely under `/tmp/tp_synopt_license_probe.tI9CDi`. The probe used a tiny SystemVerilog design, a minimal ASAP7 RVT Liberty/LEF setup, and did not write source files or new run directories in the repository. Existing top-level `git status` changes remained limited to active docs and the preserved r1 failure evidence directory.

Probe purpose:

- Confirm which `syn_opt` variants are accepted by Genus 23.14.
- Confirm which variants require additional Cadence license features in the local installation.
- Avoid changing the active Phase 2 route before selecting an accepted synthesis policy.

Observed command behavior:

| command | probe result | license evidence | notes |
| --- | --- | --- | --- |
| `syn_opt` | passed | `Genus_Synthesis` only | Generated mapped HDL; emitted `SYNTH-33` deprecation warning. |
| `syn_opt -logical` | failed | tried and failed to checkout `GEN_ENG100` | Same blocker as full Gemmini r1. |
| `syn_opt -logical -spatial` | failed | tried and failed to checkout `GEN_ENG100` | Fails before any useful spatial route because it includes `-logical`. |
| `syn_opt -spatial` | passed after physical setup | checked out `Genus_Physical_Opt`; Innovus service reported extra `Genus_Physical_Opt` and `Innovus_3nm_Opt` | Requires physical/iSpatial setup and changes synthesis route character. |

Key probe evidence:

- Bare `syn_opt` completed with `rc=0`, `mapped_hdl=yes`, and `SYNTH-33: The selected flow setting will be removed in a future release`.
- `syn_opt -logical` failed with `Use of 'syn_opt -logical' requires a GEN_ENG100 license`.
- `syn_opt -spatial` initially failed without a floorplan/QRC/physical setup, then completed after using ASAP7 QRC, a tiny floorplan, `syn_generic -physical`, `syn_map -physical`, and `syn_opt -spatial`.
- The successful spatial probe log showed `Checking out license: Genus_Physical_Opt`, then launched Cadence Innovus as a service and reported extra licenses `Genus_Physical_Opt` and `Innovus_3nm_Opt`.

Current route-selection implication:

- If the accepted Phase 2 route must avoid `SYNTH-33`, `GEN_ENG100` is still required for `syn_opt -logical`.
- If `SYNTH-33` can be classified as a non-fatal Cadence deprecation warning, bare `syn_opt` is the smallest synthesis-route adjustment and keeps the flow closest to the previous successful Genus handoff style.
- `syn_opt -spatial` is locally licensed, but it is not a drop-in replacement for logical-only optimization. It moves Genus into an iSpatial/physical-aware synthesis flow, requires physical setup before synthesis, and should be treated as a larger route change.


## 0.25 Phase 2 synthesis policy changed to bare syn_opt compatibility route

Date: 2026-05-11.

User decision for subsequent Phase 2 development: use Genus `syn_opt` without arguments instead of `syn_opt -logical`. This is a deliberate compatibility route for the current local Cadence license set.

Rationale:

- Local probe in `/tmp/tp_synopt_license_probe.tI9CDi` showed bare `syn_opt` completes with the normal `Genus_Synthesis` license.
- `syn_opt -logical` and `syn_opt -logical -spatial` require the unavailable limited-access `GEN_ENG100` feature.
- `syn_opt -spatial` is locally licensed but changes the route to iSpatial/physical-aware synthesis and is not selected for the next Phase 2 attempt.

Acceptance classification update:

- `SYNTH-33` from bare `syn_opt` is now classified as a non-fatal Cadence deprecation warning for the current Phase 2 compatibility route.
- The warning must still be captured in Genus logs/reports and listed in issue classification, but it no longer blocks accepted Phase 2 if required synthesis, Innovus, and final artifact gates pass.
- If `GEN_ENG100` becomes available later, `syn_opt -logical` can be reconsidered as a cleaner no-deprecation logical optimization route.

Resume judgment for r1:

- The failed r1 run completed `syn_map` but failed before normal Genus writeout.
- Current r1 `genus/data/` and `genus/reports/` are empty.
- The only mapped-like intermediate files are formal-verification artifacts under `genus/fv/Gemmini/`, including `fv_map.v.gz`; these are not the active Genus handoff bundle and do not include the required mapped Verilog/SDC/SDF/reports produced by the manager gates.
- No Genus `write_db`, snapshot, or post-map checkpoint was written before the process exited.

Conclusion: do not resume accepted Phase 2 from the r1 post-map state. Regenerate scripts with bare `syn_opt` and rerun Genus synthesis from a clean semantic run tag. A future flow improvement may add an explicit post-`syn_map` checkpoint for debug resumes, but accepted evidence should still come from a clean rerun after route changes.


## 0.26 Physical attempt directories cleaned and bare syn_opt script update prepared

Date: 2026-05-11.

Per user request, generated files under the active Stage 2 physical run path were cleaned after documenting the r1 failure and route decision:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/
```

Deleted contents included the earlier script-only codegen directory and the r1 failed Genus attempt directory. The failure evidence and route decision are retained in this issue log instead of relying on generated run artifacts.

Nested startup script update prepared:

- `GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py` now sets `syn_opt_mode` to an empty string for the selected Phase 2 compatibility route, so generated Genus Tcl emits bare `syn_opt`.
- `manager/genus/genus_manager.py` no longer treats an empty `syn_opt_mode` as a request to default to `logical`; only a missing key may default from physical-flow settings.
- Prelaunch summaries now include the Genus synthesis policy and explicitly state that `SYNTH-33` is a non-fatal Cadence deprecation warning for this route.

Validation performed after the script edit:

```bash
source tools/env_gemmini_thermal.sh
python -m py_compile \
  runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py \
  runs/cadence_startup/manager/genus/genus_manager.py
```

Result: syntax check passed. No full Genus or Innovus rerun was launched.


## 0.27 Phase 2 r2 Innovus full blocked at floorplan macro coreBox parsing

Date: 2026-05-11.

After switching the selected synthesis policy to bare `syn_opt`, the r2 Genus synthesis/report run completed successfully under:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt
```

Genus r2 produced mapped Verilog, SDF, raw SDC, Innovus-clean SDC, `syn.db`, `report.db`, and timing/area/power/DRC/QoR reports. The expected `SYNTH-33` deprecation warning appears once and remains classified as non-fatal for this compatibility route. The known Genus input-to-output timing query still reports `No paths found` / `TIM-11` and remains a classification item.

The subsequent `--run-innovus-full` launch completed Innovus init and failed during the floorplan step before any accepted floorplan checkpoint was written. Evidence:

```text
innovus/log/floorplan.log
**ERROR: (IMPSYT-6693): Error message: .../innovus/scripts/floorplan.tcl: can't use empty string as operand of "-".
```

Generated floorplan report evidence before the abort:

```text
floorplan_macro_placement.rpt
macro_count=6
```

Classification and judgment:

- This is a Python-generated Tcl bug in explicit fake SRAM macro placement, not a Genus handoff, SDC, fake SRAM collateral, PG, CTS, or routing failure.
- Root cause: `dbGet top.fPlan.coreBox` is returned by Innovus as a nested box form for this database, while the generated Tcl treated it as a flat four-number list. `tp_urx` / `tp_ury` became empty and the slot-size expression failed.
- Innovus also reports the recurring ASAP7 M10 `IMPTR-2101`/`IMPTR-2104`/`IMPTR-2108` messages during floorplan load; these remain technology-collateral classification messages and are not the immediate abort cause.
- The r2 Innovus directory is not accepted Phase 2 evidence because `floorplan.enc` and `Gemmini.floorplan.def` were not written.

Next step before retry:

- Update the Python Innovus Tcl generator to parse `top.fPlan.coreBox` robustly for both flat and nested box forms.
- Run `py_compile` and `--write-scripts` to verify generated Tcl.
- Retry Innovus from a clean retry tag using the accepted r2 Genus handoff; do not rerun Genus unless the handoff itself changes.

## 0.28 Phase 2 r3 Innovus retry prepared with coreBox parser fix

Date: 2026-05-11.

After the r2 Innovus floorplan abort, the nested startup repo was updated and committed as:

```text
44a27fd Fix fake SRAM macro core box parsing
```

Change summary:

- `manager/innovus/innovus_manager.py` now parses `dbGet top.fPlan.coreBox` in both nested two-point and flat four-number forms.
- The generated fake SRAM macro placement report now records the resolved `core_box` before slot-size calculation.
- This keeps explicit fake SRAM macro placement in the Python-generated Innovus flow and does not introduce a Tcl-only workaround.

Validation before retry:

```bash
source tools/env_gemmini_thermal.sh
/home/lisihang/miniconda3/envs/thermal_placement/bin/python -m py_compile \
  runs/cadence_startup/manager/innovus/innovus_manager.py
git -C runs/cadence_startup diff --check
```

Result: both checks passed.

Next retry route:

- Innovus output run tag: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r3_floorplan_corebox_fix`.
- Genus handoff source remains accepted r2 Genus: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt`.
- Genus will not be rerun unless the mapped netlist, SDC, SDF, or report handoff changes.
- r3 acceptance still requires explicit 6/6 fake SRAM macros inside core, PG special connectivity 0 opens, M2-M8 CTS/routing consistency, and all final artifact gates.

## 0.29 Phase 2 r3 Innovus retry still blocked by single-list coreBox form

Date: 2026-05-11.

The r3 Innovus full retry used the committed fake SRAM macro placement parser fix and the r2 Genus handoff:

```text
Innovus tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r3_floorplan_corebox_fix
Genus handoff: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt
```

Observed result:

- Innovus init completed and wrote `innovus/data/init.enc`.
- Init read the r2 mapped netlist and Innovus-clean SDC successfully.
- Pre-place timing had WNS 0.979 ns / TNS 0.000 ns at the 5.000 ns clock target.
- Floorplan still failed before `floorplan.enc` and `Gemmini.floorplan.def` were written.

Abort evidence:

```text
innovus/log/floorplan.log
**ERROR: (IMPSYT-6693): ... unexpected coreBox format for fake SRAM macro placement: '{1.008 1.008 572.904 572.868}'.
```

Classification and judgment:

- This remains a Python-generated Tcl robustness bug in explicit fake SRAM macro placement.
- The r3 parser handled a nested two-point list and a flat four-number list, but Innovus returned a single braced Tcl list containing four coordinates.
- The fix should normalize `dbGet top.fPlan.coreBox` through Tcl list flattening before checking for four coordinates.
- ASAP7 M10 `IMPTR-2101`/`IMPTR-2104`/`IMPTR-2108` messages still appear during floorplan restore/track extraction; these remain technology-collateral classification messages, not the immediate abort cause.

Next retry route:

- Update the Python Innovus Tcl generator to flatten `top.fPlan.coreBox` before coordinate extraction.
- Run syntax/script generation checks.
- Retry Innovus from a new clean run tag using the same accepted r2 Genus handoff.

## 0.30 Phase 2 r4 Innovus retry prepared with flattened coreBox parser

Date: 2026-05-11.

After the r3 single-list `coreBox` failure, the nested startup repo was updated and committed as:

```text
78c7c15 Normalize Innovus core box Tcl list
```

Change summary:

- `manager/innovus/innovus_manager.py` now emits Tcl that records `tp_core_box_raw`, flattens it with `concat {*}$tp_core_box_raw`, and then extracts the first four coordinates.
- The diagnostic error now prints both raw and flattened forms if fewer than four coordinates remain.
- The change remains Python-first and only updates generated Innovus Tcl logic.

Validation before retry:

```bash
source tools/env_gemmini_thermal.sh
/home/lisihang/miniconda3/envs/thermal_placement/bin/python -m py_compile \
  runs/cadence_startup/manager/innovus/innovus_manager.py
git -C runs/cadence_startup diff --check
```

Result: both checks passed.

Next retry route:

- Innovus output run tag: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r4_corebox_flatten`.
- Genus handoff source remains accepted r2 Genus: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt`.
- Acceptance gates remain unchanged: explicit 6/6 fake SRAM macros inside core, PG special connectivity 0 opens, M2-M8 CTS/routing consistency, and final routed DEF/Verilog/SDF/SPEF/GDS/checkpoint/report artifacts.

## 0.31 Phase 2 r4 blocked at PG special-connectivity gate

Date: 2026-05-11.

The r4 Innovus retry used the flattened coreBox parser and the accepted r2 Genus handoff:

```text
Innovus tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r4_corebox_flatten
Genus handoff: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt
```

Observed result:

- Innovus init completed and wrote `innovus/data/init.enc`.
- Floorplan completed and wrote `innovus/data/floorplan.enc` plus `innovus/data/Gemmini.floorplan.def`.
- Explicit fake SRAM macro placement evidence was written in `innovus/reports/floorplan_macro_placement.rpt`: `macro_count=6`, core box `1.008 1.008 572.904 572.868`, six fixed macro instances, and `halo_status=applied`.
- Powerplan failed at the acceptance gate because PG special connectivity was not clean.

PG evidence:

```text
innovus/reports/powerplan_connectivity.rpt
Net VDD: has special routes with opens.
Net VSS: has special routes with opens.
Verification Complete : 1000 Viols.  0 Wrngs.

innovus/reports/powerplan_PG_short.rpt
Verification Complete : 0 Short Viols.
```

Classification and judgment:

- This is an acceptance-blocking PG connectivity failure. Per current Phase 2 policy, the run cannot be accepted or continue to final signoff artifacts unless `verifyConnectivity -type special` reaches 0 opens.
- The previous macro placement bug is resolved for r4.
- The recurring ASAP7 M10 `IMPTR-*` messages remain technology-collateral classification messages and are not the PG gate cause.
- The generated powerplan currently uses `sroute -connect { corePin blockPin }` with `-corePinTarget { None }`. Local Innovus documentation states that `-corePinTarget` controls the extension target for followpins; using `stripe` is the next acceptance-oriented route to connect followpin rails to the M8/M9 stripe grid instead of leaving rail pieces isolated.

Next retry route:

- Update Python-generated powerplan Tcl to target stripes for core pins and block pins during `sroute`.
- Keep M2-M8 route/CTS policy unchanged and keep PG clean gate enabled.
- Run syntax/script generation checks and retry Innovus from a new clean tag using the same r2 Genus handoff.

## 0.32 Phase 2 r5 Innovus retry prepared with stripe-targeted sroute

Date: 2026-05-11.

After the r4 PG special-connectivity failure, the nested startup repo was updated and committed as:

```text
41aa681 Target stripes for Innovus PG sroute
```

Change summary:

- ASAP7 defaults now include `sroute_core_pin_target=stripe` and `sroute_block_pin_target=stripe`.
- The Gemmini entry accepts environment overrides `TP_STAGE2_SROUTE_CORE_PIN_TARGET` and `TP_STAGE2_SROUTE_BLOCK_PIN_TARGET` and records both values in the prelaunch config summary.
- The Python-generated Innovus powerplan Tcl now emits `-corePinTarget $sroute_core_pin_target` and `-blockPinTarget $sroute_block_pin_target` for `sroute -connect { corePin blockPin }`.

Validation before retry:

```bash
source tools/env_gemmini_thermal.sh
/home/lisihang/miniconda3/envs/thermal_placement/bin/python -m py_compile \
  runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py \
  runs/cadence_startup/manager/innovus/innovus_manager.py \
  runs/cadence_startup/tech/asap7.py
git -C runs/cadence_startup diff --check
```

Result: both checks passed.

Next retry route:

- Innovus output run tag: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r5_pg_sroute_stripe_target`.
- Genus handoff source remains accepted r2 Genus: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt`.
- At that time, PG acceptance remained strict: `verifyConnectivity -type special` had to report 0 opens.

## 0.33 Phase 2 r5 still blocked at PG special-connectivity gate

Date: 2026-05-11.

The r5 Innovus retry used stripe-targeted `sroute` for core/block PG pins:

```text
Innovus tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r5_pg_sroute_stripe_target
Genus handoff: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt
```

Observed result:

- Init and floorplan completed again.
- Explicit fake SRAM macro placement remained correct: `macro_count=6`, six fixed macros, `halo_status=applied`.
- `sroute` accepted `srouteCorePinTarget=stripe` and `srouteBlockPinTarget=stripe`.
- PG opens improved from r4's 1000 reported violations to 333 reported violations, but the PG acceptance gate still failed.

PG evidence:

```text
innovus/log/powerplan.log
Number of Core ports routed: 8498  open: 2542
Ring/Stripe ... on layer M9 is out of layer range and is ignored.

innovus/reports/powerplan_connectivity.rpt
Verification Complete : 333 Viols.  0 Wrngs.

innovus/reports/powerplan_PG_short.rpt
Verification Complete : 0 Short Viols.
```

Classification and judgment:

- This remains an acceptance-blocking PG special-connectivity failure.
- The stripe-target route is directionally useful but incomplete.
- The generated PG grid creates horizontal stripes on M9, while `sroute_max_layer` is M8. Local log evidence shows the M9 stripe target is ignored as out of layer range.
- The next route is to allow PG `sroute` up to M9 so it can use the generated M9 special stripes. This does not change CTS/NDR/NanoRoute signal/clock routing, which remains M2-M8, and does not introduce M10.

Next retry route:

- Update the ASAP7 PG sroute maximum layer to M9 while keeping `route_max_layer=M8` and `ndr_cts_max_layer=M8`.
- Keep strict PG 0-open gate enabled.
- Retry from a new clean Innovus tag using the same accepted r2 Genus handoff.

## 0.34 Phase 2 r6 Innovus retry prepared with PG sroute M9 reach

Date: 2026-05-11.

After r5 showed that M9 horizontal PG stripes were ignored by `sroute_max_layer=M8`, the nested startup repo was updated and committed as:

```text
48dd7aa Allow PG sroute to reach M9 stripes
```

Change summary:

- ASAP7 PG default `sroute_max_layer` changed from `M8` to `M9` so `sroute` can target the generated M9 horizontal stripes.
- Signal/detail route remains `route_max_layer=M8`.
- CTS/NDR route remains `ndr_cts_max_layer=M8`.
- No M10 routing is introduced.

Validation before retry:

```bash
source tools/env_gemmini_thermal.sh
/home/lisihang/miniconda3/envs/thermal_placement/bin/python -m py_compile \
  runs/cadence_startup/tech/asap7.py
git -C runs/cadence_startup diff --check
```

Result: both checks passed.

Next retry route:

- Innovus output run tag: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r6_pg_sroute_m9`.
- Genus handoff source remains accepted r2 Genus: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt`.
- At that time, PG acceptance remained strict: `verifyConnectivity -type special` had to report 0 opens.

## 0.35 Phase 2 r6 blocked: PG special connectivity remains open

Date: 2026-05-11.

The r6 Innovus retry used PG `sroute_max_layer=M9` while keeping signal/detail route and CTS/NDR at M2-M8:

```text
Innovus tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r6_pg_sroute_m9
Genus handoff: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt
```

Observed result:

- Init and floorplan completed.
- Fake SRAM macro placement stayed correct: 6 fixed macros, halo applied, and all macros were reported inside the core.
- Powerplan `sroute` used top/target layer 9.
- PG special connectivity still failed: `Verification Complete : 336 Viols. 0 Wrngs.`
- PG short check stayed clean: `Verification Complete : 0 Short Viols.`

Key log evidence:

```text
innovus/log/powerplan.log
srouteTopLayerLimit set to 9
srouteTopTargetLayerLimit set to 9
Number of Core ports routed: 8498  open: 2542

innovus/reports/powerplan_connectivity.rpt
Verification Complete : 336 Viols.  0 Wrngs.
```

Classification and blocker:

- Acceptance-blocking PG special-net connectivity failure.
- r6 confirms the blocker is not only M9 being out of the sroute layer range.
- `IMPPP-610` via-rule warnings and persistent open core ports indicate the current stripe/followpin/viarule strategy is insufficient for this explicit fake SRAM macro floorplan.
- Phase 2 cannot proceed to place, CTS, route, extraction, or final artifact gates under the active acceptance criteria until `verifyConnectivity -type special` reaches 0 opens.
- Current accepted evidence remains r2 Genus plus r6 init/floorplan/macro evidence; there is no accepted Innovus powerplan, placement, CTS, route, extraction, GDS, routed DEF, routed Verilog, SDF, or SPEF bundle.

Recommended next step:

Treat PG as the current blocker and design a targeted PG diagnostic plan from a saved floorplan checkpoint, then fold any successful Tcl diagnostics back into Python generation before another full retry. Candidate directions include inspecting rail/stripe topology near fake SRAM macro channels, adjusting macro placement/halo/channel spacing, adding explicit PG rings/straps around macros, tuning followpin and viarule strategy, or generating custom legal via stacks for ASAP7 PG.

## 0.36 Phase 2 PG diagnostic route from floorplan checkpoint

Date: 2026-05-11.

After r6, the next attempt is deliberately narrowed to a PG diagnostic/repair loop from the accepted r6 floorplan checkpoint rather than a full Phase 2 rerun.

Planned diagnostic route:

- Reuse r6 `innovus/data/floorplan.enc` as the starting checkpoint.
- Generate diagnostic Innovus Tcl from Python so the normal flow remains Python-first.
- Run only PG construction/verification variants, not placement, CTS, route, extraction, or streamOut.
- Preserve the active acceptance rule: `verifyConnectivity -type special` must reach 0 violations before the normal flow may proceed.
- Compare variants with explicit reports for PG opens, PG shorts, macro PG pin location, special-wire counts, and key sroute warnings.

Current evidence guiding the diagnostic:

- r6 `verify_PG_short` is clean: `Verification Complete : 0 Short Viols.`
- r6 `verifyConnectivity -type special` still has 336 violations.
- r6 sroute reached M9, so the blocker is not only M9 being outside the sroute layer range.
- Fake SRAM LEF PG pins are `DIRECTION INOUT` with `USE POWER/GROUND`, but the current fake SRAM PG pin shapes are on M4 while ASAP7 stdcell row PG pins are on M1.
- The r6 connectivity report contains many row-shaped horizontal opens, which points to incomplete core rail/followpin/stripe connectivity in addition to any macro block-pin connection issue.

This is a diagnostic route change and must not be reported as accepted Phase 2 unless a later run reaches the active artifact gates.

## 0.37 Phase 2 r7 PG diagnostic aborted: detailed sroute logging too verbose

Date: 2026-05-11.

The first checkpoint-level PG diagnostic entry was launched with tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r7
```

It restored the r6 `floorplan.enc` and started the `baseline_m9` variant, but the generated Tcl used `sroute -detailed_log`. Innovus began printing thousands of per-connection `phase1 maze route: ... remain open` lines and the log grew too quickly for the intended small diagnostic loop. The run was manually terminated before it could complete all variants.

Classification:

- Diagnostic harness issue, not a new physical implementation result.
- No accepted Phase 2 evidence came from r7.
- The partial r7 log still confirms the same warning class seen in r6, including `IMPPP-531` and `IMPPP-610` while attempting PG special route.

Next retry:

- Remove `-detailed_log` from diagnostic sroute.
- Suppress Innovus stdout/stderr from the Python diagnostic subprocess while preserving each Innovus `-log` file.
- Re-run the same checkpoint-level variant set with a clean r8 diagnostic tag.

## 0.38 Phase 2 r8 PG diagnostic result: sroute target variants do not reduce opens

Date: 2026-05-11.

The r8 checkpoint-level PG diagnostic completed from the r6 floorplan checkpoint:

```text
Diagnostic tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r8_quiet
Source floorplan: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r6_pg_sroute_m9/innovus/data/floorplan.enc
```

Variants run:

- `baseline_m9`: M8/M9 stripes and current sroute-to-stripe policy.
- `m1_over_pins_then_m9`: explicit M1 over-PG-pin followpin stripes before M8/M9 stripes.
- `core_rowend_block_nearest`: `corePinTarget=firstAfterRowEnd`, `blockPinTarget=nearestTarget`.

Observed result for all three variants:

- `verifyConnectivity -type special` still reports 336 open special-wire problems.
- `verify_PG_short` remains clean with 0 shorts.
- sroute still reports `Number of Core ports routed: 8498 open: 2542`.
- Logs still include `IMPPP-531` V7 spacing warnings and `IMPPP-610` missing viarule warnings.

Classification:

- The current blocker is not solved by simple sroute target selection or by adding M1 over-pin stripes.
- Connectivity opens remain concentrated around fake SRAM macro boundaries and macro channels.
- The next diagnostic should test cutting/removing standard-cell rows under/around explicit fake SRAM macros before PG construction.

Next retry:

- Add a `cutrow_halo_then_m9` diagnostic variant from the same floorplan checkpoint.
- Use Innovus `cutRow -area <macro_box> -halo <halo>` for each fake SRAM macro before PG stripe/sroute.
- Keep this diagnostic checkpoint-only; if it works, fold row cutting into the normal Python floorplan generation before another full Phase 2 retry.

## 0.39 Phase 2 r9 PG diagnostic result: macro row cutting does not reduce opens

Date: 2026-05-11.

The r9 checkpoint-level diagnostic ran only the `cutrow_halo_then_m9` variant:

```text
Diagnostic tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r9_cutrow
Source floorplan: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r6_pg_sroute_m9/innovus/data/floorplan.enc
```

The diagnostic applied `cutRow -area <macro_box> -halo 5.000` to all 6 fake SRAM macro boxes before the same M8/M9 stripe and sroute sequence. Evidence is in `innovus_pgdiag/reports/cutrow_halo_then_m9/cutrow_halo_then_m9_diagnostic.rpt`.

Observed result:

- All 6 macro row cuts were reported as applied.
- `verifyConnectivity -type special` still reports 336 special-wire open problems.
- `verify_PG_short` remains clean with 0 shorts.
- `Number of Core ports routed: 8498 open: 2542` is unchanged.
- `IMPPP-531` and `IMPPP-610` warning classes remain.

Classification:

- Cutting rows around the existing explicit macro placement is not sufficient to repair the PG network.
- The remaining evidence points away from simple macro row overlap and toward the missing/incomplete PG topology itself: the logs repeatedly report incomplete core rings, persistent failed via generation around V7/M8, and missing matched viarules for M2-M8 stack attempts.

Next candidate diagnostic:

- Add explicit core PG ring before M8/M9 stripes, then reconnect `corePin`/`blockPin` to ring/stripe targets.
- If core ring helps, fold ring generation into Python powerplan generation and rerun the normal powerplan gate.

## 0.40 Phase 2 PG diagnostic route: test explicit core ring

Date: 2026-05-11.

After r8 and r9 showed no reduction in PG opens from sroute target changes, M1 over-pin stripes, or macro row cutting, the next checkpoint-level diagnostic is to add an explicit core PG ring before stripe/sroute.

Planned r10 diagnostic:

- Source the same r6 floorplan checkpoint.
- Add a core ring with left/right on M8 and top/bottom on M9 for `VDD`/`VSS`.
- Keep signal/detail route and CTS/NDR policy unchanged at M2-M8; the diagnostic only changes PG topology.
- Use sroute core/block pin targets aimed at the ring, then run the same `verifyConnectivity -type special` and `verify_PG_short` checks.

Acceptance remains unchanged: this is only a candidate diagnostic unless PG special connectivity reaches 0 opens and the change is folded back into the normal Python powerplan flow.

## 0.41 Phase 2 r10 PG diagnostic result: centered core ring fails to instantiate

Date: 2026-05-11.

The r10 checkpoint diagnostic ran `core_ring_then_m9`:

```text
Diagnostic tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r10_core_ring
```

The variant attempted:

```text
addRing -nets {VSS VDD} -type core_rings -follow core -layer {top M9 bottom M9 left M8 right M8} -width 0.040000 -spacing 0.400000 -offset 1.000000 -center 1
```

Observed result:

- Innovus warned `IMPPP-220`: core rings are not created outside the design boundary.
- Innovus warned `IMPPP-4051`: failed to add rings, possibly due to IO-cell gaps.
- sroute then worsened to `Number of Core ports routed: 0 open: 11040`.
- `verifyConnectivity -type special` stopped at the 1000 error limit.
- `verify_PG_short` remained clean with 0 shorts.

Classification:

- This was a failed ring-instantiation diagnostic, not a valid PG topology result.
- The `-center 1` core-ring option is unsuitable for this padless/core-only Gemmini floorplan.

Next retry:

- Try an inside-core ring variant by removing `-center 1` and keeping an explicit core-boundary offset.
- If that still fails to instantiate a ring, switch away from `addRing` and generate explicit boundary straps/stripes instead.

## 0.42 Phase 2 r11 PG diagnostic result: inside core ring also fails to instantiate

Date: 2026-05-11.

The r11 checkpoint diagnostic ran `core_ring_inside_then_m9`:

```text
Diagnostic tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r11_core_ring_inside
```

This variant removed `-center 1` from the prior `addRing` command and kept left/right on M8 and top/bottom on M9. Innovus still reported `IMPPP-220` and `IMPPP-4051`, so the ring was not instantiated as a usable PG target.

Observed result:

- `sroute` worsened to `Number of Core ports routed: 0 open: 11040`.
- `verifyConnectivity -type special` hit the 1000 violation cap.
- `verify_PG_short` stayed clean with 0 shorts.

Classification:

- Failed ring-instantiation diagnostic, not accepted Phase 2 evidence.
- `addRing` is not a viable immediate repair route for this padless/core-only floorplan without changing the IO/floorplan model.
- The next small diagnostic should switch away from ring targets and test whether disconnected floating special-wire pieces can be reconnected by expanding the `sroute -connect` set before attempting explicit manual boundary straps.

## 0.43 Phase 2 PG diagnostic route: test floating special-stripe reconnection

Date: 2026-05-11.

After r10 and r11 showed that `addRing` does not produce a usable ring in the current floorplan, the next checkpoint-level diagnostic is intentionally smaller than manual boundary strap generation.

Planned r12 diagnostic:

- Source the same r6 floorplan checkpoint.
- Keep the baseline M8/M9 stripe topology.
- Keep `corePin` and `blockPin` targets on `stripe`.
- Expand `sroute -connect` from `{ corePin blockPin }` to `{ corePin blockPin floatingStripe }` and set `-floatingStripeTarget stripe`.
- Run only `verifyConnectivity -type special` and `verify_PG_short` after PG construction.

Rationale:

- The dominant report class is `IMPVFC-200`: special-wire pieces are not connected together.
- r8/r9 reached the same `Number of Core ports routed: 8498 open: 2542`, which suggests the existing stripes and rails are partly present but not all PG pieces are joined.
- If this reduces or eliminates opens, the change should be folded back into the Python-managed normal Innovus powerplan flow before another full Phase 2 retry.
- If it does not reduce opens, the next route should move to explicit boundary straps/stripe geometry rather than more `addRing` variants.

## 0.44 Phase 2 r12 PG diagnostic result: floatingStripe reconnection does not reduce opens

Date: 2026-05-11.

The r12 checkpoint diagnostic ran `floating_stripe_then_m9`:

```text
Diagnostic tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r12_floating_stripe
```

This variant kept the baseline M8/M9 stripe topology and changed `sroute` from `{ corePin blockPin }` to `{ corePin blockPin floatingStripe }` with `-floatingStripeTarget stripe`.

Observed result:

- The generated Tcl and Innovus log confirm `srouteFloatingStripeTarget set to "stripe"`.
- `sroute` still reports `Number of Core ports routed: 8498 open: 2542`.
- `verifyConnectivity -type special` still reports 336 violations / 336 open-line entries.
- `verify_PG_short` stays clean with 0 shorts.
- `IMPPP-531` and `IMPPP-610` warning classes remain.

Classification:

- Failed PG repair diagnostic; no accepted Phase 2 evidence.
- The remaining opens are not explained by omitting `floatingStripe` from the `sroute -connect` set.
- The next diagnostic should inspect the open coordinate pattern and then test an explicit geometry repair, likely custom boundary/channel straps or via/stripe geometry changes, rather than more `sroute` target-only variants.

## 0.45 Phase 2 PG diagnostic route: test low-layer M2 rail stitching

Date: 2026-05-11.

After r12 left the PG open count unchanged, the connectivity coordinates were clustered from the r12 report. The result shows 300 of 336 opens are horizontal rail-like segments. The dominant spans are:

- full-width VDD/VSS rows from x about 1 to 573 in upper/inter-macro row bands,
- x about 304/305 to 376 near the central macro channel,
- smaller groups near x about 116 to 188 and x about 495 to 573.

This pattern matches row/followpin PG pieces and macro-channel fragments not being stitched into the higher-level M8/M9 PG grid. The r12 run also kept the prior `IMPPP-610` missing-via-rule warnings for M2-M8 stack attempts.

Planned r13 diagnostic:

- Source the same r6 floorplan checkpoint.
- Add explicit M2 vertical stitch stripes before the existing M8/M9 stripe mesh.
- Keep `sroute` targets on `stripe` and return the connect set to `{ corePin blockPin }` for the first M2 stitch test.
- Run only `verifyConnectivity -type special` and `verify_PG_short`.

Acceptance remains unchanged: this is only a PG repair diagnostic unless it reaches 0 special connectivity opens and is folded back into the normal Python-managed Innovus powerplan flow.

## 0.46 Phase 2 r13 PG diagnostic result: M2 rail stitching worsens connectivity

Date: 2026-05-11.

The r13 checkpoint diagnostic ran `m2_stitch_then_m9`:

```text
Diagnostic tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r13_m2_stitch
```

This variant added explicit M2 vertical stitch stripes before the existing M8/M9 stripe mesh and kept `sroute -connect { corePin blockPin }`.

Observed result:

- `verifyConnectivity -type special` worsened from 336 opens to 702 opens.
- `verify_PG_short` stayed clean with 0 shorts.
- `sroute` still reported `Number of Core ports routed: 8498 open: 2542`.
- The log shifted the primary warning pattern toward M2-M3 missing VIARULEs and M5/V4 min-area/spacing via-generation failures.

Classification:

- Failed PG repair diagnostic; no accepted Phase 2 evidence.
- Simple low-layer M2 stitch stripes are counterproductive in this floorplan/ASAP7 collateral setup.
- The result strengthens the diagnosis that PG failure is a topology plus legal-via/stripe-geometry issue, not only missing low-layer metal.
- Since `sroute` logs show `srouteConnectStripe set to false`, the next small diagnostic should determine whether an explicit stripe-connect mode exists and can connect existing stripe pieces without adding new low-layer geometry.

## 0.47 Phase 2 PG diagnostic conclusion: no standalone sroute stripe-connect object

Date: 2026-05-11.

After r13, a local Innovus command-help query was run in a temporary directory:

```text
innovus -no_gui -overwrite -execute 'help sroute; exit' -log sroute_help
```

The help output lists the legal `sroute -connect` objects as:

```text
blockPin corePin padPin padRing floatingStripe secondaryPowerPin
```

It does not list a standalone `stripe` connect object. Therefore the repeated log line `srouteConnectStripe set to false` cannot be repaired by simply adding `stripe` to `-connect`; the closest legal route was r12's `floatingStripe` test, which did not reduce opens.

Current PG-loop conclusion:

- `sroute` target-only changes do not fix the 336 opens.
- `floatingStripe` reconnection does not fix the 336 opens.
- `addRing` is not viable in the current padless/core-only floorplan.
- simple M2 stitch stripes worsen opens to 702.
- PG short checks remain consistently clean at 0 shorts.

Next viable repair direction is no longer a one-line `sroute` option. It should be an explicit PG topology/geometry repair folded into Python generation, likely one of:

- define legal custom via-generation or routing rules for the M1/M2 through M8/M9 PG stack,
- replace the current dense auto-generated stripe/followpin strategy with explicit boundary/channel straps that avoid the failing via geometries,
- or alter the floorplan/macro channel topology so standard-cell rails and fake SRAM PG pins connect through fewer problematic narrow via stacks.

Phase 2 remains blocked at PG special connectivity until `verifyConnectivity -type special` reaches 0 opens.

## 0.48 Phase 2 PG diagnostic cleanup and next repair plan

Date: 2026-05-11.

A cleanup pass was run after the r7-r13 checkpoint-level PG diagnostics.

Cleanup policy:

- Keep evidence needed to reproduce and audit each diagnostic: generated Tcl, ordinary `.log`, `.cmd`, reports, startup manifests, and Innovus checkpoints (`.enc` plus `.enc.dat` where present).
- Remove redundant Innovus verbose `.logv` files from diagnostic run directories.
- Do not delete `runs/cadence_startup`; it remains the nested startup source repository.
- Do not delete the r6 source floorplan checkpoint or any r8-r13 diagnostic checkpoint.

Removed files:

- `r7/innovus_pgdiag/log/baseline_m9.logv`
- `r7/innovus_pgdiag/log/m1_over_pins_then_m9.logv`
- `r8_quiet/innovus_pgdiag/log/baseline_m9.logv`
- `r8_quiet/innovus_pgdiag/log/m1_over_pins_then_m9.logv`
- `r8_quiet/innovus_pgdiag/log/core_rowend_block_nearest.logv`
- `r9_cutrow/innovus_pgdiag/log/cutrow_halo_then_m9.logv`
- `r10_core_ring/innovus_pgdiag/log/core_ring_then_m9.logv`
- `r11_core_ring_inside/innovus_pgdiag/log/core_ring_inside_then_m9.logv`
- `r12_floating_stripe/innovus_pgdiag/log/floating_stripe_then_m9.logv`
- `r13_m2_stitch/innovus_pgdiag/log/m2_stitch_then_m9.logv`

Retained diagnostic evidence summary:

- r7: aborted harness/logging attempt; ordinary logs and generated Tcl retained, no accepted checkpoint evidence.
- r8: baseline, M1 over-pins, and target-selection variants retained; all left 336 opens and 0 shorts.
- r9: `cutrow_halo_then_m9` retained; left 336 opens and 0 shorts.
- r10/r11: core-ring variants retained; ring generation failed and connectivity worsened to the 1000-violation cap, 0 shorts.
- r12: `floating_stripe_then_m9` retained; left 336 opens and 0 shorts.
- r13: `m2_stitch_then_m9` retained; worsened to 702 opens and 0 shorts.

Current blocker remains unchanged: Phase 2 cannot be accepted until `verifyConnectivity -type special` reaches 0 opens.

Next repair plan:

1. Add a Python-generated PG inspection Tcl, not a repair attempt, from the r6 floorplan checkpoint. It should report special-net wire counts by layer/subclass, via counts by layer pair, stripe/followpin extents, and marker coordinates near the r12 open clusters. This is needed before adding more geometry.
2. Inspect ASAP7 tech LEF / Innovus DB via definitions for legal V1-V8 and M2-M3/M3-M4/M7-M8 combinations used by PG. The repeated `IMPPP-610` warnings show the current auto via selection is not finding legal matched via rules for the generated PG geometry.
3. Based on the inspection, choose one narrow repair candidate:
   - custom via-generation / route-rule setup for the existing M1/M2-to-M8/M9 PG stack, if legal via definitions exist but are not selected;
   - or explicit M8/M9 channel and boundary straps with controlled coordinates and fewer via-stack locations, if auto dense stripes are creating illegal via sites;
   - or a floorplan/macro-channel adjustment only if the PG inspection shows rails are fragmented primarily by macro channels and blockages.
4. Run the next candidate as one checkpoint-level variant with a clean r14 tag. The acceptance gate for the diagnostic remains `verifyConnectivity -type special == 0` and `verify_PG_short == 0`.
5. Only if a checkpoint diagnostic reaches 0 opens, fold the proven changes into the normal Python-managed Innovus powerplan flow, regenerate scripts, run preflight/write-scripts checks, and then retry the full Phase 2 flow under a clean full-flow tag.

## 0.49 Phase 2 PG repair step: r14 inspection from retained baseline PG checkpoint

Date: 2026-05-11.

The next repair step is an inspection run, not another geometry mutation. The selected source is the retained r12 checkpoint because it represents the baseline M8/M9 PG topology with the confirmed 336-open failure and without the r13 M2-stitch regression:

```text
Source checkpoint: runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r12_floating_stripe/innovus_pgdiag/data/pgdiag_floating_stripe_then_m9.enc
Planned tag: gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pginspect_20260511_r14_baseline_def
```

Planned action:

- Add a Python-managed `--run-innovus-pg-inspection` entry in the nested startup repo.
- Source the selected PG checkpoint in Innovus.
- Export routed DEF with `defOut -routing`.
- Re-run `verifyConnectivity -type special` and `verify_PG_short` for local evidence.
- Parse exported DEF in Python to summarize `SPECIALNETS` layer/via/segment distribution and compare it with open-coordinate clusters.

This is still not accepted Phase 2 evidence. It is intended to choose the next narrow repair candidate without additional blind PG geometry attempts.

## 0.50 Phase 2 r14 PG inspection result: baseline PG DEF exposes via-rule mismatch

Date: 2026-05-11.

The r14 read-only PG inspection completed with tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pginspect_20260511_r14_baseline_def
```

Input checkpoint:

```text
r12_floating_stripe/innovus_pgdiag/data/pgdiag_floating_stripe_then_m9.enc
```

Generated evidence:

- `innovus_pginspect/reports/pg_inspection_routed.def`
- `innovus_pginspect/reports/pg_inspection_connectivity.rpt`
- `innovus_pginspect/reports/pg_inspection_PG_short.rpt`
- `startup/innovus_pg_inspection_manifest.json`

Observed result:

- Inspection completed with Innovus return code 0.
- It reproduced the r12 baseline failure: 336 special connectivity opens and 0 PG shorts.
- Exported DEF has 2 special nets: VDD and VSS.
- SPECIALNETS shape distribution:
  - VDD: 163425 FOLLOWPIN, 34424 COREWIRE, 3744 STRIPE, 30 BLOCKWIRE entries.
  - VSS: 169615 FOLLOWPIN, 34335 COREWIRE, 3744 STRIPE, 30 BLOCKWIRE entries.
- Segment orientation after DEF `*` coordinate expansion:
  - VDD: 9111 horizontal, 410 vertical segments.
  - VSS: 9055 horizontal, 412 vertical segments.
  - M8/M9 mesh is sparse and regular: 58 M8 vertical and 58 M9 horizontal segments per net.
  - M1/M2/M4 are dominated by horizontal rail/corewire pieces; M3 appears as only a small number of vertical pieces in the parsed SPECIALNETS.
- Open clusters remain dominated by horizontal rail fragments:
  - full-width x about 1 to 573,
  - central macro-channel x about 304/305 to 376,
  - smaller spans x about 116 to 188 and x about 495 to 573.

ASAP7 tech LEF inspection around generated via rules shows an important mismatch:

- There is a default `M2_M1` generated via rule.
- There are default high-layer generated rules such as `M8_M7` and `M9_M8`.
- There is no ordinary default `M3_M2` rule in the inspected tech LEF section; the available M2-M3 generated rule is `M3_M2widePWR0p936`, which requires a wide M3 geometry.
- Similar wide-PG rules exist for `M4_M3widePWR0p864`, `M5_M4widePWR0p864`, `M6_M5widePWR1p152`, and `M7_M6widePWR1p152`.

Classification:

- This supports the current blocker diagnosis: the existing dense sroute/followpin strategy is asking viaGen for narrow M2-M3 and other stack vias that do not match the ASAP7 1x generated via-rule collateral.
- The M10 `IMPTR-2101` messages still appear during checkpoint restore and remain classified as ASAP7 tech collateral warnings/errors, not the active PG acceptance blocker.
- Phase 2 remains blocked at PG special connectivity.

Next repair candidate:

- Do not repeat simple M2 stitch or sroute-target variants.
- Test one checkpoint-level r15 candidate that introduces a sparse, legal-width intermediate PG ladder/strap stack using the available wide-PG via-rule dimensions, then connects to the existing M8/M9 mesh.
- The candidate should keep geometry sparse and coordinate-controlled to avoid the r13 failure mode where dense M2 stripes created more disconnected special-wire pieces.
- At that time, acceptance for r15 remained strict: `verifyConnectivity -type special == 0` and `verify_PG_short == 0` before any fold-back into the normal full Innovus flow.

## 0.51 Phase 2 PG repair route: test ASAP7-preferred M8/M9 stripe directions

Date: 2026-05-11.

After r14, the ASAP7 1x tech LEF layer directions were checked:

```text
M8 DIRECTION HORIZONTAL
M9 DIRECTION VERTICAL
```

The current Python-generated PG stripe topology used the opposite directions in both the normal manager and checkpoint diagnostic helper:

```text
M8 vertical
M9 horizontal
```

This is a stronger and simpler repair candidate than the previously planned wide via ladder. It can explain why horizontal followpin/corewire fragments are not being joined cleanly to the high-level PG mesh and why via generation repeatedly fails near upper-layer intersections.

Planned r15 diagnostic:

- Source the same r6 floorplan checkpoint.
- Keep no M10 usage.
- Generate high-level PG mesh with M9 vertical stripes and M8 horizontal stripes, matching ASAP7 tech LEF preferred directions.
- Keep `sroute -connect { corePin blockPin }`, `corePinTarget=stripe`, `blockPinTarget=stripe`, and M1-M9 sroute range for this isolated test.
- Run only `verifyConnectivity -type special` and `verify_PG_short`.

At that time, if r15 reduced or cleared opens, the plan was to fold the direction fix into both the normal Python Innovus manager and diagnostic helper before any full Phase 2 retry. Acceptance then remained strict: 0 special opens and 0 PG shorts.

## 0.52 Phase 2 r15 direction-matched PG diagnostic result: worse opens, not accepted

Date: 2026-05-11.

The r15 checkpoint-level PG diagnostic completed with tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r15_direction_match
```

Variant tested:

- `direction_matched_m8_m9`: M9 vertical stripes and M8 horizontal stripes, matching the ASAP7 1x tech LEF preferred directions.
- Source checkpoint remained the r6 floorplan checkpoint.
- No M10 was introduced.
- `sroute` still used `-connect { corePin blockPin }`, `corePinTarget=stripe`, `blockPinTarget=stripe`, and M1-M9 range.

Generated evidence:

- `startup/innovus_pg_diagnostic_manifest.json`
- `innovus_pgdiag/scripts/direction_matched_m8_m9.tcl`
- `innovus_pgdiag/reports/direction_matched_m8_m9/direction_matched_m8_m9_connectivity.rpt`
- `innovus_pgdiag/reports/direction_matched_m8_m9/direction_matched_m8_m9_PG_short.rpt`
- `innovus_pgdiag/data/pgdiag_direction_matched_m8_m9.enc`

Observed result:

- Innovus returned 0 for the diagnostic script, but the diagnostic manifest is `ok=false` and `accepted_phase2=false`.
- `verifyConnectivity -type special` reported 481 special-wire opens.
- `verify_PG_short` reported 0 short violations.
- `sroute` reported `Number of Core ports routed: 8498 open: 2542`, matching the prior unresolved core-port symptom.
- The log still reports `IMPPP-610` missing generated via rules from M2-M3 through M7-M8, and V7 `IMPPP-531` spacing failures.
- The open count is worse than the r12/r14 baseline of 336 opens, so this direction-only repair is rejected.

Cleanup performed after result capture:

- Removed the r15 `.logv` file.
- Retained the checkpoint, manifest, generated Tcl, ordinary log, and connectivity/short reports as evidence.

Classification:

- Matching the M8/M9 preferred routing directions by itself does not solve the PG special connectivity blocker.
- The active blocker remains incomplete PG special-net stitching, especially rail/channel fragments plus failed legal via generation for the dense M1/M2-to-M8/M9 stack.
- Phase 2 remains blocked; this result is not accepted Phase 2 evidence.

## 0.53 Phase 2 next PG repair plan after r15

Date: 2026-05-11.

Next action is another checkpoint-level repair loop before any full Genus/Innovus rerun:

1. Keep the r6 floorplan checkpoint as source so the test isolates PG generation.
2. Do not repeat direction-only, dense M2 stitch, cut-row-only, floatingStripe-only, or core-ring variants.
3. Add one Python-generated diagnostic variant that targets the actual via-rule failure: a sparse, coordinate-controlled intermediate PG ladder/strap stack using legal wide-PG geometry where ASAP7 exposes wide generated via rules.
4. Keep M10 out of the route.
5. Run only the diagnostic Tcl, `verifyConnectivity -type special`, and `verify_PG_short`.
6. At that time, acceptance remained strict: 0 special opens and 0 PG shorts before folding any change into the normal Innovus manager.

If the wide-ladder diagnostic still fails, inspect whether the remaining opens are caused by macro-channel rail fragmentation that requires explicit macro-channel bridge straps or floorplan/channel adjustment.

## 0.54 Phase 2 planned r16 PG diagnostic: sparse wide PG ladder

Date: 2026-05-11.

A new Python-generated checkpoint diagnostic variant was added in the nested `runs/cadence_startup` repo:

```text
wide_pg_ladder_then_m9
```

Purpose:

- Target the active `IMPPP-610` via-rule failure rather than repeating prior geometry-only variants.
- Insert sparse legal-width intermediate straps before the existing high-level PG mesh.
- Use ASAP7 wide PG via-rule-compatible widths: M3 vertical 0.234, M4 horizontal 0.216, M5 vertical 0.216, M6 horizontal 0.288, and M7 vertical 0.288.
- Keep M10 out of the experiment.
- Keep the source as the r6 floorplan checkpoint to isolate PG generation.

Planned run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_pgdiag_20260511_r16_wide_ladder
```

Validation sequence:

1. `py_compile` for the modified Python entry.
2. Nested repo `git diff --check`.
3. `--preflight` using the r16 tag and selected variant.
4. `--run-innovus-pg-diagnostic` for only `wide_pg_ladder_then_m9`.

At that time, acceptance for this diagnostic remained strict: `verifyConnectivity -type special` had to report 0 opens and `verify_PG_short` had to report 0 shorts. A passing diagnostic would still need to be folded back into the normal Python Innovus manager and rerun through the full Phase 2 artifact gates.

## 0.55 Phase 2 PG repair stop and cleanup decision

Date: 2026-05-12.

The user stopped further PG repair attempts and requested cleanup of attempt files.

Last in-flight attempt status:

- r16 `wide_pg_ladder_then_m9` was launched on 2026-05-11 from the r6 floorplan checkpoint.
- It did not produce `startup/innovus_pg_diagnostic_manifest.json`, `verifyConnectivity`, `verify_PG_short`, or a saved PG checkpoint.
- The retained tail evidence before cleanup showed sroute still in power routing, repeated `IMPPP-610` via-rule failures around M5-M6 and M3-M4, V7 `IMPPP-531` spacing warnings, and `IMPPP-4500` extended-geometry runtime warning.
- This is classified as an incomplete diagnostic, not an accepted or failed connectivity measurement.

Cleanup policy applied:

- Remove generated PG diagnostic/inspection run directories r7 through r16 and r14 from `runs/.../physical/`.
- Keep the r6 floorplan/full attempt directory because it is the current source checkpoint and blocker evidence.
- Keep nested `runs/cadence_startup` Git commits and docs as the record of what was tried; do not add the nested repo to the top-level tracked files.

Current PG assessment for research use:

- The known accepted PG target was 0 special opens, but the latest completed diagnostics never reached it. Baseline-style attempts remained at 336 special-wire opens, r15 direction-matched worsened to 481 opens, and all completed variants reported 0 PG shorts.
- For a foundry/signoff-quality implementation this is not acceptable: PG special-route opens mean some VDD/VSS special-net shapes are disconnected, and the tool cannot prove a complete power distribution network.
- For the current thermal research goal, this may be tolerable only if Stage 2 is explicitly downgraded from accepted commercial-flow evidence to a best-effort physical proxy. The standard-cell placement, routing geometry, area, timing, parasitic extraction, and power estimates may still be useful, but PG-grid-derived IR/EM, robust supply connectivity, and any claim of clean routed implementation would not be valid.
- The largest downstream risk is not ordinary DRC noise; it is that PG opens can invalidate signoff-style connectivity and may also make power/extraction evidence harder to defend if power analysis relies on complete special nets.
- If proceeding despite this, reports must clearly label the implementation as PG-open / non-signoff and exclude PG cleanliness from acceptance. Stage 3/4 thermal conclusions should be framed as placement/activity/power proxy evidence, not final physical signoff evidence.


## 0.56 Phase 2 quality downgrade accepted: PG-open thermal proxy

Date: 2026-05-12.

User decision:

- Stop further PG repair attempts for now.
- Accept the Stage 2 quality downgrade to `PG-open thermal proxy` for the thermal research path.
- Update related docs before continuing flow execution.

Updated interpretation:

- PG special connectivity remains a documented limitation, not a solved issue.
- Completed PG diagnostics did not reach the original 0-open target: baseline-style attempts stayed at 336 opens, r15 direction-matched reported 481 opens, and completed variants reported 0 PG shorts.
- Future Stage 2 full-flow attempts should still produce the full artifact set: routed DEF, routed Verilog, SDF, SPEF, GDS, `cts.enc`, `routing.enc`, post-route timing/area/power reports, route/DRC/connectivity reports, macro placement evidence, and pin placement evidence.
- Nonzero PG special opens are now allowed only as a labeled non-signoff limitation. They must not be described as PG-clean, DRC-clean, IR/EM-clean, or foundry/signoff-clean.
- Stage 3/4 may consume the resulting Cadence physical implementation as a thermal proxy. Reports must frame conclusions as placement/activity/power-driven thermal trends and must not make power-grid integrity or IR/EM claims.

Docs updated in this task:

- `AGENTS.md`
- `docs/phase0tophase4_cadence_asap7_plan.md`
- `docs/README.md`
- `docs/agent_task_checklist.md`
- `docs/agent_command_reference.md`
- `docs/agent_onboarding.md`
- `docs/gemmini_thermal_issue_log.md`

## 0.57 Phase 2 continuation route after PG-open downgrade

Date: 2026-05-12.

The active Stage 2 requirement has changed from PG-clean acceptance to `PG-open thermal proxy`. The downgrade only relaxes the PG special-connectivity cleanliness gate; it does not relax the requirement to produce routed DEF, routed Verilog, SDF, SPEF, GDS, `cts.enc`, `routing.enc`, post-route timing/area/power reports, route/DRC/connectivity reports, macro placement evidence, and top-level pin placement evidence.

Current state review:

- r2 Genus remains the selected synthesis handoff and used bare `syn_opt`.
- r6 remains the retained Innovus full-flow attempt and blocker evidence.
- r6 has valid `innovus/data/init.enc`, `innovus/data/floorplan.enc`, `innovus/data/Gemmini.floorplan.def`, macro placement evidence, and PG connectivity/short reports.
- r6 does not have `innovus/data/powerplan.enc`, `placement.enc`, `cts.enc`, or `routing.enc` because the old PG-clean powerplan gate stopped before saving the powerplan checkpoint.
- PG diagnostic/repair attempts are not selected as continuation sources because they were checkpoint-level experiments and were not accepted full-flow states.

Selected continuation checkpoint:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r6_pg_sroute_m9/innovus/data/floorplan.enc
```

Reasoning:

- It is the latest retained clean floorplan checkpoint from the normal Python-managed Innovus full route.
- It preserves explicit fake SRAM macro placement and top-level pin placement evidence.
- It avoids resuming from a failed or absent `powerplan.enc`.
- It avoids carrying PG diagnostic modifications into the resumed full implementation.

Script update:

- Added a Python-managed `--run-innovus-full-from-floorplan` entry in the nested `runs/cadence_startup` repo.
- The entry seeds the selected `floorplan.enc` and its `.dat` directory into a new clean run tag, copies the floorplan DEF and floorplan evidence, then runs only `powerplan`, `placement`, `cts`, and `routing`.
- Full Innovus now defaults `require_pg_clean=false` unless `TP_STAGE2_REQUIRE_PG_CLEAN=true` is explicitly set, matching the user-approved PG-open downgrade.
- Any nonzero PG special opens must still be reported as a non-signoff limitation.

Planned run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260512_r17_pgopen_resume_floorplan
```

Validation before heavy run:

- Run `py_compile` on the modified entry.
- Run nested repo `git diff --check`.
- Run `--preflight` with the selected r17 tag and explicit r6 source floorplan checkpoint.
- Inspect the generated/seeded continuation scripts before launching the heavy Innovus continuation.

## 0.58 Phase 2 continuation script-only validation entry

Date: 2026-05-12.

Added a script-only companion entry for the PG-open continuation route:

```text
--write-resume-scripts-from-floorplan
```

Purpose:

- Generate the floorplan-resume `powerplan`, `placement`, `cts`, and `routing` Tcl without launching Cadence.
- Confirm that `powerplan.tcl` sources the seeded `innovus/data/floorplan.enc` checkpoint before rerunning PG generation.
- Keep the real continuation run Python-first and reviewable before the heavy Innovus launch.

This is not a new PG repair attempt. It supports the user-approved `PG-open thermal proxy` continuation by making the checkpoint recovery path auditable before execution.


## 0.59 Phase1b Gemmini gate-level boundary replay feasibility plan

Date: 2026-05-12.

User-confirmed scope:

- Only Gemmini gate-level boundary-replay simulation is in scope.
- Full-SoC gate simulation is out of scope.
- Current dynamic validation workload is `mvin_mvout` only; OS/WS gate replay is not part of current Phase1b acceptance because the warmup-to-measure cost is too high.
- Stage 1 RTL activity for all three workloads remains valid; Phase1b is a supplemental activity-quality path, not a replacement for Stage 1.

Selected feasibility input:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt/genus/data/Gemmini-mapped.v
```

Method judgment:

- Verilator + Genus mapped netlist + full ASAP7 cell Verilog is a plausible zero-delay functional gate replay route.
- Verilator ignores `specify`/SDF timing, so this cannot be reported as SDF timing simulation or commercial gate signoff.
- Gate top ports should be extracted from `module Gemmini(...)` in the mapped netlist and mapped to the Stage 1 RTL VCD `...rockettile.gemmini` scope.
- Replay must drive top inputs from sampled RTL boundary vectors and compare top outputs against RTL VCD expected outputs on deterministic 0/1 cycles.
- Warmup must establish internal flop/SRAM state before measuring gate activity; do not start from the middle of a workload window without known state.

Known blocker to validate first:

- Existing fake SRAM Verilog stubs under `.cache/fake_sram/asap7/Gemmini/verilog/` are blackboxes.
- Phase1b needs simulation-only behavioral `mem_ext` and `mem_0_ext` models, validated before formal replay.
- Initial zero-init policy is acceptable only as feasibility policy; output mismatches must be investigated before accepting activity.

Required documentation/output boundary:

- Outputs go under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_<tag>/`.
- Do not modify Chipyard/Gemmini RTL.
- Do not modify Stage 2 physical run artifacts such as `Gemmini-mapped.v`.
- If the selected Stage 2 netlist, SRAM wrappers, top ports, or ASAP7 cell Verilog set changes, Phase1b results become stale and must be rerun.


## 0.60 Phase1b mvin_mvout Verilator parameter trial record (provisional)

Date: 2026-05-13.

This entry intentionally records only the Phase1b `mvin_mvout` gate-replay Verilator parameter trials seen so far. Detailed judgment and recommended defaults are deferred until the Phase1b `mvin_mvout` attempt has completed and the final evidence can be reviewed.

Input set common to these trials:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260511_r2_bare_synopt/genus/data/Gemmini-mapped.v
/home/lisihang/asap7/asap7sc7p5t_28/Verilog/*.v
collateral/gate_sim/fake_sram/mem_ext.sv
collateral/gate_sim/fake_sram/mem_0_ext.sv
```

Recorded trial parameters:

| run tag | Verilator runtime threads | build jobs | output split | output split cfuncs | CFLAGS | status at cleanup |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `phase1b_mvin_mvout_boundary_replay_20260512_smoke` | not explicitly set in command | 8 | default / not explicitly set | default / not explicitly set | none | interrupted before completion |
| `phase1b_mvin_mvout_boundary_replay_20260512_j128_smoke` | 128 | 128 | 20000 | 20000 | none | timeout / no executable |
| `phase1b_mvin_mvout_boundary_replay_20260512_j128_t1_smoke` | 1 | 128 | 20000 | 20000 | none | timeout / no executable |
| `phase1b_mvin_mvout_boundary_replay_20260512_j128_t1_o0_split1k_smoke` | 1 | 128 | 1000 | 1000 | `-O0` | interrupted before completion / no executable |
| `phase1b_mvin_mvout_boundary_replay_20260513_t16_j64_split10k_cfunc100_o0_full` | 16 | 64 | 10000 | 100 | `-O0` | timeout after 4 h build window / no executable; 2879 build files and 74 object files at timeout |
| `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_vlto0_cxxo0_full` | 1 | 64 | 1000 | 50 | `-O0 -g0`; Verilator `-O0` | terminated after about 52 min in Verilator front-end / no generated C++ beyond command log |
| `phase1b_mvin_mvout_boundary_replay_20260513_t16_j64_split1k_cfunc100_cxxo0_full` | 16 | 64 | 1000 | 100 | `-O0 -g0` | terminated during make after about 64 min / no executable; 23276 build files, 12 object files, full ASAP7 Verilog set |
| `phase1b_mvin_mvout_boundary_replay_20260513_t16_j64_split10k_cfunc100_cxxo0_refcells_full` | 16 | 64 | 10000 | 100 | `-O0 -g0`; referenced-cell library | build failed quickly: filtered library omitted ASAP7 UDP primitives `altos_dff*` / no executable |
| `phase1b_mvin_mvout_boundary_replay_20260513_t16_j64_split10k_cfunc100_cxxo0_refcells_udp_full` | 16 | 64 | 10000 | 100 | `-O0 -g0`; referenced-cell+UDP library | terminated during make after about 62 min / no executable; 178 cells + 14 UDP primitives, 3 object files |
| `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_cxxo0_refcells_udp_full` | 1 | 64 | 1000 | 50 | `-O0 -g0`; referenced-cell+UDP library | terminated during make at cleanup request / no executable; 178 cells + 14 UDP primitives, 4 object files |
| `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_refcells_udp_full` | 1 | 64 | 1000 | 50 | `-O0 -g0`; referenced-cell+UDP library; manual make with `clang++` and Verilator `--compiler clang` | terminated during make after about 2.4 h total / no executable; build reached 42653 object files, then spent about 49 min compiling one 301M `VGemmini___024root__7636__Slow.cpp` file |
| `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split500_cfunc10_clang_noinline_refcells_udp_full` | 1 | 64 | 500 | 10 | `-O0 -g0`; referenced-cell+UDP library; manual make with `clang++`; Verilator `--compiler clang --inline-mult 0 --inline-cfuncs 0 --inline-cfuncs-product 0` | terminated during Verilator front-end after about 83 min / no executable; generated about 54663 files, largest observed C++ file about 50M |
| `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_hier64_split1k_cfunc50_clang_refcells_udp_full` | 1 | 64 | 1000 | 50 | `-O0 -g0`; referenced-cell+UDP library; manual make with `clang++`; Verilator `--compiler clang --hierarchical --hierarchical-threads 64` | terminated during Verilator front-end after about 24 min / no executable; generated about 21235 files, largest observed C++ file about 315M |
| `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full` | 1 | 64 | 1000 | 50 | `-O0 -g0`; referenced-cell+UDP library; manual make with `clang++`; Verilator `--compiler clang --no-timing` | build entered make quickly but terminated during `VGemmini___024root__7636__Slow.cpp` after about 54 min on that file / no executable; build reached 42653 object files, largest observed C++ file about 315M |
| `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_split7636_retry` | 1 | 64 | 1000 | 50 | `-O0 -g0`; referenced-cell+UDP library; manual make with `clang++`; Verilator `--compiler clang --no-timing`; post-Verilator local split of 301M `VGemmini___024root__7636__Slow.cpp` into 32 helper C++ files | build passed and produced 279M `VGemmini`; script path bug and CRLF header bug fixed; 21600s-timeout run was preempted after reaching about cycle 10048 / 110524 compare rows because projected full runtime exceeded 6h; partial compare archived |

Current fixed compilation evidence and lessons from the successful build:

- Successful build artifact exists at `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/verilator_build/VGemmini` and is about 279M. The generated archive is about 829M and the build tree contains about 42686 object files.
- The effective successful compile route is: referenced-cell+UDP ASAP7 Verilog library, Verilator `--compiler clang --no-timing`, `--threads 1`, `--threads-dpi all`, `--output-split 1000`, `--output-split-cfuncs 50`, manual `make -j64`, and `clang++` with `-O0 -g0`.
- `--threads` is Verilator model/runtime threading, not the same thing as `make -j`. The successful build used one Verilated runtime thread and many make compile jobs. Earlier high `--threads` attempts did not fix the compile bottleneck.
- Filtering to referenced ASAP7 cells is useful, but the filter must retain the required ASAP7 UDP primitives; referenced cells without UDP failed quickly.
- `--no-timing` avoids unnecessary timing handling for this zero-delay Phase1b method and made the generated make stage easier to reach. This remains non-SDF, non-timing simulation.
- The remaining compile blocker was a single generated 301M `VGemmini___024root__7636__Slow.cpp` file containing one huge `eval_stl__0` function. Verilator `--output-split` did not split inside that function. A local post-Verilator split into 32 helper C++ files, while preserving the original `eval_stl` wrapper and adding const-pool extern declarations, allowed `make -j64` to complete.
- Two replay harness bugs were fixed before the current pause: run-stage executable/compare paths now resolve to absolute paths before `cwd=out_dir`, and CSV header parsing strips a trailing CR from CRLF files.

Current replay/runtime status and mismatch interpretation:

- No Phase1b replay process should be running while this note is current.
- Two partial compare files were retained for analysis: `gate_output_compare.preempted_21600s_timeout_risk.csv` reached about cycle 10048, and `gate_output_compare.interrupted_by_user_20260513.csv` reached about cycle 4648. Neither is a complete Phase1b result.
- The observed partial compare rows are almost entirely mismatches where payload outputs such as `auto_spad_id_out_a_bits_*`, `io_resp_bits_*`, and `io_ptw_0_req_bits_*` have RTL expected nonzero values while the gate model output is zero. In the sampled RTL vectors, the corresponding valid signals remain low throughout the observed window: `auto_spad_id_out_a_valid` first goes high only at cycle 313434, `io_cmd_valid` first goes high at cycle 301367, and `io_resp_valid` / `io_ptw_0_req_valid` never go high in the full extracted vector set.
- Therefore the current mismatch evidence should not be interpreted as a functional gate replay failure yet. It mainly shows that the initial harness compares invalid ready/valid payload bits unconditionally. The next replay attempt should add validity-aware compare masks, keep scalar control comparisons, skip invalid payload comparisons, and optionally suppress reset/idle payload logging.
- Runtime is now the long step: at the observed partial-run speed, a full 334378-cycle replay is likely more than six hours, and most meaningful Gemmini activity starts after about cycle 301k. Before rerunning, add progress logging and validity-aware compare filtering to reduce output I/O and make long runs diagnosable.

The intermediate run directories for earlier failed trials were cleaned before the next Phase1b `mvin_mvout` attempt when they were no longer useful. A current generated build tree may be retained for bounded retry/debug reuse. This entry must be revisited after the Phase1b `mvin_mvout` attempt finishes, then updated with the actual outcome and any selected parameter policy.

## 0.60a Phase1b narrowed handoff scope for mvin_mvout compare

Date: 2026-05-14.

User-confirmed scope update:

- Continue Phase1b only to complete `mvin_mvout` Gemmini gate-level boundary replay and validity-aware output compare.
- The immediate purpose is simple validation/evaluation of the Verilator gate-level boundary replay method by compare, including mismatch handling and triage.
- Gate VCD, SAIF, gate internal/instance activity CSV, standard-cell activity summary, and Stage 3 activity handoff are not current Phase1b deliverables.
- Stage 3 remains on the Stage 1 RTL activity / Cadence activity mapping route unless the active plan is explicitly expanded later.
- Existing mismatch evidence should be re-evaluated after the harness compares ready/valid payload fields only when semantically valid and reports skipped invalid-payload/x/z cases separately.

## 0.61 Phase 2 r17 routing postRoute AAE/RCDB abort and cts checkpoint recovery plan

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260512_r17_pgopen_resume_floorplan
```

Observed status:

- The PG-open floorplan-resume flow successfully completed `powerplan`, `placement`, and `cts`.
- `cts.enc` and `cts.enc.dat` were saved under the r17 Innovus data directory.
- `routeDesign -globalDetail` completed with `Number of fails = 0` and no M10 routing range expansion; routing remained configured as M2-M8.
- Final detail-route DRC before post-route optimization was not clean: `Total number of DRC violations = 13171`, dominated by `WidTbl` on M6/M7.
- The routing step then entered `optDesign -postRoute -setup` and aborted internally during AAE/RCDB post-route delay calculation.

Failure signature:

```text
Innovus terminated by internal (ABORT) error/signal
peThreadGroupIdMgr<ID, TLS>::getGroupId(): Assertion `m_numThreads < m_maxThreads' failed
Crashed in AAE on net spad/_acc_mems_0_io_adder_op1_14_0[28]
Currently issued term is spad/acc_mems_0_mem_mem_mem_0_ext/R0_data[476]
```

Classification:

- This is a Cadence Innovus internal post-route AAE/RCDB crash after detailed routing, not a Genus synthesis failure.
- It is associated with post-route timing/optimization on a fake SRAM output net.
- It is separate from the known ASAP7 M10 `IMPTR-2101` collateral issue and separate from PG-open classification.
- r17 is not an accepted Phase 2 result because `routing.enc`, routed DEF, routed Verilog, routed SDF, SPEF, GDS, and final post-route reports were not produced.

Selected next checkpoint:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260512_r17_pgopen_resume_floorplan/innovus/data/cts.enc
```

Reasoning:

- It is the latest valid Python-managed checkpoint before the failing routing step.
- It preserves the r17 powerplan, placement, CTS, fake SRAM macro placement, and PG-open evidence.
- Resuming from this checkpoint avoids rerunning floorplan, powerplan, placement, and CTS.
- The next retry must first save `routing.enc` immediately after `routeDesign` before any post-route optimization/reporting that could trigger the AAE/RCDB crash.

Planned script change before retry:

- Add a Python-managed routing-from-CTS recovery entry.
- Seed the selected `cts.enc` into a clean r18 run tag.
- Generate a routing Tcl that saves `routing.enc` immediately after `routeDesign -globalDetail`.
- Use single-analysis post-route reporting by default for this PG-open thermal proxy retry.
- Skip `optDesign -postRoute -setup` unless explicitly re-enabled, because r17 showed that stage can abort after successful detailed routing and before artifact export.

## 0.62 Phase 2 CTS-routing recovery script validation before r19 retry

Date: 2026-05-13.

Script change committed in nested `runs/cadence_startup` repo:

```text
2b1edfb Add CTS routing recovery flow
```

Validation run tag used for script generation only:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r18_route_from_cts_single
```

Validated command:

```text
--preflight --write-routing-scripts-from-cts
```

Validated source checkpoint:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260512_r17_pgopen_resume_floorplan/innovus/data/cts.enc
```

Script inspection result:

- `routing.tcl` sources the clean run tag's seeded `innovus/data/cts.enc` checkpoint.
- Routing is configured as M2-M8.
- `setAnalysisMode -analysisType single` is emitted for the r17 AAE/RCDB recovery route.
- `routeDesign -globalDetail` is followed immediately by `saveDesign .../innovus/data/routing.enc`.
- `optDesign -postRoute -setup` is skipped by default and can be restored only with `TP_STAGE2_ROUTE_RUN_POSTROUTE_OPT=true`.
- Post-route timing, area, power, DRC/connectivity, routed DEF, Verilog, SDF, SPEF, and GDS export commands remain in the generated routing Tcl.

Next heavy retry tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r19_route_from_cts_single_run
```

Acceptance boundary for the retry remains downgraded: this can only be accepted as `PG-open thermal proxy` evidence unless PG connectivity and routed DRC are clean. If post-route timing/export still crashes after `routing.enc` is saved, the next retry should recover from that routing checkpoint rather than rerunning detailed routing.

## 0.63 Phase 2 r19 interruption and 8-iteration CTS-route retry plan

Date: 2026-05-13.

Interrupted run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r19_route_from_cts_single_run
```

Observed status after session interruption/resume:

- The r19 Innovus process was still running in detailed routing after the agent session was interrupted.
- The run was still using the previous default `drouteEndIteration=20`, which no longer matches the user request to limit detailed routing to 8 iterations.
- No `innovus/data/routing.enc` was produced before the stop point.
- The only checkpoint present in r19 was `innovus/data/cts.enc`, which is the seeded copy of the r17 CTS checkpoint, not a new post-routing checkpoint.
- The stale r19 Innovus process was terminated before starting a new retry to avoid consuming license/runtime on a route that does not match the requested 8-iteration setting.

Selected recovery checkpoint for the next retry:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260512_r17_pgopen_resume_floorplan/innovus/data/cts.enc
```

Reasoning:

- r19 did not advance to a saved routing checkpoint.
- r19's `cts.enc` is only a copy of r17's CTS database.
- r17 `cts.enc` is therefore the latest canonical Python-managed implementation checkpoint before routing.
- The next retry should use a clean run tag and explicitly set `TP_STAGE2_DROUTE_END_ITERATION=8` so generated routing Tcl contains `setNanoRouteMode -quiet -drouteEndIteration 8`.

Planned retry tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r20_route_from_cts_single_droute8
```

The retry remains a downgraded `PG-open thermal proxy` route. DRC and PG connectivity must be reported as non-signoff limitations if nonzero.

## 0.64 Phase 2 r20 routing checkpoint saved but SDF export AAE abort

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r20_route_from_cts_single_droute8
```

Observed status:

- r20 resumed from the r17 CTS checkpoint and honored `TP_STAGE2_DROUTE_END_ITERATION=8`.
- `routeDesign -globalDetail` completed with `Number of fails = 0` and saved `innovus/data/routing.enc` immediately after routing.
- The final routeDesign DRC summary was not clean: `Total number of DRC violations = 11139`; after post-route wire spreading the saved database carried 13582 DRC markers, still dominated by `WidTbl` on M6/M7.
- `optDesign -postRoute -setup` was skipped as intended.
- `timeDesign -postRoute` completed before the crash and reported setup WNS `0.067 ns`, TNS `0.000 ns`, and 0 violating setup paths at the 5.000 ns / 200 MHz target.
- Routed DEF and routed Verilog were exported.
- `write_sdf` then triggered the same Cadence internal AAE/RCDB assertion family seen in r17, this time on `spad/_acc_mems_1_io_adder_op1_14_0[20]` driven by fake SRAM output `spad/acc_mems_1_mem_mem_mem_0_ext/R0_data[468]`.
- The SDF file present in r20 is zero bytes because the crash happened during SDF generation. SPEF, GDS, post-route DRC report, and post-route connectivity report were not produced.
- The crashed Innovus residual process was terminated after the log printed the internal abort summary.

Classification:

- r20 is useful as a routed checkpoint and partial artifact source, but is not an accepted Phase 2 proxy result because final SDF/SPEF/GDS/DRC/connectivity artifact gates are incomplete.
- The remaining blocker is post-route export/report robustness from a routed database, not placement/CTS/detail-route completion.
- The next retry should recover from r20 `routing.enc` rather than rerunning detail route.

Selected next checkpoint:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r20_route_from_cts_single_droute8/innovus/data/routing.enc
```

Planned recovery:

- Add a Python-managed export/report-only route from `routing.enc`.
- Generate DEF, routed Verilog, SDF, SPEF, DRC, connectivity, and GDS without rerunning routeDesign.
- Use a conservative SDF fallback first: `write_sdf <file> -interconn none -base_delay -view setup_view`, to test whether avoiding interconnect delay annotation bypasses the AAE/RCDB crash.
- Preserve the limitation explicitly if the only successful SDF is cell-only/no-interconnect; SPEF remains the routed parasitic handoff for interconnect evidence.

## 0.65 Phase 2 r21 export-only area/power report crash

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r21_export_from_routing_sdf_nointerconn
```

Observed status:

- r21 used the Python-managed export-from-routing path committed as nested `runs/cadence_startup` commit `853df34`.
- The script restored r20 `routing.enc` and did not rerun `routeDesign`.
- The generated Tcl used `write_sdf <file> -interconn none -base_delay -view setup_view`, but the run did not reach `defOut` or `write_sdf`.
- Innovus crashed immediately after `report_power -hierarchy all`, with `MEMPOOL-112` / internal SEGV: `Memory error: Thread number is greater than max number in mem_thread_create`.
- No new routed DEF/SDF/SPEF/GDS/DRC/connectivity artifacts were produced in r21.

Classification:

- r21 exposed a separate report-generation crash during export-only recovery.
- The existing r20 post-route area and power reports are already available, so rerunning area/power inside export-only recovery is unnecessary and risky.

Next retry:

- Reuse r20 `routing.enc` again.
- Set `TP_STAGE2_EXPORT_RUN_AREA_POWER=false` so export-only Tcl skips `report_area` and `report_power`.
- Preserve/copy r20 post-route timing/area/power reports into the new export run manifest after Innovus completes.
- Keep the SDF fallback `-interconn none -base_delay -view setup_view` for the next SDF test.

## 0.66 Phase 2 r22 SDF-only export crash and non-SDF export split plan

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r22_export_from_routing_no_reports_sdf_nointerconn
```

Observed status:

- r22 restored the r20 `routing.enc` checkpoint and did not rerun `routeDesign`.
- `TP_STAGE2_EXPORT_RUN_AREA_POWER=false` avoided the r21 area/power report crash.
- The run successfully exported routed DEF and routed Verilog before SDF generation.
- `write_sdf <file> -interconn none -base_delay -view setup_view` still triggered Innovus `MEMPOOL-112` / internal SEGV during SDF delay calculation.
- The r22 SDF file is zero bytes and is not usable.
- Because SDF was emitted before SPEF/GDS/DRC/connectivity in the export Tcl, SPEF, GDS, post-route DRC report, post-route connectivity report, and final export checkpoint were not reached.

Classification:

- The remaining primary blocker is Innovus SDF generation from the routed fake-SRAM design database.
- The failed SDF command still enters delay calculation even with `-interconn none -base_delay`, so this setting is not a sufficient workaround.
- DEF and routed Verilog export from the r20 routed checkpoint are viable.
- SDF must no longer block the other required routed physical artifacts.

Next retry plan:

- Add Python-managed switches to skip SDF or emit it after SPEF/GDS/DRC/connectivity.
- Run a clean r23 export-from-routing retry from the r20 `routing.enc` checkpoint with SDF skipped, area/power skipped, and no reroute.
- Target r23 artifacts: routed DEF, routed Verilog, SPEF, GDS, post-route DRC report, post-route connectivity report, and `export_routing.enc`.
- Preserve r20 post-route timing/area/power reports as the timing/area/power evidence for the routed checkpoint.
- After r23, handle SDF as a separate SDF-only recovery attempt or classify missing routed SDF as a Phase 2 blocker if Innovus continues to crash.

Planned r23 tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r23_export_from_routing_skip_sdf
```

## 0.67 Phase 2 r23 skip-SDF export reaches rcOut but needs explicit RC extraction

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r23_export_from_routing_skip_sdf
```

Observed status:

- r23 restored r20 `routing.enc` and did not rerun `routeDesign`.
- The generated Tcl skipped `write_sdf` as intended and avoided the r21/r22 SDF/report internal crashes.
- Routed DEF and routed Verilog were exported again.
- The run stopped at `rcOut -spef` with Innovus `IMPDC-495`: `Run RC extraction before invoking RC output command`.
- No SPEF, GDS, post-route DRC report, post-route connectivity report, or `export_routing.enc` was produced by r23.

Classification:

- r23 was a Tcl sequencing failure in export recovery, not a routing failure and not a new SDF crash.
- Earlier `write_sdf` attempts appear to have triggered delay/RC calculation before failing; when SDF is skipped, the flow must explicitly run Innovus native RC extraction before `rcOut`.

Next retry plan:

- Add Python-generated `setExtractRCMode -engine postRoute -effortLevel low` and `extractRC` before `rcOut` in routed artifact export.
- Keep SDF skipped and area/power skipped for the next retry so the only intended behavior change is explicit RC extraction before SPEF.
- Reuse the same r20 `routing.enc` checkpoint in a clean r24 run tag.

Planned r24 tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r24_export_from_routing_skip_sdf_extractrc
```

## 0.68 Phase 2 r24 extractRC effort-level retry needed

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r24_export_from_routing_skip_sdf_extractrc
```

Observed status:

- r24 restored r20 `routing.enc`, skipped SDF, and exported routed DEF/routed Verilog.
- The added `setExtractRCMode -engine postRoute -effortLevel low -localCpu 1` was rejected before `extractRC` ran.
- Innovus error: `IMPEXT-6192 Effort level 'low' for postRoute extraction mode is not allowed in current setup, as captable files are either ignored or not specified during multi-corner setup`.
- SPEF, GDS, DRC/connectivity reports, and `export_routing.enc` were therefore still not produced.

Classification:

- r24 is an RC extraction mode parameter issue, not a routing failure and not an SDF internal crash.
- The restored database log says postRoute extraction effort defaults to `medium` in this setup, so the recovery flow should use `medium` instead of `low`.

Next retry plan:

- Change Python flow default `TP_STAGE2_EXPORT_EXTRACT_RC_EFFORT` from `low` to `medium`.
- Reuse r20 `routing.enc` in a clean r25 run tag, still with SDF skipped and area/power skipped.

Planned r25 tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r25_export_from_routing_skip_sdf_extractrc_medium
```

## 0.69 Phase 2 r25 non-SDF physical artifact export complete; SDF blocker later waived

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r25_export_from_routing_skip_sdf_extractrc_medium
```

Observed status:

- r25 restored r20 `routing.enc` and did not rerun `routeDesign`.
- `write_sdf` was intentionally skipped.
- Native RC extraction with `setExtractRCMode -engine postRoute -effortLevel medium -localCpu 1` completed and `rcOut -spef` completed.
- The run produced routed DEF, routed Verilog, SPEF, GDS, post-route DRC report, post-route connectivity report, and `export_routing.enc`.
- Post-route timing/area/power reports were copied from the r20 routed checkpoint into the r25 report directory.
- Python artifact gate failed only because `routed_sdf` is missing, which was expected for this split-export retry.

Key artifact evidence:

```text
innovus/data/export_routing.enc
innovus/data/Gemmini.routed.def
innovus/data/Gemmini.routed.v
innovus/data/Gemmini.routed.spef
innovus/data/Gemmini.gds
innovus/reports/postRoute_timing/timing.rpt
innovus/reports/postRoute_area.rpt
innovus/reports/postRoute_power.rpt
innovus/reports/postRoute_drc.rpt
innovus/reports/postRoute_connectivity.rpt
```

Quality classification:

- At the time of this entry, r25 was not accepted complete Phase 2 because routed SDF was missing. This was superseded by the 0.72 user-approved routed-SDF waiver.
- r25 is useful as the current best `PG-open thermal proxy` physical artifact set.
- DRC remains open: `verify_drc` hit the 1000 violation error limit.
- Connectivity remains open: `verifyConnectivity -type all` hit 1000 total issues, including 158 special-wire connectivity problems and 842 dangling-wire problems on VDD/VSS-style special routes.
- GDS streamout warns that fake SRAM master cells `mem_0_ext` and `mem_ext` are not found in merged stdcell GDS collateral; this is expected for fake SRAM physical abstract handling and must be recorded as a limitation if GDS is used downstream.

Next retry plan:

- Do not rerun routing or non-SDF exports.
- Investigate Innovus `write_sdf` options for a minimal SDF-only retry from the routed/export checkpoint.
- This retry plan was later executed as r26; the resulting SDF blocker was superseded by the 0.72 user-approved routed-SDF waiver.

## 0.70 Phase 2 minimal SDF container retry plan

Date: 2026-05-13.

Context:

- r25 produced the non-SDF physical artifact set from the routed checkpoint.
- Prior Innovus SDF attempts with full SDF and with `-interconn none -base_delay -view setup_view` both triggered delay calculation and crashed with AAE/MEMPOOL internal errors.
- Innovus `write_sdf` documentation shows `-celltiming none` prevents cell delays and timing checks from being written, while `-interconn none` prevents INTERCONN delays from being written.

Classification:

- A `write_sdf -celltiming none -interconn none` output, if successful, is only a minimal routed SDF container and not a useful routed delay annotation.
- It must be labeled as a degraded SDF artifact. Timing evidence must remain the r20 post-route timing report plus the routed SPEF from r25.

Next retry plan:

- Run a clean r26 export-from-routing retry from r20 `routing.enc` with:
  - `TP_STAGE2_SDF_EXPORT_ARGS="-celltiming none -interconn none -view setup_view"`
  - `TP_STAGE2_EXPORT_RUN_AREA_POWER=false`
- Keep explicit medium-effort `extractRC` before SPEF so the run can still produce a full artifact bundle if the minimal SDF command succeeds.
- This minimal SDF retry later crashed as r26; the resulting SDF blocker was superseded by the 0.72 user-approved routed-SDF waiver.

Planned r26 tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r26_export_from_routing_min_sdf_container
```

## 0.71 Phase 2 r26 minimal SDF retry failed; routed SDF blocker later waived

Date: 2026-05-13.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r26_export_from_routing_min_sdf_container
```

Observed status:

- r26 restored r20 `routing.enc` and attempted `write_sdf` with `-celltiming none -interconn none -view setup_view`.
- Even this minimal SDF container attempt entered preRoute extraction and full delay calculation.
- Innovus failed with the same `MEMPOOL-112` / internal SEGV family seen in r22.
- The r26 `Gemmini.routed.sdf` file is zero bytes and is not usable.
- Because the crash occurs inside `write_sdf`, the run did not reach the already-proven r25 `extractRC`/SPEF/GDS/report export path.

Classification:

- At the time of this entry, routed SDF generation was the remaining Phase 2 blocker. This was superseded by the 0.72 user-approved routed-SDF waiver.
- Script-side options tried so far include normal SDF, `-interconn none -base_delay -view setup_view`, and `-celltiming none -interconn none -view setup_view`; all hit Innovus internal AAE/MEMPOOL/SEGV behavior on this routed fake-SRAM design database.
- At the time of this entry, r25 remained incomplete because the active artifact gate still required routed SDF. This was superseded by the 0.72 user-approved routed-SDF waiver.
- Genus SDF exists from r2, but it is not routed SDF and must not be substituted as accepted routed SDF without an explicit plan change.

Then-current best incomplete physical artifact run:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r25_export_from_routing_skip_sdf_extractrc_medium
```

Then-current blocker before the 0.72 waiver:

```text
Cadence Innovus 23.14 write_sdf crashes internally during delay calculation from the routed PG-open fake-SRAM Gemmini database; no nonzero routed SDF has been produced.
```

## 0.72 Phase 2 routed SDF waived for thermal-proxy handoff

Date: 2026-05-13.

Decision:

- The user approved directly skipping routed SDF for the current research target.
- r25 was then the selected Stage 2 handoff before the later r28 replacement under `PG-open / DRC-open / routed-SDF-waived thermal proxy` quality.
- No further Innovus `write_sdf` retry is required unless the active plan changes again.

Rationale:

- r20 produced the routed checkpoint and post-route timing evidence at the 5.000 ns / 200 MHz target.
- r25 produced the non-SDF routed physical artifact set: routed DEF, routed Verilog, SPEF, GDS, `export_routing.enc`, post-route DRC/connectivity reports, and copied post-route timing/area/power reports.
- Normal routed SDF, reduced `-interconn none -base_delay -view setup_view`, and minimal `-celltiming none -interconn none -view setup_view` all triggered Innovus internal AAE/MEMPOOL/SEGV behavior or zero-byte SDF output.
- Stage 1b is zero-delay Verilator replay and does not consume SDF timing.
- Stage 3/4 thermal-proxy work needs placement, routed netlist, SPEF/parasitic context, post-route timing/power evidence, and physical geometry; SDF timing simulation is not part of the current research claim.

Accepted degraded Stage 2 handoff:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r25_export_from_routing_skip_sdf_extractrc_medium/
```

Required labels and limits:

- Always label this handoff `PG-open`, `DRC-open`, and `routed-SDF-waived`.
- Do not claim routed-SDF-complete, timing-signoff, PG-clean, DRC-clean, IR/EM-clean, LVS-clean, or foundry/signoff-clean.
- Genus r2 SDF may be recorded only as mapped-stage context; it is not a routed SDF replacement.

## 0.73 Phase 2 routed-SDF waiver gate repair and r28 export plan

Date: 2026-05-13.

Context:

- The active plan now allows routed SDF to be skipped for the current thermal-proxy research target.
- The Python flow still treated `routed_sdf` as a hard artifact gate in `main.py` and in Innovus per-step expected artifacts.

Changes made before the next Cadence attempt:

- Updated the Python artifact gate so `TP_STAGE2_EXPORT_SDF=false` requires `innovus/reports/routed_sdf_waiver.md` instead of `Gemmini.routed.sdf`.
- Updated generated Innovus Tcl to write `routed_sdf_waiver.md` when SDF export is disabled.
- Updated prelaunch summary wording so artifact gates say routed SDF or routed-SDF waiver report.

Validation completed before heavy launch:

```text
source tools/env_gemmini_thermal.sh && python -m py_compile \
  runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py \
  runs/cadence_startup/manager/innovus/innovus_manager.py
```

Result: pass.

Script-only validation run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r27_sdf_waiver_gate_check
```

Result: `--preflight --write-export-scripts-from-routing` passed under the `thermal_placement` conda environment with `TP_STAGE2_EXPORT_SDF=false`. The generated `export_routing.tcl` skips `write_sdf`, writes `routed_sdf_waiver.md`, runs `extractRC`, exports SPEF, DRC/connectivity reports, GDS, and saves `export_routing.enc`.

Next Cadence attempt:

- Launch a clean export-only recovery from the r20 `routing.enc` checkpoint.
- Use a new run tag so the earlier script-only r27 directory remains diagnostic only.
- Planned tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived
```

Acceptance target for r28:

- routed DEF
- routed Verilog
- SPEF
- GDS
- `export_routing.enc`
- copied or regenerated post-route timing/area/power reports
- post-route DRC/connectivity reports
- `routed_sdf_waiver.md`
- explicit `PG-open / DRC-open / routed-SDF-waived thermal proxy` classification

## 0.74 Phase 2 r28 accepted degraded Cadence/full-ASAP7 handoff

Date: 2026-05-14.

Run tag:

```text
gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived
```

Observed status:

- r28 restored the r20 `routing.enc` checkpoint and did not rerun `routeDesign`.
- `TP_STAGE2_EXPORT_SDF=false` skipped `write_sdf` and generated `innovus/reports/routed_sdf_waiver.md`.
- Native RC extraction with `setExtractRCMode -engine postRoute -effortLevel medium -localCpu 1` completed.
- `rcOut -spef`, `verify_drc`, `verifyConnectivity`, `streamOut`, and `saveDesign export_routing.enc` completed.
- Python startup artifact gate passed with `ok=true` and `missing=[]`.
- The nested `runs/cadence_startup` source commit for the waiver gate repair is `14741e1 Accept routed SDF waiver in stage2 gates`.

Accepted degraded Stage 2 handoff:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/
```

Primary evidence:

```text
startup/innovus_export_from_routing_manifest.json
innovus/reports/export_routing_manifest.json
innovus/reports/routed_sdf_waiver.md
innovus/data/Gemmini.routed.def
innovus/data/Gemmini.routed.v
innovus/data/Gemmini.routed.spef
innovus/data/Gemmini.gds
innovus/data/export_routing.enc
innovus/reports/postRoute_timing/
innovus/reports/postRoute_area.rpt
innovus/reports/postRoute_power.rpt
innovus/reports/postRoute_drc.rpt
innovus/reports/postRoute_connectivity.rpt
```

Quality classification:

- Accepted only as `PG-open / DRC-open / routed-SDF-waived thermal proxy` for Stage 3/4 thermal research.
- Not PG-clean, DRC-clean, routed-SDF-complete, timing-signoff, IR/EM-clean, LVS-clean, or foundry/signoff-clean.
- DRC remains open: `verify_drc` stopped at the 1000 violation report limit.
- Connectivity remains open: 158 special-wire connectivity problems and 842 dangling-wire problems were reported before the 1000 issue limit.
- GDS streamOut still warns that fake SRAM masters `mem_0_ext` and `mem_ext` are not found in merged stdcell GDS collateral.

Follow-up:

- Stage 2 is complete for the current downgraded research target.
- Stage 3/4 may consume r28 only with the above non-signoff labels and limitations.

## 0.75 Documentation synchronized to r28 downgraded Phase 2 handoff standard

Date: 2026-05-14.

The active documentation has been checked for residual wording that could imply the old strict/signoff-clean Stage 2 standard still applies. Current active Phase 2 acceptance is the user-approved r28 Cadence/full-ASAP7 `PG-open / DRC-open / routed-SDF-waived thermal proxy` handoff, not PG-clean, DRC-clean, routed-SDF-complete, timing-signoff, IR/EM-clean, LVS-clean, foundry-clean, or strict signoff closure.

The current accepted artifact folder is:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/
```

Some current Stage 0/1/2 path components still contain `__signoff` or run names created before the Phase 2 quality downgrade. These names are retained historical labels and intermediate-development paths. Do not delete, rename, or reject those artifacts only because the path contains `signoff`; instead, read the current quality label from the latest Phase 2 handoff report and active plan.

Updated docs in this cleanup include `AGENTS.md`, `docs/README.md`, `docs/phase0tophase4_cadence_asap7_plan.md`, `docs/agent_command_reference.md`, `docs/agent_task_checklist.md`, `docs/agent_onboarding.md`, `docs/gemmini_thermal_environment_setup.md`, and the Stage 2 report index/legacy report notes.

## 0.60b Phase1b validity-aware compare harness repair plan

2026-05-14 update before the next Phase1b retry: the `mvin_mvout` gate replay harness is being changed from unconditional output comparison to validity-aware comparison. The planned script-only change is in `scripts/phase1b_run_gate_boundary_replay.py`; it does not modify Chipyard/Gemmini RTL, the r2 `Gemmini-mapped.v`, or any Cadence Stage 2 artifact.

Planned compare policy for the next smoke:

- Compare valid/ready/control-style output ports every cycle when the RTL expected value is deterministic `0/1`.
- Compare output payload fields named with `_bits` only when their same-channel RTL expected `_valid` output is known `1`.
- Count RTL expected x/z skips separately from invalid-payload skips.
- Keep mismatch CSV bounded so invalid or repetitive payload rows cannot flood the report.
- Emit progress logging plus `replay_summary.json` and Markdown summaries with coverage, skip counts, mismatch count, first mismatch cycle, and elapsed runtime.
- Reuse the existing successful `VGemmini` build tree by recompiling/relinking only the generated C++ harness before the smoke.

Next validation step: run a short `mvin_mvout` smoke with the repaired harness and `--max-cycles` before attempting a longer replay.

## 0.60c Phase1b validity-aware compare smoke result

2026-05-14 result for the repaired `mvin_mvout` compare harness: a 64-cycle smoke reused the existing successful `VGemmini` build tree and recompiled/relinked only `tb_phase1b_gemmini.cpp` with `make -j64 CXX=clang++ LINK=clang++`. No gate VCD, SAIF, activity CSV, full-SoC gate simulation, or Stage 3 handoff artifact was generated.

Smoke command shape: `phase1b_run_gate_boundary_replay.py --max-cycles 64 --skip-build-if-exists --relink-if-build-exists --max-mismatch-rows 1000 --progress-interval-cycles 16` with the existing r2 `Gemmini-mapped.v`, referenced ASAP7 cells plus UDP primitives, and simulation-only fake SRAM models.

Smoke summary:

- `cycles_run=64`
- `output_ports_total=19`
- `control_output_ports=7`
- `payload_output_ports=12`
- `compared_values=448`
- `skipped_invalid_payload_values=768`
- `skipped_xz_values=0`
- `mismatches=0`
- `elapsed_sec=6.97276`

Archived smoke evidence in the Phase1b output directory uses suffix `.smoke64_validmask_20260514`. This smoke validates that the old reset/idle payload mismatch flood was a harness artifact for the early window. It does not yet prove full `mvin_mvout` gate replay equivalence, because the known first meaningful output-valid events are much later in the vector set. Next step: run a longer/full bounded replay with the same validity-aware harness and classify any remaining mismatches by ready/valid semantics, SRAM model behavior, reset/warmup, X/2-state behavior, port mapping, cycle alignment, and Verilator zero-delay semantics.

## 0.60d Phase1b full replay attempt stopped for runtime-risk calibration

2026-05-14 full-vector `mvin_mvout` replay attempt was launched with `--max-cycles 334378`, the validity-aware harness, existing `VGemmini`, no gate VCD/SAIF/activity export, `--max-mismatch-rows 20000`, and `--progress-interval-cycles 10000`. Required inputs existed and the run stayed within Gemmini-only boundary replay scope.

Runtime observation before stopping: the `VGemmini` process was active at about one CPU and `gate_replay_run.log` contained only the command line after several minutes, meaning the run had not reached the first 10k-cycle progress point. This is consistent with the earlier 2026-05-13 partial replay reaching only about cycle 10048 within a 21600 s timeout-risk window. Since the first meaningful output-valid region is around cycle 313434, waiting for the full-vector run is not a practical way to finish Phase1b in the current turn.

Judgment change before the next attempt: stop this full attempt, preserve the repaired smoke evidence, and switch to a bounded runtime-calibration/debug route. The next attempt should use smaller `--max-cycles` and a shorter progress interval to quantify current cycles/sec, then use offline analysis of the already extracted RTL vectors and any bounded gate replay evidence to decide whether the Verilator zero-delay boundary replay method is feasible enough or blocked by runtime before reaching the output-valid payload window.

## 0.60e Phase1b 256-cycle runtime calibration

2026-05-14 bounded calibration with the repaired validity-aware harness completed `--max-cycles 256` using the existing `VGemmini` executable, no VCD/SAIF/activity export, and progress interval 64. Evidence was archived in the Phase1b output directory with suffix `.calib256_validmask_20260514`.

Calibration summary:

- `cycles_run=256`
- `elapsed_sec=19.7056`
- effective rate about `13.0 cycles/sec`
- `compared_values=1792` across 7 non-payload outputs
- `skipped_invalid_payload_values=3072` across 12 payload outputs whose corresponding output valid was low
- `skipped_xz_values=0`
- `mismatches=0`

Runtime implication: reaching the first `auto_spad_id_out_a_valid` event near cycle 313434 is expected to take roughly 6.7 hours at this measured rate; the full 334378-cycle vector is expected to take about 7.1 hours, within the current 43200 s run timeout but too expensive for repeated debug loops. Next attempt is a full-vector replay with the same harness and no activity handoff artifacts. If it fails or times out, preserve the evidence and classify the blocker before retrying.

## 0.60f Phase1b full mvin_mvout validity-aware replay result

2026-05-14 full `mvin_mvout` Gemmini-only boundary replay completed with the repaired validity-aware compare harness. No full-SoC gate simulation, OS/WS gate replay, gate VCD, SAIF, activity CSV, standard-cell activity summary, or Stage 3 gate-activity handoff was generated.

Full replay result:

- `cycles_run=334377`
- `elapsed_sec=36216.7`
- `output_ports_total=19`
- `control_output_ports=7`
- `payload_output_ports=12`
- `compared_values=2342687`
- `skipped_invalid_payload_values=4010476`
- `skipped_xz_values=0`
- `mismatches=146`
- `first_mismatch_cycle=313434`
- mismatch rows written/suppressed: `146 / 0`

The old reset/idle mismatch flood is fixed: invalid payload rows are counted separately instead of being reported as mismatches. All full-run mismatches are concentrated on `auto_spad_id_out_a_bits_address`; other ready/valid/control outputs and other valid payload fields compare cleanly. The valid window has 256 valid rows and ready is high in the inspected valid rows. The address mismatch is mostly `actual = expected + 0x10`, and many actual values match the next-cycle RTL expected address.

Current triage judgment: the full Phase1b run is method-informative but not a strict functional pass. The remaining likely blocker is cycle-alignment / Verilator zero-delay boundary sampling semantics for the TileLink A address output. SRAM model, reset/warmup, x/z, and gross port mapping issues are less supported by the evidence but not formally closed by a timing-accurate simulator. Report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/phase1b_mvin_mvout_gate_boundary_replay_20260514.md`; detailed triage: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/mismatch_triage_report.md`.

## 0.60g Phase1b TL-A address shifted-compare follow-up and disposition

2026-05-14 follow-up requested by the user: run offline shifted compare and a local TL-A valid-window table only, without rerunning Verilator or modifying the replay method.

Evidence generated under the existing ignored Phase1b run directory:

- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/alignment_check_20260514_shifted_compare/shifted_compare_summary.md`
- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/alignment_check_20260514_shifted_compare/tl_a_address_window_313430_313830.csv`

Important method note: the Phase1b directory does not contain a complete `gate_outputs.csv`; the available full result is the mismatch-only `gate_output_compare.csv.full_validmask_20260514`. The shifted compare therefore reconstructs `auto_spad_id_out_a_bits_address` on valid non-mismatch rows as `actual == expected@N`, while mismatch rows use the recorded gate `actual` value. This is sufficient to classify the existing mismatch pattern without rerunning Verilator, but it is not a new gate simulation.

Shifted-compare result for `auto_spad_id_out_a_bits_address` over the 256 rows where `auto_spad_id_out_a_valid=1`:

- shift `-1`, gate `N` vs RTL expected `N-1`: `256 / 256` mismatches.
- shift `0`, gate `N` vs RTL expected `N`: `146 / 256` mismatches, reproducing the full replay compare.
- shift `+1`, gate `N` vs RTL expected `N+1`: `171 / 256` mismatches overall, or `133 / 218` mismatches when the shifted expected row is also valid.

Local window inspection around cycles `313430..313830` shows that some valid bursts behave like a one-beat lead: for example `313434..313448` and `313802..313816` have gate address equal to the next RTL expected address, while the final valid beat in those bursts realigns to shift-0 match. Therefore the issue is not a simple global one-cycle offset; it is better described as burst-local TL-A address beat alignment mismatch in the current zero-delay boundary replay compare.

User disposition recorded 2026-05-14: the root cause is not fully understood. Because the affected evidence is confined to 146 TL-A address payload rows out of a 334377-cycle replay, and because the affected time-scale share is extremely low relative to the thermal simulation horizon, the user classifies the issue as unlikely to significantly affect final thermal simulation results. Do not repeatedly revisit or deepen this issue by default in later work. Preserve the limitation in reports as a non-clean Phase1b gate replay compare, but proceed without treating this TL-A address mismatch as a blocker unless new evidence shows broader functional/activity impact or the user explicitly asks to reopen it.

## 0.60h Formal Phase1b r28 gate-SAIF handoff plan decision

Date: 2026-05-15.

The user replaced the temporary Phase1b `mvin_mvout` compare-feasibility scope with a formal Phase1b gate-SAIF handoff scope for all three fixed workloads. The old r2 `mvin_mvout` compare replay directory remains historical validation only:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/
```

The old report has been moved into that directory:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/phase1b_mvin_mvout_gate_boundary_replay_20260514.md
```

The old validation result is not a Phase3 handoff artifact and must not be reused as the formal r28 build cache. The old TL-A address mismatch remains documented but is not a blocker for the new no-compare SAIF flow.

Formal Phase1b decisions confirmed by the user:

- Continue Gemmini-only boundary replay; do not run full-SoC gate simulation.
- Produce one raw Verilator gate SAIF per workload for Phase3: `mvin_mvout`, `tiled_matmul_ws`, and `tiled_matmul_os`.
- Do not perform output compare in the formal flow; do not generate mismatch CSV/report.
- Use r28 accepted Stage2 routed/export Verilog as primary netlist: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v`.
- Do not fallback to r2 unless the user first confirms after a stop-and-report.
- Regenerate referenced-cell-only ASAP7 Verilog from r28 and include required UDP primitives; do not assume the old r2 referenced-cell set is enough.
- New formal output directory is `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/`; if it exists and is non-empty, stop by default.
- Build one shared r28 executable and run smoke plus formal workloads with that executable.
- Formal workload order is `mvin_mvout -> tiled_matmul_ws -> tiled_matmul_os`, one process at a time.
- Use Stage1 selected windows without refinement: `mvin_mvout` `[66875550, 601879950)`, `tiled_matmul_ws` `[1072392550, 3753373925)`, `tiled_matmul_os` `[9272956950, 10303285500)` ps.
- Extract inputs-only boundary vectors for each workload from `start_ps=0` to that workload's `trace_end_ps`; retain boundary vectors and manifests.
- Do one top-port mapping smoke with `mvin_mvout` RTL VCD; per-workload signal-map files may still be retained.
- Use direct Verilator SAIF: `--trace-saif`, fixed `--trace-depth 9`, no default gate VCD.
- Raw SAIF hierarchy is Verilator `Gemmini` top-rooted; Phase3 must perform Cadence `read_saif` scope/instance mapping and annotation coverage reporting.
- Fixed build parameters: `--verilate-jobs 192`, `--threads 16`, `make -j192 CXX=clang++ LINK=clang++`, `--compiler clang`, `--no-timing`, `-CFLAGS "-O0 -g0"`, `--output-split 200 --output-split-cfuncs 20 --output-split-ctrace 20`.
- Do not use `--hierarchical` by default. If non-hierarchical build fails or becomes impractical, stop and ask before trying it.
- If generated C++ in the new build tree exceeds `128 MiB`, split it into 32 helper C++ files before make; automatic split is allowed, and manual split inside the new run directory is allowed if automatic split is unsafe.
- Use current simulation-only fake SRAM behavioral models; do not introduce real SRAM macro behavior models.
- SAIF smoke uses `mvin_mvout` active-window start for 100 cycles: `[66875550, 67075550)` ps, stored under `smoke_mvin_mvout_100cyc/`; smoke is excluded from Phase3 handoff.
- Long Verilator front-end, make, and replay tasks use startup checks, then about 20-minute wall-clock monitoring; do not proactively interrupt without clear error, exit, resource anomaly, or user instruction.
- No disk-space preflight gate is required per user direction.

Documentation update target after this decision set: active plan, docs README, command reference, task checklist, tool inventory, issue log, and `scripts/README_phase1b.md`. Environment setup is not updated because no new environment variable or dependency was added.

## 0.60i Formal Phase1b r28 smoke build attempt 1: SAIF dump timestamp overload

Date: 2026-05-15.

The first formal Phase1b r28 `mvin_mvout` 100-cycle smoke attempt was launched with the confirmed fixed policy: `--verilate-jobs 192`, Verilator model `--threads 16`, `make -j192 CXX=clang++ LINK=clang++`, `--compiler clang`, `--no-timing`, direct `--trace-saif`, `--trace-depth 9`, and split parameters `--output-split 200 --output-split-cfuncs 20 --output-split-ctrace 20`.

Outcome: Verilator frontend/elaboration completed successfully on r28 and generated the build tree. Evidence from `build.log` reports Verilator 5.047, 371.603 MB sources, 424 modules, 328935 generated C++ files, and frontend wall time 1259.133 s. The attempt failed only during C++ harness compilation because `VerilatedSaifC::dump(long long)` was ambiguous between the available `uint64_t`, `double`, `uint32_t`, and `int` overloads.

Fix before retry: cast all SAIF dump timestamps in the generated harness to `uint64_t`. The r28 Verilator build tree is preserved under the new Phase1b run directory and can be reused for a make-only retry; there is no evidence requiring fallback to r2 or `--hierarchical`.

## 0.60j Formal Phase1b r28 make-only retry 1: make segfault after object compilation

Date: 2026-05-15.

After fixing the generated SAIF harness timestamp casts, the preserved r28 Verilator build tree was retried with the user-required command policy `make -j192 CXX=clang++ LINK=clang++`. The retry did not report a new C++ compile error. It progressed through the generated fast, trace, and slow C++ compilation and reached approximately 328939 object files in the r28 build directory.

Outcome: `make` itself exited with segmentation fault at the end of the run, returning 139, before producing `verilator_build/VGemmini`. The log does not identify a specific failing generated C++ file or link error. This is currently classified as a tool/make stability failure on an extremely large non-hierarchical r28 SAIF trace build tree, not as a Gemmini/r28 netlist elaboration failure. No fallback to r2 or `--hierarchical` is justified by this evidence.

Next action: preserve the build tree and run an incremental `make -j192 CXX=clang++ LINK=clang++` retry on the same tree, because most object files already exist and the fixed policy requires `-j192`. If repeated make segfaults persist before link, reassess whether a safer manual build completion route is needed while keeping the user-confirmed build policy constraints visible in the documentation.

## 0.60k Formal Phase1b r28 make-only retry 2: repeated make parser/setup segfault

Date: 2026-05-15.

A second incremental `make -j192 CXX=clang++ LINK=clang++` retry was run on the same preserved r28 build tree after the first make segfault. The retry entered the Verilator build directory and immediately segfaulted before launching a new compile or link command. The build directory already contained approximately 328939 object files, and no `VGemmini` executable had been produced.

Current classification: repeated GNU make instability while handling the extremely large non-hierarchical r28 direct-SAIF generated build graph, after object compilation is effectively complete. This is still not evidence of r28 netlist elaboration failure, SRAM model failure, or a need to fallback to r2 or enable `--hierarchical`.

Next action: manually perform the same build tail that Verilator's makefile would perform: archive generated `VGemmini*.o` objects into `VGemmini__ALL.a` and link `tb_phase1b_gate_saif.o`, Verilator runtime objects, and the archive with `clang++` plus the Verilator thread libraries. This manual tail stays inside the new Phase1b build directory and does not modify r28 or other external tool artifacts.

## 0.60l Formal Phase1b r28 object completeness check after make segfault

Date: 2026-05-15.

Before continuing the manual build tail, the r28 Verilator build tree was checked against `VGemmini_classes.mk`. Result:

- expected generated objects from `VM_CLASSES_FAST`, `VM_CLASSES_SLOW`, `VM_SUPPORT_FAST`, and `VM_SUPPORT_SLOW`: 328935
- existing generated `VGemmini*.o` objects: 328935
- missing generated objects: 0
- extra generated objects: 0
- required global runtime objects present: `verilated.o`, `verilated_saif_c.o`, `verilated_threads.o`
- required user harness object present: `tb_phase1b_gate_saif.o`
- executable present before manual link: no

Evidence: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/build/object_completeness_check_20260515.json`. The earlier partially-created manual archive was renamed to `VGemmini__ALL.a.partial_before_obj_check_20260515` and is not treated as a usable build product.

Next action: proceed with the manual archive/link tail using the complete object set.

## 0.60m Formal Phase1b r28 manual archive/link completion

Date: 2026-05-15.

The manual archive/link tail was completed after the user requested confirming `.o` completeness before trusting the workaround. The verified pre-link object set remained complete: 328935 expected generated `VGemmini*.o` objects, 328935 present, 0 missing, 0 extra, plus required `verilated.o`, `verilated_saif_c.o`, `verilated_threads.o`, and `tb_phase1b_gate_saif.o`. Evidence: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/build/object_completeness_check_20260515.json`.

Manual tail result:

- archive command: `find . -maxdepth 1 -type f -name 'VGemmini*.o' -printf '%f\0' | xargs -0 -n 2000 ar -rc VGemmini__ALL.a`
- archive index command: `ar -s VGemmini__ALL.a`
- link command: `clang++ tb_phase1b_gate_saif.o verilated.o verilated_saif_c.o verilated_threads.o VGemmini__ALL.a -pthread -lpthread -latomic -o VGemmini`
- manual link return code: 0
- archive: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/build/verilator_build/VGemmini__ALL.a`, 4347158298 bytes
- executable: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/build/verilator_build/VGemmini`, 1563430560 bytes
- completion manifest: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/build/manual_link_completion_20260515.json`

Classification: the confirmed issue was GNU make instability on the very large non-hierarchical r28 direct-SAIF build graph after object compilation, not a Verilator frontend elaboration failure, r28 netlist failure, SRAM model failure, or evidence requiring r2 fallback / `--hierarchical`. The mitigation is to use the user-required `make -j192 CXX=clang++ LINK=clang++` through object compilation, then, only after verifying all expected `.o` files exist, manually perform the archive/index/link tail inside the new Phase1b build directory.

The shared r28 executable is now available for the no-compare smoke and formal workload replays. The formal flow still has not completed until smoke and all three workload SAIFs are generated and listed in the handoff manifest.

## 0.60n Formal Phase1b smoke attempt 1 after manual link: global max-cycle truncation

Date: 2026-05-15.

After the shared r28 `VGemmini` executable was produced, the first no-compare smoke replay reused the executable with `--skip-build-if-exists`, but failed with return code 3 because the smoke orchestration passed `--max-cycles 100` while boundary vectors started at `time_ps=0`. The replay therefore stopped at `last_time_ps=201000`, far before the requested trace window `[66875550, 67075550)`, and reported `trace_enabled_cycles=0`. This was a smoke orchestration bug, not a build/link failure or r28 replay failure.

Invalid smoke evidence was preserved under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/smoke_mvin_mvout_100cyc/failed_global_max_cycles_20260515/`.

Fix before retry: smoke still uses the 100-cycle active trace window, but replay must warm up from `time_ps=0` to the trace window and must not cap total simulation at the first 100 global cycles. The orchestrator now treats smoke `max_cycles` as optional and leaves it unset for this warmup smoke.

## 0.60o Formal Phase1b smoke success after warmup fix

Date: 2026-05-15.

The corrected no-compare `mvin_mvout` smoke reused the completed r28 `VGemmini` executable and warmed up from `time_ps=0` while enabling SAIF trace only for `[66875550, 67075550)` ps. Result:

- run return code: 0
- cycles run: 33537
- rows seen: 33538
- first trace cycle/time: 33438 / 66877000 ps
- last trace cycle/time: 33537 / 67075000 ps
- trace enabled cycles: 100
- elapsed: 484.206 s
- SAIF bytes: 445600062
- smoke SAIF: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/smoke_mvin_mvout_100cyc/mvin_mvout.gate.saif`

This validates the harness executable, direct Verilator SAIF API, trace-window gating, and non-empty SAIF generation. Smoke remains excluded from the Phase3 handoff manifest. Next action: run formal workloads one at a time, starting with `mvin_mvout`, using the same shared executable and no output compare.

## 0.60p Formal Phase1b concurrent replay preflight preparation

Date: 2026-05-15.

The previous formal `mvin_mvout` replay was found no longer running before completion. It had entered the trace window but did not write `[finish]`, `replay_summary.json`, or a non-empty SAIF. The invalid replay outputs were moved out of the active `mvin_mvout/` handoff path into `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/mvin_mvout/failed_interrupted_replay_20260515/`. The parent `mvin_mvout/` directory now retains only reusable extraction inputs/provenance for the rerun.

Per user direction, the next replay launch is prepared for three simultaneous formal workload processes rather than the earlier one-at-a-time execution policy. No replay was started during this preparation step. Preparation completed:

- shared executable exists: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/build/verilator_build/VGemmini`
- `mvin_mvout` vectors ready: 357052189 bytes, trace `[66875550, 601879950)` ps
- `tiled_matmul_ws` vectors ready: 2229717252 bytes, trace `[1072392550, 3753373925)` ps
- `tiled_matmul_os` vectors ready: 6123791579 bytes, trace `[9272956950, 10303285500)` ps
- no existing formal replay SAIF, replay summary, or gate activity manifest remains in the three active workload directories
- launch script prepared but not executed: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/launch_phase1b_concurrent_replays_20260515.sh`
- preflight evidence: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/phase1b_concurrent_replay_preflight_20260515.json` and `.md`

Concurrency safety fix: `scripts/phase1b_run_gate_saif_replay.py` now checks `--skip-build-if-exists` before generating the shared harness C++ file. This prevents three concurrent replay-only processes from racing on `build/tb_phase1b_gate_saif.cpp`; the shared r28 executable remains read-only for the replay launches.

## 0.60q Phase1b acceleration attempt plan: harness-only binary boundary vectors

Date: 2026-05-15.

The user approved a Phase1b acceleration attempt for formal r28 gate-SAIF replay. The attempt is confined to `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/accelerate/` and is not yet the default Phase1b method.

Confirmed plan:

- do not rerun Verilator frontend;
- do not modify r28 `Gemmini.routed.v`, Stage2 Cadence artifacts, or Chipyard/Gemmini RTL;
- do not use `--hierarchical` or fallback to r2;
- do not reduce `--trace-depth 9` or the per-cycle SAIF dump policy;
- do not perform output compare or mismatch reporting;
- do not interrupt any existing unoptimized `VGemmini` or mainline Phase1b process;
- copy completed mainline inputs into `accelerate/<workload>/` using ordinary file copies;
- convert inputs-only CSV vectors to strict 2-state fixed little-endian packed binary rows with layout and SHA256 manifests;
- compile only a new binary-input harness and relink `accelerate/build/VGemmini_accelerate` against the existing r28 `VGemmini__ALL.a` and Verilator runtime objects;
- run one binary `smoke_mvin_mvout_100cyc` first;
- after smoke success, run the three formal accelerated workloads in parallel and let independent failures report per-workload without terminating other runs;
- ask the user after smoke/runtime evidence before changing the main Phase1b method to use the accelerated route.

Run-local acceleration docs were created under `phase1b_gate_saif_r28_20260515/accelerate/docs/`.

## 0.60r Phase1b acceleration binary smoke success

Date: 2026-05-15.

The harness-only binary/preparsed acceleration route completed its first smoke under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/accelerate/smoke_mvin_mvout_100cyc/`.

Implemented scripts:

- `scripts/phase1b_convert_boundary_vectors_to_binary_acceleration.py`
- `scripts/phase1b_run_gate_saif_binary_replay_acceleration.py`

Smoke evidence:

- copied mainline smoke inputs into `accelerate/smoke_mvin_mvout_100cyc/`;
- binary conversion succeeded: 33538 rows, 1120 bytes/row;
- harness-only relink succeeded without Verilator frontend rerun and without generated-object recompilation;
- accelerated executable: `accelerate/build/VGemmini_accelerate`;
- replay return code: 0;
- cycles run: 33537;
- trace enabled cycles: 100;
- first/last trace time: 66877000 / 67075000 ps;
- elapsed: 610.023 s;
- SAIF bytes: 445600062.

The smoke ran concurrently with three unoptimized mainline `VGemmini` formal replays, so elapsed time is not a clean standalone performance baseline. The result validates binary layout, strict input parsing, harness-only relink, progress logging, unchanged direct-SAIF policy, and non-empty SAIF generation. Next action: copy/convert the three formal workload inputs in parallel and run accelerated formal replays in parallel.

## 0.60s Phase1b acceleration formal input binary conversion complete

Date: 2026-05-15.

After binary smoke success, the formal workload inputs were copied into `phase1b_gate_saif_r28_20260515/accelerate/<workload>/` and converted in parallel. Results:

| workload | rows | row bytes | binary bytes | conversion elapsed sec |
| --- | ---: | ---: | ---: | ---: |
| `mvin_mvout` | 300940 | 1120 | 337052848 | 31.816 |
| `tiled_matmul_ws` | 1876687 | 1120 | 2101889488 | 197.735 |
| `tiled_matmul_os` | 5151643 | 1120 | 5769840208 | 548.200 |

Next action: launch the three accelerated formal replay processes in parallel using `accelerate/build/VGemmini_accelerate`. Existing unoptimized mainline `VGemmini` processes remain running and must not be interrupted.

## 0.60t Phase3 mvin_mvout-only bring-up scope and live Phase1b replay status

Date: 2026-05-16.

After repository handoff review, current Phase1b/Phase3 status is:

- Mainline formal `mvin_mvout` r28 gate SAIF completed with non-empty SAIF, `replay_summary.json`, `gate_activity_manifest.json`, and `phase3_consumable=true`; it is the only current Phase3 bring-up input candidate.
- Mainline formal `tiled_matmul_ws` and `tiled_matmul_os` `VGemmini` replay processes are still running and must not be interrupted. Their active SAIF files are currently 0 bytes and they do not yet have complete replay summaries/manifests, so they are not Phase3 handoff inputs.
- Accelerated `mvin_mvout`, `tiled_matmul_ws`, and `tiled_matmul_os` `VGemmini_accelerate` processes are also still running and must not be interrupted. Until each accelerated run writes a non-empty SAIF plus complete summary/manifest and the method is explicitly adopted, accelerated outputs are not the default Phase3 handoff method.
- Smoke SAIF, old r2 compare validation, 0-byte SAIF placeholders, and directories missing `replay_summary.json` or `gate_activity_manifest.json` remain excluded from Phase3 handoff.

User-confirmed Phase3 scope: start development with single-workload `mvin_mvout` bring-up only. Phase3 must label results non-signoff, consume r28 `PG-open / DRC-open / routed-SDF-waived thermal proxy` physical data, use Phase1b SAIF only as Verilator zero-delay activity, and perform Cadence `read_saif` scope/instance mapping plus annotation coverage reporting before treating activity as usable power input.

Documentation action: `docs/phase0tophase4_cadence_asap7_plan.md` was updated to remove the stale Stage 1b/Stage 3 contradiction that said Stage 1b was not a Stage 3 activity handoff, and `docs/README.md` was updated with the current mvin-only Phase3 bring-up status.

## 0.60u Phase3 mvin_mvout output directory decision

Date: 2026-05-16.

User confirmed the Phase3 `mvin_mvout` single-workload bring-up output directory:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/
```

This path is now the fixed output root for the initial Phase3 development pass. It should consume only the completed mainline formal `mvin_mvout` r28 gate SAIF and the accepted r28 Cadence/full-ASAP7 physical handoff. It must not consume still-running WS/OS or accelerated replay placeholders, and the running replay processes must not be interrupted.

## 0.60v Phase3 mvin_mvout preflight-first entry decision

Date: 2026-05-16.

User confirmed the first Phase3 `mvin_mvout` bring-up step should be a read-only preflight manifest, before launching Cadence or developing the power run itself. The planned output files are:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_manifest.json
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_report.md
```

The preflight must check the completed mainline `mvin_mvout` Phase1b gate SAIF and manifest, accepted r28 Cadence/full-ASAP7 physical artifacts, non-signoff labels, and excluded WS/OS/accelerated placeholders. It must not launch Cadence, modify Stage2 artifacts, modify Phase1b artifacts, or interrupt running replay processes.

2026-05-16 doc-edit retry note: the first attempt to insert the Phase3 preflight command into `docs/agent_command_reference.md` failed because the `perl -0pi` substitution delimiter was malformed. No command-reference content was changed by that failed substitution. Retrying with a safer marker-based insertion before running the preflight script.

## 0.60w Phase3 mvin_mvout read-only preflight result

Date: 2026-05-16.

Implemented and ran the read-only Phase3 `mvin_mvout` preflight entry:

```bash
source tools/env_gemmini_thermal.sh
python scripts/phase3_mvin_mvout_preflight.py
```

Validation:

- `python -m py_compile scripts/phase3_mvin_mvout_preflight.py` passed in the `thermal_placement` conda environment.
- Preflight completed with status `pass_with_warnings`.
- No Cadence tool was launched.
- No Stage2 physical artifact, Phase1b artifact, Chipyard/Gemmini RTL, or running replay process was modified or interrupted.
- Completed mainline `mvin_mvout` SAIF is accepted for Phase3 bring-up: 457660905 bytes, `phase3_consumable=true`, replay return code 0, 267502 trace-enabled cycles.
- Required r28 artifacts were present and non-empty: routed DEF, routed Verilog, SPEF, GDS, `cts.enc`, `routing.enc`, `export_routing.enc`, post-route power/area/DRC/connectivity/timing reports, and routed-SDF waiver.
- Excluded inputs remain excluded: smoke SAIF, old r2 compare validation, mainline WS/OS placeholders, and accelerated formal placeholders.

Warning:

- The global `phase1b_gate_saif_handoff_manifest.json` still has no `formal_workloads`; the preflight therefore uses the per-workload `mvin_mvout/gate_activity_manifest.json` as the current Phase3 bring-up source. This is acceptable for the user-confirmed mvin-only bring-up, but the global Phase1b handoff manifest should be regenerated or updated after all formal replays complete.

Outputs:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_manifest.json
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_report.md
```

2026-05-16 doc-edit retry note: the first attempt to update Phase3 command wording from `read_saif` to `read_activity_file -format SAIF` failed because a guard detected remaining historical `read_saif` text in the active plan and aborted before writing files. Retrying with an explicit replacement of both active-plan occurrences before generating Cadence script-only collateral.

## 0.60x Phase3 mvin_mvout Cadence script-only plan decision

Date: 2026-05-16.

User confirmed the next Phase3 `mvin_mvout` step should generate Cadence script-only collateral and must not launch Innovus yet. Scope remains single-workload `mvin_mvout` bring-up under:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/
```

Local Cadence documentation check found that Innovus/Voltus 23.14 exposes `read_activity_file` with `-format SAIF`; no usable local `read_saif` help entry was found. The script-only Phase3 plan should therefore use `read_activity_file -format SAIF` and record the detected SAIF root scope before any Cadence run. A direct inspection of the completed Phase1b `mvin_mvout` SAIF shows the first SAIF instance scope is `TOP`.

This remains non-signoff: r28 is `PG-open / DRC-open / routed-SDF-waived thermal proxy`, and Phase1b SAIF is Verilator zero-delay activity, not SDF timing simulation or commercial gate simulation.

2026-05-16 Phase3 script-generation retry note: the first run of `scripts/phase3_mvin_mvout_write_cadence_power_scripts.py` failed before generating Cadence collateral because it incorrectly required `innovus/data/export_routing.enc.dat` to be a non-empty file. Current r28 evidence shows this Innovus checkpoint payload is a directory, paired with the non-empty `export_routing.enc` Tcl wrapper. No Cadence tool was launched and no Stage2/Phase1b artifact was modified. Retrying after changing the generator input validation to accept a non-empty checkpoint directory.

## 0.60y Phase3 mvin_mvout Cadence script-only collateral generated

Date: 2026-05-16.

Implemented and ran the script-only Phase3 `mvin_mvout` Cadence collateral generator:

```bash
source tools/env_gemmini_thermal.sh
python -m py_compile scripts/phase3_mvin_mvout_write_cadence_power_scripts.py
python scripts/phase3_mvin_mvout_write_cadence_power_scripts.py
```

Result: `script_only_generated`. No Cadence tool was launched, no Stage2 physical artifact or Phase1b artifact was modified, and no running replay process was interrupted.

Generated files:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/scripts/phase3_mvin_mvout_read_activity_power.tcl
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/scripts/run_phase3_mvin_mvout_innovus_no_gui.sh
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/phase3_mvin_mvout_cadence_script_manifest.json
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/README.md
```

The generated Tcl restores `export_routing.enc.dat` as a checkpoint directory with top `Gemmini`, reads the completed mainline `mvin_mvout` SAIF using `read_activity_file -format SAIF -scope TOP -reset -zero_delay true`, emits annotation diagnostics (`get_activity` and `dump_unannotated_nets`), and then emits initial average `report_power` hierarchy/instance/net reports. It deliberately does not call `saveDesign`. The generated runner is present only for later approval and was not executed.

All outputs and future reports remain non-signoff because r28 is `PG-open / DRC-open / routed-SDF-waived thermal proxy` and the SAIF is Verilator zero-delay activity, not SDF timing simulation or commercial gate simulation.

## 0.60z Phase3/Phase4 ATSim3D object-level handoff requirement

Date: 2026-05-16.

User confirmed that Phase4 must not stop at grid-level ATSim3D. The plan now adds a layout-object-level ATSim3D v1 path in addition to the existing grid-level PACT, ATSim3D, and HotSpot paths.

Local ATSim3D v1 usage was checked against `docs/atsim_tool_guide.md`, `scripts/run_atsim3d.sh`, and public examples under `third_party/ATSim3D_pub`. The real v1 entry is:

```bash
scripts/run_atsim3d.sh --lcfFile <lcf.csv> --ConfigFile <config> --SimParamsFile <simparams>
```

Relevant v1 input format from examples:

- LCF: `Layer,Main_compo,Thickness (m),FloorplanFile,PowerFile,Clip_num_x,Clip_num_y,Clip_num_z`.
- Object floorplan: `UnitName,X,Y,Length (m),Width (m),ConfigFile,Label`; some examples also include `Z` and `Thickness (m)`. Units are meters.
- Object power: `UnitName,Power_dyn,Power_leak`, keyed by the same `UnitName`.
- Config/SimParams: INI-style material, temperature, package, leakage, solver, and grid settings.

Phase3 must therefore add an object-level ATSim3D handoff under `power/mvin_mvout/atsim3d_object/` in addition to grid outputs. Exact object granularity remains open and must be confirmed before implementation: individual placed standard-cell instances versus coarser placement-derived layout objects. All such outputs remain non-signoff and `single_window_average` for the first bring-up.

## 0.60aa Phase4 ATSim3D local per-instance hotspot refinement decision

Date: 2026-05-16.

User refined the ATSim3D object-level plan: Phase4 should first run the original grid-level thermal flow (PACT, grid-level ATSim3D, and HotSpot), then select hotspot ROI and run a local ATSim3D v1 refinement where every placed standard-cell instance inside the selected ROI is one ATSim object.

Phase3 impact:

- Phase3 must provide a complete full-chip standard-cell instance geometry/power catalog, not only grid power.
- Phase4 is responsible for hotspot ROI selection and for slicing the Phase3 catalog into local ATSim3D v1 `flp.csv` / `power.csv` / `lcf.csv` / config / SimParams inputs.
- Full-chip per-instance ATSim3D should not be the first execution target. The r28 DEF has `COMPONENTS 586968`, so full-chip instance-level ATSim3D is a scalability risk.
- The first mvin handoff remains `single_window_average` and non-signoff.
