#!/usr/bin/env python3
"""Build M6T5 from the existing one-mean layout, with paired-data semantics.

Writes only a candidate unless --output names a deliberate destination. The
reviewed native scene and full exports must be recovered from the editor.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from build_excalidraw_inference import workflow
from build_excalidraw_module6 import COLORS, FORMULAS, OUT

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path.home() / '.codex/skills/excalidraw-math'
NAME = 'paired-differences-workflow'
EXPRESSIONS = {
    't5-difference': 'd_i = A_i - B_i',
    't5-parameter': 'mu_d quad "estimated by" quad overline(d)',
    't5-df': '"df" = n - 1',
    't5-ci-se': '"SE" = s_d / sqrt(n)',
    't5-ci-center': '"Center" = overline(d)',
    't5-ht-center': '"Null center" = mu_(d,0)',
    't5-ci': 'overline(d) plus.minus t^* s_d / sqrt(n)',
    't5-stat': 't_"obs" = (overline(d) - mu_(d,0)) / (s_d / sqrt(n))',
    't5-null': 'H_0: mu_d = mu_(d,0)',
    't5-alt': 'H_a: mu_d > mu_(d,0), quad mu_d < mu_(d,0), quad "or" quad mu_d != mu_(d,0)',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/excalidraw-m6t5/candidate')
    parser.add_argument('--force-formulas', action='store_true')
    args = parser.parse_args()
    profile_path = OUT / f'{NAME}.style.json'
    profile = json.loads(profile_path.read_text())
    # Match the existing course series; these settings drive the builder.
    COLORS.update(profile['series_colors'])
    spec = importlib.util.spec_from_file_location('render_formula', SKILL / 'scripts/render_formula.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    formulas = {}
    for name, expression in EXPRESSIONS.items():
        metadata_path = OUT / 'formulas' / f'{name}.json'
        if not metadata_path.exists() or args.force_formulas:
            renderer.render(expression, 'typst', OUT / 'formulas', name, profile,
                            color=COLORS['ink'], force=args.force_formulas)
        meta = json.loads(metadata_path.read_text())
        if meta['expression'] != expression:
            raise ValueError(f'{name} changed; use --force-formulas for an intentional revision')
        svg = (OUT / 'formulas' / f'{name}.svg').read_bytes()
        formulas[name] = {'svg': svg, 'width': meta['width'], 'height': meta['height']}
    # Reuse shared tail/decision formulas without rewriting existing artifacts.
    for name in ['decision', 't-right', 't-left', 't-two']:
        data = (OUT / 'formulas' / f'{name}.svg').read_bytes()
        bounds = [float(n) for n in ET.fromstring(data).attrib['viewBox'].split()]
        formulas[name] = {'svg': data, 'width': bounds[2], 'height': bounds[3]}
    FORMULAS.update(EXPRESSIONS)
    mapping = {name.replace('t5-', 't3-'): name for name in EXPRESSIONS if name != 't5-difference'}
    for old, new in mapping.items():
        formulas[old] = formulas[new]
    scene = workflow(3, formulas, save=False)
    scene.name = NAME
    for element in scene.elements:
        if element['y'] >= 155:
            element['y'] += 340
        if element['type'] == 'image':
            old = Path(element['customData']['formulaSource']).stem
            if old in mapping:
                new = mapping[old]
                element['customData'] = {'formulaSource': f'formulas/{new}.typ', 'typst': EXPRESSIONS[new],
                                         'equation': {'metadata': f'formulas/{new}.json', 'language': 'typst', 'expression': EXPRESSIONS[new]}}
    texts = {
        'subtitle': 'One-sample t inference applied to within-pair differences',
        'title': 'STAT 250 · Module 6 · Topic 5',
        'define-title': '2  SUMMARIZE ONE SAMPLE OF DIFFERENCES',
        'define-note': 'Count n complete pairs; summarize the differences.\nThe parameter is the population mean difference.',
        'design-title': '3  CHECK THE SAMPLING / ASSIGNMENT DESIGN',
        'design-body': 'Independent differences ACROSS pairs.\nSampling / assignment must support the conclusion.\nWithout replacement: small fraction of pairs.',
        'choose-text': '4  WHAT IS THE QUESTION?',
        'ci-setup-text': 'Choose confidence level C\nFind t* with middle t area C\nUse n pairs for the degrees of freedom',
        'ht-alpha': 'Choose Hₐ; set α. Null value usually 0 (no mean difference).',
        'ci-conditions-title': 'CHECK THE DIFFERENCES',
        'ht-conditions-title': 'CHECK THE DIFFERENCES',
        'ci-conditions-body': 'Differences approximately Normal, or n ≥ 30 pairs.\nFor fewer pairs: inspect difference plots for\nstrong skewness and clear outliers.\nCourse guideline; check influential outliers at every n.',
        'ht-conditions-body': 'Differences approximately Normal, or n ≥ 30 pairs.\nFor fewer pairs: inspect difference plots for\nstrong skewness and clear outliers.\nCourse guideline; check influential outliers at every n.',
        'ci-center-note': 'Use the SD of the DIFFERENCES.\nThe interval is centered at the observed mean difference.',
        'ht-center-note': 'Use the same SD of the DIFFERENCES.\nUnder H₀, center at the claimed population mean difference.',
        'ci-interpret-body': 'We are C% confident that the population\nmean A − B lies between [lower] and [upper].\nState the paired population and units.\nPositive values mean A is higher on average.',
        'ht-reference-distribution': 'T follows t with df = n − 1, centered at 0.',
    }
    for element in scene.elements:
        if element['id'] in texts:
            element['text'] = element['originalText'] = texts[element['id']]
            if element['id'] == 'ht-alpha': element['fontSize'] = 18
            if element['id'] == 'design-body':
                element['fontSize'] = 21
                element['y'] = 446 + 340
            element['height'] = element['fontSize'] * 1.25 * len(element['text'].splitlines())
    scene.box('pairing', 400, 155, 800, 260)
    scene.text('pairing-title', '1  IDENTIFY PAIRS AND DEFINE THE DIFFERENCE', 420, 173, 760, 24)
    scene.text('pairing-design', 'Same unit measured twice, or a meaningful matched pair.\nWithin-pair dependence is expected.', 420, 216, 760, 21)
    difference = scene.formula('t5-difference', 580, 278, 440, 40)
    scene.text('pairing-order', 'Fix A − B before calculating; positive means A is larger.\nOne pair → one difference → one-sample t inference.', 420, 332, 760, 23)
    difference['customData']['equation'] = {'metadata': 'formulas/t5-difference.json', 'language': 'typst', 'expression': EXPRESSIONS['t5-difference']}
    scene.arrow('pairing-summary', [(800,423),(800,487)])
    # Match native labels and geometry to the approved series profile.
    for element in scene.elements:
        if element['type'] == 'text':
            element['fontFamily'] = profile['text']['font_family']
            element['lineHeight'] = profile['text']['line_height']
    scene.save(args.output)
    print(json.dumps({'candidate': str(args.output / f'{NAME}.excalidraw'),
                      'elements': len(scene.elements), 'svg_files': len(scene.files)}, indent=2))


if __name__ == '__main__':
    main()
