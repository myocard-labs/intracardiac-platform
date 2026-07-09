# Pre-PR checklist

Run through this before opening any pull request. It's the **per-PR quality gate**; the
phase-level release gate (cross-repo alignment, manifest release-gate, tagging) lives separately in
[release_checklist.md](release_checklist.md).

Each repo mirrors the boxes below as a `.github/pull_request_template.md` (copied from
[`templates/pull_request_template.md`](templates/pull_request_template.md)) so the checklist
auto-populates the PR description in the GitHub web UI. **This** document is the canonical, fuller
version the template points back to.

> PRs are opened / reviewed / merged in the GitHub web UI; the repo chat supplies the local `git`
> commands (commit + push + post-merge tag/sync). No `gh` CLI.

## 1. Tests + static checks — all green

- [ ] `ruff format src tests` — run the **formatter**, not just the linter. A pre-commit hook
  reformats and fails the commit until you re-stage, so do this before committing.
- [ ] `ruff check src tests` clean.
- [ ] `mypy src` clean.
- [ ] `pytest` passes — the fast set locally (egm-studio: `-m "not gui"`); the **full** suite runs
  on the PR itself (CI runs fast on a push to `development`, full on a PR into `release`).
- [ ] **egm-contracts only:** if any schema changed, codegen was re-run and the codegen-drift check
  passes — and **generated code was not hand-edited**.

## 2. Code-placement audit — against [repo_charters.md](repo_charters.md)

This is the "is the code in the right place?" pass Daniel asked for; walk the placement guide:

- [ ] Every new piece of code is in the **right repo** — no DSP primitive that belongs in
  egm-signal, no feature that belongs in egm-features, etc. sitting inside a consumer.
- [ ] Cross-module handoffs use **typed egm-contracts models**, not loose dicts or mirror
  dataclasses.
- [ ] No **policy defaults** baked into a foundation library (they live in the JSON Schemas or in
  the executable consumer's config).
- [ ] Train-time per-call transforms are augmentation (egm-classifier); once-per-dataset transforms
  are producer-side preprocessing — the two aren't blurred.
- [ ] No new shared "utils" dumping-ground module or repo.

## 3. Docs stay in sync

- [ ] Code and docs match: `README.md`, `docs/usage.md`, `project/architecture.md`,
  `docs/theory.md` updated for anything the change affects.
- [ ] `CHANGELOG.md` `[Unreleased]` updated.
- [ ] `roadmap.md` updated — shipped items removed, anything newly discovered added (future-only).
- [ ] The phase's `phase_<N>_plan.md` step statuses updated.

## 4. Cross-repo + versioning

- [ ] If a shared package's schema/API changed: version bumped, and the **re-pin cascade** followed
  in order (egm-contracts → egm-data → producers/consumers) with the coordinated versions recorded
  in the CHANGELOGs.
- [ ] Consumer tests that assert the *old* behavior were found and updated — editable local siblings
  make a shared change go live before the re-pin, so grep for them.

## 5. Repo hygiene

- [ ] No IDE/editor files (`.vscode/`, `.idea/`), no `.venv*/`, no secrets, no large data/bank
  files committed.
- [ ] After adding or moving a source directory, `git status` / `git ls-files` confirms it's
  tracked — guard against an unanchored `data/`-style `.gitignore` glob silently swallowing a
  same-named source package.
- [ ] Commits follow `[Type] Subject` + asterisk-bullet body; feature vs docs vs test-fixture
  changes are separate commits; WIP squashed into logical units.

## 6. Self-review

- [ ] Read the full diff once, top to bottom.
- [ ] The PR description names the phase item + step IDs it implements — the traceability thread
  (phase feature → steps → this PR).
