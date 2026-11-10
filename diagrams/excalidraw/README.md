# Excalidraw workflow for STAT 250

The [Module 6 diagrams](module6/README.md) include the approved Topics 1–5 overview and Topic 1 workflow, plus matching Topic 2–4 workflows prepared for review.
Use native Excalidraw shapes and text, with embedded SVG images for mathematics.
The tested formula route uses Typst and the full official editor; no math plugin or local canvas server was installed.

## Authoritative files and prerequisites

- Teaching content: the course slide decks in `STAT250-instruct`; record source paths and slide numbers in each diagram's companion README.
- Reproducible formula definitions and layout: [`build_excalidraw_module6.py`](../../scripts/build_excalidraw_module6.py) for the overview/Topic 1 and [`build_excalidraw_inference.py`](../../scripts/build_excalidraw_inference.py) for Topics 2–4.
- Approved editable deliverable: the local `.excalidraw` file, including its embedded `files` collection.
- Reviewed outputs: full-diagram `.png` and `.svg` exports from the editor.
- Formula assets: generated `.typ` and `.svg` files retained for inspection and reuse.

The generator needs Python 3.10+ and Typst on PATH; Typst 0.14.2 was used for the approved outputs.
The offline validator uses only the Python standard library.
The official hosted MCP connection does not require a local Node environment, Docker, a Plus subscription, or an API key in the tested setup.
Opening the saved scene does not require Typst, because its formula SVGs are embedded.

## Authoring rules

1. Inspect the teaching sources and settle the statistical content before drawing.
2. Start with a sketch, then revise one diagram at a time against the approved examples.
3. Use top-to-bottom flow, concise labels, Excalifont (`fontFamily: 5`) for native text, and SVG mathematics.
4. Use consistent red borders and pale red fills for design/condition checks and stop branches.
5. Match the course notation and assumptions exactly; put source provenance and implementation notes in the README rather than crowding the canvas.
6. Group each card with its text and formulas; preserve formula aspect ratios and keep connectors clear of labels.
7. Save manual edits before regeneration and transfer approved content/layout changes back to the generator.

For Module 6 Topic 1, preserve `p₀`, observed counts for CI, null expected counts for HT, and the slide deck's at-least-10 conditions.
These are course-specific choices, not defaults to impose on every future topic.

## Exact SVG formula workflow

### 1. Define and render the formula

Edit the generator's `FORMULAS` dictionary, not just a generated `.typ` file.
For example, `ci-se` contains `"SE"_"CI" = sqrt((hat(p)(1-hat(p)))/n)`.
The generated Typst file is:

```typst
#set page(width: auto, height: auto, margin: 3pt, fill: none)
#set text(size: 25pt, fill: rgb("243247"))
$ "SE"_"CI" = sqrt((hat(p)(1-hat(p)))/n) $
```

The renderer invokes `typst compile formula.typ formula.svg`.
Automatic page dimensions, a small margin, and transparent fill keep each formula tightly bounded.
The resulting SVG contains glyph outlines, so the editor does not need the mathematical font installed.
Use `overline(x)` for a sample mean and whitespace after symbolic subscripts before multiplication, such as `n_i (1-hat(p)_i)`; inspect the resulting mathematical notation.
Condition formulas use the same red as their alert cards.

### 2. Embed and position the SVG

`Scene.formula()` reads the SVG `viewBox`, scales it proportionally into the requested rectangle, and centers it there.
It hashes the SVG bytes to obtain a file ID, then stores a file entry containing:

```json
{
  "id": "<file ID>",
  "mimeType": "image/svg+xml",
  "created": 1,
  "dataURL": "data:image/svg+xml;base64,<encoded SVG bytes>"
}
```

The native image element references that ID through `fileId`, with `status: "saved"`, `scale: [1, 1]`, and the calculated position and dimensions.
Its `customData` preserves `formulaSource` and the Typst expression.
The generator supplies the other required Excalidraw element fields.
An image element alone is insufficient: the matching entry must travel in the scene's `files` collection.

### 3. Generate the intended scene

From the repository root:

```sh
python3 scripts/build_excalidraw_module6.py --diagram overview
python3 scripts/build_excalidraw_module6.py --diagram detailed
```

Choose the command for the diagram being revised.
Omitting `--diagram` rebuilds both and produces a one-formula smoke fixture under ignored `build/excalidraw-smoke/`.
Generation overwrites native scenes and formula assets; it does not refresh the reviewed PNG/SVG exports.
For Topics 2–4, use `python3 scripts/build_excalidraw_inference.py --topic 2` (or `3`, `4`); omit `--topic` to rebuild those three workflows.

### 4. Import through the full editor

The tested automated route reads the generated native document and writes the following actual object as JSON to the browser clipboard:

```javascript
JSON.stringify({
  type: "excalidraw/clipboard",
  elements: scene.elements,
  files: scene.files
})
```

In the intended Excalidraw canvas, use **right-click → Paste**.
For a revision, preserve the previous scene first, then replace only that diagram's elements to avoid duplicates.
Fit the drawing to view and inspect it at readable zoom.
The tested MCP widget did not carry the image-file collection into its canvas, so these formula-bearing diagrams used the full editor.
This is an observed integration limitation from November 10, 2026, not a guarantee about future versions.

### 5. Export and preserve the reviewed scene

With no partial selection, use the canvas context menu's **Copy to clipboard as PNG** and **Copy to clipboard as SVG**.
Read the PNG clipboard entry as binary bytes and the SVG entry as text, then save each beside the native scene.
Do not assume a PNG contains an editable scene; our sampling PNG did not.

For the editable export, use **Select all → right-click → Copy** and read the clipboard JSON.
Verify `type: "excalidraw/clipboard"`, then preserve its `elements` and `files` in this native wrapper:

```javascript
{
  type: "excalidraw",
  version: 2,
  source: "https://excalidraw.com",
  elements: copied.elements,
  files: copied.files,
  appState: { viewBackgroundColor: "#ffffff", gridSize: null }
}
```

This retains the actual editor elements and formulas, but does not capture every editor setting.
The context-menu Copy action worked where keyboard-only copy and automated file dialogs did not.
Use the final native file as the durable checkpoint; browser tabs and remote checkpoint IDs are temporary working state.

### 6. Validate and visually review

```sh
python3 scripts/validate_excalidraw.py
python3 scripts/validate_excalidraw.py \
  diagrams/excalidraw/module6/one-proportion-workflow.excalidraw \
  --roundtrip build/excalidraw-smoke/one-proportion-workflow.roundtrip.json
```

The optional roundtrip file is the saved clipboard JSON from step 5.
Compare it against the scene before replacing that scene with the editor-normalized export.
Checks cover document format, IDs, bindings, Excalifont, formula references, embedded glyph geometry, export structure, and optional clipboard text/metadata preservation.
SVG markup is sanitized on import: compare `viewBox` and glyph paths rather than raw SVG bytes.
The validator does not establish mathematical correctness, export freshness, or visual layout.
Inspect the actual PNG/editor for clipped text, overlap, subscripts, hats, radicals, arrow routing, and readable formula sizes.
A successful tool response is not proof of visible rendering.

## Official MCP connection and diagnostic fixture

The repository's `.codex/config.toml` records the official endpoint and timeouts.
During setup, project-only registration did not appear in desktop settings, so the same endpoint was also registered at user level:

```sh
codex mcp add excalidraw --url https://mcp.excalidraw.com/mcp
codex mcp get excalidraw --json
```

Do not duplicate registrations automatically when the existing connection works.
Check for native `read_me` and `create_view` tools in the current chat after reconnecting.
A hook refresh, configured URL, or external protocol check does not prove that the current chat's tool catalog has reloaded.
The exact reload mechanism was not established in the setup session; a fresh chat is a diagnostic option, not a verified universal fix.

Run network diagnostics explicitly, outside the site's CI:

```sh
python3 scripts/excalidraw_smoke.py
python3 scripts/excalidraw_smoke.py --draw
```

The default checks initialization, tool discovery, format reference, and widget HTML.
`--draw` also sends the synthetic sampling fixture, restores a checkpoint, replaces a subtitle, and checks preservation of the remaining elements.
The script exercises widget-only checkpoint operations directly for diagnostics; those are not ordinary model-facing tools.
Outputs go to ignored `build/excalidraw-smoke/`.
On the setup machine, `/opt/homebrew/bin/python3` provided a working TLS trust store; certificate verification was never bypassed.

For the shape-only fixture, call `read_me` before `create_view` and send `sampling-workflow.elements.json` as its `elements` string.
This simplified MCP input includes camera/label shorthand and must not be renamed to `.excalidraw`.
The saved `sampling-workflow.excalidraw` and `sampling-workflow.png` preserve the earlier editor test.
The initial sample was reopened through the official share-link route; the final clipboard-derived sample and Module 6 scenes were not reopened through the automated file picker.
Module 6 clipboard import/export and formula preservation were verified.

## Troubleshooting and archival boundaries

- Text dimensions: specify Excalifont before layout and inspect pixels; early renderer font substitution caused clipping.
- Missing formulas: check both image `fileId` and the matching embedded `files` entry before changing the formula itself.
- Manual edits: regeneration overwrites them unless they are reflected in the source generator.
- Sharing: **Open in Excalidraw** in the MCP widget uploads a scene and creates a link; it is not a local save operation.
- Reproducibility: preserve content/layout and reviewed outputs; editor-generated IDs and XML serialization need not be byte-identical.
- Provenance: record source paths, slide numbers, tool versions, and source revisions or hashes when available; the current Module 6 record does not pin a teaching-source revision.
- Git: retain sources, approved native scenes, formula assets, reviewed exports, and concise verification records; exclude raw clipboard dumps, screenshots of intermediate states, caches, and remote checkpoint IDs.

No course-site publication is implied by saving or committing diagrams.
Reviewed exports can later be embedded using the root README's standalone HTML workflow.

## Local backup — not installed

The community [`yctimlin/mcp_excalidraw`](https://github.com/yctimlin/mcp_excalidraw) remains an alternative to evaluate separately if needed.
Use a supported Node LTS, a pinned version, a loopback canvas, and explicit export/state directories.
Its stdio MCP connection is distinct from its canvas HTTP URL.
Do not silently replace the official connection or register both under the same name.

## Implementation references

- [Official Excalidraw MCP](https://github.com/excalidraw/excalidraw-mcp)
- [Official checkpoint implementation](https://github.com/excalidraw/excalidraw-mcp/blob/main/src/server.ts)
