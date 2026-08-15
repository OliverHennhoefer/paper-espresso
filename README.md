# Paper Espresso

Codex-first plugin for turning a paper title or arXiv identifier into a compact, mathematically faithful LaTeX digest (`.tex` + verified `.pdf`).

## Structure

```text
.codex-plugin/plugin.json           Codex plugin manifest
skills/paper-espresso/SKILL.md      canonical agent workflow
skills/paper-espresso/scripts/      retrieval, extraction, compile, density QA, cleanup
skills/paper-espresso/assets/       compact LaTeX template
skills/paper-espresso/references/   content and evidence contract
.claude/skills/paper-espresso/      thin Claude Code compatibility shim
```

The runtime uses Python's standard library. PDF fallback extraction and verification require Poppler (`pdftotext`, `pdfinfo`, `pdftoppm`). PDF generation requires Tectonic, `pdflatex`, `lualatex`, or `xelatex`. The compile helper supplies a vendored, MIT-licensed copy of `annotate-equations`; generated source also works with the normal TeX Live package. Validation rejects unresolved placeholders, unsafe source constructs, undersized type, wrong page counts, overfull boxes, large empty bands, and badly imbalanced columns.

Invoke the installed Codex skill with a request such as:

```text
Use $paper-espresso to distill “Attention Is All You Need” into one page, emphasizing the mathematics.
```

Downloaded source is treated as untrusted data and is never compiled. Temporary workspaces are explicitly marked and removed after the final artifacts pass validation.
