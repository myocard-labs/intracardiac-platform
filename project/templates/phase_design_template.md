# Phase <N> — <short title> — Design Document

> _Template. Copy to `phases/phase_<N>/design.md` to start a phase; fill the `<...>` placeholders
> and delete these guidance blockquotes once a section is real. This document is the **spine of
> the phase** — it opens in Phase Planning and stays live through Cleanup. It is **owned by the
> project-lead chat**, which folds in the science section from the research chat and the estimates
> from each repo chat. Rule of the multi-chat scheme: anything not written here (or in a doc linked
> from here) does not officially exist. Relative links below are written for the instance location
> `phases/phase_<N>/`. See [chat_charters.md](../../project/chat_charters.md) and
> [phase_process.md](../../project/phase_process.md) for the roles + lifecycle this fits into._

**Phase:** <N>
**Title:** <short descriptive title>
**Status:** planning | implementation | science | cleanup | shipped | abandoned
**Started:** <YYYY-MM-DD> · **Target:** <rough date or TBD>
**Manifest:** [`manifest.json`](manifest.json) · **Paper:** <../../.../intracardiac-papers/papers/&lt;slug&gt;/ or "none">

---

## 1. Scientific objective

> _Owned by the research chat. The "why" of the phase, settled before any code is scoped._

- **Question / hypothesis:** <the scientific question this phase answers, or the hypothesis it tests>
- **Motivation:** <why now — the prior result or gap that makes this the next step>
- **Success criteria:** <what outcome makes this phase a success, stated so it's checkable. Be honest about what "success" means where IAFDB has no fibrosis ground truth — a directional/qualitative result, not a scored one.>
- **Out of scope:** <what this phase explicitly does NOT attempt, to hold the boundary>
- **Key references:** <papers driving the approach — link entries in [references/README.md](../../references/README.md)>

## 2. Core phase features

> _Owned by the project-lead chat. The science translated into code work, assigned to repos, with
> any new cross-repo data types called out. This is the science→code half of the traceability
> thread (science feature → code → repo → steps → PR → artifact → figure → paper claim)._

| # | Feature (capability) | Repo(s) | New data type? | Notes |
|---|---|---|---|---|
| C1 | <capability> | <repo> | <egm-contracts schema, or "none"> | <why / dependency> |

Any **new cross-repo data type** must be designed into
[`cross_artifact_linkage_design.md`](../../project/cross_artifact_linkage_design.md) and shipped via
egm-contracts before its consumers can use it.

## 3. Backlog items pulled in

> _Which existing per-repo backlog/roadmap items we're choosing to do this phase. Everything left
> unpicked stays in each repo's `roadmap.md`._

| # | Backlog item | Repo | Why it fits this phase |
|---|---|---|---|
| B1 | <item> | <repo> | <reason> |

## 4. Per-repo work + estimates

> _Each repo chat breaks its C-items and B-items into an ordered implementation plan (see
> [implementation_plan_template.md](../../project/templates/implementation_plan_template.md)) in its
> own repo, estimates it as a **range**, and the estimate flows up here. Record actuals at cleanup
> (§9) so future estimates calibrate._

| Repo | Items | Estimate (range) | Implementation plan |
|---|---|---|---|
| egm-contracts | <C1, …> | <e.g. 1–2 d> | <link to the repo's plan> |
| egm-data | | | |
| egm-signal | | | |
| egm-features | | | |
| iafdb-pipeline | | | |
| synthetic-egm-pipeline | | | |
| egm-classifier | | | |
| egm-studio | | | |
| **Phase total** | | **<sum range>** | |

## 5. Dependency + parallelization plan

> _The order the work must happen in (repo dependencies), and — importantly — what can run in
> parallel so several chats can be kicked off at once. Contracts/data changes usually gate their
> consumers; independent producers/consumers can then proceed simultaneously._

- **Wave 1 (gating):** <e.g. egm-contracts schema bump → egm-data re-pin>
- **Wave 2 (parallel):** <e.g. iafdb-pipeline ∥ synthetic-egm-pipeline ∥ an egm-classifier change>
- **Wave 3:** <e.g. egm-studio, once banks + predictions exist>

## 6. Data + analysis plan

> _Enumerate what the phase will generate. This is the seed for [`manifest.json`](manifest.json);
> each item gets a stable ID when it's actually produced (§ IDs in
> [cross_artifact_linkage_design.md](../../project/cross_artifact_linkage_design.md))._

- **Training banks (`tbank_`):** <which banks, from which producer configs>
- **Noise banks (`nbank_`):** <…>
- **Prediction banks (`lpred_` / `upred_`):** <which model × which eval bank; note the label-free IAFDB sanity-check banks explicitly>
- **Training runs (`run_`) / models (`model_`):** <which configs>
- **Figures:** <the figures expected for the paper — recipe + what each shows>
- **Other analysis:** <tables, ad-hoc results>

## 7. Risks + open questions

> _What could invalidate the phase, unknowns to resolve, decisions still pending. An unresolved
> high-risk item is a reason not to start implementation yet._

- <risk / open question — owner — status>

## 8. Progress

> _The bird's-eye view; fine-grained progress lives in each repo's `roadmap.md` + the manifest.
> Each stage has a definition of done — don't check it until the criteria are met._

- [ ] **Planning done** — §1–§6 filled; every affected repo's `roadmap.md` updated with this
  phase's items; estimates rolled up (§4); data + figure list enumerated (§6).
- [ ] **Implementation done** — all C/B items merged (+ tagged where a coordinated bump is needed);
  the constellation installs and the integration smoke test passes.
- [ ] **Data generated** — every bank / run in §6 produced and indexed in the manifest.
- [ ] **Science done** — planned figures + analyses generated; findings captured as observations in
  the manifest; the paper drafted.
- [ ] **Cleanup done** — every repo's [PR](../../project/pr_checklist.md) + [release](../../project/release_checklist.md)
  checks passed; platform docs updated; plan readjusted (§9); repos tagged for the phase release.

## 9. Outcomes + readjustment

> _Filled during Cleanup — what we learned and what it changes for future phases._

- **What we found:** <headline results; links to the paper + key observations>
- **Estimate vs. actual:** <how §4 held up — feeds future estimate calibration>
- **Changes to the plan:** <phases added / reordered / rescoped in [project_plan.md](../../project/project_plan.md) as a result>

## Revision history

> _Big changes to the phase plan only — a science pivot, a scope change, a new data type. Small
> edits go to git._

- <YYYY-MM-DD> — <change>
