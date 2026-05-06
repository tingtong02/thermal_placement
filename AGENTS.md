# AGENTS.md

Rules for this copied Cadence startup repository:

- Run all project Python commands from the parent repository's `thermal_placement` conda environment.
  Preferred entry:

  ```bash
  cd /home/lisihang/thermal_placement
  source tools/env_gemmini_thermal.sh
  ```

- Do not use base conda or system Python for checks or flow scripts.
- After any modification inside `runs/cadence_startup`, run the smallest relevant checks and create a Git commit in this repository before handing work back.
- Keep this tree Python-manager-first. Tcl is generated or launched by Python managers except for one-off tool diagnostics.
- The current active Gemmini entry is `GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py`.
