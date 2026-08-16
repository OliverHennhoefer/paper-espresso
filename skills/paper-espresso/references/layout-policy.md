# Layout policy

Read this only when composing non-text elements or revising a rendered page. The objective is fast, accurate understanding—not maximum ink.

## Structure and typography

- Use three to five compact visible guideposts when they expose the paper's conceptual structure. Prefer inline `\pehead{...}` labels that run into the paragraph; adapt, combine, or omit them rather than forcing a fixed miniature-paper template.
- Keep the linked or plain paper title and compact identity on one line. Do not add an author block, rule, abstract label, source footer, or numbered sections.
- Default to 10 pt, two columns, 0.55-inch margins, and 0.20-inch column separation. Never go below 9.5 pt.
- Use direct sentences, concrete subjects, active voice where natural, and local definitions. Dense layout must not become syntactically dense prose.

## Mathematics

- Keep mathematics inline when it remains legible. Use an unnumbered display only when width or internal structure requires one; number it only when the digest refers to it more than once.
- Define every surviving non-obvious symbol adjacent to its first use. State inputs, outputs, normalization axes, domains, and decisive assumptions when they affect interpretation.
- For two to four semantic operations that adjacent prose must reference, use `\pemathmark{<color>}{...}` and repeat the marker on a short named phrase with `\petextmark{<color>}{...}`. Use `peblue`, `peamber`, `peviolet`, or `pegreen`; keep text and mathematics black, and never rely on color alone.
- If direct prose and markers do not make an equation accessible, decompose, simplify, or remove it. Do not add arrows, callout diagrams, legends, or annotations merely for appearance.

## Figures and tables

- Use a visual only when geometry, causal flow, or comparison communicates essential knowledge more efficiently than prose or mathematics.
- Prefer a small native construction or an explicitly permitted local source figure. Pass every local asset to `compile_tex.py --asset`; the final `.tex` must use only relative paths and remain portable with those assets.
- Wrap an object only when it fits legibly within roughly 30% of a column and the remaining text width stays readable. Use `wrapfigure` directly, never inside another environment.
- Omit standalone captions by default. Put indispensable interpretation, conditions, and provenance into adjacent prose. Do not shrink tables or diagrams until their labels become harder to read than equivalent prose.

## Page-budget iteration

- Treat `--max-pages N` as the hard budget. Use `--exact-pages N` only when the user explicitly requests an exact count.
- Treat used height, blank bands, column bottoms, and balance as diagnostics. A warning triggers one check for missing high-value understanding, not automatic content insertion.
- Add only a missing mechanism, assumption, definition, evidence condition, limitation, or other item that improves the reader's mental model. Accept remaining whitespace when none exists.
- When over budget, remove repetition, history, secondary examples, and weak evidence before changing layout. Tighten wording and object placement before margins; never use negative spacing, whole-block resizing, fonts below 9.5 pt, manual page/column breaks, `balance`, `flushend`, `\flushbottom`, or stretched glue.
- Inspect every rendered page for clipping, collisions, awkward wraps, separated explanations, overly short lines, and color-marker interference.
