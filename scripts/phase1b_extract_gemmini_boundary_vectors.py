#!/usr/bin/env python3
"""Extract Gemmini boundary vectors from a Stage 1 full-SoC RTL VCD."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from phase1b_gate_replay_common import (
    bits_known,
    map_ports_to_vcd,
    normalize_bits,
    parse_module_ports,
    parse_vcd_header,
    parse_vcd_value,
    write_csv,
    write_json,
)

DEFAULT_SCOPE = "TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rtl-vcd", required=True, type=Path)
    parser.add_argument("--gate-netlist", required=True, type=Path)
    parser.add_argument("--rtl-gemmini-scope", default=DEFAULT_SCOPE)
    parser.add_argument("--workload", default="mvin_mvout")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--start-ps", type=int, default=0)
    parser.add_argument("--end-ps", type=int, default=None)
    parser.add_argument("--max-cycles", type=int, default=None)
    parser.add_argument("--module", default="Gemmini")
    parser.add_argument("--vectors-inputs-only", action="store_true", help="write only clock/reset/input ports to boundary_vectors.csv; still emit full boundary_signal_map")
    return parser.parse_args()


def extract_vectors(args: argparse.Namespace) -> dict[str, object]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ports = parse_module_ports(args.gate_netlist, args.module)
    signals, body_offset = parse_vcd_header(args.rtl_vcd)
    mapping = map_ports_to_vcd(ports, signals, args.rtl_gemmini_scope)
    write_json(
        args.out_dir / "boundary_signal_map.json",
        {
            "module": args.module,
            "rtl_vcd": str(args.rtl_vcd),
            "gate_netlist": str(args.gate_netlist),
            "rtl_gemmini_scope": args.rtl_gemmini_scope,
            "ports": mapping,
        },
    )
    write_csv(
        args.out_dir / "boundary_signal_map.csv",
        mapping,
        ["name", "direction", "width", "msb", "lsb", "rtl_vcd_path", "rtl_vcd_code", "rtl_vcd_width", "matched"],
    )

    unmatched = [row for row in mapping if not row["matched"]]
    if unmatched:
        raise RuntimeError(f"unmatched or width-mismatched boundary ports: {len(unmatched)}; see boundary_signal_map.json")

    by_code = {str(row["rtl_vcd_code"]): row for row in mapping}
    clock_row = next(row for row in mapping if row["name"] == "clock")
    clock_code = str(clock_row["rtl_vcd_code"])
    current_values: dict[str, str] = {str(row["name"]): "x" * int(row["width"]) for row in mapping}
    raw_values_by_code: dict[str, str | None] = {code: None for code in by_code}

    if args.vectors_inputs_only:
        vector_ports = [row for row in mapping if row["direction"] == "input"]
    else:
        vector_ports = mapping
    port_names = [str(row["name"]) for row in vector_ports]
    fieldnames = ["cycle", "time_ps"] + port_names
    vector_path = args.out_dir / "boundary_vectors.csv"
    cycle_count = 0
    skipped_before_start = 0
    last_time = 0
    last_clock = "x"
    unknown_counts = defaultdict(int)

    with args.rtl_vcd.open("rb") as f, vector_path.open("w", newline="", encoding="utf-8") as out:
        f.seek(body_offset)
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        while True:
            raw = f.readline()
            if not raw:
                break
            line = raw.decode("ascii", errors="ignore").strip()
            if not line:
                continue
            if line.startswith("#"):
                try:
                    last_time = int(line[1:])
                except ValueError:
                    pass
                if args.end_ps is not None and last_time > args.end_ps:
                    break
                continue
            parsed = parse_vcd_value(line)
            if parsed is None:
                continue
            code, value = parsed
            row = by_code.get(code)
            if row is None:
                continue
            raw_values_by_code[code] = value
            port_name = str(row["name"])
            width = int(row["width"])
            current_values[port_name] = normalize_bits(value, width)

            if code != clock_code:
                continue
            new_clock = normalize_bits(value, 1)
            is_posedge = last_clock == "0" and new_clock == "1"
            last_clock = new_clock
            if not is_posedge:
                continue
            if last_time < args.start_ps:
                skipped_before_start += 1
                continue
            out_row = {"cycle": cycle_count, "time_ps": last_time}
            for port in vector_ports:
                name = str(port["name"])
                bits = current_values[name]
                if not bits_known(bits):
                    unknown_counts[name] += 1
                out_row[name] = bits
            writer.writerow(out_row)
            cycle_count += 1
            if args.max_cycles is not None and cycle_count >= args.max_cycles:
                break

    manifest = {
        "workload": args.workload,
        "rtl_vcd": str(args.rtl_vcd),
        "gate_netlist": str(args.gate_netlist),
        "rtl_gemmini_scope": args.rtl_gemmini_scope,
        "vector_file": str(vector_path),
        "start_ps": args.start_ps,
        "end_ps": args.end_ps,
        "max_cycles": args.max_cycles,
        "sample": "posedge clock after VCD timestamp updates",
        "cycles_written": cycle_count,
        "skipped_posedges_before_start": skipped_before_start,
        "last_time_ps_seen": last_time,
        "ports": len(mapping),
        "input_ports": sum(1 for row in mapping if row["direction"] == "input"),
        "output_ports": sum(1 for row in mapping if row["direction"] == "output"),
        "vector_ports": len(vector_ports),
        "vectors_inputs_only": bool(args.vectors_inputs_only),
        "unknown_counts_by_port": dict(sorted(unknown_counts.items())),
    }
    write_json(args.out_dir / "boundary_vectors_manifest.json", manifest)

    report = args.out_dir / "phase1b_extract_report.md"
    report.write_text(
        "# Phase1b Boundary Vector Extraction\n\n"
        f"- workload: `{args.workload}`\n"
        f"- RTL VCD: `{args.rtl_vcd}`\n"
        f"- gate netlist: `{args.gate_netlist}`\n"
        f"- RTL scope: `{args.rtl_gemmini_scope}`\n"
        f"- cycles written: `{cycle_count}`\n"
        f"- output: `{vector_path}`\n"
        f"- vectors inputs only: `{bool(args.vectors_inputs_only)}`\n"
        f"- vector ports: `{len(vector_ports)}`\n"
        f"- unmatched ports: `0`\n"
        f"- unknown-bearing ports: `{len(unknown_counts)}`\n\n"
        "Sampling note: vectors are sampled on RTL VCD clock posedges after processing timestamp updates. "
        "The formal SAIF replay harness applies the previous sampled input vector before the next rising edge. "
        "The historical compare harness also compares against the current sampled output vector when output columns are present.\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    args = parse_args()
    manifest = extract_vectors(args)
    print(json.dumps({"cycles_written": manifest["cycles_written"], "vector_file": manifest["vector_file"]}, indent=2))


if __name__ == "__main__":
    main()
