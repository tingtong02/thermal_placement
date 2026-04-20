#!/usr/bin/env python3
"""Smoke-test the Python analysis environment used by the thermal flow."""

from __future__ import annotations

import importlib
import tempfile
from pathlib import Path

from vcdvcd import VCDVCD


REQUIRED_MODULES = [
    "numpy",
    "pandas",
    "matplotlib",
    "yaml",
    "scipy",
    "vcd",
    "vcdvcd",
]


def main() -> None:
    versions: list[str] = []
    for name in REQUIRED_MODULES:
        module = importlib.import_module(name)
        versions.append(f"{name}={getattr(module, '__version__', 'ok')}")

    vcd_text = """$date
  smoke-test
$end
$version
  check_python_env.py
$end
$timescale 1ns $end
$scope module top $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
#0
0!
#5
1!
#10
0!
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        vcd_path = Path(tmpdir) / "tiny.vcd"
        vcd_path.write_text(vcd_text, encoding="ascii")
        parsed = VCDVCD(str(vcd_path), store_tvs=True)
        if "top.clk" not in parsed.signals:
            raise RuntimeError(f"vcdvcd did not find top.clk; signals={parsed.signals!r}")
        transitions = parsed["top.clk"].tv
        if len(transitions) != 3:
            raise RuntimeError(f"unexpected VCD transition count: {transitions!r}")

    print("python environment ok")
    print(", ".join(versions))


if __name__ == "__main__":
    main()
