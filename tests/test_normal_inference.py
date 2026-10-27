"""Check the actual JavaScript simulation and inference against Python references."""

import json
import math
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / 'sources' / 'normal-inference.html'
NODE = shutil.which('node')


@unittest.skipUnless(NODE, 'Node.js is required for the visualization math')
class NormalInferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = re.search(r'<script id="normal-inference-math">(.*?)</script>',
                           SOURCE.read_text(), re.S).group(1)
        harness = r'''
const fs = require('node:fs'), vm = require('node:vm');
const model = vm.runInNewContext(fs.readFileSync(0, 'utf8') + '\n;NormalInferenceMath');
const before = JSON.stringify([model.nullCounts, model.bootstrapCounts]);
const tests = Array.from({length:41}, (_, i) => model.testResult(i + 30));
const intervals = Array.from({length:20}, (_, i) => model.intervalResult((i + 80) / 100));
const rejects = (fn, values) => values.map(value => {
  try {fn(value); return false;} catch (e) {return e.name === 'RangeError';}
});
console.log(JSON.stringify({
  tests, intervals,
  nullCounts:model.nullCounts, bootstrapCounts:model.bootstrapCounts,
  bins:[model.nullBins, model.bootstrapBins],
  cdf:Array.from({length:801}, (_, i) => [(i-400)/100, model.normalCDF((i-400)/100)]),
  densities:[.3,.4,.5,.6,.7,.8].map(x => [x, model.density(x, .5, model.TEST_SE)]),
  testSE:model.TEST_SE, ciSE:model.CI_SE,
  unchanged:before === JSON.stringify([model.nullCounts, model.bootstrapCounts]),
  deterministic:JSON.stringify(model.simulateNull()) === JSON.stringify(model.nullCounts)
    && JSON.stringify(model.bootstrap()) === JSON.stringify(model.bootstrapCounts),
  rejected:[...rejects(model.testResult, [29,71,30.5,NaN,Infinity]),
    ...rejects(model.intervalResult, [.79,1,NaN,Infinity]),
    ...rejects(model.normalCDF, [-4.01,4.01,NaN])]
}));
'''
        result = subprocess.run([NODE, '-e', harness], input=script,
                                text=True, capture_output=True, check=True)
        cls.audit = json.loads(result.stdout)

    def test_normal_cdf_and_density_against_independent_reference(self):
        for z, value in self.audit['cdf']:
            self.assertAlmostEqual(value, .5 * math.erfc(-z / math.sqrt(2)), delta=2e-14)
        for x, value in self.audit['densities']:
            self.assertAlmostEqual(value, statistics.NormalDist(.5, .05).pdf(x), delta=1e-13)
        self.assertAlmostEqual(self.audit['testSE'], .05)
        self.assertAlmostEqual(self.audit['ciSE'], math.sqrt(.6 * .4 / 100))

    def test_test_tails_include_ties_and_both_sides(self):
        draws = self.audit['nullCounts']
        for count, result in enumerate(self.audit['tests'], start=30):
            distance = abs(count - 50)
            extreme = sum(abs(draw - 50) >= distance for draw in draws)
            self.assertEqual(result['extreme'], extreme)
            self.assertEqual(result['simulation'], extreme / len(draws))
            self.assertAlmostEqual(result['normal'], math.erfc(distance / (5 * math.sqrt(2))), delta=3e-14)
            self.assertAlmostEqual(result['lower'], (50 - distance) / 100)
            self.assertAlmostEqual(result['upper'], (50 + distance) / 100)
        at_center = self.audit['tests'][20]
        self.assertEqual(at_center['extreme'], 1000)
        self.assertEqual(at_center['normal'], 1)
        # Compare the simulated tails to the exact discrete null, allowing Monte Carlo error.
        default = self.audit['tests'][30]
        exact = sum(math.comb(100, k) / 2**100 for k in range(101) if abs(k - 50) >= 10)
        self.assertLess(abs(default['simulation'] - exact), 4 * math.sqrt(exact * (1 - exact) / 1000))

    def test_p_values_decrease_with_distance_from_null(self):
        previous = self.audit['tests'][20]
        for result in self.audit['tests'][21:]:
            self.assertLessEqual(result['simulation'], previous['simulation'])
            self.assertLess(result['normal'], previous['normal'])
            previous = result
        for left, right in zip(self.audit['tests'], reversed(self.audit['tests'])):
            self.assertEqual(left['simulation'], right['simulation'])
            self.assertAlmostEqual(left['normal'], right['normal'])

    def test_interval_endpoints_and_coverage_target(self):
        # Python's inclusive quantiles independently implement type-7 percentiles.
        draws = self.audit['bootstrapCounts']
        quantiles = statistics.quantiles(draws, n=200, method='inclusive')
        previous = None
        for level, result in enumerate(self.audit['intervals'], start=80):
            tail_index = 100 - level
            expected = [quantiles[tail_index - 1] / 100, quantiles[200 - tail_index - 1] / 100]
            for actual, reference in zip(result['bootstrap'], expected):
                self.assertAlmostEqual(actual, reference, delta=1e-13)
            z = statistics.NormalDist().inv_cdf((1 + level / 100) / 2)
            self.assertAlmostEqual(result['z'], z, delta=2e-13)
            for actual, reference in zip(result['normal'], [.6 - z * math.sqrt(.0024), .6 + z * math.sqrt(.0024)]):
                self.assertAlmostEqual(actual, reference, delta=2e-14)
            included = sum(expected[0] - 1e-12 <= x / 100 <= expected[1] + 1e-12 for x in draws)
            self.assertEqual(result['included'], included)
            if previous:
                for method in ['bootstrap', 'normal']:
                    self.assertLessEqual(result[method][0], previous[method][0])
                    self.assertGreaterEqual(result[method][1], previous[method][1])
            previous = result

    def test_simulation_moments_bin_mass_and_reproducibility(self):
        self.assertTrue(self.audit['deterministic'])
        self.assertTrue(self.audit['unchanged'])
        self.assertTrue(all(self.audit['rejected']))
        for draws, bins, p in zip([self.audit['nullCounts'], self.audit['bootstrapCounts']], self.audit['bins'], [.5, .6]):
            self.assertEqual(len(draws), 1000)
            self.assertTrue(all(isinstance(x, int) and 0 <= x <= 100 for x in draws))
            self.assertEqual(sum(bins), 1000)
            self.assertEqual(bins, [draws.count(k) for k in range(101)])
            self.assertAlmostEqual(sum(count / (1000 * .01) * .01 for count in bins), 1)
            # Verify that every generated dot fits the fixed plot domain.
            self.assertGreaterEqual(min(draws) / 100 - .005, .25)
            self.assertLessEqual(max(draws) / 100 + .005, .85)
            self.assertLessEqual(max(bins) / 10, 11)
            self.assertLess(abs(statistics.mean(draws) - 100 * p), .5)
            self.assertLess(abs(statistics.variance(draws) - 100 * p * (1 - p)), 3)


if __name__ == '__main__':
    unittest.main()
