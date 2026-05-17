# Phase1b Scripts

This README documents only the Phase1b-related scripts in `scripts/`. Other repository scripts are intentionally out of scope here.

## Shared Helpers

- `phase1b_gate_replay_common.py`
  - Shared parser/helper code for old and new Phase1b flows.
  - Handles Gemmini top-port parsing, RTL VCD header parsing, signal mapping helpers, and VCD value normalization.

- `phase1b_extract_gemmini_boundary_vectors.py`
  - Shared boundary vector extractor from Stage1 full-SoC RTL VCDs.
  - Old compare validation may keep output expected columns.
  - New formal SAIF flow uses the `--vectors-inputs-only` mode: `cycle`, `time_ps`, `clock`, `reset`, and Gemmini input ports only.

- `phase1b_validate_gate_sim_inputs.py`
  - Gate replay input/collateral validation helper.
  - New formal Phase1b must validate the r28 routed netlist path and regenerate referenced ASAP7 cells plus required UDP primitive collateral from r28, not from the old r2 validation run.

## Historical Old Validation Flow

- `phase1b_run_gate_boundary_replay.py`
  - Historical compare-oriented Phase1b entry point.
  - Used for the 2026-05-14 r2 `mvin_mvout` validity-aware output compare feasibility run.
  - Generates compare/mismatch summaries and is not the formal Phase1b SAIF handoff entry.
  - Its old result directory is:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/
```

The old directory is historical validation only. It is excluded from the new Phase1b handoff manifest and must not be reused as the r28 build cache.

## New Formal Phase1b SAIF Flow

- `phase1b_run_gate_saif_replay.py`
  - Implemented single-workload replay entry point for formal Phase1b.
  - Builds/runs a no-compare SAIF harness around r28 `Gemmini.routed.v`.
  - Runtime arguments provide vectors, SAIF output, trace window, run kind, build root, and output directory.
  - It must not generate output compare CSVs or mismatch reports.

- `phase1b_run_gate_saif_workloads.py`
  - Implemented formal orchestration entry point.
  - Owns the full r28 Phase1b SAIF handoff workflow:
    - create/use `gate_activity/phase1b_gate_saif_r28_20260515/`, stopping if non-empty by default;
    - regenerate r28 referenced-cell-only ASAP7 library plus required UDP primitives;
    - build one shared r28 `VGemmini` executable;
    - run `smoke_mvin_mvout_100cyc/` with `[66875550, 67075550)` ps trace window;
    - smoke warms up from `time_ps=0` and only enables trace in `[66875550, 67075550)`; do not cap total replay at the first 100 global cycles;
    - run formal workloads one at a time in order: `mvin_mvout`, `tiled_matmul_ws`, `tiled_matmul_os`;
    - write per-workload manifests plus global `phase1b_gate_saif_handoff_manifest.json` and `phase1b_gate_saif_method_report.md`.

Formal fixed build policy for the new flow:

```text
--verilate-jobs 192
--threads 16
make -j192 CXX=clang++ LINK=clang++
--compiler clang
--no-timing
--trace-saif
--trace-depth 9
--output-split 200
--output-split-cfuncs 20
--output-split-ctrace 20
-CFLAGS "-O0 -g0"
```

Do not use `--hierarchical` by default. Stop and ask before trying it. Do not fallback from r28 to r2 without user confirmation. If generated C++ in the new build tree exceeds `128 MiB`, split it into 32 helper C++ files before make; this may be automated or done manually inside the new run directory.


## Phase1b Acceleration Scripts

The 2026-05-15 acceleration attempt uses separate acceleration-only scripts. These names are reserved for the implementation and must not be merged into the main CSV replay scripts:

- `phase1b_convert_boundary_vectors_to_binary_acceleration.py`
  - Implemented converter for copied inputs-only `boundary_vectors.csv` into fixed little-endian `boundary_vectors.bin`.
  - Generates `boundary_vectors_binary_layout.json` and `boundary_vectors_binary_manifest.json`.
  - Rejects compare/expected-output columns and any non-2-state bit tokens.

- `phase1b_run_gate_saif_binary_replay_acceleration.py`
  - Implemented binary replay/harness-only relink entry point.
  - Generates `tb_phase1b_gate_saif_binary.cpp`, compiles only the harness object, and relinks `accelerate/build/VGemmini_accelerate` against the existing r28 generated archive/runtime objects.
  - Does not rerun Verilator frontend, does not recompile generated `VGemmini*.o`, does not modify r28 or RTL, and does not change trace depth or SAIF dump policy.

Acceleration outputs and method docs live under:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/accelerate/
```

This acceleration route is not the default Phase1b handoff method until smoke/runtime evidence is available and the user confirms adoption.

Phase3 handoff note: new formal Phase1b SAIF files are raw Verilator `Gemmini` top-rooted SAIFs. Phase3 must perform Cadence `read_saif` scope/instance mapping and annotation coverage reporting.

Current r28 build status as of 2026-05-15: Verilator frontend/elaboration succeeded and generated 328935 C++ objects. `make -j192 CXX=clang++ LINK=clang++` repeatedly segfaulted after object compilation on the huge build graph. After verifying all expected `.o` files were present, the archive/index/link tail was manually completed inside the build directory, producing `build/verilator_build/VGemmini`. Evidence is recorded in `build/object_completeness_check_20260515.json` and `build/manual_link_completion_20260515.json` under the formal output root.
