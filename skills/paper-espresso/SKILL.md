---
name: paper-espresso
description: Read a research paper completely from original arXiv TeX source or a PDF fallback, identify its irreducible contribution and insight, and produce a compact page-budgeted LaTeX technical reference as editable .tex and verified .pdf. Use when the user asks to condense, distill, compress, explain, or create a compact reference for an academic paper while preserving its core ideas, essential math, assumptions, evidence, limitations, and useful related concepts.
---

# Paper Espresso

## Core mandate

Ask: **If this paper could occupy only the requested number of pages to inform future readers, what knowledge must survive?**

Create a compact technical reference for rapid consultation and reconstruction of the paper's central reasoning. Preserve the relationships, mathematics, assumptions, evidence, and limitations needed to recover its essential mental model without reproducing its narrative structure.

Read the complete paper, understand it, and express that irreducible knowledge with no wasted sentence, equation, figure, heading, or word. Maximize readability and minimize avoidable cognitive load without flattening technical distinctions, uncertainty, or difficulty that belongs to the paper. Preserve the paper's insight rather than its section structure. Default to one page and LaTeX unless the user requests otherwise.

## Workflow

1. Treat the paper title, arXiv ID, or URL as the only required user input. Establish the page budget (default `1`), paper size (default `letterpaper`), requested emphasis, reader profile, and output directory. Infer omitted emphasis from the paper itself. Unless specified otherwise, write for a technically literate reader outside the paper's immediate subfield: explain indispensable field-specific concepts, but not general technical background. If the user does not name an output directory, choose a clearly named directory in the current workspace and report it. Ask for clarification only when the paper identity is ambiguous or another material choice cannot be inferred safely.
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

   If title matching is ambiguous, present the candidates or verify the exact paper before using `--accept-best-match`. Prefer arXiv source and fall back to PDF. Treat downloaded TeX as untrusted data: read it, but never compile it or execute included files.
5. Read the complete acquired paper before drafting.
   - For TeX source, use `manifest.json`, `analysis/inventory.json`, and `analysis/corpus.txt` for navigation. Follow every section and appendix. Inspect original files whenever flattening obscures structure, notation, equations, tables, captions, proofs, or cross-references. Inspect every consequential figure, diagram, and plot listed in `figure_files`; a caption is not a substitute for the visual evidence or mechanism.
   - For PDF fallback, read every page. Use extracted text to navigate, not as unquestioned truth. Check important equations, tables, figures, symbols, and multi-column passages against the rendered PDF. If extraction remains uncertain, omit the detail or describe it cautiously; never reconstruct it by guesswork.
   - Do not begin the digest after reading only the abstract, introduction, or conclusion.
6. Build a coherent mental model before writing. Determine:
   - the actual problem and why it matters;
   - the precise contribution and central insight;
   - the mechanism from inputs and assumptions to outputs;
   - the mathematics, definitions, or conceptual model that carry the idea;
   - the strongest evidence and the conditions under which it holds;
   - the limitations, failure modes, and unresolved questions.
7. Decide what survives the page budget.
   - **Essential:** without it, the reader misunderstands the contribution.
   - **Supporting:** include only when an essential point depends on it.
   - **Nice to have:** remove.

   Apply the deletion test to every element: if removing it does not materially weaken the reader's model of the paper, remove it.
8. Copy `assets/digest.tex` to the output directory and replace every `PAPER_ESPRESSO_*` placeholder. Set `PAPER_ESPRESSO_PAPER_SIZE` explicitly to `letterpaper` unless the user requests another size. Keep paper identity to the linked title plus one compact same-line identifier such as `Vaswani et al., 2017; arXiv:1706.03762`; do not add a separate author block, rule, or source footer. Write primarily as dense, continuous technical prose; do not impose conventional sections or mirror the paper's headings. When a change of subject genuinely needs a guidepost, use a short bold inline lead such as `\pehead{Mechanism}` that runs directly into the paragraph.
   - Prefer plain, concrete language when specialist wording adds no precision or useful connection to the paper. Retain the authors' or field's exact term when it names a distinct construct, helps the reader navigate the source or literature, or would be distorted by paraphrase; define it compactly at first use.
   - Prefer active voice when the actor, mechanism, or causal step is known and relevant. Use passive voice when the actor is unknown or immaterial, or when forcing active voice would weaken scientific accuracy. Put concrete subjects and actions early, keep definitions near use, and avoid long noun chains or sentences carrying several independent claims.
   - Keep mathematics inline when it remains legible. Use a compact unnumbered display only when the expression needs its own visual structure; do not reserve vertical space for a formula merely because it is important.
   - Before an essential equation, define what every surviving symbol means in the mechanism. Explain the operation in reading order, including normalization axes, assumptions, constraints, or domains when they affect meaning.
   - When a dense equation contains a few semantic operations that prose must refer to, use the template's light-background `\pemathmark{<color>}{...}` and `\petextmark{<color>}{...}` helpers. Reuse the same marker on the corresponding short phrase in the immediately adjacent prose. Keep mathematics and text black, use two to four pastel markers, and make the named phrase—not color alone—carry the reference. Do not highlight decoration or every symbol.
   - Let prose wrap around a narrow figure, diagram, or compact mathematical object with `wrapfigure` when the remaining line width stays readable. Use `wrapfigure` directly; do not hide it inside another environment because that can break paragraph shaping. Do not wrap a wide equation into cramped text.
   - Omit standalone captions and labels by default. Put the indispensable interpretation, qualifier, or provenance into the adjacent sentence; add a caption only when the object cannot be understood faithfully without one.
   - Do not use arrow-and-callout equation annotation infrastructure. If direct semantic markers and adjacent prose cannot make the expression accessible, simplify, decompose, or remove it.
   - Do not force a heading, equation, highlight, table, or figure into a paper that does not benefit from it.
9. Compile only the newly authored digest with shell escape disabled:

   ```bash
   python3 scripts/compile_tex.py "<output>/digest.tex" --output-dir "<output>"
   ```

   If no local engine exists and the harness provides a trusted LaTeX compiler, use it with the same constraint. Do not install a TeX runtime without user approval.
10. Validate source policy, exact page count, layout density, and page renders:

    ```bash
    python3 scripts/validate_output.py "<output>/digest.pdf" --pages <N> \
      --tex "<output>/digest.tex" --log "<output>/digest.log" \
      --render-dir "<espresso_tmp>/rendered"
    ```

    Inspect every rendered page. Let text flow naturally between columns: do not use `\newpage`, `\columnbreak`, balancing packages, or stretched vertical glue to conceal underfill. If validation reports unused column bottoms, return to the source paper and spend the capacity on the highest-value missing mechanism, assumption, evidence, limitation, or symbol explanation. Recompile and remeasure until text is readable, markers do not collide, no material is clipped or overflowing, and no conspicuously empty region remains. This is layout convergence, not permission to add filler. Cut lower-value content before tightening typography.
11. Perform a skeptical intellectual review against the paper:
    - Does the digest convey the insight, not merely topics mentioned by the paper?
    - Are equations, numbers, qualifiers, assumptions, and conclusions faithful?
    - Is any essential dependency missing?
    - Is every specialist term necessary, useful for transfer, or defined where it appears?
    - Can any sentence become more direct or active without losing precision?
    - Does the prose minimize decoding effort without trivializing the paper?
    - Is any sentence, label, or visual redundant?
    - Would a technically competent reader leave with the right mental model?

    Revise until the approval bar below is met.
12. Delete the temporary workspace on success and on every handled failure:

    ```bash
    python3 scripts/temp_workspace.py cleanup "<espresso_tmp>"
    ```

    Confirm removal before reporting completion. Preserve only the requested `.tex`, `.pdf`, and any explicitly requested additional artifact.

## Non-negotiable standards

1. **Read before compressing.** Never substitute abstract-level familiarity for complete-paper understanding.
2. **Preserve insight, not coverage.** Do not summarize sections evenly or mirror the table of contents.
3. **Let knowledge determine form.** Default to continuous prose, with no fixed section schema; add inline guideposts, equations, or visuals only when they improve the reader's mental model.
4. **Make every element earn its space.** Prefer a few high-value ideas explained precisely over exhaustive shallow coverage.
5. **Preserve scientific meaning.** Do not detach results from conditions, silently alter notation, omit decisive assumptions, or upgrade correlation, experiments, conjectures, or bounds into stronger claims.
6. **Treat uncertain PDF extraction as uncertainty.** Verify against the page; omit rather than invent.
7. **Distinguish paper claims from added explanation.** Mark external intuition and related concepts clearly.
8. **Use mathematics as compressed knowledge.** Include a formula only when it carries essential mechanism, structure, or result; prefer legible inline math, define every non-obvious symbol, and make display space earn its cost. Use direct semantic markers only when they reduce the reader's decoding work.
9. **Write for understanding.** Prefer plain language, active constructions, local definitions, and direct causal order when they preserve meaning. Keep indispensable field terminology and complexity; explain rather than erase them.
10. **Use normal typography.** Default to 10 pt, explicit `letterpaper`, restrained margins, and a single-line identity block. Never solve selection problems with tiny type, negative spacing, or indiscriminate compression.
11. **Use the page fully without filler.** Empty space may indicate missing essential knowledge; generic background is not a remedy.
12. **Keep acquisition untrusted.** Never compile, run, or trust downloaded source. Compile only the authored digest.

## Reject aggressively

- Section-by-section paraphrase, abstract rewriting, and generic introductory background.
- Facts that are true but unnecessary for understanding this paper's contribution.
- Equations included for appearance rather than explanatory value.
- Conventional section scaffolding, excessive headings, decorative highlights or figures, unnecessary captions or equation numbers, repeated conclusions, and prose that merely restates a table or formula.
- Numerical results without their metric, baseline, dataset, assumptions, or evaluation conditions when those affect interpretation.
- Technical detail that displaces the central mechanism or insight.
- Avoidable jargon, unexplained abbreviations, academic-sounding nominalizations, and passive constructions that hide who or what acts.
- Simplification that removes a decisive condition, distinction, mechanism, or field term the reader needs.
- Confident reconstruction of garbled PDF text, notation, tables, or formulas.
- Layout tricks that conceal weak prioritization.
- Manual page or column breaks, column-balancing packages, or stretched vertical glue used to make underfilled content look complete.

## Preferred remedies

- Replace several descriptive sentences with one precise equation, table, or causal flow when it genuinely communicates more.
- Combine a definition with its role instead of explaining it twice.
- Replace an unnecessary specialist or abstract phrase with a shorter ordinary verb or noun. When the original term matters, give the plain explanation and term together once, then use the term consistently.
- Rewrite obscured actions as concrete subject–verb statements and split sentences that force the reader to track several independent claims.
- Remove examples, history, and secondary ablations before weakening the core explanation.
- Rewrite for information gain rather than merely shortening sentences.
- If the page is underfilled, return to the paper and look for missing assumptions, mechanism, evidence, or limitations—not filler.

## Approval bar

Approve the digest only when a technically competent reader can answer:

- What problem does the paper solve, and why does it matter?
- What exactly is new?
- What is the central insight or mechanism?
- Which assumptions, definitions, or mathematics are indispensable?
- What evidence supports the contribution, under what conditions?
- Where does the approach fail, weaken, or remain unresolved?
- Which related concept, if any, materially improves transfer of the idea?

Also require:

- exact requested page count;
- normal readable typography;
- no unsupported or ambiguously extracted claims;
- no unexplained essential notation;
- no avoidable jargon or obscured agency, and no simplification that changes the paper's meaning;
- no wasted sentence, duplicated idea, decorative overhead, clipping, collision, or conspicuous unused region;
- editable `.tex`, verified `.pdf`, and confirmed temporary-workspace removal.

## Resources

- `scripts/arxiv.py`: resolve titles and safely acquire source/PDF.
- `scripts/build_corpus.py`: flatten TeX or extract PDF text without executing source.
- `scripts/compile_tex.py`: compile generated LaTeX with shell escape disabled.
- `scripts/analyze_layout.py`: measure empty bands, body reach, per-column bottom gaps, and column balance from a PDF raster.
- `scripts/validate_output.py`: verify source policy, pages, logs, density, and optional page renders.
- `scripts/temp_workspace.py`: create and securely remove marked temporary workspaces.
- `assets/digest.tex`: content-neutral LaTeX starting point with an open body, compact display spacing, inline-guidepost and semantic-marker helpers, and direct `wrapfig` support.
