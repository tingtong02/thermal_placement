#!/usr/bin/env python3
"""Shared helpers for Stage 1b Gemmini gate boundary replay."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Port:
    name: str
    direction: str
    width: int
    msb: int | None = None
    lsb: int | None = None


@dataclass(frozen=True)
class VcdSignal:
    code: str
    path: str
    name: str
    base_name: str
    width: int


def clean_vcd_name(name: str) -> str:
    return name.replace(" ", "")


def base_signal_name(name: str) -> str:
    return re.sub(r"\[[^\]]+\]$", "", name)


def parse_width(range_text: str | None) -> tuple[int, int | None, int | None]:
    if not range_text:
        return 1, None, None
    match = re.match(r"\[(\d+)\s*:\s*(\d+)\]", range_text.strip())
    if not match:
        return 1, None, None
    msb = int(match.group(1))
    lsb = int(match.group(2))
    return abs(msb - lsb) + 1, msb, lsb


def split_decl_names(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.split(","):
        token = raw.strip()
        if not token:
            continue
        token = re.sub(r"=.*$", "", token).strip()
        token = token.split()[-1]
        token = token.rstrip(";").strip()
        if token:
            names.append(token)
    return names


def extract_module_text(netlist: Path, module_name: str) -> str:
    text = netlist.read_text(encoding="utf-8", errors="ignore")
    start = text.find(f"module {module_name}(")
    if start < 0:
        start = text.find(f"module {module_name} (")
    if start < 0:
        raise RuntimeError(f"module {module_name} not found in {netlist}")
    end = text.find("endmodule", start)
    if end < 0:
        raise RuntimeError(f"endmodule for {module_name} not found in {netlist}")
    return text[start : end + len("endmodule")]


def parse_module_ports(netlist: Path, module_name: str = "Gemmini") -> list[Port]:
    module_text = extract_module_text(netlist, module_name)
    header_match = re.search(rf"module\s+{re.escape(module_name)}\s*\((.*?)\);", module_text, re.S)
    if not header_match:
        raise RuntimeError(f"module header for {module_name} not found")
    ordered_names = [name.strip() for name in header_match.group(1).replace("\n", " ").split(",") if name.strip()]

    decls: dict[str, Port] = {}
    for match in re.finditer(r"\b(input|output)\b\s*(?:wire|reg|logic)?\s*(\[[^\]]+\])?\s*([^;]+);", module_text):
        direction = match.group(1)
        width, msb, lsb = parse_width(match.group(2))
        for name in split_decl_names(match.group(3)):
            decls[name] = Port(name=name, direction=direction, width=width, msb=msb, lsb=lsb)

    ports: list[Port] = []
    missing: list[str] = []
    for name in ordered_names:
        port = decls.get(name)
        if port is None:
            missing.append(name)
        else:
            ports.append(port)
    if missing:
        raise RuntimeError(f"missing declarations for {len(missing)} {module_name} ports: {missing[:10]}")
    return ports


def parse_vcd_header(vcd: Path) -> tuple[dict[str, VcdSignal], int]:
    signals: dict[str, VcdSignal] = {}
    scopes: list[str] = []
    with vcd.open("rb") as f:
        while True:
            raw = f.readline()
            if not raw:
                raise RuntimeError(f"missing $enddefinitions in {vcd}")
            line = raw.decode("ascii", errors="ignore").strip()
            if not line:
                continue
            if line.startswith("$scope"):
                parts = line.split()
                if len(parts) >= 3:
                    scopes.append(clean_vcd_name(parts[2]))
            elif line.startswith("$upscope"):
                if scopes:
                    scopes.pop()
            elif line.startswith("$var"):
                parts = line.split()
                if len(parts) >= 6:
                    width = int(parts[2])
                    code = parts[3]
                    name = clean_vcd_name("".join(parts[4:-1]))
                    path = ".".join(scopes + [name])
                    existing = signals.get(code)
                    sig = VcdSignal(code=code, path=path, name=name, base_name=base_signal_name(name), width=width)
                    if existing is None or (".gemmini." in sig.path and ".gemmini." not in existing.path):
                        signals[code] = sig
            elif line.startswith("$enddefinitions"):
                return signals, f.tell()


def build_scope_index(signals: Iterable[VcdSignal], scope: str) -> dict[str, VcdSignal]:
    prefix = scope.rstrip(".") + "."
    index: dict[str, VcdSignal] = {}
    for sig in signals:
        if not sig.path.startswith(prefix):
            continue
        local = sig.path[len(prefix) :]
        if "." in local:
            continue
        key = base_signal_name(local)
        index[key] = sig
    return index


def map_ports_to_vcd(ports: list[Port], signals: dict[str, VcdSignal], scope: str) -> list[dict[str, object]]:
    scope_index = build_scope_index(signals.values(), scope)
    rows: list[dict[str, object]] = []
    for port in ports:
        sig = scope_index.get(port.name)
        rows.append(
            {
                "name": port.name,
                "direction": port.direction,
                "width": port.width,
                "msb": port.msb,
                "lsb": port.lsb,
                "rtl_vcd_path": sig.path if sig else None,
                "rtl_vcd_code": sig.code if sig else None,
                "rtl_vcd_width": sig.width if sig else None,
                "matched": sig is not None and sig.width == port.width,
            }
        )
    return rows


def parse_vcd_value(line: str) -> tuple[str, str] | None:
    if not line:
        return None
    c = line[0]
    if c in "01xXzZ":
        return line[1:], c.lower()
    if c in "bBrR":
        parts = line.split()
        if len(parts) != 2:
            return None
        return parts[1], parts[0][1:].lower()
    return None


def normalize_bits(value: str | None, width: int) -> str:
    if value is None:
        return "x" * width
    value = value.lower()
    if any(ch not in "01xz" for ch in value):
        value = "x"
    if len(value) < width:
        value = value.rjust(width, value[0] if value and value[0] in "xz" else "0")
    elif len(value) > width:
        value = value[-width:]
    return value


def bits_known(bits: str) -> bool:
    return not any(ch in bits for ch in "xzXZ")


def bits_to_hex(bits: str) -> str:
    clean = "".join("0" if ch in "xzXZ" else ch for ch in bits)
    if not clean:
        return "0"
    return format(int(clean, 2), f"0{(len(clean) + 3) // 4}x")


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
