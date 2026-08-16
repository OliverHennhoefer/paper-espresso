# Get started

Paper Espresso is currently an early, Codex-first skills-only plugin. The canonical workflow is [`skills/paper-espresso/SKILL.md`](https://github.com/OliverHennhoefer/paper-espresso/blob/main/skills/paper-espresso/SKILL.md).

## Start a processing pass

A paper title, arXiv ID, or URL is the only input required to start. Choose exactly one of the following alternative launch lanes. They start the same workflow; do not run both.

### Installed plugin

Use this lane for normal operation:

```text
$paper-espresso PAPER
```

### Repository checkout

Use this lane only while developing from the repository before installing the plugin:

```text
Read and follow skills/paper-espresso/SKILL.md for PAPER.
```

In either prompt, replace `PAPER` with a paper title, arXiv ID, or URL.

With no other instructions, Paper Espresso uses these defaults:

- one explicit US Letter page (request A4 or another size when needed);
- emphasis inferred from the paper;
- a technically literate reader outside the paper's immediate subfield;
- editable `digest.tex` and verified `digest.pdf` output.

Everything after `PAPER` is optional and overrides a default. For example:

```text
$paper-espresso PAPER — two A4 pages; emphasize the proof strategy.
```

If a title matches multiple papers, Paper Espresso asks for clarification before continuing.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Poppler: `pdftotext`, `pdfinfo`, and `pdftoppm`
- Tectonic, `pdflatex`, `lualatex`, or `xelatex`

The runtime itself uses Python's standard library.

For local marketplace installation during development, consult the [official Codex plugin guidance](https://learn.chatgpt.com/docs/build-plugins).

## Expected output

- `digest.tex`: editable LaTeX with no dependency on temporary downloads
- `digest.pdf`: compiled and verified at the exact requested page count

Downloaded source and intermediate files live in a marked temporary workspace and are deleted after completion.

## Build this documentation

```bash
uv sync --extra docs
uv run --extra docs zensical serve
```

For a production build:

```bash
uv run --extra docs zensical build --clean
```

The generated site is written to `site/`.

## Publish with GitHub Pages

The included workflow deploys the documentation after relevant pushes to `main`. In the GitHub repository, configure **Settings → Pages → Build and deployment → Source** to **GitHub Actions** once. The workflow then builds and deploys the site automatically.
