# Digest content contract

Use this contract to decide what survives the page budget.

## Required content

Include, in descending priority:

1. Paper identity: exact title, authors, venue/year if known, and stable URL.
2. Problem: what is being solved and why the prior approach is insufficient.
3. Contribution: the smallest accurate statement of what is new.
4. Assumptions and definitions required to understand the contribution.
5. One or two governing equations with every non-obvious symbol defined.
6. Method: causal flow from inputs through the mechanism to outputs.
7. Strongest quantitative or theoretical result, including baseline and metric context.
8. Limitations, boundary conditions, and known failure cases.
9. Closely related concepts that help transfer the idea, clearly labeled as context.

## Evidence rules

- Trace every equation, number, comparison, and limitation to a source file/section/page while drafting.
- Preserve qualifiers such as “under assumption,” “on dataset,” “in expectation,” and “upper bound.”
- Do not upgrade correlation to causation, an experiment to a general result, or a conjecture to a theorem.
- Mark added interpretation with phrases such as “Intuition:” or “Related concept:”.
- If source and PDF disagree, prefer the latest identified version and disclose the discrepancy.

## Page-budget strategy

- One page: problem, contribution, one central equation, method, headline result, one limitation, citation.
- Two pages: add assumptions, a second equation, stronger result detail, and related concepts.
- Three or more pages: add ablations, proof sketch, implementation detail, or expanded failure analysis.
- Cut background and prose before shrinking typography.
- Never go below 9.5 pt body text or use line spacing below normal single spacing.

## Equation annotations

Annotate terms whose roles are not visually obvious. Use short noun phrases, not sentences. Keep a symbol legend below the equation so the document remains understandable when annotations are unavailable or inaccessible.

Do not annotate every token. A useful annotated equation should reveal mechanism, competing terms, constraints, or optimization direction at a glance.

## Deliverables

- Editable `.tex` source with no external dependency on the temporary workspace.
- Compiled `.pdf` with the exact requested page count.
- Optional provenance ledger only when requested; otherwise keep it temporary.
