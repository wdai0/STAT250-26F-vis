# STAT 250 · Introductory Statistics I

[Open the live collection](https://wdai0.github.io/STAT250-26F-vis/).

A GitHub Pages collection of self-contained HTML visualizations for Introductory Statistics I, Fall 2026.
Each visualization opens through a searchable, topic-grouped collection and can be downloaded as a complete HTML file to use and edit offline.
The homepage is an animated Galton board in the **Tactile paper** style: warm ivory, graphite, and matte brass, with gentle peg recoil and a soft settling motion.
The collection also includes Cars, NBA, 95% rule, Bootstrap CI, Three distributions, and Sample size & p-values.
The separate **Create your own** guide contains the original exploration principles and a copyable prompt template.
The **Real-world p-values** guide has Business, Physics, Medicine, and Technology tabs with paper links, labeled exact excerpts, contextual interpretations, and a shared classroom threshold control.
The **Type I & Type II errors** visualization compares two fixed normal sampling distributions while a single cutoff controls false alarms, missed effects, and power.
Its Explore and Explanation tabs, significance-level presets, and exact reset work in the standalone download.
Controls and plots take priority; detailed methods are collapsed or placed in a separate view.

## Data sources and adaptations

The supplied `data/cars20.csv` and `data/nba23.csv` are authoritative for the data exploration visualizations.
The build embeds all 110 car records and 332 NBA records directly into the downloadable HTML files.
Source values and category spellings are retained; only display labels trim surrounding whitespace.
The Cars data in the original HTML differed from the CSV, so it was replaced.
The original NBA HTML was truncated before its application code, so its controls and statistical displays were rebuilt around the complete CSV.
The NBA visualization exposes all 28 numeric columns, with team and position filters.
Unspecified units and definitions remain labelled as unverified rather than inferred from plausible values.

The four probability and inference visualizations retain their supplied calculations and seeded simulations.
The 95% rule plot expands its vertical scale for narrow normal curves so their peaks remain visible.
This changes only the display, not the density or probability calculations.
The original files in Downloads are not modified.

The Galton board draws an independent left/right outcome at each row for every ball.
Its dot stacks show individual landed balls, and the optional reference shows the expected binomial counts for the same number of landings and selected settings.
Changing either setting clears the previous run; Reset clears the run while retaining the settings.
Pause freezes balls in flight, and reduced-motion mode replaces autoplay and animated rain with immediate batches.
The standalone file requires no external assets or data.

## Content and design references

The **Tests & confidence intervals** visualization illustrates exact test inversion for a two-sided normal-mean test with known population SD 2, sample size 16, and fixed observed mean 5.
Its sampling-distribution plot and candidate-mean strip share the same 0–10 scale, plot width, and margins; their moving candidate markers align vertically, and the fixed interval center aligns with the observed mean.
The candidate null mean moves while the data and standard error remain fixed; both shaded tails represent its p-value.
A finite sweep reveals the analytically computed non-rejected interval, with pauses at its exact endpoints and the observed mean.
The strict `p < 0.05` rejection rule retains endpoints in the closed 95% interval; decisions use unrounded bounds to avoid numerical disagreement.
The sweep supports pause, resume, replay, immediate reveal, reduced motion, and suspension when hidden.
Open it at `#test-ci-duality`.

The **Sample size & detectable effect** visualization varies the number of independent observations from 25 to 10,000 in a one-sided normal-mean test with known population SD 2.
It fixes alpha at 5% and target power at 80%, selecting the minimum detectable true effect using the exact normal-model formula.
Both sampling distributions share fixed horizontal limits in the overview; an optional magnified detail uses matched, explicitly changing scales.
The Explanation tab distinguishes increasing power for a fixed effect from decreasing the effect required for fixed power, and includes an MDE-versus-sample-size plot.
Open it at `#sample-size-mde`; its complete HTML download requires no external assets.

The **Type I & Type II errors** model uses independent normal observations with known standard deviation 2 and sample size 25.
It tests a mean of zero against a positive mean, with a specified alternative mean of 1 and standard error 0.4.
The error probabilities come from the normal CDF, independently checked against Python's `math.erfc`; no studies are simulated.
The displayed expected counts per 1,000 condition on each panel's population truth.
The source fixes both distributions and the horizontal range, uses one cutoff with linked 10%, 5%, and 1% alpha presets, and distinguishes long-run error rates from the probability a particular decision is wrong.
Open it at `#type-i-type-ii-errors`.

The **Real-world p-values** guide is adapted from the October 13, 2026 three-paper teaching handoff (`stat250-real-world-p-values-handoff.md`).
It retains the original publication links and locations, separates author excerpts from instructor wording, and does not reproduce full abstracts or long result sentences.
The fourth tab uses the Microsoft/Bing A/B experiment in Section 5.5 of [Dmitriev et al. (KDD 2017)](https://doi.org/10.1145/3097983.3098024), checked against the original paper on October 13, 2026.
It distinguishes the initial p-value of 0.029 from an independent rerun with no statistically significant change; the rerun's exact p-value is not reported.
The threshold control illustrates a hypothetical decision rule, including the indeterminate case when a reported upper bound cannot settle a stricter cutoff; it does not reconstruct the papers' testing protocols.
Open it at `#real-world-p-values`; external paper links need a network connection, while the guide and its controls work offline.

The **Create your own** guide contains practical guidance and an expandable prompt template with a Copy prompt button.
Its address is `#create-your-own`; the former `#overview` address also opens this guide.
The homepage deliberately uses animated statistical imagery for play and discovery.
Keep the other visualizations and guide plain: prioritize controls, statistical content, and downloads, without promotional headlines or unnecessary animation.

The guidance paraphrases the supplied *Prompt Template for Interactive Data Exploration* (`prompts_interactive_data_exploration.pdf`):

- Pages 1–2: explicit questions and variables, consistent comparison scales and bins, separate display settings from data selection, report counts and missingness, verify units, and explain boxplot conventions.
- Page 3: adapt and revise prompts, check AI output, ask follow-up questions, preserve the student's own reasoning, protect sensitive information, and state the optional nature of AI-assisted exploration.

The descriptive-exploration prompt does not set restrictions on future inference visualizations.
The supplied Fall 2026 STAT 250-007 syllabus, pages 1–2, informs the broader course scope: data collection and study design; one- and two-variable summaries; probability; sampling distributions and bootstrap methods; confidence intervals and hypothesis tests for means and proportions; correlation and regression.
These topics guide future integration rather than representing visualizations already available.
The reference PDFs are not redistributed with the site, and the source course repository is not modified.

## Build and preview

The build uses Python 3.10 or later with no third-party packages.
The Galton statistical regression checks also use Node.js to exercise the actual JavaScript model.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

Open [the local preview](http://localhost:8000).
Rebuild after editing sources, configuration, or styling, then refresh the browser.
The build recreates `dist/`, so edit the sources rather than generated files.
Generated asset and visualization URLs include content versions so a refreshed page loads matching navigation, styles, catalog data, and updated standalone files.

## Project structure

| Path | Purpose |
| --- | --- |
| `index.html` | Shared hub layout |
| `assets/theme.css` | Shared colors, typography, controls, and visualization styles |
| `assets/site.css` | Hub-specific layout |
| `assets/site.js` | Search, grouped navigation, links, embedded views, and downloads |
| `site.json` | Course identity, authorship, and homepage visualization ID |
| `visualizations.json` | Ordered list of visualization metadata and source paths |
| `sources/` | Editable HTML visualization sources |
| `data/` | Authoritative CSV inputs for Cars and NBA |
| `scripts/build.py` | Validation and standalone HTML generation |
| `tests/test_build.py` | Build-contract tests using temporary fixtures |
| `tests/test_galton_math.py` | Independent checks of the Galton probability model and event accounting |
| `tests/test_galton_motion.py` | Motion continuity, narrow layouts, and landing alignment with counted dots |
| `dist/` | Generated site uploaded to GitHub Pages |

## Navigation

**Browse visualizations** opens a searchable panel grouped by `category`.
Search matches titles, topics, and short descriptions.
Selecting an item closes the panel and displays the visualization at its existing `#id` link; the browser Back and Forward buttons also work.
**Home**, **Create your own**, **Open on its own**, and **Download** remain available in the toolbar.
The panel supports keyboard navigation and Escape to close, and adapts to small screens.
Homepage topic shortcuts use the same registry and groups, so no separate navigation list needs maintaining.
The highlighted Browse button counts entries with `kind: "visualization"`; guides appear in the searchable collection under **Guides**.
The `homepage` ID in `site.json` selects the initial visualization; `#home` is an alias.
The build rejects a homepage ID that is missing from the registry.
The Galton animation suspends while its panel is hidden or the browse dialog is open, and preserves its current run.
Loaded visualizations retain their current controls and simulations when switching between them.

## Add a visualization

1. Place an HTML file in `sources/` with a unique, descriptive filename.
2. Add exactly one `<!-- SHARED_THEME -->` inside its `<head>` and one `<!-- AUTHORSHIP -->` inside its `<body>`.
3. Adapt its typography, controls, layout, and chart colors to the tokens and components in `assets/theme.css`.
4. Add an entry to `visualizations.json` with its topic in `category`; registry order controls the order of topics and items within each topic.
5. Run the tests and build, then check the embedded and downloaded versions in a browser.

An example registry entry:

```json
{
  "id": "sampling-distribution",
  "title": "Sampling distributions",
  "description": "Explore how sample means vary across repeated samples.",
  "source": "sources/sampling-distribution.html",
  "category": "Sampling",
  "kind": "visualization"
}
```

IDs use lowercase letters, digits, and single separating hyphens, beginning with a letter.
`home` and `overview` are reserved for the homepage and legacy guidance aliases.
Each ID and resolved source path must be unique.
An empty registry (`[]`) is valid when no `homepage` is configured.
Use `kind: "guide"` and category `Guides` for a standalone guide, or `kind: "preview"` for a design demonstration.

The build embeds the shared CSS, authorship, and any configured CSV into each generated HTML file.
The iframe and Download button use that same generated file, so the online and downloadable versions stay aligned.
The download contains the complete visualization source; it does not capture the current interactive settings or simulation results.

For CSV-backed visualizations, add a `dataset` object to the registry entry:

```json
"dataset": {
  "source": "data/nba23.csv",
  "text_columns": ["Player", "POS", "Team"]
}
```

In its source script, use `const DATA = /* EMBEDDED_DATA */ [];` exactly once.
The build replaces the marker and empty array with complete records.
Listed text columns retain their original strings; other columns must be finite numbers or missing values (blank, `NA`, `N/A`, or `null`).
Missing numeric values become `null`, never zero.
To refresh these visualizations, replace the CSV, keep its column names, rebuild, and check the counts and summaries.
The generated HTML needs no CSV alongside it and performs no data fetching.

## Standalone files and consistency

Keep visualization scripts, CSS, and required data inside the HTML file.
Use inline SVG or embedded data URLs for required images and avoid CDNs, remote fonts, external stylesheets, JavaScript imports, and fetched data.
Preserve required third-party notices when incorporating existing code or libraries.
Use `sources/interface-preview.html` as the layout and control reference.
It remains a source fixture and is not published as a collection tab.
Add visualization-specific styles only when the shared theme does not cover the need.
When chart colors are set in JavaScript, read the shared CSS custom properties so charts use the same palette.

Importing an existing file requires both a visual adaptation and a behavior check.
Do not alter calculations or statistical assumptions as an incidental part of restyling.
For each new visualization, inspect desktop and narrow layouts, visible keyboard focus, labels, keyboard controls, readable plots, direct visualization links, and the Download button.
Open the downloaded file through `file://` with network access disabled and exercise all its controls.
Check statistical results against known examples or the original implementation where applicable.
The build validates paths, metadata, and required markers; it does not prove that arbitrary visualization JavaScript works offline or that its statistics are correct.

## Authorship

The visible credit is “Ideas and instructional design: [wdai0](https://wdai0.github.io)” and “Implementation: ChatGPT-6 Astra”.
Update `authorship.ideas` and the optional HTTPS link `authorship.ideas_url` in `site.json`, then rebuild.
The hub reads the same configuration, and every downloaded file includes visible credit and an HTML source comment.
The existing repository `LICENSE` is also embedded unchanged in a separate HTML source comment in every download and copied to `dist/LICENSE`.
This retains the MIT copyright and permission notice independently of the display credit.

## GitHub Pages

The [Pages workflow](.github/workflows/pages.yml) tests and builds on pull requests and on pushes to `main`.
Only `main` can deploy; a manual workflow run on `main` is also supported.
In the repository's **Settings → Pages → Build and deployment**, select **GitHub Actions** as the publishing source.
The workflow uploads only `dist/` and deploys it to the `github-pages` environment after a successful build.
Generated files do not need to be committed.
The public site URL appears in the deployment job and the repository's Pages settings.
All published file links are relative so the hub works under a project-site path.

See GitHub's [custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) for deployment settings.
