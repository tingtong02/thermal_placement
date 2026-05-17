# Reduced edahub Technology Libraries

This directory adapts the reduced technology libraries vendored in `third_party/edahub` for the main Thermal Placement repository.

Supported first:

- `asap7`
- `nangate45`
- `sky130hd`

These are not complete PDKs. They are minimal standard-cell library bundles intended for early synthesis, timing setup, floorplanning, placement, and routing experiments. They do not include a complete signoff stack.

## Make Usage

Include one of the Make fragments from a flow config:

```make
include $(TP_ROOT)/configs/reduced_techlibs/nangate45.mk

LIB_FILES := $(TECHLIB_LIB_FILES)
TECH_LEF := $(TECHLIB_TECH_LEF)
SC_LEF := $(TECHLIB_SC_LEF)
```

## Tcl Usage

Source one of the Tcl fragments from OpenROAD/OpenSTA scripts:

```tcl
source $::env(TP_ROOT)/configs/reduced_techlibs/nangate45.tcl

foreach lib $TECHLIB(LIB_FILES) {
  read_liberty $lib
}
foreach lef $TECHLIB(LEF_FILES) {
  read_lef $lef
}
```

## OpenROAD-flow-scripts Overlay

The main repository also provides ORFS platform overlays under `configs/openroad/reduced_platforms`. Use them by pointing `PLATFORM_HOME` at the overlay directory:

```sh
make -C third_party/OpenROAD-flow-scripts/flow \
  PLATFORM_HOME="$TP_ROOT/configs/openroad/reduced_platforms" \
  DESIGN_CONFIG="$DESIGN_CONFIG" synth floorplan place route
```

The overlays use edahub's reduced Liberty/DB/LEF files and reuse OpenROAD-flow-scripts' platform Tcl helpers where needed.
