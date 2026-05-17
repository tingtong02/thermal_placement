# Optional Phase 2 Sweep Notes

This document records optional parameter guidance for possible future Phase 2 sweeps across different Stage 2 targets or variants. It is not a mandatory development plan and does not change the active Stage 0-4 route in `docs/phase0tophase4_plan.md`.

The current active baseline remains the single `tiled_matmul_os` Gemmini target unless the user explicitly changes the plan.

## Intended Use

Use this note only when a later task explicitly asks to sweep multiple Phase 2 implementation targets or parameter variants. Before running any sweep, still re-check the active plan, current repository state, tool availability, and output directory isolation.

## Suggested Sweep Defaults

| Item | Suggested default | Rationale / caveat |
| --- | --- | --- |
| Timing target | `200 MHz` / `5.000 ns` | Future sweep variants should relax the current 500 MHz target to reduce pressure on placement/CTS/route. This is expected to improve routability and reduce timing-repair cost, but it changes the timing context and must be recorded in every variant manifest. |
| Outer parallel jobs | Maximum `MAKE_JOBS=4` independent jobs | `MAKE_JOBS` is outer task concurrency, not OpenROAD internal threading. Use only with isolated output directories or unique `FLOW_VARIANT` values. |
| Detail route iteration cap | `DETAILED_ROUTE_END_ITERATION=8` | Keeps route runtime bounded and matches the current proxy acceptance style. Results with residual DRC must be labelled `proxy / non-signoff`. |
| Per-variant output isolation | Unique `FLOW_VARIANT` or output directory per sweep point | Prevents jobs from overwriting ORFS intermediate targets and reports. |
| GUI screenshots | Disabled / skipped by default | GUI images are not needed for Phase 3/4. Prefer a non-GUI final-report path if final report must be rerun. |

## Current Bring-Up / Proxy Settings To Record

The current accepted Phase 2 proxy result used several settings that helped bring-up and runtime, but they reduce fidelity or completeness. Future formal-quality flows should not keep them silently.

| Setting / behavior | Current use | Why it was used | Formal-flow expectation |
| --- | --- | --- | --- |
| `FLOW_VARIANT=noaddermap` | Enabled | Avoided the default adder mapping / `EXTRACT_FA` blocker. | Restore default adder mapping or document an equivalent, validated alternative before claiming strict fidelity. |
| `REMOVE_ABC_BUFFERS=1` | Enabled | Part of the current no-adder-map bring-up path. | Re-evaluate and remove unless still required with evidence. |
| `SKIP_REPORT_METRICS=1` | Enabled | Avoided/report-side overhead and helped keep the flow moving. | Do not skip metrics in formal comparison or strict acceptance. |
| `GPL_TIMING_DRIVEN=0` | Enabled | Reduced placement/timing-driven complexity for bring-up. | Restore timing-driven placement for formal-quality runs. |
| `SKIP_CTS_REPAIR_TIMING=1` | Enabled | Avoided extra CTS timing-repair cost/failure surface. | Restore CTS timing repair when timing/power fidelity matters. |
| `MAX_PLACE_STEP_COEF=1.05` | Override | Helped placement progression in current proxy route. | Treat as a tuned placement parameter; record per sweep point and compare with default if fidelity matters. |
| `PLACE_PINS_ARGS='-min_distance 0.54'` | Override | Cleared observed left-boundary global-route congestion. | Keep only with rationale; record because it changes IO pin placement behavior. |
| No SDF generated | Current outcome | ORFS/OpenROAD finish path did not emit SDF for this proxy run. | Strict Stage 2 should restore/produce SDF or explicitly define the substitute timing/parasitic method. |
| Non-physical VDD/VSS IR report | Present in current reports | PDN/proxy context is not valid for IR signoff. | Do not use as power or thermal input; rerun with proper PDN context before any IR claim. |
| Residual detailed-route DRC | 6,988 violations after 8 iterations | Route was accepted as proxy only. | Formal route must either clean DRC or document why each class is irrelevant to the downstream claim. |
| GUI image failure ignored | Accepted | GUI screenshots are not required artifacts. | Keep ignored unless screenshots are explicitly needed. |

## Sweep Parallelism Guidance

A later sweep may run multiple independent ORFS jobs at once, but each job must have isolated outputs. Do not use outer parallelism to run multiple targets into the same `FLOW_VARIANT`.

Resource limits for outer parallel runs:

- `MAKE_JOBS=1`: normal single-task path; one task may use up to `NUM_CORES=128` after command-path smoke.
- `MAKE_JOBS=2`: two independent jobs; each job may use up to `NUM_CORES=128` if memory and IO are acceptable.
- `MAKE_JOBS=3` or `MAKE_JOBS=4`: three or four independent jobs; each job may use up to `NUM_CORES=64`.
- Avoid any run pattern that writes multiple jobs into the same `FLOW_VARIANT` or output directory.

Before launching a full sweep, run one smoke variant through at least `synth` and one representative variant through `route` to estimate runtime, peak memory, and output size.

## Additional Efficiency Options

These are optional efficiency ideas. They should be used only if they do not undermine the downstream Stage 3/4 thermal objective.

| Option | Expected benefit | Fidelity / downstream impact |
| --- | --- | --- |
| Stage targets incrementally (`synth`, then `floorplan/place`, then `route`, then `finish`) | Avoids rerunning earlier stages after a late failure. | Low impact if outputs are tracked correctly. |
| Reuse proven memory blackbox/stub setup | Avoids re-debugging memory `pin_access` and macro placement. | Low impact for the current standard-cell thermal target; memory array body remains proxy/out-of-scope. |
| Keep `DETAILED_ROUTE_END_ITERATION=8` for exploratory sweeps | Bounds long route tails. | Medium impact: residual DRC means proxy-only, but Stage 3 can still use placement/routing geometry cautiously. |
| Skip GUI screenshots | Removes a known fragile final-report path. | No meaningful impact on Phase 3/4 because screenshots are not consumed. |
| Use `200 MHz` for all sweep points | Reduces timing pressure and may reduce repair/runtime instability. | Changes timing context; all comparisons must use the same target. |
| Preflight required outputs before heavy downstream steps | Catches missing DEF/netlist/SPEF/SDC early. | No fidelity impact. |
| Limit sweep dimensions first | Prevents combinatorial explosion. | No fidelity impact if the selected dimensions match the research question. |
| Keep Stage 3 grid moderate for exploratory variants | Reduces power/thermal post-processing size. | Must record grid size; too coarse a grid can blur hotspot localization. |

Avoid these as default efficiency shortcuts for formal-quality runs:

- Dropping SPEF/parasitic context entirely.
- Using VDD/VSS IR reports from the current proxy PDN as power or thermal input.
- Changing workload, top scope, memory policy, and timing target simultaneously without a manifest.
- Treating residual DRC proxy routes as signoff-clean implementations.

## Per-Variant Manifest Checklist

Every sweep point should record at least:

- target module or design scope
- workload anchor
- `FLOW_VARIANT`
- timing target and SDC path
- memory policy and LEF/stub path
- exact ORFS command or script entry
- `MAKE_JOBS`, per-job `NUM_CORES`, output isolation, and host resource assumption
- detail-route iteration cap
- whether bring-up/proxy knobs are enabled
- final available artifacts: ODB, DEF, netlist, SDC, SPEF, SDF if any, GDS if any
- residual route DRC count and antenna result
- whether the result is `strict`, `strict candidate`, or `proxy / non-signoff`
- downstream caveats for Stage 3/4

## Current Recommendation

For future exploratory Phase 2 sweeps, use a `200 MHz` timing target, isolated variants, no GUI screenshots, and `DETAILED_ROUTE_END_ITERATION=8`. Treat resulting designs as exploratory proxy outputs unless the skipped fidelity steps are restored and the route/report artifacts meet strict acceptance requirements.
