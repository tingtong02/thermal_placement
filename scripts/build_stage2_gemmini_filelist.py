#!/usr/bin/env python3
"""Build a reduced Stage 2 RTL filelist for the Gemmini top closure."""

from __future__ import annotations

import argparse
import re
from collections import deque
from pathlib import Path

MODULE_DEF_RE = re.compile(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", re.MULTILINE)
PACKAGE_DEF_RE = re.compile(r"^\s*package\s+([A-Za-z_][A-Za-z0-9_$]*)\b", re.MULTILINE)
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")

SV_KEYWORDS = {
    "always", "always_comb", "always_ff", "always_latch", "and", "assign", "assert", "assume",
    "begin", "buf", "bufif0", "bufif1", "case", "casex", "casez", "cell", "class", "clocking",
    "cmos", "config", "const", "constraint", "cover", "deassign", "default", "defparam", "design",
    "disable", "edge", "else", "end", "endcase", "endclass", "endclocking", "endconfig", "endfunction",
    "endgenerate", "endgroup", "endinterface", "endmodule", "endpackage", "endprimitive", "endprogram",
    "endproperty", "endspecify", "endsequence", "endtable", "endtask", "enum", "event", "final",
    "for", "force", "forever", "fork", "function", "generate", "genvar", "highz0", "highz1", "if",
    "iff", "ifnone", "import", "initial", "inout", "input", "instance", "interface", "join", "join_any",
    "join_none", "liblist", "library", "localparam", "logic", "macromodule", "modport", "module", "nand",
    "negedge", "nettype", "new", "nmos", "nor", "not", "notif0", "notif1", "or", "output", "package",
    "parameter", "pmos", "posedge", "primitive", "program", "property", "pull0", "pull1", "pulldown",
    "pullup", "rand", "randc", "ref", "reg", "release", "repeat", "rnmos", "rpmos", "rtran", "rtranif0",
    "rtranif1", "scalared", "sequence", "shortint", "shortreal", "signed", "specify", "specparam", "static",
    "string", "struct", "supply0", "supply1", "table", "task", "time", "tran", "tranif0", "tranif1",
    "tri", "tri0", "tri1", "triand", "trior", "trireg", "type", "typedef", "union", "unsigned", "use",
    "uwire", "var", "vectored", "wait", "wand", "weak0", "weak1", "while", "wire", "wor", "xnor", "xor",
}
DEFAULT_EXCLUDED_BASENAMES = {
    "chipyard.harness.TestHarness.GemminiRocketConfig.top.mems.v",
    "chipyard.harness.TestHarness.GemminiRocketConfig.model.mems.v",
    "TestDriver.v",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rtl-dir", type=Path, required=True)
    parser.add_argument("--top-module", default="Gemmini")
    parser.add_argument("--seed-filelist", type=Path)
    parser.add_argument("--blackbox-file", type=Path, action="append", default=[])
    parser.add_argument("--exclude-basename", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def strip_comments(text: str) -> str:
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def collect_seed_order(seed_filelist: Path | None, rtl_dir: Path, excluded: set[str]) -> list[Path]:
    if seed_filelist and seed_filelist.exists():
        ordered = []
        for raw in seed_filelist.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            path = Path(line)
            if path.exists() and path.name not in excluded:
                ordered.append(path.resolve())
        if ordered:
            return ordered
    candidates = sorted(path.resolve() for path in rtl_dir.glob("*.sv")) + sorted(path.resolve() for path in rtl_dir.glob("*.v"))
    return [path for path in candidates if path.name not in excluded]


def collect_definitions(files: list[Path]) -> tuple[dict[str, Path], set[Path]]:
    module_to_file: dict[str, Path] = {}
    package_files: set[Path] = set()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in MODULE_DEF_RE.finditer(text):
            module_to_file.setdefault(match.group(1), path)
        if PACKAGE_DEF_RE.search(text):
            package_files.add(path)
    return module_to_file, package_files


def find_module_body(text: str, module_name: str) -> str:
    pattern = re.compile(rf"\bmodule\s+{re.escape(module_name)}\b")
    match = pattern.search(text)
    if not match:
        return ""
    start = match.start()
    end = text.find("endmodule", start)
    if end == -1:
        end = len(text)
    else:
        end += len("endmodule")
    return text[start:end]


def instantiated_modules(body: str, known_modules: set[str]) -> set[str]:
    body = strip_comments(body)
    found: set[str] = set()
    for token in IDENT_RE.findall(body):
        if token in known_modules and token not in SV_KEYWORDS:
            found.add(token)
    return found


def main() -> None:
    args = parse_args()
    rtl_dir = args.rtl_dir.resolve()
    excluded = set(DEFAULT_EXCLUDED_BASENAMES)
    excluded.update(args.exclude_basename)
    files = collect_seed_order(args.seed_filelist, rtl_dir, excluded)
    module_to_file, package_files = collect_definitions(files)
    known_modules = set(module_to_file)
    if args.top_module not in known_modules:
        raise SystemExit(f"top module not found: {args.top_module}")

    deps: dict[str, set[str]] = {}
    for module_name, path in module_to_file.items():
        text = path.read_text(encoding="utf-8", errors="ignore")
        body = find_module_body(text, module_name)
        children = instantiated_modules(body, known_modules)
        children.discard(module_name)
        deps[module_name] = children

    reachable_modules: set[str] = set()
    queue = deque([args.top_module])
    while queue:
        module_name = queue.popleft()
        if module_name in reachable_modules:
            continue
        reachable_modules.add(module_name)
        for child in sorted(deps.get(module_name, set())):
            if child not in reachable_modules:
                queue.append(child)

    reachable_files = {module_to_file[module] for module in reachable_modules}
    reachable_files |= package_files
    ordered_output: list[Path] = [path for path in files if path in reachable_files]
    for extra in args.blackbox_file:
        ordered_output.append(extra.resolve())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(str(path) for path in ordered_output) + "\n", encoding="utf-8")

    print(f"top_module={args.top_module}")
    print(f"reachable_modules={len(reachable_modules)}")
    print(f"reachable_files={len(ordered_output)}")
    print(f"excluded_basenames={len(excluded)}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
