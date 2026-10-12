"""Independent statistical checks for the standalone Galton board's pure script.

Node executes the source's math API without a DOM; Python supplies the independent
binomial formula and sampling-error bounds. Animation timing needs separate browser QA.
"""

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "sources" / "galton-board.html"
NODE = shutil.which("node")
NODE_AUDIT = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {script, uiRows} = JSON.parse(fs.readFileSync(0, 'utf8'));
const api = vm.runInNewContext(script + '\n;GaltonMath', {});
const probabilities = [0, .05, .5, .95, 1];
const pmfs = [];
for (let n = 1; n <= 64; n++) {
  for (const p of probabilities) pmfs.push({n, p, values:api.binomialProbabilities(n, p)});
}

// Deterministic coin draws check the path independently of the PMF routine.
let pathsChecked = 0;
for (const n of uiRows) {
  for (let k = 0; k <= n; k++) {
    let draws = 0;
    const path = api.samplePath(n, .5, () => draws++ < k ? 0 : .999999);
    assert.deepEqual(Array.from(path), Array.from({length:n + 1}, (_, i) => Math.min(i, k)));
    assert.equal(draws, n);
    assert.equal(Object.isFrozen(path), true);
    pathsChecked++;
  }
  assert.deepEqual(Array.from(api.samplePath(n, 0, () => 0)), Array(n + 1).fill(0));
  assert.deepEqual(Array.from(api.samplePath(n, 1, () => .999999)), Array.from({length:n + 1}, (_, i) => i));
}

function seeded(seed) {
  let state = seed >>> 0;
  return () => {
    state ^= state << 13; state ^= state >>> 17; state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}
const simulations = [];
for (const n of uiRows) {
  for (const p of probabilities) {
    const rng = seeded(0x4f29a817 ^ (n << 16) ^ Math.round(p * 10000));
    const run = api.createRun(n, p);
    for (let i = 0; i < 20000; i++) {
      const ball = api.releaseBall(run, rng);
      assert.equal(ball.path.length, n + 1);
      assert.equal(ball.path[0], 0);
      for (let j = 1; j <= n; j++) {
        const change = ball.path[j] - ball.path[j - 1];
        assert.ok(change === 0 || change === 1);
      }
      assert.equal(ball.bin, ball.path[n]);
      assert.equal(api.completeBall(run, ball), true);
      assert.equal(api.completeBall(run, ball), false);
    }
    assert.equal(run.balls.length, 0);
    assert.equal(run.counts.reduce((a, b) => a + b, 0), run.total);
    simulations.push({n, p, count:run.total, counts:run.counts});
  }
}

// A reset invalidates in-flight and completed results, even if IDs are reused.
const accounting = [];
for (const changeSettings of [false, true]) {
  const run = api.createRun(12, .5);
  const landed = api.releaseBall(run, () => .25);
  const stale = api.releaseBall(run, () => .75);
  assert.equal(api.completeBall(run, landed), true);
  const generation = run.generation;
  if (changeSettings) api.resetRun(run, 8, 1);
  else api.resetRun(run);
  assert.equal(run.generation, generation + 1);
  assert.equal(run.total, 0);
  assert.equal(run.balls.length, 0);
  assert.equal(run.counts.length, run.rows + 1);
  assert.ok(run.counts.every(count => count === 0));
  const fresh = api.releaseBall(run, () => .4);
  const foreignRun = api.createRun(run.rows, run.p);
  const foreign = api.releaseBall(foreignRun, () => .4);
  assert.equal(api.completeBall(run, stale), false);
  assert.equal(api.completeBall(run, landed), false);
  assert.equal(api.completeBall(run, foreign), false);
  assert.equal(run.total, 0);
  assert.equal(run.balls.length, 1);
  assert.equal(api.completeBall(run, fresh), true);
  assert.equal(api.completeBall(run, fresh), false);
  assert.equal(run.total, 1);
  assert.equal(run.counts[fresh.bin], 1);
  assert.equal(run.counts.reduce((a, b) => a + b, 0), 1);
  accounting.push({rows:run.rows, p:run.p, total:run.total, bin:fresh.bin});
}

let invalidInputsChecked = 0;
for (const [n, p] of [[0, .5], [65, .5], [2.5, .5], [12, -.01], [12, 1.01], [12, NaN]]) {
  assert.throws(() => api.createRun(n, p), {name:'RangeError'});
  invalidInputsChecked++;
}
for (const draw of [-.01, 1, Infinity, NaN]) {
  assert.throws(() => api.samplePath(12, .5, () => draw), {name:'RangeError'});
  invalidInputsChecked++;
}
process.stdout.write(JSON.stringify({pmfs, simulations, pathsChecked, accounting, invalidInputsChecked}));
"""


@unittest.skipUnless(NODE, "Node.js is needed to execute the standalone JavaScript math API")
class GaltonMathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = SOURCE.read_text()
        scripts = re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", source)
        pure_scripts = [script for script in scripts if "const GaltonMath =" in script]
        if len(pure_scripts) != 1:
            raise AssertionError("Expected one standalone GaltonMath script")
        slider = re.search(r'<input\b[^>]*\bid="rows"[^>]*>', source).group(0)
        bounds = {key: int(re.search(rf'\b{key}="(\d+)"', slider).group(1))
                  for key in ("min", "max", "step")}
        cls.ui_rows = list(range(bounds["min"], bounds["max"] + 1, bounds["step"]))
        completed = subprocess.run(
            [NODE, "-e", NODE_AUDIT],
            input=json.dumps({"script": pure_scripts[0], "uiRows": cls.ui_rows}),
            text=True, capture_output=True, timeout=45,
        )
        if completed.returncode:
            raise AssertionError(completed.stderr)
        cls.audit = json.loads(completed.stdout)

    def test_pmf_matches_independent_binomial_formula(self):
        for item in self.audit["pmfs"]:
            n, p, values = item["n"], item["p"], item["values"]
            with self.subTest(n=n, p=p):
                self.assertEqual(len(values), n + 1)
                for k, observed in enumerate(values):
                    expected = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
                    self.assertTrue(math.isclose(observed, expected, rel_tol=2e-13, abs_tol=2e-15))

    def test_pmf_normalization_mean_and_variance(self):
        for item in self.audit["pmfs"]:
            n, p, values = item["n"], item["p"], item["values"]
            with self.subTest(n=n, p=p):
                self.assertTrue(all(0 <= value <= 1 for value in values))
                self.assertAlmostEqual(sum(values), 1, delta=2e-14)
                self.assertAlmostEqual(sum(k * value for k, value in enumerate(values)), n * p, delta=2e-12)
                variance = sum((k - n * p) ** 2 * value for k, value in enumerate(values))
                self.assertAlmostEqual(variance, n * p * (1 - p), delta=2e-12)

    def test_seeded_paths_have_binomial_empirical_moments(self):
        for item in self.audit["simulations"]:
            n, p, count, bins = item["n"], item["p"], item["count"], item["counts"]
            with self.subTest(n=n, p=p):
                self.assertEqual(count, 20000)
                self.assertEqual(sum(bins), count)
                mean = sum(k * number for k, number in enumerate(bins)) / count
                variance = sum((k - mean) ** 2 * number for k, number in enumerate(bins)) / (count - 1)
                target_variance = n * p * (1 - p)
                mean_se = math.sqrt(target_variance / count)
                fourth_moment = 3 * target_variance ** 2 + target_variance * (1 - 6 * p * (1 - p))
                variance_se = math.sqrt(max(0, (fourth_moment - (count - 3) / (count - 1) * target_variance ** 2) / count))
                self.assertAlmostEqual(mean, n * p, delta=7 * mean_se + 1e-12)
                self.assertAlmostEqual(variance, target_variance, delta=7 * variance_se + 1e-12)

    def test_paths_count_once_and_match_each_injected_decision(self):
        self.assertEqual(self.audit["pathsChecked"], sum(n + 1 for n in self.ui_rows))
        self.assertEqual(len(self.audit["simulations"]), 5 * len(self.ui_rows))

    def test_reset_and_settings_change_reject_stale_duplicate_and_foreign_arrivals(self):
        self.assertEqual(self.audit["accounting"], [
            {"rows": 12, "p": .5, "total": 1, "bin": 12},
            {"rows": 8, "p": 1, "total": 1, "bin": 8},
        ])

    def test_invalid_settings_and_random_draws_are_rejected(self):
        self.assertEqual(self.audit["invalidInputsChecked"], 10)


if __name__ == "__main__":
    unittest.main()
