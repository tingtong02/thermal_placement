# GemminiRocketConfig mesh16x16_tile1x1_dim16

This is the Gemmini Phase 2 startup entry for the copied dacs-style Cadence flow.

Inputs come from:

```text
/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/rtl/generated/
```

Outputs are staged under:

```text
/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/
```

Initial checks:

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --dry-run
```

No Cadence commercial tool is launched by these startup checks.
