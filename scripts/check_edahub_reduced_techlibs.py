#!/usr/bin/env python3
"""Validate reduced edahub technology libraries adapted by the main repo."""

from __future__ import annotations

import argparse
from pathlib import Path


REDUCED_TECHLIBS = {
    "asap7": {
        "db": [
            "third_party/edahub/edahub/technology/asap7/db/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.db",
            "third_party/edahub/edahub/technology/asap7/db/asap7sc7p5t_SEQ_RVT_TT_nldm_201020.db",
            "third_party/edahub/edahub/technology/asap7/db/asap7sc7p5t_AO_RVT_TT_nldm_201020.db",
            "third_party/edahub/edahub/technology/asap7/db/asap7sc7p5t_OA_RVT_TT_nldm_201020.db",
            "third_party/edahub/edahub/technology/asap7/db/asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.db",
        ],
        "lib": [
            "third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.lib",
            "third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_SEQ_RVT_TT_nldm_201020.lib",
            "third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_AO_RVT_TT_nldm_201020.lib",
            "third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_OA_RVT_TT_nldm_201020.lib",
            "third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.lib",
        ],
        "lef": [
            "third_party/edahub/edahub/technology/asap7/lef/asap7_tech_4x_201209.lef",
            "third_party/edahub/edahub/technology/asap7/lef/asap7sc7p5t_27_R_4x_201211.lef",
        ],
        "aux": [
            "third_party/edahub/edahub/technology/asap7/qrc/qrcTechFile_typ03_scaled4xV06",
            "configs/reduced_techlibs/asap7.mk",
            "configs/reduced_techlibs/asap7.tcl",
            "configs/openroad/reduced_platforms/asap7/config.mk",
            "configs/openroad/reduced_platforms/asap7/setRC.tcl",
        ],
    },
    "nangate45": {
        "db": [
            "third_party/edahub/edahub/technology/nangate45/db/NangateOpenCellLibrary.db",
        ],
        "lib": [
            "third_party/edahub/edahub/technology/nangate45/lib/Nangate45_typ.lib",
            "third_party/edahub/edahub/technology/nangate45/lib/Nangate45_slow.lib",
            "third_party/edahub/edahub/technology/nangate45/lib/Nangate45_fast.lib",
        ],
        "lef": [
            "third_party/edahub/edahub/technology/nangate45/lef/Nangate45_tech.lef",
            "third_party/edahub/edahub/technology/nangate45/lef/Nangate45_stdcell.lef",
        ],
        "aux": [
            "configs/reduced_techlibs/nangate45.mk",
            "configs/reduced_techlibs/nangate45.tcl",
            "configs/openroad/reduced_platforms/nangate45/config.mk",
            "configs/openroad/reduced_platforms/nangate45/setRC.tcl",
        ],
    },
    "sky130hd": {
        "db": [
            "third_party/edahub/edahub/technology/sky130hd/db/sky130_fd_sc_hd__tt_025C_1v80.db",
        ],
        "lib": [
            "third_party/edahub/edahub/technology/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib",
            "third_party/edahub/edahub/technology/sky130hd/lib/sky130_fd_sc_hd__ff_n40C_1v95.lib",
            "third_party/edahub/edahub/technology/sky130hd/lib/sky130_fd_sc_hd__ss_n40C_1v40.lib",
        ],
        "lef": [
            "third_party/edahub/edahub/technology/sky130hd/lef/sky130hd.tlef",
            "third_party/edahub/edahub/technology/sky130hd/lef/sky130_fd_sc_hd_merged.lef",
        ],
        "aux": [
            "configs/reduced_techlibs/sky130hd.mk",
            "configs/reduced_techlibs/sky130hd.tcl",
            "configs/openroad/reduced_platforms/sky130hd/config.mk",
            "configs/openroad/reduced_platforms/sky130hd/setRC.tcl",
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "techlib",
        nargs="?",
        default="all",
        choices=["all", *REDUCED_TECHLIBS.keys()],
        help="Reduced technology library to validate.",
    )
    return parser.parse_args()


def validate(root: Path, techlib: str) -> list[Path]:
    missing: list[Path] = []
    data = REDUCED_TECHLIBS[techlib]
    for paths in data.values():
        for rel_path in paths:
            path = root / rel_path
            if not path.exists():
                missing.append(path)
    return missing


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    names = REDUCED_TECHLIBS.keys() if args.techlib == "all" else [args.techlib]

    all_missing: dict[str, list[Path]] = {}
    for name in names:
        missing = validate(root, name)
        if missing:
            all_missing[name] = missing
            continue

        data = REDUCED_TECHLIBS[name]
        print(
            f"{name}: ok "
            f"({len(data['lib'])} Liberty, {len(data['db'])} DB, {len(data['lef'])} LEF)"
        )

    if all_missing:
        for name, paths in all_missing.items():
            print(f"{name}: missing {len(paths)} required file(s)")
            for path in paths:
                print(f"  {path}")
        return 1

    print("Note: these are reduced technology libraries, not complete PDKs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
