import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

from manager.common import BaseManager
from utils import mkdir, if_exist


class InnovusManager(BaseManager):
    """
        Cadence Innovus Manager implement netlist into GDSII
    """

    def __init__(self, configs: dict) -> None:
        super().__init__(configs)
        mkdir(self.rundir)
        mkdir(self.data_dir)
        mkdir(self.log_dir)
        mkdir(self.report_dir)
        mkdir(self.script_dir)

    @property
    def name(self) -> str:
        return 'innovus_manager'

    @property
    def data_dir(self) -> str:
        return os.path.join(self.rundir, 'data')
    
    @property
    def log_dir(self) -> str:
        return os.path.join(self.rundir, 'log')
    
    @property
    def report_dir(self) -> str:
        return os.path.join(self.rundir, 'reports')
    
    @property
    def script_dir(self) -> str:
        return os.path.join(self.rundir, 'scripts')
    
    @property
    def mmmc_script_path(self) -> str:
        return os.path.join(self.script_dir, 'mmmc.tcl')

    @property
    def top_module(self) -> str:
        return self.configs.get('top_module')
    
    @property
    def innovus_bin(self) -> str:
        return self.configs.get('innovus_bin')

    @property
    def env_setup_script(self) -> str:
        return self.configs.get('env_setup_script', '')

    @property
    def floorplan_def_path(self) -> str:
        return os.path.join(self.data_dir, f"{self.top_module}.floorplan.def")

    @property
    def routed_def_path(self) -> str:
        return os.path.join(self.data_dir, f"{self.top_module}.routed.def")

    @property
    def routed_verilog_path(self) -> str:
        return os.path.join(self.data_dir, f"{self.top_module}.routed.v")

    @property
    def routed_sdf_path(self) -> str:
        return os.path.join(self.data_dir, f"{self.top_module}.routed.sdf")

    @property
    def routed_spef_path(self) -> str:
        return os.path.join(self.data_dir, f"{self.top_module}.routed.spef")

    @property
    def routed_gds_path(self) -> str:
        return os.path.join(self.data_dir, f"{self.top_module}.gds")

    def step_manifest_path(self, step_name: str) -> str:
        return os.path.join(self.report_dir, f"{step_name}_manifest.json")

    def expected_step_artifacts(self, step_name: str) -> dict:
        mapping = {
            'init': {'checkpoint': os.path.join(self.data_dir, 'init.enc')},
            'floorplan': {
                'checkpoint': os.path.join(self.data_dir, 'floorplan.enc'),
                'floorplan_def': self.floorplan_def_path,
                'macro_placement_report': os.path.join(self.report_dir, 'floorplan_macro_placement.rpt'),
            },
            'powerplan': {
                'checkpoint': os.path.join(self.data_dir, 'powerplan.enc'),
                'connectivity_report': os.path.join(self.report_dir, 'powerplan_connectivity.rpt'),
                'pg_short_report': os.path.join(self.report_dir, 'powerplan_PG_short.rpt'),
            },
            'placement': {
                'checkpoint': os.path.join(self.data_dir, 'placement.enc'),
                'timing_dir': os.path.join(self.report_dir, 'preCTS_timing'),
                'area_report': os.path.join(self.report_dir, 'preCTS_area.rpt'),
                'power_report': os.path.join(self.report_dir, 'preCTS_power.rpt'),
            },
            'cts': {
                'checkpoint': os.path.join(self.data_dir, 'cts.enc'),
                'timing_dir': os.path.join(self.report_dir, 'postCTS_timing'),
            },
            'routing': {
                'checkpoint': os.path.join(self.data_dir, 'routing.enc'),
                'routed_def': self.routed_def_path,
                'routed_verilog': self.routed_verilog_path,
                'routed_sdf': self.routed_sdf_path,
                'routed_spef': self.routed_spef_path,
                'gds': self.routed_gds_path,
                'timing_dir': os.path.join(self.report_dir, 'postRoute_timing'),
                'area_report': os.path.join(self.report_dir, 'postRoute_area.rpt'),
                'power_report': os.path.join(self.report_dir, 'postRoute_power.rpt'),
                'drc_report': os.path.join(self.report_dir, 'postRoute_drc.rpt'),
                'connectivity_report': os.path.join(self.report_dir, 'postRoute_connectivity.rpt'),
            },
        }
        return mapping.get(step_name, {})

    def write_step_manifest(self, step_name: str, ok: bool, error: str | None = None) -> None:
        expected = self.expected_step_artifacts(step_name)
        artifact_status = {name: Path(path).exists() for name, path in expected.items()}
        manifest = {
            'step': step_name,
            'ok': ok,
            'error': error,
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'rundir': self.rundir,
            'script': os.path.join(self.script_dir, f'{step_name}.tcl'),
            'log': os.path.join(self.log_dir, f'{step_name}.log'),
            'expected_artifacts': expected,
            'artifact_status': artifact_status,
            'classification': self.classify_step(step_name, ok, artifact_status, error),
        }
        Path(self.step_manifest_path(step_name)).write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    def classify_step(self, step_name: str, ok: bool, artifact_status: dict, error: str | None) -> dict:
        if ok and all(artifact_status.values()):
            return {'status': 'complete', 'reason': 'expected artifacts exist'}
        if step_name == 'powerplan':
            return {'status': 'pg_connectivity_check_required', 'reason': 'powerplan acceptance requires zero special-net opens'}
        if step_name == 'routing':
            return {'status': 'post_route_artifact_gate', 'reason': 'routing acceptance requires routed DEF/Verilog/SDF/SPEF/GDS and reports'}
        if error:
            return {'status': 'failed', 'reason': error}
        return {'status': 'incomplete', 'reason': 'one or more expected artifacts are missing'}

    def get_file_list(self, key: str, sep: str = " ") -> str:
        """
            Get the string of a file list from configs.
        """
        files = self.configs.get(key, [])
        return sep.join(files)
    
    def generate_code(self, name: str) -> str:
        """
            Generate code for specific script
        """
        if name == 'mmmc':
            return self.generate_mmmc_code()
        elif name == 'init':
            return self.generate_init_code()
        elif name == 'floorplan':
            return self.generate_floorplan_code()
        elif name == 'powerplan':
            return self.generate_powerplan_code()
        elif name == 'placement':
            return self.generate_placement_code()
        elif name == 'cts':
            return self.generate_cts_code()
        elif name == 'routing':
            return self.generate_routing_code()
        else:
            raise NotImplementedError("Script %s is not implemented" % name)

    def write_to_file(self, codes: str, filepath: str, is_tcl: bool, prev_checkpoint: str = None, cur_checkpoint: str = None) -> None:
        """
            Write the code to the file, with necessary checkpoints.
        """
        mkdir(os.path.dirname(filepath))

        with open(filepath, 'w') as f:
            if prev_checkpoint:
                load_codes = """
# -------------------------------------------------------------
# Read previous checkpoint
# -------------------------------------------------------------
source %s
""" % (os.path.join(self.data_dir, f'{prev_checkpoint}.enc'))
                f.write(load_codes)

            f.write(codes)

            if cur_checkpoint:
                save_codes = """
# -------------------------------------------------------------
# Save Design
# -------------------------------------------------------------
saveDesign %s
""" % os.path.join(self.data_dir, f'{cur_checkpoint}.enc')
                f.write(save_codes)

            if is_tcl:
                f.write("exit 0\n")

    def run_tcl_script(self, step_name: str, timeout: int, condition: Callable) -> None:
        source_env = f"source {self.env_setup_script} && " if self.env_setup_script else ""
        cmd = "cd {} && " \
                "{}{} -no_gui -abort_on_error -overwrite " \
                "-file {} " \
                "-log {} ".format(
                self.rundir,
                source_env,
                self.innovus_bin,
                os.path.join(self.script_dir, f'{step_name}.tcl'),
                os.path.join(self.log_dir, step_name),
            )
        self.routine_check(timeout, cmd, condition)
    
    def run_impl(self) -> None:
        """
            Generate scripts and run innovus
        """
        default_steps = [
            'init',
            'floorplan',
            'powerplan',
            'placement',
            'cts',
            'routing',
        ]
        steps = self.configs.get('steps', default_steps)

        runmode = self.configs.get('runmode', 'normal')

        if runmode == 'script_only':
            self.write_to_file(self.generate_mmmc_code(), self.mmmc_script_path, is_tcl=False)
            prev_step = self.configs.get('start_prev_checkpoint')
            for step in steps:
                self.write_to_file(self.generate_code(step),
                                   os.path.join(self.script_dir, f'{step}.tcl'),
                                   is_tcl=True, prev_checkpoint=prev_step, cur_checkpoint=step)
                prev_step = step
            return

        if runmode == 'fast':
            self.write_to_file(self.generate_mmmc_code(), self.mmmc_script_path, is_tcl=False)
            
            fused_code = "\n\n".join([self.generate_code(step) for step in steps])
            self.write_to_file(fused_code, os.path.join(self.script_dir, 'fused_pnr.tcl'), 
                               is_tcl=True, cur_checkpoint='routing')
            
            self.run_tcl_script(
                step_name='fused_pnr',
                timeout=24 * 3600,
                condition=lambda: if_exist(os.path.join(self.data_dir, 'routing.enc'))
            )
        
        elif runmode == 'normal':
            self.write_to_file(self.generate_mmmc_code(), self.mmmc_script_path, is_tcl=False)

            prev_step = self.configs.get('start_prev_checkpoint')
            for step in steps:
                # Possibly you don't need a clock tree for combinational module
                # So you have to make sure you can run through the flow!
                self.write_to_file(self.generate_code(step),
                                   os.path.join(self.script_dir,  f'{step}.tcl'),
                                   is_tcl=True, prev_checkpoint=prev_step, cur_checkpoint=step)
                prev_step = step

            for step in steps:
                try:
                    self.run_tcl_script(
                        step_name=step,
                        timeout=10 * 3600,
                        condition=lambda step_name=step: if_exist(os.path.join(self.data_dir, f'{step_name}.enc'))
                    )
                except Exception as exc:
                    self.write_step_manifest(step, ok=False, error=repr(exc))
                    raise
                self.write_step_manifest(step, ok=True)

        else:
            raise NotImplementedError("runmode %s is not supported" % runmode)

    def generate_output_impl(self) -> dict:
        return {
            'floorplan_def_file': self.floorplan_def_path,
            'init_checkpoint': os.path.join(self.data_dir, 'init.enc'),
            'floorplan_checkpoint': os.path.join(self.data_dir, 'floorplan.enc'),
            'def_file': self.routed_def_path,
            'routed_verilog_file': self.routed_verilog_path,
            'sdf_file': self.routed_sdf_path,
            'spef_file': self.routed_spef_path,
            'gds_file': self.routed_gds_path,
            'routing_checkpoint': os.path.join(self.data_dir, 'routing.enc'),
            'post_route_timing_dir': os.path.join(self.report_dir, 'postRoute_timing'),
            'post_route_area_report': os.path.join(self.report_dir, 'postRoute_area.rpt'),
            'post_route_power_report': os.path.join(self.report_dir, 'postRoute_power.rpt'),
            'post_route_drc_report': os.path.join(self.report_dir, 'postRoute_drc.rpt'),
            'post_route_connectivity_report': os.path.join(self.report_dir, 'postRoute_connectivity.rpt'),
        }

    def generate_mmmc_code(self) -> str:
        """
            Generate mmmc script
        """
        qrc_techfiles = self.get_file_list('qrc_techfiles')
        qrc_tech_suffix = ('-qrc_tech [list %s]' % qrc_techfiles) if qrc_techfiles else ''

        codes = """
# -------------------------------------------------------------
# Set the SDC FILE
# -------------------------------------------------------------
create_constraint_mode -name setup_constraint -sdc_files %s
create_constraint_mode -name hold_constraint -sdc_files %s

# -------------------------------------------------------------
# Set the lib
# -------------------------------------------------------------
create_library_set -name setup_set -timing [list %s]
create_library_set -name hold_set -timing [list %s]

# -------------------------------------------------------------
# Create timing condition
# -------------------------------------------------------------
create_timing_condition -name setup_cond -library_sets [list setup_set]
create_timing_condition -name hold_cond -library_sets [list hold_set]

# -------------------------------------------------------------
# Create RC corner
# -------------------------------------------------------------
create_rc_corner -name rc_corner %s

# -------------------------------------------------------------
# Create the delay corner
# -------------------------------------------------------------
create_delay_corner -name setup_delay -timing_condition setup_cond -rc_corner rc_corner
create_delay_corner -name hold_delay -timing_condition hold_cond -rc_corner rc_corner

# -------------------------------------------------------------
# Create the analysis view
# -------------------------------------------------------------
create_analysis_view -name setup_view -delay_corner setup_delay -constraint_mode setup_constraint
create_analysis_view -name hold_view -delay_corner hold_delay -constraint_mode hold_constraint

# -------------------------------------------------------------
# Set the analysis view for setup & hold
# -------------------------------------------------------------
set_analysis_view -setup { setup_view } -hold { hold_view }
""" % (
    self.configs.get('setup_sdc_file'),
    self.configs.get('hold_sdc_file'),
    self.get_file_list('setup_lib_files'),
    self.get_file_list('hold_lib_files'),
    qrc_tech_suffix,
)
        return codes
        
    def generate_init_code(self) -> str:
        """
            Generate init script
        """
        codes = """
# ---------------------------------------------
# Read input files
# ---------------------------------------------
set defHierChar {/}
set init_gnd_net {VSS}
set init_pwr_net {VDD}
set init_verilog {%s}
set init_lef_file {%s}
set init_mmmc_version 2
set init_mmmc_file {%s}
set init_top_cell %s

# -------------------------------------------------------------
# Set global configs
# -------------------------------------------------------------
setMultiCpuUsage -localCpu %d

init_design

# -------------------------------------------------------------
# Check design after init
# -------------------------------------------------------------
checkDesign -netList -noHtml -outfile %s
""" % (
    self.configs.get('verilog_file'),
    self.get_file_list('lef_files'),
    self.mmmc_script_path,
    self.top_module,
    self.configs.get('max_threads', 8),
    os.path.join(self.report_dir, 'check_netlist_upon_init.rpt'),
)
        codes += self.generate_timing_report_code(stage='prePlace')

        return codes
        
    def generate_floorplan_code(self) -> str:
        """
            Generate floorplan script.
        """
        codes = ""
        """
            Define a rectangular block die
            The area is placement density times total cell area
        """
        codes += """
# -------------------------------------------------------------
# Define the block die area
# -------------------------------------------------------------
floorPlan -site %s -su 1 %f 1 1 1 1
""" % (
    self.configs.get('place_site'),
    self.configs.get('place_utilization', 0.4),
)
        if self.configs.get('assign_io_pins', True):
            codes += """
# -------------------------------------------------------------
# Assign top-level IO pins
# -------------------------------------------------------------
assignIoPins -autoBusGroup
"""
        else:
            codes += """
# -------------------------------------------------------------
# Allow global placement to place IO pins
# -------------------------------------------------------------
setPlaceMode -place_global_place_io_pins true
"""
        codes += """
# -------------------------------------------------------------
# Explicit fake SRAM macro placement
# -------------------------------------------------------------
set tp_fake_sram_cells {%s}
set tp_expected_fake_sram_macros %d
set tp_macro_cols %d
set tp_macro_halo_x %.3f
set tp_macro_halo_y %.3f
set tp_macro_report [open %s w]
puts $tp_macro_report "# Fake SRAM macro placement report"
puts $tp_macro_report "# policy=explicit_grid cols=$tp_macro_cols halo=${tp_macro_halo_x}x${tp_macro_halo_y}um"
set tp_macros {}
foreach inst_ptr [dbGet top.insts] {
    set master [dbGet $inst_ptr.cell.name]
    if {[lsearch -exact $tp_fake_sram_cells $master] >= 0} {
        lappend tp_macros [dbGet $inst_ptr.name]
    }
}
set tp_macros [lsort $tp_macros]
puts $tp_macro_report "macro_count=[llength $tp_macros]"
if {[llength $tp_macros] != $tp_expected_fake_sram_macros} {
    close $tp_macro_report
    error "expected $tp_expected_fake_sram_macros fake SRAM macro instances, found [llength $tp_macros]: $tp_macros"
}
set tp_core_box_raw [dbGet top.fPlan.coreBox]
set tp_core_box [concat {*}$tp_core_box_raw]
if {[llength $tp_core_box] < 4} {
    close $tp_macro_report
    error "unexpected coreBox format for fake SRAM macro placement: '$tp_core_box_raw' flattened='$tp_core_box'"
}
set tp_llx [lindex $tp_core_box 0]
set tp_lly [lindex $tp_core_box 1]
set tp_urx [lindex $tp_core_box 2]
set tp_ury [lindex $tp_core_box 3]
puts $tp_macro_report "core_box=$tp_llx $tp_lly $tp_urx $tp_ury"
set tp_rows [expr {int(ceil(double([llength $tp_macros]) / double($tp_macro_cols)))}]
set tp_slot_w [expr {($tp_urx - $tp_llx - 2.0 * $tp_macro_halo_x) / double($tp_macro_cols)}]
set tp_slot_h [expr {($tp_ury - $tp_lly - 2.0 * $tp_macro_halo_y) / double($tp_rows)}]
set tp_i 0
foreach inst $tp_macros {
    set tp_col [expr {$tp_i %% $tp_macro_cols}]
    set tp_row [expr {int($tp_i / $tp_macro_cols)}]
    set tp_x [expr {$tp_llx + $tp_macro_halo_x + $tp_col * $tp_slot_w}]
    set tp_y [expr {$tp_lly + $tp_macro_halo_y + $tp_row * $tp_slot_h}]
    placeInstance $inst $tp_x $tp_y R0 -fixed
    puts $tp_macro_report "$inst placed x=$tp_x y=$tp_y orient=R0 status=fixed"
    incr tp_i
}
if {[catch {addHaloToBlock $tp_macro_halo_x $tp_macro_halo_y $tp_macro_halo_x $tp_macro_halo_y -allMacro} tp_halo_msg]} {
    puts $tp_macro_report "halo_warning=$tp_halo_msg"
} else {
    puts $tp_macro_report "halo_status=applied"
}
close $tp_macro_report

# -------------------------------------------------------------
# Generate floorplan
# -------------------------------------------------------------
defOut -floorplan -noStdCells %s
""" % (
    " ".join(self.configs.get('fake_sram_macro_cells', ['mem_ext', 'mem_0_ext'])),
    self.configs.get('expected_fake_sram_macro_instances', 6),
    self.configs.get('macro_placement_cols', 3),
    self.configs.get('macro_halo_x', 5.0),
    self.configs.get('macro_halo_y', 5.0),
    os.path.join(self.report_dir, 'floorplan_macro_placement.rpt'),
    self.floorplan_def_path,
)
        return codes

    def generate_powerplan_code(self) -> str:
        """
            Generate powerplan script
        """
        codes = ""
        """
            Connect pins to PDN
        """
        codes += """
# -------------------------------------------------------------
# Global PG net connect
# -------------------------------------------------------------
set pwr_port %s
set gnd_port %s
globalNetConnect VDD -type pgpin -pin $pwr_port -inst *
globalNetConnect VDD -type tiehi -pin $pwr_port -inst *
globalNetConnect VDD -type net -net VDD
globalNetConnect VSS -type pgpin -pin $gnd_port -inst *
globalNetConnect VSS -type tielo -pin $gnd_port -inst *
globalNetConnect VSS -type net -net VSS
""" % (
    self.configs.get('pwr_port'),
    self.configs.get('gnd_port'),
)
        """
            Add power stripes between lower-level power rails and higher-level power net.
            Here we just add one horizontal layer and one vertical layer.
            (Double check asap7 lef for correct layer direction)
            TODO: potentially adding more stripes will benefit IR drop
        """
        codes += """
# -------------------------------------------------------------
# Add power stripes
# -------------------------------------------------------------
set stripe_width %f
set stripe_spacing %f
set stripe_distance %f

addStripe -nets {VSS VDD} \
    -layer {%s} \
    -direction vertical \
    -width $stripe_width \
    -spacing $stripe_spacing \
    -set_to_set_distance $stripe_distance \
    -start_from left \
    -uda power_stripe_v

addStripe -nets {VSS VDD} \
    -layer {%s} \
    -direction horizontal \
    -width $stripe_width \
    -spacing $stripe_spacing \
    -set_to_set_distance $stripe_distance \
    -start_from bottom \
    -uda power_stripe_h
""" % (
    self.configs.get('stripe_width'),
    self.configs.get('stripe_spacing'),
    self.configs.get('stripe_distance'),
    self.configs.get('stripe_v_layer'),
    self.configs.get('stripe_h_layer'),
)
        """
            Add power rails
            
        """
        codes += """
# -------------------------------------------------------------
# Add power rails
# -------------------------------------------------------------
set sroute_min_layer %s
set sroute_max_layer %s
set sroute_core_pin_target %s
set sroute_block_pin_target %s
sroute -connect { corePin blockPin } \
    -layerChangeRange " $sroute_min_layer $sroute_max_layer " \
    -corePinTarget $sroute_core_pin_target \
    -blockPinTarget $sroute_block_pin_target \
    -allowJogging 1 \
    -crossoverViaLayerRange " $sroute_min_layer $sroute_max_layer " \
    -nets { VDD VSS } \
    -allowLayerChange 1 \
    -targetViaLayerRange " $sroute_min_layer $sroute_max_layer " \
    -uda power_rail
""" % (
    self.configs.get('sroute_min_layer'),
    self.configs.get('sroute_max_layer'),
    self.configs.get('sroute_core_pin_target', 'stripe'),
    self.configs.get('sroute_block_pin_target', 'stripe'),
)
        """
            Verify connect violation
        """        
        codes += """
verifyConnectivity -type special \
    -noAntenna \
    -noWeakConnect \
    -noUnroutedNet \
    -error 1000 \
    -warning 50 \
    -report %s
verify_PG_short -no_routing_blkg -report %s
set tp_require_pg_clean %s
if {$tp_require_pg_clean} {
    set tp_pg_report %s
    set tp_pg_fh [open $tp_pg_report r]
    set tp_pg_text [read $tp_pg_fh]
    close $tp_pg_fh
    if {![regexp {Verification Complete[ ]*:[ ]*0[ ]+Viols} $tp_pg_text]} {
        error "PG special-net connectivity is not clean; expected 0 Viols in $tp_pg_report"
    }
}
""" % (
    os.path.join(self.report_dir, 'powerplan_connectivity.rpt'),
    os.path.join(self.report_dir, 'powerplan_PG_short.rpt'),
    'true' if self.configs.get('require_pg_clean', True) else 'false',
    os.path.join(self.report_dir, 'powerplan_connectivity.rpt'),
)
        return codes

    def generate_placement_code(self) -> str:
        """
            Generate placement script
        """
        codes = ""
        
        codes += """
# -------------------------------------------------------------
# Default path group settings
# -------------------------------------------------------------
reset_path_group -all

set input [all_inputs]
set output [all_outputs]
set reg [filter_collection [all_registers] "is_integrated_clock_gating_cell != true"]
set ckgating [filter_collection [all_registers] "is_integrated_clock_gating_cell == true"]
set ignore_path_groups [list inp2reg reg2out reg2out feedthr]

# default path group definition
group_path -name reg2reg -from $reg -to $reg
group_path -name reg2cg -from $reg -to $ckgating
group_path -name in2reg -from $input
group_path -name reg2out -to $output
group_path -name feedthr -from $input -to $output

# default path group effort level
setPathGroupOptions reg2reg -effortLevel high
setPathGroupOptions reg2cg -effortLevel high
setPathGroupOptions in2reg -effortLevel low
setPathGroupOptions reg2out -effortLevel low
setPathGroupOptions feedthr -effortLevel low
setOptMode -ignorePathGroupsForHold $ignore_path_groups
"""

        # TODO: there're options eliminating IR Drop
        codes += """
# -------------------------------------------------------------
# Placement Mode settings
# -------------------------------------------------------------        
setPlaceMode -reset
setPlaceMode -place_global_ignore_scan true
setDesignMode -topRoutingLayer %s
setDesignMode -bottomRoutingLayer %s

# customized detailed placement options
setPlaceMode -place_detail_eco_max_distance %.1f
setPlaceMode -place_detail_eco_priority_insts %s
setPlaceMode -place_detail_activity_power_driven %s
setPlaceMode -place_detail_wire_length_opt_effort %s
setPlaceMode -place_detail_legalization_inst_gap %d

# customized global placement options
setPlaceMode -place_global_auto_blockage_in_channel %s
setPlaceMode -place_global_activity_power_driven %s
setPlaceMode -place_global_activity_power_driven_effort %s
setPlaceMode -place_global_clock_power_driven %s
setPlaceMode -place_global_clock_power_driven_effort %s
setPlaceMode -place_global_timing_effort %s
setPlaceMode -place_global_cong_effort %s
setPlaceMode -place_global_max_density %.3f
setPlaceMode -place_global_clock_gate_aware %s
setPlaceMode -place_global_uniform_density %s
""" % (
    self.configs.get('route_max_layer'),  # early global routing use same layer as detailed routing
    self.configs.get('route_min_layer'),
    # self.configs.get('process_node', ''),

    self.configs.get('place_detail_eco_max_distance', 10.0),            # 0 ~ 999, unit: micron
    self.configs.get('place_detail_eco_priority_insts', 'placed'),      # { placed | fixed | eco }
    self.configs.get('place_detail_activity_power_driven', 'false'),    # { true | false }
    self.configs.get('place_detail_wire_length_opt_effort', 'medium'),  # { none | medium | high }
    self.configs.get('place_detail_legalization_inst_gap', 0),          # 0 ~ 999, unit: micron

    self.configs.get('place_global_auto_blockage_in_channel', 'none'),  # { none | soft | partial }
    self.configs.get('place_global_activity_power_driven', 'false'),    # { true | false }
    self.configs.get('place_global_activity_power_driven_effort', 'standard'),  # { none | standard | high }
    self.configs.get('place_global_clock_power_driven', 'true'),        # { true | false }
    self.configs.get('place_global_clock_power_driven_effort', 'low'),  # { low | standard | high }
    self.configs.get('place_global_timing_effort', 'medium'),           # { medium | high }
    self.configs.get('place_global_cong_effort', 'auto'),               # { low | medium | high | auto }
    self.configs.get('place_global_max_density', -1.000),               # 0 ~ 1
    self.configs.get('place_global_clock_gate_aware', 'true'),          # { true | false }
    self.configs.get('place_global_uniform_density', 'false'),          # { true | false }
)

        codes += """
# -------------------------------------------------------------
# place the design & report congestion
# -------------------------------------------------------------
place_opt_design
reportCongestion -overflow
""" 
        codes += self.generate_timing_report_code(stage='preCTS')
        codes += self.generate_area_report_code(stage='preCTS')
        codes += self.generate_power_report_code(stage='preCTS')
        
        return codes

    def generate_cts_code(self) -> str:
        """
            Generate CTS script
        """
        codes = ""

        cts_inv_cells = map(lambda x: ('*/' + x) if not x.startswith('*/') else x, self.configs.get('cts_inv_cells', []))
        cts_inv_cells = ' '.join(cts_inv_cells)

        codes += """
# -------------------------------------------------------------
# set cts opt use cells
# -------------------------------------------------------------
set_ccopt_property use_inverters true
# FIXME: get_lib_cells have strange return values
# set cts_inv_cells [list %s]
# foreach lib_cell $cts_inv_cells {
#     setDontUse $lib_cell false
# }
# set_ccopt_property inverter_cells [get_db lib_cells $cts_inv_cells]
""" % cts_inv_cells
        
        codes += """
# -------------------------------------------------------------
# clk net routing non-default rule setting
# -------------------------------------------------------------
set mul %.2f
set ndr_cts_min_layer %s
set ndr_cts_max_layer %s
add_ndr -name cts_1 \
    -width_multiplier "$ndr_cts_min_layer:$ndr_cts_max_layer $mul" \
    -spacing_multiplier "$ndr_cts_min_layer:$ndr_cts_max_layer $mul"
create_route_type -name clk_net_rule \
    -non_default_rule cts_1 \
    -top_preferred_layer $ndr_cts_max_layer \
    -bottom_preferred_layer $ndr_cts_min_layer
set_ccopt_property -route_type clk_net_rule -net_type trunk
""" % (
    self.configs.get('cts_routing_mul', 2),
    self.configs.get('ndr_cts_min_layer'),
    self.configs.get('ndr_cts_max_layer'),
)

        codes += """
# -------------------------------------------------------------
# create cts
# -------------------------------------------------------------
create_ccopt_clock_tree_spec -file %s
source %s
""" % (
    os.path.join(self.data_dir, 'clk.spec'),
    os.path.join(self.data_dir, 'clk.spec'),
)
        
        cts_command = self.configs.get('cts_command', 'clock_opt_design')
        codes += """
# -------------------------------------------------------------
# run CTS
# -------------------------------------------------------------
%s
report_ccopt_skew_groups
""" % cts_command
        
        codes += """
# -------------------------------------------------------------
# post cts opt
# -------------------------------------------------------------
set_interactive_constraint_modes [all_constraint_modes -active]
set_propagated_clock [all_clocks]
setOptMode -fixDrc true -fixFanoutLoad true

optDesign -postCTS
optDesign -postCTS -hold
"""
        codes += self.generate_timing_report_code(stage='postCTS')

        return codes

    def generate_routing_code(self) -> str:
        """
            Generate routing script
        """
        codes = ""

        codes += """
# -------------------------------------------------------------
# NanoRoute Mode setting
# -------------------------------------------------------------
setMultiCpuUsage -localCpu %d
setAnalysisMode -analysisType onChipVariation
setDesignMode -topRoutingLayer %s
setDesignMode -bottomRoutingLayer %s

# FIXME: many routing configuration still missing!
#        They are now just copied from the example script
setNanoRouteMode -quiet -drouteEndIteration %d
setNanoRouteMode -quiet -drouteFixAntenna %s
setNanoRouteMode -quiet -drouteUseMultiCutViaEffort %s
setNanoRouteMode -quiet -drouteMinSlackForWireOptimization %.3f
setDelayCalMode -engine %s -siAware %s
""" % (
    self.configs.get('route_max_threads', self.configs.get('max_threads', 8)),
    self.configs.get('route_max_layer'),
    self.configs.get('route_min_layer'),
    self.configs.get('droute_end_iteration', 20),
    'true' if self.configs.get('droute_fix_antenna', True) else 'false',
    self.configs.get('droute_multicut_via_effort', 'medium'),
    self.configs.get('droute_min_slack_for_wire_optimization', 0.1),
    self.configs.get('route_delay_engine', 'default'),
    'true' if self.configs.get('route_si_aware', True) else 'false',
)

        codes += """
# -------------------------------------------------------------
# Route Design
# -------------------------------------------------------------
routeDesign -globalDetail
"""
        
        codes += """
# -------------------------------------------------------------
# post routing opt
# -------------------------------------------------------------
optDesign -postRoute -setup
"""
        codes += self.generate_timing_report_code(stage='postRoute')
        codes += self.generate_area_report_code(stage='postRoute')
        codes += self.generate_power_report_code(stage='postRoute')
        codes += """
# -------------------------------------------------------------
# Export routed implementation artifacts
# -------------------------------------------------------------
defOut -routing %s
saveNetlist %s
write_sdf %s
rcOut -spef %s
verify_drc -report %s
verifyConnectivity -type all -error 1000 -warning 50 -report %s
streamOut %s -mapFile %s -merge { %s } -mode ALL
""" % (
            self.routed_def_path,
            self.routed_verilog_path,
            self.routed_sdf_path,
            self.routed_spef_path,
            os.path.join(self.report_dir, 'postRoute_drc.rpt'),
            os.path.join(self.report_dir, 'postRoute_connectivity.rpt'),
            self.routed_gds_path,
            self.configs.get('stream_layer_map'),
            self.get_file_list('gds_files'),
        )


        return codes

    def generate_timing_report_code(self, stage: str) -> str:
        """
            Timing report code, reused in multiple stages ()
        """
        assert stage in ('prePlace', 'preCTS', 'postCTS', 'postRoute')

        timing_report_dir = os.path.join(self.report_dir, f'{stage}_timing')

        codes = """
# -------------------------------------------------------------
# Report design timing
# -------------------------------------------------------------
set report_dir %s

timeDesign -%s \
  -pathReports \
  -drvReports \
  -slackReports \
  -numPaths 50 \
  -prefix %s \
  -outDir ${report_dir}     

report_timing -nworst 1 -machine_readable > ${report_dir}/timing.rpt   
""" % (
    timing_report_dir,
    stage,
    stage,
)
        codes += """
# -------------------------------------------------------------
# Report path group timing
# -------------------------------------------------------------
"""
        for path_group in self.configs.get('path_groups', []):
                if path_group.get('report', False):
                    codes += """
report_timing -from %s -to %s -nworst 1 -machine_readable > ${report_dir}/group_timing_%s.rpt
""" % (
    path_group.get('from'),
    path_group.get('to'),
    path_group.get('name'),
)
        return codes
    
    def generate_area_report_code(self, stage: str) -> str:
        """
            Area report code
        """

        area_report_path = os.path.join(self.report_dir, f'{stage}_area.rpt')
        
        codes = """
# -------------------------------------------------------------
# Report area
# -------------------------------------------------------------
report_area -detail > %s
""" % area_report_path
        return codes

    def generate_power_report_code(self, stage: str) -> str:
        power_report_path = os.path.join(self.report_dir, f'{stage}_power.rpt')

        codes = """

# -------------------------------------------------------------
# Report area
# -------------------------------------------------------------
report_power -hierarchy all > %s
""" % power_report_path

        return codes