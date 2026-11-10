#!/usr/bin/env python3
"""Read-only integrity checks for the Module 6 scenes and optional clipboard export.

Uses only the Python standard library. Does not establish visual or statistical
correctness, PNG freshness, or byte-identical rendering across editor versions.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "diagrams/excalidraw/module6"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def svg_signature(data: bytes) -> tuple:
    """Compare glyph geometry while tolerating editor XML reserialization."""
    root = ET.fromstring(data)
    paths = Counter(e.attrib["d"] for e in root.iter()
                    if e.tag.rsplit("}", 1)[-1] == "path")
    require(bool(paths), "Formula SVG has no glyph paths")
    return root.attrib["viewBox"], paths


def embedded_svg(file: dict) -> bytes:
    prefix = "data:image/svg+xml;base64,"
    require(file["dataURL"].startswith(prefix), "Formula must be embedded SVG")
    return base64.b64decode(file["dataURL"][len(prefix):], validate=True)


def compare_roundtrip(scene: dict, copied: dict) -> None:
    require(copied.get("type") == "excalidraw/clipboard", "Expected clipboard payload")
    for key in ("type", "text"):
        require(Counter(e.get(key) for e in scene["elements"]) ==
                Counter(e.get(key) for e in copied["elements"]), f"Changed element {key}")
    require(scene["files"].keys() == copied["files"].keys(), "Changed embedded files")
    for key in scene["files"]:
        require(svg_signature(embedded_svg(scene["files"][key])) ==
                svg_signature(embedded_svg(copied["files"][key])), "Changed SVG glyph geometry")
    metadata = lambda doc: Counter(json.dumps(e.get("customData"), sort_keys=True)
                                   for e in doc["elements"] if e["type"] == "image")
    require(metadata(scene) == metadata(copied), "Changed formula metadata")


def validate(path: Path) -> dict:
    scene = json.loads(path.read_text())
    require(scene.get("type") == "excalidraw" and scene.get("version") == 2,
            "Expected native version-2 Excalidraw document")
    elements, files = scene["elements"], scene["files"]
    ids = {e["id"] for e in elements}
    require(len(ids) == len(elements), "Duplicate element IDs")
    for element in elements:
        if element["type"] == "text":
            require(element["fontFamily"] == 5, "Expected Excalifont text")
        for binding in element.get("boundElements") or []:
            require(binding["id"] in ids, "Dangling bound element")
        for key in ("startBinding", "endBinding"):
            binding = element.get(key)
            if binding:
                require(binding["elementId"] in ids, "Dangling arrow binding")
        if element["type"] != "image":
            continue
        require(element["fileId"] in files, "Missing image file")
        metadata = element["customData"]
        source = path.parent / metadata["formulaSource"]
        require(source.is_file(), "Missing formula source")
        require(f'$ {metadata["typst"]} $' in source.read_text(), "Formula source mismatch")
        require(svg_signature(embedded_svg(files[element["fileId"]])) ==
                svg_signature(source.with_suffix(".svg").read_bytes()), "Formula SVG mismatch")
    png = path.with_suffix(".png").read_bytes()
    require(png[:8] == b"\x89PNG\r\n\x1a\n" and png[12:16] == b"IHDR", "Invalid PNG header")
    size = struct.unpack(">II", png[16:24])
    require(min(size) > 0, "Empty PNG dimensions")
    ET.parse(path.with_suffix(".svg"))
    return {"scene": path.name, "elements": len(elements), "embedded_svgs": len(files),
            "png_dimensions": size, "integrity": "passed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", nargs="?", type=Path)
    parser.add_argument("--roundtrip", type=Path, help="Compare a clipboard JSON export with scene")
    args = parser.parse_args()
    if args.roundtrip and not args.scene:
        parser.error("--roundtrip requires a scene path")
    paths = [args.scene] if args.scene else sorted(DIRECTORY.glob("*.excalidraw"))
    require(bool(paths), "No scenes found")
    results = [validate(path) for path in paths]
    if args.roundtrip:
        compare_roundtrip(json.loads(args.scene.read_text()), json.loads(args.roundtrip.read_text()))
        results[0]["clipboard_roundtrip"] = "passed"
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
