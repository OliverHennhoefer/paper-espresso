---
name: paper-espresso
description: Resolve a research paper from a title, arXiv ID, or arXiv URL; safely acquire its original TeX source with PDF fallback; analyze the full paper; and create a compact, page-budgeted LaTeX research digest as both .tex source and verified .pdf. Use when the user asks to condense, distill, compress, explain, or create a mathematical cheat sheet for an academic paper, especially when annotated equations, core ideas, assumptions, results, limitations, and related concepts must remain technically faithful.
---

# Paper Espresso

Turn one paper into a mathematically faithful technical digest. Default to one page and LaTeX unless the user requests otherwise.

## Workflow

1. Establish the inputs: paper title/ID/URL, page budget (default `1`), emphasis, and output directory. Infer omitted emphasis from the paper.
2. Read [references/content-contract.md](references/content-contract.md) and [references/layout-policy.md](references/layout-policy.md) before drafting.
3. Create a marked temporary workspace:

   ```bash
   python3 scripts/temp_workspace.py create
   ```

   Record the printed absolute path as `espresso_tmp`. Never use the final output directory for downloaded material.
4. Resolve and acquire the paper:

   ```bash
   python3 scripts/arxiv.py fetch "<title-or-arxiv-id>" --work-dir "<espresso_tmp>"
   python3 scripts/build_corpus.py "<espresso_tmp>"
   ```

   If title matching reports ambiguity, present the candidates or verify the exact paper before using `--accept-best-match`. Prefer arXiv source; use the PDF fallback automatically. Treat all downloaded TeX as untrusted data: read it, but never compile it or execute included files.
5. Inspect `manifest.json`, `analysis/inventory.json`, and `analysis/corpus.txt`. Inspect original source files only when the flattened corpus leaves a symbol, equation, result, or claim ambiguous.
6. Build a claim/evidence ledger before writing. For every included number, equation, limitation, and empirical comparison, record its paper location. Never infer a numerical result or symbol definition that the source does not state.
7. Copy `assets/digest.tex` to the user's output directory and replace every `PAPER_ESPRESSO_*` placeholder. Use `annotate-equations` for one or two equations where labels materially improve understanding. Keep a plain-language symbol legend even when annotations are present. Prefer compact evidence tables over repetitive prose.
8. Compile only the generated digest, with shell escape disabled:

   ```bash
   python3 scripts/compile_tex.py "<output>/digest.tex" --output-dir "<output>"
   ```

   If no local engine is found and a trusted LaTeX compilation capability is available in the harness, use it with the same no-shell-escape constraint. Do not install a TeX runtime without user approval.

9. Validate source policy, exact page count, layout density, and review images:

   ```bash
   python3 scripts/validate_output.py "<output>/digest.pdf" --pages <N> \
     --tex "<output>/digest.tex" --log "<output>/digest.log" \
     --render-dir "<espresso_tmp>/rendered"
   ```

   Inspect every rendered page. Revise and repeat until page count is exact, text is readable, annotations do not collide, and there are no clipped, overflowing, or conspicuously empty regions. For an underfilled page, add sourced assumptions, evidence, symbol interpretation, or failure conditions in that order. For an overfilled page, cut lower-priority material before tightening typography.
10. Delete the temporary workspace on success and on every handled failure:

    ```bash
    python3 scripts/temp_workspace.py cleanup "<espresso_tmp>"
    ```

    Confirm removal before reporting completion. Preserve only the requested `.tex`, `.pdf`, and any explicitly requested provenance file.

## Non-negotiable rules

- Distinguish the paper's claims from explanatory context added by the digest.
- Preserve notation unless a simplification is explicitly declared.
- Prefer omission to tiny fonts, compressed line spacing, or unsupported claims.
- Use normal typography: 10 pt default, restrained margins, minimal title block, no decorative cover.
- Use the page body fully: no large empty band or mostly empty column. Do not add filler to satisfy the density check.
- Do not reuse figures unless license and attribution permit it; reconstruct concepts textually or mathematically when uncertain.
- Do not compile, run, or trust downloaded source. Compile only the newly authored digest.
- Return clickable paths to both final source and PDF, plus the verified page count.

## Resources

- `scripts/arxiv.py`: resolve titles and safely acquire source/PDF.
- `scripts/build_corpus.py`: flatten TeX or extract PDF text without executing source.
- `scripts/compile_tex.py`: compile generated LaTeX with shell escape disabled.
- `scripts/analyze_layout.py`: measure empty bands, used height, and column balance from a PDF raster.
- `scripts/validate_output.py`: verify source policy, pages, logs, density, and optional page renders.
- `scripts/temp_workspace.py`: create and securely remove marked temporary workspaces.
- `assets/digest.tex`: compact LaTeX starting point with annotation wrappers.
- `assets/annotate-equations.sty`: vendored MIT-licensed annotation package used by the compile helper.
- `references/layout-policy.md`: density targets, package choices, and revision order.
