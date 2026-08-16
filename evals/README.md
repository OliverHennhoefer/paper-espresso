# Immediate-comprehension benchmark

This small benchmark checks whether Paper Espresso transfers the mental model of a careful first reading. It evaluates the learning artifact, not memory training.

## Protocol

1. Generate the default at-most-one-page digest for each entry in `cases.json`, without case-specific prompting.
2. Verify the digest against the complete source before evaluation.
3. Give a technically literate reader 60--90 seconds to orient themselves. Keep the artifact open: the reader should locate and explain, not memorize.
4. Score each dimension from 0 (missing or wrong), through 1 (partial or hard to recover), to 2 (faithful and readily recoverable): problem, contribution, mechanism or proof spine, evidence or guarantee with conditions, material limits, and navigation/readability.

Fidelity is a gate. Any unsupported load-bearing claim, materially changed equation or comparison, erased condition, or false certainty fails the case regardless of the numeric score. A revision is better only when fidelity does not regress and it improves comprehension or reduces reading/search effort.

No delayed-recall experiments are included. Do not place evaluation prompts or questions in the generated artifact.
