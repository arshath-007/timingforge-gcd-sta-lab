export DESIGN_NAME = gcd_binary_combined
export PLATFORM = nangate45
export VERILOG_FILES = $(GITHUB_WORKSPACE)/rtl/gcd_binary_combined.sv
export SDC_FILE = $(GITHUB_WORKSPACE)/constraints/gcd_baseline.sdc

# Small educational block floorplan; keep the same interface timing model as
# the pre-layout STA matrix so the two stages remain directly comparable.
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 5
export PLACE_DENSITY = 0.60
export TNS_END_PERCENT = 100
export ABC_AREA = 1
