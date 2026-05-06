from pathlib import Path

from .asap7 import Asap7Library


class GemminiAsap7Library(Asap7Library):
    """Gemmini Phase 2 ASAP7 tech bundle with fake SRAM collateral."""

    def __init__(
        self,
        pdk_dir: str,
        repo_root: str | Path,
        fake_sram_cache: str | Path,
        syn_tool: str = "genus",
        pnr_tool: str = "innovus",
        version: str = "asap7sc7p5t_28",
    ) -> None:
        super().__init__(pdk_dir, syn_tool=syn_tool, pnr_tool=pnr_tool, version=version)
        self.repo_root = Path(repo_root)
        self.fake_sram_cache = Path(fake_sram_cache)

    @property
    def name(self) -> str:
        return "GemminiAsap7FakeSram"

    @property
    def fake_sram_lib_files(self) -> list:
        return sorted(str(path) for path in (self.fake_sram_cache / "lib").glob("*.lib"))

    @property
    def fake_sram_lef_files(self) -> list:
        return sorted(str(path) for path in (self.fake_sram_cache / "lef").glob("*.lef"))

    @property
    def fake_sram_stub_files(self) -> list:
        verilog_dir = self.fake_sram_cache / "verilog"
        return sorted(str(path) for path in verilog_dir.glob("*.sv")) + sorted(str(path) for path in verilog_dir.glob("*.v"))

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["setup_lib_files"] = d["setup_lib_files"] + self.fake_sram_lib_files
        d["hold_lib_files"] = d["hold_lib_files"] + self.fake_sram_lib_files
        d["lib_files"] = d["lib_files"] + self.fake_sram_lib_files
        d["lef_files"] = d["lef_files"] + self.fake_sram_lef_files
        d.update(
            {
                "fake_sram_cache": str(self.fake_sram_cache),
                "fake_sram_lib_files": self.fake_sram_lib_files,
                "fake_sram_lef_files": self.fake_sram_lef_files,
                "fake_sram_stub_files": self.fake_sram_stub_files,
            }
        )
        return d
