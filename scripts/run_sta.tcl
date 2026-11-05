# OpenSTA script for a mapped GCD netlist.
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
check_setup -verbose
puts "=== MAX / SETUP PATHS ==="
report_checks -path_delay max -format full_clock_expanded -digits 3
puts "=== MIN / HOLD PATHS ==="
report_checks -path_delay min -format full_clock_expanded -digits 3
puts "=== UNCONSTRAINED PATHS ==="
report_checks -unconstrained -digits 3
