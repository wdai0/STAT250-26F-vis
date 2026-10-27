"""Check the public flashcard boundary, real controls, and numerical examples."""

from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/flashcards.html"
NODE = shutil.which("node")


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        self.references.extend(value for key, value in attrs
                               if key in ("src", "href") and value)


class FlashcardPublicationTests(unittest.TestCase):
    def test_flashcards_are_standalone_without_the_question_section(self):
        source = SOURCE.read_text()
        page = PageLinks()
        page.feed(source)
        self.assertEqual(page.references, [])
        self.assertIn("<title>Flashcards · STAT 250</title>", source)
        self.assertIn("<span>Flashcards</span>", source)
        for excluded in ("Questions", "Concepts &amp; flashcards", "Classroom only",
                         "review-later", "window.openai", "openai:set_globals",
                         "/Users/", "handoff", "Show visual", "Hide visual",
                         "Explore this concept"):
            self.assertNotIn(excluded, source)
        self.assertEqual(source.count("<!-- SHARED_THEME -->"), 1)
        self.assertEqual(source.count("<!-- AUTHORSHIP -->"), 1)
        self.assertNotRegex(source, r"fetch\s*\(|XMLHttpRequest|WebSocket")

    def test_public_route_registers_only_the_flashcards(self):
        entries = json.loads((ROOT / "visualizations.json").read_text())
        flashcards = [entry for entry in entries if entry["id"] == "flashcards"]
        self.assertEqual(len(flashcards), 1)
        self.assertEqual(flashcards[0]["title"], "Flashcards")
        self.assertEqual(flashcards[0]["source"], "sources/flashcards.html")
        self.assertFalse(any("question" in entry["id"] for entry in entries))
        self.assertIn('href="#flashcards">Flashcards</a>',
                      (ROOT / "index.html").read_text())


@unittest.skipUnless(NODE, "Node.js is needed to exercise the flashcard controls")
class FlashcardControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            [NODE, str(ROOT / "tests/flashcards_controls.cjs")],
            input=SOURCE.read_text(), text=True, capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.audit = json.loads(result.stdout)

    def test_all_topics_controls_and_answer_reveals(self):
        self.assertEqual(len(self.audit["topics"]), 13)
        self.assertEqual(sum(topic["count"] for topic in self.audit["topics"]), 52)
        self.assertEqual(self.audit["buttonsExercised"], 75)

    def test_normal_tail_probabilities_against_python(self):
        for result in self.audit["cdf"]:
            expected = .5 * math.erfc(-result["x"] / math.sqrt(2))
            self.assertAlmostEqual(result["p"], expected, delta=1e-7)

    def test_bootstrap_draws_and_interval_arithmetic(self):
        original = [2, 4, 4, 6, 9]
        for group in self.audit["replicates"]:
            state = 3250
            values = []
            for _ in range(group["n"]):
                sample = []
                for _ in range(5):
                    state = (state * 1664525 + 1013904223) % 2**32
                    sample.append(original[int(state / 2**32 * 5)])
                values.append(statistics.mean(sample))
            self.assertEqual(values, group["values"])
            if group["n"] == 600:
                self.assertAlmostEqual(statistics.stdev(values), self.audit["boot"]["se"])
                ordered = sorted(values)
                for probability, field in ((.025, "low"), (.975, "high")):
                    index = (len(values) - 1) * probability
                    lower = math.floor(index)
                    expected = ordered[lower] + (ordered[lower + 1] - ordered[lower]) * (index - lower)
                    self.assertEqual(expected, self.audit["boot"][field])


if __name__ == "__main__":
    unittest.main()
