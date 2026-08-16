# Get started

Paper Espresso is currently an early, Codex-first skills-only plugin. The canonical workflow is [`skills/paper-espresso/SKILL.md`](https://github.com/OliverHennhoefer/paper-espresso/blob/main/skills/paper-espresso/SKILL.md).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Poppler: `pdftotext`, `pdfinfo`, and `pdftoppm`
- Tectonic, `pdflatex`, `lualatex`, or `xelatex`

The runtime itself uses Python's standard library.

## Run from an installed plugin

Install the checkout from a local marketplace source during development, then start a new Codex conversation and invoke the skill:

```text
Use $paper-espresso to read “<paper title>” completely and create a one-page technical reference that preserves its essential mental model.
```

Useful variations:

```text
Create a two-page technical reference and emphasize the proof strategy.
```

```text
Use one page. Keep the governing equation and the strongest empirical result.
```

```text
Make the digest accessible to a technically literate reader outside the paper's immediate subfield without removing essential mathematics.
```

While the plugin is under development, consult the [official Codex plugin guidance](https://learn.chatgpt.com/docs/build-plugins) for local marketplace installation.

## Run directly from the checkout

Open the repository in Codex and ask it to read and follow `skills/paper-espresso/SKILL.md` for the requested paper. This is useful while iterating before marketplace installation.

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
