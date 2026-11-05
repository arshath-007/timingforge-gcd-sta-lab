# OpenSTA/OpenROAD-integrated STA script for a mapped GCD netlist.
# Required environment: LIBERTY, NETLIST, SDC. Optional: TOP.
if {![info exists ::env(LIBERTY)]} { error "Set LIBERTY to a standard-cell Liberty file" }
if {![info exists ::env(NETLIST)]} { error "Set NETLIST to a mapped Verilog netlist" }
if {![info exists ::env(SDC)]} { error "Set SDC to an SDC file" }
set top "gcd_binary_combined"
if {[info exists ::env(TOP)]} { set top $::env(TOP) }

read_liberty $::env(LIBERTY)
read_verilog $::env(NETLIST)
link_design $top
read_sdc $::env(SDC)

puts "=== TIMINGFORGE SETUP CHECK ==="
check_setup -verbose -unconstrained_endpoints
puts "=== CLOCK PERIOD / FREQUENCY ==="
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
puts "=== HOLD / MIN PATH DETAILS ==="
report_checks -path_delay min -format full_clock_expanded -digits 3
puts "=== UNCONSTRAINED PATH DETAILS ==="
report_checks -unconstrained -digits 3
