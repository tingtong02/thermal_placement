# Stage 3 Tiled Matmul OS Baseline Preflight Plan

## Status

- Stage: 3 preflight / not yet executing grid-power generation
- Baseline workload: `tiled_matmul_os_baseline`
- Date: 2026-04-26
- Input acceptance state: Stage 2 is accepted only as `proxy / non-signoff`, not strict signoff P&R.
- Current action: prepare Phase 3 method, inputs, resource policy, and documentation rules before the user approves execution.

## Inputs Confirmed Before Start

### Stage 1 Activity Inputs

- Main manifest: `reports/stage1_tiled_matmul_os_baseline_manifest.txt`
- Activity summary: `reports/stage1_tiled_matmul_os_baseline_activity_summary.md`
- Window report: `reports/stage1_tiled_matmul_os_baseline_windows.md`
- Known limitation: the current `steady_high_load` interval is a coarse sustained-load marker. It is not yet a target-scoped PE-array/control/datapath power window, so Stage 3 must refine or justify the selected window before building the formal grid waveform.

### Stage 2 Physical Inputs

Stage 3 starts from the Stage 2 no-addermap proxy output directory:

```text
physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/
physical/stage2_tiled_matmul_os_baseline_asap7/logs/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/
physical/stage2_tiled_matmul_os_baseline_asap7/reports/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/
physical/stage2_tiled_matmul_os_baseline_asap7/objects/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/
```

Required physical handoff artifacts:

- `6_final.def`
- `6_final.v`
- `6_final.sdc`
- `6_final.spef`

Useful supporting artifacts:

- `6_final.odb`
- `6_final.gds`
- `5_route_drc.rpt`
- `6_report.log`
- `6_report.json`

Important path clarification:

- `6_report.log` and `6_report.json` are expected under the ORFS `logs/.../noaddermap/` tree.
- `5_route_drc.rpt` and most stage reports are expected under the ORFS `reports/.../noaddermap/` tree.
- This split is an ORFS output convention. Do not move the JSON/log files into `reports/` to make the names look uniform.

Known Stage 2 limitations inherited by Stage 3:

- Stage 2 is a proxy implementation with residual route DRC, blackboxed memories, filler-tap omissions, relaxed timing, and no signoff claim.
- No SDF handoff is recorded. Stage 3 must use `6_final.v`, `6_final.def`, `6_final.sdc`, and `6_final.spef` for physical/electrical context.
- `6_report.log` / `6_report.json` final-report VDD/VSS IR values are physical sanity evidence only. They must not be treated as power or thermal input.

## Documentation-First Retry Rule

For Stage 3 and all later Stage 0-4 work, every failed attempt, parser/extractor error, planned method change, script route change, or retry must update the relevant active documentation before the next attempt starts.

For Stage 3, update at least one of:

- this preflight/method report,
- the eventual Stage 3 stage report,
- `docs/gemmini_thermal_issue_log.md`,
- `docs/agent_command_reference.md` or `docs/tool_environment_inventory.md` if command/resource assumptions changed.

## Planned Execution Order

1. **Input preflight manifest**
   Verify Stage 1 activity files and Stage 2 physical handoff artifacts exist. Record exact paths, sizes, timestamps, and accepted caveats. Do not begin heavy parsing until this is complete.

2. **Target-scoped window refinement**
   Revisit the `steady_high_load` window and select a PE-array/control/nearby-datapath focused interval. Reject CPU-dominated or whole-program average activity as the Stage 3 baseline.

3. **Activity mapping manifest**
   Define how RTL/module/activity names are mapped to the placed netlist and physical instances. Record unmapped categories and any aggregation assumptions.

4. **Physical inventory**
   Parse or inspect `6_final.def`, `6_final.v`, `6_final.sdc`, and `6_final.spef` only as needed to confirm instance names, placement extents, supply/clock context, and available parasitic data.

5. **Grid and instance-to-grid mapping**
   Define the grid resolution, die/core bounds, target region bounds, and how standard-cell instance power is assigned to grid cells.

6. **Power model sanity selection**
   Choose the smallest defensible proxy model for dynamic/leakage power from the available activity and physical data. Record limits clearly if Liberty/internal-power data is incomplete or too expensive to use in the first pass.

7. **Grid power trace generation**
   Generate the Stage 3 grid-level power waveform in a new Stage 3 output directory. Preserve run tags and do not overwrite Stage 1/2 artifacts.

8. **Top-N and traceback reports**
   Emit ranked hot grids/instances/modules and trace each major contribution back to source activity and physical placement evidence.

9. **Stage 3 method and acceptance report**
   Write the Stage 3 report required by `docs/phase0tophase4_plan.md`, including limitations, acceptance status, and Stage 4 handoff readiness.

## Minimal Validation Before Heavy Work

Before any full VCD, DEF, SPEF, or netlist parse:

- verify required paths exist with `test -s` / `ls -lh`,
- inspect only headers or small samples,
- run parser smoke checks on bounded subsets where possible,
- document missing fields or naming mismatches before retrying.

## Resource And Parallelism Policy

- For ORFS/backend tasks, `MAKE_JOBS` means outer independent task count, not the internal thread count of one OpenROAD process.
- For the normal single Stage 3 preparation task, use `MAKE_JOBS=1` when ORFS/backend commands are involved.
- For a single OpenROAD/backend task, `NUM_CORES` may be up to 128.
- If two independent backend tasks are intentionally run concurrently, use `MAKE_JOBS=2` and at most `NUM_CORES=128` per task.
- If three or four independent backend tasks are intentionally run concurrently, use `MAKE_JOBS=3` or `MAKE_JOBS=4` and at most `NUM_CORES=64` per task.
- Do not set `MAKE_JOBS>4` for this project.
- Stage 3 Python parsing worker counts, if added, are separate from ORFS `MAKE_JOBS`; introduce them only after single-thread smoke validation and record the chosen limit in the Stage 3 report.
- Avoid concurrent large reads of the Stage 1 VCD and Stage 2 DEF/SPEF until memory and I/O behavior are measured.

## Planned Stage 3 Outputs

Stage 3 should create a new active output area, expected to include:

- input/preflight manifest,
- activity-to-instance mapping report,
- grid definition and instance-to-grid map,
- grid-level power waveform or time-series table,
- top-grid / top-instance / top-module reports,
- Stage 3 method and acceptance report.

The exact output directory should be confirmed at Stage 3 start and then recorded here plus in `docs/README.md` or `reports/README.md` if it becomes a stable report path.

## Readiness State

Phase 3 is prepared to start after user confirmation. No Phase 3 script execution, heavy parsing, or experiment run has been started by this preflight documentation task.

## Attempt Log

### 2026-04-26 target-window extraction method correction

Initial target-window extraction completed, but the Top-N toggles were dominated by `monitor.watchdog` simulation monitor signals under Gemmini scratchpad paths. These signals are useful simulator/debug context, but they are not PE-array/control/nearby-datapath standard-cell thermal activity targets.

Before retrying, the Stage 3 target-window extractor is updated to exclude paths containing `monitor` or `watchdog`. The next extraction must regenerate:

- `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`
- `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_bins.csv`
- `reports/stage1_tiled_matmul_os_baseline_target_windows.md`

### 2026-04-26 transient bin scaling method correction

The first grid build used non-zero-bin mean normalization for transient scaling. Because the candidate window contains many low background bins and one true target-active bin, this produced an inflated peak around 50x the requested `proxy_total_power_w`.

Before regenerating final Stage 3 power outputs, the transient scaling is changed to max-bin normalization: the highest target-activity bin represents `proxy_total_power_w`, and lower bins are scaled relative to that peak. This better matches the refined target-window interpretation and avoids overstating instantaneous proxy power.

### 2026-04-26 OpenSTA sanity retry

The first lightweight OpenSTA sanity attempt successfully read Liberty and the Stage 2 proxy netlist far enough to report blackbox creation for `mem_0_ext` and `mem_ext`, but failed because this local `sta` does not support `report_design_area`.

Before retrying, the sanity Tcl is reduced to commands supported by OpenSTA in this environment: read Liberty, read Verilog, link `Gemmini`, read SDC, and emit `report_checks`. SPEF remains recorded as a Stage 3 input but is not read in this lightweight sanity run.
