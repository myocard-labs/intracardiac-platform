# docs/ — user-facing documentation

Material for people who *use* the project: setting it up, running the pipeline end to end, and
reading the paper alongside the code. Internal design rationale and decision records live in
[`../project/`](../project/README.md) instead — the split is audience-driven (use vs. build).

## Start here

- **[quick_start.md](quick_start.md)** — install the constellation and get it running. Two tracks:
  a **User** path (install the tools and run them) and a **Developer** path (a venv per repo,
  tests, editor setup, and building the papers).
- **[walkthrough.md](walkthrough.md)** — the whole pipeline end to end, one stage at a time: real
  recordings → synthetic data → train / eval / export → explore and make figures in egm-studio →
  validate the phase → build the paper. It spells out every hand-off between repos.

## Related locations in this repo

- [`../README.md`](../README.md) — the platform overview and the map of how the repos fit together.
- [`../references/`](../references/README.md) — the annotated reading index of papers the project
  builds on.
- [`../scripts/`](../scripts/README.md) — workspace tooling: clone the repos, run the fast tests,
  validate a phase index.
- [`../phases/`](../phases/README.md) — the cross-artifact phase index (what each science phase
  produced and how the artifacts relate).
- [`../project/`](../project/README.md) — **internal**: design rationale, the canonical project
  plan, and investigations.

## Elsewhere

- **Per-component usage + API** — each component repo documents its own CLIs and internals in its
  own `docs/` (for example, egm-classifier's `docs/usage.md`). This meta-repo `docs/` is the
  cross-component, high-level layer, not a per-repo API reference.
- **The papers** — drafts live in the separate `intracardiac-papers` repo.

## Planned

Conceptual primers on the electrophysiology background needed to read the paper — intracardiac
EGMs, the bipolar voltage-threshold convention, activation-peak vs. R-wave anchoring — aimed at
ML-side readers without a cardiology background, and vice versa. These fill in when there's a
reader asking for them; sparse is fine, misleading is not.

The convention behind the `docs/` (external) + `project/` (internal) split is described in the
[platform README](../README.md).
