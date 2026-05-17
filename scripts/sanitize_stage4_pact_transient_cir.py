#!/usr/bin/env python3
"""Sanitize a generated PACT transient Xyce netlist for local Xyce."""

from __future__ import annotations

import argparse
import configparser
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-params", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    cfg = configparser.ConfigParser()
    cfg.read(args.model_params)
    grid = int(manifest["grid"])
    cell_side = float(manifest["cell_side_m"])
    si_thickness = 0.0001
    si_thermal_resistivity = 0.0077
    si_lateral_r = si_thermal_resistivity * cell_side / (cell_side * si_thickness)
    total_time = cfg.get("Simulation", "total_simulation_time", fallback=None)
    if total_time is None:
        total_time = cfg.get("Simulation", "total_simualation_time")
    if total_time is None or total_time == "None":
        raise SystemExit("could not determine total_simulation_time from modelParams")

    text = args.cir.read_text(encoding="utf-8")
    inf_pattern = re.compile(r"^(R_0_\d+_\d+_[12]\s+\S+\s+\S+\s+)inf$", re.MULTILINE)
    text, inf_count = inf_pattern.subn(lambda m: f"{m.group(1)}{si_lateral_r:.15g}", text)
    text, tran_count = re.subn(r"(\.TRAN\s+\S+\s+)None(\b)", rf"\g<1>{total_time}\2", text)
    text, opt_count = re.subn(r"(\.OPTIONS OUTPUT INITIAL_INTERVAL=\S+\s+)None(\b)", rf"\g<1>{total_time}\2", text)
    if inf_count == 0:
        raise SystemExit("no Si-layer lateral inf resistors were replaced; refusing silent pass")
    if tran_count == 0:
        raise SystemExit("no .TRAN None field was replaced; refusing silent pass")
    args.output.write_text(text, encoding="utf-8")
    print(f"grid={grid}")
    print(f"si_lateral_r={si_lateral_r:.15g}")
    print(f"total_time={total_time}")
    print(f"replaced_inf_resistors={inf_count}")
    print(f"replaced_tran_none={tran_count}")
    print(f"replaced_output_none={opt_count}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
