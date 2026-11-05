# TimingForge illustrative block-level SDC baseline.
# Educational assumptions only; derive real interface budgets for real designs.
create_clock -name core_clk -period 10.000 [get_ports clk]
set_clock_uncertainty -setup 0.150 [get_clocks core_clk]
set_clock_uncertainty -hold 0.050 [get_clocks core_clk]
set_clock_transition 0.050 [get_clocks core_clk]

# Synchronous reset is timed like the other input controls in this example.
set_input_delay -clock core_clk -max 1.200 [get_ports start]
set_input_delay -clock core_clk -min 0.100 [get_ports start]
set_input_delay -clock core_clk -max 1.500 [get_ports a_in*]
set_input_delay -clock core_clk -min 0.100 [get_ports a_in*]
set_input_delay -clock core_clk -max 1.500 [get_ports b_in*]
set_input_delay -clock core_clk -min 0.100 [get_ports b_in*]
set_input_delay -clock core_clk -max 0.500 [get_ports rst]
set_input_delay -clock core_clk -min 0.050 [get_ports rst]

set_output_delay -clock core_clk -max 1.000 [get_ports done]
set_output_delay -clock core_clk -min 0.100 [get_ports done]
set_output_delay -clock core_clk -max 1.000 [get_ports busy]
set_output_delay -clock core_clk -min 0.100 [get_ports busy]
set_output_delay -clock core_clk -max 1.500 [get_ports gcd_out*]
set_output_delay -clock core_clk -min 0.100 [get_ports gcd_out*]
set_load 20 [get_ports done]
set_load 20 [get_ports busy]
set_load 30 [get_ports gcd_out*]
set_input_transition 0.050 [get_ports {start rst a_in* b_in*}]
