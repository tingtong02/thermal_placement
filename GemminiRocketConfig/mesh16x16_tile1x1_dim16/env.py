"""Environment constants for the GemminiRocketConfig mesh16x16 Phase 2 entry."""

from __future__ import annotations

import os
from pathlib import Path

CADENCE_STARTUP_ROOT = Path(__file__).resolve().parents[2]
TP_ROOT = Path(os.environ.get("THERMAL_PLACEMENT_ROOT", "/home/lisihang/thermal_placement"))
RUN_ROOT = TP_ROOT / "runs" / "GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff"
RESULT_ROOT = RUN_ROOT / "physical"
RTL_FILELIST = RUN_ROOT / "rtl" / "generated" / "chipyard.harness.TestHarness.GemminiRocketConfig.top.f"
ASAP7_HOME = Path(os.environ.get("ASAP7_HOME", "/home/lisihang/asap7"))
FAKE_SRAM_CACHE = Path(os.environ.get("FAKE_SRAM_CADENCE_CACHE", TP_ROOT / ".cache" / "fake_sram" / "asap7")) / os.environ.get("FAKE_SRAM_DESIGN", "Gemmini")
GENUS_BIN = Path(os.environ.get("GENUS_BIN", "/opt/eda/Cadence_DDI_23.14/bin/genus"))
INNOVUS_BIN = Path(os.environ.get("INNOVUS_BIN", "/opt/eda/Cadence_DDI_23.14/bin/innovus"))
