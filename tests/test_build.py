"""Build-contract checks use disposable projects, never the repository's dist/."""

import json
from pathlib import Path
import tempfile
import unittest

from scripts.build import AUTHORSHIP_MARKER, BuildError, THEME_MARKER, build


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        (self.root / "assets").mkdir()
        (self.root / "sources").mkdir()
        self.theme = ":root { --accent: #245b80; }\n"
        (self.root / "index.html").write_text("<html>Hub</html>")
        (self.root / "assets/theme.css").write_text(self.theme)
        (self.root / "assets/site.css").write_text("body { margin: 0; }")
        (self.root / "assets/site.js").write_text("'use strict';")
        self.license = "MIT License\n\nCopyright (c) 2026 Fixture Author\n\nFixture permission notice.\n"
        (self.root / "LICENSE").write_text(self.license)
        self.site = {
            "title": "STAT 250", "subtitle": "Interactive statistics", "term": "Fall 2026",
            "authorship": {"ideas": "The course author", "implementation": "ChatGPT-6 Astra"},
        }
        self.entry = {
            "id": "example", "title": "Example", "description": "An example.",
            "source": "sources/example.html", "category": "Examples", "kind": "preview",
        }
        self.source = (
            f"<!doctype html><html><head>{THEME_MARKER}</head>"
            f"<body><h1>Example</h1><script>const x = 1;</script>{AUTHORSHIP_MARKER}</body></html>"
        )
        (self.root / self.entry["source"]).write_text(self.source)
        self.write_json("site.json", self.site)
        self.write_json("visualizations.json", [self.entry])

    def write_json(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def catalog(self):
        script = (self.root / "dist/assets/catalog.js").read_text()
        return json.loads(script.removeprefix("window.STAT250_SITE = ").removesuffix(";\n"))

    def test_embeds_theme_and_credit_in_the_downloadable_file(self):
        self.assertEqual(build(self.root), 1)
        page = (self.root / "dist/visualizations/example.html").read_text()
        self.assertIn(f"<style>\n{self.theme}\n</style>", page)
        self.assertIn('<footer class="attribution">', page)
        self.assertIn("Ideas and instructional design: The course author", page)
        self.assertIn("Implementation: ChatGPT-6 Astra", page)
        self.assertIn("<script>const x = 1;</script>", page)
        self.assertNotIn(THEME_MARKER, page)
        self.assertNotIn(AUTHORSHIP_MARKER, page)
        metadata = self.catalog()["visualizations"][0]
        self.assertEqual(metadata["file"], "visualizations/example.html")
        self.assertNotIn("source", metadata)
        self.assertTrue((self.root / "dist/.nojekyll").is_file())

    def test_preserves_the_license_in_downloads_and_published_site(self):
        build(self.root)
        page = (self.root / "dist/visualizations/example.html").read_text()
        self.assertIn(f"<!--\n{self.license}\n-->", page)
        self.assertEqual((self.root / "dist/LICENSE").read_text(), self.license)
        self.assertIn("Ideas and instructional design: The course author", page)

    def test_empty_catalog_builds_and_removes_stale_generated_files(self):
        build(self.root)
        self.write_json("visualizations.json", [])
        self.assertEqual(build(self.root), 0)
        self.assertEqual(self.catalog()["visualizations"], [])
        self.assertTrue((self.root / "dist/index.html").is_file())
        self.assertFalse((self.root / "dist/visualizations/example.html").exists())

    def test_invalid_ids_and_reserved_overview_fail(self):
        for identifier in ("../other", "MixedCase", "with spaces", "overview", "a/b"):
            with self.subTest(identifier=identifier):
                self.write_json("visualizations.json", [self.entry | {"id": identifier}])
                with self.assertRaisesRegex(BuildError, "Invalid or reserved"):
                    build(self.root)

    def test_duplicate_ids_fail(self):
        self.write_json("visualizations.json", [self.entry, self.entry])
        with self.assertRaisesRegex(BuildError, "Duplicate visualization id"):
            build(self.root)

    def test_duplicate_sources_fail_even_with_different_ids(self):
        self.write_json("visualizations.json", [self.entry, self.entry | {"id": "second"}])
        with self.assertRaisesRegex(BuildError, "Duplicate visualization source"):
            build(self.root)

    def test_source_paths_cannot_escape_the_sources_directory(self):
        for source in ("../outside.html", "/tmp/example.html", "sources/../index.html",
                       "index.html", "sources\\example.html", "sources/example.js"):
            with self.subTest(source=source):
                self.write_json("visualizations.json", [self.entry | {"source": source}])
                with self.assertRaisesRegex(BuildError, "below sources"):
                    build(self.root)

    def test_source_symlinks_cannot_point_outside_sources(self):
        (self.root / "sources/link.html").symlink_to(self.root / "index.html")
        self.write_json("visualizations.json", [self.entry | {"source": "sources/link.html"}])
        with self.assertRaisesRegex(BuildError, "resolves outside"):
            build(self.root)

    def test_markers_must_be_unique_and_in_the_correct_element(self):
        cases = (
            self.source.replace(THEME_MARKER, ""),
            self.source.replace(AUTHORSHIP_MARKER, AUTHORSHIP_MARKER * 2),
            self.source.replace(THEME_MARKER, "").replace("</body>", THEME_MARKER + "</body>"),
        )
        for source in cases:
            with self.subTest(source=source):
                (self.root / self.entry["source"]).write_text(source)
                with self.assertRaises(BuildError):
                    build(self.root)

    def test_invalid_input_preserves_previous_build(self):
        build(self.root)
        previous = (self.root / "dist/assets/catalog.js").read_bytes()
        self.write_json("visualizations.json", [self.entry | {"title": ""}])
        with self.assertRaisesRegex(BuildError, "nonempty string"):
            build(self.root)
        self.assertEqual((self.root / "dist/assets/catalog.js").read_bytes(), previous)

    def test_attribution_is_escaped_as_text(self):
        self.site["authorship"]["ideas"] = '<script>alert("name")</script>'
        self.write_json("site.json", self.site)
        build(self.root)
        page = (self.root / "dist/visualizations/example.html").read_text()
        self.assertNotIn('<script>alert("name")</script>', page)
        self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
