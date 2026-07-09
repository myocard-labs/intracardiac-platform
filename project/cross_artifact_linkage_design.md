# Cross-artifact linkage + per-phase organization design

This is the **canonical design for how data moves between the myocard-labs repos** — the stable
IDs every artifact carries, the schemas that cross repo boundaries, the per-phase manifest that
indexes them, and the egm-studio + validator tooling that curates them. It began by resolving
three egm-studio Block 0 ADRs that all shared one underlying question — *"how do we systematically
track what produced what, across phases and across artifact types?"*:

- **ADR-017** — unified save schema for observations + trace sets
- **ADR-021** — per-phase manifest file structure
- **ADR-022** — model unique-ID + cross-artifact linkage

Resolving them in isolation would have produced mismatched designs, so this doc lays out one
coherent design covering all three, then enumerates the per-repo work.

It reflects what is **actually shipped**, not an aspirational draft. **When a new kind of data
needs to travel between repos, extend this document** — add its ID role (§1), its schema (§2),
and its manifest section (§3) — as part of that work.

## Status

- **Drafted:** 2026-06-25 (egm-studio Block 0 design conversation — Daniel Klein + Claude).
- **Resolves:** egm-studio ADR-017 / ADR-021 / ADR-022, which carry short "see this doc" entries
  in `egm-studio/project/design.md`.
- **Boundary with egm-studio:** the current-state source of truth for egm-studio *GUI behavior* is
  `egm-studio/project/` (architecture.md + ADRs 017 / 021 / 022 / 026 / 027). This document owns
  the cross-repo data-transfer design; that repo owns its GUI's as-built detail.

## Revision history

Big changes only — small fixes and refactors are left to git history.

- **2026-06-25 — drafted** across egm-studio ADR-017 / 021 / 022.
- **2026-06-27 — shipped in egm-contracts v0.5.0.** On-disk format is **JSON, not YAML**. Stable-id
  patterns (`ArtifactId` / `FigureId` / `PaperId`) single-sourced in `common.schema.json`. Manifest
  banks split into `egm_banks` + `noise_banks` (a prediction bank is an `egm_banks` entry that also
  fills `model` + `source_bank`). Observation prose field is `description`, with no `phase` field;
  figure spec requires `description` and drops `inventory_ref`; the model sidecar carries only
  `model_id`. The predictions-bank id lives on egm-data's `ClassifierBank`, not a contracts schema.
  `hybrid_eval_metrics` was removed.
- **2026-07 — egm-studio as-built (Blocks 6–10).** The Phase GUI, save/scratch, and curation were
  built ground-up (not a merge of the old viewers). Scratch is a full mini-phase with its own
  `manifest.json` in an app-data folder. A single Open-bank path detects predictions (no separate
  "Load Evaluated Bank"). Noise is a fourth top-level mode. The figure-render CLI is
  `egm-studio-render <spec>.json`. Manual *Add to / Remove from phase* curation shipped; the
  after-each-write validator hook is still deferred.
- **2026-07 — platform Step 8.** The phase index moved from `project/phases/` to the repo top-level
  `phases/`; it ships as a convention + validator only — no backfilled or placeholder phase folders
  (a `phase_X/` folder appears when that phase has a real artifact).

## Settled decisions (summary)

| # | Decision | Rationale |
|---|---|---|
| 1 | **Artifact IDs are human-readable slug + ISO date** | Readable in prose + file paths. Matches research-project culture. e.g. `synthegm_v1_5_courtemanche_2026-06-25`. |
| 2 | **Observation files are standalone JSON files in the meta repo** | One file per observation under `phases/phase_X/observations/<id>.json`. Easy to git-diff + parse, and consistent with the other egm-contracts record formats (`run.json`, `model_metadata.json`). |
| 3 | **Per-phase manifest is a shallow index with named relationship fields** | Each artifact entry has its ID + path + relationship fields. Field names map cleanly to future edge types if we ever upgrade to a full provenance graph. |
| 4 | **Backfill scope: new artifacts only** | Schema changes apply only to artifacts produced after the change lands. Old artifacts keep their current state. |
| 5 | **Trace ID strategy: hybrid** | v0.1 ships integer-index addressing inside a bank `(bank_id, index)`. Stable per-trace IDs on the roadmap; trigger condition is "if the integer-index fragility proves problematic in practice." |
| 6 | **Manifest curation: egm-studio is the curator; producers don't touch it; scan-and-validate script is the safety net** | Producers write artifacts with stable IDs; egm-studio's Phase GUI updates the manifest as the user saves observations / figures / etc. Scan-and-validate runs periodically to catch drift. |
| 7 | **Storage strategy: images gitignored + regenerated; banks via GitHub Releases** | Image files are deterministic build outputs from spec JSON — gitignored, rebuilt locally. Banks attached as GitHub Release assets on the producer-repo's version tag. Manifest records local path + release URL. If active bank-sharing with collaborators becomes load-bearing, shift bank distribution to Hugging Face Datasets. |
| 8 | **Phase GUI shape: collapsible right-rail sidebar** | Phase loaded once at startup; right-rail sidebar with manual-add controls + collapsible artifact tree grouped by type. Click artifact → inline expansion; "Open in tab" promotes to full detail tab. Affects what every egm-studio mode sees. Scratch mode = no phase loaded. |
| 9 | **Scratch is a scratch mini-phase; can be promoted to a phase later** | Observations / figure specs saved without a loaded phase land in a Settings-editable app-data scratch folder that is itself a full mini-phase (its own `manifest.json`). "Promote to Phase X" moves + indexes them into a real phase. |
| 10 | **Trace sets are embedded inside observations, not standalone artifacts** | One artifact type for "I noticed something cool." An observation can carry a free-text `description`, an embedded trace list, or both. Figures and other observations reference the parent observation by ID. |

---

## 1. Artifact ID scheme

### Format

```
<artifact_type_prefix>_<descriptive_name>_<YYYY-MM-DD>
```

- **Prefix** identifies the artifact's **role in the ML pipeline**, not its data origin. Almost
  every bank in the project flows through the `ClassifierBank` structure for analysis (synthetic
  and IAFDB banks get converted on read), so categorizing prefixes by origin would split things
  that downstream code treats identically. Categorizing by role tells consumers what they can do
  with the artifact:

  | Prefix | Role | Notes |
  |---|---|---|
  | `tbank_` | **Training bank** | ClassifierBank with truth labels; usable for train / val / labeled eval. |
  | `lpred_` | **Labeled prediction bank** | Predictions + truth labels — full metric suite available (ROC / confusion / calibration / etc.). |
  | `upred_` | **Unlabeled prediction bank** | Predictions but no truth labels (the IAFDB shape) — qualitative inspection only per [[feedback-iafdb-unlabeled-no-ml-validation]]. |
  | `ptbank_` | **Pretraining bank** | Unlabeled bank for self-supervised pretraining (CLOCS in Phase 5+). Phase-5 introduction. |
  | `nbank_` | **Noise bank** | Additive-noise source for the synthetic-egm-pipeline mixer. Distinct role from training data. |
  | `run_` | Training run record | The `run.json` artifact. |
  | `model_` | Exported model | Paired with its run via a `trained_from_run` pointer. |
  | `obs_` | Observation | Free-text + optional trace list + view state. |
  | `fig_` | Figure spec | Date often unnecessary — typically use the inventory ID directly (e.g. `fig_F-1-5-2`). |

  **Signal source goes in the descriptive name OR in the bank's internal description field** — not
  in the prefix. So `tbank_synthetic_courtemanche_v1_5_2026-06-25` reads as "training bank,
  synthetic / Courtemanche / v1.5, dated 2026-06-25." `upred_iafdb_v1_5_2026-06-25` reads as
  "unlabeled predictions on IAFDB from the v1.5 model on 2026-06-25."

  **Why role-first matters:** egm-studio's single Open-bank action branches on whether truth labels
  are present. With role-based prefixes the loader can tell a labeled predictions bank (`lpred_`)
  from an unlabeled one (`upred_`) from the ID before opening the file; with origin-based prefixes
  (the old `synthegm_` / `iafdb_` / `pred_`) the same ID could mean any of several branches and the
  loader would have to inspect file contents to decide. (egm-studio detects predictions + labels on
  open via `gui/sources.frame_eval_mode` and populates the ML-diagnostics mode automatically —
  there is no separate "Load Evaluated Bank" entry.)
- **Descriptive name** uses lowercase + underscore. Should be terse but specific enough to
  disambiguate by eye. e.g. `v1_5_courtemanche` rather than `v1_5` alone.
- **Date** is ISO 8601 (`YYYY-MM-DD`). The date the artifact was produced.
- **Optional iteration suffix** for multiple variants in a day: `_v1`, `_v2`. Use only if same-day
  disambiguation is needed.

### Examples

```
tbank_synthetic_courtemanche_v1_5_2026-06-25      # training bank, synthetic source
tbank_synthetic_aliev_panfilov_v1_2026-05-20      # earlier training bank, Aliev-Panfilov source
nbank_iafdb_2026-06-15                            # noise bank from IAFDB
upred_iafdb_v1_5_2026-06-25                       # unlabeled predictions on IAFDB
upred_iafdb_v1_baseline_2026-05-20                # baseline-model unlabeled preds on IAFDB
lpred_synthetic_v1_5_holdout_2026-06-25           # labeled preds on synthetic held-out
ptbank_iafdb_adjacent_segments_2026-09-01         # pretraining bank for CLOCS (Phase 5)
run_v1_5_courtemanche_2026-06-25                  # training run record
model_egm_classifier_v1_5_2026-06-25              # exported model paired with the run
obs_courtemanche_high_entropy_tail_2026-06-25     # observation
fig_F-1-5-2_feature_distributions                 # figure spec, no date needed
```

### Constraints

- Lowercase + underscore + ASCII only (avoid OS-level filename weirdness across Linux / macOS /
  Windows / GitHub).
- No spaces.
- Hyphens reserved for the date portion only.
- Pattern enforced by JSON-Schema validation: regex
  `^[a-z]+_[a-z0-9_]+_\d{4}-\d{2}-\d{2}(_v\d+)?$` (modulo the `fig_` exception). The `ArtifactId` /
  `FigureId` / `PaperId` patterns are single-sourced in egm-contracts' `common.schema.json` and
  referenced cross-file by every schema that carries an ID.

### Uniqueness

- Across the project. Same ID = same artifact, no exceptions.
- Enforced at validate-time, not write-time. The scan-and-validate script catches duplicates.

### How IDs get assigned

- **Producers** (synthetic-egm-pipeline, iafdb-pipeline, egm-classifier) compute the ID at
  artifact-write time from `(prefix, descriptive_name_from_config, today's_date)`. The ID is
  written into the artifact's provenance record (HDF5 attribute or JSON sidecar field). **No
  interactive prompt** — the producer's config carries the descriptive name; the producer stamps
  the date.
- **egm-studio** (for observations, figure specs) computes the ID at Save time the same way. The
  user types the descriptive name in the Save dialog; date auto-fills.

---

## 2. Schemas that cross repo boundaries

egm-contracts v0.5.0 added an `id` field — and, where applicable, relationship-pointer fields — to
the existing record schemas, plus three new schemas for the per-phase index. All ID fields use the
§1 format, validated by the shared `ArtifactId` pattern in `common.schema.json`.

| Schema | New / changed fields | Notes |
|---|---|---|
| `iafdb_bank_run_record` (embedded in HDF5) | + `bank_id` | Required for new banks; absent on legacy. |
| `synthetic_bank_run_record` (embedded in HDF5) | + `bank_id` | Same. |
| `noise_bank_run_record` (JSON sidecar) | + `bank_id` | Same. |
| `training_run_record` (`run.json`) | + `run_id`, + `produced_model_id`, + `trained_on_bank_id` | Run ID is the run's own; relationship pointers reference the model + bank. |
| `egm_class_model_metadata` (JSON sidecar) | + `model_id` | Model gets its own ID; the model→run link is recorded solely by the run record's `produced_model_id` (the sidecar carries only what a deployed model needs). |
| Predictions bank — egm-data `ClassifierBank` (**not** a contracts schema) | + `bank_id`, + `model_id`, + `source_bank_id` | This predictions bank's own ID + the model + the source bank. Lives on the egm-data `ClassifierBank` because a JSON Schema would force its numpy arrays into a JSON shape. |
| **NEW: `phase_manifest`** (JSON) | full schema; see §3 | Lives in intracardiac-platform; egm-contracts owns the schema. |
| **NEW: `observation`** (JSON) | full schema; see §4 | Lives in intracardiac-platform. |
| **NEW: `figure_spec`** (JSON) | full schema; see §5 | Lives in intracardiac-platform. |

### Optional vs required during transition

For the existing schemas that gained ID fields, the field is **required for new artifacts** but
**optional for legacy artifacts** (per backfill decision #4). The distinction is enforced on write
by egm-data (the fields are optional in-schema so legacy files still validate); the companion
`schema_version` on every record marks the format generation.

---

## 3. Per-phase manifest schema

Lives at `phases/phase_X/manifest.json`.

### Top-level structure

```json
{
  "schema_version": "1",
  "phase": 1.5,
  "status": "in_progress",
  "phase_summary": "One-paragraph description of what this phase is about. Free-text; mostly for human readability when opening the file cold.",

  "egm_banks": [],
  "noise_banks": [],
  "training_runs": [],
  "models": [],
  "observations": [],
  "figures": [],
  "papers": []
}
```

`status` is one of `in_progress` / `shipped` / `abandoned`. Sections run data → models → derived
observations → figures → papers; each is empty-list-OK. **Banks split by content/role:**
`egm_banks` holds the EGM-trace banks — training (`tbank_`), pretraining (`ptbank_`), and
prediction (`lpred_` / `upred_`); a prediction bank is just an entry that additionally fills
`model` + `source_bank`. `noise_banks` holds additive-noise banks (`nbank_`), whose content and
role differ.

### Entry shape — universal pattern

**Manifest entries are pointers, not content.** Each entry has only:

- `id` — required, unique across the project.
- `path` — required, relative to the meta repo (or relative to the manifest's location).
- `produced_by_package` + `produced_by_version` — required on every entry type. Even for
  observations / figures (where the producer is egm-studio), tracking the producer version matters
  for reproducibility — if egm-studio's view-state schema changes between versions, knowing which
  version saved the observation matters.
- Relationship references to other artifacts — wherever applicable, as ID strings.
- `usage_tag` — optional, on artifact types that aren't self-evidently load-bearing (observations
  and figures get this). Used by the scan-and-validate script to ensure nothing tagged important
  got forgotten. See §8.
- `usage_notes` — optional free-text nuance.
- `download_url` — **optional**, only on artifact types that get distributed (banks, models).
  Filled in at **phase-release time** when the producer-repo cuts a versioned release and the
  artifact is attached as a GitHub Release asset. Not filled during day-to-day phase work; the
  local `path` is sufficient there.

**Everything else** (title, date, description, embedded traces, view state, training-run select
metric, epoch counts, similarity-metric choice, etc.) lives **inside the standalone JSON file** at
`path`. The manifest only carries pointers.

### Per-artifact-type entry shape

**`egm_banks:` entry** (training / pretraining / prediction — the prefix tells the type)

```json
{
  "id": "tbank_synthetic_courtemanche_v1_5_2026-06-25",
  "path": "relative/or/abs/path/to/file.h5",
  "produced_by_package": "synthetic-egm-pipeline",
  "produced_by_version": "v0.3.0",
  "download_url": "https://github.com/.../releases/download/v0.3.0/tbank_synthetic_courtemanche_v1_5.h5"
}
```

`download_url` is **optional**, filled at phase-release time (not write time). During day-to-day
work banks live locally and the manifest carries only the local `path`; when the phase ships a
paper and the producer-repo cuts a versioned release, the bank is attached as a GitHub Release
asset and the entry is updated with the URL. Same applies to model entries.

A **prediction bank** is an `egm_banks` entry that additionally fills `model` + `source_bank`:

```json
{
  "id": "upred_iafdb_v1_5_2026-06-25",
  "path": "predictions/upred_iafdb_v1_5.classifier.h5",
  "produced_by_package": "egm-classifier",
  "produced_by_version": "v0.4.0",
  "model": "model_egm_classifier_v1_5_2026-06-25",
  "source_bank": "tbank_iafdb_v1_2026-06-15"
}
```

**`training_runs:` entry**

```json
{
  "id": "run_v1_5_courtemanche_2026-06-25",
  "path": "relative/or/abs/path/to/run.json",
  "produced_by_package": "egm-classifier",
  "produced_by_version": "v0.4.0",
  "trained_on_bank": "tbank_synthetic_courtemanche_v1_5_2026-06-25",
  "produced_model": "model_egm_classifier_v1_5_2026-06-25"
}
```

**`models:` entry**

```json
{
  "id": "model_egm_classifier_v1_5_2026-06-25",
  "path": "relative/or/abs/path/to/best.pt",
  "produced_by_package": "egm-classifier",
  "produced_by_version": "v0.4.0",
  "trained_from_run": "run_v1_5_courtemanche_2026-06-25",
  "download_url": "https://..."
}
```

(The model metadata sidecar is referenced from the model's run.json, not duplicated in the
manifest.)

**`observations:` entry**

```json
{
  "id": "obs_courtemanche_high_entropy_tail_2026-06-25",
  "path": "observations/obs_courtemanche_high_entropy_tail.json",
  "produced_by_package": "egm-studio",
  "produced_by_version": "v0.1.0",
  "usage_tag": "informed_paper"
}
```

(Title, date, description, trace list, view state — all inside the observation JSON itself, not the
manifest.)

**`figures:` entry**

```json
{
  "id": "fig_F-1-5-2_feature_distributions",
  "path": "figures/F-1-5-2_feature_distributions.json",
  "produced_by_package": "egm-studio",
  "produced_by_version": "v0.1.0",
  "consumes_banks": [
    "tbank_synthetic_courtemanche_v1_5_2026-06-25",
    "tbank_iafdb_v1_2026-06-15"
  ],
  "consumes_models": [],
  "consumes_observations": [],
  "usage_tag": "in_paper_main"
}
```

(`output.path`, layout, styling, etc. live inside the figure spec JSON, not the manifest. The
figure's manifest-entry `path` is the spec JSON.)

**`papers:` entry**

```json
{
  "id": "paper_phase_1_5_realism",
  "path": "../../../intracardiac-papers/papers/phase_1_5_realism/",
  "produced_by_package": "intracardiac-papers",
  "produced_by_version": "latest",
  "figures": [
    "fig_F-1-5-2_feature_distributions",
    "fig_F-1-5-3_distance_reduction"
  ]
}
```

### Relationship-field naming convention (graph-upgrade-compatible)

When/if we ever upgrade to a full provenance graph, the shallow-index field names translate
directly to typed edges. The convention:

| Shallow field name | Future edge type | Direction |
|---|---|---|
| `trained_on_bank` | `TRAINED_ON` | run → bank |
| `produced_model` | `PRODUCED` | run → model |
| `trained_from_run` | `TRAINED_FROM` | model → run (inverse of PRODUCED) |
| `source_bank` | `REFERENCES_SOURCE` | predictions → bank |
| `model` (in predictions / eval) | `EVALUATED_BY` | predictions → model |
| `consumes_banks` | `VISUALIZES` | figure → bank |
| `consumes_models` | `VISUALIZES_MODEL` | figure → model |
| `consumes_observations` | `BUILDS_ON` | figure → observation |

The upgrade script reads the shallow index, generates the corresponding edge list. One-time
migration, no producer changes.

---

## 4. Observation file schema

Lives at `phases/phase_X/observations/<id>.json`.

```json
{
  "schema_version": "1",
  "id": "obs_courtemanche_high_entropy_tail_2026-06-25",
  "date": "2026-06-25",
  "title": "Courtemanche synthetic produces high-entropy traces IAFDB doesn't show",

  "description": "When loading the Courtemanche-based synthetic bank alongside IAFDB, the synthetic sample_entropy distribution has a long tail above 1.5 that IAFDB never reaches. ~5% of synthetic traces show sample_entropy > 1.5; 0% of IAFDB does. The high-entropy synthetic traces appear visually as fragmented multi-deflection patterns; IAFDB high-amplitude segments are uniformly cleaner biphasic morphology.",

  "references": {
    "models": [],
    "observations": []
  },

  "traces": [
    { "bank": "tbank_synthetic_courtemanche_v1_5_2026-06-25", "index": 1247 },
    { "bank": "tbank_iafdb_v1_2026-06-15", "index": 89 }
  ],

  "view_state": {
    "banks_loaded": [
      "tbank_synthetic_courtemanche_v1_5_2026-06-25",
      "tbank_iafdb_v1_2026-06-15"
    ],
    "filter": "sample_entropy > 1.5",
    "sort": "sample_entropy desc",
    "selected_trace_indices_within_filter": [0, 1, 2]
  }
}
```

Field notes:

- `description` is **required** — the prose "what I noticed." The whole point of an observation is
  to record a discovery; a pure trace list with no prose is data without context. (The prose field
  is `description`, not `body`; the artifact does not record its own `phase` — phase membership is
  held only by the manifest that points at it.)
- `references` holds structured pointers to **other artifact types** — models and parent
  observations (this observation builds on those). Bank references are **not** listed here: they'd
  be redundant with `view_state.banks_loaded` + `traces[].bank`, so the scan-and-validate script
  derives the bank-reference set as the union of those two sources.
- `traces` is **optional**. An observation can be pure-prose with no trace list. When present, the
  trace list becomes the data source for downstream figures (e.g. a trace-gallery figure that
  references this observation's ID). `index` is the integer index inside the bank (the v0.1
  trace ID).
- `view_state` is **optional**. Adds reproducibility — egm-studio can offer a "reload this
  observation's view" button.

Since trace sets live inside observations (decision #10), the trace-list form of an observation
serves both roles.

---

## 5. Figure spec schema

Lives at `phases/phase_X/figures/<id>.json`.

```json
{
  "schema_version": "1",
  "id": "fig_F-1-5-2_feature_distributions",
  "description": "Per-feature distribution overlay of the v1.5 Courtemanche synthetic bank against IAFDB, annotated with the Wasserstein distance per feature — the sim-realism diagnostic behind the Phase 1.5 realism claim.",
  "recipe": "feature-distribution-overlay",

  "inputs": {
    "groups": [
      { "name": "Synthetic v1.5 (Courtemanche)", "bank_id": "tbank_synthetic_courtemanche_v1_5_2026-06-25" },
      { "name": "IAFDB", "bank_id": "tbank_iafdb_v1_2026-06-15" }
    ],
    "feature_subset": "all",
    "distance_annotation": "wasserstein"
  },

  "layout": {
    "panel_grid": [3, 4],
    "per_panel_size_inches": [1.5, 1.2]
  },

  "styling": {
    "palette": "project_standard",
    "font_family": "Helvetica",
    "font_size_pt": 9,
    "dpi": 300
  },

  "output": {
    "format": "pdf",
    "path": "../../../intracardiac-papers/papers/phase_1_5/figures/F-1-5-2_feature_distributions.pdf"
  },

  "illustrates_observations": [
    "obs_courtemanche_high_entropy_tail_2026-06-25"
  ]
}
```

Field notes:

- `description` is **required** — it records why the figure exists. (The old `inventory_ref`
  cross-ref to a paper-figure-inventory was dropped: the inventory is a study, not a fixed
  contract. The spec does not record its own `phase`.)
- `recipe` names one of the egm-studio figure recipes; `inputs` / `layout` / `styling` are
  recipe-specific and validated by the schema's discriminator on `recipe`.
- `output.path` points **out** of the meta repo into the paper repo (decision #7). The output image
  is gitignored at the paper repo and regenerated locally from this spec at paper-build time; the
  spec JSON is the git-tracked source of truth.
- `illustrates_observations` drives the `consumes_observations` field on the manifest entry.

---

## 6. Image + bank storage strategy

### Images (figure outputs)

- **Gitignored** at the paper repo (`intracardiac-papers/papers/<slug>/figures/`).
- **Regenerated locally** from spec JSON via the headless CLI:
  ```
  egm-studio-render <spec>.json
  ```
- **Paper-build pipeline** (the papers repo's `make`) runs the render step before `latexmk`,
  ensuring the figures exist at build time.
- **No version control of binary outputs.** The spec is the artifact; the image is build output.

### Banks (HDF5 producer outputs)

- **Local-first.** Banks live wherever the producer wrote them (e.g.
  `~/data/banks/synthegm_v1_5_courtemanche.h5`). The manifest entry records the local path.
- **Distribution via GitHub Releases.** When a producer ships a tagged release, the reference bank
  for that release gets uploaded as a release asset:
  ```
  synthetic-egm-pipeline v0.3.0 release
  └── synthegm_v1_5_courtemanche.h5  (asset, public download)
  ```
  The manifest entry records the `download_url` alongside the local path.
- **Reproducibility flow:** someone reproducing a phase's paper results clones intracardiac-platform,
  reads the manifest, sees the URLs, downloads via `wget` / curl. A collaborator producing locally
  has the local path and skips the download.
- **GitHub Releases free quota:** unlimited download bandwidth + 2 GB per asset + a reasonable
  storage budget. Suffices for current bank sizes (~100–500 MB).

### Future upgrade: Hugging Face Datasets

If active bank-sharing between collaborators gets painful via the Release-download workflow, shift
bank distribution to **Hugging Face Datasets** (Daniel already has an account): cleaner
multi-collaborator workflow, versioned + branchable, and public-visibility benefit when papers cite
the dataset. Trigger condition: at least two people actively producing banks that need to flow
between them.

### Future: Zenodo for paper-archival data

When a paper actually publishes, push the paper's specific bank set to Zenodo for a citable DOI.
Working data stays on GitHub Releases (or HF Datasets); paper-archived data also gets a DOI.

---

## 7. Phase GUI in egm-studio

*(As-built lives in `egm-studio/project/`; this is the cross-artifact rationale for the shape.)*

### Shape: collapsible right-rail sidebar

A persistent **right-rail sidebar** that can collapse to a thin strip and expand for active phase
work. Visible regardless of which of the four top-level modes — **signal exploration · noise · ML
diagnostics · paper-figure prep** — is active. The header always shows the currently-loaded phase
name (or "scratch mode") and a count summary.

### Expanded sidebar — top section: manual add + scratch promotion

A controls area at the top of the sidebar lets the user:

- **Add an existing file to the current phase.** File picker; user selects any artifact file (bank,
  model, observation JSON, figure spec).
- **When the selected file is NOT already inside `phases/phase_X/<type>/`**, the user is prompted
  with three options: **Move** into the expected location (canonical), **Copy** (leaves the
  original in place), or **Leave in place** (the manifest entry references the out-of-tree
  location).
- **If "leave in place" is chosen**, the sidebar shows a warning indicator on the artifact (red
  text + icon) with a hover tooltip, and a "Fix it" button that offers to move / copy with one
  click.
- **Promote scratch artifacts.** A button brings up the scratch inventory; the user selects which
  scratch items to promote into the current phase (same move / copy / leave-in-place options).

### Expanded sidebar — bottom section: phase artifact tree

The phase's artifacts display as a **collapsible grouped tree**, split by role (matching the §1
prefix scheme) so the user can find "training banks" or "unlabeled predictions" without scrolling
past unrelated entries. This 10-group split is a **display** grouping the GUI derives from each
artifact's ID prefix — it's independent of the manifest's **storage** shape (groups
`tbank_`/`ptbank_`/`lpred_`/`upred_` all live in `egm_banks`; `nbank_` lives in `noise_banks`), so
no manifest change is needed to keep the tree.

Groups, in order:

1. **Training banks** (`tbank_`)
2. **Pretraining banks** (`ptbank_`) — hidden when empty (Phase 5+ only)
3. **Noise banks** (`nbank_`)
4. **Training runs** (`run_`)
5. **Models** (`model_`)
6. **Labeled prediction banks** (`lpred_`)
7. **Unlabeled prediction banks** (`upred_`)
8. **Observations** (`obs_`)
9. **Figures** (`fig_`)
10. **Papers** (`paper_`)

Each group header shows the **item count** next to the group name at all times ("Training banks
(7)"), collapsed or expanded, for a quick scan of phase contents. Groups collapse / expand
independently; the default-expanded set persists across sessions. A group with zero entries
collapses to a single clickable line ("Pretraining banks (0)"); groups that don't apply to the
phase are hidden entirely.

### Artifact click → inline expansion + Open in tab

Clicking an artifact **expands it inline** to show the manifest-entry view (ID, path, producer
info, relationship references, usage tag). A small **`[Open in tab]`** button promotes to a full
detail tab in the main work area — loads the full artifact content, lets you edit the usage tag,
and shows the artifact's "neighborhood" (related artifacts as clickable links). Tabs are persistent
for side-by-side comparison; closing one doesn't affect the file. **Rationale for
inline-default + open-in-tab:** most clicks are quick lookups ("what produced this bank?"), which
inline expansion answers without disturbing the current view; deeper inspection wants persistence
and comparison, which a tab gives. A popup would combine the worst of both.

### What the phase context controls

- **Default save target.** Every Save action (observation, figure spec, trace export) lands in the
  loaded phase's folder; the manifest entry is added automatically.
- **Suggested loaders.** When loading a bank or model, in-phase artifacts sort to the top of the
  file picker; others still load normally.
- **Cross-phase references.** Loading an artifact from another phase works fine; the manifest entry
  records the cross-phase reference. Phase IDs are globally unique so the reference is unambiguous.

### Scratch mode

- Triggered when egm-studio opens without a phase loaded.
- **Save target: a Settings-editable app-data scratch folder that is itself a full mini-phase** —
  its own `manifest.json`, rendered by the same Phase-tree widget with the same status dots +
  viewers. Each scratch artifact gets a stable ID like any other.
- The sidebar header reads "scratch mode" + the scratch artifact count.
- **Promote to Phase…** moves the file(s) + re-indexes producer pointers into the target phase, and
  pulls the artifact's scratch-resident dependency closure along (auto-add, Settings-toggle).
  Verification is **cross-scope**: a scratch item resolves IDs against scratch + the loaded phase; a
  phase item against the phase only.

### Default-phase preference

- User preference "open this phase on launch," stored in egm-studio's user config (XDG-respecting).
  Manual override always available via "Open Phase…".

---

## 8. Scan-and-validate script

Lives at `scripts/validate_manifest.py`. Runs manually or via a git pre-commit / pre-push hook.
**Must be run as a release gate before any phase containing a paper is considered released.** (The
egm-studio hook that would re-run it after each in-app write is still deferred — curation is manual
today.)

The script's two principal purposes:

### Check A: No orphan files in the phase folder

Every file in `phases/phase_X/<type>/` should appear in the manifest. Catches "I saved this
observation manually, forgot to add the manifest entry."

Sub-checks:
1. **Stable-ID format.** Every artifact ID matches the §1 regex. Reports violations.
2. **No duplicate IDs across the project.** Reports dupes.
3. **Path validity.** Every manifest entry's `path` resolves to a real file. Reports dangling.
4. **Unindexed artifacts.** Scans each phase's subfolders for files NOT mentioned in the manifest.
   Reports drift.
5. **Cross-reference integrity.** Every `trained_on_bank`, `produced_model`, `source_bank`, etc.
   resolves to an artifact ID present somewhere in the project (current phase or another). Reports
   orphans.
6. **Schema validity.** Validates each JSON file against the egm-contracts schema for its type.
   Reports violations.

### Check B: No load-bearing artifact got forgotten

Every tagged artifact (observation, figure) must EITHER appear in the phase's paper OR carry a
usage tag explaining why it's not directly in the paper. Catches "I noticed something cool three
months ago, the observation file is right here, I never wrote it into the paper, and now I forgot
why I made it."

Sub-checks:
7. **Observation usage coverage.** Every observation entry has a `usage_tag` set. Reports unset.
8. **Figure usage coverage.** Every figure entry has a `usage_tag` set. Reports unset.
9. **In-paper consistency.** Every figure tagged `in_paper_main` / `in_paper_supplementary` is
   referenced by at least one `papers:` entry's `figures:` list; every observation tagged
   `informed_paper` has at least one figure listing it under `consumes_observations`. Reports
   inconsistencies.

### Check C: Distribution URLs present (release-gate only)

When a phase ships a paper, the banks + models it depends on need `download_url` populated so
collaborators can reproduce without local artifacts. Runs only in `--release-gate` mode.

Sub-checks:
10. **Bank distribution URL coverage.** Every bank entry has a `download_url`. Reports missing.
11. **Model distribution URL coverage.** Every model entry has a `download_url`. Reports missing.
12. **URL reachability.** (Optional / slow.) Each `download_url` returns HTTP 200 on a HEAD request.
    Reports broken URLs.

### Usage tag vocabulary

Standardized `usage_tag` values across observations + figures; free-text `usage_notes` captures
nuance.

| Tag | Meaning |
|---|---|
| `in_paper_main` | Used in the paper's main body. (Figures only.) |
| `in_paper_supplementary` | Used in the paper's supplementary material. (Figures only.) |
| `informed_paper` | Observation that informed a paper claim, even if no specific figure references it. (Observations only.) |
| `exploratory` | Generated during exploration; didn't end up in the paper but kept as a record of investigation. |
| `additional_example` | Extra visualization or note that goes beyond the paper's argument. |
| `pending` | Still being investigated; usage TBD. |
| `superseded` | Replaced by another artifact (note the replacement in `usage_notes`). |
| `dead_end` | Investigated, didn't pan out. Kept for historical record. |

A figure / observation MUST have a `usage_tag` once it's been in the manifest longer than a brief
working window; the script enforces this at release-gate time (fresh artifacts can be tag-less).

### Release-gate usage

Before declaring a phase shipped (and committing its paper to `intracardiac-papers`), run:

```bash
python scripts/validate_manifest.py --phase 1_5 --release-gate
```

`--release-gate` treats Check B (usage coverage) and Check C (distribution URLs) as fatal. In
day-to-day mode (no flag) Check B is a warning, so users can save artifacts mid-investigation
without being nagged.

### Output

A human-readable report + a non-zero exit code for CI / pre-commit gating. **Not auto-fixing** —
Daniel reviews + fixes manually. Auto-fix is a foot-gun for a research project.

---

## Implementation (shipped)

Ordered by dependency; all steps have shipped.

**Step 1 — egm-contracts v0.5.0.** Added the `id` field (regex-validated, optional during
transition) and relationship-pointer fields per §2 to the bank/run/model records; added the new
`phase_manifest` / `observation` / `figure_spec` schemas; single-sourced the id patterns in
`common.schema.json`. Codegen regen + tests; tagged v0.5.0.

**Step 2 — egm-data.** Bank/record readers surface the new IDs on the returned Pydantic models;
writers require the ID on new files while preserving backward compatibility for files without it.
The predictions-bank ID lives on egm-data's `ClassifierBank`.

**Step 3 — producer repos (parallel).** synthetic-egm-pipeline + iafdb-pipeline stamp `bank_id` at
write time; egm-classifier stamps `run_id` + `model_id` at train + export and writes predictions
banks with `bank_id` + `model_id` + `source_bank_id`. Each bumped its version + re-pinned.

**Step 4 — intracardiac-platform.** Shipped as a **folder convention + validator only**. The
top-level `phases/` directory holds one `phase_X/` folder per phase that has real artifacts — **no
backfill, no placeholder folders** for future phases (a `phase_X/` folder appears when that phase
first has something real to record). `scripts/validate_manifest.py` (+ its tests) is the safety
net; egm-data's phase readers + the contracts validators are its two dependencies. Manifests are
authored going forward by the stamped-ID producers + egm-studio curation.

**Step 5 — egm-studio (Blocks 6–10).** The Phase GUI, Open Phase, Save Observation / Save Figure,
scratch mini-phase, and Promote-to-Phase all shipped — built ground-up, not ported from the old
viewers. Manual *Add to / Remove from phase* curation shipped; the after-each-write validator hook
is deferred (see revision history). ADRs 017 / 021 / 022 in `egm-studio/project/design.md` point
back here.

---

## Open follow-ups (not decided here)

Intentionally deferred; each gets reviewed when its trigger fires:

- **Stable per-trace IDs inside banks.** Currently integer index + bank ID. Upgrade to stable
  per-trace IDs (synthetic: `<sim_id>_<electrode_pair_id>`; IAFDB:
  `<record>_<channel>_<segment_start_ms>`) when integer-index fragility proves problematic. Trigger:
  first time a re-extracted bank invalidates a saved trace-list observation painfully.
- **Provenance-graph upgrade.** The shallow-index manifest can upgrade to a full graph (typed nodes
  + edges) if query needs grow. Trigger: first time a query like "everything downstream of artifact
  X" requires custom traversal code that essentially rebuilds the graph at read time.
- **Hugging Face Datasets for bank distribution.** Trigger: at least two people actively producing
  banks that need to flow between them.
- **Zenodo for paper-archival data.** Trigger: first actual paper publication.
- **After-write validation hook in egm-studio.** Re-run the scan-and-validate check after each
  in-app manifest write. Trigger: manual curation drift getting tedious.
- **Auto-fix scan-and-validate.** Currently reports; user fixes by hand. Trigger: a pattern of
  routine drift that hand-fixing gets tedious.
- **Multi-version artifacts.** Today's design assumes one entry per (artifact, phase); the `_v1`,
  `_v2` iteration suffix covers same-phase re-runs informally. A formal versioning scheme would
  need more thought.
