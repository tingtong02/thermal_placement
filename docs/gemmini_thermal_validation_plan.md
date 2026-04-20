# Gemmini Tensor Core 热-布局现象验证计划（可执行版）

## 0. 文档目的

本计划的目标不是重新手写一个新的 tensor core，而是：

1. **直接使用 Gemmini 生成一个 tensor-core-like 加速器 RTL**；
2. 对该设计进行**功能测试**与**活动率采集**；
3. 将活动率映射为模块/区域功耗；
4. 将该设计抽象成多个 macro，并进行 **placement**；
5. 使用 **thermal simulator** 验证：
   - 不同区域活动率是否显著不均；
   - 将多个 MAC/PE 聚成 macro 后，是否会形成更明显的局部热点；
   - 不同 macro 分组方式/布局方式，是否会导致不同峰值温度与热点分布。

---

## 1. 总体研究问题

需要验证的核心现象是：

> 当 Gemmini 生成的 tensor core 中，不同 PE/MAC、buffer、控制模块的活动率存在空间不均时，如果后续将这些单元揉成若干 macro 做物理布局，那么这种非均匀活动是否会转化为非均匀功耗密度，并最终形成局部热点？

因此，本计划的主线为：

**Gemmini RTL 生成**  
→ **功能测试**  
→ **活动率统计**  
→ **功耗建模**  
→ **macro 抽象与分组**  
→ **OpenROAD placement**  
→ **HotSpot 热仿真**  
→ **结果比较与结论**

---

## 2. 工具链（直接定死）

本计划固定使用以下工具，不再模糊建议：

### 2.1 Tensor core / RTL 生成
- **Chipyard + Gemmini**
- 用途：生成 Gemmini accelerator RTL、构建仿真器、运行 bare-metal Gemmini 测试。

### 2.2 功能仿真与波形导出
- **Verilator**
- 用途：运行 cycle-accurate 仿真，导出 VCD 波形，统计活动率。

### 2.3 Gemmini 软件测试
- **gemmini-rocc-tests**（Gemmini 自带/配套测试）
- 用途：运行基础 GEMM、搬运、边界 tile、矩阵乘相关测试，触发不同模块活动。

### 2.4 波形解析与活动率统计
- **Python 3**
- 建议库：
  - `pyvcd` 或自写 VCD 解析脚本
  - `pandas`
  - `numpy`
  - `matplotlib`
- 用途：从 VCD 中提取 per-module / per-region toggle、active cycles、access counts。

### 2.5 综合与布局实现
- **OpenROAD-flow-scripts (ORFS)**
- 用途：对抽象后的 Gemmini block-level 设计执行 floorplan、macro placement、global placement、detailed placement。

### 2.6 时序合理性检查
- **OpenSTA**
- 用途：检查不同 placement 下时序是否出现明显异常；作为 sanity check，而不是本阶段的主优化目标。

### 2.7 热仿真
- **HotSpot**
- 用途：输入 floorplan + block power / power trace，做 steady-state 和 transient 热分析。

### 2.8 结果管理与脚本组织
- **Make + Python + Bash**
- 用途：串联整个实验流程，保证可复现。

---

## 3. 工程目录建议

建议单独建立一个研究工程目录，例如：

```text
project_root/
├── third_party/
│   ├── chipyard/
│   ├── gemmini/                  # 如果单独引用，也可作为镜像/备份
│   ├── OpenROAD-flow-scripts/
│   └── HotSpot/
├── configs/
│   ├── gemmini/
│   ├── openroad/
│   └── hotspot/
├── scripts/
│   ├── run_gemmini_tests.sh
│   ├── extract_vcd_activity.py
│   ├── build_block_power.py
│   ├── make_macro_grouping.py
│   ├── export_floorplan_for_hotspot.py
│   └── plot_results.py
├── rtl_exports/
│   ├── generated-verilog/
│   └── top_wrappers/
├── sim/
│   ├── binaries/
│   ├── waves/
│   ├── logs/
│   └── activity/
├── physical/
│   ├── case_baseline/
│   ├── case_hot_clustered/
│   ├── case_hot_cold_balanced/
│   └── case_connectivity_first/
├── thermal/
│   ├── floorplans/
│   ├── power/
│   ├── steady/
│   └── transient/
└── reports/
    ├── figures/
    ├── tables/
    └── notes/
```

---

## 4. Phase A：直接用 Gemmini 生成 tensor core RTL

## 4.1 目标

获得一个**真实来源于 Gemmini 的 accelerator RTL**，而不是手工编造的小玩具模块。

## 4.2 执行方式

1. 克隆并初始化 Chipyard。
2. 使用 Chipyard 的 Gemmini 配置构建 Verilator 仿真器。
3. 在 `generated-src/` 中导出 Verilog。
4. 从生成的 SoC 级 Verilog 中，定位 Gemmini 相关模块边界。

## 4.3 推荐起始配置

优先从一个中小规模配置开始，避免第一轮仿真和物理流程过重。建议：

- 从 **GemminiRocketConfig** 入手；
- 第一轮研究不改 Gemmini ISA 和软件栈；
- 如果后续要做参数扫描，再修改：
  - systolic array 维度
  - tileRows / tileColumns
  - dataflow
  - local scratchpad / accumulator 参数

## 4.4 本阶段输出

- Verilator simulator 可运行
- Gemmini bare-metal 程序可运行
- 生成的 Verilog 位于 `rtl_exports/generated-verilog/`
- 明确 Gemmini 相关模块层次结构

## 4.5 本阶段注意事项

### 注意 1：研究对象不是整个 SoC，而是 Gemmini accelerator 部分
虽然仿真层面依赖 SoC 环境，但后续 physical/thermal 研究时，应把研究对象收敛到：

- PE array
- scratchpad / local buffers
- accumulator
- controller / data movement logic

### 注意 2：必须先做模块分层清点
后续所有活动率、功耗、macro 分组，必须绑定到清晰的层次。
建议先在 `reports/notes/` 中写一个模块清单表：

| 模块名 | 功能 | 是否纳入热研究 | 备注 |
|---|---|---:|---|
| PE array | MAC 主算力阵列 | 是 | 核心对象 |
| scratchpad banks | 数据缓存 | 是 | 访问很可能热点明显 |
| accumulator | 部分和累加 | 是 | 可能高度活跃 |
| controller | 控制调度 | 是 | 体积小但高切换 |
| TileLink / SoC glue | 接口逻辑 | 暂缓 | 第一轮可简化 |

---

## 5. Phase B：运行 Gemmini 功能测试，产生真实活动

## 5.1 目标

用真实工作负载激活 Gemmini，得到可信活动模式，而不是人工瞎设 activity。

## 5.2 固定使用的测试来源

使用 **gemmini-rocc-tests** 中的 bare-metal 测试为第一批 workload。

## 5.3 第一轮必须跑的测试集

### 组 1：基础功能测试
用于确保设计正常。

- `mvin_mvout`
- 基础 matmul / tiled matmul
- 小矩阵 GEMM

### 组 2：阵列高利用测试
用于制造接近满负载的 PE 活动。

- 方阵 GEMM
- K 维较大、能够持续推高阵列利用率的 case

### 组 3：阵列低利用/边界测试
用于观察活动不均。

- 非方阵 GEMM
- 小 tile / 尾块 case
- 不能整除阵列维度的 case

### 组 4：访存偏重测试
用于观察 buffer 与 compute 活动分离。

- 搬运为主的 case
- mvin/mvout 密集 case
- compute 与 data movement 相对分离的 case

## 5.4 本阶段执行细节

1. 在 Chipyard 中构建 Gemmini 软件测试。
2. 在 Verilator debug 模式运行，以便生成波形。
3. 每个 workload 单独运行，并独立保存：
   - stdout log
   - simulator log
   - VCD 文件
   - workload 元信息（矩阵尺寸、tile 方式、数据类型）

## 5.5 产物命名建议

```text
sim/
├── binaries/
│   ├── gemm_64x64.bin
│   ├── gemm_61x67x59.bin
│   └── mvin_heavy.bin
├── waves/
│   ├── gemm_64x64.vcd
│   ├── gemm_61x67x59.vcd
│   └── mvin_heavy.vcd
└── logs/
    ├── gemm_64x64.log
    ├── gemm_61x67x59.log
    └── mvin_heavy.log
```

---

## 6. Phase C：从 VCD 提取活动率，识别“热风险区域”

## 6.1 目标

回答第一个关键问题：

> Gemmini 内部的活动率是否真的不均匀？

## 6.2 提取粒度

第一轮建议不要直接做到每一根信号，而是按以下粒度统计：

### 粒度 A：模块级
- PE array 总体
- scratchpad 总体
- accumulator 总体
- controller 总体

### 粒度 B：区域级
把 PE array 按空间分区，例如：

- 上半/下半
- 左半/右半
- 四象限
- 或 4×4 超块

这样后面更容易转为 macro。

### 粒度 C：bank/子模块级
如果 scratchpad / accumulator 有 bank 结构，则按 bank 分开统计。

## 6.3 必须统计的指标

对每个模块/区域，统计：

1. **toggle_count**：总翻转数
2. **active_cycles**：处于工作状态的周期数
3. **utilization**：active_cycles / total_cycles
4. **read_count / write_count**：对 buffer 类模块
5. **normalized_activity**：归一化活动率
6. **burstiness**：活动是否集中在少量时段

## 6.4 推荐实现方式

`scripts/extract_vcd_activity.py`：

输入：
- 一个 workload 的 VCD
- 一个层次映射文件，例如 `configs/gemmini/hierarchy_map.yaml`

输出：
- `sim/activity/<workload>_module_activity.csv`
- `sim/activity/<workload>_region_activity.csv`

CSV 示例：

```csv
workload,block,cycles_active,toggle_count,normalized_activity
GEMM_64,module_pe_array,84213,5123401,1.00
GEMM_64,module_spad,90321,3112044,0.61
GEMM_64,module_accum,79812,2541220,0.49
GEMM_64,module_ctrl,91550,420884,0.08
```

## 6.5 本阶段判据

只要满足以下任意一项，就说明“活动不均”已被观察到：

- PE 区域间 normalized_activity 方差明显不为 0
- 某些 bank 的访问显著高于其他 bank
- compute-heavy 与 memory-heavy workload 下，热点区域位置不同
- 边界 tile workload 比满阵列 workload 产生更不均匀的活动分布

---

## 7. Phase D：建立 block-level 功耗模型

## 7.1 目标

将活动率转换为可用于 placement / thermal 的功耗输入。

## 7.2 第一轮固定策略

第一轮不追求 signoff 级精度，使用**活动率加权功耗模型**：

\[
P_i = P_{static,i} + \alpha_i \cdot P_{dyn,max,i}
\]

其中：
- `i`：某个模块或区域
- `alpha_i`：来自 VCD 提取的 normalized_activity
- `P_static,i`：静态功耗估计
- `P_dyn,max,i`：满负载动态功耗上界系数

## 7.3 系数来源

第一轮可采用以下方法给系数：

### 方法 A：结构经验系数（推荐起步）
给不同模块设不同单位功耗权重，例如：

- PE region：1.0
- scratchpad bank：0.6
- accumulator bank：0.8
- controller：0.2

该方法目的是先验证热趋势，而不是绝对温度值。

### 方法 B：后续增强项
后续可以补：

- 综合后面积归一化
- 单位面积功耗上限
- 更真实的 gate-level 或 switching-based power estimation

## 7.4 输出格式

`scripts/build_block_power.py` 输出：

- `thermal/power/<case>_steady.ptrace`
- `thermal/power/<case>_transient.ptrace`

steady 文件：一行一个 block 的平均功耗。  
transient 文件：按时间步输出各 block 功耗序列。

## 7.5 本阶段重点

你现在关心的是：

- block 之间的**相对功耗关系**是否明显不同；
- 这些差异是否足以在热仿真中形成不同热点。

绝对数值误差在第一轮不是主要风险。

---

## 8. Phase E：定义 macro 分组，模拟“多个 MAC 揉成一个 macro”

## 8.1 目标

显式构造不同的 macro grouping 策略，作为核心实验变量。

## 8.2 分组对象

建议以 **PE array 的空间子区块** 作为最小分组单元，例如：

- 若阵列较大，可先切成 4×4 或 8×8 个 PE super-block；
- 每个 super-block 视为一个小计算砖块；
- 再将多个 super-block 聚合成更大的 macro。

buffer / accumulator / controller 也可以按 bank 或功能块作为独立 macro。

## 8.3 第一轮必须比较的 4 种策略

### Case 1：Baseline 均匀切分
- 不看热、不看连接
- 按几何位置平均切 macro

### Case 2：Hot-clustered
- 将高 activity super-block 尽量聚在同一 macro 中
- 用于制造最容易热点集中的对照组

### Case 3：Hot-cold balanced
- 每个 macro 中混合高 activity 与低 activity 区块
- 用于验证冷热均衡是否能缓和热点

### Case 4：Connectivity-first
- 优先按通信/数据局部性分组
- 用于观察“连线友好”是否会牺牲热表现

## 8.4 分组脚本

`scripts/make_macro_grouping.py`

输入：
- `*_region_activity.csv`
- 逻辑邻接图 / 几何位置表

输出：
- `physical/<case>/macro_grouping.csv`
- `physical/<case>/macro_blocks.yaml`

输出需至少包含：

| macro_id | members | area_weight | avg_activity | power_weight |
|---|---|---:|---:|---:|

---

## 9. Phase F：用 OpenROAD-flow-scripts 跑 placement

## 9.1 目标

将不同 macro grouping 的设计放到统一 die 上，得到可比较布局。

## 9.2 为什么固定用 ORFS

因为本阶段重点是：

- floorplan
- macro placement
- global placement
- detailed placement

ORFS 可以直接对自定义 Verilog 设计跑快速 smoke-test，也支持完整 RTL-to-GDS 流程，适合建立可复现实验脚本。

## 9.3 第一轮物理抽象策略

### 关键原则
第一轮**不要直接把整个 Gemmini SoC 拿去跑完整后端**。  
而是：

1. 基于前面定义的 macro grouping；
2. 构造一个 **block-level top wrapper**；
3. 每个 macro 作为一个抽象 block / module；
4. 用代表性 netlist 连接这些 macro；
5. 在统一工艺/库/面积约束下跑 placement。

这样更适合验证“热-布局现象”，而不是挑战全系统实现难度。

## 9.4 block-level top wrapper 内容

建议生成一个顶层，例如 `gemmini_block_top.v`，其包含：

- `macro_pe_0 ... macro_pe_n`
- `macro_spad_0 ...`
- `macro_accum_0 ...`
- `macro_ctrl`

连线原则：
- PE 宏块之间按阵列邻接连接；
- PE 与 buffer / accumulator 按 Gemmini 数据流关系连接；
- 保持四种 case 的总连线规模基本一致。

## 9.5 本阶段统一控制条件

必须固定以下条件，保证对比公平：

- die size 相同
- utilization target 相同
- macro 数量相同
- macro 总面积相同
- 工艺库相同
- 时钟约束相同

## 9.6 ORFS 输出必须保留的文件

每个 case 至少保存：

- `floorplan.def`
- `placed.def`
- `final.sdc`
- `report_tns.rpt`
- `report_wns.rpt`
- `report_hpwl.rpt`
- 拥塞报告

## 9.7 本阶段判据

若各 case 都能得到：

- 合法 placement
- 无明显崩溃
- 基本可比的布局结果

则说明“place 先跑通”已经完成。

---

## 10. Phase G：用 OpenSTA 做 timing sanity check

## 10.1 目标

排除一种情况：某种 placement 虽然热更低，但其实已经极不合理。

## 10.2 本阶段做法

对每个 case：

- 读入 netlist / liberty / SDC
- 运行基本 timing 报告
- 记录 WNS / TNS

## 10.3 本阶段定位

这里不要求 timing closure，只要求：

- 没有某一 case 在时序上完全失真；
- 热结果不是建立在荒谬布局上。

---

## 11. Phase H：将 placement 结果导入 HotSpot 做热仿真

## 11.1 目标

验证：不同 macro grouping / placement 是否真的导致不同温度分布。

## 11.2 输入准备

HotSpot 需要两类核心输入：

1. **floorplan 文件**
   - block 名称
   - 宽高
   - 坐标

2. **power 文件 / power trace**
   - steady-state：每个 block 一个平均功耗
   - transient：每个时间步每个 block 一个功耗值

## 11.3 从 OpenROAD 导出到 HotSpot

`scripts/export_floorplan_for_hotspot.py`

输入：
- ORFS 输出的 DEF/位置文件
- `macro_blocks.yaml`

输出：
- `thermal/floorplans/<case>.flp`
- `thermal/power/<case>.ptrace`

## 11.4 第一轮固定做 steady-state

先做 steady-state 即可，回答：

- 不同 case 的 **peak temperature** 是否不同；
- 热点是否集中在某些 macro；
- 热冷均衡 grouping 是否更平滑。

## 11.5 第二轮再做 transient

当 steady-state 观察到差异后，再做 transient，回答：

- 热点是否随 workload phase 漂移；
- 某些 macro 是否始终为热点中心；
- burst workload 是否造成瞬态过热。

---

## 12. 第一轮必须输出的比较指标

对每个 case，至少输出以下指标：

### 12.1 逻辑/活动层
- PE 区域 activity variance
- bank activity variance
- top-5 active blocks

### 12.2 物理层
- HPWL
- congestion proxy
- WNS / TNS
- macro 邻接情况

### 12.3 热层
- `Tmax`
- `Tavg`
- `max temperature gradient`
- hotspot 面积占比
- top-5 hottest blocks

---

## 13. 现象成立的判定标准

若满足以下任意一组结果，即可认为该现象被初步验证：

### 判定 A：活动不均成立
- workload 驱动下，不同 PE/区域/bank 的 activity 明显不同。

### 判定 B：热集中成立
- 在总功耗接近的前提下，Hot-clustered case 的 `Tmax` 明显高于 Baseline。

### 判定 C：均衡缓解成立
- Hot-cold balanced case 的 `Tmax`、hotspot area、temperature gradient 低于 Hot-clustered。

### 判定 D：布局影响成立
- 同样的 block power 分布下，不同 placement 也会改变热点位置和峰值温度。

---

## 14. 推荐实验顺序（必须按这个顺序）

## Step 1：环境就绪
安装并验证：
- Chipyard + Gemmini
- Verilator
- Python 数据处理环境
- OpenROAD-flow-scripts
- OpenSTA
- HotSpot

## Step 2：生成 Gemmini RTL
- 用 GemminiRocketConfig 构建 Verilator simulator
- 导出 generated Verilog
- 确认 Gemmini 相关模块层次

## Step 3：跑基础测试
- 先跑功能验证
- 再跑 compute-heavy / memory-heavy / boundary-heavy workload
- 生成 VCD

## Step 4：提取活动率
- 做模块级、区域级、bank 级统计
- 输出 CSV
- 先判断活动是否不均

## Step 5：构建 block power
- 先用 activity-weighted 模型
- 输出 steady 和 transient 功耗文件

## Step 6：定义 macro grouping
- 生成 4 个 case
- 固定面积、数量、总功耗

## Step 7：构建 block-level top
- 生成抽象顶层网表
- 准备 ORFS 配置

## Step 8：跑 OpenROAD placement
- 获取 floorplan / placed DEF / timing 报告
- 确认各 case 可比较

## Step 9：导出 HotSpot 输入
- 由 placement 结果生成 `.flp`
- 由 power 数据生成 `.ptrace`

## Step 10：跑热仿真
- 先 steady-state
- 有差异后再做 transient

## Step 11：汇总结果
- 表格对比
- 热图可视化
- 输出第一轮结论

---

## 15. 第一轮不做的事情

为保证研究聚焦，第一轮明确不做：

1. 不重新手写一个新的 tensor core RTL；
2. 不直接把整个 SoC 做完整签核；
3. 不一开始追求精确绝对功耗；
4. 不先做复杂 thermal-aware optimizer；
5. 不在没有活动数据的前提下凭感觉设热点。

第一轮只做一件事：

> **用 Gemmini 生成的真实 accelerator 作为来源，建立 activity → power → placement → thermal 的最小可信闭环。**

---

## 16. 第二轮扩展方向（第一轮成功后）

第一轮验证成功后，再做：

1. **参数扫描**
   - 不同 Gemmini 阵列规模
   - 不同 tile 参数
   - 不同 dataflow

2. **更真实功耗**
   - 引入综合后功耗估计
   - 引入面积归一化功耗密度

3. **瞬态热分析**
   - phase-based workload
   - burst 热点观察

4. **优化策略验证**
   - hot-cold balanced grouping
   - thermal-aware macro placement
   - spacing/halo
   - runtime 错峰调度

---

## 17. 预期交付物清单

第一轮结束时，必须至少有以下文件：

### RTL / 仿真类
- Gemmini generated RTL
- 3~6 个 workload 的日志与 VCD
- activity CSV

### 物理类
- 4 个 case 的 ORFS 配置
- 4 个 case 的 DEF / placement 报告
- OpenSTA timing 报告

### 热类
- 4 个 case 的 HotSpot floorplan 文件
- steady-state 热结果
- 至少 1 组对比热图

### 文档类
- 实验记录
- 指标对比表
- 初步结论：现象是否存在

---

## 18. 最终一句话版本

本计划的执行原则是：

> **直接用 Gemmini 生成一个真实 tensor-core-like accelerator，先用 Verilator + Gemmini tests 采集真实活动率，再用 Python 建立 block-level 功耗，之后把 Gemmini 计算阵列与相关存储/控制模块抽象为多个 macro，用 OpenROAD-flow-scripts 跑 placement、用 OpenSTA 做时序 sanity check、用 HotSpot 做热仿真，最终比较不同 macro 分组方式是否会导致不同 hotspot 与峰值温度。**

