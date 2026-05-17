#!/usr/bin/env python3
"""Convert Phase1b inputs-only boundary vectors to packed binary rows.

Acceleration-only helper. It intentionally does not support old compare CSVs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

FORMAT = "phase1b_binary_boundary_vectors_acceleration"
VERSION = 1
ENDIANNESS = "little"
MAGIC = b"TPP1B_BINVEC" + b"\0" * 4
HEADER_STRUCT = struct.Struct("<16sIIQIIQ")
HEADER_BYTES = HEADER_STRUCT.size
ROW_SEMANTICS = "row N-1 input vector drives replay cycle N; trace decision uses row N time_ps"
COPY_NAMES = [
    "boundary_vectors.csv",
    "boundary_signal_map.json",
    "boundary_signal_map.csv",
    "boundary_vectors_manifest.json",
    "phase1b_extract_report.md",
    "extract_command.log",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--copy-inputs", action="store_true")
    parser.add_argument("--overwrite-input-copy", action="store_true")
    parser.add_argument("--progress-rows", type=int, default=500000)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_info(path: Path) -> dict[str, object]:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    st = path.stat()
    return {
        "path": str(path.resolve()),
        "bytes": st.st_size,
        "mtime": st.st_mtime,
        "sha256": h.hexdigest(),
    }


def copy_inputs(source_dir: Path, out_dir: Path, overwrite: bool) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in COPY_NAMES:
        src = source_dir / name
        if not src.exists():
            continue
        dst = out_dir / name
        if dst.exists() and not overwrite:
            if name in {"boundary_vectors.csv", "boundary_signal_map.json", "boundary_vectors_manifest.json"}:
                raise SystemExit(f"refusing to overwrite existing input copy: {dst}; use --overwrite-input-copy")
            copied.append({"source": str(src.resolve()), "destination": str(dst.resolve()), "status": "already_exists"})
            continue
        shutil.copy2(src, dst)
        copied.append({"source": str(src.resolve()), "destination": str(dst.resolve()), "status": "copied"})
    return copied


def input_ports(boundary_map: Path) -> list[dict[str, object]]:
    data = json.loads(boundary_map.read_text(encoding="utf-8"))
    ports = [p for p in data["ports"] if p.get("direction") == "input" and p.get("name") != "clock"]
    return ports


def build_layout(ports: list[dict[str, object]], row_count: int | None = None) -> dict[str, object]:
    offset = 16
    layout_ports: list[dict[str, object]] = []
    for csv_col, p in enumerate(ports, start=4):
        name = str(p["name"])
        width = int(p["width"])
        if width <= 0:
            raise SystemExit(f"invalid width for {name}: {width}")
        if width <= 64:
            storage = "uint64"
            word_count = 1
            size = 8
        else:
            storage = "uint32_words_lsb_first"
            word_count = (width + 31) // 32
            size = 4 * word_count
        layout_ports.append({
            "name": name,
            "width": width,
            "csv_column": csv_col,
            "storage": storage,
            "word_count": word_count,
            "offset": offset,
        })
        offset += size
    return {
        "format": FORMAT,
        "version": VERSION,
        "endianness": ENDIANNESS,
        "row_semantics": ROW_SEMANTICS,
        "row_prefix": [
            {"name": "cycle", "type": "uint64", "offset": 0},
            {"name": "time_ps", "type": "int64", "offset": 8},
        ],
        "ports": layout_ports,
        "port_count": len(layout_ports),
        "row_bytes": offset,
        "row_count": row_count if row_count is not None else 0,
        "binary_header_bytes": HEADER_BYTES,
        "binary_magic_text": "TPP1B_BINVEC\\0\\0\\0\\0",
    }


def validate_header(csv_path: Path, layout: dict[str, object]) -> list[str]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        line = f.readline()
    if not line:
        raise SystemExit(f"empty CSV: {csv_path}")
    header = line.rstrip("\n").rstrip("\r").split(",")
    expected = ["cycle", "time_ps", "clock"] + [str(p["name"]) for p in layout["ports"]]
    if header != expected:
        first = None
        for i, (got, exp) in enumerate(zip(header, expected), start=1):
            if got != exp:
                first = {"column": i, "got": got, "expected": exp}
                break
        if first is None and len(header) != len(expected):
            first = {"got_columns": len(header), "expected_columns": len(expected)}
        raise SystemExit("CSV header does not match inputs-only boundary map order: " + json.dumps(first, sort_keys=True))
    return header


def parse_int_field(token: str, name: str, row_num: int) -> int:
    try:
        return int(token, 10)
    except ValueError as exc:
        raise ValueError(f"row {row_num} field {name}: invalid integer {token!r}") from exc


def parse_bits(token: str, width: int, port: str, row_num: int) -> int:
    if len(token) != width:
        raise ValueError(f"row {row_num} port {port}: width {len(token)} != {width}")
    bad = next((ch for ch in token if ch not in "01"), None)
    if bad is not None:
        raise ValueError(f"row {row_num} port {port}: non-2-state bit {bad!r}")
    return int(token, 2) if token else 0


def convert(csv_path: Path, bin_path: Path, layout_path: Path, manifest_path: Path, workload: str, copied: list[dict[str, object]], argv: list[str], progress_rows: int) -> None:
    map_path = csv_path.parent / "boundary_signal_map.json"
    ports = input_ports(map_path)
    layout = build_layout(ports)
    header = validate_header(csv_path, layout)
    row_bytes = int(layout["row_bytes"])
    port_layout = list(layout["ports"])
    bin_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    row_count = 0
    csv_hash = hashlib.sha256()
    error: dict[str, object] | None = None
    try:
        with csv_path.open("rb") as raw, bin_path.open("wb") as bout:
            header_line = raw.readline()
            csv_hash.update(header_line)
            bout.write(HEADER_STRUCT.pack(MAGIC, VERSION, HEADER_BYTES, 0, int(layout["port_count"]), row_bytes, 0))
            for row_num, raw_line in enumerate(raw, start=2):
                csv_hash.update(raw_line)
                line = raw_line.decode("ascii", errors="strict").rstrip("\n").rstrip("\r")
                fields = line.split(",")
                if len(fields) != len(header):
                    raise ValueError(f"row {row_num}: column count {len(fields)} != {len(header)}")
                row = bytearray(row_bytes)
                cycle = parse_int_field(fields[0], "cycle", row_num)
                time_ps = parse_int_field(fields[1], "time_ps", row_num)
                struct.pack_into("<Qq", row, 0, cycle, time_ps)
                for p in port_layout:
                    idx = int(p["csv_column"]) - 1
                    width = int(p["width"])
                    value = parse_bits(fields[idx], width, str(p["name"]), row_num)
                    off = int(p["offset"])
                    if str(p["storage"]) == "uint64":
                        struct.pack_into("<Q", row, off, value)
                    else:
                        for w in range(int(p["word_count"])):
                            struct.pack_into("<I", row, off + 4 * w, (value >> (32 * w)) & 0xFFFFFFFF)
                bout.write(row)
                row_count += 1
                if progress_rows > 0 and row_count % progress_rows == 0:
                    elapsed = time.time() - started
                    rate = row_count / elapsed if elapsed > 0 else 0.0
                    print(f"[convert-progress] workload={workload} rows={row_count} elapsed_sec={elapsed:.1f} rows_per_sec={rate:.1f}", flush=True)
            bout.seek(0)
            bout.write(HEADER_STRUCT.pack(MAGIC, VERSION, HEADER_BYTES, row_count, int(layout["port_count"]), row_bytes, 0))
    except Exception as exc:
        error = {"message": str(exc), "type": type(exc).__name__}
        manifest = {
            "status": "failed",
            "created_utc": utc_now(),
            "workload": workload,
            "csv": str(csv_path.resolve()),
            "boundary_map": str(map_path.resolve()),
            "binary": str(bin_path.resolve()),
            "layout": str(layout_path.resolve()),
            "error": error,
            "copied_inputs": copied,
            "command": argv,
        }
        write_json(manifest_path, manifest)
        raise
    layout["row_count"] = row_count
    write_json(layout_path, layout)
    elapsed = time.time() - started
    manifest = {
        "status": "ok",
        "created_utc": utc_now(),
        "workload": workload,
        "format": FORMAT,
        "version": VERSION,
        "row_count": row_count,
        "row_bytes": row_bytes,
        "elapsed_sec": elapsed,
        "rows_per_sec": row_count / elapsed if elapsed > 0 else None,
        "copied_inputs": copied,
        "command": argv,
        "files": {
            "boundary_vectors_csv": file_info(csv_path) | {"stream_sha256_during_conversion": csv_hash.hexdigest()},
            "boundary_signal_map_json": file_info(map_path),
            "boundary_vectors_bin": file_info(bin_path),
            "boundary_vectors_binary_layout_json": file_info(layout_path),
        },
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"status": "ok", "workload": workload, "row_count": row_count, "row_bytes": row_bytes, "binary": str(bin_path)}, indent=2), flush=True)


def main() -> None:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    out_dir = args.out_dir.resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"missing source dir: {source_dir}")
    copied: list[dict[str, object]] = []
    if args.copy_inputs:
        copied = copy_inputs(source_dir, out_dir, args.overwrite_input_copy)
    csv_path = out_dir / "boundary_vectors.csv"
    map_path = out_dir / "boundary_signal_map.json"
    for path in [csv_path, map_path]:
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"missing non-empty copied input: {path}")
    convert(
        csv_path=csv_path,
        bin_path=out_dir / "boundary_vectors.bin",
        layout_path=out_dir / "boundary_vectors_binary_layout.json",
        manifest_path=out_dir / "boundary_vectors_binary_manifest.json",
        workload=args.workload,
        copied=copied,
        argv=sys.argv,
        progress_rows=args.progress_rows,
    )


if __name__ == "__main__":
    main()
