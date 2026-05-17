#!/usr/bin/env python3
"""Extract a small module/region activity summary from a VCD file.

The default path remains a conservative single-process streaming parse.
When requested, the parser can split the VCD body into chunks, parse them in
parallel workers, and merge signal boundary state between chunks.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
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


@dataclass
class ChunkStats:
    first: str
    last: str
    toggles: int
    changes: int


@dataclass
class BodyChunkResult:
    time_steps: int
    last_time: int
    signals: dict[str, ChunkStats]


SCALAR_PREFIXES = set("01xzXZ")
VECTOR_PREFIXES = set("bBrR")
DEFAULT_TERMS: dict[str, list[str]] = {
    "scratchpad": ["scratchpad", "spad", "sp_bank", "spadmem"],
    "accumulator": ["accumulator", "accumulator_mem", "accumulator_scale"],
    "load_store_dma": ["loadcontroller", "load_controller", "storecontroller", "store_controller", "streamreader", "streamwriter", "dma"],
    "controller": ["executecontroller", "reservationstation", "gemminicmd", "cmd", "rob", "loopmatmul", "unroller"],
    "pe_array": ["meshwithdelays", "mesh", "macunit", "pe_256", "pe"],
    "tl_soc_glue": ["tilelink", "rocc", "axi", "cache", "bus"],
    "gemmini_other": ["gemmini"],
    "non_gemmini_context": ["rocket", "system", "debug", "jtag", "uart", "testharness"],
}


def load_category_terms(path: Path | None) -> dict[str, list[str]]:
    terms = {category: values[:] for category, values in DEFAULT_TERMS.items()}

    if path is None or not path.exists() or yaml is None:
        return terms

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    categories = data.get("categories", {})
    for category, value in categories.items():
        modules = value.get("modules", []) if isinstance(value, dict) else []
        terms.setdefault(category, [])
        terms[category].extend(str(module).lower() for module in modules)
    return terms


def term_matches(lower_path: str, term: str) -> bool:
    term = term.lower()
    if not term:
        return False
    components = re.split(r"[^a-zA-Z0-9_]+", lower_path)
    if term == "pe":
        return any(component == "pe" or component.startswith("pe_") for component in components)
    if len(term) <= 3:
        return any(component == term or component.startswith(term + "_") or component.startswith(term) for component in components)
    return term in lower_path


def classify(path: str, terms: dict[str, list[str]]) -> str:
    lower = path.lower()
    for category, category_terms in terms.items():
        for term in category_terms:
            if term_matches(lower, str(term)):
                return category
    return "other"


def alias_priority(path: str) -> int:
    lower = path.lower()
    score = 0
    if ".gemmini" in lower or lower.endswith("gemmini"):
        score += 1000
    for token, weight in (
        (".mesh", 400),
        ("mesh_", 350),
        ("execute", 300),
        ("load", 260),
        ("store", 260),
        ("stream", 240),
        ("scratch", 220),
        ("spad", 220),
        ("accumulator", 220),
        ("dma", 180),
        ("rocc", 120),
    ):
        if token in lower:
            score += weight
    if "monitor.watchdog" in lower:
        score -= 200
    return score


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


def parse_vcd_header(path: Path) -> tuple[dict[str, Signal], int]:
    signals: dict[str, Signal] = {}
    scopes: list[str] = []

    with path.open("rb") as f:
        while True:
            raw_line = f.readline()
            if not raw_line:
                raise RuntimeError(f"missing $enddefinitions in VCD: {path}")
            line = raw_line.decode("ascii", errors="ignore").strip()
            if not line:
                continue
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
                    existing = signals.get(code)
                    if existing is None:
                        signals[code] = Signal(path=full_path, width=width)
                    elif alias_priority(full_path) > alias_priority(existing.path):
                        existing.path = full_path
                        existing.width = max(existing.width, width)
            elif line.startswith("$enddefinitions"):
                return signals, f.tell()


def parse_value_change(line: str) -> tuple[str, str] | None:
    if not line:
        return None
    prefix = line[0]
    if prefix in SCALAR_PREFIXES:
        return line[1:], prefix.lower()
    if prefix in VECTOR_PREFIXES:
        parts = line.split()
        if len(parts) != 2:
            return None
        return parts[1], parts[0][1:].lower()
    return None


def build_body_chunks(path: Path, body_offset: int, workers: int) -> list[tuple[int, int]]:
    file_size = path.stat().st_size
    if body_offset >= file_size:
        return []

    worker_count = max(1, min(workers, 128))
    if worker_count == 1:
        return [(body_offset, file_size)]

    body_size = file_size - body_offset
    step = max(1, math.ceil(body_size / worker_count))
    boundaries = [body_offset]

    with path.open("rb") as f:
        for index in range(1, worker_count):
            target = body_offset + index * step
            if target >= file_size:
                break
            f.seek(target)
            f.readline()
            boundary = f.tell()
            if boundary <= boundaries[-1] or boundary >= file_size:
                continue
            boundaries.append(boundary)

    boundaries.append(file_size)
    chunks: list[tuple[int, int]] = []
    for start, end in zip(boundaries, boundaries[1:]):
        if start < end:
            chunks.append((start, end))
    return chunks


def parse_vcd_chunk(path_str: str, start: int, end: int, widths: dict[str, int]) -> BodyChunkResult:
    path = Path(path_str)
    time_steps = 0
    last_time = 0
    per_signal: dict[str, ChunkStats] = {}

    with path.open("rb") as f:
        f.seek(start)
        while True:
            line_start = f.tell()
            if line_start >= end:
                break
            raw_line = f.readline()
            if not raw_line:
                break
            line = raw_line.decode("ascii", errors="ignore").strip()
            if not line:
                continue
            if line.startswith("#"):
                time_steps += 1
                try:
                    last_time = int(line[1:])
                except ValueError:
                    pass
                continue

            parsed = parse_value_change(line)
            if parsed is None:
                continue
            code, value = parsed
            width = widths.get(code)
            if width is None:
                continue

            stats = per_signal.get(code)
            if stats is None:
                per_signal[code] = ChunkStats(first=value, last=value, toggles=0, changes=0)
                continue

            delta = value_toggle_delta(stats.last, value, width)
            if delta:
                stats.toggles += delta
                stats.changes += 1
            stats.last = value

    return BodyChunkResult(time_steps=time_steps, last_time=last_time, signals=per_signal)


def iter_vcd(path: Path, workers: int = 1) -> tuple[dict[str, Signal], int, int, int]:
    signals, body_offset = parse_vcd_header(path)
    widths = {code: signal.width for code, signal in signals.items()}
    chunks = build_body_chunks(path, body_offset, workers)
    if not chunks:
        return signals, 0, 0, 0

    if len(chunks) == 1:
        chunk_results = [parse_vcd_chunk(str(path), chunks[0][0], chunks[0][1], widths)]
    else:
        with ProcessPoolExecutor(max_workers=len(chunks)) as executor:
            futures = [executor.submit(parse_vcd_chunk, str(path), start, end, widths) for start, end in chunks]
            chunk_results = [future.result() for future in futures]

    time_steps = 0
    last_time = 0
    for result in chunk_results:
        time_steps += result.time_steps
        if result.last_time:
            last_time = result.last_time
        for code, stats in result.signals.items():
            signal = signals.get(code)
            if signal is None:
                continue
            if signal.last is not None:
                delta = value_toggle_delta(signal.last, stats.first, signal.width)
                if delta:
                    signal.toggles += delta
                    signal.changes += 1
            signal.toggles += stats.toggles
            signal.changes += stats.changes
            signal.last = stats.last

    return signals, time_steps, last_time, len(chunks)


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
        leaf_name = signal.path.rsplit(".", 1)[-1]
        if exclude_clocks and clock_re.search(leaf_name):
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcd", required=True, type=Path)
    parser.add_argument("--hierarchy-map", type=Path)
    parser.add_argument("--workload", default="thermal_smoke")
    parser.add_argument("--signal-csv", required=True, type=Path)
    parser.add_argument("--region-csv", required=True, type=Path)
    parser.add_argument("--top-signals", type=int, default=10000)
    parser.add_argument("--include-clocks", action="store_true")
    parser.add_argument("--workers", type=int, default=1, help="Number of VCD body parsing workers to use (default: 1)")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.workers > 128:
        parser.error("--workers must be <= 128")
    return args


def main() -> int:
    args = parse_args()
    signals, time_steps, last_time, chunk_count = iter_vcd(args.vcd, workers=args.workers)
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
    print(f"parse_workers={args.workers} body_chunks={chunk_count}")
    print(f"parsed_signals={len(signals)} time_steps={time_steps} last_time_ps={last_time}")
    print(f"signal_csv={args.signal_csv}")
    print(f"region_csv={args.region_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
