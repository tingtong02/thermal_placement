#!/usr/bin/env python3
"""Extract a small module/region activity summary from a VCD file.

This parser is intentionally streaming and conservative. It is meant for
smoke-level flow validation, not final signoff-grade activity accounting.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


@dataclass
class Signal:
    path: str
    width: int
    last: str | None = None
    toggles: int = 0
    changes: int = 0


def load_category_terms(path: Path | None) -> dict[str, list[str]]:
    terms: dict[str, list[str]] = {
        "pe_array": ["gemmini", "mesh", "pe", "tile"],
        "scratchpad": ["scratchpad", "spad", "sp_bank"],
        "accumulator": ["accumulator", "acc_", "accumulator_mem"],
        "load_store_dma": ["load_controller", "store_controller", "streamreader", "streamwriter", "dma"],
        "controller": ["controller", "reservationstation", "cmd", "rob"],
        "tl_soc_glue": ["tl", "axi", "cache", "bus"],
        "non_gemmini_context": ["rocket", "system", "debug", "jtag", "uart"],
    }

    if path is None or not path.exists() or yaml is None:
        return terms

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    categories = data.get("categories", {})
    for category, value in categories.items():
        modules = value.get("modules", []) if isinstance(value, dict) else []
        terms.setdefault(category, [])
        terms[category].extend(str(module).lower() for module in modules)
    return terms


def classify(path: str, terms: dict[str, list[str]]) -> str:
    lower = path.lower()
    for category, category_terms in terms.items():
        for term in category_terms:
            if term and term.lower() in lower:
                return category
    return "other"


def clean_name(name: str) -> str:
    return name.replace(" ", "")


def value_toggle_delta(old: str, new: str, width: int) -> int:
    if old == new:
        return 0
    if set(old) <= {"0", "1"} and set(new) <= {"0", "1"}:
        max_len = max(len(old), len(new), width)
        old = old.zfill(max_len)
        new = new.zfill(max_len)
        return sum(1 for a, b in zip(old, new) if a != b)
    return max(1, min(width, 1))


def iter_vcd(path: Path) -> tuple[dict[str, Signal], int, int]:
    signals: dict[str, Signal] = {}
    scopes: list[str] = []
    in_header = True
    time_steps = 0
    last_time = 0

    with path.open("r", encoding="ascii", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if in_header:
                if line.startswith("$scope"):
                    parts = line.split()
                    if len(parts) >= 3:
                        scopes.append(clean_name(parts[2]))
                elif line.startswith("$upscope"):
                    if scopes:
                        scopes.pop()
                elif line.startswith("$var"):
                    parts = line.split()
                    if len(parts) >= 6:
                        width = int(parts[2])
                        code = parts[3]
                        name = clean_name("".join(parts[4:-1]))
                        full_path = ".".join(scopes + [name])
                        signals.setdefault(code, Signal(path=full_path, width=width))
                elif line.startswith("$enddefinitions"):
                    in_header = False
                continue

            if line.startswith("#"):
                time_steps += 1
                try:
                    last_time = int(line[1:])
                except ValueError:
                    pass
                continue

            if line[0] in "01xzXZ":
                value = line[0].lower()
                code = line[1:]
            elif line[0] in "bBrR":
                parts = line.split()
                if len(parts) != 2:
                    continue
                value = parts[0][1:].lower()
                code = parts[1]
            else:
                continue

            signal = signals.get(code)
            if signal is None:
                continue
            if signal.last is not None:
                delta = value_toggle_delta(signal.last, value, signal.width)
                if delta:
                    signal.toggles += delta
                    signal.changes += 1
            signal.last = value

    return signals, time_steps, last_time


def write_outputs(
    signals: dict[str, Signal],
    time_steps: int,
    last_time: int,
    workload: str,
    terms: dict[str, list[str]],
    signal_csv: Path,
    region_csv: Path,
    top_signals: int,
    exclude_clocks: bool,
) -> None:
    signal_csv.parent.mkdir(parents=True, exist_ok=True)
    region_csv.parent.mkdir(parents=True, exist_ok=True)

    clock_re = re.compile(r"(^|[._])(clock|clk|reset)([._]|$)", re.IGNORECASE)
    rows = []
    region = defaultdict(lambda: {"signals": 0, "toggles": 0, "activity_sum": 0.0})
    for category in terms:
        region[category]

    denom = max(1, time_steps)
    for signal in signals.values():
        if exclude_clocks and clock_re.search(signal.path):
            continue
        category = classify(signal.path, terms)
        activity = signal.toggles / float(denom * max(1, signal.width))
        row = {
            "workload": workload,
            "signal_path": signal.path,
            "region": category,
            "width": signal.width,
            "toggle_count": signal.toggles,
            "value_change_count": signal.changes,
            "time_steps": time_steps,
            "last_time_ps": last_time,
            "normalized_activity": activity,
        }
        rows.append(row)
        region[category]["signals"] += 1
        region[category]["toggles"] += signal.toggles
        region[category]["activity_sum"] += activity

    rows.sort(key=lambda item: int(item["toggle_count"]), reverse=True)
    if top_signals > 0:
        rows = rows[:top_signals]

    with signal_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "workload",
                "signal_path",
                "region",
                "width",
                "toggle_count",
                "value_change_count",
                "time_steps",
                "last_time_ps",
                "normalized_activity",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with region_csv.open("w", newline="", encoding="utf-8") as f:
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
    parser.add_argument("--vcd", required=True, type=Path)
    parser.add_argument("--hierarchy-map", type=Path)
    parser.add_argument("--workload", default="thermal_smoke")
    parser.add_argument("--signal-csv", required=True, type=Path)
    parser.add_argument("--region-csv", required=True, type=Path)
    parser.add_argument("--top-signals", type=int, default=10000)
    parser.add_argument("--include-clocks", action="store_true")
    args = parser.parse_args()

    signals, time_steps, last_time = iter_vcd(args.vcd)
    terms = load_category_terms(args.hierarchy_map)
    write_outputs(
        signals=signals,
        time_steps=time_steps,
        last_time=last_time,
        workload=args.workload,
        terms=terms,
        signal_csv=args.signal_csv,
        region_csv=args.region_csv,
        top_signals=args.top_signals,
        exclude_clocks=not args.include_clocks,
    )
    print(f"parsed_signals={len(signals)} time_steps={time_steps} last_time_ps={last_time}")
    print(f"signal_csv={args.signal_csv}")
    print(f"region_csv={args.region_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
