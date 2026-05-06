# cadence_startup

This is a copied DACS-style Cadence startup tree for Thermal Placement Phase 2.
It is being adapted for GemminiRocketConfig with full ASAP7 and fake SRAM.

## Current Entry

```bash
source tools/env_gemmini_thermal.sh
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --dry-run
```

`GemminiRocketConfig/` is the Chipyard config family. The next directory level is the concrete Gemmini parameter set. The current active set is:

```text
mesh16x16_tile1x1_dim16
```

Future Gemmini parameter sets can be added as sibling entries, for example:

```text
GemminiRocketConfig/
  mesh16x16_tile1x1_dim16/
  <other_mesh_tile_dim>/
```

Each parameter-set entry should own its `env.py`, `main.py`, and local README, and should point to the matching run root under `runs/`. The active project plan currently permits only `mesh16x16_tile1x1_dim16`; adding another parameter set for real runs requires updating the active plan first.

Inputs come from:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/rtl/generated/
```

Stage 2 outputs should go to:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/
```

## Local Tools

- Genus: `/opt/eda/Cadence_DDI_23.14/bin/genus`, `23.14-s090_1`
- Innovus: `/opt/eda/Cadence_DDI_23.14/bin/innovus`, `v23.14-s088_1`
- ASAP7 root: `/home/lisihang/asap7`
- ASAP7 NLDM cache: `.cache/asap7/asap7sc7p5t_28/NLDM`
- fake SRAM cache: `.cache/fake_sram/asap7/Gemmini`

## Directory Notes

- `GemminiRocketConfig/`: project-specific entries grouped by Gemmini parameter set.
- `flow/`: copied flow wrappers from DACS; kept as reference for the Python-driven structure.
- `manager/`: copied DACS tool managers; next area to adapt before real Genus/Innovus execution.
- `tech/`: ASAP7 and Gemmini fake-SRAM tech configuration.
- `utils/`: helper functions used by the copied managers and tech classes.

See `GEMMINI_PHASE2_RESTRUCTURE_PLAN.md` before continuing this adaptation.
