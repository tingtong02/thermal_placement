#!/usr/bin/env python3
"""Prepare the full ASAP7 NLDM Liberty cache for Cadence flows."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


DEFAULT_VTS = ("RVT", "LVT", "SLVT")
DEFAULT_GROUPS = ("SIMPLE", "INVBUF", "SEQ", "AO", "OA")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_archives(src_dir: Path, vts: tuple[str, ...], corner: str) -> list[Path]:
    archives: list[Path] = []
    for group in DEFAULT_GROUPS:
        for vt in vts:
            matches = sorted(src_dir.glob(f"asap7sc7p5t_{group}_{vt}_{corner}_nldm_*.lib.7z"))
            if not matches:
                raise FileNotFoundError(f"missing archive for group={group} vt={vt} corner={corner} in {src_dir}")
            archives.extend(matches)
    return archives


def extractor() -> str:
    for name in ("bsdtar", "7z"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in (Path("/home/lisihang/miniconda3/bin/bsdtar"),):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise FileNotFoundError("missing extractor: install or expose bsdtar or 7z")


def extract_archive(tool: str, archive: Path, out_dir: Path) -> None:
    if Path(tool).name == "7z":
        subprocess.run([tool, "x", "-y", f"-o{out_dir}", str(archive)], check=True)
    else:
        subprocess.run([tool, "-xf", str(archive), "-C", str(out_dir)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asap7-home", type=Path, default=Path(os.environ.get("ASAP7_HOME", "/home/lisihang/asap7")))
    parser.add_argument("--version", default=os.environ.get("ASAP7_STDCELL_VERSION", "asap7sc7p5t_28"))
    parser.add_argument("--corner", default=os.environ.get("ASAP7_CORNER", "TT"))
    parser.add_argument("--vt", action="append", choices=DEFAULT_VTS, help="VT class to include. May be repeated.")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(os.environ.get("ASAP7_LIB_CACHE", repo_root() / ".cache" / "asap7" / "asap7sc7p5t_28" / "NLDM")),
    )
    parser.add_argument("--check-only", action="store_true", help="Validate source archives and existing cache without extracting.")
    args = parser.parse_args()

    vts = tuple(args.vt) if args.vt else DEFAULT_VTS
    src_dir = args.asap7_home / args.version / "LIB" / "NLDM"
    if not src_dir.is_dir():
        print(f"missing ASAP7 NLDM source directory: {src_dir}")
        return 1

    try:
        archives = find_archives(src_dir, vts, args.corner)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    expected_libs = [args.cache_dir / archive.name.removesuffix(".7z") for archive in archives]
    missing_libs = [path for path in expected_libs if not path.is_file()]

    if args.check_only:
        print(f"ASAP7 archives ok: source={src_dir} archives={len(archives)} vt={','.join(vts)} corner={args.corner}")
        if missing_libs:
            print(f"ASAP7 Liberty cache incomplete: cache={args.cache_dir} missing={len(missing_libs)}")
            return 1
        print(f"ASAP7 Liberty cache ok: cache={args.cache_dir} libs={len(expected_libs)}")
        return 0

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        tool = extractor()
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    extracted = 0
    for archive, lib in zip(archives, expected_libs, strict=True):
        if lib.is_file():
            continue
        extract_archive(tool, archive, args.cache_dir)
        if not lib.is_file():
            print(f"extractor did not create expected Liberty: {lib}")
            return 1
        extracted += 1

    print(
        f"ASAP7 Liberty cache ready: cache={args.cache_dir} "
        f"libs={len(expected_libs)} extracted={extracted} vt={','.join(vts)} corner={args.corner}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
