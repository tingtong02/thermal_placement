# AGENTS.md

## Scope

This file is for Codex / ChatGPT agents working in this repository. It defines the mandatory project rules, reading order, execution order, and documentation maintenance expectations.

The current active project plan is:

- `docs/phase0tophase4_cadence_asap7_plan.md`

That document is the highest-priority project plan for technical scope, phase boundaries, selected hardware configuration, selected workload set, selected Cadence/full-ASAP7 backend route, and run directory conventions. The previous OpenROAD/reduced-ASAP7/proxy plans under `docs/references/legacy_openroad_proxy/` are historical references only. Other historical flow/workload/container references live directly under `docs/references/`. If there is any uncertainty about what to do next, read the active plan again before continuing.

## Reading Policy

On the first full repository onboarding, read broadly enough to understand the repository structure, active plan, tools, scripts, and archived context.

After that first onboarding, do not read every document on every task. Read only the necessary documents for the current task, then re-read additional documents only when you need to confirm a specific fact.

Always read at task start:

1. `AGENTS.md`
2. `docs/phase0tophase4_cadence_asap7_plan.md`
3. `docs/README.md`

Then read only the task-relevant docs:

- Cadence Genus/Innovus smoke and threading evidence: `docs/references/cadence_genus_innovus_edahub_smoke_2026-05-04.md`
- Legacy Gemmini/OpenROAD/proxy plans: `docs/references/legacy_openroad_proxy/`
- Historical Gemmini flow/workload/container references: `docs/references/gemmini_flow_reference.md`, `docs/references/gemmini_workload_reference.md`, `docs/references/gemmini_container_reference.md`
- Environment and tool inventory: `docs/tool_environment_inventory.md`
- Environment setup and known path conventions: `docs/gemmini_thermal_environment_setup.md`
- Known failures and fixes: `docs/gemmini_thermal_issue_log.md`
- PACT / Xyce / OpenMPI / slang / sv2v / yosys-slang: `docs/pact_slang_sv2v_yosys_slang_install_report.md`
- Historical archived Gemmini route: `docs/archive/gemmini_thermal_validation_2026-04-23/`

Reference documents are only references. They may contain historical commands, assumptions, or paths that do not apply to new development. Do not assume a reference document is directly reusable until you verify it against the active plan and current repository state.

Do not treat archived documents as active plans. Use them only as historical reference.

## Plan Re-Read Rule

Immediately re-read `docs/phase0tophase4_cadence_asap7_plan.md` when any of the following happens:

- Context or memory was compressed.
- You are uncertain about the active phase or scope.
- You are about to run a heavy command or experiment.
- You are about to modify scripts, flow definitions, or docs.
- You suspect an instruction conflicts with the active phase 0-4 plan.
- You resumed after a long interruption.

Do not continue from vague memory.

## Active Scope

The active route is stages 0-4 only:

```text
Stage 0 research definition
-> Stage 1 RTL activity waveform
-> Stage 2 Cadence Genus + Innovus full-ASAP7 standard-cell implementation
-> Stage 3 Cadence activity-aware grid-level power waveform
-> Stage 4 PACT thermal simulation + HotSpot coarse comparison
```

The active research target is Gemmini PE-array-related standard-cell thermal simulation:

- PE array
- Control logic
- Nearby datapath

The active workload set is restricted to the three workloads named in the active Cadence/full-ASAP7 plan: `tiled_matmul_os`, `tiled_matmul_ws`, and `mvin_mvout`. Do not add, remove, resize, or substitute workloads unless the plan is explicitly changed.

The active Stage 2 backend is Cadence Genus + Innovus with the external full ASAP7 PDK at `/home/lisihang/asap7`, defaulting to `asap7sc7p5t_28` 1x collateral and NLDM RVT/LVT/SLVT libraries cached under `.cache/asap7/`. OpenROAD/ORFS/reduced-ASAP7 outputs are legacy references only and must not be used as active Stage 3/4 handoff inputs.

As of 2026-05-12, the user accepted a Stage 2 quality downgrade to `PG-open thermal proxy` because PG special connectivity repair did not reach 0 opens. As of 2026-05-13, the user also accepted a routed-SDF waiver for the current research target. The accepted Stage 2 handoff is r28 under `PG-open / DRC-open / routed-SDF-waived thermal proxy` quality. Continue to use Cadence/full-ASAP7 outputs, but label downstream Stage 3/4 results as non-signoff when PG opens, route/DRC issues, or missing routed SDF remain. Do not present PG-open/SDF-waived outputs as PG-clean, DRC-clean, routed-SDF-complete, timing-signoff, IR/EM-clean, or foundry/signoff-clean evidence. Paths or tags containing `signoff` are retained historical names from before this downgrade and must not be interpreted as current signoff quality.

## Out Of Scope Unless User Explicitly Changes The Plan

Do not expand the task into:

- Thermal-aware optimization
- RTL optimization
- Timing closure optimization
- Workload sweeps beyond the fixed three-workload set
- Multiple array-configuration sweeps
- Full SoC physical implementation as the research target
- SRAM macro detailed thermal modeling
- Package / TSV / 2.5D / 3D-IC extensions
- Future stage 5+ work

If a user request appears to require one of these, stop and ask whether the active plan should be changed.

## Execution Order

For every stage or substantial task, follow this order:

1. Read the active plan and relevant docs.
2. Inspect current repository state.
3. Check required inputs and tool availability.
4. State the intended minimal changes or commands.
5. Make only necessary changes.
6. Run the smallest useful validation first.
7. Run heavier commands only after inputs are confirmed.
8. Record outputs, failures, and follow-up requirements.
9. Update relevant documentation when environment, plan, command, or result state changes.

Do not jump directly into implementation or heavy runs.

## Edit Rules

Do not use `apply_patch` in this repository.

Use ordinary shell-safe file editing methods instead, and keep edits small and reviewable. Before editing, read the target file and understand nearby context.

Do not make unrelated formatting-only changes.

Do not rewrite archived historical documents unless the task explicitly asks to edit an archive.

Do not modify ignored tool payloads under `tools/` or `third_party/` unless the user explicitly requests an environment repair. If ignored paths must change, document the change in an appropriate active doc.


## Python Environment Rule

All project Python commands must use the conda environment `thermal_placement`. Prefer entering through:

```bash
source tools/env_gemmini_thermal.sh
```

or explicitly using:

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python
```

Do not use the base conda Python or system Python for project scripts. If a Python package is genuinely needed for project data processing, visualization, testing, or flow scripts, it may be installed into the `thermal_placement` conda environment. Record any newly installed package, version, reason, and validation command in the relevant active environment/tool documentation. This authorization applies only to Python packages in this conda environment; missing non-Python system, EDA, compiler, or vendored tool dependencies still require stopping and reporting unless the user explicitly approves that repair.

## Experiment Rules

Before running an experiment:

- Confirm which stage it belongs to.
- Confirm expected inputs exist.
- Confirm expected outputs and output directory.
- Prefer smoke checks before heavy VCD, synthesis, P&R, or thermal runs.
- Use explicit run tags or stage-specific output paths when possible.
- Do not overwrite archived artifacts.
- After every failed attempt, planned route change, method change, or retry in any Stage 0-4 task, update the relevant active docs with the attempt status, failure evidence, current judgment, and next-step plan before starting the next attempt. This documentation-first rule is mandatory for all stages, not only Stage 2 route iterations.
- Route-stage OpenROAD runs may be silent for long periods. Monitor them at relaxed intervals after confirming progress, and never proactively terminate a running route stage unless the user explicitly asks to stop it or the process exits/fails on its own.

If a dependency is missing, stop and report:

- What is missing
- Which step needs it
- What evidence shows it is missing
- What the user needs to provide or approve

Do not silently install new non-Python dependencies unless the user explicitly authorizes it. Python package dependencies required by project scripts may be installed only into the `thermal_placement` conda environment under the Python Environment Rule, and must be documented.

## Documentation Update Rule

Whenever any of the following changes, update the relevant docs in the same task:

- Active plan or phase boundaries
- Environment variables or tool locations
- Tool versions or installed tool availability
- Script names, command entry points, or output paths
- Validation results or known failure modes
- Selected hardware configuration, workload set, or generated artifact conventions
- Agent rules in `AGENTS.md` or related helper docs

Use these docs as update targets:

- General agent rules: `AGENTS.md`
- Agent onboarding: `docs/agent_onboarding.md`
- Stage checklist: `docs/agent_task_checklist.md`
- Command reference: `docs/agent_command_reference.md`
- Active project plan: `docs/phase0tophase4_cadence_asap7_plan.md`
- Docs index: `docs/README.md`
- Tool inventory: `docs/tool_environment_inventory.md`
- Environment setup: `docs/gemmini_thermal_environment_setup.md`
- Known issues: `docs/gemmini_thermal_issue_log.md`

If you are unsure which doc to update, state that uncertainty and add a concise note to the most relevant active doc.

## Verification Expectations

For documentation-only changes:

- Re-read changed files.
- Check that links and paths are consistent.
- Run `git status --short`.

For script changes:

- Run syntax checks where applicable.
- Run the smallest relevant smoke test.
- Do not run heavy flows unless the task requires it and the active phase permits it.

For stage work:

- Follow `docs/agent_task_checklist.md`.
- Write or update the stage report required by `docs/phase0tophase4_cadence_asap7_plan.md`.

## Communication

Be concise and explicit.

When reporting progress, include:

- What was read
- What was changed
- What was run
- What passed or failed
- What remains blocked or undecided

Do not present historical archived results as current validation unless they were re-run in the current active route.
