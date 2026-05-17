# Stage 3 Fidelity Recovery Roadmap

## Purpose

This note records the recommended changes for a later rigorous standard-cell power / activity waveform flow. It is a reference roadmap, not a change to the current completed Stage 0-4 prototype route.

Current Stage 3 status remains:

- accepted level: `proxy / thermal-flow prototype`
- current output: grid-level proxy power waveform from target RTL activity, DEF placement, Liberty area, and region mapping
- current limitation: not signoff power and not SPEF/SAIF/SDF-based standard-cell power

Use this note when the project goal changes from "run the thermal-flow prototype" to "build a more accurate standard-cell power/activity input for thermal simulation."

## Target To Improve Toward

The stricter target is:

```text
chip design + workload simulation data
-> target operation window
-> standard-cell / gate-level activity or power
-> grid-level thermal input that more accurately reflects workload and operation mode
```

The current flow already reflects the workload and operation mode at a proxy level. The missing rigor is mainly in standard-cell timing/physical fidelity and per-cell/per-net power calculation.

## Current Gaps

### Phase 2 Physical Package Is Proxy / Non-Signoff

Current Phase 2 produced usable `DEF + netlist + SDC + SPEF`, but it still has:

- residual detailed-route DRC
- severe timing violations in OpenSTA sanity
- bring-up/proxy knobs such as `noaddermap`, `REMOVE_ABC_BUFFERS=1`, `GPL_TIMING_DRIVEN=0`, `SKIP_CTS_REPAIR_TIMING=1`, and `SKIP_REPORT_METRICS=1`
- memory macro blackbox/proxy treatment
- no SDF

This limits any downstream claim about standard-cell power accuracy.

### Phase 3 Uses Activity/Area Proxy Power

Current Phase 3 uses:

```text
Stage 1 target RTL VCD activity
-> target region activity
-> Stage 2 DEF instance placement
-> Liberty cell area
-> region/area proxy power distribution
```

It does not yet use:

- gate-level SAIF
- SDF-annotated gate simulation
- SPEF-based per-net capacitance power
- per-cell internal/switching/leakage power from a signoff-like power engine

## Recommended Upgrade Path

## Phase 1 / Stage 1 Changes

Do not change the workload unless the active plan changes. Keep the single `tiled_matmul_os_baseline` workload.

Recommended changes:

1. Keep the full-SoC RTL VCD as the workload and operation-mode evidence.
2. Keep the target-scoped window refinement as the activity-window authority.
3. Add or preserve an explicit activity-window acceptance record:
   - final target window
   - candidate coarse window
   - target scopes included
   - monitor/debug scopes excluded
   - reason CPU-reference / boot activity is excluded

Relevant current output:

- `reports/stage1_tiled_matmul_os_baseline_target_windows.md`
- `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`
- `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_bins.csv`

Goal:

- ensure later gate-level or SPEF-based power uses the correct Gemmini active interval, not whole-program average activity.

## Phase 2 / Stage 2 Changes

This is the highest-priority fidelity recovery area.

Create a new isolated recovery variant; do not overwrite the current `noaddermap` proxy outputs. Suggested naming:

```text
FLOW_VARIANT=timing_recovery
```

Recommended order:

1. **Restore reports and metrics**
   - Try removing `SKIP_REPORT_METRICS=1` or use an equivalent supported report path.
   - Goal: recover complete timing/area/report evidence.
   - Stop and document if local ORFS/OpenROAD incompatibilities reappear.

2. **Restore CTS timing repair**
   - Try removing `SKIP_CTS_REPAIR_TIMING=1`.
   - Goal: reduce severe clock/timing artifacts before using results for power.

3. **Restore timing-driven placement**
   - Try `GPL_TIMING_DRIVEN=1` or default timing-driven placement.
   - Goal: improve timing-aware physical structure and reduce unrealistic long paths.

4. **Evaluate `REMOVE_ABC_BUFFERS=1` removal**
   - Try restoring normal buffer/timing repair behavior.
   - Goal: avoid power/area distortion from skipped synthesis/repair behavior.

5. **Evaluate `noaddermap` replacement or justification**
   - Default adder mapping previously blocked around `EXTRACT_FA`.
   - For rigorous standard-cell power, either recover default mapping or document a validated alternative.
   - Compare at least cell count, area, major cell-type mix, and runtime if both variants can run.

6. **Check SDF capability**
   - Determine whether this ORFS/OpenROAD path can emit SDF for the routed design.
   - If SDF is unavailable, document why and use a non-SDF STA/SPEF/Liberty power path instead.

7. **Keep memory boundary scoped**
   - Do not expand into SRAM macro detailed thermal modeling unless the active plan changes.
   - Ensure PE array, control logic, and load/store nearby standard-cell logic remain present and mapped.

Expected better Phase 2 package:

```text
DEF + gate netlist + SDC + SPEF + timing reports + area/cell reports
optional SDF if available
reduced timing/DRC/proxy caveats compared with current noaddermap proxy
```

## Phase 2.5 Optional Gate-Activity Preparation

If the rigorous route needs gate-level SAIF, add a Phase 2.5 preparation step before rebuilding Phase 3.

Possible levels:

### Level A: Pseudo-SAIF / Activity Annotation

Use Stage 1 target-window RTL activity and mapping rules to generate a tool-readable activity annotation for the gate netlist.

Outputs to consider:

- `power/stage3_tiled_matmul_os_baseline_activity.saif`
- `reports/stage3_tiled_matmul_os_baseline_activity_mapping_report.md`

This is still approximate, but it is closer to a power-tool input than region CSV alone.

### Level B: Real Gate-Level Simulation

Run gate-level simulation for the selected target window and generate SAIF or gate-level VCD.

Inputs ideally include:

- recovered gate netlist
- SDF if available
- workload/testbench strategy
- selected target interval

This is heavier and should only be attempted after Phase 2 physical/timing recovery makes the gate netlist credible enough.

## Phase 3B Changes

Add a more rigorous Phase 3B path instead of replacing the current proxy path immediately.

Suggested naming:

```text
reports/stage3b_tiled_matmul_os_baseline_* 
power/stage3b_tiled_matmul_os_baseline_*
```

Recommended Phase 3B flow:

1. **Input manifest**
   - record recovered Phase 2 variant
   - record whether SDF exists
   - record activity source: real SAIF, pseudo-SAIF, or RTL-mapped activity

2. **Power-tool smoke**
   - test whether OpenSTA/OpenROAD or another available tool can read:
     - Liberty
     - gate netlist
     - SDC
     - SPEF
     - activity annotation / SAIF
   - output at least a small power report or clear failure evidence.

3. **Per-instance power extraction**
   - generate per-instance or per-cell power with separate fields:
     - internal power
     - switching power
     - leakage power
     - total power
     - activity source
     - mapping confidence

4. **Grid aggregation**
   - aggregate per-instance power to the existing grid scheme.
   - preserve instance-to-grid and hotspot traceback outputs.

5. **Fallback accounting**
   - record unmapped activity ratio.
   - record unmapped cell ratio.
   - record cells/nets without Liberty, SPEF, or activity.

Target Phase 3B output schema:

```text
instance, master, region, x_dbu, y_dbu, grid_x, grid_y,
internal_power_w, switching_power_w, leakage_power_w, total_power_w,
activity_source, mapping_confidence
```

The grid power output should then be derived from `total_power_w`, not area-based proxy distribution.

## Phase 4 Changes

Phase 4 should not repair activity or timing. It should consume the best available Phase 3/3B power input.

Recommended input priority:

1. `stage3b` SPEF/SAIF/Liberty-based grid power if available
2. current `stage3` proxy grid power if only prototype input exists

Every Phase 4 report should record an input-power level:

```text
input_power_level = proxy_area_activity
input_power_level = pseudo_saif_spef_power
input_power_level = gate_saif_spef_power
input_power_level = signoff_like_power
```

Do not make absolute thermal-accuracy claims unless the input power level justifies them.

## Minimal Practical Sequence For A Later Rigorous Run

Recommended sequence when the user wants to run the stricter flow:

1. Re-read active plan and this note.
2. Create a new Phase 2 recovery variant; do not overwrite `noaddermap` outputs.
3. Restore report/metrics first.
4. Restore CTS timing repair.
5. Restore timing-driven placement.
6. Evaluate normal buffer/adder mapping recovery.
7. Check SDF generation capability.
8. Re-run Stage 2 finish/export for the recovered variant.
9. Build Phase 3B activity annotation or real gate-level SAIF.
10. Run SPEF/Liberty/activity-based per-instance power smoke.
11. Generate full per-instance power and grid aggregation.
12. Run Stage 4 using the highest-quality grid power available.

## Stop Conditions

Stop and report before continuing if any of the following happens:

- restoring timing/report knobs reintroduces ORFS/OpenROAD command incompatibility
- route cannot complete for the recovered variant
- timing remains so broken that gate-level simulation is not meaningful
- SDF generation is unavailable and no alternative activity/power annotation route works
- power tool cannot consume the gate netlist/SPEF/activity combination
- memory blackbox handling starts to expand into SRAM macro detailed thermal modeling without explicit plan change

## Current Recommendation

For the current active Stage 0-4 prototype, proceed to Phase 4 using the existing Stage 3 proxy outputs.

For a later rigorous standard-cell power/thermal run, first add Phase 2 recovery and Phase 3B as described above. The most important change is not in Phase 4; it is improving Phase 2 physical credibility and Phase 3 per-instance power calculation.
