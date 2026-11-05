PYTHON ?= python3
IVERILOG ?= iverilog
VVP ?= vvp

.PHONY: help rtl-test mutants lint-sdc python-test benchmark synth sta sta-matrix clean

help:
	@echo "Targets: rtl-test mutants lint-sdc python-test benchmark synth sta sta-matrix clean"

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

clean:
	rm -rf build
