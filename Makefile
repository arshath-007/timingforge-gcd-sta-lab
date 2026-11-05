PYTHON ?= python3
IVERILOG ?= iverilog
VVP ?= vvp

.PHONY: help rtl-test ip-block-test mutants lint-sdc python-test benchmark synth sta sta-matrix sta-quality sensitivity clean

help:
	@echo "Targets: rtl-test ip-block-test mutants lint-sdc python-test benchmark synth sta sta-matrix sta-quality clean"

ip-block-test:
	mkdir -p build
	$(IVERILOG) -g2012 -s tb_sync_fifo -o build/tb_sync_fifo.vvp rtl/sync_fifo.sv tb/tb_sync_fifo.sv
	$(VVP) build/tb_sync_fifo.vvp
	$(IVERILOG) -g2012 -s tb_mac_accumulator -o build/tb_mac_accumulator.vvp rtl/mac_accumulator.sv tb/tb_mac_accumulator.sv
	$(VVP) build/tb_mac_accumulator.vvp

rtl-test:
	mkdir -p build
	$(IVERILOG) -g2012 -s tb_gcd_compare -o build/tb_gcd_compare.vvp rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv tb/tb_gcd_compare.sv
	$(VVP) build/tb_gcd_compare.vvp

mutants:
	$(PYTHON) tools/make_mutants.py

lint-sdc:
	$(PYTHON) tools/lint_sdc.py constraints/gcd_baseline.sdc

python-test:
	$(PYTHON) -m unittest discover -s tests -v

benchmark: mutants
	$(PYTHON) -m tools.run_benchmark

synth:
	bash scripts/synth.sh

sta:
	bash scripts/run_sta.sh

sta-matrix:
	bash scripts/run_nangate_sta.sh

sta-quality: sta-matrix
	$(PYTHON) -m tools.quality_checks build/reports/sta_matrix_summary.json --output build/reports/sta_quality_findings.json

sensitivity: sta-matrix
	$(PYTHON) -m tools.run_sensitivity

clean:
	rm -rf build
