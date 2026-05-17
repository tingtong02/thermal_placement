# Docs Guide

## Active Plan

- [phase0tophase4_cadence_asap7_plan.md](/home/lisihang/thermal_placement/docs/phase0tophase4_cadence_asap7_plan.md)  
  当前唯一主计划：固定 `GemminiRocketConfig` / mesh16x16 tile1x1 DIM16 和 `tiled_matmul_os`、`tiled_matmul_ws`、`mvin_mvout` 三个 workload，使用 Cadence Genus + Innovus、外部 full ASAP7 PDK `/home/lisihang/asap7`、`asap7sc7p5t_28` 1x collateral、NLDM RVT/LVT/SLVT、fake SRAM abstract，完成 Stage 0-4 热研究验证。2026-05-12 用户接受 Stage 2 降级为 `PG-open thermal proxy`；2026-05-13 用户接受 routed-SDF waiver，当前 accepted handoff 是 r28 `PG-open / DRC-open / routed-SDF-waived thermal proxy`。2026-05-15 正式 Phase1b 改为 Gemmini-only r28 gate-level SAIF handoff：三个固定 workload 各生成一个 raw Verilator SAIF 供 Phase3 消费；旧 2026-05-14 `mvin_mvout` compare replay 仅保留为 historical validation。后续结果必须标注 non-signoff，不能声称 PG-clean、DRC-clean、routed-SDF-complete、SDF timing simulation、commercial gate simulation 或 timing signoff。

## Active Agent Docs

- [agent_onboarding.md](/home/lisihang/thermal_placement/docs/agent_onboarding.md)  
  Agent 接手仓库时的阅读顺序、仓库地图和启动注意事项。
- [agent_task_checklist.md](/home/lisihang/thermal_placement/docs/agent_task_checklist.md)  
  Stage 0-4 和通用任务检查表、停止条件和验收要求。
- [agent_command_reference.md](/home/lisihang/thermal_placement/docs/agent_command_reference.md)  
  常用环境检查、Cadence/ASAP7、Gemmini Stage 1、Stage 3/4 helper 命令索引；包含 Phase 2 Python-first Cadence flow、IO pin placement 检查和 GDS-to-PNG 版图导出参考。

## Active Environment And Tool Docs

- [gemmini_thermal_environment_setup.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_environment_setup.md)  
  环境入口、conda 规则、Cadence/full-ASAP7/fake-SRAM/thermal 工具路径和验证方式。
- [tool_environment_inventory.md](/home/lisihang/thermal_placement/docs/tool_environment_inventory.md)  
  当前可用工具、环境变量、命令入口和验证状态总表。
- [gemmini_thermal_issue_log.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_issue_log.md)  
  工具链、子模块、Cadence/ASAP7/fake-SRAM 和 thermal flow 已知问题与修复记录。
- [pact_slang_sv2v_yosys_slang_install_report.md](/home/lisihang/thermal_placement/docs/pact_slang_sv2v_yosys_slang_install_report.md)  
  PACT、Xyce、OpenMPI、slang、sv2v、yosys-slang 的安装和验证记录。slang/sv2v/Yosys 现在主要作为辅助工具或 legacy reference，PACT/Xyce 仍服务 Stage 4。
- [atsim_tool_guide.md](/home/lisihang/thermal_placement/docs/atsim_tool_guide.md)  
  ATSim3D v1/v2 本地路径、论文对应关系、输入输出、命令行入口、示例运行和验证状态。当前 Stage 4 强制 ATSim3D v1 steady comparison，ATSim3D v2 仍是可选探索。

## Active Run And Report Locations

当前 active run root（历史目录名保留 `__signoff`，不代表当前 r28 是 signoff-clean）：

- [runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff](/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff)

当前 active plan 允许保留并复用该目录中的 Stage 0/1 输入和结果。不要因为目录或 run tag 中包含 `signoff` 就删除或重命名；这些名称来自 Phase2 降级前的开发过程，是当前中间产物和 handoff 路径的一部分。包括：

- `rtl/`
- `workloads/`
- `sim/`
- `activity/`
- `reports/` 中的 Stage 0/1 报告

Stage 1b formal gate-level SAIF handoff 结果应写入：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/
```

该正式 Phase1b 只做 Gemmini-only r28 routed-netlist zero-delay boundary replay、direct SAIF generation 和 Phase3 handoff manifest，不做 full-SoC gate simulation、不做 output compare、不生成 mismatch report、不默认生成 gate VCD。三个正式 workload 均需产出一个 raw Verilator SAIF：`mvin_mvout`、`tiled_matmul_ws`、`tiled_matmul_os`。

2026-05-15 r28 shared Verilator executable 已完成：frontend 成功，`.o` 完整性检查为 328935/328935 present、0 missing，GNU make 尾段 139 通过先验对象完整性检查后的手工 archive/index/link 解决，`build/verilator_build/VGemmini` 已生成。

2026-05-16 Phase1b/Phase3 handoff status: mainline formal `mvin_mvout` SAIF is complete and is the only current Phase3 bring-up input candidate. Mainline `tiled_matmul_ws` and `tiled_matmul_os` replays are still running; accelerated `mvin_mvout`, `tiled_matmul_ws`, and `tiled_matmul_os` replays are also still running. Do not interrupt those processes. Until each run writes a non-empty SAIF plus `replay_summary.json` and `gate_activity_manifest.json` with `phase3_consumable=true`, it is not a Phase3 handoff input. Current Phase3 development is limited to single-workload `mvin_mvout` bring-up, with outputs under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/`. After the read-only preflight, the next approved step is script-only Cadence collateral generation under `power/mvin_mvout/cadence/`; it must not launch Innovus until separately confirmed. Script-only Cadence collateral has now been generated there; the generated runner remains unexecuted pending explicit approval. Phase3 planning now also requires a complete full-chip standard-cell instance geometry/power catalog for Phase4 local ATSim3D v1 hotspot refinement; Phase4 will first run grid-level thermal, then slice a hotspot ROI so each placed standard-cell instance in the ROI becomes one ATSim object. 


2026-05-15 acceleration attempt note: a harness-only binary/preparsed boundary-vector acceleration plan is being recorded under:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/accelerate/
```

This attempt is constrained to copied inputs, binary vector conversion, a new harness-only relink named `VGemmini_accelerate`, and direct SAIF replay with unchanged trace policy. It does not rerun Verilator frontend, does not modify r28 or RTL, does not use `--hierarchical`, and is not yet the default Phase1b handoff method. The user must be asked after smoke/runtime evidence before the main method is updated to use the accelerated route.

旧 Phase1b compare 验证产物保留在：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/
```

2026-05-14 old Phase1b result: the `mvin_mvout` validity-aware Verilator replay completed under the old validation directory. It found 146 mismatches, all on `auto_spad_id_out_a_bits_address`; offline shifted compare showed this is not a clean global one-cycle offset, though local valid bursts show one-beat lead behavior. User disposition: root cause remains not fully understood, but the mismatch has very low time-scale share and is not expected to significantly affect thermal simulation; do not repeatedly revisit it by default. The old report is now stored with the old evidence: [phase1b_mvin_mvout_gate_boundary_replay_20260514.md](/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/phase1b_mvin_mvout_gate_boundary_replay_20260514.md). It is not a Phase3 handoff artifact.

来自旧 OpenROAD/ORFS/reduced-ASAP7 的 Stage 2 产物不再是 active handoff 输入。新的 Stage 2 结果应写到 run root 内按 run tag 分隔的 physical path，例如：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/
```

Phase 2 Gemmini 主线在 2026-05-06 已重置到 dacs-style startup tree；2026-05-11 已新增 non-smoke `--run-innovus-full`、prelaunch summary、per-step manifests、artifact gates、explicit fake SRAM macro placement、PG connectivity reporting、CTS/routing M2-M8 alignment 和 Innovus-clean SDC handoff。2026-05-12 起 PG 0-open 不再是继续 Stage 3/4 的硬停止条件，但必须作为 non-signoff 降级项记录：

- [cadence_startup](/home/lisihang/thermal_placement/runs/cadence_startup)

该启动树必须使用父仓库 `thermal_placement` conda 环境；当前 Gemmini entry 支持 `--preflight`、`--dry-run`、`--write-scripts`、`--run-genus-elab`、`--run-genus-syn`、`--run-innovus-floorplan-smoke`、`--run-innovus-pnr-smoke`、`--run-innovus-cts-route-smoke`、`--run-innovus-full`、PG diagnostic/inspection helpers。其中 `--write-scripts` 只生成 Genus/Innovus Tcl，不启动商业工具；`--run-innovus-full` 是后续 Stage 2 non-smoke 入口，最终必须产出 routed DEF/Verilog/SPEF/GDS、`cts.enc`、`routing.enc`、post-route timing/area/power/DRC/connectivity reports；2026-05-13 起 routed SDF 可按 documented waiver 跳过。2026-05-12 状态：PG repair attempts 已停止并清理 r7-r16/r14 诊断目录；当前保留 r6 floorplan/full attempt 作为 blocker evidence。已知 completed diagnostics 未达到 0 special opens：baseline-style 为 336 opens，r15 direction-matched 为 481 opens，PG shorts 为 0。用户已接受后续 Stage 2 作为 `PG-open thermal proxy` 推进，并于 2026-05-13 接受 routed-SDF waiver；报告必须标注 non-signoff，不得声明 routed-SDF-complete、PG-clean、IR/EM-clean 或 foundry/signoff-clean。

旧 `stage2_cadence_python_flow_plan.md` 对应的 run-local 文件和 `physical/cadence/python_flow/` 均已删除；相关历史结论只保留在仓库级 issue log 中。

## References

- [references/cadence_genus_innovus_edahub_smoke_2026-05-04.md](/home/lisihang/thermal_placement/docs/references/cadence_genus_innovus_edahub_smoke_2026-05-04.md)  
  Cadence Genus/Innovus 本机安装、license、threading、edahub smoke 和 ASAP7 read-lib/read-LEF 证据。Cadence 参数设置和多线程策略必须参考该文档，不沿用 OpenROAD 参数语义。
- [references/legacy_openroad_proxy](/home/lisihang/thermal_placement/docs/references/legacy_openroad_proxy)  
  旧 OpenROAD/reduced-ASAP7/proxy 计划文档。可作历史证据，不得作为当前 active plan 或 handoff 方法。
- [references/gemmini_flow_reference.md](/home/lisihang/thermal_placement/docs/references/gemmini_flow_reference.md)  
  历史 Gemmini flow/script 参考。使用任何命令前必须按当前 Cadence/full-ASAP7 主计划重新验证。
- [references/gemmini_workload_reference.md](/home/lisihang/thermal_placement/docs/references/gemmini_workload_reference.md)  
  历史 workload 选择与 GEMM 证据参考。当前 active workload 集合仍固定为三个 workload。
- [references/gemmini_container_reference.md](/home/lisihang/thermal_placement/docs/references/gemmini_container_reference.md)  
  历史容器能力边界参考。
- [references/atsim_proxy_experiment_plan.md](/home/lisihang/thermal_placement/docs/references/atsim_proxy_experiment_plan.md)  
  历史 ATSim proxy rerun 计划。当前 Stage 4 只能消费非 proxy Stage 3 power grid。
- [references/atsim](/home/lisihang/thermal_placement/docs/references/atsim)  
  ATSim3D 与 ATSim3.5D 公开论文 PDF。
- [archive/gemmini_thermal_validation_2026-04-23](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23)  
  更早期 Gemmini thermal validation 文档归档。

## Legacy Docs Moved To Reference

2026-05-05 起，以下旧计划文档已移入 `docs/references/legacy_openroad_proxy/`：

- `phase0tophase4_plan.md`
- `phase0tophase4_signoff_multiworkload_plan.md`

以下历史参考文档直接放在 `docs/references/` 下：

- `gemmini_flow_reference.md`
- `gemmini_workload_reference.md`
- `gemmini_container_reference.md`
- `atsim_proxy_experiment_plan.md`

这些文件可能包含历史命令、路径、质量等级和 proxy 假设。使用其中任何结论前，必须对照当前 active plan 和当前仓库状态重新验证。

Accepted Stage 2 artifact folder:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/
```

Note: the parent run root contains `__signoff` only as a historical path label retained from the earlier stricter target. Do not delete or rename it; current quality is `PG-open / DRC-open / routed-SDF-waived thermal proxy`.

2026-05-13 Phase 2 handoff status: r28 is the accepted degraded Cadence/full-ASAP7 Stage 2 handoff for Stage 3/4 under `PG-open / DRC-open / routed-SDF-waived thermal proxy` quality. r28 restored the r20 `routing.enc` checkpoint, skipped `write_sdf` by user-approved waiver, generated `routed_sdf_waiver.md`, and produced routed DEF, routed Verilog, SPEF, GDS, `export_routing.enc`, post-route DRC/connectivity reports, and copied post-route timing/area/power reports. Do not present it as routed-SDF-complete, PG-clean, DRC-clean, IR/EM-clean, LVS-clean, or signoff-clean.
