# Post-route STA using the final OpenROAD database and extracted SPEF.
# Required environment: LIBERTY, TECH_LEF, SC_LEF, ODB, SDC, SPEF.
foreach name {LIBERTY TECH_LEF SC_LEF ODB SDC SPEF} {
    if {![info exists ::env($name)]} {
        error "Set $name for extracted-parasitic post-route STA"
    }
}
read_lef $::env(TECH_LEF)
read_lef $::env(SC_LEF)
read_liberty $::env(LIBERTY)
read_db $::env(ODB)
read_sdc $::env(SDC)
set_propagated_clock [all_clocks]
read_spef $::env(SPEF)

puts "=== TIMINGFORGE POST-ROUTE SETUP CHECK ==="
check_setup -verbose
puts "=== POST-ROUTE CLOCK PROPERTIES ==="
report_clock_properties
puts "=== POST-ROUTE CLOCK PERIOD ==="
report_clock_min_period
puts "=== POST-ROUTE SETUP SUMMARY ==="
report_worst_slack -max -digits 3
report_wns -max -digits 3
report_tns -max -digits 3
puts "=== POST-ROUTE SETUP PATHS ==="
report_checks -path_delay max -format full_clock_expanded -group_path_count 20 -digits 3
puts "=== POST-ROUTE HOLD SUMMARY ==="
report_worst_slack -min -digits 3
report_wns -min -digits 3
report_tns -min -digits 3
puts "=== POST-ROUTE HOLD PATHS ==="
report_checks -path_delay min -format full_clock_expanded -group_path_count 20 -digits 3
puts "=== POST-ROUTE DRV ==="
foreach check {max_slew max_capacitance max_fanout} {
    if {[catch {report_check_types -$check -violators -verbose -digits 3} err]} {
        puts "TIMINGFORGE_DRV_UNSUPPORTED: $check: $err"
    }
}
puts "=== POST-ROUTE PARASITICS LOADED ==="
puts "SPEF=$::env(SPEF)"
