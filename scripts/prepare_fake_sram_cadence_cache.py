#!/usr/bin/env python3
"""Prepare patched fake SRAM collateral for Cadence ASAP7 flows."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path


DEFAULT_DESIGN = "RISCY"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_lef_area(lef: Path) -> float:
    text = lef.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^\s*SIZE\s+([0-9.]+)\s+BY\s+([0-9.]+)\s*;", text, re.MULTILINE)
    if not match:
        raise ValueError(f"cannot find LEF SIZE in {lef}")
    return float(match.group(1)) * float(match.group(2))


def patch_liberty(src: Path, dst: Path, area: float, voltage: float, temperature: float) -> None:
    text = src.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"nom_temperature\s*:\s*[-0-9.]+\s*;", f"nom_temperature : {temperature:g};", text)
    text = re.sub(r"nom_voltage\s*:\s*[-0-9.]+\s*;", f"nom_voltage : {voltage:.6f};", text)
    text = re.sub(r"voltage_map\(VDD,\s*[-0-9.]+\);", f"voltage_map(VDD, {voltage:.6f});", text)
    text = re.sub(r"temperature\s*:\s*[-0-9.]+\s*;", f"temperature : {temperature:g};", text)
    text = re.sub(r"voltage\s*:\s*[-0-9.]+\s*;", f"voltage : {voltage:.6f};", text)

    if not re.search(r"^\s*area\s*:", text, re.MULTILINE):
        text = re.sub(
            r"(cell\s*\([^)]+\)\s*\{\n)",
            rf"\1        area : {area:.6f};\n",
            text,
            count=1,
        )
    dst.write_text(text, encoding="utf-8")


def prepare_design(src_root: Path, out_root: Path, design: str, voltage: float, temperature: float) -> tuple[int, Path]:
    src_design = src_root / design
    if not src_design.is_dir():
        raise FileNotFoundError(f"missing fake SRAM design root: {src_design}")

    out_design = out_root / design
    for kind in ("lef", "lib", "db"):
        (out_design / kind).mkdir(parents=True, exist_ok=True)

    count = 0
    for lef in sorted((src_design / "lef").glob("*.lef")):
        stem = lef.stem
        lib = src_design / "lib" / f"{stem}.lib"
        db = src_design / "db" / f"{stem}.db"
        if not lib.is_file() or not db.is_file():
            raise FileNotFoundError(f"missing matching lib/db for {lef}")

        area = parse_lef_area(lef)
        shutil.copy2(lef, out_design / "lef" / lef.name)
        shutil.copy2(db, out_design / "db" / db.name)
        patch_liberty(lib, out_design / "lib" / lib.name, area=area, voltage=voltage, temperature=temperature)
        count += 1

    if count == 0:
        raise FileNotFoundError(f"no fake SRAM LEFs found for design {design}")
    return count, out_design


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(os.environ.get("FAKE_SRAM_ASAP7_ROOT", "/home/lisihang/fake_sram/results/asap7")),
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=Path(os.environ.get("FAKE_SRAM_CADENCE_CACHE", repo_root() / ".cache" / "fake_sram" / "asap7")),
    )
    parser.add_argument("--design", default=os.environ.get("FAKE_SRAM_DESIGN", DEFAULT_DESIGN))
    parser.add_argument("--voltage", type=float, default=0.7)
    parser.add_argument("--temperature", type=float, default=25.0)
    args = parser.parse_args()

    try:
        count, out_design = prepare_design(
            args.source_root.resolve(),
            args.cache_root.resolve(),
            args.design,
            voltage=args.voltage,
            temperature=args.temperature,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc))
        return 1

    print(
        f"fake SRAM Cadence cache ready: design={args.design} macros={count} "
        f"cache={out_design} voltage={args.voltage:g} temperature={args.temperature:g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
