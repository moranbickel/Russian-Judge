# Contributing

Issues and discussions are open. Real-use-case feedback is the highest-value input.

## What's most helpful

- **Adoption reports.** "I used this for X kind of work; here's what I noticed." Specifics beat generalities.
- **Edge cases the protocol didn't anticipate.** If a finding doesn't fit C/I/M cleanly in your domain, that's signal.
- **Adaptations.** If you tuned the protocol for a different domain (medical, regulated, academic), share what you changed and why.
- **Reproducibility issues.** If priming is degrading on a model the spec mentions as supported, file an issue with the model + version.

## What's less helpful

- Style edits to README, PROTOCOL.md, or docs. The voice is intentional.
- Suggestions for new sections, modalities, or finding classes without a specific use case behind them.
- Pull requests that change the C/I/M taxonomy or the pass-floor formula. Those are versioned changes — open an issue first.

## How to propose changes

- **Typos and minor clarifications:** open a PR directly.
- **Substantive changes:** open an issue first to discuss before writing the PR.
- **Adaptations for your own use:** fork. The MIT license on templates and CC BY 4.0 on prose are designed for this.

## Versioning

Per [PROTOCOL.md §12](./PROTOCOL.md):

- Material changes to the taxonomy, the floor formula, or the round protocol → v2.0.
- Refinements to priming, format, or anti-patterns → v1.1, v1.2, etc.

See [CHANGELOG.md](./CHANGELOG.md) for the version history.
