"""Build-contract checks use disposable projects, never the repository's dist/."""

import json
from pathlib import Path
import tempfile
import unittest

from scripts.build import AUTHORSHIP_MARKER, BuildError, DATA_MARKER, THEME_MARKER, build


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

    def add_dataset(self, contents="Name,Value\nExample,1\n", text_columns=None):
        (self.root / "data").mkdir(exist_ok=True)
        (self.root / "data/example.csv").write_text(contents)
        self.entry["dataset"] = {
            "source": "data/example.csv",
            "text_columns": ["Name"] if text_columns is None else text_columns,
        }
        self.source = self.source.replace("const x = 1;", f"const data = {DATA_MARKER};")
        (self.root / self.entry["source"]).write_text(self.source)
        self.write_json("visualizations.json", [self.entry])

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

    def test_invalid_ids_and_reserved_routes_fail(self):
        for identifier in ("../other", "MixedCase", "with spaces", "overview", "home", "a/b"):
            with self.subTest(identifier=identifier):
                self.write_json("visualizations.json", [self.entry | {"id": identifier}])
                with self.assertRaisesRegex(BuildError, "Invalid or reserved"):
                    build(self.root)

    def test_homepage_must_resolve_without_overwriting_previous_build(self):
        self.site["homepage"] = "example"
        self.write_json("site.json", self.site)
        build(self.root)
        self.assertEqual(self.catalog()["homepage"], "example")
        previous = (self.root / "dist/assets/catalog.js").read_bytes()
        for homepage in ("missing", "", None):
            with self.subTest(homepage=homepage):
                self.write_json("site.json", self.site | {"homepage": homepage})
                with self.assertRaises(BuildError):
                    build(self.root)
                self.assertEqual((self.root / "dist/assets/catalog.js").read_bytes(), previous)

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

    def test_csv_values_are_embedded_and_missing_values_remain_null(self):
        self.add_dataset(
            'Name,Value,Other\n"A, B",0,2.5\nC,NA,\nD,N/A,null\nE,-3,4e2\n'
        )
        build(self.root)
        page = (self.root / "dist/visualizations/example.html").read_text()
        payload = page.split("const data = ", 1)[1].split(";</script>", 1)[0]
        self.assertEqual(json.loads(payload), [
            {"Name": "A, B", "Value": 0, "Other": 2.5},
            {"Name": "C", "Value": None, "Other": None},
            {"Name": "D", "Value": None, "Other": None},
            {"Name": "E", "Value": -3, "Other": 400},
        ])
        self.assertNotIn(DATA_MARKER, page)
        self.assertNotIn("dataset", self.catalog()["visualizations"][0])
        self.assertFalse((self.root / "dist/data/example.csv").exists())

    def test_csv_text_cannot_close_the_script_element(self):
        self.add_dataset('Name,Value\n"</script><script>alert(1)</script>",1\n')
        build(self.root)
        page = (self.root / "dist/visualizations/example.html").read_text()
        self.assertNotIn("</script><script>alert(1)</script>", page)
        self.assertIn(r"\u003c/script>", page)
        payload = page.split("const data = ", 1)[1].split(";</script>", 1)[0]
        self.assertEqual(json.loads(payload)[0]["Name"], "</script><script>alert(1)</script>")

    def test_csv_rejects_malformed_headers_fields_and_numbers(self):
        cases = (
            ("", "headers"),
            ("Name,Value,Value\nA,1,2\n", "headers"),
            ("Name,\nA,1\n", "headers"),
            ("Name,Value\n", "at least one data row"),
            ("Name,Value\nA\n", "expected 2 fields"),
            ("Name,Value\nA,1,2\n", "expected 2 fields"),
            ("Name,Value\nA,text\n", "numeric or missing"),
            ("Name,Value\nA,NaN\n", "finite"),
            ("Name,Value\nA,Infinity\n", "finite"),
            ('Name,Value\n"unterminated,1\n', "Invalid CSV"),
        )
        self.add_dataset()
        for contents, message in cases:
            with self.subTest(contents=contents):
                (self.root / "data/example.csv").write_text(contents)
                with self.assertRaisesRegex(BuildError, message):
                    build(self.root)

    def test_dataset_text_columns_must_be_unique_existing_names(self):
        self.add_dataset()
        for columns in (None, "Name", ["Name", "Name"], ["Name", "Absent"], [""], [1]):
            with self.subTest(columns=columns):
                self.entry["dataset"]["text_columns"] = columns
                self.write_json("visualizations.json", [self.entry])
                with self.assertRaisesRegex(BuildError, "text_columns"):
                    build(self.root)

    def test_dataset_paths_cannot_escape_data(self):
        self.add_dataset()
        for source in ("../example.csv", "/tmp/example.csv", "data/../example.csv",
                       "example.csv", "data\\example.csv", "data/example.html"):
            with self.subTest(source=source):
                self.entry["dataset"]["source"] = source
                self.write_json("visualizations.json", [self.entry])
                with self.assertRaisesRegex(BuildError, "below data"):
                    build(self.root)

    def test_dataset_symlinks_cannot_point_outside_data(self):
        self.add_dataset()
        (self.root / "data/link.csv").symlink_to(self.root / "index.html")
        self.entry["dataset"]["source"] = "data/link.csv"
        self.write_json("visualizations.json", [self.entry])
        with self.assertRaisesRegex(BuildError, "resolves outside data"):
            build(self.root)

    def test_dataset_requires_one_marker_inside_a_script(self):
        self.add_dataset()
        cases = (
            self.source.replace(DATA_MARKER, "[]"),
            self.source.replace(DATA_MARKER, f"{DATA_MARKER}; const second = {DATA_MARKER}"),
            self.source.replace(DATA_MARKER, "[]").replace("</body>", DATA_MARKER + "</body>"),
        )
        for source in cases:
            with self.subTest(source=source):
                (self.root / self.entry["source"]).write_text(source)
                with self.assertRaisesRegex(BuildError, "embedded data marker|exactly one"):
                    build(self.root)

    def test_embedded_data_marker_without_dataset_fails(self):
        self.add_dataset()
        del self.entry["dataset"]
        self.write_json("visualizations.json", [self.entry])
        with self.assertRaisesRegex(BuildError, "requires a dataset"):
            build(self.root)

    def test_invalid_dataset_preserves_previous_build(self):
        self.add_dataset()
        build(self.root)
        previous = (self.root / "dist/visualizations/example.html").read_bytes()
        (self.root / "data/example.csv").write_text("Name,Value\nA,not-a-number\n")
        with self.assertRaises(BuildError):
            build(self.root)
        self.assertEqual((self.root / "dist/visualizations/example.html").read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
