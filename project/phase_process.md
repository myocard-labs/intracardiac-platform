# Phase process — the lifecycle of a project phase

How a Project Phase runs start to finish, which chat drives each step, and which document it writes
against. The chat roles are in [chat_charters.md](chat_charters.md); the documents referenced are
the templates in [`templates/`](templates/) and the checklists in this folder.

A phase moves through four stages — **Planning → Implementation → Science → Cleanup** — and
produces one co-located folder, `phases/phase_<N>/`, holding its `design.md` (the spine),
`manifest.json` (the artifact index), and `observations/` + `figures/`. The through-line is the
**traceability thread**: scientific question → core feature → repo + implementation steps → PR →
artifact (stable ID) → figure → paper claim. Every stage advances that thread and writes its result
down — nothing load-bearing lives only in a chat.

> A "Project Phase" (science scope; numbered 1, 1.5, 2, …, tracked in `project_plan.md`) is distinct
> from a "Refactor Step". The two number lines are independent.

## Stage 1 — Planning

Output: a filled-in Phase Design Doc (copy
[`templates/phase_design_template.md`](templates/phase_design_template.md) to
`phases/phase_<N>/design.md`) plus updated per-repo roadmaps.

1. **Define the science.** *(research chat → design §1)* Settle the question/hypothesis, the
   motivation, honest success criteria, and the scope boundary; read the relevant papers. Usually
   the longest step.
2. **Break science into code.** *(project-lead → design §2)* Translate the science features into
   concrete code chunks, assign each to a repo per [repo_charters.md](repo_charters.md), and call
   out any **new cross-repo data type** — which is designed into
   [cross_artifact_linkage_design.md](cross_artifact_linkage_design.md) and shipped via egm-contracts
   before its consumers can use it.
3. **Pull from the backlogs.** *(project-lead + repo chats → design §3)* Decide which existing
   per-repo `roadmap.md` items ride along this phase; the rest stay in the backlog.
4. **Flow down + estimate.** *(repo chats → per-repo `phase_<N>_plan.md`, rolled up to design §4)*
   Each repo chat breaks its assigned items into an ordered implementation plan
   ([`templates/implementation_plan_template.md`](templates/implementation_plan_template.md)) and
   estimates it as a range; the project-lead rolls the estimates up and lays out the dependency /
   parallelization waves (design §5).
5. **Enumerate the data + figures.** *(project-lead + research → design §6)* List the banks, runs,
   models, figures, and analyses the phase expects to produce — the seed for the manifest.

**Done when:** design §1–§6 are filled, every affected repo's `roadmap.md` is updated, estimates are
rolled up, and the data/figure list is enumerated. (Design §8 "Planning done".)

## Stage 2 — Implementation

1. **Write the code.** *(repo chats)* Implement each repo's plan, ordered by the dependency waves so
   independent work runs in parallel across chats. Fine-grained progress lives in each
   `phase_<N>_plan.md`; the bird's-eye view in design §8. Every merged change clears
   [pr_checklist.md](pr_checklist.md).
2. **Generate the data.** *(repo chats + project-lead)* Write the producer / classifier config files
   and run them one at a time to create the phase's banks, runs, and models. This is where the phase
   **manifest is created** — egm-studio curates `phases/phase_<N>/manifest.json` as artifacts land,
   each stamped with its stable ID.

**Done when:** all core + backlog items are merged (and tagged where a coordinated bump was needed),
the constellation installs and the integration smoke test passes, and every planned bank/run in
design §6 is produced and indexed. (Design §8 "Implementation done" + "Data generated".)

## Stage 3 — Science

1. **Run the science.** *(Daniel, in egm-studio)* Run the tests, generate the figures and graphs,
   analyze. This stage is deliberately exploratory — a finding can send you back to generate a few
   more banks and re-process, and that's fine: capture the change as a **Phase Design Doc revision**,
   not silent scope drift. Findings are recorded as **observations** in the manifest as you go, so
   the paper has a trail. The manifest is **fully completed** by the end of this stage.
2. **Write the paper.** *(paper-writing chat)* Turn the observations, figures, and metrics into the
   white-paper narrative over several write/edit passes. (First-paper specifics will firm up once
   we've written one.)

**Done when:** the planned figures + analyses are generated, findings are captured as observations,
and the paper is drafted. (Design §8 "Science done".)

## Stage 4 — Cleanup

Driven mostly by [release_checklist.md](release_checklist.md).

1. **Repo cleanup.** *(repo chats)* Each changed repo goes release-ready: full suites green,
   CHANGELOG/roadmap finalized, `phase_<N>_plan.md` **deleted**, docs current.
2. **Platform docs cleanup.** *(project-lead)* Update `project_plan.md`'s phase table + any platform
   docs the phase touched.
3. **Phase readjustment.** *(research + project-lead → design §9 + `project_plan.md`)* Review the
   future phases against what this phase discovered; add / reorder / rescope. Record
   estimate-vs-actual so future estimates calibrate.
4. **Release + tag.** *(repo chats + Daniel)* Merge `development → release`, tag each repo at its new
   version (the end-of-phase release), sync branches, and flip the manifest `status` to `shipped`.

**Done when:** the release checklist passes for every changed repo, platform docs are updated, the
plan is readjusted, and the repos are tagged. (Design §8 "Cleanup done".) The phase is shipped.

## At a glance

| Stage | Driver(s) | Produces | Gate |
|---|---|---|---|
| Planning | research → project-lead → repo chats | `design.md` §1–§6; per-repo plans + estimates | design §8 "Planning done" |
| Implementation | repo chats + project-lead | merged code; seeded `manifest.json` | PR checklist per change; §8 rows |
| Science | Daniel + paper chat | figures, observations, drafted paper | §8 "Science done" |
| Cleanup | repo chats + project-lead + research | tagged releases; readjusted plan | release checklist; §8 "Cleanup done" |
