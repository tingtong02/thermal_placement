# ATSim v1 Proxy Experiment Attempts

更新时间：2026-05-03

## Attempt 1: generated single-layer proxy input

Command:

```bash
timeout 600 scripts/run_atsim3d.sh \
  --lcfFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.csv \
  --ConfigFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline.config \
  --SimParamsFile thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_simparams.config
```

Result: failed during ATSim3D v1 input parsing before thermal solve.

Evidence:

```text
ValueError: cannot convert float NaN to integer
```

Root cause found by disassembling the local Python 3.8 `.pyc` parser: ATSim v1 calls `pd.read_csv(lcfFile, lineterminator='\n')`. The generated CSVs used Python `csv.writer` default CRLF line endings, so the last lcf header was read as `Clip_num_z\r`; the tool then saw `Clip_num_z` as NaN.

Next action: regenerate all ATSim v1 input CSVs with explicit `lineterminator='\n'`, then rerun the same command.

## Attempt 2: LF-normalized CSV inputs

Result: failed after lcf/floorplan parsing and grid initialization.

Evidence:

```text
chipStack length 0.003373864, width 0.003373864
Grids num: 64 x 64 ; grid length and width: 5.2716625e-05 5.2716625e-05
KeyError: 'TSV'
```

Root cause: ATSim3D v1 `ATSimCore.py` reads `SimParams._sections['TSV']`. The generated `[TSV]` section was placed in the Config file, but ATSim v1 examples place `[TSV]` in `SimParms.config`.

Next action: regenerate inputs with `[TSV]` in the SimParams file.

## Attempt 3: TSV section moved to SimParams

Result: passed. ATSim3D v1 completed the steady solve and wrote layer0 result data.

Evidence:

```text
chipStack length 0.003373864, width 0.003373864
Grids num: 64 x 64 ; grid length and width: 5.2716625e-05 5.2716625e-05
Size of Sparse matrix:  8192
Coarse solve takes 0.62 s.
Fine solve takes 216.46 s.
Res of the Layer0 saved to /home/lisihang/thermal_placement/thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res!
Total takes 265.10 s
```

Artifacts:

- stdout: `logs/run_atsim3d_stdout.log`
- stderr: `logs/run_atsim3d_stderr.log`，为空
- exit status: `logs/run_atsim3d.status`，值为 `0`
- result: `inputs/proxy_stage4_tiled_matmul_os_baseline_lcf.layer0.res`
- summary: `results/atsim_result_summary.json` and `results/atsim_result_summary.csv`
