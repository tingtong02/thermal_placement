# ATSim References

更新时间：2026-05-03

本目录保存与 `third_party/ATSim3D_pub` 和本地 ATSim 工具直接相关的公开论文 PDF。PDF 均来自 arXiv 公开页面。

## Papers

| 文件 | 论文 | 来源 | 关联工具 | SHA256 |
| --- | --- | --- | --- | --- |
| `ATSim3D_ISEDA2024_Wang_arXiv2601.11050.pdf` | Qipan Wang, Tianxiang Zhu, Yibo Lin, Runsheng Wang, Ru Huang, "ATSim3D: Towards Accurate Thermal Simulator for Heterogeneous 3D-IC Systems Considering Nonlinear Leakage and Conductivity" | arXiv:2601.11050; related DOI `10.1109/ISEDA62518.2024.10617604` | `third_party/ATSim3D_pub/src/ATSim3D.py`; `scripts/run_atsim3d.sh` | `bb8ea9fa1dc067df25e62ecdfc10a2fa20a7fd167214ad439ac032264ae1280d` |
| `ATSim3_5D_ISEDA2025_Wang_arXiv2601.11053.pdf` | Qipan Wang, Tianxiang Zhu, Yibo Lin, Runsheng Wang, Ru Huang, "ATSim3.5D: A Multiscale Thermal Simulator for 3.5D-IC Systems based on Nonlinear Multigrid Method" | arXiv:2601.11053; related DOI `10.1109/ISEDA65950.2025.11101154` | `tools/atsim3d-bin/ATSim3_5D`; `scripts/run_atsim3_5d.sh` | `f1fa6dd18690440d52552d40acb8f815133f8c5a32d1c2200ed39af030d83c49` |

## Download and validation commands

```bash
mkdir -p docs/references/atsim
curl -L -f -o docs/references/atsim/ATSim3D_ISEDA2024_Wang_arXiv2601.11050.pdf https://arxiv.org/pdf/2601.11050
curl -L -f -o docs/references/atsim/ATSim3_5D_ISEDA2025_Wang_arXiv2601.11053.pdf https://arxiv.org/pdf/2601.11053
file docs/references/atsim/*.pdf
sha256sum docs/references/atsim/*.pdf
```

Validation result on 2026-05-03:

- `ATSim3D_ISEDA2024_Wang_arXiv2601.11050.pdf`: PDF 1.7, 6 pages.
- `ATSim3_5D_ISEDA2025_Wang_arXiv2601.11053.pdf`: PDF 1.7, 8 pages.
