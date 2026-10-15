"""Audit the browser's normal-model design and plotted areas independently."""

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "sources" / "sample-size-mde.html"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required to exercise the JavaScript model")
class MinimumDetectableEffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = re.search(r'<script id="mde-math">(.*?)</script>', SOURCE.read_text(), re.S).group(1)
        audit = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const model = vm.runInNewContext(fs.readFileSync(0, 'utf8') + '\n;MDEMath');
const integrate = points => points.slice(1).reduce((sum, [x, y], i) => {
  const [previousX, previousY] = points[i];
  return sum + (x - previousX) * (y + previousY) / 2;
}, 0);
const sweep = Array.from({length: 9976}, (_, i) => model.design(i + 25));
const areas = model.PRESETS.map(n => {
  const {se, cutoff, mde} = model.design(n);
  return {n,
    alpha: integrate(model.curvePoints(cutoff, 8 * se, 0, se)),
    beta: integrate(model.curvePoints(mde - 8 * se, cutoff, mde, se)),
    power: integrate(model.curvePoints(cutoff, mde + 8 * se, mde, se)),
    total: integrate(model.curvePoints(mde - 8 * se, mde + 8 * se, mde, se)),
    densities: [-2, 0, .5, 2].map(z => [z, model.density(mde + z * se, mde, se)])
  };
});
const rejects = (fn, values) => values.map(value => {
  try { fn(value); return false; } catch (error) { return error.name === 'RangeError'; }
});
console.log(JSON.stringify({sweep, areas, range: model.FIXED_RANGE,
  roundTrips: sweep.every(({n}) => model.sampleSize(model.sliderPosition(n)) === n),
  slider: Array.from({length: 1001}, (_, i) => model.sampleSize(i / 1000)),
  invalidN: rejects(model.design, [0, 24, 10001, 25.1, NaN, Infinity, '25']),
  invalidPosition: rejects(model.sampleSize, [-.01, 1.01, NaN, Infinity])
}));
"""
        result = subprocess.run([NODE, "-e", audit], input=script, text=True,
                                capture_output=True, check=True)
        cls.audit = json.loads(result.stdout)

    def test_every_integer_sample_size_meets_design_targets(self):
        previous = None
        for result in self.audit["sweep"]:
            se, cutoff, mde = result["se"], result["cutoff"], result["mde"]
            self.assertAlmostEqual(se, 2 / math.sqrt(result["n"]), delta=1e-15)
            alpha = .5 * math.erfc(cutoff / se / math.sqrt(2))
            beta = .5 * math.erfc((mde - cutoff) / se / math.sqrt(2))
            self.assertAlmostEqual(alpha, .05, delta=2e-14)
            self.assertAlmostEqual(beta, .20, delta=2e-14)
            self.assertAlmostEqual(result["alpha"], alpha, delta=2e-14)
            self.assertAlmostEqual(result["beta"], beta, delta=2e-14)
            self.assertAlmostEqual(result["power"], .80, delta=2e-14)
            self.assertEqual(result["nullMean"], 0)
            self.assertEqual(result["sigma"], 2)
            self.assertEqual(result["alternative"], mde)
            self.assertGreater(mde, cutoff)
            self.assertGreater(cutoff, 0)
            if previous:
                self.assertLess(mde, previous["mde"])
            previous = result

    def test_numerical_checkpoints_and_inverse_square_root_scaling(self):
        checkpoints = [(25, .4, .657941, .994590), (100, .2, .328971, .497295),
                       (400, .1, .164485, .248647), (1600, .05, .082243, .124324),
                       (6400, .025, .041121, .062162), (10000, .02, .032897, .049729)]
        for n, se, cutoff, mde in checkpoints:
            result = self.audit["sweep"][n - 25]
            self.assertAlmostEqual(result["se"], se, delta=1e-15)
            self.assertAlmostEqual(result["cutoff"], cutoff, delta=5e-7)
            self.assertAlmostEqual(result["mde"], mde, delta=5e-7)
        for n in range(25, 2501):
            small, large = self.audit["sweep"][n - 25], self.audit["sweep"][4 * n - 25]
            for key in ("se", "cutoff", "mde"):
                self.assertAlmostEqual(large[key], small[key] / 2, delta=1e-15)

    def test_rendered_curve_areas_and_densities(self):
        for result in self.audit["areas"]:
            for name, target in [("alpha", .05), ("beta", .20), ("power", .80), ("total", 1)]:
                self.assertAlmostEqual(result[name], target, delta=5e-6)
            se = 2 / math.sqrt(result["n"])
            for z, density in result["densities"]:
                expected = math.exp(-z * z / 2) / (se * math.sqrt(2 * math.pi))
                self.assertAlmostEqual(density, expected, delta=2e-14)
        self.assertAlmostEqual(self.audit["range"][0], -1.6, delta=1e-15)
        self.assertAlmostEqual(self.audit["range"][1], 2.5945899442097547, delta=1e-14)

    def test_slider_round_trips_and_invalid_inputs(self):
        self.assertTrue(self.audit["roundTrips"])
        self.assertEqual(self.audit["slider"][0], 25)
        self.assertEqual(self.audit["slider"][-1], 10000)
        self.assertEqual(self.audit["slider"], sorted(self.audit["slider"]))
        self.assertTrue(all(self.audit["invalidN"]))
        self.assertTrue(all(self.audit["invalidPosition"]))


if __name__ == "__main__":
    unittest.main()
