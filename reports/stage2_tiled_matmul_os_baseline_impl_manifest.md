# Stage 2 Tiled Matmul OS Baseline Implementation Manifest

> Legacy note: this file documents the old OpenROAD/reduced-ASAP7 proxy route. It is not the current active Stage 2 handoff and must not be read as the current acceptance standard. The current accepted Stage 2 folder is:
>
> `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/`
>
> Current quality label: `PG-open / DRC-open / routed-SDF-waived thermal proxy`. The `__signoff` text in path names is historical and should not be interpreted as signoff quality.


## Final Phase 2 Proxy Artifact Manifest - 2026-04-26

Acceptance level: `proxy / non-signoff`.

Base variant directory:

`physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/`

| File | Size | Status | Notes |
| --- | ---: | --- | --- |
| `6_final.odb` | 3,741,011,680 bytes | accepted | final OpenROAD database |
| `6_final.def` | 2,498,823,083 bytes | accepted | primary Stage 3 geometry input |
| `6_final.v` | 343,483,229 bytes | accepted | gate-level netlist input |
| `6_final.sdc` | 136,668 bytes | accepted | timing constraint input |
| `6_final.spef` | 2,120,927,954 bytes | accepted | parasitic proxy input |
| `6_final.gds` | 2,624,530,664 bytes | accepted | GDS export / visualization reference |
| `5_route.odb` | generated | accepted | route checkpoint |
| `5_route.sdc` | generated | accepted | route-stage SDC copy |
| `6_1_merged.gds` | 2,624,530,664 bytes | accepted | source copied to `6_final.gds` |

Relevant report/log directories:

- ORFS logs: `physical/stage2_tiled_matmul_os_baseline_asap7/logs/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/`
- ORFS reports: `physical/stage2_tiled_matmul_os_baseline_asap7/reports/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/`

`6_report.log` and `6_report.json` are final-report artifacts emitted under the ORFS logs tree. This is expected for the current flow and these files should not be moved into the reports tree merely for naming consistency.

| File | Actual location class | Status | Notes |
| --- | --- | --- | --- |
| `5_2_route.log` | logs | accepted evidence | detail route reached capped iteration 8 and wrote `5_2_route.odb` |
| `5_3_fillcell.log` | logs | accepted evidence | filler completed and route result copied to `5_route.odb` |
| `5_route_drc.rpt` | reports | caveat evidence | residual DRC exists; not signoff clean |
| `drt_antennas.log` | reports | caveat evidence | empty file; route log reports 0 antenna net/pin violations |
| `6_report.log` | logs | caveat evidence | contains first-attempt GUI image-save failure and final-report summaries |
| `6_report.json` | logs | caveat evidence | final report metrics json from first finish attempt |
| `6_1_merge.log` | logs | accepted evidence | KLayout merge completed; no orphan cells reported |

Missing or intentionally not accepted:

- No SDF file was emitted by this ORFS/OpenROAD flow.
- VDD/VSS IR report values are not accepted as PDN, power, or thermal inputs.
- GUI screenshots are auxiliary evidence only; they are not acceptance-critical artifacts.

## Current Goal

Build an ASAP7 reduced standard-cell implementation entry for the fixed `tiled_matmul_os` baseline without expanding the target to the full SoC.

## Implementation Boundary

- implementation top: `Gemmini`
- workload anchor: `tiled_matmul_os`
- dataflow: output-stationary
- target logic:
  - PE array
  - execute/control logic
  - load/store nearby datapath
- memory policy:
  - `mem_ext`
  - `mem_0_ext`
  - `mem_1_ext`
  are blackboxed with Verilog stubs and physical LEF macro stubs

## Tool and Environment

- conda env: `thermal_placement`
- Yosys: `tools/oss-cad-suite/oss-cad-suite/bin/yosys`
- SystemVerilog frontend: `yosys-slang`
- OpenROAD: `tools/openroad-prebuilt/root/usr/bin/openroad`, `v2.0-17598-ga008522d8`
- OpenSTA: `tools/opensta/bin/sta`
- reduced ASAP7 path: `third_party/edahub/edahub/technology/asap7`
- ORFS platform overlay: `configs/openroad/reduced_platforms/asap7/config.mk`

## Active Stage 2 Files

- design config: `physical/stage2_tiled_matmul_os_baseline_asap7/config.mk`
- SDC: `physical/stage2_tiled_matmul_os_baseline_asap7/constraint.sdc`
- filelist: `physical/stage2_tiled_matmul_os_baseline_asap7/src/gemmini_stage2_sources_reduced.f`
- filelist generator: `scripts/build_stage2_gemmini_filelist.py`
- memory blackbox Verilog: `physical/stage2_tiled_matmul_os_baseline_asap7/src/gemmini_stage2_memory_blackboxes.sv`
- memory LEF generator: `physical/stage2_tiled_matmul_os_baseline_asap7/tools/generate_memory_stub_lef.py`
- memory LEF: `physical/stage2_tiled_matmul_os_baseline_asap7/lef/gemmini_stage2_memory_macros.lef`
- macro placement: `physical/stage2_tiled_matmul_os_baseline_asap7/macro_placement.tcl`
- PDN override: `physical/stage2_tiled_matmul_os_baseline_asap7/pdn_stage2.tcl`
- run script: `scripts/run_stage2_openroad.sh`
- no-adder-map helper: `scripts/run_stage2_openroad_noaddermap.sh`

## Current Config Highlights

- `DESIGN_NAME = Gemmini`
- `SYNTH_HDL_FRONTEND = slang`
- `SYNTH_HIERARCHICAL = 1`
- `SYNTH_BLACKBOXES = mem_ext mem_0_ext mem_1_ext`
- `SYNTH_MINIMUM_KEEP_SIZE =`
- `ADDITIONAL_LEFS = $(DESIGN_HOME)/lef/gemmini_stage2_memory_macros.lef`
- `CORE_UTILIZATION = 25`
- `PLACE_DENSITY = 0.35`
- `MAX_PLACE_STEP_COEF = 1.01` in config, commonly overridden to `1.05` for the current placement run
- timing target: `500 MHz` / `2.000 ns`

## Current Working Command Pattern

Single-baseline runs must keep `make -j 1`:

```bash
source tools/env_gemmini_thermal.sh
make -j 1 -C "$FLOW_HOME" \
  PLATFORM_HOME="$TP_ROOT/configs/openroad/reduced_platforms" \
  DESIGN_CONFIG="$TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/config.mk" \
  YOSYS_EXE="$YOSYS_EXE" OPENROAD_EXE="$OPENROAD_EXE" OPENSTA_EXE="$OPENSTA_EXE" \
  FLOW_VARIANT=noaddermap REMOVE_ABC_BUFFERS=1 SKIP_REPORT_METRICS=1 \
  NUM_CORES=128 GPL_TIMING_DRIVEN=0 MAX_PLACE_STEP_COEF=1.05 \
  SKIP_CTS_REPAIR_TIMING=1 PLACE_PINS_ARGS='-min_distance 0.54' \
  DETAILED_ROUTE_END_ITERATION=8 \
  "$TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/5_route.odb"
```

Reason for this command shape:

- `FLOW_VARIANT=noaddermap`: produces mapped netlist by avoiding the default `EXTRACT_FA` bottleneck
- `MAKE_JOBS=1`: deterministic outer task count for one baseline; previous higher values duplicated ORFS multi-output recipes
- `NUM_CORES=128`: uses OpenROAD internal P&R threads for the single task
- `PLACE_PINS_ARGS='-min_distance 0.54'`: A-side IO spreading fix that cleared the previous `GRT-0116` global-route congestion
- `DETAILED_ROUTE_END_ITERATION=8`: caps detailed-route optimization iterations for the current Phase 2 proxy route
- `REMOVE_ABC_BUFFERS=1`, `SKIP_REPORT_METRICS=1`, `GPL_TIMING_DRIVEN=0`, `SKIP_CTS_REPAIR_TIMING=1`: bring-up compromises to avoid nonessential timing/report paths while Stage 2 is being used as a thermal-flow prototype

## Output Directories

- results: `physical/stage2_tiled_matmul_os_baseline_asap7/results/`
- logs: `physical/stage2_tiled_matmul_os_baseline_asap7/logs/`
- reports: `physical/stage2_tiled_matmul_os_baseline_asap7/reports/`
- objects: `physical/stage2_tiled_matmul_os_baseline_asap7/objects/`

Current active variant:

`physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/`

## Current Artifact Status

Available:

- `1_2_yosys.v`
- `1_2_yosys.sdc`
- `1_synth.odb`
- `1_synth.sdc`
- `2_floorplan.odb`
- `2_floorplan.sdc`
- `3_place.odb`
- `3_place.sdc`
- `4_cts.odb`
- `4_cts.sdc`
- `5_1_grt.odb`
- `5_2_route.odb`
- `5_3_fillcell.odb`
- `5_route.odb`
- `5_route_drc.rpt`
- `drt_antennas.log`


Available after final finish/export:

- `6_1_fill.odb`
- `6_1_fill.sdc`
- `6_final.odb`
- `6_final.def`
- `6_final.v`
- `6_final.sdc`
- `6_final.spef`
- `6_1_merged.gds`
- `6_final.gds`
- `6_report.log`
- `6_report.json` in the ORFS logs tree
- final GUI image files (`final_all.webp.png`, `final_routing.webp.png`, `final_placement.webp.png`, `final_ir_drop.webp.png`, `final_clocks.webp.png`)

Known finish/export caveats:

- no SDF emitted by this ORFS/OpenROAD flow
- first `6_report` attempt exited at GUI image saving (`get_scenes` unsupported), after core final exports were written; the subsequent `make ... finish` completed by reusing `6_report.log` and finishing `6_final.sdc` plus GDS packaging
- `6_1_merge.log` uses `GDS_ALLOW_EMPTY=.*`; many standard-cell and memory LEF cells are ignored as empty GDS, but KLayout reports no orphan cells in the final layout
- VDD/VSS static IR output is non-physical and is not PDN signoff evidence

Phase 2 proxy acceptance status:

- accepted as `proxy / non-signoff` input for Stage 3 preflight
- not accepted as strict P&R, DRC-clean, timing-closed, or PDN-signoff implementation

## Current Route Status

The previous `DRT-0073 No access point` memory macro access blocker has been cleared by the `0.096um` generated memory macro LEF in full-design route: `pin_access` reported `macroNoAp=0`. The later `GRT-0116` congestion blocker was cleared by the A-side IO spreading attempt with `PLACE_PINS_ARGS='-min_distance 0.54'`.

The current route was resumed from the existing `5_1_grt.odb` into `5_2_route` and completed with `DETAILED_ROUTE_END_ITERATION=8`. It wrote `5_2_route.odb`, `5_3_fillcell.odb`, and `5_route.odb`; antenna reported 0 net violations and 0 pin violations. Because detailed route still has 6,988 residual violations after the capped 8th iteration and the bring-up knobs remain active, this is a routed proxy / non-signoff result, not strict Stage 2 closure.

## Candidate Variant: `mem_boundary_stub`

Status: not executed yet. This is a possible fallback direction if full-design route still fails on generated memory macro `pin_access`.

The variant would keep `Gemmini` as the implementation top but stop treating the scratchpad/accumulator array bodies as routed hard macros. Instead, `mem_ext` / `mem_0_ext` / `mem_1_ext` would be replaced or wrapped by synthesizable boundary stubs that preserve memory-near control and datapath activity while avoiding fake macro LEF route pins.

Required conventions if attempted:

- use a new `FLOW_VARIANT=mem_boundary_stub`;
- do not overwrite the current `noaddermap` route artifacts;
- remove or bypass `ADDITIONAL_LEFS = $(DESIGN_HOME)/lef/gemmini_stage2_memory_macros.lef` for this variant;
- document all RTL/config changes before running synthesis;
- verify that PE array/control/load-store nearby logic is still present and not optimized away;
- label Stage 3/4 outputs as memory-boundary/proxy results, not SRAM macro detailed thermal results.

## Stage 2 Completion Definition

Strict completion requires non-empty, readable:

- gate-level netlist
- DEF
- SPEF
- SDF or an explicit documented SDF-unavailable status with substitute timing/parasitic inputs
- instance physical locations
- area/cell statistics
- timing report
- DRC/timing/fidelity caveats resolved or explicitly ruled out for the claim being made

Current Phase 2 target is proxy completion for the Stage 0-4 thermal-flow prototype. Proxy acceptance may proceed after final export files are generated from `5_route.odb`, verified non-empty, and labeled non-signoff with the residual DRC and bring-up/fidelity caveats.
