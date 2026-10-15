"""Independent probability, boundary, rendering-area, and sweep checks."""

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "sources" / "test-ci-duality.html"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is needed to exercise the actual browser model")
class DualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = re.search(r'<script id="duality-math">(.*?)</script>', SOURCE.read_text(), re.S).group(1)
        audit = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const model = vm.runInNewContext(fs.readFileSync(0, 'utf8') + '\n;DualityMath');
const integrate = points => points.slice(1).reduce((sum, [x, y], i) => {
  const [lastX, lastY] = points[i];
  return sum + (x - lastX) * (y + lastY) / 2;
}, 0);
const edges = [model.LOWER, model.UPPER].flatMap(endpoint =>
  [-1e-6, -1e-10, -Number.EPSILON * 4, 0, Number.EPSILON * 4, 1e-10, 1e-6].map(offset => model.test(endpoint + offset)));
const tailAreas = [3, 4, model.LOWER, 4.9, 5, 5.1, model.UPPER, 6, 7].map(mu => {
  const result = model.test(mu);
  return {...result,
    leftArea: integrate(model.curvePoints(0, result.left, mu)),
    rightArea: integrate(model.curvePoints(result.right, 10, mu)),
    centerDensity: model.density(mu, mu)
  };
});
const invalid = [2.999, 7.001, NaN, Infinity, '5'].map(mu => {
  try { model.test(mu); return false; } catch (error) { return error.name === 'RangeError'; }
});
console.log(JSON.stringify({
  lower:model.LOWER, upper:model.UPPER, observed:model.OBSERVED, se:model.SE,
  sweep:Array.from({length:4001}, (_, i) => model.test(3 + i / 1000)),
  edges, tailAreas, invalid,
  timeline:Array.from({length:model.DURATION + 1}, (_, i) => model.sweepAt(i)),
  holds:[1800, 2999, 4800, 5799, 7600, 8799].map(t => [t, model.sweepAt(t)]),
  final:model.sweepAt(model.DURATION + 1000), duration:model.DURATION
}));
"""
        result = subprocess.run([NODE, "-e", audit], input=script, text=True,
                                capture_output=True, check=True)
        cls.audit = json.loads(result.stdout)

    def test_model_and_checkpoints(self):
        self.assertEqual(self.audit["observed"], 5)
        self.assertEqual(self.audit["se"], .5)
        self.assertAlmostEqual(self.audit["lower"], 4.020018007729973, delta=1e-15)
        self.assertAlmostEqual(self.audit["upper"], 5.979981992270027, delta=1e-15)
        self.assertEqual(self.audit["sweep"][2000]["p"], 1)
        self.assertAlmostEqual(self.audit["sweep"][3000]["p"], .0455002638963584, delta=2e-14)
        self.assertTrue(all(self.audit["invalid"]))

    def test_p_values_and_membership_across_range(self):
        for result in self.audit["sweep"]:
            mu = result["mu"]
            reference_p = math.erfc(abs(5 - mu) / (.5 * math.sqrt(2)))
            self.assertAlmostEqual(result["p"], reference_p, delta=2e-14)
            self.assertEqual(result["reject"], reference_p < .05)
            self.assertEqual(result["reject"], not self.audit["lower"] <= mu <= self.audit["upper"])
            self.assertGreaterEqual(result["p"], 0)
            self.assertLessEqual(result["p"], 1)
            self.assertAlmostEqual(result["left"] + result["right"], 2 * mu, delta=2e-15)
            self.assertTrue(result["left"] == 5 or result["right"] == 5)

    def test_closed_endpoints_and_adjacent_floats(self):
        for result in self.audit["edges"]:
            mu = result["mu"]
            expected = not self.audit["lower"] <= mu <= self.audit["upper"]
            self.assertEqual(result["reject"], expected)
            if mu in (self.audit["lower"], self.audit["upper"]):
                self.assertTrue(result["boundary"])
                self.assertFalse(result["reject"])
                self.assertEqual(result["p"], .05)
            else:
                self.assertFalse(result["boundary"])
            self.assertAlmostEqual(result["p"], math.erfc(abs(5 - mu) / (.5 * math.sqrt(2))), delta=2e-14)
        # Rounded labels are not substituted for the unrounded endpoints.
        self.assertLess(4.020018, self.audit["lower"])
        self.assertGreater(5.979982, self.audit["upper"])

    def test_shaded_tails_and_fixed_spread(self):
        for result in self.audit["tailAreas"]:
            self.assertAlmostEqual(result["leftArea"] + result["rightArea"], result["p"], delta=5e-6)
            # Visible tails use slightly different mesh widths; check each
            # against its full-distribution probability at rendering precision.
            self.assertAlmostEqual(result["leftArea"], result["p"] / 2, delta=2.5e-6)
            self.assertAlmostEqual(result["rightArea"], result["p"] / 2, delta=2.5e-6)
            self.assertAlmostEqual(result["centerDensity"], 1 / (.5 * math.sqrt(2 * math.pi)), delta=1e-15)

    def test_finite_sweep_is_continuous_monotone_and_holds_exact_values(self):
        timeline = self.audit["timeline"]
        self.assertEqual(timeline[0]["mu"], 3)
        for previous, current in zip(timeline, timeline[1:]):
            self.assertGreaterEqual(current["mu"], previous["mu"])
            self.assertLessEqual(current["mu"] - previous["mu"], .001)
        for time, state in self.audit["holds"]:
            expected = self.audit["lower"] if time < 3000 else 5 if time < 5800 else self.audit["upper"]
            self.assertEqual(state["mu"], expected)
            self.assertTrue(state["message"])
        self.assertTrue(timeline[-1]["complete"])
        self.assertTrue(self.audit["final"]["complete"])
        self.assertEqual(self.audit["final"]["mu"], 7)
        self.assertEqual(self.audit["duration"], 10600)


if __name__ == "__main__":
    unittest.main()
