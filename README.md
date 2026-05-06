# cadence_startup

This is a copied DACS-style Cadence startup tree for Thermal Placement Phase 2.
It is being adapted for GemminiRocketConfig mesh16x16_tile1x1_dim16 with full ASAP7 and fake SRAM.

## Current Entry

```bash
source tools/env_gemmini_thermal.sh
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --dry-run
```

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

- `GemminiRocketConfig/`: current project-specific experiment entry.
- `flow/`: copied flow wrappers from DACS; kept as reference for the Python-driven structure.
- `manager/`: copied DACS tool managers; next area to adapt before real Genus/Innovus execution.
- `tech/`: ASAP7 and Gemmini fake-SRAM tech configuration.
- `utils/`: helper functions used by the copied managers and tech classes.

See `GEMMINI_PHASE2_RESTRUCTURE_PLAN.md` before continuing this adaptation.
