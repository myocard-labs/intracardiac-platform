<!--
  Copy this file into each repo as `.github/pull_request_template.md` so GitHub auto-populates
  the PR description with this checklist. Fuller detail for every box:
  intracardiac-platform/project/pr_checklist.md
-->

## Summary

<!-- What this PR does, and the phase item + step IDs it implements (e.g. "C1 / S1–S3"). -->

## Checklist

- [ ] `ruff format` + `ruff check` + `mypy` clean
- [ ] `pytest` green (fast set locally; full suite runs on this PR)
- [ ] egm-contracts: codegen re-run + drift check passes, generated code not hand-edited (or N/A)
- [ ] Code is in the right repo per `repo_charters.md`; boundaries use typed egm-contracts models
- [ ] No policy defaults in a library; augmentation vs. preprocessing kept distinct
- [ ] Docs in sync (README / usage / architecture / theory) + `CHANGELOG.md` `[Unreleased]` + `roadmap.md`
- [ ] `phase_<N>_plan.md` step statuses updated
- [ ] Shared schema/API change → version bump + re-pin cascade + consumer tests swept (or N/A)
- [ ] No IDE/`.venv*`/secret/large-data files; new source dirs confirmed tracked (`git ls-files`)
- [ ] Commits: `[Type] Subject` + bullets; feature/docs/fixtures separated; WIP squashed
- [ ] Diff self-reviewed
