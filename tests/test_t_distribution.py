"""Check the standalone t visualization's actual JavaScript numerical routines.

Uses the handoff's reference cases, Python's normal functions, and the exact
Cauchy identities for df=1. SciPy is not a runtime or test dependency.
"""

import json
import math
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / 'sources' / 't-distribution.html'
NODE = shutil.which('node')


@unittest.skipUnless(NODE, 'Node.js is required to check the JavaScript model')
class TDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = SOURCE.read_text()
        script = re.search(r'<script id="t-distribution-math">(.*?)</script>', html, re.S)[1]
        harness = r'''
const m = TDistributionMath;
const dfs = [1, 2, 5, 15, 30, 100, 1000];
const xs = [0, 1e-8, .1, .5, 1, 2, 3, 5, 10];
const ps = [.0005, .001, .005, .025, .05, .1, .2];
const rejects = fn => { try {fn(); return false;} catch (e) {return e.name === 'RangeError';} };
console.log(JSON.stringify({
  tails: dfs.flatMap(df => xs.map(x => ({df, x, sf: m.tSF(x, df),
    negative: m.tSF(-x, df), pdf: m.tPDF(x, df), negativePDF: m.tPDF(-x, df)}))),
  quantiles: dfs.flatMap(df => ps.map(p => {
    const q = m.tISF(p, df); return {df, p, q, roundtrip: m.tSF(q, df)};
  })),
  normal: xs.map(x => ({x, sf: m.normalSF(x), negative: m.normalSF(-x)})),
  normalQ: ps.map(p => ({p, q: m.normalISF(p)})),
  invalid: [
    ...[0, 1001, 2.5, NaN, Infinity].map(df => rejects(() => m.tSF(2, df))),
    ...[NaN, Infinity, -Infinity].map(x => rejects(() => m.tSF(x, 5))),
    ...[0, .00049, .21, NaN].map(p => rejects(() => m.normalISF(p)))
  ]
}));
'''
        run = subprocess.run([NODE, '-e', script + harness], text=True,
                             capture_output=True, check=True)
        cls.audit = json.loads(run.stdout)

    def test_reference_cases_from_handoff(self):
        tails = {(r['df'], r['x']): r['sf'] for r in self.audit['tails']}
        self.assertAlmostEqual(tails[5, 2], .05096974, delta=1e-8)
        self.assertAlmostEqual(2 * tails[5, 2], .10193948, delta=1e-8)
        normal = {r['x']: r['sf'] for r in self.audit['normal']}
        self.assertAlmostEqual(normal[2], .02275013, delta=1e-8)
        self.assertAlmostEqual(2 * normal[2], .04550026, delta=1e-8)
        quantiles = {(r['df'], r['p']): r['q'] for r in self.audit['quantiles']}
        for df, cutoff in [(5, 2.57058184), (15, 2.13144955), (30, 2.04227246)]:
            self.assertAlmostEqual(quantiles[df, .025], cutoff, delta=1e-8)
        self.assertAlmostEqual(next(r['q'] for r in self.audit['normalQ']
                                    if r['p'] == .025), 1.95996398, delta=1e-8)

    def test_normal_tails_against_erfc_and_quantiles(self):
        for row in self.audit['normal']:
            expected = .5 * math.erfc(row['x'] / math.sqrt(2))
            self.assertAlmostEqual(row['sf'], expected, delta=max(1e-30, expected * 1e-12))
            self.assertAlmostEqual(row['sf'] + row['negative'], 1, delta=1e-15)
        for row in self.audit['normalQ']:
            self.assertAlmostEqual(row['q'], statistics.NormalDist().inv_cdf(1 - row['p']), delta=1e-12)

    def test_cauchy_distribution_and_extreme_cutoff(self):
        for row in self.audit['tails']:
            if row['df'] != 1:
                continue
            self.assertAlmostEqual(row['sf'], .5 - math.atan(row['x']) / math.pi, delta=1e-13)
            self.assertAlmostEqual(row['pdf'], 1 / (math.pi * (1 + row['x'] ** 2)), delta=1e-13)
        for row in self.audit['quantiles']:
            if row['df'] == 1:
                self.assertAlmostEqual(row['q'], 1 / math.tan(math.pi * row['p']), delta=1e-9)

    def test_symmetry_heavy_tails_and_convergence(self):
        normal = {r['x']: r['sf'] for r in self.audit['normal']}
        for row in self.audit['tails']:
            self.assertAlmostEqual(row['sf'] + row['negative'], 1, delta=1e-15)
            self.assertEqual(row['pdf'], row['negativePDF'])
            if row['x'] == 0:
                self.assertEqual(row['sf'], .5)
            else:
                self.assertGreater(row['sf'], normal[row['x']])
        tails = {(r['df'], r['x']): r['sf'] for r in self.audit['tails']}
        for x in [.5, 1, 2, 3, 5]:
            values = [tails[df, x] for df in [1, 2, 5, 15, 30, 100, 1000]]
            self.assertEqual(values, sorted(values, reverse=True))
            self.assertLess(abs(values[-1] - normal[x]), .0002)

    def test_quantile_roundtrips_and_two_tail_allocation(self):
        normal = {r['p']: r['q'] for r in self.audit['normalQ']}
        for row in self.audit['quantiles']:
            self.assertAlmostEqual(row['roundtrip'], row['p'], delta=1e-12)
            self.assertAlmostEqual(2 * row['roundtrip'], 2 * row['p'], delta=2e-12)
            self.assertGreater(row['q'], normal[row['p']])

    def test_invalid_model_inputs(self):
        self.assertTrue(all(self.audit['invalid']))

    def test_standalone_has_no_external_dependencies(self):
        html = SOURCE.read_text()
        self.assertNotRegex(html, r'<(?:script|link|img)[^>]+(?:src|href)=')
        self.assertNotRegex(html, r'\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(')
        self.assertEqual(html.count('<!-- SHARED_THEME -->'), 1)
        self.assertEqual(html.count('<!-- AUTHORSHIP -->'), 1)


if __name__ == '__main__':
    unittest.main()
