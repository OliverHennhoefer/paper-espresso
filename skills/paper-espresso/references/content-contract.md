# Irreducible content contract

Use this contract to decide what deserves space. The digest is not a shorter copy of the paper; it is the smallest faithful representation of the knowledge a future reader should retain.

## Governing question

If the paper could occupy only the requested number of pages, what would a technically competent reader need in order to understand, evaluate, and reuse its central idea?

Do not optimize for section coverage. Optimize for the reader's final mental model.

Unless the user chooses another audience, assume a technically literate reader outside the paper's immediate subfield. Define the specialized concepts needed to understand the contribution without spending space on general technical background.

## Complete-paper understanding

- Read the entire acquired paper before drafting, including appendices.
- Use the abstract, introduction, and conclusion as orientation, not as a substitute for the body.
- Resolve the relationship between definitions, assumptions, mechanism, evidence, and conclusions.
- For TeX source, inspect original files when flattened text loses structure or notation.
- Inspect consequential source figures, diagrams, and plots themselves; captions alone do not reveal all visual evidence, relationships, or failure cases.
- For PDF fallback, check consequential equations, tables, figures, and multi-column passages against the rendered pages.
- If a PDF detail remains ambiguous, omit or qualify it rather than guessing.

## Content hierarchy

Select in this order, adapting the form to the paper:

1. Exact paper identity and stable source link, kept in the compact title line rather than a separate citation block.
2. The problem and the specific deficiency or gap that motivates the work.
3. The paper's precise contribution and central insight.
4. The mechanism: how assumptions and inputs lead to the claimed output or result.
5. Indispensable definitions, assumptions, mathematics, or conceptual structure.
6. The strongest theoretical or empirical evidence, with the conditions needed to interpret it.
7. Limitations, boundary conditions, failure modes, or unresolved questions that materially constrain the contribution.
8. A closely related concept only when it improves transfer or understanding of the central idea; label it as context.

This is a priority order, not a mandatory section template. Omit a category when it does not help explain the paper. Do not force mathematics, highlights, tables, or related concepts into work that does not benefit from them.

## Fidelity rules

- Preserve qualifiers such as “under assumption,” “on dataset,” “in expectation,” and “upper bound.”
- Do not upgrade correlation to causation, an experiment to a general result, or a conjecture to a theorem.
- Keep numerical results with the relevant metric, baseline, dataset, and evaluation conditions.
- Preserve notation unless a simplification is explicitly declared; define every non-obvious symbol that survives.
- Distinguish added interpretation with labels such as `Intuition:` or `Related concept:`.
- If source and PDF disagree, prefer the latest identified version and disclose the discrepancy when it affects the digest.

## Readability without flattening

Reduce the work required to decode the paper, not the precision or difficulty inherent in its ideas.

- Prefer ordinary, concrete wording when specialist language adds no precision.
- Retain the authors' or field's term when it names a distinct construct, is needed to navigate the source or related literature, or would lose meaning under paraphrase. Give a compact plain-language explanation at first use, then use the term consistently.
- Prefer active voice when the actor, mechanism, or causal step matters: state what performs the operation and what changes. Keep passive voice when the actor is unknown or irrelevant, or when the result or procedure is legitimately the scientific focus.
- Put the main subject and action early. Replace avoidable nominalizations and stacked nouns with verbs and explicit relationships.
- Keep one principal claim or causal relation per sentence when combining them would increase tracking effort. Keep decisive qualifiers next to the claim they limit.
- Define notation, abbreviations, and specialist terms close to first use. Do not vary technical vocabulary merely for stylistic variety.
- Use intuition and analogy to expose structure, never as substitutes for the mechanism, assumptions, or evidence.

Do not make the digest sound elementary by deleting the paper's terminology, edge cases, mathematical structure, or uncertainty. Accessibility means that necessary complexity is well explained.

## Compression rules

- Apply three classes: essential, supporting, and nice to have. Remove nice-to-have material. Keep supporting detail only when an essential point depends on it.
- Apply the deletion test: if an element can disappear without materially weakening the reader's model, delete it.
- Prefer one precise statement over multiple approximate statements.
- Prefer a direct subject–verb statement over an abstract or passive construction when both are equally faithful.
- Let an equation, compact table, or causal flow replace prose only when it communicates more clearly per unit of space.
- Avoid generic background, chronology, literature-listing, decorative examples, secondary ablations, and implementation trivia unless they are central to the contribution.
- Never repeat the same idea in prose, mathematics, and a table.
- Rewrite for information gain before shortening mechanically.

## Page-budget behavior

- One page: express the irreducible knowledge. Do not mechanically reserve space for fixed sections.
- Additional pages: add the next-highest-value understanding—deeper assumptions, proof intuition, evidence, ablations, implementation consequences, or failure analysis—not longer prose about material already covered.
- Cut lower-value content before shrinking typography.
- Never go below 9.5 pt body text or use line spacing below normal single spacing.

## Mathematics

Keep mathematics inline when it remains clear and legible. Give an equation its own unnumbered display only when its structure, width, or role requires one; number it only when the digest must refer to it more than once. Integrate symbol definitions and interpretation into the surrounding prose instead of adding a separate legend when possible. Before presenting an essential equation, state what its inputs, outputs, and non-obvious symbols mean. Preserve assumptions needed for a derivation or interpretation, and name the axis, domain, or normalization when ambiguity would change the reader's model.

Use semantic highlighting only when it reduces decoding effort. Mark two to four meaningful subexpressions with the template's light pastel backgrounds, then reuse the same background on the corresponding short, named phrase in immediately adjacent prose. Keep glyphs black and never make color the only reference. Avoid arrows, callouts, legends, nested boxes, and labels that create extra vertical infrastructure. If direct markers still leave the equation cognitively dense, decompose or rewrite it; if it still does not carry the insight efficiently, remove it.

## Figures

Use a figure only when its visual structure carries essential mechanism, evidence, geometry, or comparison more efficiently than prose or mathematics. Prefer a compact native LaTeX/TikZ schematic. Wrap prose around a narrow visual when doing so preserves readable line lengths; otherwise use the smallest legible full-column placement.

Do not add a conventional caption by default. State only the indispensable interpretation or provenance in adjacent prose or a compact inline label. Reuse a source figure only when it is indispensable, legible at the target size, and permitted by its license; copy every required asset beside the `.tex` source and identify its provenance. Never include a decorative or merely representative figure.

## Deliverables

- Editable `.tex` source with no dependency on the temporary workspace, plus any indispensable local figure asset it references.
- Compiled `.pdf` with the exact requested page count.
- No additional artifact unless the digest requires a permitted figure asset or the user explicitly requests one.
