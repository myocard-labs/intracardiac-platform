# References — reading index

Third-party literature this project draws on. The PDFs live in this folder **locally** but are
**not committed** to git (large, third-party); this index is the committed record of what they
are and why they matter.

**Two links per entry.** The **title** links to the local copy in `references/` — clicking it
opens the PDF when you have it downloaded here and you're reading this file in a local tool (VS
Code, a file browser, a local markdown preview). The **download** link fetches it from the
source; that is also the link that works on GitHub, where the PDFs are absent. To populate the
folder from a fresh clone, download each paper from its link into `references/` under the
filename shown in the title link.

For *reading progress* and additional papers not downloaded here (search seeds, background
reading), see the internal [`project/architecture_reading_list.md`](../project/architecture_reading_list.md).

---

## The problem & closest precedent — intracardiac-EGM machine learning

- **[Using Machine Learning to Characterize Atrial Fibrotic Substrate From Intracardiac Signals With a Hybrid in silico and in vivo Dataset](fphys-12-699291.pdf)** — Sánchez et al., *Frontiers in Physiology* 12:699291 (2021). *Why:* **the paper this project replicates and extends.** Its hybrid synthetic + real dataset, per-trace feature set, and fibrosis-classification framing are the direct methodological template. · [download](https://doi.org/10.3389/fphys.2021.699291)
- **[Atrial fibrillation signatures on intracardiac electrograms identified by deep learning](1-s2.0-S0010482522002438-main.pdf)** — Rodrigo et al. (Narayan lab), *Computers in Biology and Medicine* 145:105451 (2022). *Why:* the closest **deep-learning-on-intracardiac-EGM** precedent — DL recovers AF signatures from EGM shape/rate/timing, evidence the DL-on-iEGM premise holds. (+ [supplement](1-s2.0-S0010482522002438-suplement.pdf)) · [download](https://doi.org/10.1016/j.compbiomed.2022.105451)

## Cardiac deep-learning analogs

- **[Cardiologist-Level Arrhythmia Detection and Classification in Ambulatory Electrocardiograms Using a Deep Neural Network](nihms-1051795.pdf)** — Hannun et al. (Stanford), *Nature Medicine* 25:65–69 (2019). *Why:* the canonical 1D residual-CNN rhythm classifier — the end-to-end template most cardiac-signal CNN work builds on (backbone shape, class-imbalance handling, long-window inputs). · [download](https://doi.org/10.1038/s41591-018-0268-3)
- **[CLOCS: Contrastive Learning of Cardiac Signals Across Space, Time, and Patients](2005.13249v3.pdf)** — Kiyasseh, Zhu & Clifton, *ICML* 2021. *Why:* the Phase-5 direction — self-supervised pretraining on unlabeled IAFDB before fine-tuning on the labeled synthetic set. · [download](https://arxiv.org/abs/2005.13249)

## Model architecture — the 1D MobileViT lineage

- **[MobileViT: Light-weight, General-purpose, and Mobile-friendly Vision Transformer](MobileViT.pdf)** — Mehta & Rastegari, *ICLR* 2022. *Why:* the architecture the v1 classifier is a **1D adaptation of** — the MobileViT block (local conv + global attention + fusion) is the core. · [download](https://arxiv.org/abs/2110.02178)
- **[MobileNetV2: Inverted Residuals and Linear Bottlenecks](MobileNetV2.pdf)** — Sandler et al., *CVPR* 2018. *Why:* the inverted-residual (MV2) block the MobileViT backbone — and our 1D version — is built from. · [download](https://arxiv.org/abs/1801.04381)
- **[CoAtNet: Marrying Convolution and Attention for All Data Sizes](CoAtNet.pdf)** — Dai et al., *NeurIPS* 2021. *Why:* a principled CNN+attention hybrid with a scaling-law analysis — informs sizing a hybrid model on the project's small dataset. · [download](https://arxiv.org/abs/2106.04803)
- **[An Image Is Worth 16×16 Words: Transformers for Image Recognition at Scale (ViT)](2010.11929v2.pdf)** — Dosovitskiy et al., *ICLR* 2021. *Why:* patch-embedding + transformer classification — the patching idea that adapts directly to 1D EGM time-windows. · [download](https://arxiv.org/abs/2010.11929)
- **[Attention Is All You Need](1706.03762v7.pdf)** — Vaswani et al., *NeurIPS* 2017. *Why:* the Transformer — scaled dot-product attention + positional encoding behind MobileViT's transformer sub-blocks. · [download](https://arxiv.org/abs/1706.03762)
- **[Neural Machine Translation by Jointly Learning to Align and Translate](1409.0473v7.pdf)** — Bahdanau, Cho & Bengio, *ICLR* 2015. *Why:* the original (additive) attention mechanism; also the indexed-summation notation style the project's ML theory docs follow ("Bahdanau-style"). · [download](https://arxiv.org/abs/1409.0473)
- **[VisualBERT: A Simple and Performant Baseline for Vision and Language](VisualBert.pdf)** — Li et al., 2019. *Why:* surveyed while researching attention / fusion architectures; **not load-bearing** for the current single-modality (EGM-only) design — kept as a cross-modal reference against a possible future joint MRI + EGM direction. · [download](https://arxiv.org/abs/1908.03557)

## Model calibration

- **[On Calibration of Modern Neural Networks](1706.04599v2.pdf)** — Guo, Pleiss, Sun & Weinberger, *ICML* 2017. *Why:* temperature scaling, ECE, and reliability diagrams — the post-hoc calibration the classifier fits and bakes into the exported model. · [download](https://arxiv.org/abs/1706.04599)

## Synthetic substrate & simulation — the Finitewave lineage

- **[Computer based method for identification of fibrotic scars from electrograms and local activation times on the epi- and endocardial surfaces of the ventricles](pone.0300978.pdf)** — Okenov, Nezlobinsky, Zeppenfeld, Vandersickel & Panfilov, *PLoS ONE* 19(4):e0300978 (2024). *Why:* the Panfilov/Finitewave group's method for pseudo-EGM-from-simulation + fibrosis-from-electrogram — the pseudo-bidomain extraction and density-from-signal approach the synthetic pipeline draws on. · [download](https://doi.org/10.1371/journal.pone.0300978)
- **[Multiparametric analysis of geometric features of fibrotic textures leading to cardiac arrhythmias](41598_2021_Article_606.pdf)** — Nezlobinsky, Okenov & Panfilov, *Scientific Reports* 11:21111 (2021). *Why:* the same group's in-silico study of how fibrotic-texture geometry drives arrhythmia — background for the synthetic fibrosis-substrate design. · [download](https://doi.org/10.1038/s41598-021-00606-x)
- **openCARP publications** — `openCARP/` holds an **untriaged** set of PDFs collected from openCARP's *"Publications using openCARP"* list. Not yet curated — **Phase 1.5** will sift which are relevant to the planned phases versus noise. (openCARP itself was evaluated as a simulation backend and rejected in favor of Finitewave's laptop-runnable 2D approach.) · [opencarp.org](https://opencarp.org)
