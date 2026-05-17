# Stage 2 initial timing target: 500 MHz (2.000 ns)
create_clock [get_ports clock] -name clock -period 2.000
set_clock_uncertainty 0.10 [get_clocks clock]
set_input_delay 0.20 -clock [get_clocks clock] [all_inputs]
set_output_delay 0.20 -clock [get_clocks clock] [all_outputs]
