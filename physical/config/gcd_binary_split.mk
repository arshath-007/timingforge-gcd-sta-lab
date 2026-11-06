export DESIGN_NAME = gcd_binary_split
export PLATFORM = nangate45
export VERILOG_FILES = $(DESIGN_REPO_ROOT)/rtl/gcd_binary_split.sv
export SDC_FILE = $(DESIGN_REPO_ROOT)/constraints/gcd_baseline.sdc

# Keep floorplan, timing constraints, and synthesis policy matched to the
# combined architecture. This is not netlist-matched to the pre-layout flow.
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 5
export PLACE_DENSITY = 0.60
export TNS_END_PERCENT = 100
export ABC_AREA = 1
