# <repo> — Phase <N> implementation plan

> _Template. Copy to `<repo>/project/phase_<N>_plan.md` once this repo's slice of the phase is
> scoped. **Owned by the repo chat.** It breaks this repo's assigned phase items into small,
> ordered, independently-verifiable steps — the formalized version of "break a big change into a
> sequence of safe commits." Fill the `<...>` placeholders; delete these guidance blockquotes._
>
> _**Where this lives relative to the other per-repo docs:** `roadmap.md` stays **future-only**
> (the backlog not yet scheduled into a phase); **this** plan is the **active** phase's step list +
> fine-grained progress; at release the shipped work summarizes into `CHANGELOG.md` and anything
> unfinished drops back to `roadmap.md`. Keeping the three separate preserves the
> changelog/roadmap split. **This plan is ephemeral** — created at Phase Planning and **deleted at
> Phase Cleanup** once its shipped work is captured in `CHANGELOG.md`, so old step-by-step plans
> don't pile up in the repo (the release checklist enforces the deletion; git keeps the history).
> Cross-repo references (the phase design doc, the checklists) live in the
> `intracardiac-platform` repo — paths are given as plain text since they resolve across repos, not
> as links._

**Repo:** <repo> · **Phase:** <N>
**Phase design doc:** `intracardiac-platform/phases/phase_<N>/design.md`
**Status:** planning | in progress | done · **Progress:** <k>/<n> steps done
**Repo estimate:** <sum range — flows to §4 of the phase design doc>

---

## Scope — what this plan covers

> _The phase-design items assigned to this repo (the C#/B# IDs from §2/§3 of the phase design doc),
> each mapped to the steps that implement it. This keeps the traceability thread intact: phase
> feature → these steps → the commits/PR that reference them._

| Phase item | What it needs from this repo | Steps |
|---|---|---|
| C1 | <capability slice> | S1–S3 |
| B2 | <backlog item> | S4 |

## Design notes (optional)

> _Only if the repo needs a local decision before coding — a new module layout, which existing code
> to touch, a small trade-off. Anything branching or long-lived belongs in the repo's
> `project/architecture.md` (or an ADR there), not buried here._

- <note, or "none">

## Steps

> _Each step is small enough to be one focused commit, **ends green** (its own tests pass +
> `ruff format`/`ruff check` + `mypy` clean), and states how it's verified. Use any stable step-ID
> scheme (`S1…`, or the `Bn.m` style some repos already use); commits and the PR reference these
> IDs. Mark status inline: ☐ todo · 🔨 wip · ✅ done. Order by dependency; note where two steps can
> proceed in parallel._

### S1 — <deliverable> ☐ (<estimate>)
- **Change:** <files / modules touched; the behavior or contract this step adds>
- **Verify:** <the specific check — a unit test added + passing, a `--help` / render output, a
  screenshot, a schema round-trip, a snapshot baseline, …>
- **Depends on:** <prior step / cross-repo prerequisite, or "none">

### S2 — <deliverable> ☐ (<estimate>)
- **Change:** <…>
- **Verify:** <…>
- **Depends on:** S1

<!-- Add steps as needed. Keep each one commit-sized and independently green. -->

### S<final> — Docs + phase-exit ☐ (<estimate>)
- **Change:** update this repo's `roadmap.md` (remove the now-shipped items), `CHANGELOG.md` (add
  the shipped summary), and any `docs/` / `architecture.md` the change touched.
- **Verify:** the full pre-PR run in `intracardiac-platform/project/pr_checklist.md` passes.
- **Depends on:** all prior steps.

## Estimate roll-up

> _Sum of the per-step estimates as a range — the number that flows up to §4 of the phase design
> doc. Record the actual at phase cleanup so future estimates calibrate._

- **Estimated:** <sum range>
- **Actual (filled at cleanup):** <…>

## Notes / decisions log (optional)

> _Short running log of anything surprising discovered mid-implementation — a step that split, a
> dependency that emerged, a decision that changed. Keeps the repo chat's working memory in the doc
> rather than in the chat's context._

- <YYYY-MM-DD> — <note>
