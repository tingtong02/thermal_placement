# mvin_mvout Threading Smoke Archive (2026-04-24)

## 定位

本文件归档 2026-04-24 对 Gemmini 官方 `mvin_mvout` bare-metal 程序的辅助 smoke 结果。

它不是当前 Stage 1-4 的 GEMM baseline，也不参与后续热结论。保留它的目的只有三个：

- 记录官方辅助测试的源码来源和计算内容
- 记录 Verilator 多线程 VCD 仿真的实测结果
- 固定本轮生成的大体积波形和日志路径，避免后续与 `tiled_matmul_os` baseline 混淆

## 源码与程序语义

源文件：

- [mvin_mvout.c](/home/lisihang/thermal_placement/third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/mvin_mvout.c)

程序行为：

- `N=8`
- 每个 batch 的矩阵大小是 `DIM x DIM`，当前软件头文件下 `DIM=16`
- 先配置 `gemmini_config_ld()` 与 `gemmini_config_st()`
- 依次对 8 个矩阵执行 `gemmini_mvin()` 和 `gemmini_mvout()`
- 执行 `gemmini_fence()` 等待完成
- 最后逐个比较输入矩阵和输出矩阵，验证搬入/搬出路径正确性

因此它是官方搬运/读回测试，不是 GEMM 计算负载。

## 本轮实测 run

统一入口：

```bash
source tools/env_gemmini_thermal.sh
scripts/build_gemmini_workloads.sh mvin_mvout
```

统一运行方式：

```bash
RUN_TAG=<tag> \
TIMEOUT_CYCLES=2000000 \
MAKE_JOBS=128 \
VERILATOR_THREADS=<threads> \
CLEAN_DEBUG_SIM=1 \
EXTRACT_ACTIVITY=0 \
scripts/run_gemmini_workload.sh mvin_mvout
```

本轮保留的 VCD run：

| run tag | verilator threads | sim walltime | VCD size | log |
| --- | --- | --- | --- | --- |
| `bench_mvin_vcd_t1` | 1 | `143.129 s` | `1.8G` | [t1.log](/home/lisihang/thermal_placement/sim/logs/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t1.log) |
| `bench_mvin_vcd_t16` | 16 | `61.168 s` | `1.8G` | [t16.log](/home/lisihang/thermal_placement/sim/logs/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t16.log) |
| `bench_mvin_vcd_t32` | 32 | `92.657 s` | `1.8G` | [t32.log](/home/lisihang/thermal_placement/sim/logs/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t32.log) |
| `bench_mvin_vcd_t64` | 64 | `247.615 s` | `1.8G` | [t64.log](/home/lisihang/thermal_placement/sim/logs/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t64.log) |
| `bench_mvin_vcd_t128` | 128 | `415.556 s` | `1.8G` | [t128.log](/home/lisihang/thermal_placement/sim/logs/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t128.log) |

当前只归档事实，不在这里给出 active 策略结论。active 策略仍以主线文档和用户确认为准。

## 产物路径

波形：

- [t1.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t1.vcd)
- [t16.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t16.vcd)
- [t32.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t32.vcd)
- [t64.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t64.vcd)
- [t128.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t128.vcd)

stdout / simulator out：

- [sim/logs/GemminiRocketConfig](/home/lisihang/thermal_placement/sim/logs/GemminiRocketConfig)

artifact symlink：

- [artifacts/stage1](/home/lisihang/thermal_placement/artifacts/stage1)

manifest：

- [reports/stage1_mvin_mvout_baseline_manifest.txt](/home/lisihang/thermal_placement/reports/stage1_mvin_mvout_baseline_manifest.txt)
- [archive manifest](/home/lisihang/thermal_placement/archive/mvin_mvout_threading_smoke_2026-04-24/manifest.txt)

## 使用约束

- 不把 `mvin_mvout` 当作 sustained high-load GEMM baseline
- 不引用该测试推导 Stage 2-4 的热结论
- 仅在需要复查 simulator/threading/VCD 成本时回看本归档
