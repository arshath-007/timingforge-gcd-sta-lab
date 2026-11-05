"""Filter known corner-inconsistent ASAP7 SIMPLE cells for valid MCMM linking."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

PROCESSES = ("FF", "TT", "SS")
SIMPLE_VERSION = "211120"
EXCLUDED_PATTERNS = ("^XOR", "^XNOR", "^HAxp5")
CELL_RE = re.compile(r"(?m)^[ \t]*cell\s*\(\s*([^)]+)\s*\)\s*\{)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def matching_brace(text: str, open_index: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    line_comment = False
    block_comment = False
    i = open_index
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == "/" and nxt == "*":
            block_comment = True
            i += 1
        elif ch == "/" and nxt == "/":
            line_comment = True
            i += 1
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced Liberty cell block")


def filter_liberty(text: str) -> tuple[str, list[str]]:
    output = []
    removed = []
    cursor = 0
    search_at = 0
    excluded = tuple(re.compile(pattern) for pattern in EXCLUDED_PATTERNS)
    while True:
        match = CELL_RE.search(text, search_at)
        if not match:
            output.append(text[cursor:])
            break
        end = matching_brace(text, match.end() - 1)
        name = match.group(1).strip().strip('"')
        output.append(text[cursor:match.start()])
        if any(pattern.match(name) for pattern in excluded):
            removed.append(name)
        else:
            output.append(text[match.start():end + 1])
        cursor = end + 1
        search_at = end + 1
    if not removed:
        raise ValueError("no excluded XOR/XNOR/HA cells found in SIMPLE Liberty")
    return "".join(output), sorted(removed)


def build_filtered_libraries(lib_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = {}
    for process in PROCESSES:
        source = lib_dir / (
            f"asap7sc7p5t_SIMPLE_RVT_{process}_nldm_{SIMPLE_VERSION}.lib.gz"
        )
        if not source.is_file():
            raise FileNotFoundError(source)
        with gzip.open(source, "rt", encoding="utf-8", errors="replace") as stream:
            original = stream.read()
        filtered, removed = filter_liberty(original)
        destination = output_dir / (
            f"asap7sc7p5t_SIMPLE_RVT_{process}_nldm_{SIMPLE_VERSION}.filtered.lib"
        )
        destination.write_text(filtered, encoding="utf-8")
        records[process] = {
            "source_file": source.name,
            "source_sha256": sha256(source),
            "filtered_file": destination.name,
            "filtered_sha256": sha256(destination),
            "removed_cells": removed,
        }
    return {
        "schema_version": "1.0",
        "excluded_patterns": list(EXCLUDED_PATTERNS),
        "corners": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lib-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_filtered_libraries(args.lib_dir, args.output_dir)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: filtered ASAP7 SIMPLE Liberty libraries written to {args.output_dir}")
    for corner, record in manifest["corners"].items():
        print(f"{corner}: excluded {len(record['removed_cells'])} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
