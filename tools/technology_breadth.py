"""Validate and manifest TimingForge's ASAP7 MCMM and SKY130HD experiments."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TOPS = ("gcd_binary_combined", "gcd_binary_split")
ASAP7_LIB_VERSIONS = {"AO": "211120", "INVBUF": "220122", "OA": "211120", "SIMPLE": "211120", "SEQ": "220123"}
ASAP7_SCENES = {
    "ASAP7_BC": {"process": "FF", "temperature": "25C", "voltage_v": 0.77},
    "ASAP7_TC": {"process": "TT", "temperature": "0C", "voltage_v": 0.70},
    "ASAP7_WC": {"process": "SS", "temperature": "100C", "voltage_v": 0.63},
}
REQUIRED = (
    "2_floorplan.odb", "3_place.odb", "4_cts.odb", "5_route.odb",
    "6_final.odb", "6_final.v", "6_final.gds", "6_final.spef", "6_final.sdc",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_scene_report(text: str, scene: str) -> dict:
    begin = f"TIMINGFORGE_SCENE_BEGIN {scene}"
    end = f"TIMINGFORGE_SCENE_END {scene}"
    if begin not in text or end not in text:
        raise ValueError(f"missing complete MCMM scene report: {scene}")
    body = text.split(begin, 1)[1].split(end, 1)[0]
    result = {"scene": scene}
    for kind in ("SETUP", "HOLD"):
        section_begin = f"TIMINGFORGE_{kind}_BEGIN {scene}"
        section_end = f"TIMINGFORGE_{kind}_END {scene}"
        if section_begin not in body or section_end not in body:
            raise ValueError(f"missing {kind.lower()} report for {scene}")
        section = body.split(section_begin, 1)[1].split(section_end, 1)[0]
        slacks = [
            float(value) for value in re.findall(
                r"slack\s+\((?:MET|VIOLATED)\)\s+([-+]?(?:\d+\.?\d*|\.\d+))",
                section, re.IGNORECASE,
            )
        ]
        if not slacks:
            raise ValueError(f"no {kind.lower()} path slack rows reported for {scene}")
        result[f"{kind.lower()}_reported_path_count"] = len(slacks)
        result[f"{kind.lower()}_worst_reported_slack_ps"] = min(slacks)
    for marker in (f"TIMINGFORGE_DRV_BEGIN {scene}", f"TIMINGFORGE_DRV_END {scene}"):
        if marker not in body:
            raise ValueError(f"missing DRV report markers for {scene}")
    result["drv_report_present"] = True
    return result


def parse_units(text: str, expected_time: str, expected_capacitance: str) -> dict:
    time_match = re.search(r"^\s*time\s+1(\w+)\s*$", text, re.IGNORECASE | re.MULTILINE)
    cap_match = re.search(r"^\s*capacitance\s+1(\w+)\s*$", text, re.IGNORECASE | re.MULTILINE)
    if not time_match or not cap_match:
        raise ValueError("OpenSTA report_units output is missing time/capacitance units")
    actual = {"time": time_match.group(1).lower(), "capacitance": cap_match.group(1).lower()}
    if actual != {"time": expected_time.lower(), "capacitance": expected_capacitance.lower()}:
        raise ValueError(f"Liberty units mismatch: expected {expected_time}/{expected_capacitance}, got {actual}")
    return actual


def parse_sky130_postroute_metrics(text: str) -> dict:
    def period(marker: str) -> dict:
        section = text.split(marker, 1)[1]
        match = re.search(r"core_clk period_min = ([0-9.]+) fmax = ([0-9.]+)", section)
        if not match:
            raise ValueError(f"missing post-route period metrics after {marker}")
        return {"minimum_period_ns": float(match.group(1)), "fmax_mhz": float(match.group(2))}

    def summary(marker: str, kind: str) -> dict:
        section = text.split(marker, 1)[1]
        match = re.search(
            rf"worst slack {kind} ([-+]?[0-9.]+)\s+wns {kind} ([-+]?[0-9.]+)\s+tns {kind} ([-+]?[0-9.]+)",
            section,
        )
        if not match:
            raise ValueError(f"missing post-route {kind} slack summary after {marker}")
        return {"worst_slack_ns": float(match.group(1)), "wns_ns": float(match.group(2)), "tns_ns": float(match.group(3))}

    return {
        "register_to_register": period("=== POST-ROUTE REGISTER-TO-REGISTER CLOCK PERIOD ==="),
        "all_path": period("=== POST-ROUTE ALL-PATH CLOCK PERIOD ==="),
        "setup": summary("=== POST-ROUTE SETUP SUMMARY ===", "max"),
        "hold": summary("=== POST-ROUTE HOLD SUMMARY ===", "min"),
    }


def build_manifest(root: Path, orfs_root: Path) -> dict:
    versions_path = root / "tool_versions.txt"
    if not versions_path.is_file():
        raise FileNotFoundError(versions_path)
    versions = {}
    for line in versions_path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            versions[key.strip().lower().replace(" ", "_")] = value.strip()

    filtered_manifest_path = root / "asap7/filtered_libs_manifest.json"
    if not filtered_manifest_path.is_file():
        raise FileNotFoundError(filtered_manifest_path)
    filtered_manifest = json.loads(filtered_manifest_path.read_text(encoding="utf-8"))

    platforms = {}
    for platform in ("asap7", "sky130hd"):
        designs = {}
        for top in TOPS:
            work = root / platform / top
            results = work / "results" / platform / top / "base"
            missing = [name for name in REQUIRED if not (results / name).is_file()]
            if missing:
                raise FileNotFoundError(f"{platform}/{top} missing: {', '.join(missing)}")
            record = {
                "physical_corner": "TC" if platform == "asap7" else "TT_025C_1V80",
                "artifacts": {
                    name: {"path": str((results / name).relative_to(root)),
                           "sha256": sha256(results / name)}
                    for name in REQUIRED
                },
            }
            if platform == "asap7":
                log = work / "asap7_mcmm_postroute.log"
                if not log.is_file():
                    raise FileNotFoundError(log)
                log_text = log.read_text(encoding="utf-8", errors="replace")
                record["units"] = parse_units(log_text, "ps", "fF")
                record["mcmm"] = {
                    "engine": "OpenROAD-integrated OpenSTA MCMM scenes",
                    "scenes": [
                        {**ASAP7_SCENES[scene], **parse_scene_report(log_text, scene)}
                        for scene in ASAP7_SCENES
                    ],
                    "shared_spef_sha256": sha256(results / "6_final.spef"),
                    "filtered_simple_libraries": filtered_manifest["corners"],
                    "excluded_cell_patterns": filtered_manifest["excluded_patterns"],
                    "rc_assumption": (
                        "The single TC-extracted SPEF is reused unchanged in BC, TC and WC scenes; "
                        "no corner-specific RC scaling or extraction is applied."
                    ),
                    "report_log": str(log.relative_to(root)),
                    "report_log_sha256": sha256(log),
                }
            else:
                log = work / "sky130hd_postroute_sta.log"
                if not log.is_file():
                    raise FileNotFoundError(log)
                log_text = log.read_text(encoding="utf-8", errors="replace")
                if "POST-ROUTE PARASITICS LOADED" not in log_text:
                    raise ValueError(f"SKY130HD post-route SPEF marker missing for {top}")
                record["units"] = parse_units(log_text, "ns", "pF")
                record["postroute_sta"] = {
                    "metrics": parse_sky130_postroute_metrics(log_text),
                    "corner": "TT, 25C, 1.80V",
                    "liberty": "sky130_fd_sc_hd__tt_025C_1v80.lib",
                    "liberty_sha256": sha256(
                        orfs_root / "flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
                    ),
                    "report_log": str(log.relative_to(root)),
                    "report_log_sha256": sha256(log),
                    "spef_loaded": True,
                }
            designs[top] = record
        platforms[platform] = designs

    lib_root = orfs_root / "flow/platforms/asap7/lib/NLDM"
    library_hashes = {}
    for scene, pvt in ASAP7_SCENES.items():
        process = pvt["process"]
        files = []
        for group in ("AO", "INVBUF", "OA", "SIMPLE"):
            path = lib_root / (
                f"asap7sc7p5t_{group}_RVT_{process}_nldm_{ASAP7_LIB_VERSIONS[group]}.lib.gz"
            )
            if not path.is_file():
                raise FileNotFoundError(f"missing pinned ASAP7 {group}/{process} Liberty: {path}")
            files.append(path)
        seq = lib_root / (
            f"asap7sc7p5t_SEQ_RVT_{process}_nldm_{ASAP7_LIB_VERSIONS['SEQ']}.lib"
        )
        if not seq.is_file():
            raise FileNotFoundError(f"missing pinned ASAP7 SEQ/{process} Liberty: {seq}")
        files.append(seq)
        library_hashes[scene] = [
            {"file": path.name, "sha256": sha256(path)} for path in files
        ]

    return {
        "schema_version": "1.0",
        "tool_versions": versions,
        "orfs_platform_source_revision": versions.get("orfs_source_revision", "unknown"),
        "orfs_container_image_digest": versions.get("orfs_container_image_digest", "unknown"),
        "experiments": platforms,
        "asap7_liberty_sha256": library_hashes,
        "asap7_filtered_simple_manifest": filtered_manifest,
        "asap7_mcmm_cell_policy": (
            "XOR, XNOR and HAxp5 cells are excluded from the ASAP7 physical mapping and "
            "filtered from each SIMPLE corner Liberty because the pinned platform's "
            "FF/TT/SS models do not provide consistent timing groups for those cells."
        ),
        "asap7_pvt": ASAP7_SCENES,
        "platform_licenses": {
            "asap7": {
                "license": "BSD-3-Clause",
                "upstream": "https://github.com/The-OpenROAD-Project/asap7",
                "license_url": "https://github.com/The-OpenROAD-Project/asap7/blob/main/LICENSE",
            },
            "sky130hd": {
                "license": "Apache-2.0",
                "upstream": "https://github.com/google/skywater-pdk",
                "license_url": "https://github.com/google/skywater-pdk/blob/main/LICENSE",
            },
        },
        "asap7_spef_policy": (
            "One TC physical implementation per architecture; its extracted SPEF is reused "
            "unchanged in the BC/TC/WC MCMM scenes. No corner-specific RC extraction or scaling."
        ),
        "cross_library_absolute_ppa_comparison_claim": False,
        "foundry_signoff_claim": False,
        "interpretation": (
            "ASAP7 is an academic predictive platform and SKY130HD is an open PDK platform. "
            "These are reproducible educational implementation experiments, not foundry signoff."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--orfs-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_manifest(args.root, args.orfs_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: technology breadth manifest written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
