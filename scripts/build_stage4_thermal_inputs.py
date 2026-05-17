#!/usr/bin/env python3
"""Generate Phase 4 PACT and HotSpot inputs from Stage 3 proxy power grids."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from pathlib import Path

BASE = "stage4_tiled_matmul_os_baseline"
STAGE3 = "stage3_tiled_matmul_os_baseline"
DIE_SIDE_M = 0.003373864
SI_THICKNESS_M = 0.0001

COARSE_BLOCKS = [
    "pe_array",
    "controller_execute",
    "load_store_datapath",
    "scratchpad_accumulator_context",
    "other_context",
]

REGION_TO_BLOCK = {
    "pe_array": "pe_array",
    "controller": "controller_execute",
    "clock_tree": "controller_execute",
    "load_store_dma": "load_store_datapath",
    "scratchpad": "scratchpad_accumulator_context",
    "gemmini_other": "other_context",
    "unmapped_standard_cell": "other_context",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--power-dir", type=Path, default=Path("power"))
    parser.add_argument("--pact-dir", type=Path, default=Path("thermal/pact") / BASE)
    parser.add_argument("--hotspot-dir", type=Path, default=Path("thermal/hotspot") / BASE)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts/stage4"))
    parser.add_argument("--die-side-m", type=float, default=DIE_SIDE_M)
    parser.add_argument("--si-thickness-m", type=float, default=SI_THICKNESS_M)
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing or empty required input: {path}")


def read_metadata(path: Path) -> dict:
    require_file(path)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_transient_ptrace(path: Path) -> tuple[list[str], list[int], list[list[float]]]:
    require_file(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if not header or header[0] != "time_ps":
            raise SystemExit(f"unexpected transient ptrace header in {path}")
        unit_names = header[1:]
        time_ps: list[int] = []
        rows: list[list[float]] = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise SystemExit(f"bad row length in {path}: got {len(row)}, expected {len(header)}")
            t = int(float(row[0]))
            vals = [float(x) for x in row[1:]]
            if any((not math.isfinite(v)) or v < 0 for v in vals):
                raise SystemExit(f"non-finite or negative power in {path} at time {t}")
            time_ps.append(t)
            rows.append(vals)
    if not rows:
        raise SystemExit(f"no transient rows in {path}")
    return unit_names, time_ps, rows


def read_region_summary(path: Path) -> dict[str, float]:
    require_file(path)
    powers = {block: 0.0 for block in COARSE_BLOCKS}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["region"]
            power = float(row["proxy_power_w"])
            block = REGION_TO_BLOCK.get(region)
            if block is None:
                raise SystemExit(f"unmapped Stage 3 region for HotSpot block aggregation: {region}")
            powers[block] += power
    total = sum(powers.values())
    if total <= 0:
        raise SystemExit(f"non-positive region power total in {path}")
    return powers


def infer_grid(unit_names: list[str], metadata: dict) -> int:
    grid = int(metadata.get("grid", 0))
    if grid <= 0:
        raise SystemExit("metadata missing positive grid size")
    expected = [f"g{x}_{y}" for y in range(grid) for x in range(grid)]
    if unit_names != expected:
        raise SystemExit("Stage 3 transient ptrace unit order does not match expected gX_Y row-major grid")
    return grid


def median_step_us(time_ps: list[int]) -> tuple[float, float]:
    if len(time_ps) < 2:
        return 1.0, 1e-6
    deltas = [b - a for a, b in zip(time_ps, time_ps[1:])]
    if any(d <= 0 for d in deltas):
        raise SystemExit("transient time_ps values must be strictly increasing")
    deltas_sorted = sorted(deltas)
    mid = len(deltas_sorted) // 2
    if len(deltas_sorted) % 2:
        delta_ps = float(deltas_sorted[mid])
    else:
        delta_ps = (deltas_sorted[mid - 1] + deltas_sorted[mid]) / 2.0
    return delta_ps * 1e-6, delta_ps * 1e-12


def write_pact_floorplan(path: Path, grid: int, die_side_m: float) -> None:
    cell = die_side_m / grid
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["UnitName", "X", "Y", "Length (m)", "Width (m)", "ConfigFile", "Label"])
        for y in range(grid):
            for x in range(grid):
                writer.writerow([
                    f"g{x}_{y}",
                    f"{x * cell:.15g}",
                    f"{y * cell:.15g}",
                    f"{cell:.15g}",
                    f"{cell:.15g}",
                    "",
                    "Si",
                ])


def write_pact_ptraces(steady_path: Path, transient_path: Path, unit_names: list[str], rows: list[list[float]]) -> tuple[int, float]:
    totals = [sum(row) for row in rows]
    peak_idx = max(range(len(totals)), key=lambda idx: totals[idx])
    peak_row = rows[peak_idx]
    with steady_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["UnitName", "Power"])
        for name, power in zip(unit_names, peak_row):
            writer.writerow([name, f"{power:.15g}"])
    with transient_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["UnitName", "Power", *[f"Power{i}" for i in range(1, len(rows))]])
        for col, name in enumerate(unit_names):
            writer.writerow([name, *[f"{rows[row][col]:.15g}" for row in range(len(rows))]])
    return peak_idx, totals[peak_idx]


def write_pact_config(path: Path) -> None:
    path.write_text(
        """[DEFAULT]\nlabel = \n\n[Si]\nthermalresistivity ((m-k)/w) = 0.0077\nspecificheatcapacity (j/m^3k) = 1750000\n\n[Init]\nambient = 318.15 K\ntemperature = 318.15 K\n\n[NoPackage]\nhtc = 1e4\nthickness (m) = 0.00001\nthermalresistivity ((m-k)/w) = 0.0025\nspecificheatcapacity (j/m^3k) = 1750000\n""",
        encoding="utf-8",
    )


def write_model_params(path: Path, solver: str, grid: int, step_us: float, num_steps: int) -> None:
    is_superlu = solver == "SuperLU"
    total_us = max(step_us * max(num_steps - 1, 1), step_us)
    steady_state = "True" if is_superlu else "False"
    transient = "False" if is_superlu else "True"
    wrapper = "SuperLU_steady.py" if is_superlu else "SPICE_transient.py"
    text = f"""[DEFAULT]\nlabel = \n\n[Path]\nhome = ./../\nlibrary = %(home)slib/\nflp = %(home)sflp_files/\nptrace = %(home)sptrace_files/\n\n[Simulation]\nsteady_state = {steady_state}\nsteady_state_solver = Solver\ntransient = {transient}\nstep_size = {step_us:.9g}us\ntotal_simualation_time = {total_us:.9g}us\ntotal_simulation_time = {total_us:.9g}us\nptrace_step_size = {step_us:.9g}us\ntemperature_dependent = False\nconvergence = 0.1\nlayer = 1\ntemperature_dependent_library = TemperatureDependent.py\nnumber_of_core = 1\ninit_file = False\n\n[Solver]\nname = {solver}\nwrapper = {wrapper}\nll_steady_solver = KLU\nll_transient_solver = TRAP\n\n[Grid]\ngrid_mode = max\ntype = Uniform\ngranularity = Grid\nrows = {grid}\ncols = {grid}\n\n[VirtualNodes]\ncenter_center = 0.5\nbottom_center = 1\n\n[NoPackage]\nLateralHeatFlow = True\nVerticalHeatFlow = False\nlibrary_name = NoPackage_sec\nlibrary = Solid.py\nvirtual_node = bottom_center\ntransient = False\nmode = single\n\n[NoPackage_sec]\nproperties = htc, thickness (m), thermalresistivity ((m-k)/w), specificheatcapacity (j/m^3k)\n\n[Si]\nlibrary_name = Solid\nlibrary = Solid.py\ntransient = True\nvirtual_node = bottom_center\nmode = single\n\n[Solid]\nproperties = thermalresistivity ((m-k)/w), specificheatcapacity (j/m^3k)\n"""
    path.write_text(text, encoding="utf-8")


def write_lcf(path: Path, flp: Path, ptrace: Path, thickness_m: float) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Layer", "FloorplanFile", "Thickness (m)", "PtraceFile", "LateralHeatFlow"])
        writer.writerow([0, str(flp.resolve()), f"{thickness_m:.15g}", str(ptrace.resolve()), "True"])


def hot_spot_blocks(die_side_m: float) -> dict[str, tuple[float, float, float, float]]:
    s = die_side_m
    left_w = 0.20 * s
    right_w = 0.20 * s
    center_w = s - left_w - right_w
    bottom_h = 0.20 * s
    top_h = 0.20 * s
    middle_h = s - bottom_h - top_h
    return {
        "load_store_datapath": (left_w, s, 0.0, 0.0),
        "scratchpad_accumulator_context": (right_w, s, left_w + center_w, 0.0),
        "other_context": (center_w, bottom_h, left_w, 0.0),
        "pe_array": (center_w, middle_h, left_w, bottom_h),
        "controller_execute": (center_w, top_h, left_w, bottom_h + middle_h),
    }


def write_hotspot_inputs(hotspot_dir: Path, powers: dict[str, float], total_by_time: list[float], sample_s: float, die_side_m: float) -> dict[str, Path]:
    hotspot_dir.mkdir(parents=True, exist_ok=True)
    flp = hotspot_dir / f"{BASE}.flp"
    ptrace = hotspot_dir / f"{BASE}.ptrace"
    config = hotspot_dir / f"{BASE}.config"
    blocks = hot_spot_blocks(die_side_m)
    with flp.open("w", encoding="utf-8") as f:
        f.write("# Phase 4 coarse HotSpot floorplan. Dimensions are meters.\n")
        for name in COARSE_BLOCKS:
            width, height, left_x, bottom_y = blocks[name]
            f.write(f"{name}\t{width:.15g}\t{height:.15g}\t{left_x:.15g}\t{bottom_y:.15g}\n")
    total_region_power = sum(powers.values())
    shares = {name: powers[name] / total_region_power for name in COARSE_BLOCKS}
    with ptrace.open("w", encoding="utf-8") as f:
        f.write("\t".join(COARSE_BLOCKS) + "\n")
        for total in total_by_time:
            f.write("\t".join(f"{total * shares[name]:.15g}" for name in COARSE_BLOCKS) + "\n")
    template = Path("third_party/HotSpot/template.config")
    require_file(template)
    text = template.read_text(encoding="utf-8")
    text = text.replace("\t\t-sampling_intvl\t\t0.01", f"\t\t-sampling_intvl\t\t{sample_s:.15g}")
    text = text.replace("\t\t-model_type\t\t\tblock", "\t\t-model_type\t\t\tblock")
    config.write_text(text, encoding="utf-8")
    return {"flp": flp, "ptrace": ptrace, "config": config}


def write_manifest(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    metadata_path = args.power_dir / f"{STAGE3}_metadata.json"
    transient_path = args.power_dir / f"{STAGE3}_transient_ptrace.csv"
    region_path = args.power_dir / f"{STAGE3}_region_power_summary.csv"
    grid_power_path = args.power_dir / f"{STAGE3}_grid_power.csv"
    require_file(grid_power_path)
    metadata = read_metadata(metadata_path)
    unit_names, time_ps, rows = read_transient_ptrace(transient_path)
    powers = read_region_summary(region_path)
    grid = infer_grid(unit_names, metadata)
    if len(unit_names) != grid * grid:
        raise SystemExit(f"grid/unit mismatch: {len(unit_names)} units for {grid}x{grid}")
    step_us, sample_s = median_step_us(time_ps)
    total_by_time = [sum(row) for row in rows]
    if max(total_by_time) <= 0:
        raise SystemExit("all transient total powers are zero")

    args.pact_dir.mkdir(parents=True, exist_ok=True)
    args.hotspot_dir.mkdir(parents=True, exist_ok=True)
    args.artifacts_dir.mkdir(parents=True, exist_ok=True)

    pact_flp = args.pact_dir / f"flp_{BASE}.csv"
    pact_steady_ptrace = args.pact_dir / f"ptrace_{BASE}_steady.csv"
    pact_transient_ptrace = args.pact_dir / f"ptrace_{BASE}_transient.csv"
    pact_config = args.pact_dir / f"config_{BASE}.config"
    model_steady = args.pact_dir / f"modelParams_{BASE}_steady_superlu.config"
    model_transient = args.pact_dir / f"modelParams_{BASE}_transient_spice_serial.config"
    lcf_steady = args.pact_dir / f"lcf_{BASE}_steady.csv"
    lcf_transient = args.pact_dir / f"lcf_{BASE}_transient.csv"

    write_pact_floorplan(pact_flp, grid, args.die_side_m)
    peak_idx, peak_power = write_pact_ptraces(pact_steady_ptrace, pact_transient_ptrace, unit_names, rows)
    write_pact_config(pact_config)
    write_model_params(model_steady, "SuperLU", grid, step_us, len(rows))
    write_model_params(model_transient, "SPICE_transient", grid, step_us, len(rows))
    write_lcf(lcf_steady, pact_flp, pact_steady_ptrace, args.si_thickness_m)
    write_lcf(lcf_transient, pact_flp, pact_transient_ptrace, args.si_thickness_m)

    hotspot_paths = write_hotspot_inputs(args.hotspot_dir, powers, total_by_time, sample_s, args.die_side_m)

    manifest = {
        "base": BASE,
        "stage3_inputs": {
            "grid_power": str(grid_power_path),
            "transient_ptrace": str(transient_path),
            "metadata": str(metadata_path),
            "region_power_summary": str(region_path),
        },
        "grid": grid,
        "die_side_m": args.die_side_m,
        "cell_side_m": args.die_side_m / grid,
        "time_rows": len(rows),
        "first_time_ps": time_ps[0],
        "last_time_ps": time_ps[-1],
        "median_step_us": step_us,
        "hotspot_sampling_interval_s": sample_s,
        "peak_time_index": peak_idx,
        "peak_time_ps": time_ps[peak_idx],
        "peak_total_power_w": peak_power,
        "min_total_power_w": min(total_by_time),
        "max_total_power_w": max(total_by_time),
        "coarse_block_power_w": powers,
        "coarse_block_mapping": REGION_TO_BLOCK,
        "pact": {
            "floorplan": str(pact_flp),
            "steady_ptrace": str(pact_steady_ptrace),
            "transient_ptrace": str(pact_transient_ptrace),
            "config": str(pact_config),
            "steady_modelParams": str(model_steady),
            "transient_modelParams": str(model_transient),
            "steady_lcf": str(lcf_steady),
            "transient_lcf": str(lcf_transient),
            "threading": "number_of_core=1 for formal SPICE transient because local Xyce is serial",
        },
        "hotspot": {key: str(value) for key, value in hotspot_paths.items()},
        "caveat": "Stage 4 inputs are derived from Stage 3 normalized proxy power, not signoff power.",
    }
    manifest_path = args.pact_dir / f"manifest_{BASE}_inputs.json"
    write_manifest(manifest_path, manifest)
    shutil.copy2(manifest_path, args.artifacts_dir / manifest_path.name)

    print(f"grid={grid} time_rows={len(rows)} units={len(unit_names)}")
    print(f"die_side_m={args.die_side_m:.9g} cell_side_m={args.die_side_m / grid:.9g}")
    print(f"peak_time_index={peak_idx} peak_total_power_w={peak_power:.12g}")
    print(f"pact_dir={args.pact_dir}")
    print(f"hotspot_dir={args.hotspot_dir}")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
