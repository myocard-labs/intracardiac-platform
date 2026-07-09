# scripts/

Tooling for the myocard-labs workspace. These scripts aren't part of any Python package and
aren't installed — run them directly (`bash` for shell scripts, `python` for Python scripts).
Two operate on the whole workspace (all sibling repos); the other two are `intracardiac-platform`
phase-index tooling.

## `clone_repos.sh` — fetch the sibling repos

Clones every myocard-labs repo as a sibling of `intracardiac-platform` — the workspace layout the
inter-repo git pins and tooling expect. Run it right after cloning this repo:

```bash
bash intracardiac-platform/scripts/clone_repos.sh          # HTTPS
bash intracardiac-platform/scripts/clone_repos.sh --ssh    # SSH
```

Idempotent: repos already present are skipped. Full setup flow in
[`../docs/quick_start.md`](../docs/quick_start.md).

## `run_fast_tests.sh` — CI-parity fast test sweep

Runs each repo's **fast** test suite — the set CI runs on a push to `development`. egm-studio's
slow Qt-GUI tests are excluded (`-m "not gui"`); its full suite runs on PRs into `release`.
Developer setup is one venv per repo, so this uses each repo's own `.venv` and skips repos that
don't have one.

```bash
bash intracardiac-platform/scripts/run_fast_tests.sh                 # every repo with a .venv
bash intracardiac-platform/scripts/run_fast_tests.sh egm-classifier  # just the named repos
```

Exit code is non-zero if any suite fails, so it drops into a pre-push hook.

## `validate_manifest.py` — phase-index safety net

The [`phases/`](../phases/README.md) folder is the project's cross-artifact index: one
`manifest.json` per science phase listing every artifact it produced (banks, runs, models,
observations, figures, papers) and how they relate. egm-studio is the canonical curator that
writes those manifests; **this script is the scan-and-validate safety net** that catches drift
the GUI can't — a hand-saved file with no manifest entry, a dangling id reference, a forgotten
usage tag — and it is the **release gate** run before any phase that ships a paper is declared
done. It never auto-fixes: it reports, and you fix by hand.

### Prerequisites

It reuses the egm-contracts validators and the egm-data phase readers, so both must be
importable:

```bash
# Easiest: the shared venv with the constellation installed — see docs/quick_start.md.
# Minimal, standalone:
pip install \
  "myocard-egm-contracts @ git+https://github.com/myocard-labs/egm-contracts.git" \
  "myocard-egm-data @ git+https://github.com/myocard-labs/egm-data.git"
```

### Usage

Run from the repo root:

```bash
# All phases under phases/. Integrity errors are fatal; coverage / URL gaps are warnings.
python scripts/validate_manifest.py

# One phase — the folder suffix (phases/phase_1_5 -> "1_5").
python scripts/validate_manifest.py --phase 1_5

# Release gate: usage-tag and download-url gaps become fatal too.
python scripts/validate_manifest.py --phase 1_5 --release-gate

# Also HEAD-request every download_url (slow; needs network).
python scripts/validate_manifest.py --phase 1_5 --release-gate --check-urls

# Point at a different phases directory (default: <repo>/phases).
python scripts/validate_manifest.py --phases-dir /path/to/phases
```

The exit code is non-zero on any *fatal* issue (integrity errors always; coverage / URL
warnings only under `--release-gate`), so it drops cleanly into a pre-push hook or CI. The
shipped `phases/phase_1_5_example/` template validates clean — its only warnings are the
expected "external producer artifact" ones for banks/models that live outside the repo.

### What it checks

Three tiers (full detail in
[`../project/cross_artifact_linkage_design.md`](../project/cross_artifact_linkage_design.md) §8
and [`../phases/README.md`](../phases/README.md)):

- **A — integrity** (always fatal): id format · no duplicate ids across the project · every
  `path` resolves (in-repo observation/figure files = error, external bank/model targets =
  warning) · no on-disk observation/figure orphaned from the manifest · every relationship
  pointer resolves · every file passes its egm-contracts schema.
- **B — coverage** (warning; fatal under `--release-gate`): every observation/figure carries a
  `usage_tag`; in-paper consistency between figures, observations, and papers.
- **C — distribution** (`--release-gate` only): every bank/model has a `download_url`, and
  (with `--check-urls`) each URL answers an HTTP HEAD.

## `test_validate_manifest.py` — self-tests

```bash
pytest scripts/test_validate_manifest.py
```

Throwaway `tmp_path` phase fixtures exercise each check (valid phase clean, schema-invalid id,
duplicate id across phases, dangling in-repo path, orphan file, unresolved reference, missing
usage tag, release-gate download-url, empty dir). Needs the same two packages importable.
