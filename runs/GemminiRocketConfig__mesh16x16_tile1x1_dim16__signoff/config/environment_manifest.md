# Environment Manifest

Date: 2026-04-29
Run root: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`

## Repository

| Field | Value |
| --- | --- |
| Root | `/home/lisihang/thermal_placement` |
| Branch | `master` |
| Remote | `origin https://github.com/tingtong02/thermal_placement.git` |
| Required environment | `thermal_placement` conda env |
| Environment entry | `source tools/env_gemmini_thermal.sh` |

## Tool Snapshot

| Tool | Path / version |
| --- | --- |
| Python | `/home/lisihang/miniconda3/envs/thermal_placement/bin/python`, 3.11.15 |
| Verilator | `/home/lisihang/thermal_placement/tools/verilator/bin/verilator`, 5.047 devel |
| OpenROAD | `/home/lisihang/thermal_placement/tools/openroad-prebuilt/root/usr/bin/openroad`, v2.0-17598-ga008522d8 |
| OpenSTA | `/home/lisihang/thermal_placement/tools/opensta/bin/sta`, 3.1.0 |
| Yosys | `/home/lisihang/thermal_placement/tools/oss-cad-suite/oss-cad-suite/bin/yosys` |
| Cadence Genus | `/opt/eda/Cadence_DDI_23.14/bin/genus`, `23.14-s090_1` |
| Cadence Innovus | `/opt/eda/Cadence_DDI_23.14/bin/innovus`, `v23.14-s088_1` |
| Full ASAP7 | `/home/lisihang/asap7/asap7sc7p5t_28`, 1x collateral |
| ASAP7 Liberty cache | `/home/lisihang/thermal_placement/.cache/asap7/asap7sc7p5t_28/NLDM`, 15 TT NLDM files |
| Gemmini fake SRAM cache | `/home/lisihang/thermal_placement/.cache/fake_sram/asap7/Gemmini`, `mem_ext` and `mem_0_ext` |
| PACT | `/home/lisihang/thermal_placement/third_party/PACT/src/PACT.py` |
| HotSpot | `/home/lisihang/thermal_placement/third_party/HotSpot/hotspot` |
| Xyce | `/home/lisihang/thermal_placement/tools/xyce-7.4-build/install/bin/Xyce`, 7.4.0-opensource |
| sv2v | `/home/lisihang/thermal_placement/tools/sv2v/bin/sv2v`, v0.0.13 |
| slang | `/home/lisihang/thermal_placement/tools/slang/bin/slang`, 10.0.0+ace09c5 |
| ORFS flow | `/home/lisihang/thermal_placement/third_party/OpenROAD-flow-scripts/flow` |

## Notes

This snapshot was gathered with light commands only. Stage 1 has completed. Stage 2 Cadence/full-ASAP7 development now uses a 200 MHz / 5.000 ns timing target and will start through run-local Python-first flow code under `physical/cadence/python_flow/`.
