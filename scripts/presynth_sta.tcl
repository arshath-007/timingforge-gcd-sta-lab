# Post-synthesis STA on the exact ORFS 1_2_yosys.v mapped netlist.
foreach name {LIBERTY NETLIST SDC TOP} {
    if {![info exists ::env($name)]} {
        error "Set $name for ORFS post-synthesis STA"
    }
}
read_liberty $::env(LIBERTY)
read_verilog $::env(NETLIST)
link_design $::env(TOP)
read_sdc $::env(SDC)

puts "=== ORFS POST-SYNTHESIS SETUP CHECK ==="
check_setup -verbose -no_input_delay -no_output_delay -multiple_clock -no_clock -unconstrained_endpoints -loops -generated_clocks
puts "=== ORFS POST-SYNTHESIS CLOCK PROPERTIES ==="
report_clock_properties
puts "=== ORFS POST-SYNTHESIS REGISTER-TO-REGISTER CLOCK PERIOD ==="
report_clock_min_period
puts "=== ORFS POST-SYNTHESIS ALL-PATH CLOCK PERIOD ==="
report_clock_min_period -include_port_paths
puts "=== ORFS POST-SYNTHESIS SETUP SUMMARY ==="
report_worst_slack -max -digits 3
report_wns -max -digits 3
report_tns -max -digits 3
puts "=== ORFS POST-SYNTHESIS HOLD SUMMARY ==="
report_worst_slack -min -digits 3
report_wns -min -digits 3
report_tns -min -digits 3
puts "=== ORFS POST-SYNTHESIS SETUP PATHS ==="
report_checks -path_delay max -format full_clock_expanded -group_path_count 10 -digits 3
puts "=== ORFS POST-SYNTHESIS HOLD PATHS ==="
report_checks -path_delay min -format full_clock_expanded -group_path_count 10 -digits 3
