import os
from pathlib import Path
from typing import Callable

from .stdcell_library import StdcellLibrary


def collect_filtered_files(root: str | Path, filter_func: Callable[[str], bool]) -> list:
    root = Path(root)
    if not root.is_dir():
        return []
    return sorted(str(root / name) for name in os.listdir(root) if filter_func(name))


def thermal_placement_root() -> Path:
    return Path(os.environ.get("THERMAL_PLACEMENT_ROOT", "/home/lisihang/thermal_placement"))


class Asap7Library(StdcellLibrary):
    """
    Full ASAP7 PDK collateral for the Cadence Genus/Innovus startup flow.
    """

    def __init__(
        self,
        pdk_dir: str,
        syn_tool: str = "genus",
        pnr_tool: str = "innovus",
        version: str = "asap7sc7p5t_28",
    ) -> None:
        super().__init__(pdk_dir, syn_tool, pnr_tool)
        self.version = version
        assert version in (
            "asap7sc6t_26",
            "asap7sc7p5t_27",
            "asap7sc7p5t_28",
        )
        assert syn_tool == "genus", "We cannot support Yosys for now"
        assert pnr_tool == "innovus", "We cannot support OpenROAD for now"

    @property
    def name(self) -> str:
        return "Asap7"

    @property
    def nldm_cache_dir(self) -> Path | None:
        env_cache = os.environ.get("ASAP7_LIB_CACHE")
        if env_cache and Path(env_cache).is_dir():
            return Path(env_cache)
        project_cache = thermal_placement_root() / ".cache" / "asap7" / self.version / "NLDM"
        if project_cache.is_dir():
            return project_cache
        return None

    @property
    def lib_files(self) -> list:
        if self.nldm_cache_dir:
            return collect_filtered_files(
                self.nldm_cache_dir,
                lambda x: x.endswith(".lib") and "_TT_nldm_" in x,
            )
        lib_dir = Path(self.pdk_dir) / self.version / "LIB" / "NLDM"
        return collect_filtered_files(lib_dir, lambda x: x.endswith("TT_nldm_201020.lib.gz"))

    @property
    def setup_lib_files(self) -> list:
        if self.nldm_cache_dir:
            return self.lib_files
        lib_dir = Path(self.pdk_dir) / self.version / "LIB" / "NLDM"
        return collect_filtered_files(lib_dir, lambda x: x.endswith("SS_nldm_201020.lib.gz"))

    @property
    def hold_lib_files(self) -> list:
        if self.nldm_cache_dir:
            return self.lib_files
        lib_dir = Path(self.pdk_dir) / self.version / "LIB" / "NLDM"
        return collect_filtered_files(lib_dir, lambda x: x.endswith("FF_nldm_201020.lib.gz"))

    @property
    def lef_files(self) -> list:
        pdk_version_dir = Path(self.pdk_dir) / self.version
        techlef_1x = pdk_version_dir / "techlef_misc" / "asap7_tech_1x_201209.lef"
        lef_dir = pdk_version_dir / "LEF"
        if techlef_1x.exists() and lef_dir.is_dir():
            return [str(techlef_1x)] + collect_filtered_files(
                lef_dir,
                lambda x: x.endswith("_1x_220121a.lef"),
            )

        techlef_4x = pdk_version_dir / "techlef_misc" / "asap7_tech_4x_201209.lef"
        scaled_lef_dir = pdk_version_dir / "LEF" / "scaled"
        return [str(techlef_4x)] + collect_filtered_files(scaled_lef_dir, lambda x: x.endswith(".lef"))

    @property
    def qrc_techfiles(self) -> list:
        qrc_1x = Path(self.pdk_dir) / self.version / "qrc" / "qrcTechFile_typ03_unscaledV02"
        if qrc_1x.exists():
            return [str(qrc_1x)]
        return [str(Path(self.pdk_dir) / self.version / "qrc" / "qrcTechFile_typ03_scaled4xV06")]

    @property
    def gds_files(self) -> list:
        gds_dir = Path(self.pdk_dir) / self.version / "GDS"
        return collect_filtered_files(gds_dir, lambda x: x.endswith(".gds"))

    @property
    def stream_layer_map(self) -> str:
        candidates = [
            Path(self.pdk_dir) / "asap7_pdk_r1p7" / "cdslib" / "asap7_TechLib_10" / "asap7_fromAPR_08b.layermap",
            Path(self.pdk_dir) / "asap7_pdk_r1p7" / "cdslib" / "asap7_TechLib_10" / "asap7_TechLib_08.layermap",
        ]
        for path in candidates:
            if path.is_file():
                return str(path)
        return str(candidates[0])

    @property
    def dont_use_cells(self) -> list:
        return [
            "ICGx*DC*",
            "AND4x1*",
            "SDFLx2*",
            "AO21x1*",
            "XOR2x2*",
            "OAI31xp33*",
            "OAI221xp5*",
            "SDFLx3*",
            "SDFLx1*",
            "AOI211xp5*",
            "OAI322xp33*",
            "OR2x6*",
            "A2O1A1O1Ixp25*",
            "XNOR2x1*",
            "OAI32xp33*",
            "FAx1*",
            "OAI21x1*",
            "OAI31xp67*",
            "OAI33xp33*",
            "AO21x2*",
            "AOI32xp33*",
        ]

    @property
    def innovus_vars(self) -> dict:
        return {
            "place_site": "asap7sc7p5t",
            "assign_io_pins": True,
            "pwr_port": "VDD",
            "gnd_port": "VSS",
            "stripe_width": 0.04,
            "stripe_spacing": 0.40,
            "stripe_distance": 10.00,
            "stripe_v_layer": "M8",
            "stripe_h_layer": "M9",
            "sroute_min_layer": "M1",
            "sroute_max_layer": "M9",
            "sroute_core_pin_target": "stripe",
            "sroute_block_pin_target": "stripe",
            "route_min_layer": "M2",
            "route_max_layer": "M8",
            "cts_routing_mul": 2,
            "ndr_cts_min_layer": "M2",
            "ndr_cts_max_layer": "M8",
            "require_pg_clean": True,
            "fake_sram_macro_cells": ["mem_ext", "mem_0_ext"],
            "expected_fake_sram_macro_instances": 6,
            "macro_placement_cols": 3,
            "macro_halo_x": 5.0,
            "macro_halo_y": 5.0,
            "cts_inv_cells": [],
            "cts_buf_cells": [],
        }

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(self.innovus_vars)
        d.update({"gds_files": self.gds_files, "stream_layer_map": self.stream_layer_map})
        return d
