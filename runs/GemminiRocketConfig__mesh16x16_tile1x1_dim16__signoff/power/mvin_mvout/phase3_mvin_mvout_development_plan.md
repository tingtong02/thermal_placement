# Phase3 mvin_mvout Development Plan

Date: 2026-05-16

Scope: single-workload `mvin_mvout` Phase3 bring-up from the completed mainline formal Phase1b r28 gate SAIF. All outputs are non-signoff because Stage2 r28 is `PG-open / DRC-open / routed-SDF-waived thermal proxy`, and the activity source is Verilator zero-delay SAIF, not SDF timing simulation or commercial gate simulation.

## Confirmed Decisions

### 1. Power Waveform Bring-Up Target

Decision: first Phase3 `mvin_mvout` bring-up accepts a **single-window average** power model.

Implementation meaning:

- Cadence reads the completed `mvin_mvout` SAIF and produces activity-aware average power for the full traced window.
- Stage3 will generate average instance power and average grid power from that result.
- The initial transient handoff will be clearly labeled `single_window_average` and may contain a single row or constant-power rows only for Stage4 interface smoke.
- This is not a true time-resolved waveform. Phase4 must not interpret it as cycle/bin-resolved thermal excitation.
- A real time-resolved waveform requires a later binned-SAIF or multi-window activity design and is out of scope for this first bring-up unless separately confirmed.

### 2. Grid Resolution And Coordinate Contract

Decision: the first Phase3 `mvin_mvout` bring-up uses a `64 x 64` uniform physical grid.

Implementation meaning:

- Grid cells cover the r28 DEF die area uniformly.
- Grid coordinates follow the active Stage4 convention: `grid_y=0` is die bottom, and `grid_y` increases upward.
- Stage4-facing transient/power-trace unit names use existing row-major order: `g0_0`, `g1_0`, ..., `g63_0`, `g0_1`, ..., `g63_63`.
- This keeps the first handoff compatible with existing Stage4 grid ingestion.
- Grid-resolution sweeps are out of scope for this first bring-up unless separately confirmed.

### 3. Instance-To-Grid Assignment

Decision: the first grid-level handoff assigns each standard-cell instance to one grid cell by its DEF placement point.

Implementation meaning:

- Parse r28 routed DEF instance placement coordinates.
- Exclude physical-only filler/tap/decap/tie cells from activity power mapping unless Cadence power reporting explicitly requires otherwise.
- Map each included standard-cell instance to exactly one `64 x 64` grid cell by placement coordinate.
- Add the full instance power to that grid cell.
- Do not perform cell bounding-box area overlap across multiple grid cells in the first bring-up. That would require a stronger LEF/size parser and is deferred unless separately confirmed.

### 4. ATSim3D Object-Level Handoff Requirement

Decision: Phase4 must add an ATSim3D v1 **layout-object-level** path in addition to the existing grid-level PACT, ATSim3D, and HotSpot comparisons.

Evidence from local ATSim3D v1 examples:

- Real entry: `scripts/run_atsim3d.sh --lcfFile <lcf.csv> --ConfigFile <config> --SimParamsFile <simparams>` using `third_party/ATSim3D_pub/src/ATSim3D.py` and Python 3.8 runtime.
- LCF fields observed in public examples: `Layer,Main_compo,Thickness (m),FloorplanFile,PowerFile,Clip_num_x,Clip_num_y,Clip_num_z`.
- Object floorplan fields observed in public examples: `UnitName,X,Y,Length (m),Width (m),ConfigFile,Label`; some examples also include `Z` and `Thickness (m)`. Coordinates and sizes are in meters.
- Object power fields observed in public examples: `UnitName,Power_dyn,Power_leak`. `UnitName` must match the floorplan object names.
- Config and SimParams follow INI-style ATSim3D v1 files, including material sections such as `[Si]`, `[Temperature]`, `[NoPackage]`, `[Leakage]`, plus solver/grid sections.

Phase3 impact:

- In addition to grid-level CSV/trace outputs, Phase3 must generate ATSim3D v1 object-level input candidates under `power/mvin_mvout/atsim3d_object/`.
- Required Phase3 object-level handoff files for the first version:
  - `phase3_mvin_mvout_atsim3d_object_flp.csv`
  - `phase3_mvin_mvout_atsim3d_object_power.csv`
  - `phase3_mvin_mvout_atsim3d_object_lcf.csv`
  - `phase3_mvin_mvout_atsim3d_object.config`
  - `phase3_mvin_mvout_atsim3d_object_simparams.config`
  - `phase3_mvin_mvout_atsim3d_object_manifest.json`
  - `phase3_mvin_mvout_atsim3d_object_method_report.md`
- These files must preserve the same non-signoff label and `single_window_average` power caveat.
- Confirmed refinement flow: Phase4 first runs the original grid-level PACT / grid-level ATSim3D / HotSpot flow, identifies hotspot ROI, then creates a local ATSim3D v1 instance-level refinement from the Phase3 complete instance handoff.
- Phase3 must provide complete full-chip standard-cell instance-level geometry and power data, because Phase4 is responsible for selecting and slicing the hotspot ROI.
- The local refinement object granularity is mandatory: **each placed standard-cell instance inside the selected hotspot ROI becomes one ATSim3D object**.
- Do not run full-chip ATSim3D with all standard-cell instances as objects in the first bring-up. The r28 DEF has `COMPONENTS 586968`, so full-chip per-instance ATSim3D is a scalability risk; full-chip grid-level thermal remains the coarse global pass.
- Existing grid-level outputs remain required for PACT/HotSpot and for grid-level ATSim3D comparison.

## Open Questions

The remaining Phase3 design decisions are still being resolved one at a time with the user.
