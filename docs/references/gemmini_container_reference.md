# Gemmini Container Reference

## 文档定位

注意：本文件只是参考资料，不保证其中历史流程、命令、路径或结论可以在新的开发中直接复用。使用前必须对照 `docs/phase0tophase4_signoff_multiworkload_plan.md` 和当前仓库状态重新确认。

本文件整理归档中的容器评估结果，作为当前阶段 0–4 的辅助参考。它不是当前主线环境说明，也不代表后续工作必须进入容器执行。

原始历史文档见：

- [docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_riscv_container_assessment.md](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_riscv_container_assessment.md)

## 1. 评估对象

历史上评估过的容器：

- 容器：`lisihang.gem5_npu_mpu_container`
- 镜像：`gem5/npu-compiler:latest`

这份评估的关键价值不在于容器名字本身，而在于它回答了：

- 哪些任务可以迁移到 gem5 / Linux userspace 环境
- 哪些任务仍然必须留在当前 bare-metal / Chipyard 主线环境里

## 2. 历史上确认可用的能力

该容器历史上确认可用于：

- `riscv64-linux-gnu-*` 交叉编译
- RISC-V Linux 动态与静态 ELF 构建
- `gem5` RISCV binary 执行最小 userspace 程序
- 高并行 CPU 编译任务

如果后续某个阶段需要做：

- Linux userspace 程序验证
- gem5 SE 模式验证
- 与 `/gem5` 仓库相关的辅助测试

那么这个结论仍然有参考价值。

## 3. 历史上明确不满足的部分

对当前仓库的 Gemmini / Chipyard bare-metal 主线，这个容器历史上不够用，原因包括：

- 没有 `riscv64-unknown-elf-gcc`
- 没有完整 bare-metal `RISCV` prefix
- 没有 `spike` / `spike-dasm` / `pk`
- 当时 `thermal_placement` 仓库没有自动挂进容器

因此它不能直接替代：

- `gemmini-rocc-tests` bare-metal workload 构建
- Chipyard `run-binary-debug` 主线
- 依赖 `riscv64-unknown-elf-*` 的官方 workload 路径

## 4. 对当前计划的可迁移结论

当前 [phase0tophase4_signoff_multiworkload_plan.md](/home/lisihang/thermal_placement/docs/phase0tophase4_signoff_multiworkload_plan.md) 的主线仍然是：

- Gemmini RTL / activity
- ASAP7 标准单元实现
- PACT 主线热仿真

因此这个容器只能作为辅助环境参考，而不是主执行环境。更具体地说：

- 如果要跑当前仓库已有的 Gemmini bare-metal 与 Verilator 主线，优先仍使用宿主机现有环境
- 如果后续出现独立的 Linux userspace 或 gem5 验证子任务，这份容器评估可以减少重复试错

## 5. 当前使用建议

建议把这份资料理解为“备用环境能力边界”：

1. 它可以帮助判断某个子任务是否适合迁移到容器。
2. 它不能替代当前仓库的主环境文档。
3. 如果以后真的要重新启用该容器，应重新检查：
   - 当前容器是否还存在
   - 是否已挂载 `thermal_placement`
   - 是否已补齐 bare-metal toolchain

当前主环境仍以：

- [gemmini_thermal_environment_setup.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_environment_setup.md)
- [tool_environment_inventory.md](/home/lisihang/thermal_placement/docs/tool_environment_inventory.md)

为准。
