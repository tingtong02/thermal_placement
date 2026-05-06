# GemminiRocketConfig mesh16x16_tile1x1_dim16

This is the Gemmini Phase 2 startup entry for the copied dacs-style Cadence flow.

The directory name encodes the concrete Gemmini parameters used by this entry:

```text
mesh16x16_tile1x1_dim16
```

For future Gemmini variants, add a sibling directory under `GemminiRocketConfig/` with the same pattern and keep that variant's paths in its own `env.py` and `main.py`. The current active plan still fixes the real run target to this mesh16x16/tile1x1/DIM16 configuration.

Run from the parent repository with the shared conda environment:

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

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
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --dry-run
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-scripts
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-genus-elab
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-genus-syn
```

`--run-genus-elab` launches Genus for frontend/elaboration only; the other checks do not launch Cadence commercial tools.
