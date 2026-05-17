#!/usr/bin/env python3
"""Reclassify an existing signal activity CSV without rescanning the VCD."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_vcd_activity import classify, load_category_terms  # noqa: E402


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def int_field(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0") or 0))


def float_field(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0.0)


def write_signal_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_region_csv(path: Path, rows: list[dict[str, str]], terms: dict[str, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    region = defaultdict(lambda: {"signals": 0, "toggles": 0, "activity_sum": 0.0})
    for category in terms:
        region[category]
    workload = rows[0].get("workload", "") if rows else ""
    time_steps = rows[0].get("time_steps", "0") if rows else "0"
    last_time = rows[0].get("last_time_ps", "0") if rows else "0"
    for row in rows:
        category = row.get("region", "other")
        region[category]["signals"] += 1
        region[category]["toggles"] += int_field(row, "toggle_count")
        region[category]["activity_sum"] += float_field(row, "normalized_activity")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "workload",
                "region",
                "signal_count",
                "toggle_count",
                "avg_normalized_activity",
                "time_steps",
                "last_time_ps",
            ],
        )
        writer.writeheader()
        for category, item in sorted(region.items(), key=lambda kv: kv[0]):
            signal_count = max(1, int(item["signals"]))
            writer.writerow(
                {
                    "workload": workload,
                    "region": category,
                    "signal_count": item["signals"],
                    "toggle_count": item["toggles"],
                    "avg_normalized_activity": item["activity_sum"] / signal_count,
                    "time_steps": time_steps,
                    "last_time_ps": last_time,
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal-csv", required=True, type=Path)
    parser.add_argument("--hierarchy-map", type=Path)
    parser.add_argument("--output-signal-csv", type=Path)
    parser.add_argument("--region-csv", required=True, type=Path)
    args = parser.parse_args()

    rows = read_rows(args.signal_csv)
    if not rows:
        raise SystemExit(f"no rows found in {args.signal_csv}")
    fieldnames = list(rows[0].keys())
    if "region" not in fieldnames:
        raise SystemExit("signal CSV does not contain a region column")

    terms = load_category_terms(args.hierarchy_map)
    for row in rows:
        row["region"] = classify(row.get("signal_path", ""), terms)
    rows.sort(key=lambda row: int_field(row, "toggle_count"), reverse=True)

    output_signal_csv = args.output_signal_csv or args.signal_csv
    write_signal_csv(output_signal_csv, rows, fieldnames)
    write_region_csv(args.region_csv, rows, terms)
    print(f"signal_csv={output_signal_csv}")
    print(f"region_csv={args.region_csv}")
    print(f"rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
