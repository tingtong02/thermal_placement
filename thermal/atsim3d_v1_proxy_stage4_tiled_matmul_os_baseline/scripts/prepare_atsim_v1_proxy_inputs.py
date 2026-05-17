#!/usr/bin/env python3
"""Prepare ATSim3D v1 inputs from the Stage 4 proxy PACT inputs."""

from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "thermal" / "atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline"
INPUT_DIR = RUN_DIR / "inputs"
RESULTS_DIR = RUN_DIR / "results"
LOGS_DIR = RUN_DIR / "logs"

PACT_DIR = ROOT / "thermal" / "pact" / "stage4_tiled_matmul_os_baseline"
SOURCE_FLP = PACT_DIR / "flp_stage4_tiled_matmul_os_baseline.csv"
SOURCE_POWER = PACT_DIR / "ptrace_stage4_tiled_matmul_os_baseline_steady.csv"
SOURCE_CONFIG = PACT_DIR / "config_stage4_tiled_matmul_os_baseline.config"
SOURCE_METADATA = ROOT / "power" / "stage3_tiled_matmul_os_baseline_metadata.json"

DIE_SIDE_M = 0.003373864
SI_THICKNESS_M = 0.0001
SI_THERMAL_RESISTIVITY = 0.0077
SI_CONDUCTIVITY = 1.0 / SI_THERMAL_RESISTIVITY
AMBIENT_K = 318.15
INIT_K = 318.15
NOPACKAGE_HTC = 1e4
NOPACKAGE_THICKNESS_M = 1e-5
NOPACKAGE_CONDUCTIVITY = 400.0


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing or empty input: {path}")


def read_flp(path: Path) -> list[dict[str, str]]:
    require_file(path)
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = ["UnitName", "X", "Y", "Length (m)", "Width (m)", "ConfigFile", "Label"]
    if not rows:
        raise SystemExit(f"empty floorplan: {path}")
    missing = [key for key in required if key not in rows[0]]
    if missing:
        raise SystemExit(f"floorplan missing columns {missing}: {path}")
    return rows


def read_power(path: Path) -> dict[str, float]:
    require_file(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["UnitName", "Power"]:
            raise SystemExit(f"unexpected power header in {path}: {reader.fieldnames}")
        powers = {}
        for row in reader:
            name = row["UnitName"]
            power = float(row["Power"])
            if not math.isfinite(power) or power < 0:
                raise SystemExit(f"bad power for {name}: {power}")
            powers[name] = power
    if not powers:
        raise SystemExit(f"empty power file: {path}")
    return powers


def write_floorplan(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["UnitName", "X", "Y", "Length (m)", "Width (m)", "ConfigFile", "Label"])
        for row in rows:
            writer.writerow([
                row["UnitName"],
                row["X"],
                row["Y"],
                row["Length (m)"],
                row["Width (m)"],
                "",
                row.get("Label") or "Si",
            ])


def write_power(path: Path, unit_order: list[str], powers: dict[str, float]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["UnitName", "Power_dyn", "Power_leak"])
        for name in unit_order:
            writer.writerow([name, f"{powers[name]:.15g}", "0"])


def write_lcf(path: Path, floorplan: Path, power: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["Layer", "Main_compo", "Thickness (m)", "FloorplanFile", "PowerFile", "Clip_num_x", "Clip_num_y", "Clip_num_z"])
        writer.writerow([0, "Si", f"{SI_THICKNESS_M:.15g}", str(floorplan.resolve()), str(power.resolve()), 64, 64, 1])


def write_config(path: Path) -> None:
    path.write_text(
        f"""[Si]\nnon_linear = False\nconductivity (w/(m-k)) = {SI_CONDUCTIVITY:.15g}\nt_0 = 300 K\nalpha = 1.5\n\n[Temperature]\nambient = {AMBIENT_K:.2f} K\ninit = {INIT_K:.2f} K\n\n[NoPackage]\nhtc = {NOPACKAGE_HTC:.15g}\nthickness (m) = {NOPACKAGE_THICKNESS_M:.15g}\nconductivity (w/(m-k)) = {NOPACKAGE_CONDUCTIVITY:.15g}\nclip_num_x = 4\nclip_num_y = 4\nclip_num_z = 1\n\n[Leakage]\nt_base = 358.15 K\nbeta = 0.0 1/K""",
        encoding="utf-8",
    )


def write_simparams(path: Path) -> None:
    path.write_text(
        """[TSV]\ntsv_path = None\ntsv_shape = \n\n[Solver]\nnumber_of_core = 1\nprocesses = 1\niter_num = 1\n\n[Grid]\ngranularity = 1\nrows = 64\ncols = 64\ndepth = 1\ngrid_mode = max\n\n[NoPackage]\nlibrary_name = NoPackage_sec\nlibrary = Solid.py\n\n[NoPackage_sec]\nproperties = htc, thickness (m), conductivity (w/(m-k))\n\n[Si]\nlibrary_name = Solid\nlibrary = Solid.py\n\n[Solid]\nproperties = conductivity (w/(m-k)), non_linear\n""",
        encoding="utf-8",
    )


def main() -> int:
    for path in [SOURCE_FLP, SOURCE_POWER, SOURCE_CONFIG, SOURCE_METADATA]:
        require_file(path)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    flp_rows = read_flp(SOURCE_FLP)
    powers = read_power(SOURCE_POWER)
    unit_order = [row["UnitName"] for row in flp_rows]
    missing_power = [name for name in unit_order if name not in powers]
    extra_power = [name for name in powers if name not in set(unit_order)]
    if missing_power or extra_power:
        raise SystemExit(f"floorplan/power mismatch: missing={len(missing_power)} extra={len(extra_power)}")
    if len(unit_order) != 64 * 64:
        raise SystemExit(f"expected 4096 proxy grid units, got {len(unit_order)}")
    total_power = sum(powers.values())
    if total_power <= 0:
        raise SystemExit("proxy steady power total is not positive")

    floorplan = INPUT_DIR / "proxy_stage4_tiled_matmul_os_baseline_flp.csv"
    power = INPUT_DIR / "proxy_stage4_tiled_matmul_os_baseline_power.csv"
    lcf = INPUT_DIR / "proxy_stage4_tiled_matmul_os_baseline_lcf.csv"
    config = INPUT_DIR / "proxy_stage4_tiled_matmul_os_baseline.config"
    simparams = INPUT_DIR / "proxy_stage4_tiled_matmul_os_baseline_simparams.config"

    write_floorplan(floorplan, flp_rows)
    write_power(power, unit_order, powers)
    write_lcf(lcf, floorplan, power)
    write_config(config)
    write_simparams(simparams)

    shutil.copy2(SOURCE_CONFIG, INPUT_DIR / SOURCE_CONFIG.name)
    with SOURCE_METADATA.open(encoding="utf-8") as f:
        metadata = json.load(f)
    manifest = {
        "run_dir": str(RUN_DIR.relative_to(ROOT)),
        "source_floorplan": str(SOURCE_FLP.relative_to(ROOT)),
        "source_power": str(SOURCE_POWER.relative_to(ROOT)),
        "source_config": str(SOURCE_CONFIG.relative_to(ROOT)),
        "source_metadata": str(SOURCE_METADATA.relative_to(ROOT)),
        "generated_lcf": str(lcf.relative_to(ROOT)),
        "generated_floorplan": str(floorplan.relative_to(ROOT)),
        "generated_power": str(power.relative_to(ROOT)),
        "generated_config": str(config.relative_to(ROOT)),
        "generated_simparams": str(simparams.relative_to(ROOT)),
        "units": len(unit_order),
        "grid": 64,
        "die_side_m": DIE_SIDE_M,
        "cell_side_m": DIE_SIDE_M / 64,
        "si_thickness_m": SI_THICKNESS_M,
        "ambient_k": AMBIENT_K,
        "init_k": INIT_K,
        "si_conductivity_w_mk": SI_CONDUCTIVITY,
        "proxy_total_power_w": total_power,
        "stage3_proxy_total_power_w": metadata.get("proxy_total_power_w"),
        "peak_power_unit": max(powers, key=powers.get),
        "peak_unit_power_w": max(powers.values()),
        "notes": [
            "Power_dyn is copied from Stage 4 steady proxy Power; Power_leak is set to 0.",
            "This is a steady ATSim3D v1 rerun of old proxy data, not current signoff power.",
        ],
    }
    (INPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
