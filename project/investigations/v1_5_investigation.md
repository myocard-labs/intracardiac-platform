# v1.5 — label_threshold = 0.1 ablation diagnostic

**Started:** 2026-06-12 (evening)
**Last updated:** 2026-06-12 (evening)
**Status:** v1.5 trained; trajectory shows label-noise overfitting signature. Honest-comparison AUROC is slightly better than v1 test (0.964 vs 0.922) but the train-val gap is uglier. Recommended path: run v1.5 test, then proceed with v1 to IAFDB rather than further synthetic-side iteration.

**Prior context:** [`v1_baseline_investigation.md`](v1_baseline_investigation.md) reached the H4 conclusion that v1 errors are class-overlap at the synthetic label boundary, not shortcut learning. v1.5 was the cheap one-line config-change ablation to validate H4 by moving the binary boundary from `density > 0` to `density > 0.1`.

---

## TL;DR

The label_threshold change from 0.0 → 0.1 **relabeled** ~120 train traces (density in [0.05, 0.1)) from positive to negative instead of dropping them. That moved the class-overlap problem from test time (model errors at the boundary) into train time (conflicting training signals for similar morphology). Net effect:

- v1.5 train loss converges fine (0.004 by epoch 25), but val loss stays high (~0.55) and won't come down. Classic label-noise overfit signature.
- v1.5 best val AUROC = 0.9636 (epoch 11). Better than v1's *honest* number (test AUROC 0.9224), worse than v1's *optimistic* val number (0.9998). Apples-to-apples the move is a small AUROC improvement, but the training trajectory is meaningfully unhealthier.
- The diagnostic question H4 ("is the class overlap at the synthetic label boundary the real bottleneck?") isn't cleanly answered by relabeling because relabeling *creates* a new label-noise problem in the same density range. The clean experiment would be to **drop** the [0.05, 0.1) traces (v1.5b), not relabel them.

Practical implication: don't spend more cycles on synthetic-side iteration before IAFDB. The IAFDB sim-to-real result is what decides Phase 1 viability; the v1.5 vs v1 question is largely orthogonal until we know the model transfers at all.

---

## Run details

- **Checkpoint dir:** `egm_classifier/checkpoints/v1_5_baseline/` (`best.pt`, `metrics.csv`, `run.json`)
- **Config:** v1_baseline.yaml with `data.label_threshold: 0.1` (only change from v1)
- **Model:** same — 1D MobileViT, width_multiplier=1.0, 1.56M params
- **Data:** same bank `hybrid_v1.h5`, same 80/10/10 patient-aware split, same patient IDs
- **Class balance shift:**
  - v1: train = 440 negative / 1160 positive  (pos_weight 0.379)
  - v1.5: train = 560 negative / 1040 positive  (pos_weight 0.538)
  - Δ = 120 traces relabeled positive → negative (density in [0.05, 0.1))
- **Training:** same — 60 epochs, AdamW lr=3e-4, cosine LR, weight_decay=0.05

---

## Trajectory comparison

### v1.5 best epoch (epoch 11)

| | v1 best val (ep 20) | v1 test | v1.5 best val (ep 11) |
|---|---|---|---|
| Loss | 0.127 | 0.270 | **0.385** |
| AUROC | 0.9998 | 0.9224 | **0.9636** |
| Accuracy | 0.925 | 0.960 | 0.930 |
| Precision | 1.000 | 0.958 | **0.896** |
| Recall | 0.893 | 0.986 | **1.000** |
| ECE | 0.072 | 0.0415 | 0.071 |

**Apples-to-apples comparison is v1.5 val vs v1 test** (since v1 val was optimistic): AUROC ticks up 0.922 → 0.964 (+0.04), but precision drops 0.958 → 0.896 (-0.06) and val loss balloons 0.27 → 0.39. Net: small AUROC gain at the cost of more confidently-wrong false positives. Not a clear win.

### Training-trajectory shape (not just endpoints)

v1.5 train loss collapses to ~0.004 by epoch 25 and stays there, but val loss never gets near it. From epoch 11 onwards:

- val_loss stays in [0.40, 0.65] for the next 49 epochs
- val_AUROC oscillates 0.90–0.95, no clear improvement after epoch 11
- val_accuracy stays 0.92–0.93 essentially flat
- model essentially predicts every val trace at sigmoid ~0.999 (concentrated reliability bin) with ~7% confidently-wrong

v1 by contrast had train_loss ~ 1e-4 and val_loss converging to ~0.05 by epoch 22. The v1.5 train-val gap is much larger in *absolute* terms (train 0.004 vs val 0.6 is ~150× ratio; the magnitudes are what matter for the overfit reading).

This is the canonical signature of **the model memorizing label noise**: it can drive train loss to zero by fitting individual training examples by their specific sim/noise/seed fingerprint, but those memorized labels don't transfer to val because val has different examples in the same ambiguous density range.

---

## Diagnosis

### Why relabeling didn't help

The v1 H4 hypothesis: at density ≈ 0–0.1, healthy and fibrotic morphologies overlap. The model gets test errors there because the binary boundary doesn't correspond to a real feature-space boundary.

My v1.5 prediction was that moving the boundary to 0.1 would put it in a region where morphology *does* differ — and val AUROC would jump to 0.97–0.99.

What I missed: **relabeling [0.05, 0.1) as negative doesn't move the model's decision boundary, it muddies the negative class.** Some of those 120 relabeled traces have detectable fibrotic morphology (small but real). The model now sees:

- "Sim X, density 0.15, morphology fibrotic-clear → label 1"
- "Sim Y, density 0.08, morphology fibrotic-mild → label 0"  ← relabeled
- "Sim Z, density 0.07, morphology fibrotic-mild → label 0"  ← relabeled
- "Sim 88, density 0.0, morphology fibrotic-mild-looking → label 0"  ← truly healthy

The model can fit this on training only by memorizing sim-specific identifiers (which conv layers can do — there's enough capacity). But the val set has *different* sims with similar borderline densities, and the memorization doesn't transfer.

### What would have been a cleaner experiment

**v1.5b: drop the [0.05, 0.1) traces entirely.** Filter the bank to exclude `0 < fibrosis_density < 0.1`. This gives a clean boundary in the training data — density = 0 (truly healthy) vs density ≥ 0.1 (clearly fibrotic), no muddied middle. Expected outcome:

- train loss converges normally
- val loss stays low and converges
- val AUROC ≥ 0.97 with high precision
- The H4 hypothesis gets a clean test

Total cost: maybe 30 min of work in `synthetic_egm_pipeline` (or the classifier's data loader) + ~15 min training.

### Why we still don't run v1.5b right now

The IAFDB sim-to-real result is the actual Phase 1 viability decision. If v1's model already transfers to IAFDB acceptably, the whole synthetic-label-boundary question becomes a footnote. Spending cycles polishing the synthetic-side label before knowing whether the *model* transfers at all is pre-optimization on the wrong problem.

The right sequencing:

1. Run v1.5 test (5 min) — honest in-distribution number for v1.5.
2. Decide which model goes to IAFDB. Currently leaning v1 (better-understood; the FP/FN inspection is for v1 specifically).
3. Run IAFDB eval against the chosen model.
4. Based on IAFDB result, decide whether to iterate synthetic (v1.5b or a real v2 with broader changes) or move to Phase 2.

---

## Recommended next steps

In priority order:

1. **Run v1.5 on test split** (5 min). `egm-eval configs/v1_5_baseline.yaml --split test`. Gives the honest in-distribution AUROC for v1.5 to anchor the comparison. Expected: AUROC around 0.92–0.94, similar pattern to v1's val→test gap.
2. **Proceed with v1 to IAFDB.** v1 is the model whose failure modes we've already characterized in detail (sim 88, density ≈ 0.07 boundary, etc.). When IAFDB results come back, we'll be able to interpret them in light of what we already know about v1 — vs v1.5 where there's a new label-noise confounder we'd have to control for separately.
3. **Defer v1.5b.** Don't pre-iterate the synthetic side. If IAFDB lands in the "pursue with synthetic-side work" zone (AUROC 0.65–0.85), v1.5b becomes the natural next experiment with v1 IAFDB transfer as the ground truth to beat.

---

## Decision log

| Date | Event |
|---|---|
| 2026-06-12 (evening) | v1.5 trained with `label_threshold: 0.1`. Best val AUROC 0.9636 at epoch 11. |
| 2026-06-12 (evening) | Daniel observed "doesn't train well, at least not for validation data." High val_loss, val AUROC drops after epoch 11. |
| 2026-06-12 (evening) | Diagnosis: relabeling vs dropping the [0.05, 0.1) density traces introduces label noise into the negative class. Train loss collapses (memorization) but val_loss stays high (no generalization). |
| 2026-06-12 (evening) | Honest comparison (v1.5 val vs v1 test): AUROC +0.04, precision −0.06, val_loss +0.12. Small AUROC gain at the cost of more confident FPs. Not a clear win. |
| 2026-06-12 (evening) | Decision: don't spend more cycles on synthetic-side iteration before IAFDB. Proceed with v1 (better-understood) to IAFDB; v1.5b (drop instead of relabel) parked as a fallback if IAFDB result needs synthetic-side work. |
| 2026-06-12 (evening) | Recommended sequence: v1.5 test (5 min) → v1 IAFDB eval → branch on result. |
| 2026-06-12 (late evening) | **v1.5 test result:** "similar to the test data but the loss is just a bit lower. Overall not good." The relabel-instead-of-drop change didn't deliver meaningful improvement on the honest test number either. v1.5 closed out as a learning experiment, not a model-quality improvement. v1.5b (drop instead of relabel) remains parked. |
| 2026-06-12 (late evening) | **IAFDB healthy-segment bank generated.** `iafdb-export-bank` ran successfully (output bank exists in `iafdb_pipeline/banks/iafdb_healthy_v1.h5` or similar). Ready for the classifier to consume for sim-to-real eval. |
| 2026-06-12 (late evening) | **Decision confirmed:** proceed with v1 (not v1.5) to IAFDB. v1.5 didn't improve the model meaningfully and added a label-noise confounder; v1's failure modes are already characterized in detail. |
