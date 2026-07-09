# Phases — cross-artifact index & reproducibility record

This top-level folder is the project's **cross-artifact index**: a per-phase
record of every artifact a science phase produced (banks, runs, models,
observations, figures, papers) and how they relate ("what produced what"). It
is the ground truth the provenance graph and the per-paper reproducibility gate
are both built on.

It lives at the repo root (not under `project/`) because it is *not* internal
design documentation — it is the reproducibility data for each phase's results,
the thing a reader reaches for to answer "which bank + model + config produced
this figure?". The full rationale and schema-by-schema reference live in
[`../project/cross_artifact_linkage_design.md`](../project/cross_artifact_linkage_design.md);
this README is the operational quickstart.

`phase_1_5_example/` is a committed **template** — a minimal, well-formed phase
folder so a new reader (or a fresh chat) can see the shape without loading a
real, data-heavy phase. Real phase folders appear here as phases produce
artifacts.

## Layout

One folder per science phase. The folder name uses the underscore form of the
phase number (`phase_1_5` for phase 1.5):

```
phases/
├── README.md                     ← this file
├── phase_1_5_example/            ← committed template (see below)
└── phase_1_5/                    ← a real phase folder
    ├── manifest.json             ← the shallow index (PhaseManifest schema)
    ├── observations/
    │   └── <obs-id>.json         ← one Observation file per discovery
    └── figures/
        └── <fig-id>.json         ← one FigureSpec file per figure
```

The `manifest.json` is a **shallow index of pointers, not content**. Each entry
carries only an `id`, a `path` to the real artifact, its producer
(`produced_by_package` / `produced_by_version`), the relationship pointers to
other artifacts, and an optional `usage_tag` / `download_url`. Everything
descriptive — an observation's prose, a figure's recipe and inputs, a bank's
metrics — lives in the file the entry points at. Banks and models are large
binaries that live **outside** this repo (in producer output dirs / GitHub
Release assets) and are gitignored; the manifest only points at them.
Observation and figure-spec files are small JSON and live **inside** the phase
folder, alongside the manifest.

Manifest sections: `egm_banks` (training `tbank_`, pretraining `ptbank_`, and
prediction `lpred_`/`upred_` banks — a prediction bank is just an EGM-bank
entry that also fills `model` + `source_bank`), `noise_banks` (`nbank_`),
`training_runs` (`run_`), `models` (`model_`), `observations` (`obs_`),
`figures` (`fig_`), and `papers` (`paper_`).

## Stable IDs

Every artifact carries a stable id, assigned by its producer at write time and
never reused. The id prefix encodes the role:

| Prefix | Artifact | Id shape |
|---|---|---|
| `tbank_` / `ptbank_` | training / pretraining EGM bank | `<prefix>_<descriptor>_<date>[_vN]` |
| `lpred_` / `upred_` | labeled / unlabeled prediction bank | `<prefix>_<descriptor>_<date>[_vN]` |
| `nbank_` | noise bank | `nbank_<descriptor>_<date>[_vN]` |
| `run_` | training run record | `run_<descriptor>_<date>[_vN]` |
| `model_` | exported model | `model_<descriptor>_<date>[_vN]` |
| `obs_` | observation | `obs_<descriptor>_<date>[_vN]` |
| `fig_` | figure spec | `fig_<descriptor>` |
| `paper_` | paper | `paper_<descriptor>` |

The exact regexes are single-sourced in egm-contracts' `common.schema.json`
(`ArtifactId`, `FigureId`, `PaperId`) and enforced by the schemas — so the
validator's schema check (A.6 below) is also what guarantees id format. The
date suffix is optional (a hand-set id may omit it; egm-contracts ≥ v0.5.3).

## Usage tags

Observations and figures carry a `usage_tag` recording why the artifact exists
relative to the phase's paper (free-text `usage_notes` captures nuance):

| Tag | Meaning |
|---|---|
| `in_paper_main` | In the paper's main body. *(Figures only.)* |
| `in_paper_supplementary` | In the supplementary material. *(Figures only.)* |
| `informed_paper` | Informed a paper claim, even if no figure references it. *(Observations only.)* |
| `exploratory` | Generated while exploring; kept as a record, not in the paper. |
| `additional_example` | Extra visualization/note beyond the paper's argument. |
| `pending` | Still being investigated; usage TBD. |
| `superseded` | Replaced by another artifact (name it in `usage_notes`). |
| `dead_end` | Investigated, didn't pan out; kept for the historical record. |

Tags are optional during a working window so you can save artifacts
mid-investigation without being nagged, but **required at release-gate time** —
anything still untagged when a paper ships is a hard error.

## Curation workflow

1. **Producers stamp IDs.** synthetic-egm-pipeline, iafdb-pipeline, and
   egm-classifier write each artifact with its stable id already in the file
   (egm-contracts ≥ v0.5.0, egm-data ≥ v0.4.0). Producers never touch the
   manifest.
2. **egm-studio is the canonical curator.** Its Phase GUI updates
   `manifest.json` as you save observations and figures and as you point it at
   producer artifacts. Day to day, you should not be hand-editing the manifest.
3. **`validate_manifest.py` is the safety net.** Run it (manually or from a
   git hook) to catch drift the curator can't — a file saved by hand without a
   manifest entry, a dangling reference, a forgotten usage tag.
4. **Release gate.** Before declaring a phase shipped and committing its paper
   to intracardiac-papers, run the validator with `--release-gate`. It must
   pass.

The validator never auto-fixes — it reports, and you fix by hand. Auto-fix is a
foot-gun on a research project.

### No backfill

Manifests are created **going forward**, as phases produce artifacts through
the stamped-id pipeline. Past work is not retro-indexed. A phase folder appears
the first time that phase has an artifact worth recording; until then it simply
doesn't exist here (the `phase_1_5_example/` template aside).

## Running the validator

`scripts/validate_manifest.py` builds on the egm-contracts validators and the
egm-data phase readers, so both packages must be importable. See
[`../scripts/README.md`](../scripts/README.md) for the full CLI reference.

```bash
# All phases. Errors are fatal; coverage/URL gaps are warnings.
python scripts/validate_manifest.py

# One phase (folder suffix).
python scripts/validate_manifest.py --phase 1_5

# Release gate: usage-tag (B) and download-url (C) gaps become fatal too.
python scripts/validate_manifest.py --phase 1_5 --release-gate

# Also HEAD-request every download_url (slow; needs network).
python scripts/validate_manifest.py --phase 1_5 --release-gate --check-urls
```

What it checks (numbers match `cross_artifact_linkage_design.md` §8):

- **A — integrity (always fatal).** A.1 id format · A.2 no duplicate ids across
  the project · A.3 every `path` resolves (in-repo files = error; external
  bank/model/paper targets = warning) · A.4 no on-disk observation/figure file
  missing from the manifest · A.5 every relationship pointer resolves to a known
  id · A.6 every manifest/observation/figure file passes its egm-contracts
  schema (this is what enforces A.1).
- **B — load-bearing coverage (warn; fatal at release-gate).** B.7/B.8 every
  observation/figure has a `usage_tag` · B.9 in-paper consistency.
- **C — distribution (release-gate only).** C.10/C.11 every bank/model has a
  `download_url` · C.12 (with `--check-urls`) each URL answers an HTTP HEAD.

Self-tests for the validator live next to it at
`scripts/test_validate_manifest.py`.
