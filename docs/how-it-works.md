# How it works

Paper Espresso separates model judgment from deterministic infrastructure. The model reads, reasons, selects, and writes. Scripts handle retrieval, archive safety, compilation, page checks, layout checks, and cleanup.

## 1. Resolve the exact paper

The workflow accepts a title, arXiv identifier, or arXiv URL. Ambiguous title matches must be resolved before analysis begins.

## 2. Prefer original source

When arXiv TeX source is available, Paper Espresso acquires it safely and reads it as data. Original source preserves notation, labels, equations, tables, captions, bibliography, visual assets, and document structure better than extracted PDF text. Consequential figures, diagrams, and plots are inspected directly rather than inferred from captions.

Downloaded TeX is never compiled or executed.

## 3. Fall back carefully to PDF

When only a PDF is available, the complete document is still read. Extracted text assists navigation but is not treated as unquestioned truth. Consequential equations, tables, figures, symbols, and multi-column passages are checked against rendered pages.

If a detail cannot be extracted confidently, it is omitted or qualified rather than reconstructed by guesswork.

## 4. Understand before drafting

The agent does not begin after reading only the abstract, introduction, and conclusion. It first builds a coherent model of:

- the actual problem;
- the precise contribution;
- the central insight and mechanism;
- indispensable assumptions and definitions;
- essential mathematics or conceptual structure;
- the strongest evidence and its conditions;
- limitations and unresolved questions.

## 5. Decide what survives

Material is classified as essential, supporting, or nice to have. The digest follows the paper's intellectual structure rather than its table of contents.

The digest defaults to dense, continuous technical prose rather than fixed sections. Short bold inline guideposts are used only for genuine conceptual turns. Mathematics remains inline when legible; standalone equations use minimal surrounding space. Narrow figures or compact mathematical objects may be wrapped so prose fills the adjacent area. Captions, numbering, and equation annotations are omitted unless they add indispensable meaning.

## 6. Compile and inspect

Only the newly authored digest is compiled, with shell escape disabled. Validation checks:

- exact page count;
- unresolved template placeholders;
- unsafe source constructs;
- undersized typography;
- compilation errors and overfull boxes;
- large unused bands and badly imbalanced columns;
- clipping, collisions, and visual readability on rendered pages.

## 7. Apply the intellectual approval bar

Before delivery, the digest is reviewed against the complete paper. A technically competent reader should be able to explain the problem, contribution, mechanism, indispensable mathematics or assumptions, strongest evidence, and material limitations.

The final deliverables are the requested `.tex` and `.pdf`. Temporary downloads, extracted source, and rendered review pages are removed on success and cleaned up on failure.
