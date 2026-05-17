# Stage 3 OpenSTA sanity for proxy handoff
read_liberty /home/lisihang/thermal_placement/third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_OA_RVT_TT_nldm_201020.lib
read_liberty /home/lisihang/thermal_placement/third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_AO_RVT_TT_nldm_201020.lib
read_liberty /home/lisihang/thermal_placement/third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.lib
read_liberty /home/lisihang/thermal_placement/third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_SEQ_RVT_TT_nldm_201020.lib
read_liberty /home/lisihang/thermal_placement/third_party/edahub/edahub/technology/asap7/lib/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.lib
read_verilog /home/lisihang/thermal_placement/physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.v
link_design Gemmini
read_sdc /home/lisihang/thermal_placement/physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.sdc
# SPEF is intentionally not read in this lightweight sanity run; the 2.0 GiB SPEF is recorded as Stage 3 input and left to later strict power/timing recovery.
report_checks -path_delay max -group_count 1 -endpoint_count 1
