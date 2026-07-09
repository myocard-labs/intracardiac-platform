# End-of-phase release checklist

The phase-cleanup gate. Run once at the end of a phase — after the Science + paper work is done —
to get every repo release-ready and tag the end-of-phase release. The per-PR quality gate is
[pr_checklist.md](pr_checklist.md); this is the bigger, once-per-phase gate layered on top of it.

> **Order matters — the release is a cascade.** Finalize repos in dependency order (egm-contracts →
> egm-data → egm-signal / egm-features → producers → consumers), then align + smoke-test the
> constellation, then the manifest + paper + platform docs, then tag. Git is done in the GitHub web
> UI (PRs) plus local commands (commit / push / tag / branch-sync) — no `gh` CLI.

## 1. Per-repo release readiness

For each repo that changed this phase:

- [ ] Every merged PR passed [pr_checklist.md](pr_checklist.md) (this gate assumes that).
- [ ] Full test suite green on the release branch — egm-studio runs the **full** suite including the
  `gui` tests, not just the fast set; `ruff` + `mypy` clean.
- [ ] `CHANGELOG.md`: `[Unreleased]` moved into a dated, versioned release section; version bumped.
- [ ] `roadmap.md`: shipped items removed; future-only.
- [ ] **Delete the repo's `project/phase_<N>_plan.md`** — its shipped work now lives in
  `CHANGELOG.md`, so old step-by-step plans don't pile up (git keeps the history).
- [ ] `README.md` status + `docs/` + `project/architecture.md` current with the shipped reality.
- [ ] All status docs, cross-repo trackers, and memory marked shipped **in the pre-PR commit** — no
  deferred post-merge follow-up; fix any stale statuses you notice while in the shared trackers.

## 2. Cross-repo alignment (the constellation)

- [ ] **Dependency alignment** — no two repos pin conflicting versions of a shared third-party
  package, and every consumer is pinned to this phase's coordinated sibling versions (not a
  floating or stale pin). *This is the phase-closeout dependency check.*
- [ ] The re-pin cascade is fully resolved (egm-contracts → egm-data → producers/consumers), with
  the coordinated versions recorded in each `CHANGELOG.md`.
- [ ] Consumer tests that asserted old shared behavior were swept + updated (editable local siblings
  make a shared change live before the re-pin).
- [ ] Example configs across repos still compose end-to-end (once the config-alignment work lands).
- [ ] The `integration/` smoke test passes against the tagged sibling versions — the constellation
  installs and runs end to end.

## 3. Phase manifest + science artifacts (intracardiac-platform)

- [ ] `phases/phase_<N>/manifest.json` is complete — every training / prediction / noise bank, run,
  model, observation, and figure produced this phase is indexed with a stable ID.
- [ ] `python scripts/validate_manifest.py --phase <N> --release-gate` passes (integrity + usage
  coverage + distribution URLs).
- [ ] `download_url` populated for every bank/model the paper depends on (attached as GitHub Release
  assets on the producing repo's tag).
- [ ] Every figure regenerates from its spec via `egm-studio-render` (images stay gitignored + are
  rebuilt, not committed).

## 4. Paper (intracardiac-papers)

- [ ] The paper builds (`make`) with the final figures.
- [ ] `provenance.tex` records the pinned artifact versions each figure was built from.
- [ ] Paper committed (and tagged, if you tag the paper repo per release).

## 5. Platform docs + phase readjustment (intracardiac-platform)

- [ ] `project_plan.md` phase table updated — this phase marked shipped; component status current.
- [ ] Platform docs the phase touched are updated (`walkthrough.md`, `quick_start.md` if commands
  moved, a `cross_artifact_linkage_design.md` revision-history line if the data-transfer design
  changed).
- [ ] Phase design doc: §8 stages all checked; §9 outcomes + estimate-vs-actual + plan-readjustment
  filled.
- [ ] **Phase readjustment** — review the future phases in `project_plan.md` against what this phase
  discovered; add / reorder / rescope as needed, and record it in §9.

## 6. Tag + release

- [ ] Open the `development` → `release` PR for each changed repo (web UI) and merge.
- [ ] Tag each repo on `release` at its new version — the end-of-phase software release.
- [ ] Sync `development` ← `release` so the branches don't diverge (throwaway-tag + `reset --hard`
  pattern if a squash merge diverged them).
- [ ] Set the phase manifest `status` to `shipped`.
