# Module 6 diagrams

Six Excalidraw diagrams use editable shapes and labels, with embedded SVG formula images.
The overview and Topics 1–4 were rendered and visually reviewed in the official full Excalidraw editor on November 10, 2026; Topic 5 was added and reviewed on November 12, 2026.
No additional MCP server or third-party browser plugin was installed.

| Diagram | Editable scene | Reviewed PNG | Vector export |
| --- | --- | --- | --- |
| Topics 1–5 overview | [Excalidraw](module6-overview.excalidraw) | [PNG](module6-overview.png) | [SVG](module6-overview.svg) |
| Topic 1: one proportion | [Excalidraw](one-proportion-workflow.excalidraw) | [PNG](one-proportion-workflow.png) | [SVG](one-proportion-workflow.svg) |
| Topic 2: difference in proportions | [Excalidraw](two-proportions-workflow.excalidraw) | [PNG](two-proportions-workflow.png) | [SVG](two-proportions-workflow.svg) |
| Topic 3: one mean | [Excalidraw](one-mean-workflow.excalidraw) | [PNG](one-mean-workflow.png) | [SVG](one-mean-workflow.svg) |
| Topic 4: difference in independent means | [Excalidraw](two-means-workflow.excalidraw) | [PNG](two-means-workflow.png) | [SVG](two-means-workflow.svg) |
| Topic 5: paired differences | [Excalidraw](paired-differences-workflow.excalidraw) | [PNG](paired-differences-workflow.png) | [SVG](paired-differences-workflow.svg) |

## Teaching source and scope

The source of truth is `/Users/wei/Documents/GitHub/STAT250-instruct`.
The preceding source inspection verified the registered originals with `make source-check` and visually checked the original Topic 1 conditions.

- Overview: `modules/module6/module_preamble.tex` and the module map on original M06 T01 slide 1.
- Paired-data distinction: `modules/module6/topic5/sections/01-paired-study-designs.tex` and `02-one-sample-of-differences.tex`.
- One proportion: `source-materials/originals/22sum STAT 250 M06 T01 Inference on the Proportion.pdf`, slides 32, 36–38, 44–49, and 51–55.
- Explicit design and independence checks: `modules/module6/topic1/sections/02-sampling-distribution.tex`, `03-confidence-intervals.tex`, and `04-hypothesis-tests.tex`.

The Topic 1 diagram preserves the course threshold of at least 10 successes and failures, using observed counts for the confidence interval and null expected counts for the hypothesis test.
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
The browser canvas is a working copy; the local `.excalidraw` files are the durable artifacts.
This local checkpoint does not publish the course site or push to a remote.
Run `python3 scripts/validate_excalidraw.py` for repeatable offline integrity checks.

## Topics 2–4 extension

The three additional workflows reuse the shared scene builder, fonts, colors, grouping, and SVG embedding in `build_excalidraw_module6.py`.
Their definitions live in [`build_excalidraw_inference.py`](../../../scripts/build_excalidraw_inference.py).
The overview and Topic 1 native/PNG/SVG files were preserved byte-for-byte against checkpoint `bfc370c`.
That checkpoint covered Topics 2–4; the paired-differences extension is documented below.

```sh
python3 scripts/build_excalidraw_inference.py
# Or rebuild just one topic:
python3 scripts/build_excalidraw_inference.py --topic 2
python3 scripts/build_excalidraw_inference.py --topic 3
python3 scripts/build_excalidraw_inference.py --topic 4
```

Export PNG/SVG and recover the editor-normalized native scene after regeneration, following the general workflow.
The new script does not regenerate the overview or Topic 1 scene.

### Source decisions

The original M06 T02, T03, and T04 PDFs were inspected alongside the authored topic sections in `STAT250-instruct/modules/module6/`.
Exact original-deck hashes and relevant slide numbers are retained in [topics2-4-sources.json](topics2-4-sources.json).

- Topic 2: original slides 21 and 35 check all four observed success/failure counts, each at least 10; this diagram follows those slides for both branches.
  The authored derivative recommends pooled null-expected counts for the equality test, so that difference is recorded explicitly rather than silently substituting its condition.
  Slides 33–35 supply the pooled estimate, written as `p̂_p` in the original, and the equality-null standard error.
  Pooling here is restricted to the null difference of zero; the CI standard error remains unpooled.
- Topic 3: original slides 23, 34, 40–42, and 56 supply `s/√n`, `df = n − 1`, the t interval/test, and the sample-size/shape checks.
  The diagram retains the displayed `n ≥ 30` course guideline and small-sample graphical checks, while noting influential outliers at every sample size as in the authored conditions section.
  It does not repeat the original's unconditional “in all cases” claim or automatic simulation fallback.
- Topic 4: original slides 9–16 and 29 supply the separate-variance standard error, two df choices, conditions, interval, and equality test.
  The shared df card uses the method names Welch–Satterthwaite and conservative minimum, avoiding the later example's reversed option labels documented in the authored sections.
  Shape and size checks apply to both groups; the `n ≥ 30` guideline is not presented as immunity to influential outliers.

Rendered slides were necessary: text extraction dropped the equality bar in several `≥` signs.
The displayed thresholds, not the lossy extracted text, were used.

### Style and verification

All sampling-design and condition cards use the same `#b42332` border, `#fff0f1` fill, red heading, and stroke width 3 as Topic 1.
Stop/pause boxes use the same color family; CI is blue, HT is purple, and contextual conclusions are green.
Native text uses Excalifont, while all equations are self-contained Typst SVGs.
The CI center is the observed estimate; the null center is zero for the two-group equality tests and `μ₀` for one mean.

| Diagram | Elements | Embedded SVG files | Reviewed PNG size |
| --- | ---: | ---: | --- |
| Topic 2 | 98 | 16 | 3130 × 5860 |
| Topic 3 | 95 | 13 | 3130 × 5860 |
| Topic 4 | 103 | 15 | 3130 × 6460 |

All three passed native clipboard roundtrip checks for text, element types, formula metadata, SVG viewBoxes, and glyph paths.
The saved native files contain the recovered editor-normalized scene data.
PNG and SVG exports were obtained from the full editor, and the PNGs were visually inspected.
Offline integrity validation and explicit alert-style checks passed.
Intermediate screenshots and clipboard reports remain under ignored `build/excalidraw-smoke/`.

Two Typst lessons from visual review: use `overline(x)` for the sample mean, and insert whitespace after a symbolic subscript before a parenthesized factor, for example `n_i (1-hat(p)_i)`.
Without that separation, Typst can interpret the parenthesized expression as part of the subscript.
A structural SVG check alone does not detect incorrect mathematical typography.

## Topic 5: one sample of paired differences

The paired workflow reuses the Topic 3 layout and the established Excalifont labels, outlined SVG equations, blue CI branch, purple HT branch, green conclusions, and red design/condition cards.
Its opening card makes the reduction explicit: one pair produces one ordered difference, then one-sample t inference applies to those differences.
It counts complete pairs, uses the SD of the differences, checks independence across pairs and shape within the differences, and retains the sign and units in the interpretation.

The source comparison and SHA-256 hashes are in [topic5-sources.json](topic5-sources.json).
The authored Topic 5 sections use `d̄`, `s_d`, `n` pairs, and a general null mean `μ_{d,0}`; the original slides use `x̄_d`, `n_d`, and a zero-null example.
The diagram follows the authored notation and identifies zero as the usual null value.
Original slide 14 displays `n_d ≥ 30`, whereas slide 15 displays `n > 30`.
The diagram retains the series' `n ≥ 30` course guideline, with a caution to investigate influential outliers at every sample size.
Both slides were visually inspected because text extraction loses the equality bar on slide 14.

The candidate generator is [`build_excalidraw_paired.py`](../../../scripts/build_excalidraw_paired.py).
Its saved [style profile](paired-differences-workflow.style.json) drives the series colors, native font family/line height, and formula rendering.
New formulas retain their expressions, Typst renderer inputs, SVGs, and renderer/hash metadata under `formulas/t5-*`.
The four shared tail/decision formulas reuse the existing assets.

```sh
python3 scripts/build_excalidraw_paired.py
```

By default this writes only the candidate scene to ignored `build/excalidraw-m6t5/candidate/`, leaving the reviewed native scene and exports intact.
The local `excalidraw-math` skill supplies the formula renderer; opening the saved scene does not require that skill or Typst.
Use `--force-formulas` only when intentionally revising formula assets, then import the candidate, visually review it, and export all three formats again.

The final scene contains 101 elements, including 15 equation-image objects backed by 14 unique embedded SVG files.
PNG and SVG exports were obtained from the full editor; the PNG is 3130 × 6540 and was reviewed at full-diagram and detail scales.
The saved native document wraps editor-normalized clipboard data.
The import assigned new element/group IDs and translated the selection; checks confirmed the same text, styles, dimensions, relative positions, grouping, formula metadata, and render-bearing SVG structure.
The file-picker save/reopen route remains unverified; clipboard import/export is the tested route.
The existing five native/PNG/SVG sets were preserved byte-for-byte.
See [paired-differences-workflow.verification.json](paired-differences-workflow.verification.json) for the checked artifact hashes and validation scope.
The reviewed SVG and PNG exports are registered in the website's Module 6 gallery alongside the other workflows, with the same fitted viewer and download controls.
The site build publishes the reviewed exports unchanged and embeds them in the standalone gallery.
