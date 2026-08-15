# Agent instructions

- Treat `skills/paper-espresso/SKILL.md` as the canonical workflow.
- Keep deterministic retrieval, archive handling, compilation, validation, and cleanup in scripts.
- Never compile downloaded TeX. Compile only a newly authored digest with shell escape disabled.
- Keep Codex support authoritative; compatibility shims must point back to the canonical skill.
- Preserve minimal dependencies and add regression tests for safety-sensitive script changes.
