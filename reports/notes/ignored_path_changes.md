# Ignored Path Changes

This note records environment and dependency repairs made under paths ignored by `.gitignore`.

| Date | Ignored Path | Change Reason | Verification | Follow-up |
| --- | --- | --- | --- | --- |
| 2026-04-20 | `third_party/chipyard/generators/*`, `third_party/chipyard/tools/*` | Re-aligned Chipyard submodules and restored tracked source files in damaged worktrees where only `.git` and build artifacts remained | `scripts/run_gemmini_rtl_generation.sh` completed for `GemminiRocketConfig` | Keep these paths out of version control; preserve this note as the audit trail |
| 2026-04-20 | `third_party/chipyard/tools/DRAMSim2` | Restored tracked DRAMSim2 sources from the submodule `HEAD` after debug-simulator build exposed a deleted worktree | `git -C third_party/chipyard/tools/DRAMSim2 status --short` no longer shows deleted tracked files | Re-run Verilator debug build after finishing current Phase B prep |
| 2026-04-20 | `tools/circt` | Installed prebuilt CIRCT/firtool so Chipyard FIRRTL export can lower to split Verilog | `firtool --version` and successful RTL export | Keep tool version pinned in environment notes |
| 2026-04-20 | `tools/bin/jq` | Added a local `jq` compatibility shim because Chipyard generation invoked `jq` and the host environment did not provide it | regenerated `*.appended.anno.json` and reran RTL generation successfully | Replace with system `jq` later if desired; current shim covers the used subset |
