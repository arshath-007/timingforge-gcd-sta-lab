"""Basic KLayout GDS sanity validation (not a foundry DRC deck)."""
import json
import os
from pathlib import Path

import pya

gds_path = Path(os.environ["GDS_PATH"])
top_name = os.environ["TOP_CELL"]
report_path = Path(os.environ["GDS_REPORT"])

if not gds_path.is_file() or gds_path.stat().st_size == 0:
    raise RuntimeError(f"GDS file missing or empty: {gds_path}")

layout = pya.Layout()
layout.read(str(gds_path))
top_names = [cell.name for cell in layout.top_cells()]
if top_name not in top_names:
    raise RuntimeError(f"Expected top cell {top_name!r}; found top cells {top_names}")

top = layout.cell(top_name)
bbox = top.bbox()
if bbox.width() <= 0 or bbox.height() <= 0:
    raise RuntimeError(f"Top cell {top_name} has an empty bounding box")

layer_indexes = list(layout.layer_indexes())
shape_count = sum(cell.shapes(layer).size() for cell in layout.each_cell() for layer in layer_indexes)
if not layer_indexes or shape_count == 0:
    raise RuntimeError("GDS contains no non-empty layer geometry")

result = {
    "status": "PASS",
    "top_cell": top_name,
    "top_cells": top_names,
    "dbu": layout.dbu,
    "layer_count": len(layer_indexes),
    "shape_count_all_cells": shape_count,
    "top_bbox_dbu": [bbox.left, bbox.bottom, bbox.right, bbox.top],
    "gds_bytes": gds_path.stat().st_size,
    "validation_scope": "GDS readability, expected top cell, non-empty bbox and geometry; not foundry DRC",
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("GDS_VALIDATION_PASS " + json.dumps(result, sort_keys=True))
