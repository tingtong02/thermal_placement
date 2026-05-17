#!/usr/bin/env bash
set -euo pipefail

# Generated helper only. Run this only after explicit approval.
# It launches Innovus no-GUI on the generated non-signoff Phase3 mvin_mvout Tcl.
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
innovus -no_gui -files /home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/scripts/phase3_mvin_mvout_read_activity_power.tcl -log /home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/logs/phase3_mvin_mvout_innovus.log
