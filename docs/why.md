# Why Paper Espresso

## Reading is necessary—and expensive

A serious reading of a paper is slow. Definitions depend on earlier notation, results depend on assumptions, and the real contribution may be distributed across method sections, appendices, captions, ablations, and limitations.

For seminal or consequential work, there is no honest substitute for eventually reading the original. But requiring a complete reading before gaining any useful technical understanding creates unnecessary friction.

## Orientation is not compression

Conversational research tools such as NotebookLM are valuable because they make source material approachable. Audio and dialogue are excellent ways to establish familiarity and intuition.

Paper Espresso solves a different problem. It is not trying to make the paper conversational. It is trying to preserve the maximum useful technical understanding in a severe page budget.

That means it may retain the ugly details when they matter:

- the assumption that makes a theorem possible;
- the normalization term that controls a method;
- the baseline that changes how a result should be interpreted;
- the failure condition hidden in an appendix;
- the distinction between an empirical observation and a general claim.

## Accessible without intellectual flattening

Accessibility here means that the structure of the idea is exposed clearly. It does not mean removing every difficult concept.

Unless the user specifies otherwise, the intended reader is technically literate but outside the paper's immediate subfield. Indispensable specialist concepts are explained; general technical background is not repeated.

Mathematics can be the most accessible representation when one equation explains a mechanism better than several paragraphs. It remains inline when possible and receives display space only when its structure needs it. An annotation is worthwhile only when it reveals more than the space and visual overhead it consumes. Plain prose remains the default carrier of the insight.

The medium is selected by information value, not by habit.

## The one-page discipline

A fixed page budget forces genuine editorial judgment:

1. **Essential:** removing it causes misunderstanding.
2. **Supporting:** retain only when an essential point depends on it.
3. **Nice to have:** remove.

Every sentence, equation, label, and visual must pass the deletion test: would its removal materially weaken the reader's mental model? If not, it does not belong.

The result is neither a replacement for the paper nor a beginner's overview. It is a compact technical reference for deciding what deserves deeper attention, preparing to read, rapid consultation, and later reconstruction of the paper's essential mental model.
