#!/usr/bin/env python3
"""Create minimal HotSpot inputs from smoke activity CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_regions(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda row: row["region"])
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region-csv", required=True, type=Path)
    parser.add_argument("--floorplan", required=True, type=Path)
    parser.add_argument("--ptrace", required=True, type=Path)
    parser.add_argument("--base-power", type=float, default=0.05)
    parser.add_argument("--dynamic-scale", type=float, default=2.0)
    args = parser.parse_args()

    rows = read_regions(args.region_csv)
    if not rows:
        raise SystemExit(f"no region rows in {args.region_csv}")

    args.floorplan.parent.mkdir(parents=True, exist_ok=True)
    args.ptrace.parent.mkdir(parents=True, exist_ok=True)

    # Fixed smoke floorplan: equal-width vertical stripes in a 4 mm x 4 mm chip.
    chip_w = 0.004
    chip_h = 0.004
    block_w = chip_w / len(rows)
    names = [row["region"] for row in rows]

    with args.floorplan.open("w", encoding="utf-8") as f:
        f.write("# Smoke floorplan generated from VCD activity. Dimensions are meters.\n")
        for idx, row in enumerate(rows):
            name = row["region"]
            f.write(f"{name}\t{block_w:.9f}\t{chip_h:.9f}\t{idx * block_w:.9f}\t0.000000000\n")

    powers = []
    for row in rows:
        activity = float(row["avg_normalized_activity"])
        power = args.base_power + args.dynamic_scale * activity
        powers.append(power)

    with args.ptrace.open("w", encoding="utf-8") as f:
        f.write("\t".join(names) + "\n")
        f.write("\t".join(f"{power:.6f}" for power in powers) + "\n")

    print(f"floorplan={args.floorplan}")
    print(f"ptrace={args.ptrace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
