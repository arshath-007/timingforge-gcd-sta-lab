export DESIGN_NAME = gcd_binary_combined
export PLATFORM = nangate45
export VERILOG_FILES = $(DESIGN_REPO_ROOT)/rtl/gcd_binary_combined.sv
export SDC_FILE = $(DESIGN_REPO_ROOT)/constraints/gcd_baseline.sdc

# Same interface timing model and floorplan policy as the split architecture.
# ORFS synthesis policy differs from the pre-layout synthesis script, so this
# physical run is not a netlist-matched pre-layout/post-route experiment.
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 5
export PLACE_DENSITY = 0.60
export TNS_END_PERCENT = 100
export ABC_AREA = 1
