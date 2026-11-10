# Module 6 diagrams

Two Excalidraw diagrams use editable shapes and labels, with embedded SVG formula images.
They were rendered and visually reviewed in the official full Excalidraw editor on November 10, 2026.
No additional MCP server or third-party browser plugin was installed.

| Diagram | Editable scene | Reviewed PNG | Vector export |
| --- | --- | --- | --- |
| Topics 1–5 overview | [Excalidraw](module6-overview.excalidraw) | [PNG](module6-overview.png) | [SVG](module6-overview.svg) |
| Continuous one-proportion CI/HT workflow | [Excalidraw](one-proportion-workflow.excalidraw) | [PNG](one-proportion-workflow.png) | [SVG](one-proportion-workflow.svg) |

## Teaching source and scope

The source of truth is `/Users/wei/Documents/GitHub/STAT250-instruct`.
The preceding source inspection verified the registered originals with `make source-check` and visually checked the original Topic 1 conditions.

- Overview: `modules/module6/module_preamble.tex` and the module map on original M06 T01 slide 1.
- Paired-data distinction: `modules/module6/topic5/sections/01-paired-study-designs.tex` and `02-one-sample-of-differences.tex`.
- One proportion: `source-materials/originals/22sum STAT 250 M06 T01 Inference on the Proportion.pdf`, slides 32, 36–38, 44–49, and 51–55.
- Explicit design and independence checks: `modules/module6/topic1/sections/02-sampling-distribution.tex`, `03-confidence-intervals.tex`, and `04-hypothesis-tests.tex`.

The diagram preserves the course threshold of at least 10 successes and failures, using observed counts for the confidence interval and null expected counts for the hypothesis test.
It uses the slide deck's Normal/Wald interval and null-based z test.
All hypothesis-test formulas use the slide deck's `p₀` notation for the null value.
The confidence interval is centered at the observed estimate, whereas the null sampling distribution of the sample proportion is centered at the null claim.
The standardized null reference is centered at zero.
No numerical sampling-fraction cutoff or automatic simulation fallback was added.
The revised overview includes Topic 5, the population mean of within-pair differences, with parameter `μ_d`.
It contrasts independent groups in Topic 4 with repeated observations on the same units or matched pairs in Topic 5.
Its subtitle is simply “Overview”; the earlier start-here note, inference-task footer, scope footer, and source footer were removed from the canvas.
Source provenance remains recorded here.
Both diagrams use Excalifont for native text; the formula SVGs retain their mathematical typography.
The revised Topic 1 workflow uses consistent red boxes for sampling-design and observed/null expected count checks.
It labels the three test directions and gives `z* ≈ 2` as a quick approximation specifically for 95% confidence.
The requested explanatory notes and source/notation footers were removed from the canvas.

## SVG formula workflow

Follow the [explicit authoring, SVG insertion, export, and validation steps](../README.md#exact-svg-formula-workflow) for future diagrams.

The formula-image bridge is implemented in [`scripts/build_excalidraw_module6.py`](../../../scripts/build_excalidraw_module6.py).
It uses the already installed Typst 0.14.2 to render transparent SVGs with glyph outlines, then embeds the SVG bytes in each native scene's `files` collection.
This implements the proposed SVG approach; it is not a new Excalidraw math-element plugin.
The official MCP widget tested on November 10, 2026 passed empty or null image-file collections, so these image-bearing scenes were assembled in the full editor instead of `create_view`.

The `FORMULAS` dictionary and diagram layout in the generator are the reproducible sources.
Generated `.typ` files and `.svg` formula assets are retained under `formulas/` for inspection and reuse.
No external image URLs are required to reopen the native scenes.
The formula objects have `customData.formulaSource` references, and card contents are grouped so their text and formulas move together.
An equation is editable as an image object's position and size; changing its mathematics requires editing the source and regenerating it.

Rebuild from the repository root:

```sh
python3 scripts/build_excalidraw_module6.py
```

To rebuild only the overview, use `python3 scripts/build_excalidraw_module6.py --diagram overview`.
To rebuild only the one-proportion workflow, use `python3 scripts/build_excalidraw_module6.py --diagram detailed`.

Rebuilding replaces the two generated native scenes; preserve any manual editor changes before running it.
It does not regenerate the reviewed full-diagram PNG/SVG exports; those must be exported again after importing the revised scenes.
The formula-import smoke fixture goes to ignored `build/excalidraw-smoke/`.

## Verification

- The one-formula import smoke check rendered the hat, radical, fraction, and subscript correctly in the full editor.
- The revised overview contains 42 native elements and five embedded formula SVGs.
- The detailed workflow contains 96 native elements and 15 embedded formula SVGs.
- Both scenes were imported through the editor's context-menu Paste action, using native elements and embedded files in an `excalidraw/clipboard` payload.
- Both were exported through the editor's Copy actions to PNG, SVG, and editable clipboard data.
- Roundtrip checks confirmed identical element-type counts and text, all image references, retained formula-source metadata, and identical SVG viewBoxes and glyph paths.
- Excalidraw sanitizes SVG markup on import, so byte-for-byte equality of the SVG serialization is not the appropriate check.
- The saved `.excalidraw` files contain the editor-normalized elements/files recovered through Copy, wrapped in the native version-2 document format.
- Final PNGs were visually reviewed; arrow crossings over text were corrected.
- Export dimensions: overview 3480 × 1750; detailed workflow 3130 × 5480.
- The Topic 1 revision passed text, font, image-reference, alert-color, and formula glyph-path roundtrip checks; the overview's native, PNG, and SVG files retained their prior SHA-256 digests.

The automated browser's native file-picker path remains unverified; the clipboard import/export path is the tested route.
The two editor tabs are working copies; the local `.excalidraw` files are the durable artifacts.
This local checkpoint does not publish the course site or push to a remote.
Run `python3 scripts/validate_excalidraw.py` for repeatable offline integrity checks.
