#!/usr/bin/env python3
"""Build the static hub and embed the shared theme in standalone HTML files."""

from __future__ import annotations

import html
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys


THEME_MARKER = "<!-- SHARED_THEME -->"
AUTHORSHIP_MARKER = "<!-- AUTHORSHIP -->"
STATIC_FILES = ("index.html", "assets/theme.css", "assets/site.css", "assets/site.js", "LICENSE")
ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


class BuildError(ValueError):
    """An input cannot be safely published by the site build."""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BuildError(f"Cannot read {path}: {error}") from error


def read_json(path: Path) -> object:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as error:
        raise BuildError(f"Invalid JSON in {path}: {error}") from error


def require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{label} must be a nonempty string")
    return value


def load_site(root: Path) -> dict:
    site = read_json(root / "site.json")
    if not isinstance(site, dict):
        raise BuildError("site.json must contain an object")
    for field in ("title", "subtitle", "term"):
        require_text(site.get(field), f"site.{field}")
    authorship = site.get("authorship")
    if not isinstance(authorship, dict):
        raise BuildError("site.authorship must contain an object")
    for field in ("ideas", "implementation"):
        require_text(authorship.get(field), f"site.authorship.{field}")
    return site


def source_path(root: Path, source: object) -> Path:
    """Resolve a source below sources/ without allowing traversal or outside links."""
    source = require_text(source, "visualization.source")
    relative = PurePosixPath(source)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in source
            or len(relative.parts) < 2 or relative.parts[0] != "sources"
            or relative.suffix != ".html"):
        raise BuildError(f"Source must be an HTML path below sources/: {source}")
    path = (root / source).resolve()
    if not path.is_relative_to(root / "sources"):
        raise BuildError(f"Source resolves outside sources/: {source}")
    return path


def attribution(authorship: dict) -> str:
    ideas = html.escape(authorship["ideas"])
    implementation = html.escape(authorship["implementation"])
    comment = (
        f"Ideas and instructional design: {authorship['ideas']}; "
        f"Implementation: {authorship['implementation']}"
    ).replace("--", "—").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"<!-- {comment} -->\n"
        '<footer class="attribution">\n'
        f"  <span>Ideas and instructional design: {ideas}</span>\n"
        f"  <span>Implementation: {implementation}</span>\n"
        "</footer>"
    )


def render_visualization(source: str, theme: str, authorship: dict,
                         license_text: str, label: str) -> str:
    for marker, element in ((THEME_MARKER, "head"), (AUTHORSHIP_MARKER, "body")):
        if source.count(marker) != 1:
            raise BuildError(f"{label} must contain exactly one {marker}")
        container = re.search(rf"<{element}\b[^>]*>(.*?)</{element}\s*>", source,
                              flags=re.IGNORECASE | re.DOTALL)
        if container is None or marker not in container.group(1):
            raise BuildError(f"{label}: {marker} must be inside <{element}>")
    if re.search(r"</style\s*>", theme, flags=re.IGNORECASE):
        raise BuildError("assets/theme.css cannot contain a closing </style> tag")
    license_comment = f"<!--\n{license_text}\n-->"
    return source.replace(THEME_MARKER, f"{license_comment}\n<style>\n{theme}\n</style>").replace(
        AUTHORSHIP_MARKER, attribution(authorship)
    )


def build(root: Path) -> int:
    """Validate all inputs, then replace only the generated dist/ directory."""
    root = root.resolve()
    site = load_site(root)
    entries = read_json(root / "visualizations.json")
    if not isinstance(entries, list):
        raise BuildError("visualizations.json must contain an array")

    output = {name: read_text(root / name) for name in STATIC_FILES}
    theme = output["assets/theme.css"]
    license_text = require_text(output["LICENSE"], "LICENSE")
    if "--" in license_text:
        raise BuildError("LICENSE contains '--', which cannot be embedded unchanged in an HTML comment")
    catalog = []
    used_ids: set[str] = set()
    used_sources: set[Path] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise BuildError("Each visualization must be an object")
        identifier = require_text(entry.get("id"), "visualization.id")
        if not ID_PATTERN.fullmatch(identifier) or identifier == "overview":
            raise BuildError(f"Invalid or reserved visualization id: {identifier}")
        if identifier in used_ids:
            raise BuildError(f"Duplicate visualization id: {identifier}")
        used_ids.add(identifier)
        for field in ("title", "description", "category", "kind"):
            require_text(entry.get(field), f"{identifier}.{field}")
        source = source_path(root, entry.get("source"))
        if source in used_sources:
            raise BuildError(f"Duplicate visualization source: {entry['source']}")
        used_sources.add(source)
        filename = f"visualizations/{identifier}.html"
        output[filename] = render_visualization(
            read_text(source), theme, site["authorship"], license_text, entry["source"]
        )
        catalog.append({key: value for key, value in entry.items() if key != "source"}
                       | {"file": filename})

    payload = json.dumps(site | {"visualizations": catalog}, ensure_ascii=True, indent=2)
    output["assets/catalog.js"] = f"window.STAT250_SITE = {payload};\n"
    output[".nojekyll"] = ""

    destination = root / "dist"
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise BuildError("dist must be a generated directory, not a file or symbolic link")
    if destination.exists():
        shutil.rmtree(destination)
    for name, contents in output.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    return len(catalog)


def main() -> int:
    try:
        count = build(Path(__file__).resolve().parents[1])
    except BuildError as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    print(f"Built dist/ with {count} standalone visualization(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
