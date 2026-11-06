"""Classify OpenSTA unannotated driver pins against the final routed netlist.

OpenSTA's report lists unannotated *drivers*, including dangling cell output pins.
Dangling pins are not routed nets and correctly have no SPEF network. This helper
fails closed if a reported driver is connected to a net with any sink/port use.
"""
from __future__ import annotations

import re
from pathlib import Path

CELL_RE = re.compile(r"(?ms)^\s*([A-Za-z_][A-Za-z0-9_$]*)\s+(\\?[^\s(]+)\s*\((.*?)\);")
PORT_RE = re.compile(r"\.(\w+)\s*\(\s*([^()]*)\s*\)")
COUNT_RE = re.compile(r"Found\s+(\d+)\s+(unannotated|partially\s+unannotated)\s+drivers?", re.IGNORECASE)


def _normalise_name(value: str) -> str:
    return value.strip().replace("\\", "")


def classify_annotation(log_path: Path, netlist_path: Path) -> dict:
    log = log_path.read_text(encoding="utf-8", errors="replace")
    annotation_parts = log.split("=== POST-ROUTE PARASITIC ANNOTATION ===", 1)
    if len(annotation_parts) != 2:
        raise ValueError(f"{log_path}: parasitic annotation section missing")
    annotation = annotation_parts[1].split("=== TIMINGFORGE POST-ROUTE SETUP CHECK ===", 1)[0]
    counts = {name: int(value) for value, name in COUNT_RE.findall(annotation)}
    if "unannotated" not in counts or "partially unannotated" not in counts:
        raise ValueError(f"{log_path}: annotation report must include both driver counts")
    partial = counts["partially unannotated"]
    if partial:
        raise ValueError(f"{log_path}: {partial} partially unannotated parasitic drivers")
    netlist = netlist_path.read_text(encoding="utf-8", errors="replace")
    pin_nets = {}
    instances = set()
    for cell in CELL_RE.finditer(netlist):
        instance = _normalise_name(cell.group(2))
        instances.add(instance)
        for pin, connection in PORT_RE.findall(cell.group(3)):
            pin_nets[(instance, pin)] = connection.strip()
    unannotated_names = []
    for line in annotation.splitlines():
        line = line.strip()
        if not line or line.startswith("Found "):
            continue
        unannotated_names.append(line)
    if len(unannotated_names) != counts["unannotated"]:
        raise ValueError(
            f"{log_path}: report lists {len(unannotated_names)} unannotated drivers "
            f"but summary says {counts['unannotated']}"
        )
    dangling = []
    connected = []
    unresolved = []
    for driver in unannotated_names:
        if "/" not in driver:
            unresolved.append(driver)
            continue
        instance, pin = driver.rsplit("/", 1)
        key = (_normalise_name(instance), pin)
        if key not in pin_nets:
            if key[0] in instances:
                dangling.append(driver)  # output port is omitted from the Verilog instance
            else:
                unresolved.append(driver)
            continue
        net = pin_nets[key]
        if not net:
            dangling.append(driver)
            continue
        net = _normalise_name(net)
        # A declaration plus the driver connection are the only references
        # for a dangling output. Any further token use indicates a sink or port.
        refs = re.findall(r"(?<![A-Za-z0-9_$])" + re.escape(net) + r"(?![A-Za-z0-9_$])", netlist)
        port_base = net.split("[", 1)[0]
        is_port = re.search(
            r"\b(?:input|output|inout)\b[^;]*\b" + re.escape(port_base) + r"\b",
            netlist,
            re.IGNORECASE,
        )
        if len(refs) <= 2 and not is_port:
            dangling.append(driver)
        else:
            connected.append({"driver": driver, "net": net, "net_references": len(refs)})
    if unresolved:
        raise ValueError(f"{log_path}: could not classify unannotated driver pins: {unresolved[:10]}")
    if connected:
        raise ValueError(
            f"{log_path}: {len(connected)} unannotated drivers are connected to routed nets; "
            f"examples: {connected[:5]}"
        )
    return {
        "reported_unannotated_driver_count": counts["unannotated"],
        "partially_unannotated_driver_count": partial,
        "dangling_unannotated_driver_count": len(dangling),
        "unannotated_connected_driver_count": len(connected),
        "unannotated_driver_classification": "all reported unannotated drivers are dangling cell outputs with no net sinks",
        "dangling_driver_names": dangling,
    }
