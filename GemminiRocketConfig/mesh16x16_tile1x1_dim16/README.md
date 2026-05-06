# GemminiRocketConfig mesh16x16_tile1x1_dim16

This is the Gemmini Phase 2 startup entry for the copied dacs-style Cadence flow.

The directory name encodes the concrete Gemmini parameters used by this entry:

```text
mesh16x16_tile1x1_dim16
```

For future Gemmini variants, add a sibling directory under `GemminiRocketConfig/` with the same pattern and keep that variant's paths in its own `env.py` and `main.py`. The current active plan still fixes the real run target to this mesh16x16/tile1x1/DIM16 configuration.

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
