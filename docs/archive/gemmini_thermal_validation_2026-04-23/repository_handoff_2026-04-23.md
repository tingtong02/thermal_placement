# Repository Handoff - 2026-04-23

## Purpose

This repository is a Gemmini thermal-placement research workspace. It is not just a source-code repository: it also records selected generated RTL, simulation logs/waves, activity CSVs, thermal inputs/outputs, reports, and local tool setup instructions. The local third-party source payloads and binary tool installs are intentionally ignored by git under `third_party/` and `tools/`.

The primary research chain is:

```text
Chipyard/Gemmini RTL generation
-> Verilator bare-metal simulation
-> VCD activity extraction
-> architectural activity buckets
-> proxy power / floorplan export
-> HotSpot or PACT/Xyce thermal solving
-> OpenROAD/OpenSTA physical-design sanity checks
```

## Validated Environment Entry

Always start from:

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

The environment script activates the `thermal_placement` conda environment and configures:

| Area | Main tools / paths |
| --- | --- |
| RTL and SoC generation | `CHIPYARD_HOME`, `GEMMINI_HOME`, `sbt`, `firtool` |
| Simulation | Verilator, RISC-V GCC/binutils, Spike helpers |
| Python analysis | Python 3.11, `numpy`, `pandas`, `matplotlib`, `scipy`, `pyyaml`, `pyvcd`, `vcdvcd` |
| Synthesis / physical | Yosys, OpenROAD, OpenSTA, OpenROAD-flow-scripts |
| SystemVerilog frontends | `slang`, `sv2v`, `yosys -m slang` |
| Thermal | HotSpot, PACT, serial Xyce |
| Runtime/build support | OpenMPI 3.1.4, libtool, local gfortran wrapper, local BLAS/LAPACK runtime paths |

## Tool Validation Performed

The following checks were run on 2026-04-23 from this repository:

| Check | Result |
| --- | --- |
| `bash -n scripts/*.sh tools/env_gemmini_thermal.sh` | Passed |
| `python -m py_compile scripts/*.py` | Passed |
| `scripts/check_edahub_reduced_techlibs.py` | Passed for `asap7`, `nangate45`, `sky130hd` |
| `python scripts/check_python_env.py` after sourcing env | Passed |
| `scripts/check_environment.sh` before extension | Passed for Gemmini/OpenROAD/HotSpot main chain |
| PACT `python "$PACT_ENTRY" --help` | Passed |
| PACT SuperLU 10 mm example to `/tmp` | Passed |
| `Xyce -v` and a minimal two-device netlist | Passed |
| `mpirun -np 2 /bin/hostname` | Passed |
| `slang` on minimal SystemVerilog | Passed |
| `sv2v` on minimal SystemVerilog | Passed |
| `yosys -m slang` on minimal SystemVerilog | Passed |
| `RUN_TAG=tool_validation_smoke scripts/run_thermal_smoke_flow.sh` | Passed; generated VCD/activity/HotSpot output |

The temporary `tool_validation_smoke` artifacts were removed after validation. The tracked `thermal_smoke-baremetal` binary was restored to the repository version because rebuilding it changes binary contents without adding handoff value.

## Script Fix Made

`scripts/check_environment.sh` now covers the supplemental tools that were installed after the original environment checker was written:

- required paths for `PACT_ENTRY`, `XYCE_EXE`, `slang`, `sv2v`, and the yosys-slang plugin
- Xyce minimal SPICE smoke
- OpenMPI runtime smoke
- `slang` / `sv2v` / `yosys-slang` SystemVerilog smoke
- PACT SuperLU thermal smoke

Use this script as the main full-toolchain regression check when onboarding a new shell or after changing tool installs.

## Main Flow Entry Points

| Script | What it does | Expected weight |
| --- | --- | --- |
| `scripts/check_environment.sh` | Full environment and toolchain smoke check | Moderate; includes sbt project load and PACT example |
| `scripts/check_edahub_reduced_techlibs.py` | Verifies reduced edahub Liberty/DB/LEF overlays | Light |
| `scripts/run_gemmini_rtl_generation.sh` | Generates Chipyard/Gemmini RTL and hierarchy map | Heavy |
| `scripts/build_gemmini_workloads.sh` | Builds gemmini-rocc-tests bare-metal workloads | Moderate |
| `scripts/run_gemmini_workload.sh` | Runs a selected workload through Verilator debug sim | Heavy when dumping waves |
| `scripts/run_thermal_smoke_flow.sh` | Minimal binary -> VCD -> activity -> HotSpot flow | Light/moderate |
| `scripts/run_small_gemm_thermal_flow.sh` | Functional small GEMM -> VCD -> activity -> HotSpot report | Heavy; current validated VCD is about 1.6 GB |

## Important Constraints

- `third_party/` and most of `tools/` are ignored. Do not assume a fresh clone has the local tool payloads unless they are separately provisioned.
- `tools/env_gemmini_thermal.sh` is tracked and is the canonical local environment entry.
- Current HotSpot power values are activity-weighted proxies, not signoff power.
- Current PACT/Xyce support is serial. OpenMPI itself is available, but PACT parallel mode remains incomplete until Xyce/Trilinos is rebuilt with MPI.
- Reduced edahub techlibs are bring-up libraries only, not complete PDKs.
- The Gemmini RTL export represents a full Chipyard SoC/test harness context. Thermal analysis should continue to focus on Gemmini PE array, scratchpad, accumulator, DMA/load-store, and controller buckets rather than treating the whole SoC as the final research object.

## Recommended Next Reading

- `README.md` for the main repository overview and commands.
- `docs/gemmini_thermal_handoff.md` for the detailed Gemmini state and generated artifacts.
- `docs/gemmini_thermal_issue_log.md` for previously encountered breakages and fixes.
- `docs/pact_slang_sv2v_yosys_slang_install_report.md` for PACT/Xyce/slang/sv2v/yosys-slang installation details.
- `docs/gemmini_thermal_validation_plan.md` for the broader research phases.
