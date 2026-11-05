# Advanced SDC Exercises: Generated Clocks and Multicycle Paths

These are learning templates for a future benchmark extension. They are not applied to the current single-clock GCD baseline because the current RTL does not establish a divided/generated clock domain or a verified multicycle data-transfer protocol.

## 1. Generated-clock exercise

A generated clock must be tied to a real clock-generating pin in the implemented design. Replace the illustrative hierarchy with the actual divider or clock-generator output pin.

```tcl
create_clock -name root_clk -period 10.000 [get_ports clk]
create_generated_clock -name divided_clk \
    -source [get_ports clk] \
    -divide_by 2 \
    [get_pins u_clock_divider/clk_out]
```

Review checklist:
- Confirm the target pin exists in the linked netlist.
- Confirm the source clock and generated waveform match the actual implementation.
- Confirm all registers in the generated domain receive the intended clock.
- Inspect clock propagation and cross-domain paths; do not use a generated clock as a substitute for CDC design.

## 2. Multicycle-path exercise

A multicycle exception is valid only when the RTL protocol guarantees that the receiving register is intended to capture the launched data after multiple active clock edges. The following is an illustrative two-cycle setup exception; the matching hold adjustment must be considered and verified against the timing intent.

```tcl
set_multicycle_path 2 -setup \
    -from [get_pins u_source_reg/Q] \
    -to [get_pins u_destination_reg/D]
set_multicycle_path 1 -hold \
    -from [get_pins u_source_reg/Q] \
    -to [get_pins u_destination_reg/D]
```

Review checklist:
- Prove the capture enable or protocol prevents an early capture.
- Scope the exception to exact launch and capture points.
- Review both setup and hold effects.
- Compare reports before and after the exception.
- Reject broad exceptions that silence unrelated paths.

## 3. Future mutation ideas

| Mutation | Intended check | Why it matters |
|---|---|---|
| M08 missing generated clock | Required generated clock exists and reaches expected endpoints | Prevents generated-clock domain paths from being omitted |
| M09 wrong generated-clock source | Source pin and divide/multiply relationship match design intent | Prevents a plausible but incorrect clock definition |
| M10 unjustified multicycle setup | Every multicycle path has a documented protocol justification | Prevents false timing relaxation |
| M11 missing multicycle hold companion | Setup/hold exception pair is reviewed together | Prevents accidental hold-budget changes |

The current Python SDC checker does not yet parse or validate these advanced constructs. These cases are design proposals, not counted as passing mutations. A future implementation should use an SDC/Tcl-aware parser or validate constraints in the timing engine against a purpose-built multi-clock RTL example.
