# Paper Espresso

## A careful first reading, compressed

Paper Espresso reads a research paper completely and creates the smallest faithful learning artifact that can transfer the essential understanding of a careful first reading. It preserves the mathematics, conditions, uncertainty, and difficulty that genuinely matter without reproducing the paper's narrative structure. The default output uses at most one dense, readable LaTeX page delivered as editable source and a compiled, layout-checked PDF.

It does not summarize every section. It asks a harder question:

> What must survive for a technically literate reader to understand this paper without first spending the time to read it in full?

## The middle layer

| Experience | Primary strength | Result |
| --- | --- | --- |
| Original paper | Completeness and the authors' full argument | The technical source of truth |
| **Paper Espresso** | Essential understanding per minute | A compact structured learning artifact |
| NotebookLM-style overview | Approachable exploration and audio | A conversational introduction |

Paper Espresso surrogates the first careful reading for papers that may or may not justify that investment. Important, consequential, or directly reused papers should still be checked against the original.

## What the page can contain

- The precise problem and contribution
- The central mechanism or conceptual model
- Essential assumptions and definitions
- Governing mathematics when mathematics carries the idea
- The strongest evidence with its conditions
- Limitations, failure modes, and unresolved questions
- A related concept only when it improves transfer

The format follows the knowledge while making its structure visible. Three to five compact inline guideposts normally expose the problem and contribution, mechanism or proof spine, evidence and scope, and limits. Their labels and order adapt to the paper rather than mirror its table of contents. Plain language, direct sentences, and active voice reduce avoidable decoding work when they preserve scientific meaning. Original field terminology stays when it names a real distinction or helps the reader navigate the paper; the digest defines it close to first use.

Mathematics stays inline when it remains legible; standalone equations use compact spacing. A few semantic operations may receive light pastel backgrounds that recur behind their named explanations in adjacent prose, without arrows, legends, or color-only references. Narrow visuals or mathematical objects may be wrapped so prose occupies the adjacent space. Captions appear only when their information value exceeds their cost.

## What it refuses

- Abstract rewriting and section-by-section paraphrase
- Generic background that does not improve understanding
- Decorative equations or highlights
- Avoidable jargon, unexplained abbreviations, and needlessly indirect prose
- Results detached from metrics, assumptions, datasets, or baselines
- Tiny typography used to avoid making editorial decisions
- Confident reconstruction of uncertain PDF extraction

## Start a pass

With the plugin installed, a paper title, arXiv ID, arXiv URL, or local PDF is the only required input:

```text
$paper-espresso https://arxiv.org/abs/1706.03762
```

This single prompt starts the complete workflow. See [get started](get-started.md) for the alternative repository-checkout lane and optional overrides, or continue with [why Paper Espresso exists](why.md) and [how the workflow operates](how-it-works.md).
