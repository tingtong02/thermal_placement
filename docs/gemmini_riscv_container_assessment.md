# RISC-V Toolchain Container Assessment

更新时间：2026-04-20

评估对象：

- Docker container: `lisihang.gem5_npu_mpu_container`
- Image: `gem5/npu-compiler:latest`

评估目的：

- 判断该容器是否可以支撑当前 Gemmini thermal validation 开发流程
- 明确它能替代哪些步骤，不能替代哪些步骤
- 记录实际测试结果，降低后续试错成本

## 1. 容器基本情况

通过宿主机 `docker ps -a` 确认：

- 容器名称：`lisihang.gem5_npu_mpu_container`
- 状态：`Up`
- 镜像：`gem5/npu-compiler:latest`

容器内基础环境：

- 用户：`root`
- 工作目录：`/`
- `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
- `nproc = 512`

结论：

- 这是一个偏 gem5 / cross-compile / simulation 的高并行环境
- 容器内 CPU 资源充足，适合做并行编译和仿真任务

## 2. 挂载情况

通过 `docker inspect` 确认，当前容器仅有一个显式 bind mount：

- Host: `/home/lisihang/tile_based_simulation/gem5_npu_mpu`
- Container: `/gem5`

当前 `thermal_placement` 仓库 **没有** 自动挂进这个容器。

这意味着：

1. 容器可以直接访问 `/gem5`
2. 容器不能直接看到 `/home/lisihang/thermal_placement`
3. 如果后续要在容器里直接处理本仓库，需要：
   - 增加 bind mount，或
   - 用 `docker cp` 复制文件，或
   - 通过宿主机脚本驱动 `docker exec`

## 3. 工具可用性检查

### 3.1 已确认可用

容器内可用的关键工具如下：

| 工具 | 状态 | 路径 |
| --- | --- | --- |
| `riscv64-linux-gnu-gcc` | 可用 | `/usr/bin/riscv64-linux-gnu-gcc` |
| `riscv64-linux-gnu-g++` | 可用 | `/usr/bin/riscv64-linux-gnu-g++` |
| `riscv64-linux-gnu-objdump` | 可用 | `/usr/bin/riscv64-linux-gnu-objdump` |
| `riscv64-linux-gnu-readelf` | 可用 | `/usr/bin/riscv64-linux-gnu-readelf` |
| `python3` | 可用 | 容器内默认 Python 3.12.3 |
| `gem5` RISCV binary | 可用 | `/gem5/build/RISCV/gem5.opt` |

编译器版本：

- `riscv64-linux-gnu-gcc (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0`

### 3.2 未发现

以下工具在当前容器内未发现：

| 工具 | 状态 |
| --- | --- |
| `riscv64-unknown-elf-gcc` | 未发现 |
| `riscv64-unknown-elf-objdump` | 未发现 |
| `spike` | 未发现 |
| `spike-dasm` | 未发现 |
| `pk` | 未发现 |
| `qemu-riscv64` | 未发现 |
| `qemu-riscv64-static` | 未发现 |

结论：

- 这是一个 **RISC-V Linux cross-compile + gem5 simulation** 环境
- 它 **不是** 一个现成的 Chipyard/Gemmini bare-metal 工具链环境

## 4. 最小交叉编译测试

### 4.1 动态链接 RISC-V Linux ELF

测试命令核心逻辑：

```bash
riscv64-linux-gnu-gcc -O2 hello.c -o hello
file hello
riscv64-linux-gnu-readelf -h hello
riscv64-linux-gnu-readelf -l hello
```

测试结果：

- 成功生成 `ELF 64-bit LSB pie executable`
- 架构：`RISC-V`
- ABI：`double-float ABI`
- 类型：`DYN (PIE)`
- 解释器：`/lib/ld-linux-riscv64-lp64d.so.1`

结论：

- 容器可以稳定生成 **RISC-V Linux 动态链接 ELF**

### 4.2 静态链接 RISC-V Linux ELF

测试命令核心逻辑：

```bash
riscv64-linux-gnu-gcc -O2 -static hello.c -o hello.static
file hello.static
riscv64-linux-gnu-readelf -h hello.static
```

测试结果：

- 成功生成 `ELF 64-bit LSB executable`
- 架构：`RISC-V`
- 类型：`EXEC`
- 链接方式：`statically linked`

结论：

- 容器可以稳定生成 **RISC-V Linux 静态 ELF**
- 这对后续在 gem5 SE 模式里跑最小测试非常有用

## 5. 最小 gem5 执行测试

### 5.1 测试目标

验证容器是否能够完成：

- 编译 RISC-V 程序
- 在容器内用 `gem5` RISCV build 执行
- 形成最小闭环

### 5.2 测试方法

在容器内：

1. 生成一个最小 `hello.c`
2. 使用 `riscv64-linux-gnu-gcc -static` 编译
3. 运行：

```bash
/gem5/build/RISCV/gem5.opt /gem5/configs/deprecated/example/se.py --cmd=<hello.static>
```

### 5.3 实际结果

gem5 日志中出现：

- `hello-from-gem5`
- `Exiting @ tick ... because exiting with last active thread context`
- `EXIT_STATUS=0`

同时看到以下非阻塞信息：

- `warn: The se.py script is deprecated`
- `info: RVV enabled, VLEN = 256 bits, ELEN = 64 bits`

结论：

- 容器具备 **RISC-V Linux 交叉编译 + gem5 RISCV 执行** 的闭环能力
- 对做最小 userspace 程序验证、算法测试、gem5 侧软件验证是够用的

## 6. 对当前 Gemmini 热验证流程的适配结论

### 6.1 容器能直接支撑的部分

当前容器可以较好支撑：

1. `gem5` 相关 RISC-V Linux userspace 编译与仿真
2. 最小 RISC-V Linux 程序功能验证
3. 与 `/gem5` 仓库相关的并行构建 / 仿真任务
4. 需要大量 CPU 核的编译型任务

如果后续某些分析脚本或微基准可以脱离 bare-metal 环境，转成：

- Linux userspace 程序
- gem5 SE 模式测试

那么这个容器是有价值的。

### 6.2 容器当前不能直接支撑的部分

对于 **当前这条 Chipyard + Gemmini 官方主线**，它还缺几块关键能力：

1. 没有 `riscv64-unknown-elf-gcc`
2. 没有 `RISCV` bare-metal prefix
3. 没有 `spike` / `pk` / `spike-dasm`
4. 当前 `thermal_placement` 仓库没有挂进容器

这意味着它 **不能直接替代** 以下步骤：

1. `gemmini-rocc-tests` bare-metal binary 构建
2. Chipyard `run-binary-debug` 这条按 ELF 加载 bare-metal workload 的官方路径
3. 依赖 `riscv64-unknown-elf-*` 工具链的 objdump / link / runtime 相关流程

## 7. 对“RISC-V toolchain 是否一定需要”的初步影响

基于当前容器评估，可以先得出一个比较精确的中间结论：

- 如果坚持走 **Chipyard + Gemmini 官方 bare-metal workload + Verilator run-binary-debug** 路线，
  那么当前仍然需要一套 **bare-metal RISC-V toolchain**，也就是 `riscv64-unknown-elf-gcc` 这一类工具。

- 但如果后续愿意改流程，把部分验证迁移到：
  - Linux userspace 程序
  - gem5 SE 模式
  - 或直接处理已有 ELF / memory image

  那么可以减少对 bare-metal toolchain 的依赖范围。

也就是说：

- **对当前官方主线流程来说，bare-metal RISC-V toolchain 仍然是刚需**
- **对整个研究目标来说，RISC-V toolchain 未必在所有阶段都必须以同一种形式存在**

## 8. 建议的使用策略

建议把这个容器定位为：

### 方案 A：作为辅助编译/仿真环境

用于：

- RISC-V Linux 程序编译
- gem5 执行验证
- 高并行 CPU 任务

而 Gemmini bare-metal / Chipyard 仿真主线仍在宿主机或另一套 bare-metal toolchain 环境中完成。

### 方案 B：后续扩充容器能力

如果希望把更多工作搬进这个容器，至少还需要补齐：

1. `riscv64-unknown-elf-gcc`
2. 与之配套的 `RISCV` prefix
3. 可能还需要 `spike` / `pk`
4. 将 `/home/lisihang/thermal_placement` 挂载进容器

在这四项没有补齐前，这个容器还不能直接承担当前 Gemmini thermal validation 的完整主线。

## 9. 本次评估结论

一句话总结：

> `lisihang.gem5_npu_mpu_container` 可以很好地支撑 **RISC-V Linux + gem5** 的开发与测试，但目前 **不能直接替代** 当前 Gemmini/Chipyard 所需的 bare-metal RISC-V toolchain。

更细一点：

- 对软件微基准、userspace 交叉编译、gem5 验证：**可用**
- 对 `gemmini-rocc-tests` bare-metal 和 Chipyard 官方 workload 路线：**当前还不够**
