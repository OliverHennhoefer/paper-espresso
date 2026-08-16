# Layout policy

Layout serves knowledge compression. Content selection comes first: typography cannot rescue a digest that chose the wrong material.

Target high information density, not literal zero whitespace. Keep enough local space to distinguish concepts and keep mathematics legible; reject decorative overhead, large unused bands, mostly empty columns, and accidental visual noise.

## Base stack

- `microtype`: improve justification and line breaks without shrinking text.
- `amsmath`, `amssymb`, `mathtools`: preserve mathematical semantics and control equation layout.
- `enumitem`: compact lists explicitly.
- `tabularx` with `booktabs`: use a compact, width-bounded table when comparison is clearer than prose.
- `graphicx`: include an essential, permitted figure only when it remains legible at the target size.
- `wrapfig`: reclaim adjacent line space around a narrow mathematical or visual object when the resulting text remains readable.

Use `siunitx` only for numerical tables and `cuted` only for a genuinely necessary full-width equation. Do not add `multicol`, `balance`, or `flushend` merely to disguise missing content. Avoid `savetrees`, whole-block `resizebox`, negative vertical spacing, and fonts below 9.5 pt.

Keep `annotate-equations` out of the base template. Load it only when its labels communicate more than their vertical and visual overhead. Do not preload other specialist packages; add one only when the paper's content requires its notation or it clearly communicates an essential idea more efficiently.

## Structure and flow

Default to dense, continuous technical prose rather than a miniature paper with fixed sections. Use the template's `\pehead{...}` helper sparingly when a short bold inline lead materially improves navigation; continue the paragraph on the same line. Do not stack headings above short fragments.

Let equations, tables, and figures interrupt the prose only when they carry more understanding than the space they consume. Prefer inline mathematics. Use compact unnumbered displays for expressions that truly need visual separation, with no manually added blank space.

For an object that fits legibly within roughly 30% of a column, use `wrapfigure` directly so prose reclaims the lateral space. Use a larger share only after visual inspection proves the remaining lines are comfortable. Do not wrap when it creates very short lines, separates an object from its explanation, distorts reading order, or makes mathematics or labels smaller. Do not place `wrapfigure` inside a custom environment: the extra grouping can prevent correct paragraph shaping. Use no caption by default; fold the essential explanation and provenance into adjacent prose.

## Information-efficient forms

- Use prose for causal explanation, qualifications, and insight that cannot be seen directly in notation.
- Use inline mathematics when it is the shortest faithful representation of mechanism or result; promote it to a display only when necessary for legibility or structure.
- Use a table for meaningful comparisons across shared dimensions.
- Use a compact flow when process order or dependency is otherwise difficult to understand.
- Use a wrapped figure when spatial structure or visual evidence is indispensable, remains readable at digest scale, and leaves useful line width beside it.
- Do not express the same idea in multiple forms unless each adds distinct information.

## Filling the page

If the digest is underfilled, return to the complete paper and ask whether the reader is missing:

1. the central mechanism or reasoning;
2. a decisive assumption or operating condition;
3. the strongest evidence, baseline, or theoretical guarantee;
4. an essential definition or symbol interpretation;
5. a meaningful limitation or failure condition.

Add only genuinely missing knowledge. Never add generic background or filler.

If the digest overflows, remove lower-priority context, examples, history, secondary results, and redundant explanation before changing typography. Recompose the argument rather than squeezing the same text.

## Density gates

The default raster check crops outer page furniture and requires each page to:

- use at least 82% of the available body height;
- contain no empty horizontal band larger than 16% of the body;
- keep two-column active-row balance at or above 80%.

These are regression gates, not visual truth. Inspect every rendered page for bad breaks, annotation collisions, misleading proximity, weak hierarchy, cramped mathematics, and conspicuous unused space. A dense page that is hard to understand has failed.
