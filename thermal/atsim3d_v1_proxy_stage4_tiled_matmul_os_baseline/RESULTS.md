# ATSim3D v1 Proxy Rerun Results

更新时间：2026-05-03

## 1. 本次 proxy rerun 结果

本次使用 ATSim3D v1 对旧 `stage4_tiled_matmul_os_baseline` proxy power 做 steady-state 单 active Si layer 求解。v2 `ATSim3_5D` 没有参与本次运行。

运行通过：

| 项 | 结果 |
| --- | --- |
| wrapper | `scripts/run_atsim3d.sh` |
| exit status | `0` |
| coarse solve | 0.62 s |
| fine solve | 216.46 s |
| total runtime | 265.10 s |
| result file | `inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res` |
| result size | 1,258,291,200 bytes |
| output points | 16,777,216 = 4096 x 4096 |

ATSim3D v1 温度统计：

| metric | value |
| --- | ---: |
| min | 324.900422 K |
| max | 329.634972 K |
| mean | 326.971203 K |
| max-min | 4.734550 K |
| hottest coordinate | x=0.001133819286 m, y=0.000790337526 m |
| hottest source proxy unit by floorplan containment | `g21_14` |

输入功耗统计来自 `inputs/manifest.json`：总 proxy power 为 1.0000000000003046 W；最大功耗 proxy unit 是 `g35_19`，功耗为 0.000868155873807 W。ATSim 热点位于 `g21_14`，不等于最大单元功耗位置，说明稳态温度峰值还受周围功耗分布、边界条件和横向导热影响。

### 1.1 `.res` 文件和标准单元数据边界

ATSim3D v1 的 `.res` 是 active layer 细网格温度样本表，记录空间位置与温度；本次 proxy 文件可解析为 4096 x 4096 个温度点。它不是标准单元级报告，不包含 instance name、master cell、面积、toggle、power 或 region 字段。

因此，ATSim 原生输出不能直接回答“哪个标准单元最热”。需要标准单元上下文时，流程必须先把 ATSim `.res` 下采样或聚合到项目 DEF physical grid，再与 Stage 3 placed instance map 叠加；旧 proxy route 中对应的标准单元来源是 `power/stage3_tiled_matmul_os_baseline_instance_grid_map.csv`，而不是 ATSim 求解器自身。

## 2. 与修复后 PACT / HotSpot proxy 结果对比

这些结果使用的是同一个旧 proxy thermal-flow 的输入族，但 solver、边界模型、网格粒度和输出定义不同，数值不能直接当作同一物理模型的逐点复现。2026-05-03 后处理修复后，本节 PACT grid 使用 DEF 物理坐标；PACT raw row-order 只作为诊断，不再作为主对比。

| source | points | min K | max K | mean K | max-min K |
| --- | ---: | ---: | ---: | ---: | ---: |
| ATSim3D v1 proxy layer0 | 16,777,216 | 324.900422 | 329.634972 | 326.971203 | 4.734550 |
| PACT steady layer0 | 4,096 | 322.050000 | 333.720000 | 327.002756 | 11.670000 |
| HotSpot coarse ttrace | 320 samples x blocks | 318.150000 | 318.230000 | 318.152531 | 0.080000 |

观察：

- ATSim3D v1 与修复后 PACT 的 mean 很接近：326.971203 K vs 327.002756 K，差约 -0.031554 K。
- ATSim3D v1 的 max 比 PACT 低约 4.085028 K，min 比 PACT 高约 2.850422 K，因此温度分布更平滑。
- ATSim3D v1 输出的是高分辨率细网格 `.res`，本次是 4096 x 4096 点；PACT 当前旧结果是 64 x 64 scalar grid；HotSpot 是 5 个 coarse block 的时间序列。
- HotSpot ttrace 的最大值出现在 block `other_context`，最大 318.23 K；它在旧 proxy flow 中只作为 coarse comparison，分辨率和分区都不同。

## 3. ATSim3D public 2DIC / Mono3D / TSV3D 示例结果区别

下面统计来自本仓库已运行并生成的 `third_party/ATSim3D_pub` v1 示例 `.res` 文件。它们不是 Gemmini proxy 输入，而是 ATSim3D public repo 自带测试结构。

| case | role | points | min K | max K | mean K | max-min K |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2DIC | active layer0 | 262,144 | 313.502706 | 342.634710 | 318.118264 | 29.132004 |
| Mono3D layer6 | active tier1 | 65,536 | 343.894736 | 361.999020 | 354.511235 | 18.104284 |
| Mono3D layer11 | active tier0 | 65,536 | 343.771862 | 360.428676 | 353.853211 | 16.656814 |
| TSV3D layer2 | active tier1 | 409,600 | 368.336367 | 392.518324 | 383.467698 | 24.181958 |
| TSV3D layer7 | active tier0 | 409,600 | 360.718798 | 373.216159 | 366.820691 | 12.497361 |
| TSV3D layer3 | substrate between active layers | 25,600 | 366.589962 | 391.624356 | 382.690295 | 25.034394 |
| TSV3D layer8 | bottom substrate | 25,600 | 358.548109 | 370.405967 | 364.326953 | 11.857858 |

### 3.1 2DIC

`third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.csv` 描述两层结构：

- layer0: active Si, 有 floorplan 和 power 文件，厚度 `7.5e-7 m`。
- layer1: Si substrate, 无 power 文件，厚度 `1e-4 m`。

该示例输出 `Intel_ID1_lcf.layer0.res`。它是单 active layer 的 2D IC 场景，热源都在同一个 active layer 内，热扩散主要通过 active layer、substrate 和边界条件体现。统计上它的 mean 接近 318.12 K，但局部 max 到 342.63 K，max-min 为 29.13 K，说明 public 2DIC 输入中的局部功耗分布比较集中。

### 3.2 Mono3D

`third_party/ATSim3D_pub/Mono3D/Mono3D_lcf.csv` 描述 monolithic 3D stack，包含 dielectric、metal/poly、两个 active Si tier 和底部 Si 层。两个有功耗的 active layer 是：

- layer6: `Mono3D_tier1_flp.csv` + `Mono3D_tier1_power.csv`。
- layer11: `Mono3D_tier0_flp.csv` + `Mono3D_tier0_power.csv`。

本地结果中 layer6 mean 为 354.511235 K，layer11 mean 为 353.853211 K；layer6 的 mean 高约 0.658024 K，max 高约 1.570344 K。两个 active layer 的热点坐标很接近，说明该示例的两层功耗热点在平面位置上有较强重叠，垂直热耦合使两层温度接近。

### 3.3 TSV3D

`third_party/ATSim3D_pub/TSV3D/TSV3D_lcf.csv` 描述 TSV-based 3D stack，包含 dielectric、BEOL、两个 active Si tier、substrate 和 TIM。两个有功耗的 active layer 是：

- layer2: `TSV3D_tier1_flp.csv` + `TSV3D_tier1_power.csv`。
- layer7: `TSV3D_tier0_flp.csv` + `TSV3D_tier0_power.csv`。

`third_party/ATSim3D_pub/TSV3D/SimParms.config` 指向 `flp_files/TSV_flp.csv`，TSV shape 为 `cylinder`。该 TSV floorplan 中有 16 个 TSV，半径 `1.5e-05 m`，位置集中在约 x/y 0.0008 到 0.00095 m 区域，连接 `BotLayer=5` 到 `TopLayer=2`。

本地结果中 layer2 明显热于 layer7：layer2 mean 为 383.467698 K，layer7 mean 为 366.820691 K，mean 差约 16.647007 K；layer2 max 为 392.518324 K，layer7 max 为 373.216159 K，max 差约 19.302165 K。layer3 是两个 active layer 间的 substrate，温度统计接近 layer2；layer8 是底部 substrate，统计接近 layer7。这个结果体现了 TSV3D 示例里垂直 stack、TSV array、active tier 相对位置和边界路径共同决定层间温度差。

## 4. 三类 ATSim3D v1 示例的核心区别

| 结构 | active layer 数 | TSV | public result 的主要差异 |
| --- | ---: | --- | --- |
| 2DIC | 1 | no | 单 active layer 加 substrate；只有一个主要发热层，结果展示平面内热点和到 substrate 的散热。 |
| Mono3D | 2 | no | 两个 monolithic active tier 垂直堆叠，中间有 dielectric/metal/poly 层；两个 active layer 温度接近，体现强垂直耦合。 |
| TSV3D | 2 | yes | 两个 active tier 通过 TSV array 相关联，stack 中还有 BEOL、TIM、substrate；本地结果中上下 active layer 温差显著，layer2 更热。 |

## 5. 复现命令

生成 ATSim 输入：

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python \
  thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/prepare_atsim_v1_proxy_inputs.py
```

运行 ATSim3D v1：

```bash
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.csv \
  --ConfigFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline.config \
  --SimParamsFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_simparams.config
```

生成统计：

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python \
  thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/analyze_atsim_results.py
```

## 6. Stage4-style artifacts

已按 `artifacts/stage4` 现有风格生成 ATSim3D v1 proxy 图表和统计，输出目录：

```text
artifacts/stage4/atsim3d_v1_proxy/
```

生成脚本：

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python \
  thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/generate_atsim_stage4_artifacts.py
```

主要图表：

| artifact | 内容 |
| --- | --- |
| `heatmap_atsim_proxy_downsample_256.png` | ATSim3D v1 proxy layer0 4096x4096 细网格下采样到 256x256 的热图。 |
| `heatmap_atsim_proxy_downsample_64.png` | ATSim3D v1 proxy layer0 下采样到 64x64 的热图。 |
| `heatmap_atsim_minus_pact_64.png` | `ATSim - corrected PACT` 温差热图，physical y-up。 |
| `heatmap_atsim_minus_pact_raw_order_64.png` | `ATSim - PACT raw row order` 诊断热图。 |
| `atsim_pact_hotspot_temperature_distribution.png` | ATSim fine-grid、PACT steady grid 和 HotSpot peak max 的温度分布对比。 |
| `atsim_pact_hotspot_summary_bar.png` | ATSim、PACT、HotSpot 的 max/mean summary。 |
| `atsim_public_examples_heatmaps.png` | ATSim3D public 2DIC / Mono3D / TSV3D 示例热图总览。 |
| `atsim_public_examples_summary_bar.png` | public 示例各输出层 mean/max 温度对比。 |

主要统计表：

| artifact | 内容 |
| --- | --- |
| `atsim_proxy_downsample_256_grid.csv` | ATSim proxy 256x256 下采样温度矩阵。 |
| `atsim_proxy_downsample_64_grid.csv` | ATSim proxy 64x64 下采样温度矩阵。 |
| `atsim_minus_pact_64_grid.csv` | `ATSim - corrected PACT` 64x64 温差矩阵，physical y-up。 |
| `atsim_minus_pact_raw_order_64_grid.csv` | `ATSim - PACT raw row order` 诊断矩阵。 |
| `atsim_proxy_hotspot_rank.csv` | ATSim fine-grid top-20 热点坐标和对应 64x64 source grid。 |
| `atsim_proxy_histogram.csv` | ATSim fine-grid 温度直方图。 |
| `atsim_proxy_quantiles.csv` | ATSim fine-grid 温度分位数，基于 histogram midpoint 近似。 |
| `atsim_proxy_vs_pact_hotspot_summary.csv` | ATSim / PACT / HotSpot summary。 |
| `atsim_pact_delta_summary.csv` | `ATSim - corrected PACT` 差值统计。 |
| `atsim_pact_raw_order_delta_summary.csv` | `ATSim - PACT raw row order` 诊断差值统计。 |
| `atsim_pact_coordinate_delta_comparison.csv` | corrected physical alignment 与 raw-order alignment 的 abs mean / RMS / corr 对比。 |
| `atsim_public_example_summary.csv` | public 2DIC / Mono3D / TSV3D 示例层统计。 |

ATSim proxy fine-grid 分位数近似：

| quantile | temperature K |
| ---: | ---: |
| 0.01 | 324.989195 |
| 0.05 | 325.225922 |
| 0.25 | 325.876923 |
| 0.50 | 326.646287 |
| 0.75 | 328.007470 |
| 0.95 | 329.309472 |
| 0.99 | 329.605381 |

ATSim fine-grid top hotspot 是 `fine_x=1376`, `fine_y=959`，坐标 x=0.00113381928613 m, y=0.000790337526367 m，温度 329.634972 K；对应 64x64 source grid 为 `(21, 14)`。

修复后 alignment 证据：

| alignment | abs mean K | RMS K | corr |
| --- | ---: | ---: | ---: |
| physical y-up | 1.326156 | 1.679745 | 0.972619 |
| PACT raw row order | 2.771164 | 3.371622 | -0.141279 |

## 7. 结合论文解释 ATSim3D v1 三类结构

本节依据 `docs/references/atsim/ATSim3D_ISEDA2024_Wang_arXiv2601.11050.pdf` 和 `third_party/ATSim3D_pub` 示例输入解释。ATSim3D v1 论文的目标是 steady-state temperature profile，核心方法是 global-local：全局层面用 compact thermal model 求粗粒度温度和边界，局部层面对 active layer 或非线性/异构区域使用 finite volume method 细化求解。论文还把温度相关热导率和 leakage power 纳入迭代求解；本次 Gemmini proxy 转换中设置 `Power_leak=0`、`non_linear=False`，因此本次跑的是 v1 框架中的线性 steady case。

### 7.1 2DIC

论文实验里的 2DIC 是 Intel multicore CPU 风格的二维芯片结构。本地 public example 的 `Intel_ID1_lcf.csv` 有两个 layer：

- layer0 是 active Si，有 floorplan 和 power，是主要热源层。
- layer1 是 Si substrate，无 power，用于承接和扩散来自 active layer 的热量。

所以 `Intel_ID1_lcf.layer0.res` 代表 active layer 的平面温度分布。它回答的是：单发热层在 substrate 和边界条件作用下，平面内热点在哪里、热点相对平均温度有多高。本地统计中 2DIC mean 为 318.118264 K，max 为 342.634710 K，max-min 为 29.132004 K；这表示 public 2DIC 输入存在局部功耗集中，平均温度接近 ambient 附近，但局部热点显著抬升。

### 7.2 Mono3D

论文中的 Mono3D 是 monolithic 3D IC：多个层 sequential fabrication，两个 active tier 垂直堆叠，中间有 dielectric、metal/poly 等层。public example 中两个带 power 的 active layer 是：

- layer6: `Mono3D_tier1_flp.csv` + `Mono3D_tier1_power.csv`。
- layer11: `Mono3D_tier0_flp.csv` + `Mono3D_tier0_power.csv`。

`Mono3D_lcf.layer6.res` 和 `Mono3D_lcf.layer11.res` 分别代表两个 active tier 的温度图。它们回答的是：monolithic 垂直堆叠后，两层 active tier 之间通过薄介质/金属/硅层耦合，哪个 tier 更热、热点是否垂直对齐。本地结果中 layer6 mean 为 354.511235 K，layer11 mean 为 353.853211 K；layer6 max 为 361.999020 K，layer11 max 为 360.428676 K。两个 active layer 温度接近，说明该示例的两层功耗和垂直热耦合使 active tier 的热状态接近，但 layer6 稍热。

### 7.3 TSV3D

论文中的 TSV3D 是 TSV-based 3D IC：两个 active tier 通过 TSV array 互连，stack 中还有 BEOL、TIM、substrate 等材料层。public example 的 TSV 设置来自 `TSV3D/SimParms.config` 和 `TSV3D/flp_files/TSV_flp.csv`：16 个 cylinder TSV，半径 15 um，pitch 50 um，位置集中在 stack 中部区域。

带 power 的 active layer 是：

- layer2: `TSV3D_tier1_flp.csv` + `TSV3D_tier1_power.csv`。
- layer7: `TSV3D_tier0_flp.csv` + `TSV3D_tier0_power.csv`。

本地统计中 layer2 mean 为 383.467698 K，max 为 392.518324 K；layer7 mean 为 366.820691 K，max 为 373.216159 K。layer3 是两个 active layer 间的 substrate，mean 为 382.690295 K；layer8 是 bottom substrate，mean 为 364.326953 K。这个结果代表：TSV3D 示例中上方 active tier 和中间 substrate 明显更热，下方 active tier 和底部 substrate 较冷。原因来自该测试结构的功耗分布、层顺序、TSV/材料异构导热路径以及边界散热路径共同作用。

### 7.4 三类结构结果各自代表什么

| 类型 | 结果文件代表 | 主要物理问题 | 读图重点 |
| --- | --- | --- | --- |
| 2DIC | 单 active layer 温度图 | 单发热层经 substrate/边界散热后的平面热点 | 平面热点位置、热点与平均温差 |
| Mono3D | 两个 active tier 温度图 | 无 TSV 的 monolithic 垂直堆叠热耦合 | 两个 tier 的 mean/max 是否接近、热点是否对齐 |
| TSV3D | active tier 与 substrate 层温度图 | TSV array 与多材料 stack 下的异构导热 | 上下 tier 温差、TSV/中间层附近热点、substrate 温度梯度 |

## 8. 与修复后 PACT / HotSpot 的详细对比

### 8.1 模型和输出粒度

| 项 | ATSim3D v1 proxy rerun | PACT corrected proxy | HotSpot old proxy |
| --- | --- | --- | --- |
| 求解类型 | steady-state | steady + transient | transient coarse comparison |
| 本次输入 | 旧 Stage4 proxy floorplan/power 转换到 ATSim v1 | 旧 Stage4 PACT 输入，后处理转换为 DEF physical y-up | 旧 Stage4 HotSpot block 输入 |
| 空间粒度 | 输出 4096x4096 fine grid，并下采样到 256x256/64x64 | 64x64 layer grid | 5 个 coarse blocks |
| 热模型表达 | global compact model + local FVM | thermal RC/SPICE-style grid solve | block-level compact thermal model |
| 本次边界/stack | single active Si layer + NoPackage | 旧 PACT layer0/layer1 设置 | HotSpot floorplan block 模型 |
| 输出含义 | active Si layer steady fine temperature | layer grid steady/transient temperature | coarse block transient temperature |

### 8.2 数值对比

| source | min K | max K | mean K | std K | range / delta K |
| --- | ---: | ---: | ---: | ---: | ---: |
| ATSim3D v1 proxy layer0 | 324.900422 | 329.634972 | 326.971203 | 1.311101 | 4.734550 |
| PACT steady layer0 | 322.050000 | 333.720000 | 327.002756 | 2.926532 | 11.670000 |
| HotSpot coarse ttrace | - | 318.230000 | - | - | 0.080000 over ambient |

`ATSim - PACT` 有两种统计口径：

| alignment | min K | max K | mean K | std K | mean abs K | RMS K | corr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| physical y-up | -4.136682 | 3.004252 | -0.031554 | 1.679449 | 1.326156 | 1.679745 | 0.972619 |
| PACT raw row order | -7.283838 | 5.947506 | -0.031554 | 3.371474 | 2.771164 | 3.371622 | -0.141280 |

解释：

- ATSim 与 PACT 的 mean 基本一致：ATSim mean 比 PACT mean 低约 0.031554 K。
- ATSim max 比 PACT max 低约 4.085028 K，ATSim min 比 PACT min 高约 2.850422 K，因此 ATSim 的 spatial spread 更小。
- 如果直接按 PACT raw CSV 行号比较，热点看起来位于完全不同的 y 区域；使用修复后的 PACT physical y-up grid 后，空间相关系数为 0.972619，说明两张 heatmap 的主要形状其实接近。
- 物理对齐后仍有局部差异：RMS 为 1.679745 K，来自 ATSim single-layer/NoPackage 转换模型与旧 PACT layer0/layer1 模型、边界条件、垂直散热路径和网格求解方法不同。
- HotSpot 的 peak max 为 318.23 K，远低于 steady ATSim/PACT 峰值。这里的主要原因不是同一细网格模型求出了更低温度，而是 HotSpot 旧结果是短窗口五块 coarse transient comparison；它不表达 4096x4096 或 64x64 的 steady fine-grid 热点。

### 8.3 热点位置对比

| source | hotspot |
| --- | --- |
| ATSim3D v1 fine grid | fine `(1376, 959)`, source 64x64 grid `(21, 14)`, 329.634972 K |
| PACT steady layer0 raw CSV row | 64x64 grid `(22, 47)`, 333.720000 K |
| PACT steady layer0 corrected physical y-up | 64x64 grid `(22, 16)`, 333.720000 K |
| HotSpot transient | block `other_context`, peak 318.230000 K |

ATSim 与 PACT 的热点“完全不一致”主要来自 y 轴原点约定不同：ATSim `.res` 明确给出物理 `x,y` 坐标且 y 递增；PACT raw CSV 的 row index 是矩阵行号，不是 DEF physical `grid_y`。使用修复后的 physical y-up PACT grid 后，PACT 热点 `(22,16)` 与 ATSim source grid `(21,14)` 接近。剩余差异说明两者不是同一个 solver schema 的逐点复现。

### 8.4 本次图表如何阅读

- `heatmap_atsim_proxy_downsample_256.png` 用于看 ATSim fine-grid 热场形状，比 64x64 更接近原始 4096x4096 输出。
- `heatmap_atsim_proxy_downsample_64.png` 用于和修复后的 PACT `pact_steady_layer0_grid.csv` 对齐。
- `heatmap_atsim_minus_pact_64.png` 使用修复后的 PACT physical y-up grid，是主对比图。
- `heatmap_atsim_minus_pact_raw_order_64.png` 使用 PACT raw row order，仅作为错误坐标解释的诊断图。
- `atsim_pact_hotspot_temperature_distribution.png` 用于看整体温度分布：ATSim 分布更窄，PACT 分布更宽，HotSpot 作为单个 coarse peak marker 出现。
- `atsim_public_examples_heatmaps.png` 用于比较 2DIC、Mono3D、TSV3D 三类 public 示例的层级输出，不是 Gemmini proxy 结果。
