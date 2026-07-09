# project/ — internal: design, process, investigations

The meta repo's project-truth folder. Audience: people building / maintaining the project —
currently Daniel, plus future contributors and reviewers. External, user-facing material lives in
[`../docs/`](../docs/README.md) instead; the split is audience-driven (build vs. use).

## Plan + design

- **`project_plan.md`** — the canonical roadmap: vision, the components + their statuses, locked-in
  architectural decisions, the project-level phased roadmap + dependency DAG. The hub everything
  links into.
- **`repo_charters.md`** — the division of labor: what code lives in which repo and why, with a
  placement decision guide. The source of truth when you're unsure where something belongs.
- **`cross_artifact_linkage_design.md`** — how data moves between repos: stable IDs, the cross-repo
  schemas, the per-phase manifest, and the tooling that curates it. Extend it when a new data type
  needs to cross a boundary.
- **`architecture_reading_list.md`** — CNN-architecture reading progress; the *why* behind the model
  decisions.

## How we work (process)

- **`chat_charters.md`** — the multi-chat scheme: the roles (research · project-lead · per-repo ·
  paper-writing · job-search), what each owns and does not touch, and the rules that keep them in
  sync.
- **`phase_process.md`** — the lifecycle of a Project Phase (Planning → Implementation → Science →
  Cleanup): who drives each step and its definition of done.
- **`pr_checklist.md`** — the pre-PR quality gate (tests, placement audit, docs-sync, hygiene);
  mirrored per repo as `.github/pull_request_template.md`.
- **`release_checklist.md`** — the end-of-phase release gate (cross-repo alignment, manifest
  release-gate, tag + release).
- **`templates/`** — copy-to-use templates: `phase_design_template.md` (→ `phases/phase_<N>/design.md`),
  `implementation_plan_template.md` (→ `<repo>/project/phase_<N>_plan.md`), and
  `pull_request_template.md` (→ each repo's `.github/`).

## investigations/

- **`investigations/`** — post-hoc diagnostic reports, cross-cutting by nature (each drove decisions
  in more than one component): currently `v1_baseline_investigation.md`, `v1_5_investigation.md`,
  `v1_iafdb_investigation.md`. New ones land here.

## What does NOT live here

- **API reference, install guides, walkthroughs** → [`../docs/`](../docs/README.md) (external,
  user-facing).
- **Per-component design docs** → each component's own `project/` folder; `project_plan.md` links to
  them.
- **Per-component code, tests, notes** → the component repos.
- **Per-chat handoff prompts** → moved to a `prompts/` folder at the workspace root; **not tracked**
  in any repo.

The `docs/` (external) + `project/` (internal) split is described in the [platform README](../README.md).
