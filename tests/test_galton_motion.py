"""Geometry and landing invariants for the standalone Galton board.

These checks execute the pure motion API, without a DOM or browser simulation.
They check positions against stack accounting rather than canvas draw commands.
"""

import json
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
const {math, motion} = vm.runInNewContext(script + '\n;({math:GaltonMath,motion:GaltonMotion})', {});
const near = (actual, expected, tolerance = 1e-8) => {
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);
};
const pointNear = (a, b, tolerance = 1e-8) => {
  for (const key of ['x', 'y', 'radius']) near(a[key], b[key], tolerance);
};
const metrics = {positions:0, boundaries:0, landings:0, reservations:0, stacks:0, contacts:0};

for (const rows of uiRows) {
  const clock = motion.timing(rows);
  for (const width of [240, 320, 390, 768, 1440]) {
    const g = motion.geometry(width, 442, rows);
    for (const decision of ['left', 'right', 'alternating']) {
      let draws = 0;
      const path = math.samplePath(rows, .5, () => {
        if (decision === 'left') return .9;
        if (decision === 'right') return .1;
        return draws++ % 2 ? .9 : .1;
      });
      const run = math.createRun(rows, .5);
      const ball = {id:0, generation:0, path, bin:path[rows], completed:false};
      run.balls.push(ball);
      const expected = math.binomialProbabilities(rows, .5);
      const target = motion.landingSlot(run, ball, expected, g);

      // A ball stays on the board and comes to rest on its own eventual dot.
      for (let i = 0; i <= 600; i++) {
        const position = motion.position(clock.finish * i / 600, path, g, target);
        for (const value of Object.values(position)) assert.ok(Number.isFinite(value));
        assert.ok(position.radius > 0);
        assert.ok(position.x >= -position.radius && position.x <= width + position.radius);
        assert.ok(position.y >= -position.radius && position.y <= g.baseline + 1e-8);
        metrics.positions++;
      }
      pointNear(motion.position(clock.finish, path, g, target), target);
      pointNear(motion.position(clock.finish + 10, path, g, target), target);
      near(target.x, g.binX(path[rows]));

      // Phase changes and contacts must not teleport the ball, including the
      // last physical peg: there is no extra invisible peg below the board.
      const boundaries = [clock.entry, clock.lastContact, clock.landing, clock.finish];
      for (let row = 0; row < rows; row++) boundaries.push(clock.entry + row * clock.step);
      for (const age of new Set(boundaries)) {
        const before = motion.position(Math.max(0, age - 1e-7), path, g, target);
        const after = motion.position(age + 1e-7, path, g, target);
        pointNear(before, after, .001);
        metrics.boundaries++;
      }
    }
  }

  // Reserve positions for equal-duration balls in their release order. A
  // predecessor's completion must neither change a reservation nor count a
  // still-moving ball. Include both degenerate endpoint distributions.
  for (const p of [0, .5, 1]) {
    const g = motion.geometry(320, 442, rows);
    const expected = math.binomialProbabilities(rows, p);
    const run = math.createRun(rows, p);
    let state = 0x52a9e87;
    const rng = () => {
      state ^= state << 13; state ^= state >>> 17; state ^= state << 5;
      return (state >>> 0) / 4294967296;
    };
    for (let i = 0; i < 120; i++) math.releaseBall(run, rng);
    const queue = [...run.balls];
    const reserved = queue.map(ball => motion.landingSlot(run, ball, expected, g));
    assert.equal(run.total, 0);
    assert.ok(run.counts.every(count => count === 0));
    for (let i = 0; i < queue.length; i++) {
      const ball = queue[i];
      const target = motion.landingSlot(run, ball, expected, g);
      pointNear(target, reserved[i]);
      assert.equal(target.index, run.counts[ball.bin]);
      assert.equal(run.total, i);
      const final = motion.position(clock.finish, ball.path, g, target);
      assert.equal(math.completeBall(run, ball), true);
      const stack = motion.stackLayout(run.counts, run.total, expected, g);
      pointNear(final, {
        x:g.binX(ball.bin),
        y:g.baseline - stack.radius - (run.counts[ball.bin] - 1) * stack.dotGap,
        radius:stack.radius,
      });
      assert.equal(run.total, i + 1);
      metrics.landings++;
      metrics.reservations++;
    }
  }

  // Stack compression is linear and remains representable at large totals.
  // This checks geometry, not the cost of drawing a trillion dots.
  for (const width of [240, 1440]) {
    const g = motion.geometry(width, 360, rows);
    for (const p of [0, .5, 1]) {
      const expected = math.binomialProbabilities(rows, p);
      for (const total of [0, 1, 84, 1000, 1000000, 1000000000000]) {
        const counts = Array(rows + 1).fill(0);
        counts[p === 1 ? rows : p === 0 ? 0 : Math.floor(rows / 2)] = total;
        const layout = motion.stackLayout(counts, total, expected, g);
        assert.ok(Number.isFinite(layout.dotGap) && layout.dotGap > 0);
        assert.ok(Number.isFinite(layout.radius) && layout.radius > 0);
        assert.ok(2 * layout.radius <= layout.dotGap + 1e-10);
        assert.ok(2 * layout.radius < g.gap);
        const tallest = Math.max(...counts);
        const occupied = tallest ? 2 * layout.radius + (tallest - 1) * layout.dotGap : 0;
        assert.ok(occupied <= g.plotHeight + 1e-8);
        assert.ok(total * Math.max(...expected) * layout.dotGap <= g.plotHeight + 1e-8);
        metrics.stacks++;
      }
    }
  }

  assert.equal(motion.contactRow(0, rows), -1);
  assert.equal(motion.contactRow(clock.entry, rows), 0);
  assert.equal(motion.contactRow(clock.finish + 10, rows), rows - 1);
  for (const direction of [-1, 1]) {
    const initial = motion.pegOffset(0, direction);
    const settled = motion.pegOffset(10, direction);
    near(initial.x, 0); near(initial.y, 0);
    near(settled.x, 0); near(settled.y, 0);
    for (let i = 0; i <= 100; i++) {
      const offset = motion.pegOffset(i / 100, direction);
      assert.ok(Number.isFinite(offset.x) && Number.isFinite(offset.y));
      assert.ok(Math.hypot(offset.x, offset.y) < 3);
      metrics.contacts++;
    }
  }
}
process.stdout.write(JSON.stringify(metrics));
"""


@unittest.skipUnless(NODE, "Node.js is needed to execute the standalone JavaScript motion API")
class GaltonMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = SOURCE.read_text()
        scripts = re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", source)
        pure_scripts = [script for script in scripts
                        if "const GaltonMath =" in script or "const GaltonMotion =" in script]
        if len(pure_scripts) != 2:
            raise AssertionError("Expected separate standalone GaltonMath and GaltonMotion scripts")
        slider = re.search(r'<input\b[^>]*\bid="rows"[^>]*>', source).group(0)
        bounds = {key: int(re.search(rf'\b{key}="(\d+)"', slider).group(1))
                  for key in ("min", "max", "step")}
        cls.ui_rows = list(range(bounds["min"], bounds["max"] + 1, bounds["step"]))
        completed = subprocess.run(
            [NODE, "-e", NODE_AUDIT],
            input=json.dumps({"script": "\n".join(pure_scripts), "uiRows": cls.ui_rows}),
            text=True, capture_output=True, timeout=30,
        )
        if completed.returncode:
            raise AssertionError(completed.stderr)
        cls.audit = json.loads(completed.stdout)

    def test_finite_continuous_positions_at_contacts_and_landings(self):
        self.assertEqual(self.audit["positions"], len(self.ui_rows) * 5 * 3 * 601)
        self.assertGreater(self.audit["boundaries"], len(self.ui_rows) * 5 * 3 * 8)

    def test_reserved_landing_matches_completed_stack(self):
        self.assertEqual(self.audit["landings"], len(self.ui_rows) * 3 * 120)
        self.assertEqual(self.audit["reservations"], self.audit["landings"])

    def test_compressed_stacks_keep_all_dots_within_plot(self):
        self.assertEqual(self.audit["stacks"], len(self.ui_rows) * 2 * 3 * 6)

    def test_peg_recoil_is_small_and_returns_to_rest(self):
        self.assertEqual(self.audit["contacts"], len(self.ui_rows) * 2 * 101)


if __name__ == "__main__":
    unittest.main()
