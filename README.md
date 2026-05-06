# cadence_startup

This is a copied DACS-style Cadence startup tree for Thermal Placement Phase 2.
It is being adapted for GemminiRocketConfig with full ASAP7 and fake SRAM.

## Required Environment

Run Python from the parent repository's `thermal_placement` conda environment:

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

Do not use base conda or system Python for this repository. After any modification inside `runs/cadence_startup`, run the smallest relevant checks and commit the change in this repository.

## Current Entry

```bash
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --preflight
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --dry-run
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --write-scripts
python runs/cadence_startup/GemminiRocketConfig/mesh16x16_tile1x1_dim16/main.py --run-genus-elab
```

`--preflight` validates inputs and environment. `--dry-run` writes a startup manifest. `--write-scripts` exercises the dacs-style `manager/` path and generates Genus/Innovus Tcl without launching commercial tools. `--run-genus-elab` launches a Python-managed Genus frontend/elaboration smoke without synthesis.

## Gemmini Entry Layout

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

## Active Paths

Inputs come from:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/rtl/generated/
```

Stage 2 outputs should go to:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/
```

The current `--write-scripts` check writes manager-generated scripts under:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/genus/scripts/
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/<tag>/innovus/scripts/
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
- `manager/`: copied DACS tool managers, now adapted for same-env launch commands and script-only Genus/Innovus generation.
- `tech/`: ASAP7 and Gemmini fake-SRAM tech configuration.
- `utils/`: helper functions used by the copied managers and tech classes.

## Current Manager Status

`manager/` adaptation was required because Phase 2 must stay Python-manager-first. The current adaptation supports same-environment command construction through `env_setup_script`, fake-SRAM libcell resolution in Genus, Innovus IO pin assignment, final routed artifact export commands, and `script_only` mode for checks. Real Genus/Innovus launch remains a separate explicit step after reviewing the generated Tcl.
