# Agent Task Checklist

## Universal Checklist

Before any substantial task:

- Read `AGENTS.md`.
- Read `docs/phase0tophase4_cadence_asap7_plan.md`.
- Read task-specific docs from `docs/README.md`.
- Check `git status --short`.
- Identify the active phase.
- Identify whether the task is documentation, script, experiment, or analysis.
- Confirm whether the task is within stages 0-4.
- Confirm whether the task would introduce a workload outside `tiled_matmul_os`, `tiled_matmul_ws`, `mvin_mvout`, a second Gemmini configuration, OpenROAD fallback, proxy power, or optimization work.
- For every Stage 0-4 retry, failed attempt, planned method change, or script/flow route change, update the relevant active docs before the next attempt.

If the answer is unclear, stop and ask the user.

## Documentation Task Checklist

- Read the target document before editing.
- Check related docs for consistency.
- Keep changes focused.
- Update `docs/README.md` when adding or retiring docs.
- Update `AGENTS.md` and helper docs when agent rules change.
- Re-read changed docs after editing.
- Run `git status --short`.

## Stage 0 Checklist

Goal: turn the plan into an executable signoff run definition.

Required inputs:

- `docs/phase0tophase4_cadence_asap7_plan.md`
- `docs/references/cadence_genus_innovus_edahub_smoke_2026-05-04.md`
- `docs/references/gemmini_flow_reference.md` and `docs/references/gemmini_workload_reference.md` if historical Gemmini context is needed
- `docs/references/legacy_openroad_proxy/` only if historical OpenROAD/proxy plan context is needed
- `docs/tool_environment_inventory.md`
- Existing workload and script paths

Must answer:

- What exact Gemmini module boundary is targeted?
- Which fixed Gemmini hardware configuration is selected?
- Where do the three fixed workloads come from, and what are their dimensions/checks?
- What waveform will Stage 1 capture for each workload?
- What is the stage 2 implementation top?
- How will stage 3 map activity and implementation data to grid power?
- What PACT, ATSim3D v1, and HotSpot inputs will stage 4 require?

Do not:

- Run large experiments.
- Modify Gemmini RTL.
- Start backend implementation.
- Start thermal simulation.
- Add complex automation for later stages.

Exit criteria:

- Plan is filled with concrete paths and commands.
- One hardware configuration and the three-workload set are selected and frozen.
- Inputs and outputs for stages 1-4 are defined.
- Unknowns and blockers are explicitly listed.

## Stage 1 Checklist

Goal: obtain RTL activity waveform and select useful time windows.

Before running:

- Confirm the fixed workload set and per-workload output paths.
- Confirm build/run script.
- Confirm output paths and run tag.
- Confirm waveform format and expected size.

Allowed:

- Build and run each of the three fixed workloads.
- Generate RTL VCD or equivalent waveform.
- Inspect hierarchy and high-activity windows.
- Produce activity summary.

Do not:

- Add workloads outside the fixed signoff set.
- Modify Gemmini structure.
- Start backend or thermal work.

Exit criteria:

- Functional run passes.
- Waveform exists and is readable.
- Key time windows are documented.
- Window precision is labeled: either target-scoped Gemmini active window, or coarse marker window with explicit Stage 3 refinement requirement.
- If the window is still coarse, the required target-window output paths and refinement method are documented for Stage 3 preflight.
- Activity summary report is written.

## Stage 1b Checklist

Goal: generate formal Gemmini-only r28 gate-level SAIF handoff artifacts for Phase3.

Required inputs:

- Stage 1 RTL VCDs for `mvin_mvout`, `tiled_matmul_ws`, and `tiled_matmul_os` under the active run root.
- Stage 1 selected windows:
  - `mvin_mvout`: `data_movement_active`, `66875550..601879950` ps.
  - `tiled_matmul_ws`: `steady_high_load`, `1072392550..3753373925` ps.
  - `tiled_matmul_os`: `steady_high_load`, `9272956950..10303285500` ps.
- r28 routed/export netlist: `physical/...20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v`.
- Full ASAP7 standard-cell Verilog under `/home/lisihang/asap7/asap7sc7p5t_28/Verilog/`.
- Simulation-only behavioral models for `mem_ext` and `mem_0_ext` under repository gate-sim collateral.

Before running:

- Confirm this is Gemmini-only boundary replay, not full-SoC gate simulation.
- Confirm formal run output directory is `gate_activity/phase1b_gate_saif_r28_20260515/` and stop if it already exists and is non-empty unless the user explicitly approves resume/overwrite.
- Confirm r28 is the primary netlist. Do not fallback to r2 without stopping and getting user confirmation.
- Confirm old `phase1b_mvin_mvout_boundary_replay_...` is historical validation only and excluded from new handoff.
- Confirm Verilator supports `--trace-saif`, `--verilate-jobs`, and `--output-split-ctrace`.
- Confirm fixed build parameters: `--verilate-jobs 192`, `--threads 16`, `make -j192`, `--trace-depth 9`, split `200/20/20`, `--compiler clang`, `--no-timing`, `-CFLAGS "-O0 -g0"`.
- Confirm `--hierarchical` is not used by default; stop and ask before trying it.
- Confirm r28 referenced-cell-only library is regenerated from r28 and includes required ASAP7 UDP primitives.
- Confirm the mvin top-port mapping smoke can map r28 `Gemmini` top ports to the RTL Gemmini scope. Only top ports are required for this preflight.

Allowed:

- Add or update repository-owned Phase1b scripts under `scripts/`.
- Add/update `scripts/README_phase1b.md` describing old and new Phase1b scripts.
- Generate inputs-only boundary vectors from Stage1 RTL VCDs.
- Build one shared r28 Verilator executable and reuse it for smoke and all three workload replays.
- Automatically or manually split generated C++ files larger than `128 MiB` inside the new run directory into 32 helper files before make.
- Run one no-compare SAIF smoke under `smoke_mvin_mvout_100cyc/`.
- Run formal workload SAIF replays one at a time in order: `mvin_mvout`, `tiled_matmul_ws`, `tiled_matmul_os`.

Do not:

- Modify Chipyard/Gemmini RTL.
- Modify r28 `Gemmini.routed.v` or any Stage 2 physical run source artifact.
- Use `--hierarchical` without user confirmation.
- Fallback to r2 without user confirmation.
- Reuse the old r2 `VGemmini` executable or old r2 referenced-cell library as the formal r28 build.
- Generate output compare/mismatch reports for the formal SAIF flow.
- Claim SDF timing simulation, commercial gate simulation, timing signoff, PG/DRC/IR/EM/LVS/foundry clean evidence, or full-SoC gate simulation.
- Put smoke SAIF or old validation artifacts into the Phase3 handoff manifest.

Exit criteria:

- Shared r28 executable build and referenced-cell/UDP manifests exist.
- Smoke SAIF exists, is non-empty, and records nonzero trace-enabled cycles.
- Formal `mvin_mvout`, `tiled_matmul_ws`, and `tiled_matmul_os` each have non-empty `gate_activity.saif`, trace/window manifests, replay summary, and activity manifest.
- Global `phase1b_gate_saif_handoff_manifest.json` lists only the three formal workload SAIFs as Phase3 consumable artifacts and explicitly excludes smoke and old validation artifacts.
- Global `phase1b_gate_saif_method_report.md` documents zero-delay/no-compare/fake-SRAM/raw-SAIF-hierarchy/r28-non-signoff limitations and the Phase3 SAIF mapping requirement.
- If GNU make segfaults after object compilation on the r28 SAIF build, object completeness against `VGemmini_classes.mk` is checked before any manual archive/link tail; the 2026-05-15 successful executable used this route.
- Long-running compile/replay monitoring followed the 20-minute wall-clock policy after startup.

## Stage 2 Checklist

Goal: produce ASAP7 standard-cell implementation outputs for the target design.

Before running:

- Confirm implementation top.
- Confirm full ASAP7 paths under `/home/lisihang/asap7`.
- Confirm Cadence Genus/Innovus entry points and license/threading evidence.
- Confirm ASAP7 NLDM cache under `.cache/asap7/`.
- Confirm Gemmini fake SRAM abstract policy and generated collateral under `.cache/fake_sram/asap7/Gemmini`; `/home/lisihang/fake_sram` is only the method reference unless the active plan changes.
- Confirm output directory.
- If fake SRAM LIB/LEF/stub policy changes, treat dependent Genus/Innovus checkpoints as stale and plan the rebuild point.
- Before the next Stage 2 attempt after any failure or plan update, update the active plan/report/issue log with the attempt status, evidence, and next-step plan.
- During Innovus route-stage runs, use relaxed monitoring intervals after progress is confirmed and never proactively terminate route unless the user explicitly requests it or the process exits/fails.
- Existing OpenROAD/ORFS/reduced-ASAP7 route/finish outputs are historical only. Do not use them as current handoff input.
- For the one reusable physical implementation, use Cadence CPU controls documented in the active plan and Cadence smoke reference; do not map OpenROAD `MAKE_JOBS`/`NUM_CORES` semantics onto Genus/Innovus.
- For the active plan, OpenROAD fallback remains a stop condition. As of 2026-05-12 and 2026-05-13, the user approved two scoped Stage 2 downgrades: Cadence/full-ASAP7 Stage 2 may proceed as `PG-open thermal proxy` if PG opens remain and are documented, and routed SDF may be waived for thermal-proxy acceptance if the SDF failure is documented.
- Use Python entry points / Python managers as the normal Stage 2 control surface. Generated Tcl may be inspected, run, or edited only for debugging, one-step recovery, or diagnostic export; required fixes must be moved back into Python-managed flow generation.
- Use meaningful run/result directory names that include design/config, library/collateral, clock target, purpose, and date or explicit tag. Hash-only result directories are not acceptable for active Phase 2 evidence.
- Confirm IO pin placement before expensive downstream runs: exported DEF must show all top-level pins `PLACED` or `FIXED`, and Innovus logs must not report unplaced top-level terms.
- Record non-clean causes separately: route DRC count/layers, PG connectivity violations, ASAP7 M10/Pad track collateral messages, and whether external DRC/LVS was run. Do not treat a zero process exit as clean signoff; PG opens must force a `PG-open thermal proxy` label.

Required outputs:

- Gate-level netlist
- DEF
- SPEF
- Routed SDF, or a documented 2026-05-13 routed-SDF waiver for thermal-proxy acceptance
- Instance location data or equivalent
- Area/cell statistics
- Timing report for record only

Do not:

- Optimize RTL.
- Chase timing closure.
- Add floorplan or placement optimization experiments.
- Accidentally implement the full SoC if the target is narrower.

Exit criteria:

- Outputs are non-empty and readable.
- Instance physical data can feed stage 3.
- Timing result is recorded even if not clean.
- Stage 2 acceptance level is explicit. Current user-approved level is `PG-open / DRC-open / routed-SDF-waived thermal proxy` when these limitations are documented; `higher-confidence/strict recovery` would require 0 PG special opens, usable routed SDF if timing simulation is claimed, and clean enough route/DRC evidence.

## Stage 3 Checklist

Goal: build grid-level power data from activity and implementation.

Before running:

- Confirm stage 1 time windows and refine coarse marker windows to Gemmini target activity if needed.
- Confirm stage 2 physical implementation files: current inputs must come from the new Cadence/Innovus physical implementation. Old OpenROAD/proxy files may be inspected only as historical references. If using a PG-open Stage 2 result, carry the non-signoff label into Stage 3 reports.
- Confirm final-report evidence paths under the active run directory; do not move tool logs out of their native output class just for naming consistency.
- Confirm Liberty/SPEF/VCD/SAIF input strategy; SDF is optional under the 2026-05-13 routed-SDF waiver. The active plan requires Cadence activity-aware power; fixed 1W proxy normalization is not accepted as a formal Stage 3 input.
- Confirm that VDD/VSS IR report values are not used as power or thermal inputs.
- Confirm RTL-to-gate/physical mapping manifest strategy, including blackbox/stub boundaries and fallback ratio reporting.
- Confirm grid size and units.
- Confirm the exact Stage 3 execution order from the active run Stage 3 preflight report before creating scripts or running heavy parsing.
- If any Stage 3 attempt fails or the method changes, update the Stage 3 method/preflight report and issue log before retrying.

Required outputs:

- Grid power CSV
- Transient power trace
- Top-N power instance report
- Top-N toggle instance report
- Method report
- Activity mapping manifest
- Instance-to-grid map and region power summary
- Hotspot/grid traceback report for future optimization-readiness

Do not:

- Analyze the full program if a selected window is enough.
- Add workloads outside the fixed signoff set.
- Start thermal optimization.

Exit criteria:

- Power grid sums are reasonable.
- Instance-to-grid mapping is documented.
- Output format is ready for PACT stage 4.

## Stage 4 Checklist

Goal: run PACT as the main thermal solver, ATSim3D v1 as a required independent steady solver, and HotSpot as coarse comparison.

Before running:

- Confirm PACT input file formats.
- Confirm ATSim3D v1 input LCF/config/simparams/floorplan/power formats; ATSim3.5D v2 is not required until its XML/config schema is validated.
- Confirm grid power trace exists.
- Confirm geometry and material assumptions.
- Confirm Stage 3/4 coordinate convention: main artifacts must use DEF physical grid, `grid_y=0` at die bottom.
- Confirm whether PACT raw row order needs `physical_grid_y = grid - 1 - pact_raw_row_y`, and plan raw-order audit filenames before generating reports.
- Confirm HotSpot coarse input generation method.

Required outputs:

- PACT physical-coordinate grid thermal result
- PACT coordinate manifest and raw row-order audit copy if applicable
- ATSim3D v1 input manifest, `.res` result, downsampled physical grid, hotspot rank, and ATSim-vs-corrected-PACT comparison
- Thermal heatmap data, with same-basename PNG companion for every generated SVG
- Standard-cell physical context overlay against corrected PACT/ATSim grids when standard-cell distribution is being inspected; standard-cell data comes from Stage 3 placed instance maps, not from ATSim `.res`
- HotSpot comparison result
- Stage 4 report

Do not:

- Turn results into thermal optimization.
- Add workload or configuration comparisons beyond the fixed signoff set.
- Add packaging or 3D extensions.

Exit criteria:

- PACT run completes.
- ATSim3D v1 run completes and writes the expected active-layer `.res`.
- Main PACT and ATSim grid/rank/heatmap outputs are in DEF physical coordinates; raw row-order coordinates are clearly labeled as audit-only.
- Heatmap and curves are generated or data exists to plot them.
- Every generated SVG has a same-basename PNG companion for VS Code/remote preview.
- HotSpot comparison is documented as coarse only.
- Limitations and next-stage needs are recorded.

## Stop Conditions

Stop and report if:

- A required tool is missing.
- A required path does not exist.
- The active plan conflicts with the user request.
- The next action would exceed stage 0-4.
- A command would overwrite archived artifacts.
- A heavy run would be needed but no output path or run tag is defined.
