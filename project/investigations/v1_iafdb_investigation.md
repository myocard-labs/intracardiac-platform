# v1 — IAFDB sim-to-real evaluation

**Started:** 2026-06-12 (late evening)
**Last updated:** 2026-06-12 (late evening)
**Status:** RESOLVED. Authoritative **full-bank GPU run is in** (98,549 IAFDB segments) and confirms the subsample almost exactly. **v1 does not transfer to real EGMs — it labels ~99.98% of IAFDB healthy segments as fibrotic at ~0.999 confidence, and the decision function is saturated (no usable operating threshold).** Phase 1 viability call: **pursue with synthetic-side iteration** — the synthetic *healthy* class is the thing to fix.

**Prior context:** [`v1_baseline_investigation.md`](v1_baseline_investigation.md) concluded v1's *in-distribution* errors are class overlap at the synthetic label boundary, not shortcut learning, but flagged AUROC≈1.0 / 100%-precision-for-57-epochs as a yellow flag that "the synthetic task has shortcuts the IAFDB check will reveal." [`v1_5_investigation.md`](v1_5_investigation.md) closed out the label-threshold ablation and confirmed: proceed with **v1** (not v1.5) to IAFDB. This is that check.

---

## TL;DR

The model trained on synthetic fibrosis **over-calls fibrosis on real data, totally**. On IAFDB healthy segments (truth = healthy for all of them) it outputs mean P(fibrotic) ≈ **0.999** and predicts "fibrotic" for ~99.97% of them at the 0.5 threshold — uniformly across all 8 patients. The mixed-set AUROC (≈0.77 on the subsample) is only above chance because the synthetic-fibrotic positives get pushed to ~0.9991 while the real-healthy negatives sit at ~0.9986 — a razor-thin ranking margin on top of a collapsed, saturated decision function.

This is the yellow flag from v1_baseline cashing out: the synthetic "healthy" class is too easy/clean a negative, so the model learned a decision rule that flags anything with real-EGM richness as fibrotic. It is a **sim-to-real distribution gap**, not a labeling bug. The fix is synthetic-side, not a retrain on the same bank.

**Two load-bearing caveats** (see *Caveats* below): the headline AUROC is from a 3k/98.5k subsample on CPU, and the verification used the locally-regenerated 512-sample synthetic bank, which may differ from the bank the checkpoint trained on. The **IAFDB over-calling finding is robust to both** (it's about real data and a fixed checkpoint); the **synthetic-positive side and the exact AUROC must be re-confirmed on the GPU** with the matched training bank and the full IAFDB bank.

---

## Run details

- **Command:** `egm-eval-sim2real --checkpoint checkpoints/v1_baseline/best.pt --synthetic-bank hybrid_v1.h5 --iafdb-bank iafdb_healthy_v1.h5 --output ... --max-iafdb 3000` (CPU)
- **Model:** v1_baseline `best.pt`, epoch 20, 1D MobileViT width=1.0. Same checkpoint whose in-distribution test AUROC = 0.9224.
- **Split config:** sourced from `run.json` beside the checkpoint — patient-aware split seed 0, 80/10/10, `label_threshold` 0.0, z-score on, T=512.
- **Synthetic positives:** test-split traces with `fibrosis_density >= 0.1` (the *clear* fibrosis; ambiguous low-density tail dropped, per the locked 2026-06-12 decision). N = 120.
- **IAFDB negatives:** 3,000-segment random subsample of the 98,549-segment bank (subsample is a verification convenience; the real run takes the full bank). All label 0.
- **Headline metric:** Option B mixed AUROC (synthetic-fibrotic vs IAFDB-healthy), per the locked project_plan decision.

---

## Results — authoritative full-bank GPU run (98,549 IAFDB segments)

The subsample and full-bank runs agree to ~3 decimals; the bank matched (synthetic positives are the identical 120 with recall 1.0), which **retires the subsample + bank-mismatch caveats**. Numbers below are the full-bank figures (subsample in parentheses where it differs).

### Option B — mixed set (the headline)

| Metric | Value | Reading |
|---|---|---|
| **AUROC** | **0.767** (0.768) | vs synthetic-test 0.9224. Generous — see "saturation" below. |
| Accuracy | 0.0014 | 98,534 / 98,549 real segments called fibrotic. |
| Precision | 0.0012 | ~all positives predicted are real-healthy false positives. |
| Recall | 1.000 | Catches every synthetic-fibrotic (and ~everything else). |
| F1 | 0.0024 | — |
| ECE | 0.997 | Calibration essentially inverted on the mixed set. |
| Confusion | tp 120 / fp 98534 / tn 15 / fn 0 | Predicts "fibrotic" for all but 15 traces. |

### The decision function is saturated (the load-bearing finding)

Both classes are crammed against P=1.0 with almost no spread, so **no threshold recovers a usable operating point** — this is not a temperature/calibration fix:

- IAFDB-healthy P(fibrotic): min 0.000, **p1 0.9974, p10 0.9983, median 0.9989, p90 0.9994**, max 1.000. Only **15 of 98,549** fall below 0.5; only 90 below 0.99.
- Synthetic-fibrotic P(fibrotic): min 0.567, median 0.9993, max 0.9999.
- The two medians differ by ~0.0004. The AUROC>0.5 is bought almost entirely by that sliver plus the ~15–90 low-prob real outliers (which look like quiet/degenerate windows). There is essentially **no transferable signal at the operating level.**

### Option A — IAFDB-only calibration (truth = healthy)

| Metric | Value | Well-behaved model |
|---|---|---|
| mean P(fibrotic) | **0.9986** | → near 0 |
| frac ≥ 0.5 (FPR@0.5) | 0.9997 | → near 0 |
| ECE vs healthy | 0.9986 | → near 0 |

Per-patient mean P(fibrotic) ranges 0.9975–0.9990 across iaf1–iaf8 (frac≥0.5 = 0.998–1.000). **Uniform** — not a single-patient or single-channel artifact.

### What the AUROC 0.77 actually means here

Both classes are crushed against 1.0: synthetic-fibrotic ≈ 0.9991, real-healthy ≈ 0.9986. The ranking is *barely* correct (positives slightly higher), so AUROC clears 0.5 but the decision function is saturated and useless at any fixed threshold. AUROC's imbalance-robustness is doing all the work; the number overstates how usable the model is on real data. **The calibration metrics (Option A) are the more honest summary of the failure than the AUROC.**

---

## Diagnosis

### Leading hypothesis: "real-EGM richness ⇒ fibrotic" shortcut

The synthetic *healthy* class is a clean single-activation Aliev–Panfilov wave with no fibrosis — smooth, low-complexity morphology. The synthetic *fibrotic* class adds fractionation/secondary deflections. A cheap, high-accuracy in-distribution rule is therefore **"sharp/fractionated/complex ⇒ fibrotic, smooth ⇒ healthy."** Real intracardiac EGMs — even from healthy myocardium — are far richer than the synthetic healthy class (genuine physiological deflections, electronics, residual filtered noise). Under that learned rule, **everything real looks fibrotic.** This is consistent with:

- the v1_baseline yellow flag (AUROC≈1.0 in-distribution ⇒ an easy, possibly shortcut-y synthetic boundary),
- per-trace z-score *not* saving us — the shortcut is morphological, not amplitude-based, so discarding amplitude doesn't remove it,
- the uniform per-patient collapse — a global distribution gap, not patient-specific.

### Alternative / compounding explanations to rule out on the GPU run

1. **Bank-version mismatch (verification artifact).** The local synthetic bank is the regenerated 512-sample one; the checkpoint trained on the desktop bank (`run.json` bank path is a foreign absolute path). The synthetic-positive probabilities here (~0.999, recall 1.0) look exactly like in-distribution behavior, so this probably isn't distorting much — but confirm by re-running with the exact training bank.
2. **Preprocessing skew between pipelines.** Synthetic traces and IAFDB segments both go through the same `TraceTransform` (z-score, T=512), but IAFDB is additionally calibrated + 30–300 Hz band-passed upstream. If that band-pass leaves real EGMs spectrally unlike the synthetic morphology, it compounds the gap. Worth a spectral-centroid comparison (the deferred `egm_features` package is the natural tool).
3. **Decision-threshold vs. ranking.** Even if the model is hopeless at 0.5, the AUROC says there's *some* separable signal. A swept-threshold / per-patient threshold could recover usable operating points — but that's a band-aid over the distribution gap, not a fix.

---

## Caveats (read before acting on the numbers)

1. **Subsample.** 3,000 of 98,549 IAFDB segments. Random subsample preserves the distribution, so the ~0.999 mean P(fibrotic) is trustworthy; the **exact mixed AUROC will shift** on the full bank (more negatives, same imbalance direction).
2. **Possible synthetic-bank mismatch.** Re-run on the GPU with the exact bank the checkpoint trained on before quoting the AUROC anywhere citable.
3. **CPU verification.** The full run is a few minutes on CPU, seconds on the GPU. Use the GPU.

**Authoritative command (full bank, GPU):**

```
egm-eval-sim2real \
  --checkpoint checkpoints/v1_baseline/best.pt \
  --synthetic-bank <the bank v1_baseline trained on> \
  --iafdb-bank iafdb_pipeline/banks/iafdb_healthy_v1.h5 \
  --output checkpoints/v1_baseline/sim2real_v1/ \
  --device cuda
```

(no `--max-iafdb` ⇒ all 98,549 negatives.)

---

## Recommended next steps

In priority order:

1. **Run the authoritative full-bank eval on the GPU** with the matched training bank. Confirm the mixed AUROC and that synthetic positives still behave in-distribution (recall ~1.0, probs ~0.999). The IAFDB-only numbers should barely move from the subsample.
2. **Quantify the sim-to-real morphology gap directly.** Compare feature distributions (spectral centroid, secondary-peak count, fractal/sample entropy) between synthetic-healthy, synthetic-fibrotic, and IAFDB-healthy. This is exactly the deferred `egm_features/` package's first job and would confirm/refute the "richness ⇒ fibrotic" hypothesis. If IAFDB-healthy sits in synthetic-*fibrotic* feature territory, the shortcut is confirmed.
3. **This is squarely "pursue with synthetic-side iteration" territory** (project_plan thresholds: 0.65–0.85 AUROC). Concretely, the synthetic *healthy* class needs to look more like real healthy tissue:
   - Mix real IAFDB-healthy *background* into synthetic healthy traces (the noise bank already exists in `synthetic_egm_pipeline`) so "healthy" isn't a sterile flat wave.
   - Broaden synthetic healthy morphology (multi-activation, conduction variability) so richness ≠ fibrosis.
   - Consider **Phase 5 CLOCS-style self-supervised pretraining on unlabeled IAFDB** before fine-tuning — the roadmap's designated sim-to-real-gap tool; this result is the strongest argument yet for pulling it earlier.
4. **Don't start the white paper's results section on this number** — but the *method* (mixed Option B + IAFDB-only calibration + per-patient) and this negative result are exactly the kind of honest sim-to-real finding the paper's limitations/▸methodology sections need. Keep the artifacts.

---

## Decision log

| Date | Event |
|---|---|
| 2026-06-12 (late evening) | `egm-eval-sim2real` built: schema-polymorphic bank loader (auto-detect IAFDB via `traces/label`), `load_iafdb_healthy_segments` filled in, mixed Option B + IAFDB-only Option A + per-patient + per-trace `test_predictions.csv`. Versioned in `training/reporting.py`. 48 tests green. |
| 2026-06-12 (late evening) | Locked: synthetic positives = test-split `density >= 0.1` (drop ambiguous tail); verify on subsample in-sandbox, authoritative full-bank run on GPU. |
| 2026-06-12 (late evening) | **Subsample verification (3k IAFDB, CPU):** mixed AUROC 0.768; IAFDB-only mean P(fibrotic) 0.9986, FPR@0.5 0.9997, ECE 0.9986; uniform across iaf1–iaf8. Synthetic positives behave in-distribution (recall 1.0). |
| 2026-06-12 (late evening) | **Interpretation:** sim-to-real calibration collapse — model over-calls fibrosis on all real EGMs. Leading hypothesis: "real-EGM richness ⇒ fibrotic" shortcut, because synthetic healthy is an unrealistically clean negative. Confirms the v1_baseline yellow flag on real data. |
| 2026-06-12 (late evening) | **Decision:** Phase 1 viability = "pursue with synthetic-side iteration." Next: authoritative GPU run, then make synthetic healthy realistic (real-noise/background mixing, broader morphology) and/or pull Phase 5 CLOCS pretraining forward. White-paper results deferred; keep this as a methodology/limitations artifact. |
| 2026-06-13 | **Authoritative full-bank GPU run in** (`checkpoints/v1_baseline/sim2real_v1/`): mixed AUROC 0.767, IAFDB mean P(fibrotic) 0.9987, FPR@0.5 0.9998, confusion tp120/fp98534/tn15/fn0. Matches subsample to ~3 dp; bank confirmed matched (120 synthetic positives, recall 1.0) → subsample + bank-mismatch caveats retired. New finding: decision function **saturated** (IAFDB p1=0.9974, only 15/98549 below 0.5) — no usable threshold; needs a training-distribution fix, not recalibration. Daniel's read ("simulated data needs to be more accurate") confirmed and sharpened to: the synthetic *healthy* class is the lever. Phase 1 viability decision stands: pursue with synthetic-side iteration. |
