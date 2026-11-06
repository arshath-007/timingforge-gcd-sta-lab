# OpenSTA/OpenROAD-integrated STA script for a mapped GCD netlist.
# Required environment: LIBERTY, NETLIST, SDC. Optional: TOP.
if {![info exists ::env(LIBERTY)]} { error "Set LIBERTY to a standard-cell Liberty file" }
if {![info exists ::env(NETLIST)]} { error "Set NETLIST to a mapped Verilog netlist" }
if {![info exists ::env(SDC)]} { error "Set SDC to an SDC file" }
set top "gcd_binary_combined"
if {[info exists ::env(TOP)]} { set top $::env(TOP) }

# OpenROAD's database also needs technology and standard-cell LEF files.
# Standalone OpenSTA can omit these LEFs and use Liberty/Verilog/SDC only.
if {[info exists ::env(TECH_LEF)]} {
    read_lef $::env(TECH_LEF)
}
if {[info exists ::env(SC_LEF)]} {
    read_lef $::env(SC_LEF)
}
read_liberty $::env(LIBERTY)
read_verilog $::env(NETLIST)
link_design $top
read_sdc $::env(SDC)

puts "=== TIMINGFORGE SETUP CHECK ==="
check_setup -verbose -no_input_delay -no_output_delay -multiple_clock -no_clock -unconstrained_endpoints -loops -generated_clocks
puts "=== REGISTER-TO-REGISTER CLOCK PERIOD / FREQUENCY ==="
report_clock_min_period
puts "=== ALL-PATH CLOCK PERIOD / FREQUENCY (INCLUDING PORT PATHS) ==="
report_clock_min_period -include_port_paths
puts "=== SETUP SUMMARY ==="
report_worst_slack -max -digits 3
report_wns -max -digits 3
report_tns -max -digits 3
puts "=== HOLD SUMMARY ==="
report_worst_slack -min -digits 3
report_wns -min -digits 3
report_tns -min -digits 3
puts "=== SETUP / MAX PATH DETAILS ==="
report_checks -path_delay max -format full_clock_expanded -digits 3
puts "=== REGISTER-TO-REGISTER SETUP PATHS ==="
report_checks -from [all_registers -output_pins] -to [all_registers -data_pins] -path_delay max -format full_clock_expanded -group_path_count 10 -digits 3
puts "=== RISING-EDGE REGISTER-TO-REGISTER SETUP PATHS ==="
set reg_path_count 100
if {[file tail $::env(SDC)] == "gcd_baseline.sdc"} {
    set reg_path_count 1000
}
report_checks -from [all_registers -rise_clock core_clk -output_pins] -to [all_registers -rise_clock core_clk -data_pins] -path_delay max -format full_clock_expanded -group_path_count $reg_path_count -digits 3
puts "=== CLOCK PROPERTIES ==="
report_clock_properties
puts "=== HOLD / MIN PATH DETAILS ==="
report_checks -path_delay min -format full_clock_expanded -digits 3
puts "=== DRV MAX SLEW ==="
if {[catch {report_check_types -max_slew -violators -verbose -digits 3} drv_error]} {
    puts "TIMINGFORGE_DRV_UNSUPPORTED: max_slew: $drv_error"
}
puts "=== DRV MAX CAPACITANCE ==="
if {[catch {report_check_types -max_capacitance -violators -verbose -digits 3} drv_error]} {
    puts "TIMINGFORGE_DRV_UNSUPPORTED: max_capacitance: $drv_error"
}
puts "=== DRV MAX FANOUT ==="
if {[catch {report_check_types -max_fanout -violators -verbose -digits 3} drv_error]} {
    puts "TIMINGFORGE_DRV_UNSUPPORTED: max_fanout: $drv_error"
}
puts "=== UNCONSTRAINED PATH DETAILS ==="
report_checks -unconstrained -digits 3
