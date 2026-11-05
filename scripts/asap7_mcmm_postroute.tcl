# True OpenSTA MCMM post-route analysis for ASAP7 BC/TC/WC Liberty scenes.
# One TC-routed design and one extracted SPEF are reused across scenes; the
# parasitics are NOT corner-specific and no RC-corner scaling is applied.
foreach name {TECH_LEF SC_LEF ODB SDC SPEF ASAP7_LIB_DIR} {
    if {![info exists ::env($name)]} {
        error "Set $name for ASAP7 MCMM post-route analysis"
    }
}
read_lef $::env(TECH_LEF)
read_lef $::env(SC_LEF)

set libdir $::env(ASAP7_LIB_DIR)
proc corner_libs {libdir process_tag} {
    set libs {}
    foreach group {AO INVBUF OA SIMPLE} {
        set matches [glob -nocomplain "$libdir/asap7sc7p5t_${group}_RVT_${process_tag}_nldm_*.lib.gz"]
        if {[llength $matches] != 1} {
            error "Expected one ASAP7 ${group} library for ${process_tag}; found [llength $matches]"
        }
        lappend libs [lindex $matches 0]
    }
    set seq [glob -nocomplain "$libdir/asap7sc7p5t_SEQ_RVT_${process_tag}_nldm_*.lib"]
    if {[llength $seq] != 1} {
        error "Expected one ASAP7 sequential library for ${process_tag}; found [llength $seq]"
    }
    lappend libs [lindex $seq 0]
    return [lsort $libs]
}

set bc_libs [corner_libs $libdir FF]
set tc_libs [corner_libs $libdir TT]
set wc_libs [corner_libs $libdir SS]
foreach lib [concat $bc_libs $tc_libs $wc_libs] {
    read_liberty $lib
}
read_db $::env(ODB)
read_sdc -mode functional $::env(SDC)
read_spef -name shared_tc_extracted $::env(SPEF)
set_propagated_clock [all_clocks]

define_scene ASAP7_BC -mode functional -liberty $bc_libs -spef shared_tc_extracted
define_scene ASAP7_TC -mode functional -liberty $tc_libs -spef shared_tc_extracted
define_scene ASAP7_WC -mode functional -liberty $wc_libs -spef shared_tc_extracted

puts "=== TIMINGFORGE ASAP7 MCMM METADATA ==="
puts "ASAP7 PVT: BC=FF/25C/0.77V; TC=TT/0C/0.70V; WC=SS/100C/0.63V"
puts "ASAP7 RC: same TC-extracted SPEF reused for BC, TC and WC; no corner-specific RC scaling"
report_units
report_clock_properties
check_setup -verbose

foreach scene {ASAP7_BC ASAP7_TC ASAP7_WC} {
    puts "TIMINGFORGE_SCENE_BEGIN $scene"
    puts "TIMINGFORGE_SETUP_BEGIN $scene"
    report_checks -path_delay max -scenes $scene -group_path_count 1000 -format full_clock_expanded -digits 3
    puts "TIMINGFORGE_SETUP_END $scene"
    puts "TIMINGFORGE_HOLD_BEGIN $scene"
    report_checks -path_delay min -scenes $scene -group_path_count 1000 -format full_clock_expanded -digits 3
    puts "TIMINGFORGE_HOLD_END $scene"
    puts "TIMINGFORGE_DRV_BEGIN $scene"
    report_check_types -scenes $scene -max_slew -max_capacitance -max_fanout -violators -verbose -digits 3
    puts "TIMINGFORGE_DRV_END $scene"
    puts "TIMINGFORGE_SETUP_SKEW_BEGIN $scene"
    report_clock_skew -setup -scenes $scene -digits 3
    puts "TIMINGFORGE_SETUP_SKEW_END $scene"
    puts "TIMINGFORGE_HOLD_SKEW_BEGIN $scene"
    report_clock_skew -hold -scenes $scene -digits 3
    puts "TIMINGFORGE_HOLD_SKEW_END $scene"
    puts "TIMINGFORGE_SCENE_END $scene"
}
puts "TIMINGFORGE_ASAP7_MCMM_COMPLETE"
