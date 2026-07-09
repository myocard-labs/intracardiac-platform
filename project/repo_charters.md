# Repo charters — what code lives where, and why

The single source of truth for the division of labor across the myocard-labs repos. When you're
about to write something and aren't sure which repo it belongs in, this document decides. When a
new repo is proposed, it earns a charter here or it doesn't get created.

Two companion docs: [`project_plan.md`](project_plan.md) holds the dependency DAG + phase roadmap;
[`cross_artifact_linkage_design.md`](cross_artifact_linkage_design.md) holds the design for how
data moves between these repos.

## Why polyrepo (not a monorepo)

Each component is its own GitHub repo, independently versioned and released. The monorepo
"operationally simpler for a solo dev" argument is real and was explicitly overridden, because the
polyrepo shape buys things that matter more here:

- **The medical-device narrative.** Per-component change control, independent version history, and
  a clean V&V/audit trail per module mirror how regulated (ISO 62304-style) software is
  structured. That's the story this project exists to tell.
- **A slowly-changing interface boundary.** `egm-contracts` changes rarely and deliberately;
  everything else can churn behind it without breaking consumers.
- **Context partitioning.** One repo is a tractable amount of context for a single work session
  (human or AI chat) — see [`chat_charters.md`](chat_charters.md).

## Naming conventions

| Thing | Form | Example |
|---|---|---|
| GitHub repo | bare name | `egm-contracts`, `egm-studio` |
| PyPI distribution | `myocard-` prefix | `myocard-egm-contracts` |
| Python import | underscored, `myocard_` prefix | `import myocard_egm_contracts` |
| Project-scoped repo (not a package) | `intracardiac-` prefix | `intracardiac-platform`, `intracardiac-papers` |

## The repos

### Foundation — shared libraries, `torch`-free

- **`egm-contracts`** — the data-contract layer. JSON Schema (Draft 2020-12) is the source of
  truth for every format that crosses a repo boundary; Pydantic models are codegen'd from it (C++
  structs stubbed for future TensorRT work). Also owns the stable `ArtifactId` / `FigureId` /
  `PaperId` patterns. *Does not* contain business logic, I/O, or numerics — only schemas, generated
  models, and their validators.
- **`egm-data`** — artifact I/O. Polymorphic readers + writers for every contracts-defined format
  (banks, run records, phase-index files); every reader returns a typed contracts model, every
  writer takes one. *Does not* contain DSP, features, or the training-data layer (that moved to
  egm-classifier in Refactor Step 8) — it is pure, `torch`-free I/O.
- **`egm-signal`** — reusable DSP primitives: band/low/high-pass filters, R-wave-anchored
  calibration, threshold-based segmentation, temperature scaling. numpy/scipy only. *Does not* know
  about banks or artifacts — it operates on arrays.
- **`egm-features`** — per-trace feature extraction (time-domain morphology, spectral, complexity).
  numpy/scipy/pandas/antropy. A standalone signal-analysis library; *does not* depend on the other
  siblings and *does not* do I/O.

### Producers — write banks

- **`iafdb-pipeline`** — the PhysioNet IAFDB producer: download → calibrate → segment → export
  `iafdb_bank` / ClassifierBank / noise bank. Consumes contracts + data + signal.
- **`synthetic-egm-pipeline`** — the Finitewave simulator + noise mixer: simulate → label → mix →
  export the labeled (and noise-mixed) ClassifierBank. Consumes contracts + data + signal.

### Consumers — read banks

- **`egm-classifier`** — the 1D MobileViT model: `egm-class-train` / `-eval` / `-export`, plus the
  **training-data layer** (`EGMTraceDataset`, patient-aware splits, `TraceTransform` augmentation).
  The only repo that depends on `torch`. Consumes contracts + data + signal.
- **`egm-studio`** — the desktop GUI (`egm-studio`) + headless figure renderer
  (`egm-studio-render`): signal exploration, ML diagnostics, paper-figure prep, noise browsing, and
  phase curation. Consumes contracts + data + features.

### Meta — not Python packages

- **`intracardiac-platform`** — this repo: cross-cutting `project/` docs, the `phases/` artifact
  index, workspace `scripts/`, `integration/` smoke tests, and the `references/` reading index.
- **`intracardiac-papers`** — the LaTeX papers (`papers/<slug>/`).

## Placement decision guide

When you're about to add something, find the row:

| I'm adding… | It goes in… | Because |
|---|---|---|
| A new data format that crosses a repo boundary | **egm-contracts** (JSON Schema → codegen models) | contracts is the interface boundary; both sides share the generated model |
| A reader/writer for an on-disk artifact | **egm-data** | data owns all artifact I/O |
| A reusable DSP primitive (filter, calibration, segmentation, activation detection) | **egm-signal** | shared signal math, torch-free, no bank awareness |
| A per-trace feature (morphology / spectral / complexity) | **egm-features** | the feature library |
| Model architecture / training / eval / ONNX export | **egm-classifier** | the ML consumer |
| A **train-time, per-call** augmentation | **egm-classifier** (`.data` augmentation) | per-call train-time transforms live with the trainer |
| **Static, once-per-dataset** preprocessing/curation | the **producer** that writes the bank | curation belongs at production time, not train time |
| A new figure recipe, GUI view, or analysis visualization | **egm-studio** | the visualization consumer |
| IAFDB acquisition / calibration / bank export | **iafdb-pipeline** | the real-data producer |
| Simulator / substrate / electrode / mixer logic | **synthetic-egm-pipeline** | the synthetic producer |
| A cross-repo integration test | **intracardiac-platform/integration** | the only place every repo installs side by side |
| A cross-cutting design, process, or phase doc | **intracardiac-platform/project** (or a phase folder) | the meta repo |

If a thing doesn't fit any row, it does **not** get a new shared "utils" repo — put it in the most
purposeful existing repo (usually egm-data or egm-signal) or keep it local to the one consumer that
needs it. Common-utils repos become dumping grounds.

## Cross-cutting rules

These hold regardless of which repo you're in:

- **Typed contracts at every boundary.** Every cross-module handoff is a typed egm-contracts
  Pydantic model — never a loose dict or a mirror dataclass. The "avoid the dependency" argument
  doesn't apply: contracts is already a transitive dependency everywhere.
- **Libraries ship no policy defaults.** Foundation packages expose parameters with no hardcoded
  policy values; defaults live in the JSON Schemas or in the executable-level consumer's config
  (e.g. egm-classifier's training config), not baked into a library.
- **Foundation stays `torch`-free.** contracts / data / signal / features must import cleanly
  without torch; torch lives only in egm-classifier. This keeps producer + CI images light.
- **Augmentation vs. preprocessing.** A transform applied per-call during training is augmentation
  (egm-classifier); a transform applied once when a bank is written is preprocessing/curation
  (the producer). Don't blur the two.
- **Producers don't touch the phase manifest.** They stamp stable IDs into the artifacts they
  write; egm-studio curates the manifest; the validator is the safety net (see
  [`cross_artifact_linkage_design.md`](cross_artifact_linkage_design.md)).

## Adding or splitting a repo

A new repo needs: a one-line charter (what it owns), an explicit "does not contain" boundary, its
place in the dependency DAG, and its naming per the table above. Add it here and to
`project_plan.md`'s DAG before creating it. Prefer extending an existing repo's charter over
spawning a new repo; new repos are for genuinely distinct responsibilities, not for code that's
merely awkward to place.
