# Gemmini Configuration Snapshot

Date: 2026-04-29
Run root: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`

## Selected Configuration

This run uses the default Chipyard Gemmini Rocket configuration:

```text
GemminiRocketConfig = DefaultGemminiConfig + WithNHugeCores(1) + WithSystemBusWidth(128) + AbstractConfig
```

## Key Parameters

| Parameter | Value |
| --- | --- |
| `tileRows` | 1 |
| `tileColumns` | 1 |
| `meshRows` | 16 |
| `meshColumns` | 16 |
| `DIM` | 16 |
| input type | `SInt(8.W)` / `int8_t` |
| weight type | `SInt(8.W)` / `int8_t` |
| accumulator type | `SInt(32.W)` / `int32_t` |
| spatial output type | `SInt(20.W)` |
| dataflow | `Dataflow.BOTH` |
| scratchpad capacity | 256 KiB |
| accumulator capacity | 64 KiB |
| scratchpad banks | 4 |
| accumulator banks | 2 |
| `BANK_ROWS` | 4096 |
| `ACC_ROWS` | 1024 |
| `MAX_BYTES` | 64 |
| DMA bus width | 128 |
| system bus width | 128 |

## Evidence Files

- `third_party/chipyard/generators/gemmini/chipyard/GemminiConfigs.scala`
- `third_party/chipyard/generators/gemmini/src/main/scala/gemmini/Configs.scala`
- `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/include/gemmini_params.h`

## Constraints

Do not change this hardware configuration within this run. A different Gemmini configuration requires a separate run root and a new Stage 0 freeze.
