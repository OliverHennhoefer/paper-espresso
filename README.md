# Paper Espresso

**A paper, reduced to what a future reader must know.**

Paper Espresso is a Codex-first agent skill that reads a research paper completely and creates a compact technical reference for rapid consultation and reconstruction of its central reasoning. It preserves the relationships, mathematics, assumptions, evidence, and limitations needed to recover the paper's essential mental model—without reproducing its narrative structure. The default output is one dense, readable LaTeX page (`.tex` + verified `.pdf`).

[Documentation](https://oliverhennhoefer.github.io/paper-espresso/) · [How it works](https://oliverhennhoefer.github.io/paper-espresso/how-it-works/) · [Get started](https://oliverhennhoefer.github.io/paper-espresso/get-started/)

## Why it exists

Reading the original paper remains necessary for seminal or consequential work. It is also slow, difficult, and often a poor way to get an initial technical map.

Tools such as NotebookLM are excellent for approachable exploration—especially conversational and audio introductions. Paper Espresso occupies the middle ground: shorter and more accessible than the paper, but willing to retain the hard mathematics, assumptions, mechanisms, evidence, and failure conditions when they carry the contribution.

| Experience | Optimizes for | Typical result |
| --- | --- | --- |
| Original paper | Completeness and the authors' full argument | The technical source of truth |
| **Paper Espresso** | Irreducible technical understanding | A dense one-page source and PDF |
| NotebookLM-style overview | Approachable exploration and listening | A conversational introduction |

Paper Espresso is not a replacement for reading the paper. It is a compact technical map for deciding what deserves deeper attention, preparing to read, and remembering the work afterward.

## What survives

- The actual problem and why it matters
- The precise contribution and central insight
- The mechanism from assumptions and inputs to outputs
- Essential mathematics, definitions, or conceptual structure
- The strongest evidence and the conditions under which it holds
- Material limitations, failure modes, and unresolved questions
- A related concept only when it improves transfer of the idea

Everything else must earn its place. The skill explicitly rejects section-by-section paraphrase, generic background, decorative equations, repeated conclusions, and layout tricks that conceal weak prioritization.

The digest is primarily continuous technical prose, not a miniature paper with predetermined sections. Short bold inline guideposts may clarify a real conceptual turn. Mathematics stays inline when legible; displays are compact and unnumbered unless their structure requires otherwise. Narrow visuals or mathematical objects may sit inside the prose flow so text uses the adjacent space. Captions and equation annotations are exceptional, not defaults.

## Use it

With the installed Codex plugin:

```text
Use $paper-espresso to read “Attention Is All You Need” completely and create a one-page technical reference that preserves its essential mental model, emphasizing the mathematics.
```

During local development, open this repository in Codex and ask it to use `skills/paper-espresso/SKILL.md`. The project is distributed as a skills-only plugin and can be installed from a local marketplace source while it is under development; see the [official Codex plugin guidance](https://learn.chatgpt.com/docs/build-plugins).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Poppler: `pdftotext`, `pdfinfo`, and `pdftoppm`
- A LaTeX engine: Tectonic, `pdflatex`, `lualatex`, or `xelatex`

The runtime uses Python's standard library. It prefers original arXiv TeX source and falls back to PDF. Downloaded TeX is treated as untrusted data and is never compiled; only the newly authored digest is compiled, with shell escape disabled.

## Documentation

The documentation site uses [Zensical](https://zensical.org/), with deployment through GitHub Pages.

```bash
uv sync --extra docs
uv run --extra docs zensical serve
```

Run the test suite with:

```bash
uv run python -m unittest discover -s tests
```

GitHub Pages must be configured once to use **GitHub Actions** as its publishing source. Subsequent pushes to `main` deploy automatically.

## Structure

```text
.codex-plugin/plugin.json           Codex plugin manifest
pyproject.toml                      project metadata and uv-managed docs extra
uv.lock                             reproducible dependency lockfile
skills/paper-espresso/SKILL.md      canonical editorial workflow
skills/paper-espresso/scripts/      retrieval, extraction, compile, QA, cleanup
skills/paper-espresso/assets/       compact LaTeX template and annotations
skills/paper-espresso/references/   content-selection and layout contracts
docs/                               Zensical documentation source
zensical.toml                       documentation configuration
```

## Status

Early first pass. Codex is the authoritative integration. The workflow and quality bar will evolve through real paper distillations.

## License

MIT. The vendored `annotate-equations` package retains its own MIT license notice.
