# intracardiac-platform

> Meta repo for the **Intracardiac EGM Fibrosis Detection** project — a portfolio effort
> that generates synthetic and processes in-vivo intracardiac electrograms (EGMs), trains a
> 1D MobileViT (CNN + transformer) classifier to flag fibrotic atrial tissue, and packages the
> result as a deployable model to support catheter-ablation site selection for atrial
> fibrillation.

Maintained by [Daniel Klein](https://github.com/myocard-labs). The signal-processing +
deep-learning work carries over transferable skills from aerospace/defense sensing (radar,
SAR, IR, hyperspectral) into the medical-device domain.

---

## What this repo is

This is the **meta repo**. It holds no Python source of its own — the packages live in the
component repos [below](#component-repos). It carries the cross-cutting material that has no
single component home:

- **`project/`** — internal project truth (design + planning, not user-facing):
  [`project_plan.md`](project/project_plan.md) (canonical scope, status, and phased roadmap),
  [`repo_charters.md`](project/repo_charters.md) (what code lives where),
  [`cross_artifact_linkage_design.md`](project/cross_artifact_linkage_design.md) (the design behind
  the phase index), the process docs (`chat_charters.md`, `phase_process.md`, the PR + release
  checklists, and `templates/`), `architecture_reading_list.md`, and `investigations/` (the `v1_*`
  diagnostic reports that drove each round of work).
- **`phases/`** — the project's **cross-artifact reproducibility index**: one folder per
  science phase recording every artifact it produced (banks, runs, models, observations,
  figures, papers) and how they relate. See [`phases/README.md`](phases/README.md);
  `phases/phase_1_5_example/` is a committed template.
- **`docs/`** — user-facing documentation: a [quick start](docs/quick_start.md) (clone,
  prerequisites, virtual-environments, install + verify each repo — with User and Developer
  tracks) and the whole-project [walkthrough](docs/walkthrough.md).
- **`integration/`** — cross-repo smoke tests: the single canonical "does the whole pipeline
  still install and run together?" answer.
- **`scripts/`** — repo tooling; chiefly `validate_manifest.py`, the safety net for the phase
  index. See [`scripts/README.md`](scripts/README.md).
- **`references/`** — a committed [reading index](references/README.md) of the literature the
  project draws on. The PDFs themselves are local-only (not committed).

---

## Component repos

Every component is its own released repo (bare GitHub name; `myocard-`-prefixed PyPI dist;
underscored import). The whole constellation installs and runs end-to-end (verified by the
integration smoke test).

**Foundation** — shared libraries with no CLI of their own; the producers and consumers build
on them.

- [`egm-contracts`](https://github.com/myocard-labs/egm-contracts) — JSON-Schema source of
  truth for every cross-component data format (synthetic / IAFDB / noise / classifier banks,
  training-run records, model metadata, and the phase-index formats), with codegen'd Pydantic
  models + file validators. No I/O; no torch.
- [`egm-data`](https://github.com/myocard-labs/egm-data) — the pure I/O layer: readers +
  writers for every contracts-defined bank / record / phase-manifest format. The only repo
  that touches HDF5 / CSV / JSON against project formats.
- [`egm-signal`](https://github.com/myocard-labs/egm-signal) — pure DSP primitives shared
  across producers + consumers: bandpass filtering, R-wave-anchored calibration, threshold
  segmentation, and temperature-scaling calibration (Guo 2017).
- [`egm-features`](https://github.com/myocard-labs/egm-features) — NumPy/SciPy per-trace
  feature extraction (morphology, spectral, complexity). Like egm-signal, a standalone
  signal-analysis library that doesn't run on its own — consumed by egm-classifier (realism
  diagnostics) and egm-studio (feature views + paper figures).

**Producers** (generate data)

- [`iafdb-pipeline`](https://github.com/myocard-labs/iafdb-pipeline) — downloads, calibrates,
  and segments the PhysioNet IAFDB into a healthy-segment bank and a noise bank.
- [`synthetic-egm-pipeline`](https://github.com/myocard-labs/synthetic-egm-pipeline) —
  Finitewave-driven 2D atrial simulations → pseudo-bipolar EGM extraction → an IAFDB-noise
  overlay mixer producing noise-mixed synthetic training banks.

**Consumers** (executable apps built on the foundation)

- [`egm-classifier`](https://github.com/myocard-labs/egm-classifier) — the 1D MobileViT
  binary fibrosis classifier and its training-data layer (patient-aware splits, per-trace
  augmentation, datasets). Three CLIs: train, eval (predictions bank + scalar metrics), and
  export (ONNX + a metadata sidecar with baked-in temperature calibration for C++ deployment).
- [`egm-studio`](https://github.com/myocard-labs/egm-studio) — a PySide6 desktop app with four
  modes (signal exploration, noise, ML diagnostics, paper-figure prep) plus the headless
  `egm-studio-render` CLI for reproducible publication figures.

**Paper**

- [`intracardiac-papers`](https://github.com/myocard-labs/intracardiac-papers) — LaTeX source
  for the white papers (plural; multiple papers are expected across phases). Not on PyPI.

---

## Dependency graph

```
   egm-contracts · egm-data · egm-signal · egm-features       foundation libraries
                             ↑
     ┌───────────────┬───────┴────────┬───────────────┐
  iafdb-        synthetic-       egm-classifier    egm-studio
  pipeline       egm-pipeline
       └─── producers ───┘             └─── consumers ───┘
```

Each component releases independently and pins its upstream siblings by exact version.
egm-contracts is the slowly-changing interface at the root; everything else moves freely as
long as the schema cascade (contracts → data → producers → consumers) is honored.

---

## Project status

**Phase 1 shipped (2026-06-23).** A binary 1D MobileViT classifier trained on noise-mixed
synthetic EGM banks reaches val AUROC ≈ 0.999 in-distribution. Run on the unlabeled IAFDB bank
as a **label-free sanity check**, the model saturates — it labels ~99.98% of IAFDB segments
fibrotic regardless of segment, a decision function with no usable operating threshold. That
is the informative negative result (full diagnostic:
[`project/investigations/v1_iafdb_investigation.md`](project/investigations/v1_iafdb_investigation.md)):
it is a training-distribution problem, not a recalibration one, and it is *not* a scored
validation (IAFDB carries no fibrosis ground truth).

**Polyrepo refactor complete.** The project migrated from a monorepo to the polyrepo above; all
component repos are released and interoperate. The record lives in the "Polyrepo refactor status"
section of [`project/project_plan.md`](project/project_plan.md).

**Current focus — Phase 1.5: synthetic-data realism.** The saturation result says the
synthetic side is too simple. Phase 1.5 makes it richer (Courtemanche cell model, pluggable
noise selection, multi-edge stimulation, activation-anchoring and additive-noise
investigations) — pushing the simulated distribution closer to physical reality rather than
"closing a sim-to-real gap" in the strict sense (there is no labeled real set to score
against). See [`project/project_plan.md`](project/project_plan.md) Phase 1.5.

---

## How to use this repo

Start with the docs, then the project truth:

```bash
# 1. Set up: clone the repos, create venvs, install + verify the constellation.
less docs/quick_start.md

# 2. The whole-project walkthrough — what each repo does and how they fit.
less docs/walkthrough.md

# 3. The canonical plan + current status.
less project/project_plan.md

# 4. Validate a phase index (needs myocard-egm-contracts + myocard-egm-data importable).
python scripts/validate_manifest.py            # see scripts/README.md
```

To run the pipeline end-to-end (synthetic bank → train → eval → render a figure), the
[walkthrough](docs/walkthrough.md) covers installing the pinned constellation and the reproduce
path; the [`integration/`](integration/README.md) smoke test is the minimal cross-repo check.

---

## Citation

If you reference this project in academic work, please cite the paper repo
(`intracardiac-papers`) once the first paper publishes. For software citation in the interim:

```bibtex
@software{klein_intracardiac_platform_2026,
  author = {Klein, Daniel},
  title  = {intracardiac-platform: meta repo for the intracardiac EGM fibrosis detection project},
  year   = {2026},
  url    = {https://github.com/myocard-labs/intracardiac-platform},
}
```

---

## License

MIT — see [LICENSE](LICENSE). Third-party data attribution is in [NOTICE](NOTICE).
