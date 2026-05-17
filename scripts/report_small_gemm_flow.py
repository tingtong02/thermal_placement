#!/usr/bin/env python3
"""Write a compact report for the small GEMM thermal validation flow."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_region_activity(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_ttrace(path: Path) -> tuple[list[str], list[float]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        return [], []
    names = lines[0].split()
    temps = [float(value) for value in lines[-1].split()]
    return names, temps


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def log_contains(path: Path, text: str) -> bool:
    if not path.exists():
        return False
    return text in path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-tag", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--make-jobs", required=True)
    parser.add_argument("--max-cycles", required=True)
    parser.add_argument("--sim-status", required=True)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--err", required=True, type=Path)
    parser.add_argument("--vcd", required=True, type=Path)
    parser.add_argument("--region-csv", required=True, type=Path)
    parser.add_argument("--floorplan", required=True, type=Path)
    parser.add_argument("--ptrace", required=True, type=Path)
    parser.add_argument("--ttrace", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    rows = read_region_activity(args.region_csv)
    active_rows = sorted(rows, key=lambda row: int(float(row["toggle_count"])), reverse=True)
    temps_names, temps = read_ttrace(args.ttrace)
    temp_pairs = list(zip(temps_names, temps))
    hottest = sorted(temp_pairs, key=lambda item: item[1], reverse=True)
    avg_temp = sum(temps) / len(temps) if temps else 0.0
    max_temp = max(temps) if temps else 0.0
    min_temp = min(temps) if temps else 0.0

    ok_seen = log_contains(args.log, "small-gemm-ok")
    fail_seen = log_contains(args.log, "small-gemm-fail")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as f:
        f.write("# Small GEMM Thermal Validation Report\n\n")
        f.write("## 范围\n\n")
        f.write(
            "这是一个最小 Gemmini GEMM 验证流程，用于对齐验证计划中的 Phase B/C/D/H "
            "工具闭环：运行一个 16x16 output-stationary GEMM，导出 VCD，提取活动率，"
            "用简单 activity-weighted proxy 生成 HotSpot 输入并完成 steady-state 热仿真。"
            "该报告不是 signoff 级功耗报告，也尚未包含 ORFS placement。\n\n"
        )
        f.write("## 运行配置\n\n")
        f.write(f"- workload: `{args.run_tag}`\n")
        f.write(f"- config: `{args.config}`\n")
        f.write("- matrix: `DIM x DIM` GEMM，当前为 `16 x 16 x 16`\n")
        f.write("- dataflow: `OUTPUT_STATIONARY`\n")
        f.write(f"- max_cycles: `{args.max_cycles}`\n")
        f.write(f"- sim_status: `{args.sim_status}`\n")
        f.write(f"- make_jobs: `{args.make_jobs}`\n")
        f.write(f"- functional_ok_seen: `{ok_seen}`\n")
        f.write(f"- functional_fail_seen: `{fail_seen}`\n\n")
        f.write("## 产物\n\n")
        f.write(f"- binary: `{args.binary}`\n")
        f.write(f"- stdout log: `{args.log}`\n")
        f.write(f"- stderr log: `{args.err}`\n")
        f.write(f"- VCD: `{args.vcd}` ({file_size(args.vcd)} bytes)\n")
        f.write(f"- region activity: `{args.region_csv}`\n")
        f.write(f"- HotSpot floorplan: `{args.floorplan}`\n")
        f.write(f"- HotSpot power trace: `{args.ptrace}`\n")
        f.write(f"- HotSpot steady output: `{args.ttrace}`\n\n")
        f.write("## 区域活动率\n\n")
        f.write("| region | signals | toggles | avg_normalized_activity |\n")
        f.write("| --- | ---: | ---: | ---: |\n")
        for row in active_rows:
            f.write(
                f"| `{row['region']}` | {row['signal_count']} | {row['toggle_count']} | "
                f"{float(row['avg_normalized_activity']):.6e} |\n"
            )
        f.write("\n## HotSpot Steady-State\n\n")
        f.write(f"- Tmax: `{max_temp:.2f} K`\n")
        f.write(f"- Tavg: `{avg_temp:.2f} K`\n")
        f.write(f"- Tmin: `{min_temp:.2f} K`\n")
        f.write(f"- max_gradient_proxy: `{(max_temp - min_temp):.2f} K`\n\n")
        f.write("| hottest_block | temperature_K |\n")
        f.write("| --- | ---: |\n")
        for name, temp in hottest[:5]:
            f.write(f"| `{name}` | {temp:.2f} |\n")
        f.write("\n## 初步解读\n\n")
        f.write(
            "本流程确认了本地 RISC-V 工具链、Gemmini bare-metal 程序、Verilator debug "
            "仿真器、VCD 活动率提取、activity-to-power proxy 和 HotSpot 调用可以形成一条"
            "可复现路径。当前功耗数值仍是相对 proxy；下一步应补 PE 子区域/bank 级映射，"
            "并进入 ORFS macro placement 对照实验。\n"
        )

    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
