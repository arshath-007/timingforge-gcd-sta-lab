# True OpenSTA MCMM post-route analysis for ASAP7 BC/TC/WC Liberty scenes.
# One TC-routed design and one extracted SPEF are reused across scenes; the
# parasitics are NOT corner-specific and no RC-corner scaling is applied.
foreach name {TECH_LEF SC_LEF ODB SDC SPEF ASAP7_LIB_DIR ASAP7_FILTERED_LIB_DIR} {
    if {![info exists ::env($name)]} {
        error "Set $name for ASAP7 MCMM post-route analysis"
    }
}
read_lef $::env(TECH_LEF)
read_lef $::env(SC_LEF)

set libdir $::env(ASAP7_LIB_DIR)
proc corner_libs {libdir process_tag} {
    set libs {}
    set versions [dict create AO 211120 INVBUF 220122 OA 211120 SIMPLE 211120]
    foreach group {AO INVBUF OA} {
        set version [dict get $versions $group]
        set path "$libdir/asap7sc7p5t_${group}_RVT_${process_tag}_nldm_${version}.lib.gz"
        if {![file isfile $path]} {
            error "Missing pinned ASAP7 ${group}/${process_tag} Liberty: $path"
        }
        lappend libs $path
    }
    set simple "$::env(ASAP7_FILTERED_LIB_DIR)/asap7sc7p5t_SIMPLE_RVT_${process_tag}_nldm_211120.filtered.lib"
    if {![file isfile $simple]} {
        error "Missing filtered ASAP7 SIMPLE Liberty: $simple"
    }
    lappend libs $simple
    set seq "$libdir/asap7sc7p5t_SEQ_RVT_${process_tag}_nldm_220123.lib"
    if {![file isfile $seq]} {
        error "Missing pinned ASAP7 sequential Liberty: $seq"
    }
    lappend libs $seq
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
puts "ASAP7 Liberty nominal PVT: BC=FF/0C/0.77V; TC=TT/25C/0.70V; WC=SS/100C/0.63V"
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
