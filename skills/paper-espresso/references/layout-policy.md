# Layout policy

The target is high information density, not literal zero whitespace. Keep enough local space to separate concepts and keep annotated equations legible; reject large unused bands, a mostly empty column, and decorative overhead.

## Default stack

- `annotate-equations`: label only the terms whose roles matter. Keep a symbol legend because colored callouts are explanatory, not a substitute for definitions.
- `microtype`: improve justification and line breaks without shrinking text.
- `amsmath`, `amssymb`, `mathtools`: preserve mathematical semantics and control equation layout.
- `enumitem`: compact lists explicitly.
- `tabularx` with `booktabs`: use compact, width-bounded evidence tables when a table conveys comparisons better than prose.

Use `siunitx` only for numerical tables and `cuted` only for a genuinely necessary full-width equation. Do not add `multicol`, `balance`, or `flushend` merely to disguise missing content. Avoid `savetrees`, whole-block `resizebox`, negative vertical spacing, and fonts below 9.5 pt.

## Filling the page

If the digest is underfilled, add the highest-value sourced material in this order:

1. assumptions or operating conditions;
2. quantitative evidence, baselines, or ablations;
3. symbol definitions and equation interpretation;
4. limitations and failure conditions;
5. tightly related concepts that clarify the contribution.

Never add generic background or filler. If the digest overflows, remove lower-priority context and redundant prose before changing typography.

The default density check crops the outer page furniture and requires each page to:

- use at least 82% of the available body height;
- contain no empty horizontal band larger than 16% of the body;
- keep two-column active-row balance at or above 80%.

These are regression gates, not visual truth. Inspect every rendered page for bad breaks, annotation collisions, misleading proximity, and accidental visual noise.
