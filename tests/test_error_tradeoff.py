"""Check the normal-model probabilities against an independent erfc reference."""

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "sources" / "type-i-type-ii-errors.html"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for the visualization's JavaScript")
class ErrorTradeoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = re.search(r'<script id="error-tradeoff-math">(.*?)</script>',
                           SOURCE.read_text(), re.S).group(1)
        audit = """
const fs = require('node:fs');
const vm = require('node:vm');
const model = vm.runInNewContext(fs.readFileSync(0, 'utf8') + '\\n;ErrorTradeoffMath');
const cutoffs = Array.from({length: 1601}, (_, i) => i / 1000);
const zValues = Array.from({length: 801}, (_, i) => (i - 400) / 100);
const rejected = [-0.001, 1.601, NaN, Infinity].map(value => {
  try { model.probabilities(value); return false; } catch { return true; }
});
console.log(JSON.stringify({
  cdf: zValues.map(z => [z, model.normalCDF(z)]),
  sweep: cutoffs.map(c => ({c, ...model.probabilities(c)})),
  presets: Object.entries(model.PRESETS).map(([alpha, c]) => ({c, ...model.probabilities(c), expectedAlpha:Number(alpha)})),
  defaultCutoff:model.DEFAULT,
  midpoint:model.probabilities(0.5),
  densities:[0, 1].map(mean => [-2, 0, 0.5, 1, 3].map(x => [x, mean, model.density(x, mean)])),
  rejected
}));
"""
        result = subprocess.run([NODE, "-e", audit], input=script, text=True,
                                capture_output=True, check=True)
        cls.audit = json.loads(result.stdout)

    def test_normal_cdf_against_erfc(self):
        for z, actual in self.audit["cdf"]:
            expected = 0.5 * math.erfc(-z / math.sqrt(2))
            self.assertAlmostEqual(actual, expected, delta=2e-14)

    def test_probabilities_over_full_cutoff_range(self):
        previous = None
        for result in self.audit["sweep"]:
            c = result["c"]
            alpha = 0.5 * math.erfc(c / (0.4 * math.sqrt(2)))
            beta = 0.5 * math.erfc((1 - c) / (0.4 * math.sqrt(2)))
            self.assertAlmostEqual(result["alpha"], alpha, delta=2e-14)
            self.assertAlmostEqual(result["beta"], beta, delta=2e-14)
            self.assertAlmostEqual(result["beta"] + result["power"], 1, delta=1e-15)
            for name in ("alpha", "beta", "power"):
                self.assertGreaterEqual(result[name], 0)
                self.assertLessEqual(result[name], 1)
            if previous:
                self.assertLess(result["alpha"], previous["alpha"])
                self.assertGreater(result["beta"], previous["beta"])
            previous = result

    def test_presets_and_symmetry(self):
        self.assertEqual(self.audit["defaultCutoff"], 0.4 * 1.6448536269514722)
        for result in self.audit["presets"]:
            self.assertAlmostEqual(result["alpha"], result["expectedAlpha"], delta=2e-14)
        midpoint = self.audit["midpoint"]
        self.assertAlmostEqual(midpoint["alpha"], 0.1056497736668553, delta=2e-14)
        self.assertAlmostEqual(midpoint["alpha"], midpoint["beta"], delta=2e-14)
        self.assertTrue(all(self.audit["rejected"]))

    def test_density_matches_fixed_sampling_distributions(self):
        for distribution in self.audit["densities"]:
            for x, mean, actual in distribution:
                expected = math.exp(-0.5 * ((x - mean) / 0.4) ** 2) / (0.4 * math.sqrt(2 * math.pi))
                self.assertAlmostEqual(actual, expected, delta=1e-15)


if __name__ == "__main__":
    unittest.main()
