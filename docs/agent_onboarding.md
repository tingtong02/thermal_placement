# Agent Onboarding

## Purpose

This document helps Codex / ChatGPT agents enter the repository without relying on stale context. It complements `AGENTS.md` and the active project plan.

## First Five Minutes

Run or inspect in this order:

```bash
pwd
git status --short
git rev-parse --show-toplevel
git remote -v
```

Then read:

1. `AGENTS.md`
2. `docs/phase0tophase4_cadence_asap7_plan.md`
3. `docs/README.md`

For the first full repository onboarding, also read enough of the task-relevant docs to understand the active flow, workload options, and tool state. For later tasks, do not reread every document by default; use the table below and read only what the task requires.

If context has been compressed or you are uncertain, return to `docs/phase0tophase4_cadence_asap7_plan.md` before acting. If a specific fact is uncertain, read the narrowest relevant reference doc instead of re-reading the entire documentation set.

For any Stage 0-4 failed attempt, retry, or planned method/script route change, update the relevant active documentation before starting the next attempt. This rule is stage-wide, not limited to Stage 2.

## Active Route Summary

The active route is stage 0-4 only:

```text
research definition
-> RTL waveform
-> Cadence Genus + Innovus full-ASAP7 standard-cell implementation
-> Cadence activity-aware grid-level power waveform
-> PACT thermal simulation + HotSpot coarse comparison
```

The current plan is not a thermal optimization plan. It fixes one Gemmini hardware configuration and three workloads. Stage 2 uses Cadence Genus + Innovus, external full ASAP7 at `/home/lisihang/asap7`, `asap7sc7p5t_28` 1x collateral, NLDM RVT/LVT/SLVT, and Gemmini-specific fake SRAM abstract generated under `.cache/fake_sram/asap7/Gemmini` with `/home/lisihang/fake_sram` used only as a method reference. As of 2026-05-12, the user approved a Stage 2 downgrade to `PG-open thermal proxy`; as of 2026-05-13, the accepted Stage 2 handoff is r28 `PG-open / DRC-open / routed-SDF-waived thermal proxy`; do not present such outputs as PG-clean, DRC-clean, routed-SDF-complete, timing-signoff, or foundry/signoff-clean evidence. Do not add optimization, configuration sweeps, extra workloads, OpenROAD fallback, or fixed-power proxy unless the user changes the plan.

## Important Repository Areas

| Path | Meaning |
| --- | --- |
| `docs/phase0tophase4_cadence_asap7_plan.md` | Highest-priority active Cadence/full-ASAP7 plan. |
| `docs/references/legacy_openroad_proxy/` | Historical OpenROAD/reduced-ASAP7/proxy plans; reference only. |
| `docs/references/gemmini_flow_reference.md` | Historical Gemmini flow/script reference; verify before reuse. |
| `docs/references/gemmini_workload_reference.md` | Historical workload reference; verify against the active fixed workload set. |
| `docs/references/gemmini_container_reference.md` | Historical container capability reference. |
| `AGENTS.md` | Agent rules and execution policy. |
| `docs/README.md` | Active documentation index. |
| `scripts/` | Existing automation entry points. |
| `workloads/` | Existing local workload sources. |
| `configs/asap7_full/` | Active full-ASAP7 PDK manifests and Cadence Tcl helpers. |
| `configs/fake_sram/` | Fake SRAM manifests for Cadence and helper flows. |
| `configs/reduced_techlibs/` | Legacy reduced edahub technology library adapters. |
| `docs/archive/` | Historical docs only, not active plans. |
| `archive/` | Historical generated artifacts only, not active outputs. |
| `tools/` | Local ignored tool installs. |
| `third_party/` | Local ignored third-party source trees. |

## Environment Entry

Use:

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

Then use the lightest check that matches the task. For full environment validation:

```bash
scripts/check_environment.sh
```

Do not run full or heavy flows just to gather context.

## Active Docs To Read As Needed

| Need | Read |
| --- | --- |
| Current phase plan | `docs/phase0tophase4_cadence_asap7_plan.md` |
| Cadence smoke/threading | `docs/references/cadence_genus_innovus_edahub_smoke_2026-05-04.md` |
| Legacy Gemmini script map | `docs/references/gemmini_flow_reference.md` |
| Legacy workload context | `docs/references/gemmini_workload_reference.md` |
| Legacy OpenROAD/proxy plans | `docs/references/legacy_openroad_proxy/` |
| Tool state | `docs/tool_environment_inventory.md` |
| Environment setup | `docs/gemmini_thermal_environment_setup.md` |
| Known failures | `docs/gemmini_thermal_issue_log.md` |
| PACT/Xyce/slang/sv2v | `docs/pact_slang_sv2v_yosys_slang_install_report.md` |
| Stage command checklist | `docs/agent_command_reference.md` |
| Stage execution checklist | `docs/agent_task_checklist.md` |
| Stage 3 startup | `reports/stage3_tiled_matmul_os_baseline_preflight_plan.md` |

Reference docs are not guarantees of reusability. Treat them as historical or supporting evidence, then verify applicability against `docs/phase0tophase4_cadence_asap7_plan.md` and the current repository state.

## What Not To Do During Onboarding

Do not:

- Generate RTL.
- Build or run Verilator simulators.
- Run OpenROAD-flow-scripts.
- Run Cadence Genus/Innovus beyond explicit smoke checks.
- Run PACT or HotSpot examples.
- Modify source files.
- Restore archived files into active paths.

Only do those after the active phase requires them and inputs are checked.
