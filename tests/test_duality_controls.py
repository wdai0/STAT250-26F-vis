"""Exercise the real control script with a deterministic animation clock.

The lightweight DOM stub tests state transitions and reduced motion; browser
inspection separately checks rendering, actual controls, and focus behavior.
"""

import json
from pathlib import Path
import shutil
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "sources" / "test-ci-duality.html"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is needed for the control script")
class DualityControlTests(unittest.TestCase):
    def test_sweep_lifecycle_visibility_and_reduced_motion(self):
        harness = r"""
const fs = require('node:fs'), vm = require('node:vm');
const html = fs.readFileSync(0, 'utf8');
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
class Element {
  constructor() { this.textWrites = 0; this.textContent = ''; this.events = {}; this.attrs = {}; this.dataset = {}; this.hidden = false; this.disabled = false; }
  set textContent(value) { this.content = value; this.textWrites++; }
  get textContent() { return this.content; }
  addEventListener(type, fn) { this.events[type] = fn; }
  setAttribute(key, value) { this.attrs[key] = value; }
  getAttribute(key) { return this.attrs[key]; }
  getBoundingClientRect() { return {width:0, height:0}; }
  replaceChildren(...children) { this.textContent = children.map(n => n.textContent).join(''); }
  focus() {}
}
const nodes = Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(m => [m[1], new Element()]));
const tabs = ['explore', 'explanation'].map(id => {
  nodes['tab-' + id].attrs['aria-controls'] = id; return nodes['tab-' + id];
});
nodes.explanation.hidden = true;
const shortcuts = ['observed','lower','upper'].map(name => { const node = new Element(); node.dataset.candidate = name; return node; });
const details = new Element(), documentEvents = {}, windowEvents = {}, mediaEvents = {};
let nextFrame = 0;
const frames = new Map(), parent = {}, motion = {matches:false, addEventListener:(type,fn) => mediaEvents[type] = fn};
const document = {
  hidden:false,
  querySelector: selector => selector === '.check-question' ? details : nodes[selector.slice(1)],
  querySelectorAll: selector => selector === '[role="tab"]' ? tabs : selector === '[data-candidate]' ? shortcuts : [],
  getElementById: id => nodes[id],
  createElement: () => new Element(),
  createTextNode: text => ({textContent:text}),
  addEventListener: (type,fn) => documentEvents[type] = fn
};
const window = {parent, location:{origin:'http://localhost'}, addEventListener:(type,fn) => windowEvents[type] = fn};
vm.runInNewContext(scripts, {
  document, window, matchMedia:() => motion,
  getComputedStyle:() => ({getPropertyValue:() => '#000'}),
  ResizeObserver:class {observe() {}},
  requestAnimationFrame:fn => {frames.set(++nextFrame, fn); return nextFrame;},
  cancelAnimationFrame:id => frames.delete(id)
});
const click = id => { if (nodes[id].disabled) throw Error(id + ' disabled'); nodes[id].events.click(); };
const step = time => { const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn(time)); };
const state = () => ({mu:nodes['candidate-value'].textContent, p:nodes['p-value'].textContent,
  pause:nodes.pause.textContent, summary:nodes['interval-summary'].textContent,
  status:nodes['sweep-status'].textContent, pending:frames.size,
  explore:!nodes.explore.hidden, decision:nodes.decision.textContent});
const report = {};
click('sweep'); step(0); step(1800); report.lowerHold = state();
click('pause'); report.paused = state(); step(9000); report.afterPause = state();
click('pause'); step(10000); step(11200); report.resumed = state();
nodes.candidate.value = '6'; nodes.candidate.events.input(); report.manual = state();
click('sweep'); step(12000); step(12000 + 10600); report.complete = state();
click('sweep'); step(23000); report.replay = state();
tabs[1].events.click(); report.explanation = state();
click('reset'); report.reset = state();
click('sweep'); step(24000); document.hidden = true; documentEvents.visibilitychange(); report.hidden = state();
document.hidden = false; click('reset'); click('sweep');
windowEvents.message({source:parent, origin:'http://localhost', data:{type:'stat250:visibility', visible:false}}); report.parentHidden = state();
click('reset'); click('sweep'); step(30000);
report.controlWritesBefore = [nodes.sweep.textWrites, nodes.pause.textWrites];
step(30100); step(30200); step(30300);
report.controlWritesAfter = [nodes.sweep.textWrites, nodes.pause.textWrites];
click('reset'); motion.matches = true; click('sweep'); report.reducedMotion = state();
console.log(JSON.stringify(report));
"""
        result = subprocess.run([NODE, "-e", harness], input=SOURCE.read_text(),
                                text=True, capture_output=True, check=True)
        audit = json.loads(result.stdout)
        self.assertEqual(audit["lowerHold"]["p"], "0.05 (boundary)")
        self.assertEqual(audit["paused"], audit["afterPause"])
        self.assertEqual(audit["resumed"]["pending"], 1)
        self.assertEqual(audit["manual"]["pending"], 0)
        self.assertEqual(audit["manual"]["mu"], "6.000000")
        self.assertIn("95% confidence interval", audit["complete"]["summary"])
        self.assertEqual(audit["complete"]["pending"], 0)
        self.assertEqual(audit["replay"]["mu"], "3.000000")
        self.assertEqual(audit["replay"]["pending"], 1)
        self.assertFalse(audit["explanation"]["explore"])
        self.assertEqual(audit["explanation"]["pending"], 0)
        self.assertEqual(audit["reset"]["mu"], "6.000000")
        self.assertEqual(audit["reset"]["p"], "0.0455003")
        self.assertTrue(audit["reset"]["explore"])
        self.assertIn("Sweep or reveal", audit["reset"]["summary"])
        for name in ("hidden", "parentHidden", "reducedMotion"):
            self.assertEqual(audit[name]["pending"], 0)
        self.assertIn("95% confidence interval", audit["reducedMotion"]["summary"])
        self.assertEqual(audit["reducedMotion"]["mu"], "6.000000")
        # A held mouse/key press must retain its label nodes between frames.
        self.assertEqual(audit["controlWritesBefore"], audit["controlWritesAfter"])


if __name__ == "__main__":
    unittest.main()
