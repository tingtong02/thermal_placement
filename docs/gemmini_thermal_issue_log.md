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

## 10. 后续构建建议默认开多核

### 原因

- RTL 生成、Verilator 编译、后续综合/实现都能显著受益于多核

### 当前处理

现有脚本已统一支持：

- `MAKE_JOBS="${MAKE_JOBS:-$(nproc)}"`

涉及脚本：

- [run_gemmini_rtl_generation.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_rtl_generation.sh)
- [build_gemmini_workloads.sh](/home/lisihang/thermal_placement/scripts/build_gemmini_workloads.sh)
- [run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh)

### 推荐用法

```bash
export MAKE_JOBS=$(nproc)
```

再执行各阶段脚本。
