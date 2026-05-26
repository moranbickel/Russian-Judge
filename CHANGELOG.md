# Changelog

## Unreleased

- README.md — added a **Prior art** section engaging the LLM-as-judge literature (Zheng et al. 2023, HELM) and stating what RJ does and does not inherit from it.
- examples/disputed-finding-walkthrough.md — new worked example covering a disputed finding (the author believes the reviewer is wrong): the false-positive-vs-latent-fragility decomposition, why a Critical is not author-overridable, and cross-model dispatch as the dispute resolver.

## v1.0 — 2026-05-03

Initial public release.

- README.md — overview, failure mode, worked example, adoption pointer.
- PROTOCOL.md — formal specification (§§1–12).
- Templates: reviewer-prompt, verdict-template, pre-check-gate.
- Docs: rationale, how-to-adopt, faq.
- Diagram: RJ flow (`diagram.svg`).
- Licensing: CC BY 4.0 for prose, MIT for templates.
