# Paper Espresso

## A paper, reduced to what a future reader must know

Paper Espresso reads a research paper completely and creates a compact technical reference designed for rapid consultation and reconstruction of its central reasoning. It preserves the relationships, mathematics, assumptions, evidence, and limitations needed to recover the paper's essential mental model—without reproducing its narrative structure. The default output is one dense, readable LaTeX page delivered as editable source and a verified PDF.

It does not summarize every section. It asks a harder question:

> If this paper could occupy only one page to inform future readers, what knowledge must survive?

## The middle layer

| Experience | Primary strength | Result |
| --- | --- | --- |
| Original paper | Completeness and the authors' full argument | The technical source of truth |
| **Paper Espresso** | Irreducible technical understanding | A dense, accessible technical map |
| NotebookLM-style overview | Approachable exploration and audio | A conversational introduction |

Important papers should eventually be read in full. Paper Espresso helps before that reading—by exposing the structure that matters—and after it, by preserving the insight in a form that is fast to revisit.

## What the page can contain

- The precise problem and contribution
- The central mechanism or conceptual model
- Essential assumptions and definitions
- Governing mathematics when mathematics carries the idea
- The strongest evidence with its conditions
- Limitations, failure modes, and unresolved questions
- A related concept only when it improves transfer

The format follows the knowledge. The default is continuous technical prose without predetermined sections. Mathematics stays inline when it remains legible; standalone equations use compact spacing, and narrow visuals or mathematical objects may be wrapped so prose occupies the adjacent space. Captions and equation annotations appear only when their information value exceeds their cost.

## What it refuses

- Abstract rewriting and section-by-section paraphrase
- Generic background that does not improve understanding
- Decorative equations or annotations
- Results detached from metrics, assumptions, datasets, or baselines
- Tiny typography used to avoid making editorial decisions
- Confident reconstruction of uncertain PDF extraction

## First prompt

```text
Use $paper-espresso to read “Attention Is All You Need” completely and create a one-page technical reference that preserves its essential mental model, emphasizing the mathematics.
```

Continue with [why Paper Espresso exists](why.md), [how the workflow operates](how-it-works.md), or [get started](get-started.md).
