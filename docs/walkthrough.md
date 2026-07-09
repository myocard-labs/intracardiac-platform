# End-to-end walkthrough

A step-by-step, run-it-yourself guide to taking the pipeline from raw recordings all the way to a
built paper. It spells out every hand-off between stages — where each file lands and how to feed
it to the next stage — because the pieces don't auto-connect: each repo's shipped `examples/*.yaml`
writes into *its own* `banks/` folder, so getting one stage's output into the next stage's input
is a manual step you have to get right.

> **Scope.** This is the plain-text "how to run it" guide. A richer, interactive version — with
> screenshots and a walk through the actual egm-studio analysis behind the paper figures, on the
> real data — is planned once the science settles, after Phase 1.5 / 2.

**Prerequisites:** the constellation installed and the repos cloned as siblings — see
[`quick_start.md`](quick_start.md). Run the commands from your **workspace root** (the folder that
holds all the repos) unless a step says to `cd` into a repo.

## The data flow

```
 iafdb-pipeline ──┬── iafdb_noise_v1.h5  (+ _run_record.json) ─────────┐  (noise overlay)
 (real EGMs)      └── iafdb_healthy_v1.classifier.h5  (unlabeled) ──┐   │
                                                                    │   ▼
 synthetic-egm-pipeline ── synthegm_v1_clean.classifier.h5 ─────────│── synthegm_v1_noise_mixed.classifier.h5
 (Finitewave sims)                                                  │        (labeled: healthy / fibrotic)
                                                                    │                    │ train on this
 egm-classifier   train ─▶ best.pt + run.json ─▶ eval ──────────────┤                    │
                                                                    ├─▶ synth_v1_lpred…  (scored)
                                                                    └─▶ iafdb_v1_upred…  (label-free sanity check)
                              └─▶ export ─▶ best.onnx + best.model_metadata.json
                                                                        │
 egm-studio   explore banks · diagnose runs · compose figures ◀─────────┘
                              └─▶ egm-studio-render ─▶ figure PDFs
                                                                        │
 intracardiac-platform   phase manifest + validate_manifest.py          │
 intracardiac-papers     make ─▶ paper PDF ◀─────────────────────────────┘
```

Everything is keyed by stable ids, but on disk you move files by name — so the one rule to keep in
mind at every hand-off: **the file the next stage reads has to exist, under the exact name that
stage expects.**

## 0. Make one folder for the whole run

Keep every artifact in one place, so each stage reads from a known location and the phase manifest
and paper can find everything later. Make a `run/` folder at your workspace root with four
subfolders — `banks/`, `checkpoints/`, `predictions/`, `exports/`. The commands below refer to it
through a shell variable, so set that up first and work in a single terminal session (the variable
and the `cd`s below assume it):

```bash
export RUN="$(pwd)/run"
mkdir -p "$RUN"/{banks,checkpoints,predictions,exports}
```

## 1. Real recordings — iafdb-pipeline

Download IAFDB, then produce two things: the **noise bank** the mixer will overlay, and an
**unlabeled IAFDB ClassifierBank** for the stage-3 sanity check.

```bash
cd iafdb-pipeline
iafdb-download                                            # 32 records → ./data/iafdb/
iafdb-export-noise-bank examples/iafdb_noise_percentile.yaml
```

That writes the noise bank and its run-record sidecar into `iafdb-pipeline/banks/` — the files
`iafdb_noise_v1.h5` and `iafdb_noise_v1_run_record.json`.

Next the ClassifierBank. IAFDB has no fibrosis ground truth, so this bank must be **unlabeled** —
otherwise the export stamps an "all healthy" label on every trace. Open
`examples/iafdb_classifier.yaml`, find the `label_policy` line under `format:`, and change it from
`all-healthy` to `unlabeled`. Then export:

```bash
iafdb-export-bank examples/iafdb_classifier.yaml          # writes …/banks/iafdb_healthy_v1.classifier.h5
```

(That edited a tracked example file; `git checkout examples/iafdb_classifier.yaml` restores it when
you're done.)

Now copy the three artifacts the later stages need — the noise bank, its sidecar, and the
ClassifierBank — into your run folder, and confirm all three arrived in `run/banks/`:

```bash
cp banks/iafdb_noise_v1.h5 banks/iafdb_noise_v1_run_record.json \
   banks/iafdb_healthy_v1.classifier.h5 "$RUN/banks/"
cd ..
```

Full option set → [iafdb-pipeline](https://github.com/myocard-labs/iafdb-pipeline) `docs/usage.md`.

## 2. Synthetic labeled data — synthetic-egm-pipeline

The simulator produces the **labeled** training bank (each trace healthy or fibrotic by fibrosis
density) and overlays the stage-1 noise as it goes. The catch: the mixer locates the noise bank by
a relative path in its config, so before you run it you have to put stage-1's noise bank where the
config expects and confirm the name lines up.

Open `synthetic-egm-pipeline/examples/synthegm_v1_noise_mixed.yaml` and look at the
**`mix.noise_bank`** line. It reads `../banks/iafdb_noise_v1.h5` — meaning the mixer expects a file
named **`iafdb_noise_v1.h5`** in `synthetic-egm-pipeline/banks/`. Copy stage 1's noise bank and its
sidecar there, keeping the filename exactly the same:

```bash
cd synthetic-egm-pipeline
mkdir -p banks
cp "$RUN/banks/iafdb_noise_v1.h5" "$RUN/banks/iafdb_noise_v1_run_record.json" banks/
```

Before running, sanity-check the wiring by eye: the file you just placed
(`synthetic-egm-pipeline/banks/iafdb_noise_v1.h5`) should match, name for name, what the config's
`mix.noise_bank` line points at. This is the easiest step to get wrong, and it fails quietly — a
mismatched name means the mixer overlays the wrong noise, or none.

With the noise bank in place, run the simulator, then copy the noise-mixed bank into your run
folder:

```bash
synthegm-generate-dataset examples/synthegm_v1_noise_mixed.yaml
cp banks/synthegm_v1_noise_mixed.classifier.h5 "$RUN/banks/"
cd ..
```

It writes both the noise-mixed bank and a clean pre-mix intermediate into
`synthetic-egm-pipeline/banks/`; only the noise-mixed one is needed downstream. The two-step
decoupled mix and the SNR sweep are in
[synthetic-egm-pipeline](https://github.com/myocard-labs/synthetic-egm-pipeline) `docs/usage.md`.

## 3. Train, evaluate, export — egm-classifier

Unlike the producers, the classifier CLIs take path **override flags**, so instead of editing their
YAML you point each input and output at your run folder on the command line. (The shipped example
configs mention dev bank names like `…_small_gd` and a `…_bin` checkpoint dir that don't match
stages 1–2 — the flags below override all of them, so you can ignore those defaults.)

Train on the noise-mixed synthetic bank:

```bash
cd egm-classifier
egm-class-train examples/v1_baseline.yaml \
  --bank           "$RUN/banks/synthegm_v1_noise_mixed.classifier.h5" \
  --checkpoint-dir "$RUN/checkpoints/v1_baseline"
```

This writes `best.pt`, `run.json`, and `metrics.csv` into `run/checkpoints/v1_baseline`. The
headline held-out metrics (from training's internal patient-aware split) live in `run.json` and
`metrics.csv`.

Score the model on the labeled synthetic data — this produces a predictions bank and prints AUROC,
ECE, and a confusion matrix:

```bash
egm-class-eval examples/v1_eval.yaml \
  --checkpoint       "$RUN/checkpoints/v1_baseline/best.pt" \
  --bank             "$RUN/banks/synthegm_v1_noise_mixed.classifier.h5" \
  --predictions-bank "$RUN/predictions/synth_v1_lpred.classifier.h5"
```

Run the same model over the unlabeled IAFDB bank — the label-free sanity check. It writes a
predictions bank but prints no metrics (there's no truth to score against):

```bash
egm-class-eval examples/v1_eval.yaml \
  --checkpoint       "$RUN/checkpoints/v1_baseline/best.pt" \
  --bank             "$RUN/banks/iafdb_healthy_v1.classifier.h5" \
  --predictions-bank "$RUN/predictions/iafdb_v1_upred.classifier.h5"
```

Export the calibrated model to ONNX plus a metadata sidecar:

```bash
egm-class-export examples/v1_export.yaml \
  --checkpoint       "$RUN/checkpoints/v1_baseline/best.pt" \
  --calibration-bank "$RUN/banks/synthegm_v1_noise_mixed.classifier.h5" \
  --output-dir       "$RUN/exports/v1_baseline"
cd ..
```

This writes `best.onnx` and `best.model_metadata.json` into `run/exports/v1_baseline`. Every flag
and the config schema → [egm-classifier](https://github.com/myocard-labs/egm-classifier)
`docs/usage.md`.

### The IAFDB result is a sanity check, not a score

IAFDB has no fibrosis ground truth, so there is nothing to score against — no AUROC, no confusion
matrix, and none are faked (that's why the sanity-check eval emits a `upred_` bank with metrics
skipped). What it gives you is a **direction**. The v1 model, trained on synthetic data and run
over real IAFDB segments, predicts almost everything fibrotic — clearly wrong, and precisely the
saturation baseline to improve against. When a later synthetic revision, retrained and re-run,
lands nearer a sensible split, that's *better* (still not truth, but closer). You read that shift
in egm-studio's Output histogram (stage 4), not from a number. Background:
[`project/project_plan.md`](../project/project_plan.md).

## 4. Explore, diagnose, and make figures — egm-studio

```bash
egm-studio            # the desktop app
```

Open the files from your run folder (**File ▸ Open bank** / **Open training run**):

- **Signal exploration** — open `synthegm_v1_noise_mixed.classifier.h5` *and*
  `iafdb_healthy_v1.classifier.h5` together. The Summary overlay (per-feature distributions + KS
  distance) and **Find similar in other bank** show where the synthetic diverges from real — the
  read that drives the next round of synthetic-data work.
- **ML diagnostics** — open `synth_v1_lpred.classifier.h5` for ROC / calibration / confusion
  (labeled synthetic); open `iafdb_v1_upred.classifier.h5` to see the saturation in the Output
  histogram (no metrics, by design); open `run/checkpoints/v1_baseline/run.json` for the training
  curves.
- **Paper-figure prep** — compose a figure from a recipe with a live preview, then **Save into** a
  phase.

To reproduce a saved figure without opening the app:

```bash
egm-studio-render SPEC.json --phase ../intracardiac-platform/phases/phase_1_5_example
```

The four modes, the per-figure reading guide, and the save/scratch model →
[egm-studio](https://github.com/myocard-labs/egm-studio) `docs/usage.md`.

## 5. Curate the phase and validate — intracardiac-platform

egm-studio writes a phase `manifest.json` as you save observations and figures (a per-phase index
of every artifact and how they relate). Before shipping a phase that carries a paper, run the
release gate:

```bash
cd intracardiac-platform
python scripts/validate_manifest.py --phase <your-phase> --release-gate
# to see it pass against the shipped template:
python scripts/validate_manifest.py --phase 1_5_example
cd ..
```

It checks id integrity, cross-artifact coverage, and distribution over the phase index. Details →
[`phases/README.md`](../phases/README.md) and [`scripts/README.md`](../scripts/README.md).

## 6. Build the paper — intracardiac-papers

```bash
cd intracardiac-papers
make                  # builds every paper's PDF; figures come from egm-studio-render (stage 4)
cd ..
```

LaTeX-toolchain setup is in [`quick_start.md`](quick_start.md#build-the-papers-latex) and the
papers repo's `docs/latex-setup.md`.
