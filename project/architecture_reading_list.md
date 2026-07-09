# ML architecture reading list

Tracking document for the CNN-architecture papers seeded during the early
design conversations for the [intracardiac catheter / fibrosis CNN project].
Use the checkboxes to mark progress.

**Reading priority — read in this order:** Tier 1 → Tier 3 → Tier 2 → Tier 4.
Tier 1 gives you the closest analog (cardiac-signal CNNs). Tier 3 is where
the actual architectural choice for this project is likely to land (1-D CNN
backbone + lightweight attention head). Tier 2 is the broader background to
make Tier 3 make sense. Tier 4 is domain-specific atrial work — read after
you've made an architectural choice.

**Reading goal per paper:** unless otherwise noted, you don't need to
re-derive the math — you want (a) the architectural diagram, (b) what
problem it was designed to solve, and (c) which design choices would
translate to a 1-D intracardiac EGM application.

**Verification status of citations:** items marked ✓ have been verified
against arxiv / publisher pages (May 2026). Items marked ◇ are search
seeds — go look them up to confirm before chasing them. Cardiac-ML
literature moves fast; group attributions and dates can drift.

---

## Tier 1 — Closest analog: cardiac-signal CNNs

These are the conceptually closest existing work. Read first; everything
else makes more sense once you've internalized how a 1-D CNN gets applied
to cardiac signals end-to-end.

- [ ✓ ] **✓ Hannun A, Rajpurkar P, Haghpanahi M, et al.** *Cardiologist-level
  arrhythmia detection and classification in ambulatory electrocardiograms
  using a deep neural network.* **Nature Medicine** 2019;25(1):65-69.
  PMID: 30617320.
  - **Why:** The canonical Stanford rhythm-net paper. Surface ECG not
    intracardiac, but the 1-D residual CNN backbone and the training
    methodology (class imbalance handling, long-window inputs) are the
    template most subsequent cardiac-ML work builds on.
  - **Focus on:** Architecture diagram (Fig. 1), output-head design for
    multi-class arrhythmia classification, how they handled long time
    series.

- [ ] **✓ Kiyasseh D, Zhu T, Clifton DA.** *CLOCS: Contrastive Learning of
  Cardiac Signals Across Space, Time, and Patients.* **ICML 2021**.
  arxiv: 2005.13249.
  - **Why:** Self-supervised pretraining on cardiac signals. Directly
    relevant if you eventually want to pretrain on unlabeled real EGMs
    (e.g., the rest of IAFDB you don't use as labeled high-voltage segments)
    before fine-tuning on the smaller noise-mixed labeled set.
  - **Focus on:** The three contrastive objectives (CMSC / CMLC / CMSMLC)
    and how patient-level views are constructed. The space dimension is
    especially relevant for multi-electrode catheter data.

---

## Tier 2 — Modern architecture primitives

The building blocks. Skim if you've already worked with these — Tier 3 is
where the project-relevant decisions get made.

- [ ] **✓ Vaswani A, Shazeer N, Parmar N, et al.** *Attention Is All You
  Need.* **NeurIPS 2017**. arxiv: 1706.03762.
  - **Why:** Read the original even if you've seen ten summaries — the math
    in §3.2.1 (scaled dot-product attention) and §3.5 (positional encoding)
    will matter when you pick a positional-encoding scheme for 1-D EGM
    patches.

- [ ] **✓ Dosovitskiy A, Beyer L, Kolesnikov A, et al.** *An Image Is Worth
  16×16 Words: Transformers for Image Recognition at Scale.* **ICLR 2021**.
  arxiv: 2010.11929.
  - **Why:** The patching idea translates almost directly to 1-D signals —
    chop your EGM into time-patches, embed, attend. Read for the
    patch-embedding scheme and the inductive-bias discussion.

- [ ] **✓ Nie Y, Nguyen NH, Sinthong P, Kalagnanam J.** *A Time Series is
  Worth 64 Words: Long-term Forecasting with Transformers* (PatchTST).
  **ICLR 2023**. arxiv: 2211.14730.
  - **Why:** The cleanest application of ViT-style patching to 1-D time
    series and a strong baseline. Two key ideas — patching and
    channel-independence — both translate naturally to multi-channel
    intracardiac EGM data.
  - **Focus on:** Fig. 2 (architecture overview) and the channel-independent
    design (which matters because your bipolar pairs are physically
    independent).

- [ ] **✓ Liu Z, Mao H, Wu C-Y, et al.** *A ConvNet for the 2020s*
  (ConvNeXt). **CVPR 2022**. arxiv: 2201.03545.
  - **Why:** Important counterpoint to all the transformer hype — shows
    that with modern training tricks, a well-designed CNN matches or beats
    transformers. Relevant because for shorter signals with strong local
    structure (like single-beat EGM windows), CNNs are often still the right
    call. ConvNeXt patterns translate cleanly to 1-D.
  - **Focus on:** Section 2 (modernization roadmap) — each step they take
    is a design knob you'd consider for your own 1-D backbone.

- [ ] **✓ Gu A, Dao T.** *Mamba: Linear-Time Sequence Modeling with
  Selective State Spaces.* **2023**. arxiv: 2312.00752.
  - **Why:** Worth being aware of as the current frontier for long-sequence
    modeling. Probably overkill for single-beat EGM windows, but interesting
    if you go to longer recordings (multi-second AF segments). Skim for
    now; revisit if you decide on longer context windows.

---

## Tier 3 — Hybrid CNN-transformer designs (sweet spot for this project)

These are the most directly applicable to your stated architectural
hypothesis (1-D ConvNeXt-style backbone + lightweight attention head).
Read after Tier 1, before making the final architecture call.

- [ ] **✓ Mehta S, Rastegari M.** *MobileViT: Light-weight, General-purpose,
  and Mobile-friendly Vision Transformer.* **ICLR 2022**. arxiv: 2110.02178.
  - **Why:** Excellent example of fusing local convolution with global
    attention efficiently. Directly relevant to your TensorRT deployment
    component — this kind of hybrid is what optimizes well on inference
    accelerators.
  - **Focus on:** The MobileViT block (Fig. 3) — that's the pattern you'd
    adapt for a 1-D EGM equivalent.

- [ ] **✓ Dai Z, Liu H, Le QV, Tan M.** *CoAtNet: Marrying Convolution and
  Attention for All Data Sizes.* **NeurIPS 2021**. arxiv: 2106.04803.
  - **Why:** Another clean example of CNN+attention hybridization, with a
    more principled scaling-law analysis. Useful for thinking about how to
    size a hybrid model for the relatively small noise-mixed dataset you'll have.

---

## Tier 4 — Domain-specific cardiac deep learning

Cardiac ML literature moves fast — read after you've made an architectural
choice, primarily to validate that choice against the recent literature.

- [ ] **✓ Sangha V, Mortazavi BJ, Haimovich AD, ... Glicksberg BS, Khera R.**
  *A foundational vision transformer improves diagnostic performance for
  electrocardiograms* (HeartBEiT). **npj Digital Medicine** 2023;6:103.
  arxiv: 2212.14040. PMID: 37280346.
  - **Why:** Foundation-model approach for ECG, pretrained via masked image
    modeling on 8.5M ECGs. The Khera lab at Yale is one of the most active
    in this space. Most relevant for understanding the foundation-model
    framing if you decide to do SSL pretraining.
  - **Focus on:** Pretraining setup, low-sample-size performance (their
    main claim), tokenization choice.

- [ ] **◇ Recent Karlsruhe-group atrial-substrate ML work** *(search seed)*
  - **Why:** Dössel and Loewe are openCARP collaborators and have published
    on ML for atrial substrate characterization. They're likely to have
    recent papers that build directly on the Sánchez et al. line of work
    you're already replicating.
  - **How to find:** Google Scholar search for `Loewe atrial fibrosis
    deep learning` and `Dössel atrial substrate machine learning`,
    sorted by year. Look at the openCARP citing-papers list on the
    project website.

- [ ] **◇ Recent Lozoya / Sermesant atrial ML work** *(search seed)*
  - **Why:** The Inria group has worked on machine-learning-based AF
    substrate characterization. Likely worth checking their recent output.
  - **How to find:** Search for `Lozoya Sermesant atrial fibrillation`
    and `Inria Asclepios cardiac machine learning`. The Sánchez paper
    might cite them.

- [ ] **◇ Hansen/Fedorov group on microstructural fibrosis EGM signatures**
  *(search seed)*
  - **Why:** The OSU group has done a lot of foundational work showing
    microstructural fibrosis patterns correlate with specific EGM
    morphology features. Less ML, more domain knowledge — useful for
    understanding what your model could in principle learn.
  - **How to find:** Search for `Hansen Fedorov atrial fibrosis
    electrogram`. The Hansen 2017 paper is already cited by Sánchez.

---

## Already covered in [[white-paper-references]]

These papers were also recommended for the white paper bibliography and are
tracked in the memory note linked above:

- Marchlinski 2000 — bipolar voltage threshold origin (ventricular).
- Sanders 2003 — atrial adoption of 0.5 mV threshold.
- Kosiuk PMID 30873619 — AF-rhythm-adjusted 0.2 mV threshold.
- Yamaguchi 2025 (PMID 41035701) — patient-specific relative voltage index.
- Sánchez 2021 — the paper this whole project is replicating/extending.

---

## Suggested journaling format (optional)

For papers you want to remember, a quick four-line summary often beats a
long writeup:

```
- Paper: <title>
- One-line takeaway: <claim that survives compression>
- Architectural idea to steal: <what would I copy?>
- What I would do differently for EGM: <where does this not translate?>
```
