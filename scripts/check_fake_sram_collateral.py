#!/usr/bin/env python3
"""Validate external fake SRAM collateral paths."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


DEFAULT_DESIGNS = (
    "RISCY",
    "RISCY-FPU",
    "Vortex-large",
    "Vortex-small",
    "nvdla-large",
    "nvdla-small",
    "openc910-1",
    "zero-riscy",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def basenames(paths: list[Path], suffix: str) -> set[str]:
    return {path.name.removesuffix(suffix) for path in paths}


def validate_design(root: Path, design: str) -> tuple[bool, str]:
    design_root = root / design
    lef_dir = design_root / "lef"
    lib_dir = design_root / "lib"
    db_dir = design_root / "db"

    missing_dirs = [str(path) for path in (lef_dir, lib_dir, db_dir) if not path.is_dir()]
    if missing_dirs:
        return False, f"{design}: missing directories: {', '.join(missing_dirs)}"

    lefs = sorted(lef_dir.glob("*.lef"))
    libs = sorted(lib_dir.glob("*.lib"))
    dbs = sorted(db_dir.glob("*.db"))
    if not lefs or not libs or not dbs:
        return False, f"{design}: empty collateral set lef={len(lefs)} lib={len(libs)} db={len(dbs)}"

    lef_names = basenames(lefs, ".lef")
    lib_names = basenames(libs, ".lib")
    db_names = basenames(dbs, ".db")
    if lef_names != lib_names or lef_names != db_names:
        missing_lib = sorted(lef_names - lib_names)
        missing_db = sorted(lef_names - db_names)
        extra_lib = sorted(lib_names - lef_names)
        extra_db = sorted(db_names - lef_names)
        return (
            False,
            f"{design}: basename mismatch "
            f"missing_lib={missing_lib[:5]} missing_db={missing_db[:5]} "
            f"extra_lib={extra_lib[:5]} extra_db={extra_db[:5]}",
        )

    return True, f"{design}: {len(lefs)} macros with matching lef/lib/db"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("FAKE_SRAM_ASAP7_ROOT", Path("/home/lisihang/fake_sram") / "results" / "asap7")),
        help="ASAP7 fake SRAM result root. Defaults to FAKE_SRAM_ASAP7_ROOT or /home/lisihang/fake_sram/results/asap7.",
    )
    parser.add_argument(
        "--design",
        action="append",
        choices=DEFAULT_DESIGNS,
        help="Design subset to validate. May be passed multiple times.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"missing fake SRAM ASAP7 root: {root}")
        return 1

    designs = tuple(args.design) if args.design else DEFAULT_DESIGNS
    ok = True
    total = 0
    for design in designs:
        design_ok, message = validate_design(root, design)
        print(message)
        ok = ok and design_ok
        if design_ok:
            count = int(message.split(": ", 1)[1].split(" ", 1)[0])
            total += count

    if ok:
        print(f"fake SRAM ASAP7 collateral ok: root={root} designs={len(designs)} macros={total}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
