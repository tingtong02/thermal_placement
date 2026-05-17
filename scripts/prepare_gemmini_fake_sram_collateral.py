#!/usr/bin/env python3
"""Generate fake SRAM collateral from the active Gemmini RTL needs."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path


TECH = {
    "row_height": 0.270,
    "site_width": 0.054,
    "step": 0.024,
    "bit_cell_area_sp": 0.046,
    "bit_cell_area_dp": 0.090,
    "hw_ratio": 2.0,
    "additive_factor": 14,
    "pin_offset": 0.003,
    "site_name": "asap7sc7p5t",
}


@dataclass(frozen=True)
class Port:
    direction: str
    name: str
    width: int


@dataclass(frozen=True)
class Macro:
    cell: str
    wrapper: str
    depth: int
    data_width: int
    port_kind: str
    ports: tuple[Port, ...]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_filelist(filelist: Path) -> list[Path]:
    files: list[Path] = []
    for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith((".sv", ".v")):
            path = Path(line)
            if path.is_file():
                files.append(path)
    return files


def parse_modules(files: list[Path]) -> dict[str, tuple[Path, str]]:
    modules: dict[str, tuple[Path, str]] = {}
    mod_re = re.compile(r"(?ms)^module\s+([A-Za-z_][\w$]*)\s*\(.*?^endmodule")
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in mod_re.finditer(text):
            modules[match.group(1)] = (path, match.group(0))
    return modules


def instantiated_types(module_text: str) -> set[str]:
    inst_re = re.compile(r"^\s*([A-Za-z_][\w$]*)\s+(?:#\s*\([^;]*?\)\s*)?([A-Za-z_][\w$]*)\s*\(", re.M | re.S)
    skip = {"module", "if", "for", "while", "case", "assign", "always", "initial", "else", "end"}
    return {m.group(1) for m in inst_re.finditer(module_text) if m.group(1) not in skip}


def reachable_modules(modules: dict[str, tuple[Path, str]], top: str) -> set[str]:
    edges = {name: {typ for typ in instantiated_types(text) if typ in modules} for name, (_, text) in modules.items()}
    seen = {top}
    stack = [top]
    while stack:
        name = stack.pop()
        for child in sorted(edges.get(name, ())):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def parse_ports(module_text: str) -> tuple[Port, ...]:
    header = module_text.split(");", 1)[0]
    ports: list[Port] = []
    decl_re = re.compile(r"\b(input|output)\s+(?:wire\s+|reg\s+|logic\s+)?(?:\[(\d+):(\d+)\]\s+)?([A-Za-z_][\w$]*)")
    for match in decl_re.finditer(header):
        direction, msb, lsb, name = match.groups()
        width = abs(int(msb) - int(lsb)) + 1 if msb is not None else 1
        ports.append(Port(direction=direction, name=name, width=width))
    return tuple(ports)


def find_external_instance(wrapper_text: str) -> str | None:
    match = re.search(r"^\s*([A-Za-z_][\w$]*_ext)\s+[A-Za-z_][\w$]*\s*\(", wrapper_text, re.M)
    return match.group(1) if match else None


def derive_macro(cell: str, wrapper: str, ports: tuple[Port, ...]) -> Macro:
    port_by_name = {port.name: port for port in ports}
    addr_width = max((port.width for port in ports if port.name.endswith("_addr")), default=0)
    data_width = max((port.width for port in ports if port.name.endswith(("_wdata", "_rdata", "_data"))), default=0)
    if addr_width <= 0 or data_width <= 0:
        raise ValueError(f"cannot derive depth/data width for {cell} from ports {[p.name for p in ports]}")
    depth = 1 << addr_width
    if "RW0_wmode" in port_by_name:
        port_kind = "1rw"
    elif "R0_addr" in port_by_name and "W0_addr" in port_by_name:
        port_kind = "1r1w"
    else:
        port_kind = "generic"
    return Macro(cell=cell, wrapper=wrapper, depth=depth, data_width=data_width, port_kind=port_kind, ports=ports)


def upper_round(length: float, unit: float) -> float:
    return (int(length / unit) + 2) * unit


def macro_size(macro: Macro) -> tuple[float, float]:
    bits = macro.depth * macro.data_width
    bit_area = TECH["bit_cell_area_dp"] if macro.port_kind == "1r1w" else TECH["bit_cell_area_sp"]
    height = math.sqrt(bits * bit_area * TECH["hw_ratio"])
    min_pin_height = TECH["step"] * 2 * (sum(max(1, p.width) for p in macro.ports) + TECH["additive_factor"])
    height = max(height, min_pin_height)
    width = bits * bit_area / height

    def control_aspect(h: float, w: float) -> tuple[float, float]:
        while h / max(w, 1e-9) > 5.0:
            h /= 2.0
            w *= 2.0
        return h, w

    height, width = control_aspect(height, width)
    return upper_round(width, TECH["site_width"]), upper_round(height, TECH["row_height"])


def liberty_bus_type(port: Port) -> str:
    return f"{port.name}_bus_{port.width - 1}_to_0"


def write_liberty(macro: Macro, path: Path, area: float) -> None:
    lines = [
        f"library ({macro.cell}_asap7_fake) {{",
        "  technology (cmos);",
        '  delay_model : table_lookup;',
        '  capacitive_load_unit (1, ff);',
        '  voltage_unit : "1V";',
        '  current_unit : "1mA";',
        '  time_unit : "1ps";',
        '  pulling_resistance_unit : "1kohm";',
        "  input_threshold_pct_rise : 50;",
        "  input_threshold_pct_fall : 50;",
        "  output_threshold_pct_rise : 50;",
        "  output_threshold_pct_fall : 50;",
        "  slew_lower_threshold_pct_rise : 20;",
        "  slew_lower_threshold_pct_fall : 20;",
        "  slew_upper_threshold_pct_rise : 80;",
        "  slew_upper_threshold_pct_fall : 80;",
        "  nom_process : 1;",
        "  nom_temperature : 25;",
        "  nom_voltage : 0.700000;",
        "  voltage_map(VDD, 0.700000);",
        "  voltage_map(VSS, 0.000000);",
        '  operating_conditions("PVT_0P70V_25C") {',
        "    process : 1;",
        "    temperature : 25;",
        "    voltage : 0.700000;",
        "  }",
        "  default_operating_conditions : PVT_0P70V_25C;",
    ]
    for port in macro.ports:
        if port.width > 1:
            lines += [
                f"  type ({liberty_bus_type(port)}) {{",
                "    base_type : array;",
                "    data_type : bit;",
                f"    bit_width : {port.width};",
                f"    bit_from : {port.width - 1};",
                "    bit_to : 0;",
                "    downto : true;",
                "  }",
            ]
    lines += [
        f"  cell ({macro.cell}) {{",
        "    dont_use : true;",
        "    dont_touch : true;",
        "    is_macro_cell : true;",
        f"    area : {area:.6f};",
        "    pg_pin (VDD) {",
        "      pg_type : primary_power;",
        "      voltage_name : VDD;",
        "    }",
        "    pg_pin (VSS) {",
        "      pg_type : primary_ground;",
        "      voltage_name : VSS;",
        "    }",
    ]
    for port in macro.ports:
        direction = "output" if port.direction == "output" else "input"
        if port.width > 1:
            lines += [
                f"    bus ({port.name}) {{",
                f"      bus_type : {liberty_bus_type(port)};",
                f"      direction : {direction};",
                "      capacitance : 2.0;",
                "      related_power_pin : VDD;",
                "      related_ground_pin : VSS;",
                "    }",
            ]
        else:
            clock = "      clock : true;" if port.name.endswith("_clk") else None
            lines += [
                f"    pin ({port.name}) {{",
                f"      direction : {direction};",
            ]
            if clock:
                lines.append(clock)
            lines += [
                "      capacitance : 2.0;",
                "      related_power_pin : VDD;",
                "      related_ground_pin : VSS;",
                "    }",
            ]
    lines += ["  }", "}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def lef_pin_names(port: Port) -> list[str]:
    if port.width == 1:
        return [port.name]
    return [f"{port.name}[{idx}]" for idx in range(port.width)]


def write_lef(macro: Macro, path: Path, width_um: float, height_um: float) -> None:
    pin_entries = [(name, port.direction.upper()) for port in macro.ports for name in lef_pin_names(port)]
    pitch = max(TECH["step"] * 2, height_um / max(len(pin_entries) + 8, 1))
    y = TECH["pin_offset"]
    lines = [
        "VERSION 5.6 ;",
        'BUSBITCHARS "[]" ;',
        'DIVIDERCHAR "/" ;',
        f"MACRO {macro.cell}",
        "  CLASS BLOCK ;",
        "  ORIGIN 0 0 ;",
        f"  FOREIGN {macro.cell} 0 0 ;",
        f"  SIZE {width_um:.3f} BY {height_um:.3f} ;",
        "  SYMMETRY X Y ;",
        f"  SITE {TECH['site_name']} ;",
    ]
    for pg_name, use in (("VDD", "POWER"), ("VSS", "GROUND")):
        lines += [
            f"  PIN {pg_name}",
            "    DIRECTION INOUT ;",
            f"    USE {use} ;",
            "    PORT",
            "      LAYER M4 ;",
            f"        RECT 0.000 {max(y, 0.003):.3f} {width_um:.3f} {max(y + TECH['step'], 0.006):.3f} ;",
            "    END",
            f"  END {pg_name}",
        ]
        y += pitch
    for pin, direction in pin_entries:
        lines += [
            f"  PIN {pin}",
            f"    DIRECTION {direction} ;",
            "    USE SIGNAL ;",
            "    PORT",
            "      LAYER M4 ;",
            f"        RECT 0.000 {y:.3f} {min(width_um, 4.000):.3f} {min(y + TECH['step'], height_um - 0.003):.3f} ;",
            "    END",
            f"  END {pin}",
        ]
        y += pitch
    lines += [
        "  OBS",
        "    LAYER M1 ;",
        f"      RECT 4.000 0.000 {width_um:.3f} {height_um:.3f} ;",
        "    LAYER M2 ;",
        f"      RECT 4.000 0.000 {width_um:.3f} {height_um:.3f} ;",
        "    LAYER M3 ;",
        f"      RECT 4.000 0.000 {width_um:.3f} {height_um:.3f} ;",
        "  END",
        f"END {macro.cell}",
        "END LIBRARY",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_verilog_stub(macro: Macro, path: Path) -> None:
    port_names = ", ".join(port.name for port in macro.ports)
    lines = [f"(* black_box *) module {macro.cell}({port_names});"]
    for port in macro.ports:
        width = f"[{port.width - 1}:0] " if port.width > 1 else ""
        lines.append(f"  {port.direction} {width}{port.name};")
    lines += ["endmodule", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def generate(filelist: Path, top: str, out_root: Path, design: str) -> dict[str, object]:
    files = read_filelist(filelist)
    modules = parse_modules(files)
    if top not in modules:
        raise ValueError(f"top module {top} not found in {filelist}")
    reachable = reachable_modules(modules, top)

    macros: list[Macro] = []
    for wrapper in sorted(reachable):
        _, text = modules[wrapper]
        ext = find_external_instance(text)
        if not ext or not ext.startswith("mem"):
            continue
        macros.append(derive_macro(ext, wrapper, parse_ports(text)))
    if not macros:
        raise ValueError(f"no reachable Gemmini memory extern modules found from top {top}")

    design_root = out_root / design
    for sub in ("lef", "lib", "verilog", "reports"):
        (design_root / sub).mkdir(parents=True, exist_ok=True)

    manifest = {"top": top, "filelist": str(filelist), "design": design, "macros": []}
    for macro in macros:
        width_um, height_um = macro_size(macro)
        area = width_um * height_um
        write_liberty(macro, design_root / "lib" / f"{macro.cell}.lib", area)
        write_lef(macro, design_root / "lef" / f"{macro.cell}.lef", width_um, height_um)
        write_verilog_stub(macro, design_root / "verilog" / f"{macro.cell}.sv")
        manifest["macros"].append(
            {
                "cell": macro.cell,
                "wrapper": macro.wrapper,
                "depth": macro.depth,
                "data_width": macro.data_width,
                "port_kind": macro.port_kind,
                "width_um": round(width_um, 3),
                "height_um": round(height_um, 3),
                "area_um2": round(area, 6),
                "ports": [port.__dict__ for port in macro.ports],
            }
        )
    (design_root / "reports" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    default_run = repo_root() / "runs" / "GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filelist", type=Path, default=default_run / "rtl/generated/chipyard.harness.TestHarness.GemminiRocketConfig.top.f")
    parser.add_argument("--top", default=os.environ.get("STAGE2_TOP_MODULE", "Gemmini"))
    parser.add_argument("--design", default=os.environ.get("FAKE_SRAM_DESIGN", "Gemmini"))
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=Path(os.environ.get("FAKE_SRAM_CADENCE_CACHE", repo_root() / ".cache" / "fake_sram" / "asap7")),
    )
    args = parser.parse_args()

    try:
        manifest = generate(args.filelist.resolve(), args.top, args.cache_root.resolve(), args.design)
    except (OSError, ValueError) as exc:
        print(str(exc))
        return 1
    print(
        f"Gemmini fake SRAM collateral ready: design={args.design} "
        f"macros={len(manifest['macros'])} cache={args.cache_root.resolve() / args.design}"
    )
    for macro in manifest["macros"]:
        print(
            f"  {macro['cell']}: wrapper={macro['wrapper']} "
            f"depth={macro['depth']} width={macro['data_width']} kind={macro['port_kind']} "
            f"size={macro['width_um']}x{macro['height_um']}um"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
