# intracardiac-platform

> Cross-cutting docs, planning, and integration tests for the **Intracardiac EGM Fibrosis Detection** project — a portfolio effort that takes synthetic + in-vivo intracardiac electrograms (EGMs), trains a 1D MobileViT-style CNN to flag fibrotic atrial tissue, and ships the result as a deployable model for catheter-ablation site selection.

Maintained by [Daniel Klein](https://github.com/myocard-labs).

---

## What this repo is

This is the **meta repo** for the project. It does not contain Python source.
It holds:

- `project/` — the canonical project-truth folder. `project_plan.md` is the source of truth for scope, status, and roadmap; `refactor_checklist.md` tracks the polyrepo migration; `v1_*_investigation.md` are the post-hoc diagnostics that drive the next round of work.
- `Documentation/` — design docs (PDFs) and the architecture reading list. Long-form rationale, not status.
- `examples/` — end-to-end scripts demonstrating cross-component workflows (train, evaluate, render a figure). Each pulls from the component repos.
- `integration/` — cross-repo smoke tests. The single canonical "does the whole pipeline still work" answer.

For the actual Python packages (data, model, viewer, paper figure renderer, etc.), see the component repos linked below.

---

## Component repos

Foundation:

- [`egm-contracts`](https://github.com/myocard-labs/egm-contracts) → PyPI `myocard-egm-contracts` — schemas + validators for the cross-component data formats (synthetic bank, IAFDB bank, run records, predictions).
- [`egm-data`](https://github.com/myocard-labs/egm-data) → PyPI `myocard-egm-data` — shared bank readers + PyTorch dataset wrappers + augmentation.

Producers (generate data):

- [`iafdb-pipeline`](https://github.com/myocard-labs/iafdb-pipeline) → PyPI `myocard-iafdb-pipeline` — downloads + calibrates + segments PhysioNet IAFDB into a healthy-trace bank.
- [`synthetic-egm-pipeline`](https://github.com/myocard-labs/synthetic-egm-pipeline) → PyPI `myocard-synthetic-egm-pipeline` — Finitewave-driven 2D atrial sims + pseudo-bipolar EGM extraction + hybrid mixing.

Consumers (build on data):

- [`egm-features`](https://github.com/myocard-labs/egm-features) → PyPI `myocard-egm-features` — engineered morphology + frequency + complexity features over EGM traces.
- [`egm-classifier`](https://github.com/myocard-labs/egm-classifier) → PyPI `myocard-egm-classifier` — 1D MobileViT binary fibrosis classifier (train / validate / export to ONNX).

Visualization + paper:

- [`egm-studio`](https://github.com/myocard-labs/egm-studio) → PyPI `myocard-egm-studio` — PySide6 desktop GUI for bank inspection + training curves + calibration + features, plus the `egm-figures` CLI for reproducible paper figures.
- [`intracardiac-paper`](https://github.com/myocard-labs/intracardiac-paper) — LaTeX source for the white paper (not published to PyPI).

Reference / learning:

- [`mobilevit-imagenette`](https://github.com/myocard-labs/mobilevit-imagenette) — 2D MobileViT reference implementation on Imagenette. The 1D classifier was adapted from this.

---

## Dependency graph

```
egm-contracts → egm-data → { iafdb-pipeline, synthetic-egm-pipeline, egm-classifier, egm-studio }
                                                                          ↑
                                                                     egm-features
```

Each component releases independently and pins its upstream dependencies via semver.

---

## Project status

Phase 1 of the [project plan](project/project_plan.md) is complete: a binary classifier (`egm-classifier` v1) trained on hybrid synthetic+noise EGM banks reached val AUROC ≈ 0.999 in-distribution. The IAFDB sim-to-real evaluation revealed the model has learned a synthetic-only shortcut and does not yet generalize to real recordings — full diagnostic in [`project/v1_iafdb_investigation.md`](project/v1_iafdb_investigation.md).

The current focus is the polyrepo refactor (this meta repo + the seven component repos above) and a parallel **synthetic v2** workstream to close the sim-to-real gap. See [`project/refactor_checklist.md`](project/refactor_checklist.md) for the plan.

---

## How to actually use this

Three workflows the meta repo enables:

```bash
# 1. Read the plan.
less project/project_plan.md

# 2. Reproduce the v1 → IAFDB result from scratch.
bash examples/reproduce_v1_iafdb.sh    # stub until component repos are tagged

# 3. Run the cross-repo smoke test.
bash integration/smoke.sh              # stub until component repos are tagged
```

---

## Citation

If you reference this project in academic work, please cite the paper repo
(`intracardiac-paper`) once it's published. For software citation:

```bibtex
@software{klein_intracardiac_platform_2026,
  author  = {Klein, Daniel},
  title   = {intracardiac-platform: meta repo for the intracardiac EGM fibrosis detection project},
  year    = {2026},
  url     = {https://github.com/myocard-labs/intracardiac-platform},
}
```

---

## License

MIT — see [LICENSE](LICENSE). Third-party data attribution is in [NOTICE](NOTICE).
