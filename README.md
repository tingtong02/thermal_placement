# Thermal Placement

Thermal Placement is a research workspace for thermal-aware RTL-to-layout experiments. The repository currently preserves a reusable local toolchain and automation layer around Chipyard/Gemmini, Verilator, Python activity analysis, HotSpot, PACT/Xyce, OpenROAD, and OpenSTA. The previous Gemmini thermal-validation route has been frozen and archived so the next development route can start from a cleaner baseline without losing historical results.

The repository intentionally keeps scripts, configs, reports, generated RTL, selected simulation outputs, and thermal artifacts under version control. Large local tool payloads and third-party source trees live under `tools/` and `third_party/` and are ignored by git.

## Current Status

- Reusable tooling and scripts remain in place under `tools/env_gemmini_thermal.sh`, `scripts/`, and `configs/reduced_techlibs/`.
- The previous Gemmini thermal-validation plan, its handoff notes, generated RTL, logs, waves, activity CSVs, and thermal outputs are archived under `docs/archive/gemmini_thermal_validation_2026-04-23/` and `archive/gemmini_thermal_validation_2026-04-23/`.
- Validated supplemental tools remain available: PACT SuperLU, serial Xyce, OpenMPI runtime, slang, sv2v, and yosys-slang.
- Reduced edahub technology-library overlays are available for `asap7`, `nangate45`, and `sky130hd`. They are useful for bring-up only and are not complete signoff PDKs.

## Repository Map

| Path | Purpose |
| --- | --- |
| `tools/env_gemmini_thermal.sh` | Single environment entry point. Activates conda and exposes all local tools. |
| `scripts/` | RTL generation, workload build/run, activity extraction, HotSpot export, reports, and environment checks. |
| `workloads/` | Local bare-metal smoke and small GEMM programs. |
| `configs/gemmini/` | Notes for regenerated Gemmini-specific hierarchy/activity mappings. The previous map is archived. |
| `configs/reduced_techlibs/` | Make/Tcl adapters for edahub reduced technology libraries. |
| `configs/openroad/reduced_platforms/` | OpenROAD-flow-scripts platform overlays for reduced techlibs. |
| `rtl_exports/generated-verilog/` | Active generated RTL exports. Historical Gemmini exports were archived. |
| `sim/` | Active simulation outputs. Historical Gemmini binaries/logs/waves/activity files were archived. |
| `thermal/` | Active HotSpot or other thermal outputs. Historical Gemmini thermal outputs were archived. |
| `reports/` | Active summaries and notes. Historical Gemmini validation reports were archived. |
| `docs/` | Active environment and tooling documentation plus an archive of the retired Gemmini route. |
| `archive/` | Frozen historical artifacts from retired development routes. |
| `third_party/` | Ignored local source payloads: Chipyard, Gemmini, HotSpot, PACT, OpenROAD, Xyce, etc. |
| `tools/` | Ignored local binary/tool installs: CIRCT, Verilator, RISC-V GCC, OpenSTA, OSS CAD Suite, Xyce, slang, sv2v, etc. |

## Environment

Always enter the workspace through:

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

The environment script sets `TP_ROOT`, `CHIPYARD_HOME`, `GEMMINI_HOME`, `HOTSPOT_HOME`, `FLOW_HOME`, `PACT_HOME`, `CIRCT_HOME`, `RISCV`, `OPENSTA_HOME`, `OSS_CAD_SUITE`, `OPENROAD_PREBUILT_ROOT`, `XYCE_HOME`, `SLANG_HOME`, `SV2V_HOME`, cache paths, `PATH`, and `LD_LIBRARY_PATH`.

Use the full checker after changing tool installs, submodules, environment variables, or core flow scripts:

```bash
scripts/check_environment.sh
```

This currently checks required paths, Chipyard submodules, Python/VCD packages, sbt project loading, Verilator lint, Yosys synthesis, OpenSTA, OpenROAD, ORFS tool detection, HotSpot, Xyce, OpenMPI, slang, sv2v, yosys-slang, and a PACT SuperLU thermal smoke.

For a quick reduced-techlib-only check:

```bash
scripts/check_edahub_reduced_techlibs.py
```

## Common Flows

Generate and export Gemmini RTL:

```bash
scripts/run_gemmini_rtl_generation.sh
```

Build selected Gemmini bare-metal tests:

```bash
scripts/build_gemmini_workloads.sh mvin_mvout
```

Run a selected workload through the Verilator debug simulator:

```bash
scripts/run_gemmini_workload.sh mvin_mvout
```

Run the minimal thermal smoke loop:

```bash
scripts/run_thermal_smoke_flow.sh
```

Run the small GEMM thermal validation loop:

```bash
GEMM_MAX_CYCLES=800000 GEMM_TIMEOUT_SECS=600 scripts/run_small_gemm_thermal_flow.sh
```

The small GEMM flow can generate a very large VCD, about 1.6 GB in the archived validated run. Prefer the smoke flow or explicit run tags for routine environment checks.

## Tool Notes

Reduced technology libraries from `third_party/edahub` are adapted through `configs/reduced_techlibs` and `configs/openroad/reduced_platforms`. They include only the Liberty, DB, LEF, and selected auxiliary files needed for early synthesis, timing setup, floorplanning, placement, and routing experiments. They do not replace full PDK distributions.

PACT is used through its Python entry point, not a `pact` executable:

```bash
python "$PACT_ENTRY" --help
```

Current Xyce is a serial build. OpenMPI 3.1.4 is available and smoke-tested, but PACT parallel mode is intentionally not treated as complete until an MPI-enabled Xyce/Trilinos build exists.

## Route Reset And Archive

The previous Gemmini validation route is frozen for reference:

- Archived docs: `docs/archive/gemmini_thermal_validation_2026-04-23/`
- Archived generated artifacts: `archive/gemmini_thermal_validation_2026-04-23/`

If you want to reuse the old Gemmini flow, regenerate fresh active outputs rather than editing archived files in place.

## Handoff Reading Order

1. `docs/README.md` for the active-vs-archived document map.
2. `docs/gemmini_thermal_environment_setup.md`, `docs/tool_environment_inventory.md`, and `docs/pact_slang_sv2v_yosys_slang_install_report.md` for reusable environment and tool details.
3. `docs/gemmini_thermal_issue_log.md` for known toolchain failure modes and fixes.
4. `archive/gemmini_thermal_validation_2026-04-23/README.md` and `docs/archive/gemmini_thermal_validation_2026-04-23/` for the retired Gemmini route.
