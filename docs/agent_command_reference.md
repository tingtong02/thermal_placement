# Agent Command Reference

## Environment

Enter the repository:

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

Basic repository check:

```bash
pwd
git status --short
git rev-parse --show-toplevel
git remote -v
```

Full environment check:

```bash
scripts/check_environment.sh
scripts/check_cadence_asap7_environment.sh
```

Python/package smoke. After sourcing the environment, `python` must resolve to `/home/lisihang/miniconda3/envs/thermal_placement/bin/python`:

```bash
command -v python
python --version
python scripts/check_python_env.py
```

Install project Python dependencies only into `thermal_placement` when they are genuinely needed, and document the package/version/use afterward:

```bash
/home/lisihang/miniconda3/bin/conda install -n thermal_placement <package>
/home/lisihang/miniconda3/bin/conda run -n thermal_placement python -m pip install <package>
```

Legacy reduced techlib check:

```bash
scripts/check_edahub_reduced_techlibs.py
```

Full ASAP7 / Cadence preflight:

```bash
source tools/env_gemmini_thermal.sh
scripts/check_cadence_asap7_environment.sh
python scripts/prepare_asap7_liberty_cache.py --check-only
python scripts/prepare_asap7_liberty_cache.py
python scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini
```

Gemmini fake SRAM collateral check:

```bash
source tools/env_gemmini_thermal.sh
python scripts/prepare_gemmini_fake_sram_collateral.py --design Gemmini
```

Cadence Tcl flows can source the full-ASAP7 and fake-SRAM manifests:

```tcl
source /home/lisihang/thermal_placement/configs/asap7_full/asap7_full.tcl
tp_asap7_require_full_pdk
set asap7_lefs [tp_asap7_lef_files]
set asap7_libs [tp_asap7_liberty_files]
set asap7_qrc [tp_asap7_qrc_file]
```

```tcl
source /home/lisihang/thermal_placement/configs/fake_sram/asap7_fake_sram.tcl
tp_fake_sram_require_design Gemmini
set fake_sram_lefs [tp_fake_sram_files Gemmini lef]
set fake_sram_libs [tp_fake_sram_files Gemmini lib]
set fake_sram_stubs [tp_fake_sram_files Gemmini verilog]
```

## Tool Location Checks

After sourcing the environment:

```bash
command -v python
command -v verilator
command -v yosys
command -v openroad
command -v sta
command -v genus
command -v innovus
command -v hotspot
command -v Xyce
command -v slang
command -v sv2v
```

Version checks:

```bash
python --version
verilator --version
yosys -V
openroad -version
sta -version
genus -version
innovus -version
Xyce -v
slang --version
sv2v --version
```

PACT entry:

```bash
python "$PACT_ENTRY" --help
```

## Cadence Stage 2 Commands

Stage 2 active backend is Cadence Genus + Innovus, not OpenROAD/ORFS. Normal Gemmini Phase 2 development remains Python-first, but the 2026-05-05 run-local `physical/cadence/python_flow/` bring-up has been deleted. The current startup base is the copied dacs-style tree:

```bash
ls runs/cadence_startup
sed -n '1,200p' runs/cadence_startup/README.md
```

```bash
source tools/env_gemmini_thermal.sh
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-scripts
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-genus-syn
TP_STAGE2_GENUS_RUN_TAG=<completed_genus_tag> \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-floorplan-smoke
TP_STAGE2_RUN_TAG=<clean_full_phase2_tag> \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-genus-syn
TP_STAGE2_RUN_TAG=<clean_full_phase2_tag> TP_STAGE2_GENUS_RUN_TAG=<clean_full_phase2_tag> \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-full
TP_STAGE2_GENUS_RUN_TAG=<completed_genus_tag> TP_STAGE2_DROUTE_END_ITERATION=5 TP_STAGE2_STRIPE_DISTANCE=20.0 \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-pnr-smoke
TP_STAGE2_RUN_TAG=<pnr_smoke_tag_with_placement_enc> TP_STAGE2_GENUS_RUN_TAG=<completed_genus_tag> \
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-cts-route-smoke
```

The Gemmini-specific dacs-style startup entry is now `runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py`. It supports `--preflight`, `--dry-run`, `--write-scripts`, `--print-config`, Genus elab/syn launch, Innovus floorplan smoke, reduced Innovus PNR smoke, reduced CTS/routing resume smoke, and non-smoke `--run-innovus-full`, and `--run-innovus-full-from-floorplan`. `--write-scripts` exercises the adapted `manager/` path and writes Genus/Innovus Tcl, `prelaunch_config_summary.json`, and manager manifests under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/` without launching commercial tools. `--write-resume-scripts-from-floorplan` does the same for the floorplan-resume path and emits scripts for powerplan/place/CTS/route only. `--run-innovus-full` is the full implementation entry and gates routed DEF/Verilog/SPEF/GDS plus either routed SDF or a documented routed-SDF waiver, `cts.enc`, `routing.enc`, post-route reports, top-level pin placement, fake SRAM macro evidence, and PG connectivity reporting. `--run-innovus-full-from-floorplan` resumes the non-smoke implementation from an existing `floorplan.enc`, seeds that checkpoint into a clean run tag, then reruns powerplan/place/CTS/route through the same artifact gates. With the 2026-05-12 PG downgrade and 2026-05-13 routed-SDF waiver, nonzero PG opens and missing routed SDF may be carried only as documented thermal-proxy limitations. `--run-innovus-cts-route-smoke` expects `innovus/data/placement.enc` in the selected `TP_STAGE2_RUN_TAG` and is intended for retrying after placement without rerunning placement.

2026-05-12 status: do not continue reduced smoke or PG diagnostic repair loops by default. The previous smoke/full attempts exposed PG opens, fake SRAM macro placement, CTS/NanoRoute layer mismatch, and missing `cts.enc`/`routing.enc`/routed artifacts; subsequent script work addressed the non-PG setup issues and Genus now uses bare `syn_opt` because `syn_opt -logical` requires unavailable `GEN_ENG100`. PG repair diagnostics did not reach 0 opens: baseline-style completed attempts stayed at 336 special opens, r15 direction-matched worsened to 481 opens, and completed variants had 0 PG shorts. The user accepted a quality downgrade to `PG-open thermal proxy`; the later 2026-05-13 waiver also allows missing routed SDF when documented. Future full-flow commands must start from a new clean semantic run tag, still target all non-waived final artifacts, and must label PG-open/SDF-waived results as non-signoff in reports. The selected continuation checkpoint is the retained r6 `innovus/data/floorplan.enc`, because no accepted or saved `powerplan.enc` exists after the PG-open failure and the r6 floorplan retains the current macro/pin evidence without carrying failed PG special routing as a checkpoint.

The older shell wrappers remain useful as low-level preflight references:

```bash
source tools/env_gemmini_thermal.sh
RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff \
scripts/run_stage2_cadence_genus.sh --dry-run

RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff \
scripts/run_stage2_cadence_innovus.sh --dry-run
```

When the Python dry-run inputs are correct, real Phase 2 runs should be launched through the Python entry point, not by hand-editing generated Tcl. Confirm with the active plan and stage report before running full Genus/Innovus on Gemmini.

Cadence threading controls:

```bash
TP_CADENCE_GENUS_CPUS=8
TP_CADENCE_INNOVUS_CPUS=8
```

Current Innovus license smoke reports 8 CPU jobs. Do not assume OpenROAD `MAKE_JOBS` / `NUM_CORES` semantics apply to Cadence.

### Phase 2 Python-First And IO/GDS Diagnostics

Normal Stage 2 development should be Python-first. Use Tcl only for debugging a failed step, recovering from a saved Innovus database, or producing a diagnostic export; once a Tcl change is needed for the normal route, move it back into Python-generated flow/config before relying on it.

Minimal IO pin placement evidence check after an Innovus floorplan DEF exists:

```bash
RUN=<stage2-run-dir>
awk '/^PINS /,/^END PINS/' "$RUN/innovus-rundir/data/floorplan.def" | rg -c '\+ (PLACED|FIXED)'
rg -n 'physical pins:|unplaced terms|Completed IO pin assignment' "$RUN/innovus-rundir/log/fused_pnr.log"
```

For the 2026-05-05 dacs-lab PPAdder validation, the expected evidence was `PINS 194 ;` and `194` placed/fixed pins. Gemmini will have a different pin count, but the acceptance rule is the same: all top-level pins placed/fixed before treating the run as valid physical evidence.

Headless layout-image route used for dacs-lab evidence:

```bash
RUN=<stage2-run-dir>
cd "$RUN/innovus-rundir"
source /home/lisihang/thermal_placement/tools/env_gemmini_thermal.sh
LD_LIBRARY_PATH=/opt/eda/Cadence_DDI_23.14/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9:${LD_LIBRARY_PATH:-} \
  /opt/eda/Cadence_DDI_23.14/bin/innovus -no_gui -abort_on_error -overwrite \
  -file scripts/export_gds_iopins_units20000.tcl \
  -log log/export_gds_iopins_units20000
QT_QPA_PLATFORM=offscreen klayout -z -r scripts/render_gds_iopins.py \
  -rd input_gds=data/routing_iopins_units20000.gds \
  -rd output_png=reports/layout_gds_iopins_100mhz.png
```

This produces a GDS-derived PNG. It is not an Innovus GUI-native screenshot. For a native Innovus screenshot, launch Innovus with a valid `DISPLAY`, load the saved database, fit the view, and capture the GUI window with an X/desktop screenshot tool.

## Existing Gemmini Stage 0/1 Commands

Generate Gemmini RTL and hierarchy mapping for the active run root:

```bash
RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff \
MAKE_JOBS=1 \
scripts/run_gemmini_rtl_generation.sh
```

Without `RUN_ROOT`, the script keeps its historical default output locations for reference/debug use.

Build the fixed Stage 1 workloads into the active run root:

```bash
RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff scripts/build_gemmini_workloads.sh tiled_matmul_os
RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff scripts/build_gemmini_workloads.sh tiled_matmul_ws
RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff scripts/build_gemmini_workloads.sh mvin_mvout
```

Run a fixed Stage 1 workload with VCD, activity extraction, and reports:

```bash
RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff \
RUN_TAG=stage1_tiled_matmul_os_signoff_YYYYMMDD \
TIMEOUT_CYCLES=100000000 \
scripts/run_gemmini_workload.sh tiled_matmul_os

RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff \
RUN_TAG=stage1_tiled_matmul_ws_signoff_YYYYMMDD \
TIMEOUT_CYCLES=100000000 \
scripts/run_gemmini_workload.sh tiled_matmul_ws

RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff \
RUN_TAG=stage1_mvin_mvout_signoff_YYYYMMDD \
TIMEOUT_CYCLES=100000000 \
scripts/run_gemmini_workload.sh mvin_mvout
```

Useful knobs for the same script:

```bash
VERILATOR_THREADS=16      # current recommended point on this machine for official mvin_mvout VCD smoke
NUMACTL=0                 # current host lacks numactl; use 1 only after command -v numactl passes
CLEAN_DEBUG_SIM=1         # required when switching VERILATOR_THREADS on an existing debug build
BUILD_DEBUG_SIM=0         # reuse an already-built simulator binary; set 1 only when simulator settings changed
EXTRACT_ACTIVITY=0        # run/copy waveform only
VCD_PARSER_WORKERS=128    # current best observed point on this machine for the in-repo parser on the 1.8G mvin_mvout VCD
WINDOW_BINS=200           # retained for compatibility; current window report avoids rescanning huge VCDs
```

Active Stage 1 route uses VCD by default and should stay on VCD. Do not switch the ongoing development flow to FST. With `RUN_ROOT` set, `scripts/run_gemmini_workload.sh` reads the hierarchy map from `RUN_ROOT/rtl/hierarchy/hierarchy_map.yaml` by default, so run the RTL generation step first or set `HIERARCHY_MAP` explicitly.

Thread-scaling benchmark examples with the official auxiliary test `mvin_mvout`.
For new runs, keep `MAKE_JOBS<=4`; Verilator simulation parallelism is controlled separately by `VERILATOR_THREADS`:

```bash
RUN_TAG=bench_mvin_vcd_t32 \
TIMEOUT_CYCLES=2000000 \
MAKE_JOBS=4 \
VERILATOR_THREADS=32 \
CLEAN_DEBUG_SIM=1 \
EXTRACT_ACTIVITY=0 \
scripts/run_gemmini_workload.sh mvin_mvout

RUN_TAG=bench_mvin_vcd_t64 \
TIMEOUT_CYCLES=2000000 \
MAKE_JOBS=4 \
VERILATOR_THREADS=64 \
CLEAN_DEBUG_SIM=1 \
EXTRACT_ACTIVITY=0 \
scripts/run_gemmini_workload.sh mvin_mvout
```

Current observed trend on this host for `mvin_mvout` VCD smoke:

- Verilator 仿真线程上限允许配置到 `128`
- 已完成 run 中 `VERILATOR_THREADS=16` walltime 最好
- `VERILATOR_THREADS=32` 比 16 慢
- `VERILATOR_THREADS=64` 明显比 16 慢
- `VERILATOR_THREADS=128` 也能完成，但继续恶化，不应默认使用
- 后续开发应把 `128` 视为可探索上限，而不是固定默认值；正式 run 线程数必须按当前机器、当前 workload、当前 tracing 形式的实测结果选择

Current strategy for VCD parsing:

- active flow 中的正式 parser 仍是 `scripts/extract_vcd_activity.py`，但现在已经支持可选并行解析
- 实现方式是“header 预解析 + body 分块 + 边界状态合并”，避免跨 chunk 漏算或重复计算 signal toggle
- 直接调用 parser 时用 `--workers <N>`；通过 Stage 1 主脚本调用时用 `VCD_PARSER_WORKERS=<N>`
- parser worker 上限同样开放到 `128`，默认值仍是 `1`
- 当前这台机器上，对 `sim/waves/GemminiRocketConfig/mvin_mvout-baremetal.bench_mvin_vcd_t16.vcd` 的实测结果为：`1=210.65s`、`32=10.77s`、`64=7.28s`、`128=6.34s`
- `1/32/64/128` 的输出 CSV 已经逐一用 `cmp` 验证一致
- 因此后续开发应把 `128` 视为当前已测最优点之一，但仍必须按实际文件和机器选择 worker 数，而不是硬编码为固定值

Build local small GEMM binary:

```bash
scripts/build_small_gemm_binary.sh
```

Run local small GEMM thermal-flow wrapper:

```bash
GEMM_MAX_CYCLES=800000 GEMM_TIMEOUT_SECS=600 scripts/run_small_gemm_thermal_flow.sh
```

Run minimal smoke thermal-flow wrapper:

```bash
scripts/run_thermal_smoke_flow.sh
```

Use these as references. Do not run heavy commands until the active phase requires them.

## Stage 1b Gate SAIF Handoff Commands

Formal Phase1b is a Gemmini-only zero-delay gate-level boundary replay route that generates raw Verilator SAIF activity for Phase3. It uses the accepted r28 routed/export netlist and does not perform output compare.

Formal fixed inputs and output root:

```bash
RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff
PHASE1B_R28_RUN="$RUN_ROOT/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived"
PHASE1B_NETLIST="$PHASE1B_R28_RUN/innovus/data/Gemmini.routed.v"
PHASE1B_OUT="$RUN_ROOT/gate_activity/phase1b_gate_saif_r28_20260515"
ASAP7_VERILOG=/home/lisihang/asap7/asap7sc7p5t_28/Verilog
SRAM_MODEL_DIR=collateral/gate_sim/fake_sram
```

Formal workload order and trace windows:

| workload | RTL VCD | trace window | start_ps | end_ps |
| --- | --- | --- | ---: | ---: |
| `mvin_mvout` | `$RUN_ROOT/sim/mvin_mvout/waves/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.vcd` | `data_movement_active` | 66875550 | 601879950 |
| `tiled_matmul_ws` | `$RUN_ROOT/sim/tiled_matmul_ws/waves/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.vcd` | `steady_high_load` | 1072392550 | 3753373925 |
| `tiled_matmul_os` | `$RUN_ROOT/sim/tiled_matmul_os/waves/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.vcd` | `steady_high_load` | 9272956950 | 10303285500 |

Formal orchestration entry, after implementation:

```bash
source tools/env_gemmini_thermal.sh
python scripts/phase1b_run_gate_saif_workloads.py \
  --run-root "$RUN_ROOT" \
  --gate-netlist "$PHASE1B_NETLIST" \
  --asap7-verilog-dir "$ASAP7_VERILOG" \
  --sram-model-dir "$SRAM_MODEL_DIR" \
  --out-dir "$PHASE1B_OUT"
```

The orchestrator must enforce these constants unless the user explicitly changes the plan:

- `--verilate-jobs 192`
- Verilator `--threads 16`
- `make -j192 CXX=clang++ LINK=clang++`
- `--compiler clang`
- `--no-timing`
- `--trace-saif`
- `--trace-depth 9`
- `--output-split 200 --output-split-cfuncs 20 --output-split-ctrace 20`
- `-CFLAGS "-O0 -g0"`
- referenced ASAP7 cells only, regenerated from r28, plus required ASAP7 UDP primitives
- no `--hierarchical` by default
- no output compare or mismatch report

If a generated C++ file in the new build tree exceeds `128 MiB`, split it into 32 helper C++ files before make. Automatic splitting is allowed inside the new run directory; if automatic splitting is unsafe, manual splitting inside the new run directory is allowed. Stop and ask the user before using `--hierarchical`, falling back to r2, modifying r28/Stage2 artifacts, modifying Chipyard/Gemmini RTL, or deleting old evidence.

Formal concurrent replay update from 2026-05-15: per user direction, the next formal workload replay launch is prepared as three simultaneous independent `phase1b_run_gate_saif_replay.py --skip-build-if-exists` processes sharing the already-linked r28 `VGemmini`. Use the prepared launch script only after explicit user instruction:

```bash
source tools/env_gemmini_thermal.sh
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/launch_phase1b_concurrent_replays_20260515.sh
```

The preflight record is `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/phase1b_concurrent_replay_preflight_20260515.json`. Do not launch until the user explicitly says to start.

Formal SAIF replay policy:

- Build one shared r28 executable once; use it for smoke and all three workload replays.
- Run smoke first under `smoke_mvin_mvout_100cyc/` with trace window `[66875550, 67075550)` ps. Smoke is not listed as a Phase3 handoff artifact.
- Run formal workloads one at a time: `mvin_mvout`, `tiled_matmul_ws`, `tiled_matmul_os`.
- Boundary vectors are re-extracted for all three workloads from Stage1 RTL VCD with `start_ps=0`, `end_ps=trace_end_ps`, and inputs-only columns.
- Keep per-workload `boundary_vectors.csv`, `boundary_vectors_manifest.json`, `boundary_signal_map.json/csv`, `trace_window.json`, `gate_activity.saif`, `replay_summary.json`, and `gate_activity_manifest.json`.
- Global outputs are `phase1b_gate_saif_handoff_manifest.json` and `phase1b_gate_saif_method_report.md`.
- SAIF hierarchy is raw Verilator `Gemmini` top-rooted output. Phase3 must perform Cadence SAIF scope/instance mapping and annotation coverage reporting.

Monitoring policy for long Verilator front-end, make, and replay tasks: after initial startup checks confirm normal progress, check about every 20 minutes. Do not proactively interrupt unless there is a clear error, process exit, resource anomaly, or a new user instruction.


Observed r28 build completion note from 2026-05-15: the required `make -j192 CXX=clang++ LINK=clang++` path reached complete object generation but GNU make segfaulted before executable link. Before any workaround, verify object completeness against `VGemmini_classes.mk`; the successful evidence had 328935 expected generated objects and 0 missing. The accepted local mitigation was manual archive/index/link tail inside the Phase1b build directory: create `VGemmini__ALL.a` from `VGemmini*.o`, run `ar -s`, then link `tb_phase1b_gate_saif.o`, `verilated.o`, `verilated_saif_c.o`, `verilated_threads.o`, and the archive with `clang++`. Do not skip the object-completeness check.


### Stage 1b Acceleration Attempt Commands

As of 2026-05-15, the user approved a harness-only binary/preparsed acceleration attempt under:

```bash
PHASE1B_ACCELERATE="$PHASE1B_OUT/accelerate"
```

Planned acceleration-only scripts are intentionally separate from the main CSV replay scripts and must end with `_acceleration.py`:

```text
scripts/phase1b_convert_boundary_vectors_to_binary_acceleration.py
scripts/phase1b_run_gate_saif_binary_replay_acceleration.py
```

The acceleration route must copy completed mainline inputs into `accelerate/<workload>/`, convert inputs-only `boundary_vectors.csv` to `boundary_vectors.bin`, generate `boundary_vectors_binary_layout.json` and `boundary_vectors_binary_manifest.json`, compile only `accelerate/build/tb_phase1b_gate_saif_binary.cpp`, and relink:

```text
accelerate/build/VGemmini_accelerate
```

against the existing mainline r28 archive/runtime objects:

```text
$PHASE1B_OUT/build/verilator_build/VGemmini__ALL.a
$PHASE1B_OUT/build/verilator_build/verilated.o
$PHASE1B_OUT/build/verilator_build/verilated_saif_c.o
$PHASE1B_OUT/build/verilator_build/verilated_threads.o
```

Do not rerun Verilator frontend, do not recompile generated `VGemmini*.o`, do not modify r28/RTL, do not use `--hierarchical`, do not fallback to r2, do not reduce trace depth or SAIF dump count, and do not interrupt any existing unoptimized `VGemmini` process. Run one `smoke_mvin_mvout_100cyc` binary smoke first. If smoke succeeds, the three formal accelerated workloads may run in parallel and failures are reported per-workload without killing the other runs. This route is not the default handoff method until the user confirms after evidence is available.

Historical old compare validation:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/phase1b_mvin_mvout_gate_boundary_replay_20260514.md
```

The old validation directory `gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/` records r2 `mvin_mvout` compare feasibility only. It is not a formal Phase1b SAIF handoff, not a Phase3 input, and not a build cache for r28.

## Stage 3 mvin_mvout Gate-SAIF Preflight

Current Phase3 development starts with a read-only `mvin_mvout` preflight. It consumes only the completed mainline Phase1b r28 gate SAIF and the accepted r28 Cadence/full-ASAP7 physical handoff, and writes under `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/`. It does not launch Cadence and must not interrupt running WS/OS or accelerated Phase1b replays.

```bash
source tools/env_gemmini_thermal.sh
python scripts/phase3_mvin_mvout_preflight.py
```

Expected outputs:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_manifest.json
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_report.md
```

## Stage 3 mvin_mvout Cadence Script-Only Power Plan

After the preflight passes, generate the Cadence script-only mvin_mvout activity-aware power plan without launching Innovus:

```bash
source tools/env_gemmini_thermal.sh
python scripts/phase3_mvin_mvout_write_cadence_power_scripts.py
```

Expected generated files:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/scripts/phase3_mvin_mvout_read_activity_power.tcl
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/scripts/run_phase3_mvin_mvout_innovus_no_gui.sh
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/phase3_mvin_mvout_cadence_script_manifest.json
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/README.md
```

The generated Tcl uses `read_activity_file -format SAIF` with the detected SAIF root scope. It is script-only collateral; do not execute the generated Innovus runner until the user explicitly approves a Cadence run.

## Activity And Thermal Helpers

Extract VCD activity:

```bash
python scripts/extract_vcd_activity.py \
  --vcd <input.vcd> \
  --hierarchy-map <hierarchy_map.yaml> \
  --workload <name> \
  --signal-csv <signal_activity.csv> \
  --region-csv <region_activity.csv> \
  --top-signals 0 \
  --workers <1-128>
```

If only the hierarchy/category rules changed and the signal CSV is known to contain all signals, reclassify without rescanning the VCD:

```bash
python scripts/reclassify_vcd_activity.py \
  --signal-csv <signal_activity.csv> \
  --hierarchy-map <hierarchy_map.yaml> \
  --region-csv <region_activity.csv>
```

Generate Stage 1 window and activity reports from completed artifacts:

```bash
python scripts/analyze_vcd_windows.py \
  --vcd <input.vcd> \
  --workload <run_tag> \
  --window-csv <window_activity.csv> \
  --window-report <stage1_windows.md>

python scripts/report_stage1_activity.py --help
```

Before Stage 3, treat the current `steady_high_load` report as a coarse marker window unless a target-scoped refinement has been written. Inspect the existing evidence first:

```bash
sed -n '1,80p' reports/stage1_tiled_matmul_os_baseline_windows.md
sed -n '1,90p' reports/stage1_tiled_matmul_os_baseline_activity_summary.md
rg -n "gemmini|ex_controller|mesh|valid|ready|busy|fire" sim/activity/stage1_tiled_matmul_os_baseline_20260423_signal_activity.csv | head -200
```

If Stage 3 needs exact per-window activity, add the smallest windowed/scoped extractor instead of averaging the full 41 GiB trace or reusing CPU-dominated whole-program activity. The extractor should keep full-SoC simulation as the source but filter to Gemmini target scopes, then write:

- `reports/stage1_tiled_matmul_os_baseline_target_windows.md`
- `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`

Do not replace this with a Gemmini-only RTL run unless a separate harness has been explicitly designed and validated.

Historical Stage 3 proxy commands, reference only for script shape; do not use as current handoff recipe:

```bash
python scripts/extract_stage3_target_window_activity.py \
  --vcd sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd \
  --window-csv sim/activity/stage1_tiled_matmul_os_baseline_20260423_window_activity.csv \
  --hierarchy-map configs/gemmini/hierarchy_map.yaml \
  --workload stage1_tiled_matmul_os_baseline_20260423 \
  --candidate-window steady_high_load \
  --output-csv sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv \
  --output-report reports/stage1_tiled_matmul_os_baseline_target_windows.md \
  --bin-csv sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_bins.csv \
  --workers 16 \
  --bins 64

python scripts/build_stage3_power_grid.py \
  --target-activity-csv sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv \
  --target-bin-csv sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_bins.csv \
  --def-file physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.def \
  --netlist physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.v \
  --sdc physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.sdc \
  --spef physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.spef \
  --liberty third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_OA_RVT_TT_nldm_201020.lib \
  --liberty third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_AO_RVT_TT_nldm_201020.lib \
  --liberty third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.lib \
  --liberty third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_SEQ_RVT_TT_nldm_201020.lib \
  --liberty third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.lib \
  --power-dir power \
  --reports-dir reports \
  --grid 64 \
  --proxy-total-power-w 1.0
```

Stage 3 `--workers` is parser-internal parallelism for one VCD extraction task. It is not ORFS `MAKE_JOBS` and does not launch multiple backend tasks.

Export coarse HotSpot inputs from region activity:

```bash
python scripts/export_smoke_hotspot_inputs.py \
  --region-csv <region_activity.csv> \
  --floorplan <output.flp> \
  --ptrace <output.ptrace>
```

Generate small GEMM report:

```bash
python scripts/report_small_gemm_flow.py --help
```

## Stage 4 PACT / ATSim3D v1 / HotSpot Preflight

Current Phase 4 tool smoke checks, run only after sourcing the environment:

```bash
source tools/env_gemmini_thermal.sh
python "$PACT_ENTRY" --help
Xyce -v
mpirun -np 2 /bin/hostname | sort | uniq -c

rm -rf /tmp/tp_phase4_pact_smoke
mkdir -p /tmp/tp_phase4_pact_smoke
cd third_party/PACT/src
timeout 120s python PACT.py \
  ../Example/lcf_files/10mm_lcf_UniformPD_50Wcm2.csv \
  ../Example/config_files/default_htc_1e4_10mm.config \
  ../Example/modelParams_files/modelParams10mm.config_40x40 \
  --gridSteadyFile /tmp/tp_phase4_pact_smoke/superlu_10mm.grid.steady
```

ATSim3D v1 local tool smoke pattern:

```bash
source tools/env_gemmini_thermal.sh
bash -n scripts/run_atsim3d.sh
scripts/run_atsim3d.sh --help
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.csv \
  --ConfigFile third_party/ATSim3D_pub/2DIC/Intel.config \
  --SimParamsFile third_party/ATSim3D_pub/2DIC/SimParms.config
```

HotSpot tiny smoke pattern:

```bash
source tools/env_gemmini_thermal.sh
mkdir -p /tmp/tp_phase4_hotspot_smoke
cd /tmp/tp_phase4_hotspot_smoke
printf 'core 0.001 0.001 0 0\nedge 0.001 0.001 0.001 0\n' > tiny.flp
printf 'core edge\n1.0 0.1\n1.0 0.1\n' > tiny.ptrace
hotspot -c "$HOTSPOT_HOME/template.config" -f tiny.flp -p tiny.ptrace -o tiny.ttrace
```

Threading and parameter boundary for Phase 4:

- PACT command shape is `python "$PACT_ENTRY" <lcf.csv> <config> <modelParams> --gridSteadyFile <output_prefix>` for steady grid output.
- PACT SPICE solvers read `number_of_core` from the modelParams file. The local source calls `mpirun -np <number_of_core> Xyce ...` only when `number_of_core > 1`.
- Current OpenMPI smoke passes, but current Xyce is serial. Formal Stage 4 PACT SPICE steady/transient runs must use `number_of_core = 1` unless the user explicitly authorizes an MPI-enabled Xyce rebuild and revalidation.
- ATSim3D v1 is required for Stage 4 steady independent comparison. It must use `scripts/run_atsim3d.sh`, which runs ATSim with `tools/atsim3d-py38/bin/python`; do not run ATSim3D v1 with the main Python 3.11 conda environment.
- ATSim3D v1 `.res` files contain fine-grid temperature samples. Standard-cell context must be derived by joining downsampled ATSim grids with the Stage 3 placed instance grid map.
- ATSim3.5D v2 `ATSim3_5D` remains a documented local binary, but it is not a required Stage 4 flow until its XML/config input schema is validated.
- HotSpot is treated as a single-process coarse comparison; no project-validated thread parameter is available.

Planned Stage 4 input generation should start from `reports/stage4_tiled_matmul_os_baseline_preflight_plan.md` and consume the existing Stage 3 `power/stage3_tiled_matmul_os_baseline_*` artifacts.

## Stage 4 Execution Commands

Historical Stage 4 PACT/ATSim3D v1/HotSpot input generation from proxy artifacts; reference only:

```bash
source tools/env_gemmini_thermal.sh
scripts/build_stage4_thermal_inputs.py
```

Run PACT steady SuperLU:

```bash
source tools/env_gemmini_thermal.sh
cd third_party/PACT/src
python PACT.py \
  /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/lcf_stage4_tiled_matmul_os_baseline_steady.csv \
  /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/config_stage4_tiled_matmul_os_baseline.config \
  /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/modelParams_stage4_tiled_matmul_os_baseline_steady_superlu.config \
  --gridSteadyFile /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/steady_temperature_stage4_tiled_matmul_os_baseline.grid.steady
```

Current PACT transient route uses the local generated-netlist compatibility repair documented in issue log items 69 and 70. The first PACT command is used to generate the `.cir`; with the current local PACT/Xyce combination it may return non-zero on the unsanitized Xyce launch. Continue only if the `.cir` file exists and the failure matches issue log item 70.

```bash
source tools/env_gemmini_thermal.sh
cd third_party/PACT/src
python PACT.py \
  /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/lcf_stage4_tiled_matmul_os_baseline_transient.csv \
  /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/config_stage4_tiled_matmul_os_baseline.config \
  /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/modelParams_stage4_tiled_matmul_os_baseline_transient_spice_serial.config \
  --gridSteadyFile /home/lisihang/thermal_placement/thermal/pact/stage4_tiled_matmul_os_baseline/transient_temperature_stage4_tiled_matmul_os_baseline.grid.transient
cd /home/lisihang/thermal_placement
test -s thermal/pact/stage4_tiled_matmul_os_baseline/transient_temperature_stage4_tiled_matmul_os_baseline.cir
scripts/sanitize_stage4_pact_transient_cir.py \
  --cir thermal/pact/stage4_tiled_matmul_os_baseline/transient_temperature_stage4_tiled_matmul_os_baseline.cir \
  --manifest thermal/pact/stage4_tiled_matmul_os_baseline/manifest_stage4_tiled_matmul_os_baseline_inputs.json \
  --model-params thermal/pact/stage4_tiled_matmul_os_baseline/modelParams_stage4_tiled_matmul_os_baseline_transient_spice_serial.config \
  --output thermal/pact/stage4_tiled_matmul_os_baseline/transient_temperature_stage4_tiled_matmul_os_baseline.sanitized.cir
Xyce -l thermal/pact/stage4_tiled_matmul_os_baseline/transient_temperature_stage4_tiled_matmul_os_baseline.sanitized.log \
  thermal/pact/stage4_tiled_matmul_os_baseline/transient_temperature_stage4_tiled_matmul_os_baseline.sanitized.cir
```

Run ATSim3D v1 steady rerun from converted Stage 4 inputs, then run HotSpot coarse comparison and generate reports/figures. For active Stage 4 reruns, use the same command shape under the active run root and workload directory:

```bash
source tools/env_gemmini_thermal.sh
/home/lisihang/miniconda3/envs/thermal_placement/bin/python \
  thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/prepare_atsim_v1_proxy_inputs.py
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.csv \
  --ConfigFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline.config \
  --SimParamsFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_simparams.config
/home/lisihang/miniconda3/envs/thermal_placement/bin/python \
  thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/generate_atsim_stage4_artifacts.py
```

Run HotSpot coarse comparison and generate reports/figures. `scripts/report_stage4_thermal_results.py` writes the main PACT grids/ranks/heatmaps in DEF physical coordinates and retains PACT raw row-order audit copies with `_pact_raw_order` filenames; do not report raw row indices as physical `grid_y`:

```bash
source tools/env_gemmini_thermal.sh
hotspot \
  -c thermal/hotspot/stage4_tiled_matmul_os_baseline/stage4_tiled_matmul_os_baseline.config \
  -f thermal/hotspot/stage4_tiled_matmul_os_baseline/stage4_tiled_matmul_os_baseline.flp \
  -p thermal/hotspot/stage4_tiled_matmul_os_baseline/stage4_tiled_matmul_os_baseline.ptrace \
  -o thermal/hotspot/stage4_tiled_matmul_os_baseline/stage4_tiled_matmul_os_baseline.ttrace
scripts/report_stage4_thermal_results.py
```

Generate standard-cell context figures from already completed Stage 3/4 artifacts, without rerunning thermal tools. This report path reads corrected PACT physical grids and writes both SVG and same-basename PNG figures for VS Code/remote preview:

```bash
source tools/env_gemmini_thermal.sh
python scripts/report_stage4_standard_cell_context.py
```

Current Stage 4 key outputs are `reports/stage4_tiled_matmul_os_baseline_summary.md`, `reports/stage4_tiled_matmul_os_baseline_standard_cell_context.md`, `thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/RESULTS.md`, `artifacts/stage4/`, `artifacts/stage4/standard_cell_context/`, and `artifacts/stage4/atsim3d_v1_proxy/`. Main PACT and ATSim comparison artifacts are physical-coordinate views; `*_pact_raw_order.*` and `*_raw_order_*` files are audit/diagnostic only. Standard-cell context SVG figures should have same-basename PNG companions.

## Backend Resource Policy

For ORFS/backend work, distinguish external task parallelism from per-tool threads:

- `MAKE_JOBS` is the outer independent-task count. For one baseline or one dependent ORFS chain, use `MAKE_JOBS=1`.
- The maximum allowed outer concurrency is `MAKE_JOBS=4`, and only for independent flows with isolated outputs or unique `FLOW_VARIANT` values.
- `NUM_CORES` is the per-OpenROAD-call thread count passed through `-threads`.
- Normal single-task work may use up to `NUM_CORES=128` after a smaller smoke confirms the command path.
- If `MAKE_JOBS=2`, each task may use up to `NUM_CORES=128`.
- If `MAKE_JOBS=3` or `MAKE_JOBS=4`, each task may use up to `NUM_CORES=64`.
- Record the chosen `MAKE_JOBS`, per-task `NUM_CORES`, output isolation, and resource assumption in each stage manifest.

Do not rely on the shell environment's legacy default `MAKE_JOBS` value for ORFS work; set it explicitly in the command.

## ASAP7 / ORFS References

Read before using:

```bash
sed -n '1,220p' configs/reduced_techlibs/README.md
find configs/openroad/reduced_platforms/asap7 -maxdepth 2 -type f | sort
```

Validate reduced techlibs:

```bash
scripts/check_edahub_reduced_techlibs.py asap7
```

Do not start an ORFS run until stage 2 has defined the implementation top, design config, and output directory.

Historical OpenROAD/ORFS Stage 2 entry shape. This is not the active Phase2 route after the Cadence/full-ASAP7 r28 handoff:

```bash
source tools/env_gemmini_thermal.sh
MAKE_JOBS=1 NUM_CORES=128 DETAILED_ROUTE_END_ITERATION=16 \
  scripts/run_stage2_signoff_openroad.sh synth
```

Historical ORFS Stage 2 settings for `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`; current Cadence handoff is r28 `PG-open / DRC-open / routed-SDF-waived thermal proxy`:

- implementation top: `Gemmini`
- SDC target: `200 MHz` / `5.000 ns`
- outer ORFS scheduling: `MAKE_JOBS=1`
- OpenROAD internal threads: `NUM_CORES=128`
- route optimization cap: `DETAILED_ROUTE_END_ITERATION=16`
- failure policy: confirmed failure stops; do not auto-enable `FLOW_VARIANT=noaddermap` or other old proxy knobs
- monitoring cadence for long backend stages: 30-60 minutes after progress is confirmed

Historical Stage 2 route bring-up entry, `noaddermap` proxy variant. This is reference only and must not be used as the active handoff recipe:

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

`DETAILED_ROUTE_END_ITERATION=8` intentionally caps detailed-route optimization at 8 iterations for this Phase 2 proxy completion attempt. If `5_2_route` cannot start from `5_1_grt.odb`, stop and report instead of cleaning or rerunning earlier stages.

This is a bring-up command, not the current handoff recipe. It records the historical compromises used to get physical data for the old thermal-flow prototype.

Historical Stage 2 finish/export command pattern, after old proxy `5_route.odb` exists:

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
  finish
```

The completed local run needed a second no-clean `finish` invocation because the first `6_report` attempt failed only at GUI image saving after core final exports were written. The second invocation skipped `6_report`, generated `6_final.sdc`, ran KLayout merge, and completed `6_final.gds`.


Verify historical final Phase 2 proxy outputs, reference only:

```bash
base="$TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap"
for f in 6_final.odb 6_final.def 6_final.v 6_final.sdc 6_final.spef 6_final.gds; do
  test -s "$base/$f" || { echo "missing or empty: $f"; exit 1; }
done
find "$base" -maxdepth 1 -type f \( -name '*.sdf' -o -name '*sdf*' \) -print
```

Expected current result: all six final proxy files exist and the SDF search prints nothing. Final-report evidence is split by ORFS output class: `6_report.log` and `6_report.json` are under the `logs/.../noaddermap/` tree, while route DRC evidence such as `5_route_drc.rpt` is under `reports/.../noaddermap/`. Do not move these files; record their actual locations.

Current GUI image note: `6_report.log` contains a `get_scenes` failure from ORFS `save_images.tcl`; existing images through `final_clocks.webp.png` are present. Since GUI screenshots are not required, the default future handling is to use a non-GUI OpenROAD final-report path if this step must be rerun, so image generation is skipped. Do not patch ignored ORFS `save_images.tcl` unless GUI screenshots become an explicit requirement.


Print backend tool defaults and thread args:

```bash
source tools/env_gemmini_thermal.sh
which -a yosys openroad sta
make -C "$FLOW_HOME" \
  PLATFORM_HOME="$TP_ROOT/configs/openroad/reduced_platforms" \
  DESIGN_CONFIG="$TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/config.mk" \
  YOSYS_EXE="$YOSYS_EXE" OPENROAD_EXE="$OPENROAD_EXE" OPENSTA_EXE="$OPENSTA_EXE" \
  print-NUM_CORES print-OPENROAD_ARGS
```

Legacy ORFS strict-quality runs would not add debug-only or quality-reduction knobs such as `-noshare`, `SKIP_LAST_GASP`, `REMOVE_ABC_BUFFERS=1`, `GPL_TIMING_DRIVEN=0`, `SKIP_CTS_REPAIR_TIMING=1`, `SKIP_REPORT_METRICS=1`, or `FLOW_VARIANT=noaddermap` unless the user explicitly downgrades the plan.

Stage 2 fidelity rule: `noaddermap`, `REMOVE_ABC_BUFFERS=1`, `GPL_TIMING_DRIVEN=0`, `SKIP_CTS_REPAIR_TIMING=1`, and `SKIP_REPORT_METRICS=1` are bring-up/proxy knobs. That historical ORFS round intentionally kept them while trying to clear the route blocker and complete the Stage 0-4 thermal-flow prototype. Any result produced with these knobs is non-signoff and must be labeled `proxy` / thermal-flow prototype.

Historical ORFS bring-up classification, retained only for reference:

- `strict`: routed outputs exist, reports are readable, and debug/proxy knobs are removed or have a documented equivalent-quality justification.
- `proxy`: routed or placed/CTS data are usable for thermal-flow prototyping, but one or more bring-up knobs remain.

For the current active plan, Stage 2 is already downgraded to the r28 `PG-open / DRC-open / routed-SDF-waived thermal proxy` handoff. Do not revive this legacy ORFS strict-gate rule unless the user explicitly changes the plan.

Historical Stage 2 proxy completion result:

- the `PIN_THICKNESS=0.096` full-design A route rebuilt through CTS; Attempt 1 added `PLACE_PINS_ARGS='-min_distance 0.54'` and generated `5_1_grt.odb`
- memory macro `pin_access` passes in full design with `macroNoAp=0`; the earlier `DRT-0073 No access point` blocker is no longer active
- the earlier `GRT-0116` global-route congestion blocker was cleared in Attempt 1: final global-route congestion reached zero overflow before `5_1_grt.odb` was written
- route resumed from existing `5_1_grt.odb`, entered `5_2_route`, and generated `5_route.odb` successfully with `DETAILED_ROUTE_END_ITERATION=8`
- ORFS `finish` completed after a no-clean rerun and generated `6_final.odb`, `6_final.def`, `6_final.v`, `6_final.sdc`, `6_final.spef`, and `6_final.gds`
- no SDF was emitted; Stage 3 must use SDC+SPEF+routed netlist as the proxy timing/parasitic package and document this gap
- final detailed-route residual violation count after the capped 8th iteration is 6988, so the result is routed proxy / non-signoff, not DRC-clean

Historical Stage 2 memory-route decision:

- stay on A-result analysis for now; do not enter C automatically
- `memory_boundary_stub + obstruction/thermal context` remains an optional fallback that has not started
- do not try pure `mem_boundary_stub` without obstruction/thermal context in the current Phase 2 plan unless the user explicitly changes the plan
- do not reuse or overwrite `FLOW_VARIANT=noaddermap` outputs if a future fallback is approved; document any fallback output as memory-boundary/proxy, not SRAM macro detailed thermal modeling
- route-stage runs can be silent for long periods; monitor them at relaxed intervals and never proactively terminate route unless the user explicitly asks or the process exits/fails

Stage 2/ORFS scheduling rule for one reusable physical implementation:

- one reusable synth / floorplan / place / route chain: use `MAKE_JOBS=1` as the deterministic outer make setting
- this does not limit OpenROAD to one CPU core; P&R acceleration should come from `NUM_CORES`
- increasing `MAKE_JOBS` is not useful for a single dependent ORFS chain and has previously triggered duplicate synth work in this local flow
- normal single-task P&R development may use up to `NUM_CORES=128` on this host after a smaller command-path smoke
- `MAKE_JOBS>1` is reserved for multiple independent `FLOW_VARIANT` jobs only; cap it at `4`, use unique outputs, and apply the `MAKE_JOBS`/`NUM_CORES` limits from Backend Resource Policy

Historical development-only floorplan compatibility entry, reference only:

```bash
source tools/env_gemmini_thermal.sh
REMOVE_ABC_BUFFERS=1 SKIP_REPORT_METRICS=1 MAKE_JOBS=1 NUM_CORES=128 \
  scripts/run_stage2_openroad_noaddermap.sh floorplan
```

## Stage 2 Speed-Up Patterns

One reusable implementation, staged progression:

```bash
source tools/env_gemmini_thermal.sh
MAKE_JOBS=1 NUM_CORES=16 scripts/run_stage2_openroad.sh synth
MAKE_JOBS=1 NUM_CORES=128 scripts/run_stage2_openroad_noaddermap.sh floorplan
MAKE_JOBS=1 NUM_CORES=128 scripts/run_stage2_openroad_noaddermap.sh place
```

Direct ORFS staged target when only one substep needs to move:

```bash
source tools/env_gemmini_thermal.sh
make -j 1 -C "$FLOW_HOME" \
  PLATFORM_HOME="$TP_ROOT/configs/openroad/reduced_platforms" \
  DESIGN_CONFIG="$TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/config.mk" \
  YOSYS_EXE="$YOSYS_EXE" OPENROAD_EXE="$OPENROAD_EXE" OPENSTA_EXE="$OPENSTA_EXE" \
  NUM_CORES=128 \
  $TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/base/3_3_place_gp.odb
```

Outer parallel for independent configs only:

```bash
source tools/env_gemmini_thermal.sh
for density in 0.55 0.60; do
  make -j 1 -C "$FLOW_HOME" \
    PLATFORM_HOME="$TP_ROOT/configs/openroad/reduced_platforms" \
    DESIGN_CONFIG="$TP_ROOT/physical/stage2_tiled_matmul_os_baseline_asap7/config.mk" \
    YOSYS_EXE="$YOSYS_EXE" OPENROAD_EXE="$OPENROAD_EXE" OPENSTA_EXE="$OPENSTA_EXE" \
    FLOW_VARIANT="pd_${density}" PLACE_DENSITY="$density" NUM_CORES=16 &
done
wait
```

Use the outer-parallel pattern only for genuinely independent configs. Keep each `FLOW_VARIANT` unique so that results do not overwrite each other.


## Documentation Checks

List active docs:

```bash
find docs -maxdepth 1 -type f | sort
```

Find references to archived route:

```bash
rg -n "archive/gemmini_thermal_validation_2026-04-23|gemmini_thermal_validation_plan" docs README.md AGENTS.md
```

Check markdown path mentions:

```bash
rg -n "TO_FILL_BY_CODEX|\[.*\]\(/home/lisihang/thermal_placement" docs/phase0tophase4_cadence_asap7_plan.md docs/*.md AGENTS.md
```

## Editing Notes

For file edits, read the file first, make a focused edit, then re-read the changed section. Keep commands simple and avoid unrelated formatting changes.

## Output Discipline

When creating new stage outputs for the active Stage 0-4 plan, put them under the run root and include:

- stage number
- workload name when workload-specific
- date or version when reruns are possible
- quality label when applicable; use `PG-open / DRC-open / routed-SDF-waived thermal proxy` for the current Stage 2 handoff, and treat existing `signoff` path components as historical names

Active run root:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/
```

Examples:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/config/stage0_config_manifest.md
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_os/stage1_activity_summary.md
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/config/stage2_cadence_asap7_phase2_handoff_20260513.md
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_ws/stage3_power_trace_method.md
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/mvin_mvout/stage4_thermal_report.md
```

Do not write new outputs into `archive/` unless explicitly archiving a completed route.

## Isolated Threading Experiments

Use a `/tmp` ORFS copy when exploring synthesis / placement threading so that the main repository does not accumulate temporary backend outputs:

```bash
rm -rf /tmp/orfs_mt_sandbox
cp -a third_party/OpenROAD-flow-scripts/flow /tmp/orfs_mt_sandbox/flow
```

Example isolated synth threading comparison:

```bash
source tools/env_gemmini_thermal.sh
rm -rf /tmp/orfs_mt_sandbox/flow/{logs,results,reports,objects}/nangate45/aes
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss_kb=%M' \
  make -j 1 -C /tmp/orfs_mt_sandbox/flow \
  DESIGN_CONFIG=/tmp/orfs_mt_sandbox/flow/designs/nangate45/aes/config.mk \
  YOSYS_EXE="$YOSYS_EXE" OPENROAD_EXE="$OPENROAD_EXE" OPENSTA_EXE="$OPENSTA_EXE" \
  MAKE_JOBS=1 NUM_CORES=1 synth
```

Example isolated placement threading comparison on the placement core stage only (the current recommendation for formal development is still to start from `16` threads and only increase when runs remain too slow):

```bash
source tools/env_gemmini_thermal.sh
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss_kb=%M' \
  make -j 1 -C /tmp/orfs_mt_sandbox/flow \
  DESIGN_CONFIG=/tmp/orfs_mt_sandbox/flow/designs/nangate45/aes/config.mk \
  YOSYS_EXE="$YOSYS_EXE" OPENROAD_EXE="$OPENROAD_EXE" OPENSTA_EXE="$OPENSTA_EXE" \
  MAKE_JOBS=1 NUM_CORES=8 SKIP_REPORT_METRICS=1 \
  results/nangate45/aes/base/3_3_place_gp.odb
```

Note: on the current OpenROAD prebuilt, ORFS sample-design threading experiments may still need temporary Tcl compatibility edits in the `/tmp` copy; see `docs/gemmini_thermal_issue_log.md` items 33 and 36 before reusing the placement example verbatim.

## ATSim3D Local Tool

ATSim3D v1 is installed as a local third-party thermal simulator. Tool details, input files, example cases, and paper mapping are documented in `docs/atsim_tool_guide.md`:

```bash
git -C third_party/ATSim3D_pub rev-parse HEAD
bash -n scripts/run_atsim3d.sh
scripts/run_atsim3d.sh --help
```

Run the README 2DIC smoke from the project root:

```bash
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile third_party/ATSim3D_pub/2DIC/Intel_ID1_lcf.csv \
  --ConfigFile third_party/ATSim3D_pub/2DIC/Intel.config \
  --SimParamsFile third_party/ATSim3D_pub/2DIC/SimParms.config
```

The wrapper uses `tools/atsim3d-py38/bin/python` because ATSim3D publishes core modules as Python 3.8 `.pyc` files. Do not run ATSim3D with the main `thermal_placement` Python 3.11 environment.

## ATSim3D v2 Binary

ATSim3D v2 binary `ATSim3_5D` is installed under `tools/atsim3d-bin/` and wrapped by `scripts/run_atsim3_5d.sh`:

```bash
bash -n scripts/run_atsim3_5d.sh
ldd tools/atsim3d-bin/ATSim3_5D
timeout 20 scripts/run_atsim3_5d.sh --help
```

The expected v2 run shape from `third_party/ATSim3D_pub/README.md` is:

```bash
scripts/run_atsim3_5d.sh \
  -xml <XmlFile> \
  -config <ConfigFile> \
  --output_path <OutputDir>
```

The public repo currently has no complete v2 XML/config example. The recovered interface notes and input skeleton are documented in `docs/atsim_tool_guide.md`; full thermal simulation still needs a matching XML/config/material/power/floorplan input set.

### Phase 2 PG-open routing recovery from CTS checkpoint

After a routing-step failure that occurs after CTS, generate or run only the routing/export step from an existing `cts.enc` checkpoint:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=<new-clean-run-tag> \
TP_STAGE2_GENUS_RUN_TAG=<accepted-genus-run-tag> \
TP_STAGE2_CTS_SOURCE_ENC=<absolute-path-to-cts.enc> \
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-routing-scripts-from-cts
```

Heavy launch:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=<new-clean-run-tag> \
TP_STAGE2_GENUS_RUN_TAG=<accepted-genus-run-tag> \
TP_STAGE2_CTS_SOURCE_ENC=<absolute-path-to-cts.enc> \
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-routing-from-cts
```

Default routing-recovery behavior as of 2026-05-13:

- `TP_STAGE2_ROUTE_ANALYSIS_TYPE=single` unless overridden.
- `TP_STAGE2_ROUTE_RUN_POSTROUTE_OPT=false` unless explicitly enabled.
- `TP_STAGE2_ROUTE_SAVE_AFTER_ROUTE_DESIGN=true`, so `routing.enc` is saved immediately after `routeDesign -globalDetail` before post-route reporting/export.
- Results are `PG-open thermal proxy` evidence unless PG connectivity and routed DRC are separately clean.

For an 8-iteration detailed-route retry from CTS, add:

```bash
TP_STAGE2_DROUTE_END_ITERATION=8
```

This is emitted into Innovus routing Tcl as:

```tcl
setNanoRouteMode -quiet -drouteEndIteration 8
```

### Phase 2 PG-open export/report recovery from routing checkpoint

After detailed routing completed and `routing.enc` exists, but later SDF/SPEF/GDS/report export failed, generate or run only export/report recovery from the routed checkpoint:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=<new-clean-run-tag> \
TP_STAGE2_GENUS_RUN_TAG=<accepted-genus-run-tag> \
TP_STAGE2_ROUTING_SOURCE_ENC=<absolute-path-to-routing.enc> \
TP_STAGE2_SDF_EXPORT_ARGS="-interconn none -base_delay -view setup_view" \
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-export-scripts-from-routing
```

Heavy launch:

```bash
source tools/env_gemmini_thermal.sh
TP_STAGE2_RUN_TAG=<new-clean-run-tag> \
TP_STAGE2_GENUS_RUN_TAG=<accepted-genus-run-tag> \
TP_STAGE2_ROUTING_SOURCE_ENC=<absolute-path-to-routing.enc> \
TP_STAGE2_SDF_EXPORT_ARGS="-interconn none -base_delay -view setup_view" \
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-innovus-export-from-routing
```

This does not rerun `routeDesign`; it restores `routing.enc`, exports final artifacts, and preserves copied post-route timing/area/power reports from the source routing run when the export-only run does not regenerate them.

Export-only recovery also supports splitting SDF away from the remaining physical artifact exports:

```bash
TP_STAGE2_EXPORT_SDF=false
```

Use this when Innovus `write_sdf` crashes after routed DEF/Verilog export and before SPEF/GDS/DRC/connectivity. After the 2026-05-13 user-approved routed-SDF waiver, this split-export route can be accepted as the degraded Stage 2 thermal-proxy handoff if routed DEF, routed Verilog, SPEF, GDS, DRC report, connectivity report, `export_routing.enc`, post-route timing/area/power reports, and the SDF waiver classification are all documented. The accepted current run is r28: `gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived`. It must still be labeled `PG-open`, `DRC-open`, and `routed-SDF-waived`, not signoff-clean.

To try SDF after the other physical artifacts in a later retry, use:

```bash
TP_STAGE2_EXPORT_SDF_LAST=true
```

When SDF is skipped, export recovery must still run native RC extraction before SPEF:

```bash
TP_STAGE2_EXPORT_EXTRACT_RC=true
TP_STAGE2_EXPORT_EXTRACT_RC_EFFORT=medium
```

These are the defaults as of 2026-05-13. The generated Tcl emits `setExtractRCMode -engine postRoute -effortLevel medium` followed by `extractRC` before `rcOut -spef`.

Historical diagnostic only: for a last-resort routed SDF container test after normal SDF generation crashes, use:

```bash
TP_STAGE2_SDF_EXPORT_ARGS="-celltiming none -interconn none -view setup_view"
```

This disables cell delay/timing-check content and interconnect annotations. r26 showed this path still crashes in Innovus for the current routed fake-SRAM Gemmini database. After the 2026-05-13 waiver, no further SDF retry is required unless the active plan changes again.
