# Gemmini Phase 2 cadence_startup Restructure Plan

Date: 2026-05-06
Branch target: `GemminiRocketConfig_collection0506`

If context is compressed or memory is uncertain, reread this file before editing `runs/cadence_startup`.

## User-Confirmed Decisions

1. Stage 2 output root changes from:

   ```text
   runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/cadence/runs/<tag>/
   ```

   to:

   ```text
   runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/
   ```

2. `manager/` is kept for now and recorded as the next implementation area. Do not rewrite it in this pass.
3. `tech/` should be adapted now. `tech/asap7.py` may be adjusted to use this project's default ASAP7/cache paths, and a Gemmini-specific tech layer should be added.
4. `genus.cmd`, `innovus.cmd`, and `README.md` should stay concise, similar to the original dacs style, but reflect the current Cadence/Gemmini startup environment.
5. `design/` should be removed. Scripts must stop importing `design.*` and should point at the active Gemmini RTL run directory.
6. `experiment/` should be replaced by:

   ```text
   GemminiRocketConfig/
     mesh16x16_tile1x1_dim16/
       env.py
       main.py
       README.md
   ```

7. The Gemmini entry should read RTL from and write results to:

   ```text
   /home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff
   ```

8. After changes, run lightweight validation only: syntax checks, no `design.*` imports, `--preflight`, and `--dry-run`.
9. Commit the `runs/cadence_startup` sub-repository after validation.

## Execution Checklist

- Rename current branch to `GemminiRocketConfig_collection0506`.
- Delete `design/`.
- Delete old `experiment/` and create the new Gemmini config path.
- Add a concise Gemmini `main.py` supporting `--preflight`, `--dry-run`, and `--print-config`.
- Add `tech/gemmini_asap7.py` and lightly adapt `tech/asap7.py` project defaults.
- Update `README.md`, `genus.cmd`, and `innovus.cmd` concisely.
- Run:

  ```bash
  source tools/env_gemmini_thermal.sh
  python -m py_compile runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py runs/cadence_startup/tech/asap7.py runs/cadence_startup/tech/gemmini_asap7.py
  rg -n "from design|import design" runs/cadence_startup --glob '!.git/**'
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
  python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --dry-run
  ```

- Commit the sub-repository.
