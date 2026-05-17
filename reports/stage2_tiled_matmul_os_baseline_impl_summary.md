# Stage 2 Tiled Matmul OS Baseline Implementation Summary

> Legacy note: this file documents the old OpenROAD/reduced-ASAP7 proxy route. It is not the current active Stage 2 handoff and must not be read as the current acceptance standard. The current accepted Stage 2 folder is:
>
> `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/`
>
> Current quality label: `PG-open / DRC-open / routed-SDF-waived thermal proxy`. The `__signoff` text in path names is historical and should not be interpreted as signoff quality.


## Phase 2 Closeout Record - 2026-04-26

This section is the objective closeout record for the current Phase 2 run. It supersedes earlier in-file attempt notes when they describe intermediate blockers.

### Acceptance Level

Phase 2 is accepted only as `proxy / non-signoff` for Stage 3 preflight. It is not accepted as strict P&R, DRC-clean, timing-closed, PDN-signoff, or SRAM detailed thermal modeling.

### Accepted Artifacts

All accepted artifacts are under `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/` unless noted otherwise.

| Artifact | Size | Role in later stages | Status |
| --- | ---: | --- | --- |
| `6_final.odb` | 3,741,011,680 bytes | OpenROAD physical database / instance geometry reference | accepted proxy |
| `6_final.def` | 2,498,823,083 bytes | Stage 3 instance-to-grid geometry input | accepted proxy |
| `6_final.v` | 343,483,229 bytes | Stage 3 gate-level netlist / instance-name input | accepted proxy |
| `6_final.sdc` | 136,668 bytes | Stage 3 timing constraint input | accepted proxy |
| `6_final.spef` | 2,120,927,954 bytes | Stage 3 parasitic proxy input | accepted proxy |
| `6_final.gds` | 2,624,530,664 bytes | final layout export / visualization reference | accepted proxy |
| `5_route.odb` | generated | routed checkpoint before final export | accepted proxy |
| `5_route.sdc` | generated | route-stage constraint copy | accepted proxy |
| `5_route_drc.rpt` | generated | detailed-route residual DRC evidence | caveat evidence |
| `drt_antennas.log` | generated, empty | antenna report; route log reports 0 net and 0 pin antenna violations | caveat evidence |
| `6_report.log` / `6_report.json` | generated under ORFS `logs/.../noaddermap/` | final-report evidence, including known GUI image-save failure; expected location, do not move | caveat evidence |
| `6_1_merge.log` | generated | KLayout DEF-to-GDS merge evidence; reports no orphan cells | caveat evidence |

No SDF artifact was generated. For this proxy acceptance, the documented substitute timing/parasitic package is `6_final.sdc + 6_final.spef + 6_final.v + 6_final.def`.

### Problems Encountered

- Default Stage 2 synthesis was blocked by the adder mapping path around `EXTRACT_FA`; the current path uses `FLOW_VARIANT=noaddermap`.
- Earlier generated memory macro LEF pins caused `DRT-0073 No access point`; the `PIN_THICKNESS=0.096` generated memory macro LEF cleared full-design memory macro `pin_access` with `macroNoAp=0`.
- Earlier global route failed with `GRT-0116` congestion; `PLACE_PINS_ARGS='-min_distance 0.54'` cleared the observed left-boundary congestion and allowed `5_1_grt.odb` generation.
- Detail route was capped at `DETAILED_ROUTE_END_ITERATION=8`; the run completed but still reported 6,988 residual detailed-route violations. This is the main DRC caveat.
- The first `make ... finish` wrote core final exports but exited at GUI image saving because current OpenROAD does not support the `get_scenes` command used by ORFS `save_images.tcl`.
- The second no-clean `make ... finish` skipped the completed `6_report` target, generated `6_final.sdc`, completed KLayout merge, and copied `6_1_merged.gds` to `6_final.gds`.
- `6_report.log` reports missing Liberty cells for `mem_ext`, `mem_0_ext`, `mem_1_ext`, and several `ICG*` masters. This is consistent with the memory/proxy setup and reduced library context, but it prevents strict signoff interpretation.
- `6_report.log` reports non-physical VDD/VSS static IR values. These values must not be used as PDN evidence, power input, or thermal input.
- `6_1_merge.log` uses `GDS_ALLOW_EMPTY=.*`; many standard-cell and memory LEF cells are treated as empty GDS, though KLayout reports no orphan cells. This is acceptable for the current proxy export but not a strict mask/GDS signoff claim.

### GUI Image Status and Possible Fixes

Existing images were generated before the GUI failure:

- `final_all.webp.png`
- `final_routing.webp.png`
- `final_placement.webp.png`
- `final_ir_drop.webp.png`
- `final_clocks.webp.png`

The failure occurs after these files, when ORFS `save_images.tcl` enters the clock-tree scene loop and calls `get_scenes`. The current OpenROAD build is GUI-enabled but does not provide that Tcl command.

Practical handling options:

1. Default for this project: do not chase GUI screenshots. If rerunning final reporting becomes necessary, prefer an OpenROAD build or invocation path that is not GUI-compiled, so `final_report.tcl` skips `gui::show save_images.tcl`. This avoids the `save_images.tcl` compatibility path entirely and keeps Phase 2 focused on DEF/netlist/SDC/SPEF/GDS/ODB artifacts.
2. If clean GUI screenshots later become explicitly required, use an OpenROAD build whose GUI Tcl supports `get_scenes` and the related clock-tree image commands, then rerun `make ... finish` or the relevant final GUI/image step.
3. Last-resort option only: add a documented local compatibility patch or wrapper for ORFS `save_images.tcl` that guards `get_scenes` with `info commands get_scenes` and skips only the unsupported clock-tree scene loop. Because ORFS lives under ignored `third_party/`, this should be treated as an environment/tool compatibility repair, not as a research-flow change.

This GUI issue is not a Phase 3 blocker because Phase 3 consumes DEF/netlist/SDC/SPEF/activity data, not GUI screenshots.

### Reference Suggestions for Phase 3

These are recommendations, not mandatory requirements:

- Start Phase 3 with a preflight manifest that lists the exact Stage 2 proxy inputs and their caveats.
- Use `6_final.def` for instance geometry and grid construction, `6_final.v` for gate instance names, `6_final.sdc` for timing context, and `6_final.spef` for parasitic proxy data.
- Do not use VDD/VSS IR report values as power or thermal inputs; they are PDN-analysis outputs from an invalid proxy setup.
- Record that no SDF is available and that any timing/power estimate is a proxy based on SDC/SPEF/Liberty/activity, not signoff power.
- Generate an activity mapping manifest before power-grid construction. The manifest should record RTL scope prefixes, gate/module prefixes, blackbox boundaries, matched/fallback ratios, and region/grid assignment rules.
- Treat memory array body power as out of scope or coarse context only. Keep PE/control/load-store nearby standard-cell power as the main target.
- Prefer a conservative first grid such as `64 x 64`; reduce to `40 x 40` or `32 x 32` only if data size or thermal runtime requires it, and record the change in the Stage 3 method report.
- Preserve `instance-to-grid`, `RTL-scope-to-region`, `module region`, `window power`, and fallback-ratio outputs so later thermal interpretation or future optimization work can trace hotspots back to instances/modules.

## Current Status - 2026-04-26

Stage 2 proxy completion is reached for the current `FLOW_VARIANT=noaddermap` A方案. This is not strict/signoff closure.

Route/export status:

- memory macro `pin_access` is cleared in full design with `macroNoAp=0`.
- the previous `GRT-0116` global-route congestion blocker is cleared by `PLACE_PINS_ARGS='-min_distance 0.54'`.
- detail route completed with `DETAILED_ROUTE_END_ITERATION=8` and wrote `5_2_route.odb`, `5_3_fillcell.odb`, and `5_route.odb`.
- final export completed after re-running `make ... finish` without cleaning; the second run reused the existing `6_report.log` and generated `6_final.sdc`, `6_1_merged.gds`, and `6_final.gds`.

Proxy acceptance evidence:

- non-empty final physical outputs exist: `6_final.odb`, `6_final.def`, `6_final.v`, `6_final.sdc`, `6_final.spef`, and `6_final.gds`.
- antenna check reported 0 net violations and 0 pin violations.
- KLayout merge reported no orphan cells in the final layout.
- final cell usage from `6_report.log`: total `1,338,035` cells, total area `3,015,219.67`.

Mandatory caveats:

- detailed route still has 6,988 residual violations after the capped 8th iteration; this is not DRC-clean.
- current bring-up/proxy knobs remain active: `noaddermap`, `REMOVE_ABC_BUFFERS=1`, `SKIP_REPORT_METRICS=1`, `GPL_TIMING_DRIVEN=0`, `SKIP_CTS_REPAIR_TIMING=1`, `MAX_PLACE_STEP_COEF=1.05`, and `PLACE_PINS_ARGS='-min_distance 0.54'`.
- no SDF was generated by this ORFS/OpenROAD finish path; Stage 3 must use SDC+SPEF+routed netlist as the available proxy timing/parasitic package and record the SDF gap.
- `6_report.log` contains a final GUI image-save error (`get_scenes` unsupported) from the first finish attempt. The second `make ... finish` completed successfully because the core final exports and `6_report.log` already existed; keep the GUI error as a known report artifact issue.
- VDD/VSS static IR values are non-physical in this proxy setup and must not be used as PDN signoff evidence.
- memory macros remain blackbox/proxy context, not SRAM detailed thermal modeling.

## Scope

The Stage 2 target remains:

- top: `Gemmini`
- process: reduced ASAP7 from `third_party/edahub/edahub/technology/asap7`
- active target: PE array, execute/control logic, load/store nearby datapath
- memory policy: `mem_ext`, `mem_0_ext`, and `mem_1_ext` are blackboxed and represented by Verilog + LEF stubs
- out of scope: full SoC backend, SRAM macro detailed thermal modeling, RTL optimization, timing closure optimization

## Results Reached So Far

The `FLOW_VARIANT=noaddermap` path has generated the following current artifacts under:

`physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/`

Generated and usable for Stage 3 proxy preflight:

- `5_route.odb`
- `5_route.sdc`
- `6_final.odb`
- `6_final.def`
- `6_final.v`
- `6_final.sdc`
- `6_final.spef`
- `6_final.gds`
- `6_report.log`
- `6_report.json` in the ORFS logs tree
- `5_route_drc.rpt`
- `drt_antennas.log`

Not generated:

- SDF. This is an explicit Stage 2 proxy caveat, not a strict acceptance result.

## Attempts and Lessons

### Synthesis

The original default adder mapping path stalled around `EXTRACT_FA`. The working branch is `FLOW_VARIANT=noaddermap`, which avoids the expensive default full-adder extraction path and successfully produced the mapped netlist.

Important threading rule:

- single baseline must use `make -j 1`
- `make -j > 1` caused ORFS multi-output synthesis recipes to run more than once against the same output path
- use `NUM_CORES` for OpenROAD internal threading; do not use `MAKE_JOBS` to accelerate one dependent baseline chain

### ORFS / OpenROAD Compatibility

The local OpenROAD binary is `v2.0-17598-ga008522d8`, and several ORFS Tcl scripts assumed commands or flags not available in this binary. The following local compatibility edits were required under `third_party/OpenROAD-flow-scripts/flow/scripts/`:

- `floorplan.tcl`: removed unsupported `repair_timing -sequence` usage and guarded `report_layer_rc`
- `report_metrics.tcl`: guarded `report_fmax_metric`
- `macro_place_util.tcl`: source manual `MACRO_PLACEMENT_TCL` when provided instead of forcing `rtl_macro_placer`
- `global_place_skip_io.tcl`: guarded unavailable `all_pins_placed`
- `global_place.tcl`: made `-force_center_initial_place` opt-in instead of default
- `cts.tcl`: made `-repair_clock_nets` opt-in instead of default

These are environment compatibility patches, not research optimizations.

### Macro and Memory Handling

Verilog blackboxes alone were insufficient because OpenROAD still needs physical LEF masters for blackbox instances. The following were added:

- `physical/stage2_tiled_matmul_os_baseline_asap7/tools/generate_memory_stub_lef.py`
- `physical/stage2_tiled_matmul_os_baseline_asap7/lef/gemmini_stage2_memory_macros.lef`
- `physical/stage2_tiled_matmul_os_baseline_asap7/macro_placement.tcl`
- `physical/stage2_tiled_matmul_os_baseline_asap7/pdn_stage2.tcl`

Manual macro placement replaced `rtl_macro_placer`, which failed on Gemmini memory pin geometry.

### Development Compromises Currently Used

These settings are deliberate Stage 2 bring-up compromises and must remain documented:

- `FLOW_VARIANT=noaddermap`: avoids the default adder mapping bottleneck; changes synthesis mapping quality versus the default ASAP7 route
- `REMOVE_ABC_BUFFERS=1`: skips expensive early buffer/timing repair paths and allows physical stages to proceed
- `SKIP_REPORT_METRICS=1`: avoids unsupported/heavy report paths during bring-up
- `GPL_TIMING_DRIVEN=0`: avoids timing-driven global placement cost while timing closure is out of scope
- `MAX_PLACE_STEP_COEF=1.05`: relaxes global placement step behavior enough to avoid unstable placement convergence
- `SKIP_CTS_REPAIR_TIMING=1`: avoids slow CTS timing repair; current stage only records timing, not closure
- `NUM_CORES=128`: used for OpenROAD internal P&R parallelism on this host for a single task
- `MAKE_JOBS=1`: deterministic outer task count for one baseline; previous `MAKE_JOBS>1` duplicated synth work in this local ORFS flow, while OpenROAD parallelism is controlled by `NUM_CORES`

These are acceptable for route bring-up and thermal-flow prototyping, but the reports must not describe them as signoff-quality implementation settings.

Fidelity acceptance policy:

- `strict` Stage 2 acceptance requires routed outputs plus readable timing/area/report artifacts, with debug/proxy knobs removed or justified by a documented equivalent-quality alternative.
- `proxy` Stage 2 acceptance may feed Stage 3 only as a thermal-flow prototype with explicit caveats.
- Current project priority is to complete the Stage 0-4 thermal-flow prototype; strict-fidelity recovery is optional future work, not required before proceeding after a usable proxy route exists.
- If strict Stage 2 is later required, recover fidelity one knob at a time in this order: reports/metrics, CTS timing repair, timing-driven placement, default or validated adder mapping.
- If any recovery step reintroduces tool incompatibility, excessive runtime, or route failure, keep the last usable result labeled as proxy and record the failed recovery step.

## Current Pin-Access Investigation

Observed failures:

1. First `5_1_grt` failure: off-grid memory stub pin shapes (`DRT-0416`).
2. Fix: snap LEF rectangles to the manufacturing grid.
3. Second failure: no access point for memory pins (`DRT-0073`).
4. Fix attempt: avoid macro-corner pin placement by applying `MARGIN=1.0` to track-center selection.
5. Full-design result: still failed at the same three `[0]` pins with 0.024um pin rectangles.
6. New fix attempt: widen memory macro pins to `PIN_THICKNESS=0.096`, matching reduced ASAP7 M4/M5 min-width expectation.
7. Validation: isolated single-`mem_ext` OpenROAD `pin_access` smoke passed with `macroNoAp=0`.
8. Additional 2026-04-25 validation: a small design containing `mem_ext`, `mem_0_ext`, and `mem_1_ext` all passed `pin_access` with `macroNoAp=0`; a PDN-enabled version of the same small design also passed.
9. Full-design validation: `pin_access` passed with `macroNoAp=0`; the 0.096um memory LEF is no longer the active blocker.
10. New blocker: `global_route` failed with `GRT-0116` congestion after 1:44:08, writing `5_1_grt-failed.odb` but not `5_route.odb`.

Why full reruns happen repeatedly:

- OpenROAD ODB files embed LEF macro geometry.
- Any change to `gemmini_stage2_memory_macros.lef` invalidates old `1_synth.odb`, floorplan, placement, and CTS ODBs.
- Running the route target after a LEF change correctly causes ORFS/make to rebuild prerequisite ODBs, otherwise route would still use stale macro pin geometry.

## Timing Target Question

Current SDC target is `500 MHz` / `2.000 ns`:

`physical/stage2_tiled_matmul_os_baseline_asap7/constraint.sdc`

Relaxing to `200 MHz` / `5.000 ns` may reduce synthesis, resize, CTS, and timing-repair pressure. It will not directly fix the current `GRT-0116` global-route congestion, because the latest failure is local routing capacity/overflow after `pin_access` already passed.

Expected impact of lowering the target:

- likely helps if future blockers are timing repair, buffering, or over-aggressive sizing
- limited help for global placement runtime, which is dominated by design size and density
- no direct help for the already-resolved memory macro pin access; only indirect impact on current local route congestion
- changes the mapped/sized netlist and absolute dynamic-power interpretation, so it must be documented if used

Given the current blocker, lowering the target is not the first fix. It remains a later pragmatic option only if sizing/buffering or timing repair becomes the dominant blocker.

## Precision and DRC Policy for Stage 2

Strict Stage 2 completion per active plan requires:

- gate-level netlist
- DEF
- SPEF
- SDF
- instance locations
- area/cell statistics
- timing report

For Stage 3 thermal mapping, the most critical data are:

- placed instance coordinates and cell areas
- consistent hierarchy / instance naming between activity and netlist
- a usable power estimation method
- a reproducible geometry grid

Small post-route DRC violations are not automatically fatal for thermal prototyping if OpenROAD still writes usable DEF/SPEF/SDF and the violations are documented. However:

- unresolved `pin_access` failure is currently fatal for the normal routed-flow path because it prevents route output generation
- if route completes with a small number of DRCs, Stage 3 can proceed with caveats
- if route cannot complete, Stage 3 can only proceed through a downgraded proxy path using placed/CTS coordinates and estimated or proxy parasitics
- proxy outputs must be labeled non-signoff and suitable for thermal-flow demonstration, not for physical-implementation claims

## Optional Fallback C: Memory Boundary Stub With Obstruction/Thermal Context

Status: optional and not executed. This is no longer required for memory `pin_access`, because the 0.096um A route passed `pin_access`; it remains a possible fallback if A-side global-route congestion fixes are judged too costly or unsuitable.

Fallback C 的核心是不再把 scratchpad / accumulator memory array 当作需要详细布线接入的 hard macro route target。Stage 2 仍保留 `Gemmini` 作为 implementation top，仍保留 PE array、execute/control、load/store 近邻数据通路和 memory 周边标准单元；但把 `mem_ext` / `mem_0_ext` / `mem_1_ext` 从“blackbox Verilog + hard macro LEF pins”改成可综合的 memory-boundary stub 或 wrapper boundary。

Implementation sketch:

- create a separate `FLOW_VARIANT`, for example `mem_boundary_stub`, so current `noaddermap` artifacts are not overwritten;
- replace routed hard-macro memory LEF usage with synthesizable boundary stubs;
- make the stubs consume address/write/control/data inputs so upstream memory-near logic is preserved;
- make the stubs produce non-constant read data/state so downstream datapath is not optimized into constants;
- add `keep` / `dont_touch` controls only where needed to prevent the boundary from disappearing;
- remove or bypass `gemmini_stage2_memory_macros.lef` in this variant, because the memory array itself is no longer a route target;
- validate by checking mapped netlist hierarchy, instance counts, placed regions, and Stage 3 power-mapping names before treating the result as usable.

Expected impact:

- avoids fake memory macro `pin_access` as the route-critical blocker;
- keeps more original Gemmini context than a smaller custom wrapper;
- aligns with the active plan statement that SRAM macro detailed thermal modeling is out of scope;
- changes the interpretation of memory-related power: memory array body power/geometry becomes a boundary/proxy assumption, while PE/control/load-store nearby standard cells remain the measured Stage 2 target;
- Stage 3/4 reports must explicitly state that SRAM array body thermal behavior is not modeled as a routed physical macro in this variant.

This direction should remain optional until the user decides that A-side congestion fixes are not the preferred path. It has not started in the current worktree.


## 2026-04-25 A Attempt Result And Optional Fallback Status

The full-design route attempt with `PIN_THICKNESS=0.096` regenerated the stale downstream implementation ODBs and reached `5_1_grt`. The previous fatal memory macro access symptom did not recur: `pin_access` completed and reported `macroNoAp=0`.

The run then completed naturally in `global_route` and failed with `GRT-0116 Global routing finished with congestion`. The final route log reports total overflow 1261, 1,327,547 routed nets, and `5_1_grt-failed.odb` as the saved artifact. The final congestion report has only 4 listed local overflow regions, concentrated near the left boundary around y=1715-1725um and involving mostly `io_ptw_*` / `io_resp_bits_data*` nets. The matching IO placement Tcl shows those bus pins assigned to the left boundary on M4, so the next A-side fix should start with IO pin spreading or boundary congestion relief.

The C path, `memory_boundary_stub + obstruction/thermal context`, is now recorded only as an optional fallback and has not started. Pure `mem_boundary_stub` without obstruction/thermal context remains out of scope unless the user changes the plan.

## Route Monitoring Rule

Route stages can run silently for long periods. Future monitoring should use relaxed intervals after progress is confirmed, and agents must not proactively terminate route; only the user may request active route termination, or the process may exit/fail on its own.

## Route Repair Attempt 1 Plan

Attempt 1 will keep the current A方案 and current bring-up/proxy knobs, but rerun place/CTS/route with more aggressive IO pin spreading: `PLACE_PINS_ARGS='-min_distance 0.54'`. The goal is to reduce the left-boundary `io_ptw_*` / `io_resp_bits_data*` congestion that caused `GRT-0116`. This is not a high-fidelity recovery attempt and any successful route remains non-signoff/proxy.

Because `PLACE_PINS_ARGS` affects `3_2_place_iop`, the attempt must regenerate downstream place/CTS/route artifacts rather than only rerunning `5_1_grt`.

## Current Route Repair Budget

Before entering C or restoring high-fidelity settings, attempt at most three small A-side fixes for the current `GRT-0116` congestion. The attempts must stay narrow and documented:

1. IO pin spreading / left-boundary congestion relief for the `io_ptw_*` and `io_resp_bits_data*` region.
2. Route capacity or global-route adjustment if IO spreading is insufficient.
3. Placement density or congestion knob adjustment if local overflow persists.

After each failed attempt or route-plan change, update the issue log and this Stage 2 summary before starting the next attempt. Any successful output from the current bring-up settings remains proxy / non-signoff.

## Next Practical Options

1. Analyze the A-route congestion failure before changing memory strategy. Focus on the final `GRT-0116` overflow near the left boundary and the large local routing resource reductions caused by blockages.
2. Consider A-side adjustments first if they are small and still within Stage 2 scope: IO pin placement/boundary spreading, route capacity/adjustment settings, placement density/congestion knobs, or allowing normal route runtime without premature interruption.
3. Treat `memory_boundary_stub + obstruction/thermal context` as an optional fallback only if A-side congestion fixes are judged too costly or incompatible with the research target.
4. Keep any current result labeled `not complete` or `proxy-progress`; strict Stage 2 still requires `5_route.odb`, routed DEF, SPEF/SDF, instance locations, area/cell statistics, and timing report.

## 2026-04-26 Detail Route Resume Plan

The latest Stage 2 status is no longer the old `GRT-0116` global-route failure. Attempt 1 added `PLACE_PINS_ARGS='-min_distance 0.54'`, regenerated downstream place/CTS/route state, passed full-design memory `pin_access` with `macroNoAp=0`, completed `global_route` with zero final congestion overflow, and wrote `5_1_grt.odb` plus `route.guide`.

The most recent run was interrupted externally during `5_2_route detail_route`, not by an observed OpenROAD fatal error. The last log shows detailed routing had reached the 4th optimization iteration, about 70% complete, with DRC/route violations trending down from 49276 after iteration 3 to about 29949 at iteration 4/70%. No `5_2_route.odb`, `5_route.odb`, routed DEF, SPEF, or SDF exists yet.

This resume plan was executed later: ORFS started from `5_1_grt.odb`, completed capped `5_2_route`, and generated `5_route.odb` plus final proxy exports.

Monitoring rule for this rerun: watch normally until the first detailed-route optimization iteration has completed and printed its violation summary. After that point, detailed route may run silently or slowly; reduce monitoring to roughly once per hour and do not terminate the route unless the user asks or the process exits/fails.

Acceptance note: even if route completes, this Stage 2 result remains `proxy / non-signoff` because the current bring-up knobs remain active. Phase 2 proxy acceptance requires non-empty routed physical outputs and explicit caveats; strict fidelity recovery remains optional future work.

## 2026-04-26 Route Completion Result

The resumed route run started from the existing `5_1_grt.odb`, entered `5_2_route` directly, and used `DETAILED_ROUTE_END_ITERATION=8` as planned. ORFS did not rerun synthesis, floorplan, placement, CTS, or `5_1_grt`.

Result:

- `5_2_route detail_route` completed all 8 optimization iterations and wrote `5_2_route.odb`.
- `5_3_fillcell` completed and wrote `5_3_fillcell.odb`.
- ORFS copied `5_3_fillcell.odb` to `5_route.odb`.
- Antenna check reported 0 net violations and 0 pin violations.
- Design area after detailed route: 3,115,146 um^2, 28% utilization; after filler: 3,442,900 um^2, 31% utilization.
- Final detailed-route violation count after the capped 8th iteration: 6,988. Dominant residual categories are M8/M9 min-step/min-width, M1 metal spacing/eolKeepOut, and M8 shorts.

This is a routed proxy result, not a DRC-clean or signoff result. It is suitable for continuing Phase 2 proxy export and Stage 3 thermal-flow prototyping only if the final export files are generated and the DRC caveat is kept in downstream reports.

This route-completion note is superseded by the later finish/export result and Phase 2 proxy acceptance conclusion below.

## 2026-04-26 Finish/Export Attempt Result

`make ... finish` continued from the completed `5_route.odb` and did not rerun route. It completed `6_1_fill`, entered `6_report final_report`, and wrote the key final implementation outputs:

- `6_final.odb` (3,741,011,680 bytes)
- `6_final.def` (2,498,823,083 bytes)
- `6_final.v` (343,483,229 bytes)
- `6_final.spef` (2,120,927,954 bytes)
- `6_report.log` / `6_report.json`
- final GUI image files through `final_clocks.webp.png`

The make target still exited with code 2 at the very end of `final_report.tcl` while saving GUI images:

- `[ERROR GUI-0070] Error: save_images.tcl, 77 invalid command name "get_scenes"`
- `Error: final_report.tcl, 72 GUI-0070`

This is not a route/export data failure: the routed database, final DEF, final Verilog, and SPEF already exist and are non-empty. No SDF file was produced by this ORFS/OpenROAD finish path, so Stage 3 must treat SDC+SPEF+routed netlist as the available proxy timing/parasitic package and explicitly record the SDF gap.

Additional caveats from `6_report.log`:

- `mem_ext`, `mem_0_ext`, `mem_1_ext`, and several `ICG*` masters have signal pins but no Liberty cell.
- Static IR reports for VDD/VSS are numerically non-physical in this proxy setup and must not be used as PDN signoff evidence.
- Cell usage summary: total `1,338,035` cells, total area `3,015,219.67`.

This intermediate failure note is superseded by the later successful no-clean `make ... finish` run and Phase 2 proxy acceptance conclusion below.

## 2026-04-26 Phase 2 Proxy Acceptance Conclusion

Phase 2 is accepted at `proxy / non-signoff` level for continuing to Stage 3 preflight.

This acceptance is based on non-empty final outputs from the completed route/finish flow: `6_final.odb`, `6_final.def`, `6_final.v`, `6_final.sdc`, `6_final.spef`, and `6_final.gds`. It is not a strict physical-implementation signoff because residual route DRC remains, SDF is unavailable, current bring-up knobs remain active, memory macros are proxy blackboxes, and final IR numbers are not meaningful.
