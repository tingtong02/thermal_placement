#!/usr/bin/env python3
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "lef" / "gemmini_stage2_memory_macros.lef"

MACROS = [
    {
        "name": "mem_ext",
        "size": (116.0, 294.0),
        "ports": [
            ("RW0_addr", "INPUT", 12),
            ("RW0_en", "INPUT", 1),
            ("RW0_clk", "INPUT", 1),
            ("RW0_wmode", "INPUT", 1),
            ("RW0_wdata", "INPUT", 128),
            ("RW0_rdata", "OUTPUT", 128),
            ("RW0_wmask", "INPUT", 16),
        ],
    },
    {
        "name": "mem_0_ext",
        "size": (82.0, 208.0),
        "ports": [
            ("R0_addr", "INPUT", 9),
            ("R0_en", "INPUT", 1),
            ("R0_clk", "INPUT", 1),
            ("R0_data", "OUTPUT", 512),
            ("W0_addr", "INPUT", 9),
            ("W0_en", "INPUT", 1),
            ("W0_clk", "INPUT", 1),
            ("W0_data", "INPUT", 512),
            ("W0_mask", "INPUT", 64),
        ],
    },
    {
        "name": "mem_1_ext",
        "size": (116.0, 294.0),
        "ports": [
            ("RW0_addr", "INPUT", 13),
            ("RW0_en", "INPUT", 1),
            ("RW0_clk", "INPUT", 1),
            ("RW0_wmode", "INPUT", 1),
            ("RW0_wdata", "INPUT", 64),
            ("RW0_rdata", "OUTPUT", 64),
            ("RW0_wmask", "INPUT", 8),
        ],
    },
]

SIDES = ["left", "right", "top", "bottom"]
LAYER_BY_SIDE = {
    "left": "M4",
    "right": "M4",
    "top": "M5",
    "bottom": "M5",
}
PIN_THICKNESS = 0.096
MARGIN = 1.0
GRID = 0.004
TRACK_OFFSET = 0.012
TRACK_PITCH = 0.048


def expand_ports(port_specs):
    pins = []
    for base, direction, width in port_specs:
        if width == 1:
            pins.append((base, direction))
        else:
            for idx in range(width):
                pins.append((f"{base}[{idx}]", direction))
    return pins


def side_capacity(size):
    w, h = size
    usable_h = max(h - 2 * MARGIN, 1.0)
    usable_w = max(w - 2 * MARGIN, 1.0)
    cap_vert = max(int(usable_h / (PIN_THICKNESS * 2)), 1)
    cap_horz = max(int(usable_w / (PIN_THICKNESS * 2)), 1)
    return {
        "left": cap_vert,
        "right": cap_vert,
        "top": cap_horz,
        "bottom": cap_horz,
    }


def track_center(slot, total, length):
    centers = []
    pos = TRACK_OFFSET
    limit = length - TRACK_OFFSET
    min_pos = MARGIN
    max_pos = length - MARGIN
    while pos <= limit + 1e-9:
        if min_pos <= pos <= max_pos:
            centers.append(pos)
        pos += TRACK_PITCH
    if not centers:
        return length / 2
    if total <= 1:
        return centers[len(centers) // 2]
    if total > len(centers):
        raise RuntimeError(f"Not enough routing tracks for side length {length} and pin count {total}")
    step = (len(centers) - 1) / (total - 1)
    return centers[round(slot * step)]


def pin_rect(side, slot, total, size):
    w, h = size
    if side in ("left", "right"):
        center = track_center(slot, total, h)
        y0 = max(center - PIN_THICKNESS / 2, 0.0)
        y1 = min(center + PIN_THICKNESS / 2, h)
        if side == "left":
            return (0.0, y0, PIN_THICKNESS, y1)
        return (w - PIN_THICKNESS, y0, w, y1)
    center = track_center(slot, total, w)
    x0 = max(center - PIN_THICKNESS / 2, 0.0)
    x1 = min(center + PIN_THICKNESS / 2, w)
    if side == "bottom":
        return (x0, 0.0, x1, PIN_THICKNESS)
    return (x0, h - PIN_THICKNESS, x1, h)


def snap(value):
    return round(value / GRID) * GRID


def snap_rect(rect):
    x0, y0, x1, y1 = (snap(v) for v in rect)
    if x1 <= x0:
        x1 = x0 + GRID
    if y1 <= y0:
        y1 = y0 + GRID
    return (x0, y0, x1, y1)


def fmt_rect(rect):
    return "{:.3f} {:.3f} {:.3f} {:.3f}".format(*snap_rect(rect))


lines = [
    "VERSION 5.7 ;",
    'BUSBITCHARS "[]" ;',
    'DIVIDERCHAR "/" ;',
]

for macro in MACROS:
    size = macro["size"]
    pins = expand_ports(macro["ports"])
    capacities = side_capacity(size)
    placements = []
    side_idx = 0
    slot_on_side = {side: 0 for side in SIDES}
    remaining = capacities.copy()
    for name, direction in pins:
        start_idx = side_idx
        while remaining[SIDES[side_idx]] == 0:
            side_idx = (side_idx + 1) % len(SIDES)
            if side_idx == start_idx:
                raise RuntimeError(f"Not enough pin capacity for {macro['name']}")
        side = SIDES[side_idx]
        placements.append((name, direction, side, slot_on_side[side]))
        slot_on_side[side] += 1
        remaining[side] -= 1
        side_idx = (side_idx + 1) % len(SIDES)

    lines.extend([
        f"MACRO {macro['name']}",
        f"  FOREIGN {macro['name']} 0 0 ;",
        "  CLASS BLOCK ;",
        "  ORIGIN 0 0 ;",
        "  SYMMETRY X Y R90 ;",
        f"  SIZE {size[0]:.3f} BY {size[1]:.3f} ;",
        "  SITE asap7sc7p5t ;",
    ])
    totals = slot_on_side
    for name, direction, side, slot in placements:
        lines.extend([
            f"  PIN {name}",
            f"    DIRECTION {direction} ;",
            "    USE SIGNAL ;",
            "    SHAPE ABUTMENT ;",
            "    PORT",
            f"      LAYER {LAYER_BY_SIDE[side]} ;",
            f"      RECT {fmt_rect(pin_rect(side, slot, totals[side], size))} ;",
            "    END",
            f"  END {name}",
        ])
    lines.extend([
        f"END {macro['name']}",
        "",
    ])

lines.append("END LIBRARY")
OUT.write_text("\n".join(lines) + "\n")
print(OUT)
