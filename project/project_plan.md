# Intracardiac Catheter Software — Project Plan

> Note: the on-disk workspace folder is still spelled `Intercardiac Catheter Software/`
> (a legacy typo). The correct clinical term is **intracardiac** ("within the heart")
> and that's what's used in all forward-looking prose, repo names
> (`intracardiac-platform`, `intracardiac-papers`), and PyPI distributions
> (`myocard-*`). See the `terminology-intracardiac` memory for the
> fix-on-contact rule. The workspace folder will be renamed in Phase 8
> (refactor cleanup); changing it sooner breaks too many shell histories
> + bookmarks.

**Status:** living document. This is the project-truth view of the whole system. Per-component design rationale lives in each component repo's `project/architecture.md`; per-component planned work lives in each repo's `project/roadmap.md`; this file is the canonical cross-cutting view that ties the per-repo plans together into the phased project roadmap.

**Last updated:** 2026-07-08 (Refactor Step 8 — platform cleanup pass).

---

## Vision

An AI/signal-processing portfolio piece demonstrating transferable skills from aerospace/defense (radar, SAR, IR, hyperspectral) into the medical device industry. Concretely: identify fibrotic atrial tissue from intracardiac electrograms (EGMs) to support catheter ablation site selection for atrial fibrillation (AFIB) treatment.

End deliverables: a sequence of white papers (see [[project-intracardiac-papers-plural]]) describing methodology, the label-free IAFDB sim-to-real sanity check (a directional baseline, not scored validation — true validation would need labeled real data), multi-class severity classification, and honest limitations.

---

## Four components (from kickoff design)

1. **Synthetic data generation** — Finitewave-based simulator producing labeled intracardiac EGMs from 2D atrial tissue models with varying fibrosis density. Output: HDF5 banks of `(trace, label, simulation_id)` records. Shipped as `myocard-synthetic-egm-pipeline`.
2. **ML model** — 1D adaptation of MobileViT for per-trace fibrosis classification. Binary first (shipped), multi-class severity / pattern / functional in later phases. Shipped as `myocard-egm-classifier`.
3. **Optimized deployment** — C++ + TensorRT for hardware-accelerated inference. Phase 1 ONNX export pipeline shipped (with baked-in temperature calibration); TensorRT/C++ deferred until post-paper.
4. **Evaluation + white papers** — Sim-to-real sanity check on PhysioNet IAFDB — a label-free directional baseline, not scored validation (Phase 1 result characterized; v1 saturates and labels nearly everything fibrotic, the "clearly wrong" baseline a richer synthetic side should move away from); calibration analysis; limitations write-up. Paper repo to be created as `intracardiac-papers`.

---

## Reference works

The papers most actively shaping current decisions. The full annotated bibliography lives in [`references/README.md`](../references/README.md); CNN-architecture reading progress is tracked in `project/architecture_reading_list.md`.

- **Sánchez J et al. 2021** — *Using Machine Learning to Characterize Atrial Fibrotic Substrate From Intracardiac Signals With a Hybrid in silico and in vivo Dataset.* Frontiers in Physiology, doi 10.3389/fphys.2021.699291. The paper this project is replicating and extending.
- **Mehta S, Rastegari M. 2022** — *MobileViT.* ICLR 2022, arxiv 2110.02178. The 2D architecture from which the `egm-classifier` 1D model is adapted.
- **Marchlinski FE et al. 2000** + **Sanders P et al. 2003** + **Kosiuk J et al. PMID 30873619** + **Yamaguchi T et al. 2025 (PMID 41035701)** — clinical voltage-threshold literature feeding the bipolar-amplitude thresholds used in IAFDB preprocessing.
- **Guo C et al. 2017** — *On Calibration of Modern Neural Networks.* ICML 2017, arxiv 1706.04599. Framing for the BCE overconfidence observed in v1_baseline, and the post-hoc temperature-scaling method used in the egm-classifier export CLI.
- **Okenov et al. 2024 (PLOS ONE)** — closest published analog to the Finitewave-based synthetic Phase-1 design. Citation in `synthetic-egm-pipeline/docs/simulation_theory.md`.

---

## Workspace layout

The on-disk workspace folder (`Intercardiac Catheter Software/`) is the OS-level container — **not a git repo**. Each subfolder is either its own git repo (the polyrepo target) or staging for one. Current state on disk (2026-07-08):

```
Intercardiac Catheter Software/                  ← workspace folder, NOT a git repo
│
├── intracardiac-platform/                       ← meta repo, → myocard-labs/intracardiac-platform
│   ├── project/                                 ← internal: plan + design + process + investigations + reading list
│   │   ├── project_plan.md                      ← this file
│   │   ├── cross_artifact_linkage_design.md     ← phase-index design
│   │   ├── architecture_reading_list.md
│   │   ├── investigations/                      ← v1_baseline / v1_5 / v1_iafdb investigation notes
│   │   └── README.md
│   ├── docs/                                    ← external user-facing: quick_start · walkthrough · README
│   ├── phases/                                  ← cross-artifact phase index (one manifest per science phase)
│   ├── scripts/                                 ← workspace tooling (clone_repos · run_fast_tests · validate_manifest)
│   ├── integration/                             ← cross-repo smoke tests
│   ├── references/                              ← reference literature: PDFs gitignored, README.md tracked
│   └── README.md, LICENSE, NOTICE, .gitignore
│
├── prompts/                                     ← per-chat handoff briefs (untracked; not part of any repo)
├── python-template/                             ← library template, → myocard-labs/python-template
│
│   --- Shipped polyrepo components (each → myocard-labs/<name>, dist myocard-<name>) ---
├── egm-contracts/                               ← foundation: JSON-Schema-first contracts + codegen'd models
├── egm-data/                                    ← foundation: bank / artifact / phase I/O
├── egm-signal/                                  ← foundation: pure DSP primitives
├── egm-features/                                ← foundation: per-trace feature extractors
├── iafdb-pipeline/                              ← producer: PhysioNet IAFDB
├── synthetic-egm-pipeline/                      ← producer: Finitewave simulator + noise mixer
├── egm-classifier/                              ← consumer: 1D MobileViT train/eval/export (+ the dataset/split/augment layer)
├── egm-studio/                                  ← consumer: PySide6 GUI + egm-studio-render CLI
├── intracardiac-papers/                         ← LaTeX papers (plural; papers/<slug>/)
│
│   --- Pre-refactor `*_old/` folders — read-only, archival pending (Refactor Step 8) ---
├── egm_viewer_old/, egm_metrics_viewer_old/     ← superseded by egm-studio
├── egm_classifier_old/, iafdb_pipeline_old/, synthetic_egm_pipeline_old/, python-template_old/
│
│   --- Companion learning project — being relocated OUT of the workspace (not a myocard-labs repo) ---
└── mobilevit_imagenette/
```

Versions are deliberately not pinned in this tree — they only go stale. Each repo's current release is in its own `CHANGELOG.md`, and the live cross-repo pin set is in each consumer's `pyproject.toml`. (Untracked run/review clutter — a `banks/` data folder, review screenshots — also sits at the workspace root and belongs to no repo.)

**Note on the `*_old/` folders:** the original underscore-named folders (`egm_viewer/`, `egm_classifier/`, …) are superseded by their dash-named GitHub siblings and linger only as `_old` archives, slated for deletion in Refactor Step 8.

**Note on `references/`:** the reference-paper PDFs are local-only (gitignored); the annotated index (`references/README.md`) is tracked. See it for what each paper is and why it matters.

---

## Polyrepo refactor status

The polyrepo refactor is **complete**. As of 2026-07-08:

| Step | Scope | Status |
|---|---|---|
| 0 | Pre-flight (org `myocard-labs`, license, python-template) | ✅ done |
| 1 | `intracardiac-platform` meta repo + `egm-contracts` (JSON-Schema-first) | ✅ done |
| 2 | `egm-data` (bank / artifact / phase I/O) | ✅ done |
| 3 | Producers (`iafdb-pipeline`, `synthetic-egm-pipeline`) | ✅ done |
| 3.5 | `egm-signal` (pure DSP primitives, extracted mid-refactor) | ✅ done |
| 4 | `egm-features` (morphology + spectral + complexity feature extractors) | ✅ done |
| 5 | `egm-classifier` (1D MobileViT + train/eval/ONNX-export CLIs + the dataset/split/augment layer) | ✅ done |
| 6 | `egm-studio` (GUI + `egm-studio-render` CLI) | ✅ done (tagged 2026-07-07) |
| 7 | `intracardiac-papers` (LaTeX, multi-paper layout) | ✅ done (scaffolded 2026-07-07) |
| 8 | Cleanup + verification (Dependabot, integration smoke, docs professionalization, workspace archive) | ✅ done |

**Refactor complete.** All eight steps have shipped. Step 8 delivered the changelog/roadmap scheme, the theory-doc retrofits, the IAFDB sanity-check scrub, the integration smoke test, Dependabot alerts, the professionalized platform docs, and the multi-chat process docs + spin-up prompts. The only mechanical acts left are the one-time `intracardiac-platform` commit and the workspace-folder rename (Intercardiac → Intracardiac Software).

**Cross-repo dependency DAG (current state):**

```
egm-contracts                         (root — no project deps)
       ↑
egm-data · egm-signal · egm-features  (foundation — I/O · DSP · feature extraction)
       ↑
   ┌───────────────┬──────────────────────┬──────────────────┐
iafdb-pipeline   synthetic-egm-pipeline   egm-classifier     egm-studio
(producer)       (producer)               (consumer)         (consumer: contracts + data + features)
```

---

## Component status

Per-repo summary of what's shipped and where to look for more detail. For per-repo plans see each repo's `project/roadmap.md`; for per-repo design see `project/architecture.md`. Current versions live in each repo's `CHANGELOG.md`, not here.

### `egm-contracts` — schemas + validators

JSON Schema (Draft 2020-12) source of truth for every cross-component data format; Pydantic models codegen'd via `datamodel-code-generator`; C++ struct codegen path stubbed for the future TensorRT deployment work. Ships the bank/record schemas (`synthetic_bank`, `iafdb_bank`, `noise_bank`, `classifier_bank`, `classifier_run_record`, `epoch_record`, `held_out_test_metrics`, `noise_bank_run_record`, `egm_class_model_metadata`), the cross-artifact phase-index schemas (`phase_manifest`, `observation`, `figure_spec`), and the stable `ArtifactId` pattern the phase index keys on.

### `egm-data` — bank / artifact / phase I/O

Polymorphic readers + writers for every contracts-defined format — banks, run records, and the phase-index files. Every reader returns typed contracts Pydantic models; every writer takes them. Pure, torch-free I/O: the PyTorch `Dataset` wrappers (`EGMTraceDataset`), patient-aware splits, and `TraceTransform` augmentation that used to live here moved into egm-classifier's `.data` layer during Refactor Step 8.

### `egm-signal` — pure DSP primitives

Extracted from iafdb-pipeline during Phase 3.5 to stop duplicating filter + calibration code across producers + consumers. Ships: bandpass / lowpass / highpass wrappers around scipy, R-wave anchoring calibration, threshold-based segmentation helpers, and `temperature_scaling` (Guo et al. 2017 NLL fit) used by egm-classifier's export CLI.

### `iafdb-pipeline` — PhysioNet IAFDB producer

PhysioNet download with hash-verified integrity, R-wave-anchored calibration, healthy-segment extraction with three threshold modes (Sánchez 0.5 mV / Kosiuk AF-adjusted 0.2 mV / per-record percentile). `iafdb-export-bank` produces a versioned `iafdb_bank.h5` (plus an optional labeled/unlabeled ClassifierBank); `iafdb-export-noise-bank` produces the noise bank that `synthetic-egm-pipeline`'s mixer consumes for additive realistic noise on simulated traces.

### `synthetic-egm-pipeline` — Finitewave-driven simulator

Aliev-Panfilov on a 2 mm-anisotropic 4 cm square patch with uniform-random fibrosis substrate; bipolar EGMs through a centered 5×5 electrode grid (20 bipolar pairs per simulation); labels per `LabelPolicy` (global density or local density around the pair). The mixer overlays IAFDB-derived noise at a target SNR distribution to produce the noise-mixed training bank.

### `egm-classifier` — 1D MobileViT binary classifier

Three CLIs: `egm-class-train` (training with patient-aware splits + AUROC-selected best-checkpoint saving), `egm-class-eval` (sequential inference + sibling predictions bank + scalar metric bundle), `egm-class-export` (optional temperature-scaling fit + ONNX export with `T` baked into the graph + typed `egm_class_model_metadata.json` sidecar for C++ deployment). Also hosts the training-data layer — `EGMTraceDataset`, patient-aware splits, and `TraceTransform` — moved here from egm-data in Refactor Step 8.

Phase 1 result, [`investigations/v1_iafdb_investigation.md`](investigations/v1_iafdb_investigation.md): val AUROC = 0.999 (in-distribution); IAFDB mixed AUROC = 0.767; IAFDB-only mean P(fibrotic) = 0.999 — the model labels ~99.98% of real healthy segments fibrotic at ~0.999 confidence. The decision function is **saturated** on real data → no usable threshold from temperature scaling alone; this needs a training-distribution fix, not recalibration. Phase 1 viability decision: pursue WITH synthetic-side iteration (Phase 1.5).

### Refactor Phase 4 / 6 / 7 repos

- **`egm-features`** (Phase 4, ✅ done) — NumPy/SciPy feature extractors (time_domain, frequency, complexity, bundle.extract_all). Source material: the chat-based feature analysis from the v1_baseline diagnostic. See [[project-egm-features-scope]].
- **`egm-studio`** (Phase 6, ✅ done) — PySide6 GUI built ground-up (four modes: signal exploration · ML diagnostics · paper-figure prep · noise), plus the `egm-studio-render` CLI for reproducible paper figures. Owns the visual-interpretation half of the docs split (its own `docs/theory.md`; the math half lives in egm-classifier `docs/theory.md`).
- **`intracardiac-papers`** (Phase 7, ✅ scaffolded) — LaTeX, plural per [[project-intracardiac-papers-plural]], `papers/<paper-slug>/` layout. No PyPI publish here — paper repo is the publishing milestone for everything (see [[project-publishing-timing]]).

---

## Phased roadmap (project-level)

Phases below describe the *project-level* phasing — they span work across multiple repos. Per-repo task-level work lives in each repo's `project/roadmap.md`; the **roadmap audit step** scheduled after this rewrite will go through each of those roadmaps and either pull cross-cutting items up into the phases below, or leave them as component-internal tech debt.

| Phase | Theme | Status |
|---|---|---|
| 1 | Binary per-trace fibrotic detection + IAFDB sim-to-real characterization | ✅ done — v0.1.0 shipped 2026-06-23; saturation diagnosed |
| 1.5 | Increase synthetic-data complexity + realism | ⏳ current — design pending (task #292) |
| 2 | Multi-class severity (healthy / border zone / dense scar — Marchlinski tiers) | ⏳ not started — **leaning toward first-publish milestone** per [[project-publishing-timing]] |
| 3 | Pattern classification (interstitial / patchy / compact fibrosis) | ⏳ not started |
| 4 | Multi-beat sequence classification (move beyond single-activation traces) | ⏳ not started |
| 5 | CLOCS-style self-supervised pretraining on unlabeled IAFDB segments | ⏳ not started |
| 6 | TensorRT deployment optimization (C++ runtime against the ONNX + metadata sidecar already shipped) | ⏳ not started |
| 7 | 3D substrate geometry (move beyond the 2D atrial patch) | ⏳ not started — requires simulator backend swap (Finitewave 2D-only → TorchCor / openCARP for 3D) |
| 8 | 3D catheter modeling for realistic electrode placement in the 3D substrate | ⏳ not started — depends on Phase 7 |

**The phase list is open-ended.** As we proceed through phases we'll discover more interesting topics to investigate; the table above will keep growing. Phases 7 and 8 in particular are the result of looking at the v1 saturation result and thinking through what makes the simulated data fundamentally more realistic — and similar additions will surface as we work through subsequent phases.

**Each phase begins with a high-level design / planning discussion** that fully enumerates which repos need changes and what those changes are. The roadmap-audit pass scheduled after this rewrite will *seed* the per-phase task lists below from the existing per-repo `project/roadmap.md` files, but it's not exhaustive — the kickoff discussion at the start of each phase will fill in additional work that wasn't on any roadmap yet.

Note on numbering: these are **project-level (science / scope) phases**, distinct from the **refactor-level steps** recorded in the "Polyrepo refactor status" section above (now complete). The two number lines run independently — "Phase 8" in this file means 3D catheter modeling, whereas "Refactor Step 8" meant cleanup + verification. When ambiguous, qualify with "Project Phase X" vs "Refactor Step X."

### Phase 1.5 — increase synthetic-data complexity + realism (current)

The v1 IAFDB result was *suggestive* — the model saturates its decision function on real data, which tells us the synthetic distribution is too easy. Phase 1.5 is the focused work to push the simulated data closer to physical reality before moving on to Phase 2.

**Important framing note:** this is NOT "close the sim-to-real gap" in the strict sense, because we don't have an accurately-labeled IAFDB set to evaluate against. IAFDB is healthy + AF recordings without ground-truth fibrosis labels, so we can't compute IAFDB AUROC against a true label. What we can do is:

- Make the synthetic data richer and more physical (the "input side" of the gap).
- Compare synthetic feature distributions to IAFDB feature distributions and tune the synthetic side to match (the "distribution check" — needs `egm-features` from Phase 4 of refactor).
- Iterate the synthetic generator informed by what features the v1 classifier looks at.

Closing the saturation result is the *expected outcome* of doing the synthetic-side work well, but it's not the eval metric we steer on — there's no labeled IAFDB to compute that on.

**Cross-cutting initiatives we know about today** (seed list — the roadmap audit will add more, and the Phase 1.5 kickoff design conversation will add still more):

- **Synthetic v2** — tighten density floor, narrow electrode height range, tighten SNR range, increase simulation count.
- **Sim-realism feature comparison** — once `egm-features` ships, compare synthetic vs IAFDB feature distributions and tune sim parameters to close per-feature gaps.
- **Activation-peak anchoring investigation** — make producer-side anchoring an opt-in flag in synthetic-egm-pipeline; A/B test; possible methods-paper candidate.
- **Additive-noise augmentation literature survey** — survey synthetic-EGM ML literature; A/B test if encouraging.
- **Per-pair labeling via `LocalDensityLabel`** — switch the v1 synthetic training from `GlobalDensityLabel` to `LocalDensityLabel` (already implemented in synthetic-egm-pipeline v0.2.0). Per-pair labels reflect what each bipolar pair actually sees rather than the substrate's global density, which should mostly resolve the class-overlap problem at the global-density boundary without losing training samples. Lowest-cost experiment for the v1_baseline diagnostic's headline finding.
- **Training-side label-noise revisions (v1.5b fallback)** — only if `LocalDensityLabel` doesn't resolve the class overlap: drop low-density traces entirely (rather than relabeling) for a cleaner test of the class-overlap hypothesis. See `v1_5_investigation.md`. These two are alternatives, not both — run the local-density experiment first since it's cheaper.
- **Items currently listed as "further out" in `synthetic-egm-pipeline/project/roadmap.md`** that the audit pulled forward into Phase 1.5 (see seeded list below).

#### Seeded tasks from the roadmap audit (2026-06-23)

The Phase 1.5 kickoff discussion will add to this list — these are only the items that already had a home in some per-repo roadmap and got promoted here. Tagged by source repo so the per-repo chats know which item is theirs.

- **egm-classifier:** `zero2one` normalization in train + eval (matching the schema's per-trace normalization options).
- **egm-classifier + synthetic-egm-pipeline:** activation-peak anchoring investigation — opt-in flag in synthetic-egm-pipeline, A/B compare in egm-classifier (tracks task #293).
- **egm-classifier:** training-time additive-noise augmentation literature survey + A/B test (tracks task #294).
- **synthetic-egm-pipeline:** swap cell model from Aliev-Panfilov to Courtemanche 1998 (human atrial ionic model). Was labelled "Phase 2 — Courtemanche" in the synthetic roadmap; promoted here.
- **synthetic-egm-pipeline:** pluggable noise-selection strategy (`PerSimPatientNoiseSelection`, `PerSimRecordNoiseSelection`, etc.) — preserves cross-pair noise correlation that real recordings have.
- **synthetic-egm-pipeline:** additional activation sources (`PointStimulus`, `S1S2Protocol` — non-multi-beat variety; `PacingTrain` is Phase 4 territory).
- **synthetic-egm-pipeline:** multi-edge stimulation. Sanchez 2021 stimulated from three different sides (left border, bottom border, top-right corner) to capture propagation-direction sensitivity; our v1 `PlanarEdgeStimulus` only stimulates from a single edge. Surfaced by the multi-beat research pass (2026-06-23); cheap realism upgrade. See [[reference-multi-beat-consensus]].
- **egm-signal:** `extraction.activation_based` primitive — enables proper segment-around-activation extraction for the anchoring investigation.
- **egm-signal:** `filters.decimation` — anti-alias + downsample primitive that pairs with the classifier's run.json downsample policy work.
- **iafdb-pipeline:** `patient-id-as-label` label policy — shortcut-hunt diagnostic for Phase 1.5 work.
- **iafdb-pipeline:** per-record audit reports (`--report PATH` JSON sidecar) — diagnostic data for per-record outlier hunts during the synthetic-vs-IAFDB feature comparison.
- **cross-cutting:** sim-realism feature comparison — compare synthetic vs IAFDB feature distributions using `egm-features` (gated on Refactor Step 4 shipping first).

### Phase 2 — multi-class severity (leaning toward first-publish milestone)

Marchlinski tiers (healthy / border zone / dense scar). The model constructor already supports `num_classes ≥ 2` and the loss switches to cross-entropy automatically; the training + eval CLIs need to grow the multi-class metric path; the export CLI needs to stop rejecting multi-class checkpoints. The synthetic side needs a `FibroticTypeLabel` policy that produces three-class labels.

**Publish milestone:** per [[project-publishing-timing]], the leaning is that Phase 2's outcome triggers the first PyPI + HuggingFace publish burst + first paper, since Phase 1.5 results are expected to still be underwhelming and a multi-class story is a stronger first-impression. If Phase 1.5 lands an unexpectedly strong result, the publish milestone shifts earlier; if Phase 2 also disappoints, it shifts to whatever the next reasonable inflection is.

#### Seeded tasks from the roadmap audit (2026-06-23)

- **synthetic-egm-pipeline:** `FibroticTypeLabel` label policy — produces multi-class labels from the substrate.
- **egm-classifier:** multi-class metric path through train / eval / export CLIs — model constructor already supports `num_classes ≥ 2` with cross-entropy auto-switch, but the CLI plumbing assumes binary today.
- **cross-cutting (egm-contracts + egm-data + synthetic-egm-pipeline):** coordinated schema bump to v0.3.0 across the three repos for the polymorphic `stimulation` object replacing today's `stim_edge` (needed for `S1S2Protocol` etc., but bundled here for the Phase 2 release).

The Phase 2 kickoff discussion will add the multi-class reporting, plot, and ONNX export work that isn't on any roadmap yet.

### Phase 3 — pattern classification

Interstitial / patchy / compact fibrosis substrate types. Needs `FibrosisTypeLabel` on the synthetic side (different generation paths for each substrate type) and a multi-output head on the classifier side (severity + pattern as joint outputs, or two parallel heads).

#### Seeded tasks from the roadmap audit (2026-06-23)

- **synthetic-egm-pipeline:** additional substrate strategies — `InterstitialFibrosis` (banded patterns between myocyte bundles), `PatchyFibrosis` (discrete fibrotic islands), `CompactFibrosis` (solid scar regions), `HeterogeneousMix` (compose multiple).
- **synthetic-egm-pipeline:** `NeighborhoodCompositionLabel` — fractional composition per fibrosis type around the bipolar pair, then thresholded. Needs the multi-type substrate (so depends on the four above).

The Phase 3 kickoff discussion will add the classifier-side multi-output head work + any cross-cutting data-format extensions needed.

### Phase 4 — multi-beat sequence classification

Move beyond single-activation traces — longer windows that span multiple activations crossing the electrode pair. Activation-peak anchoring stops applying (see egm-classifier `docs/theory.md` §1.3). May require a different backbone (e.g., a true sequence model) or just longer `T` with the current MobileViT.

**Why Phase 4 and not Phase 2/3:** the directly-comparable substrate-characterization literature (Sanchez 2021, our reference paper) uses per-activation features with multi-pulse simulation only for *tissue settling* — the classifier itself sees single-activation input. Multi-beat sequence models are the standard for rhythm classification (AT vs AF vs sinus) but aren't documented as load-bearing for fibrosis-substrate work. See [[reference-multi-beat-consensus]] for the full lit review. Phase 4 may pull forward incidentally if Phase 1.5 synthetic-realism work introduces multi-activation simulations; promoting it deliberately would put us ahead of where the substrate-classification literature is.

#### Seeded tasks from the roadmap audit (2026-06-23)

- **egm-signal:** `extraction.multi_beat` primitive — N-consecutive-beat extraction units aligned on QRS annotations. Shared primitive; both Phase 4 (synthetic side, via PacingTrain) and Phase 5 (IAFDB side, via CLOCS) consume it.
- **synthetic-egm-pipeline:** `PacingTrain(period_ms, n_beats)` activation source — synthetic steady-state pacing protocol.

The Phase 4 kickoff discussion will add the classifier-side sequence-model decisions (longer-T MobileViT vs swap in a true sequence model) + data-format work for variable-length traces if needed.

**Note:** iafdb-pipeline does NOT need multi-beat extraction wired in for Phase 4 — IAFDB has no fibrosis ground truth (see [[project-iafdb-eval-catch22]]) so it can't be a labeled train/test source for Phase 4 classification. The iafdb-pipeline multi-beat extraction work belongs in Phase 5 (CLOCS pretraining), where it's the data source for adjacent-segment self-supervised learning.

### Phase 5 — CLOCS-style self-supervised pretraining

Pretrain on unlabeled IAFDB segments before fine-tuning on labeled synthetic. Per the Phase 1 result, this might be the unlock for closing the sim-to-real gap on tasks the synthetic side can't realistically cover.

#### Seeded tasks from the roadmap audit (2026-06-23)

- **iafdb-pipeline:** wire `egm-signal`'s `extraction.multi_beat` primitive into a new IAFDB export path that emits adjacent-segment pairs (the data format CLOCS needs). egm-signal's primitive ships earlier in Phase 4 (the synthetic-side multi-beat work uses it first); iafdb-pipeline consumes it here.

The Phase 5 kickoff discussion will add the CLOCS-side adjacent-segment loss implementation in egm-classifier + design decisions about how the pretrained backbone fine-tunes onto labeled synthetic data (Phase 2/3/4 classifiers).

### Phase 6 — TensorRT deployment

C++ runtime + TensorRT optimization against the ONNX + metadata sidecar already shipped from Phase 1. Held until at least one paper-publish phase validates the classifier is worth deploying. The contracts repo's C++ codegen stub gets filled in here.

**Tasks: populated by roadmap audit if relevant items exist yet.**

### Phase 7 — 3D substrate geometry

Move beyond the 2D atrial patch. The Finitewave-driven Phase-1 design uses a 4 cm × 4 cm 2D anisotropic patch with uniform-random fibrosis; physical atrial tissue is 3D, with anatomically curved walls, varying thickness, and substrate heterogeneity in three dimensions. Phase 7 brings the synthetic geometry up to that complexity.

**Major implication:** simulator backend switch. Finitewave is a 2D finite-difference solver — it doesn't handle 3D unstructured atrial meshes. The simulator-backend evaluation (see [[simulator-backend-evaluation]]) anticipated this by sketching the swap path: Finitewave first (laptop-runnable, Phase 1), TorchCor later (GPU-accelerated, handles 3D), openCARP skipped. Phase 7 is where the swap actually happens.

The synthetic-egm-pipeline's architecture was designed to make this contained — see `synthetic-egm-pipeline/project/architecture.md` for the three guardrails that preserve the swap path. The pseudo-EGM forward calc + label policies + electrode-placement abstractions all stay; only the backend changes.

#### Seeded tasks from the roadmap audit (2026-06-23)

- **synthetic-egm-pipeline:** new `AtrialMesh3D` `GeometrySpec` carrying a `.pts/.elem/.lon` triple or equivalent unstructured-mesh reference.
- **synthetic-egm-pipeline:** new `EndocardialSurface3D` `ElectrodePlacement` strategy — electrodes sampled or projected onto the endocardial surface (Phase 8 work expands this to model the catheter geometry explicitly).
- **synthetic-egm-pipeline:** new `backends/torchcor/` subdirectory + TorchCor backend implementation. Strategy Protocols stay identical (architecture's Guardrail 2 holds); backend interface stays one `simulate()` method (Option A still in force).
- **synthetic-egm-pipeline:** compatibility validator for strategy combinations — runs at config-load time, raises clear `CompatibilityError` before the AP solver starts. Was tracked in synthetic's roadmap as "do when second geometry type lands"; this is that moment.

The Phase 7 kickoff discussion will add cross-cutting work in egm-data (3D mesh I/O if any), egm-contracts (3D geometry schema), and egm-classifier (potentially-different input shape).

### Phase 8 — 3D catheter modeling for realistic electrode placement

Once the substrate is 3D (Phase 7), the electrode placement becomes geometrically meaningful — a real catheter has a specific shape (decapolar 2-5-2 mm, spline, basket, etc.) and sits in physical contact with the substrate at specific points. Phase 8 models the catheter geometry explicitly and places electrodes on it at physical positions within the 3D substrate.

This is the synthetic-side counterpart to the IAFDB catheter geometry baked into the real-data side — IAFDB recordings already capture realistic electrode placement because they're recorded by real catheters. The Phase-1 synthetic side flattens this to "place a 5×5 electrode grid above the 2D patch," which loses the spatial sampling pattern of real recordings.

**Depends on Phase 7** — only meaningful once the substrate is 3D.

**Tasks: populated by roadmap audit if relevant items exist yet.**

---

## Cross-cutting work — current state

Items that span more than one component. Decided here once so the per-component chats don't have to re-litigate.

### Refactor Step 8 — platform cleanup + verification (complete)

The final refactor step verified the whole constellation and professionalized `intracardiac-platform`: the changelog/roadmap scheme rollout, theory-doc equation retrofits, the IAFDB sanity-check wording scrub, a cross-repo integration smoke test, Dependabot alerts, a full pass over the platform docs (README, quick_start, walkthrough, references, scripts, phases), and the multi-chat process docs (repo/chat charters, phase process, PR + release checklists, templates) with per-chat spin-up prompts. An earlier post-v0.1.0 cleanup (checklist audit, a prior `project_plan.md` rewrite, and a per-repo roadmap audit) completed on 2026-06-23. Only the one-time platform commit + the workspace-folder rename remain.

### Phase 1.5 design (next, task #292)

After the refactor cleanup lands, design what Phase 1.5 actually is in concrete per-repo terms. Inputs: this plan's Phase 1.5 description; the roadmap audit output; the activation-anchoring + additive-noise investigation tasks already on the egm-classifier roadmap.

### Earlier "Cross-cutting work — planned" items (now done)

These were planned in the original project_plan; both shipped during the refactor and now live as standard pipeline functionality:

- **IAFDB healthy-segment bank export** — shipped as `iafdb-export-bank` CLI in iafdb-pipeline; consumed by egm-classifier's label-free IAFDB diagnostic path.
- **Automated trace inspection** — shipped as the per-sample predictions bank in egm-classifier's eval CLI; the egm-viewer inspection tab (to be merged into egm-studio in Phase 6) consumes it.

---

## Key design decisions (frozen)

These were settled in early-design conversations and should be honored unless explicitly revisited.

- **Synthetic data generator: Finitewave** (not openCARP). Laptop-runnable + cleaner Python API; openCARP performance not needed for 2D patches at v1 scope.
- **ML architecture: 1D MobileViT** (CNN/transformer hybrid). Chosen for depthwise-separable + linear-bottleneck efficiency, attention for global context, TensorRT-friendly op set.
- **Binary classification head: single logit + BCEWithLogits** (not 2-logit softmax). Allows direct `sigmoid(logit) → P(fibrotic)` interpretation. Multi-logit path kept for Phase 2.
- **Patient-aware splits** on `simulation_id` (synthetic) or `patient_id` (IAFDB) for train/val/test. No substrate realization leaks between splits. Pluggable strategy (`AnyPositive` default; `BinnedDensity` for density-stratified splits).
- **Per-trace normalization** of input. v1 default is z-score (gain-invariant; learns morphology not amplitude). Schema also admits `zero2one` and `none`; train + eval CLIs currently only emit z-score, will grow zero2one support in Phase 1.5 (egm-classifier roadmap).
- **Real-data source: PhysioNet IAFDB.** Right atrium, AF rhythm, decapolar 2-5-2 mm catheter. Limitations enumerated in `iafdb-pipeline/README.md` + the Sánchez-deviation list in [[dataset-decision-iafdb]] — both must appear in the white paper limitations section.
- **Validation primary metric: AUROC** (checkpoint selection by AUROC, not accuracy or loss; threshold-free + class-imbalance-robust per egm-classifier `docs/theory.md` §5.1).
- **Post-hoc calibration: temperature scaling baked into the ONNX graph at export.** Guo et al. 2017 NLL fit against a held-out labeled calibration bank; `T` becomes a buffer in the deployed graph so the C++ runtime gets `logits / T` directly.
- **Polyrepo, not monorepo.** Each component is its own GitHub repo, independently versioned + released. See [[project-refactor-architecture]] for the full rationale (medical-device hiring narrative + regulatory-environment fit). Locked in 2026-06-12.
- **Contracts repo as the slowly-changing interface boundary.** All schemas + Pydantic models codegen'd from JSON Schema source; strict semver. See [[feedback-schemas-json-schema-first]].
- **All cross-module boundaries use typed egm-contracts Pydantic models.** No dicts, no mirror dataclasses. See [[feedback-use-contracts-at-boundaries]].
- **Library packages ship no policy defaults.** Defaults live in JSON Schemas or in executable-level consumer configs. See [[feedback-library-defaults]].
- **Branch strategy:** every repo has `development` + `release` branches; tags only on release. See [[project-branch-strategy]].
- **PR workflow:** PR open/review/merge in GitHub web UI; only local `git` commands. See [[feedback-pr-workflow]].

---

## Working preferences

(These are stable habits worth keeping consistent across the project. Future-Claude and future-Daniel: don't fight these unless there's a real reason.)

- **Sibling components written as if already on a package index.** `pip install -e ../sibling` for now; PyPI later (gated on first-paper publishing per [[project-publishing-timing]]). No requirements-dev.txt or uv.sources workarounds.
- **Internal docs live in `<repo>/project/`**; external user-facing docs live in `<repo>/docs/`. Convention applies at every level (meta repo too). See [[feedback-docs-vs-project-folders]]. The deprecated `<component>/documentation/` folder name has been swept out during the refactor.
- **Math-heavy ML concept explanations** use Bahdanau-style indexed notation + explicit shape annotations, not compressed matrix notation. See [[feedback-notation-style]].
- **Build each component standalone and readable first**; defer cross-package unification until Phase 1 proves out. See [[feedback-understand-before-refactor]].
- **Code reviews and architecture changes via diff-able files only** — large refactors get a design doc before code lands.
- **Commit format:** `[Type] Subject` + asterisk-bullet body. See [[feedback-commit-message-format]].

---

## How this project is worked on (post-refactor)

Once the polyrepo refactor is done (Refactor Step 8 complete), the project is divided across multiple Cowork chats by role rather than worked on in a single chat. Full details + failure modes are in [[project-multi-chat-structure]]; quick summary:

- **One science / research / math chat** — theory, papers, math derivations, ML architecture decisions at the conceptual level. No implementation code.
- **One project-architecture chat** — cross-cutting decisions, division of labor between repos, whether new repos are needed. Owns `intracardiac-platform/project/` docs (this file, investigations, the process docs). Acts as the memory-writer for project-wide conventions so per-repo chats see them automatically.
- **One chat per subproject repo** — deep expertise in that codebase. Owns the repo's `project/architecture.md`, `project/roadmap.md`, `docs/`, source. Defers to the architecture chat for any decision that affects more than one repo.

Memories are the cross-chat communication channel — they persist across chats so a convention written by the architecture chat is visible to every per-repo chat. This works because the multi-chat split matches Cowork's strength: per-repo chats get deep code context, the architecture chat gets the cross-cutting map.

Currently the project is still being worked on in a single chat (this one, finishing the post-v0.1.0 refactor cleanup). The multi-chat split takes effect once Refactor Step 8 is done.

---

## Cross-cutting reference index

When you want to find something:

- **CNN-architecture reading progress** → `project/architecture_reading_list.md`
- **Per-component design rationale** → `<myocard-labs/component>/project/architecture.md`
- **Per-component planned work** → `<myocard-labs/component>/project/roadmap.md`
- **Per-component user-facing docs** → `<myocard-labs/component>/docs/`
- **Per-component status / quick-start** → `<myocard-labs/component>/README.md`
- **Active diagnostics** → `project/<topic>_investigation.md` in this repo
- **Polyrepo refactor record** → the "Polyrepo refactor status" + "Refactor retrospective" sections of this file
- **PDFs of reference papers** → `references/` (this repo, gitignored)

---

## Refactor retrospective — locked-in decisions (preserved as project history)

The polyrepo refactor decisions were settled in late-conversation chats on 2026-06-12 (during waiting time on the IAFDB classifier work). Most are now executed; preserved here as the canonical record of *why* each piece exists.

- **Polyrepo, not monorepo.** Each component gets its own GitHub repo, independently versioned + released. Chosen for the medical-device hiring narrative + the regulatory-environment fit (per-component change control, ISO 62304 software safety classes, V&V audit trails). The "monorepo is operationally easier for solo developers" argument acknowledged but explicitly overridden.
- **GitHub for code hosting.** Public repos under `myocard-labs` org. Self-hosted GitLab on Raspberry Pi can mirror via cron as backup but is NOT the public face. License = MIT.
- **GitHub Actions for CI.** Per-repo: ruff + mypy + pytest + wheel-build smoke test. No training in CI. Pre-commit hooks locally.
- **HuggingFace Hub for model artifacts.** First upload gated on first-paper publishing burst per [[project-publishing-timing]].
- **`egm-contracts` as the slowly-changing interface boundary.** Owns all data-format schemas + validators. Pure-Python + numpy + h5py + pydantic + jsonschema; no torch. Strict semver.
- **`egm-data` as the shared bank-reading layer.** Depends on `egm-contracts`. Implements: bank readers + writers, record I/O, PyTorch Dataset wrappers, augmentation.
- **`egm-signal` extracted mid-refactor** for pure DSP primitives (filtering, R-wave calibration, temperature scaling). Avoids duplicating across producers + consumers.
- **Merge `egm-viewer` + `egm-metrics-viewer` into `egm-studio`** with a unified GUI + a separate reproducible figure-rendering CLI (`egm-studio-render`).
- **Separate `intracardiac-papers` repo** for the white paper(s) (plural per [[project-intracardiac-papers-plural]]). LaTeX source, all figures, and a `provenance.tex` per paper recording the pinned artifact versions each figure was built from.
- **`intracardiac-platform` meta repo** holds cross-cutting `project/` docs, the annotated references index, user-facing `docs/` (quick-start + walkthrough), the cross-artifact `phases/` index, workspace `scripts/`, and integration smoke tests. No submodules — just links to component repos.
- **Pre-1.0 semver discipline.** Every component starts at v0.x.y. Breaking change bumps minor. Move to 1.0+ when stable.
- **`pip install git+https` during iteration; PyPI when stable.** TestPyPI for publish-workflow validation; first real publish burst tied to first-paper writing (post-Phase-2 per [[project-publishing-timing]]).
- **No speculative `intracardiac-utils`.** Common-utils repos become dumping grounds. Shared code goes into a repo with a specific purpose (e.g., `egm-data` or `egm-signal`) or stays local.

The refactor is complete; this retrospective + the "Polyrepo refactor status" table above are its durable record. (The step-by-step migration checklist was retired once the refactor shipped; git history preserves it.)

---

## Open project-level questions

These need answers eventually but not blocking current work:

- **Phase 1.5 scope and ordering** — the synthetic v2 changes + the anchoring investigation + the additive-noise survey are all candidates; the order matters because some unblock others (e.g., `egm-features` needs to ship before the sim-realism feature pass). The roadmap audit step plus the Phase 1.5 design work (task #292) will settle this.
- **Phase 2 publish-burst details** — when Phase 2 numbers land, what gets published in the publishing burst? Default plan: every myocard-labs package to PyPI at its then-current version + the trained Phase-2 checkpoint to HuggingFace + the first paper to a preprint server. Open question: do we publish Phase 1 artifacts too (the v0.1.0 egm-classifier checkpoint + ONNX) for completeness, or skip those given the IAFDB saturation result is unflattering?
- **Target journal for the first paper** — Frontiers in Physiology (precedent: Sánchez 2021)? IEEE TBME? Nature Communications Medicine? Pick before paper writing starts; the LaTeX class influences figure sizing.
- **TensorRT hardware target** — should be settled before Phase 6 begins. Currently unspecified.
- **Multi-paper layout details** — naming convention for `papers/<paper-slug>/` (e.g., `papers/phase1-binary/`, `papers/phase2-multiclass/` vs date-based slugs). Decide when scaffolding `intracardiac-papers` in Phase 7.
- **Workspace folder rename timing** — `Intercardiac Catheter Software/` → `Intracardiac Catheter Software/`. Scheduled for Phase 8 cleanup; lower priority since it's cosmetic.
