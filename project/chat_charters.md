# Chat charters — who does what across the multi-chat project

Why the project is split across several AI chats, what each one is responsible for, and — just as
important — what each one does *not* touch. The phase lifecycle these chats operate is in
[phase_process.md](phase_process.md).

## Why multiple chats

A single chat can't hold the whole constellation in context: it drifts, forgets decisions made a
while ago, and burns tokens re-deriving what it already knew. Splitting the project by
responsibility splits the *context* each chat needs down to a tractable amount — one repo, or one
concern, at a time. It also mirrors how a real medical-device software org divides work
(research/clinical, program management, per-component engineering, medical writing), which is the
story this project exists to tell.

## Two rules that make it work

1. **Durable handoffs only.** Because the chats can't see each other's context, a decision isn't
   real until it's written into a document or memory — never left in a chat's head. The interfaces
   between chats are exactly four things: the **Phase Design Document**, the **per-repo roadmaps +
   implementation plans**, the **phase manifest**, and **memory**. Everything else in a chat is
   disposable working context.
2. **Single-writer per document.** Every durable doc has exactly one owning chat that writes it;
   the others read it. That's what stops two chats from silently overwriting each other. Owners are
   listed per chat below.

## The chats

### Research chat
- **Responsibility:** track down and read papers; drive the high-level scientific direction; assess
  the feasibility of a research path; plan each phase at the science level (what new capability the
  phase pursues, and why).
- **Owns (writes):** §1 (Scientific objective) of each Phase Design Doc; the `references/` reading
  index and `architecture_reading_list.md`.
- **Reads:** the literature; prior phases' outcomes.
- **Does NOT:** write code, assign work to repos, or produce implementation plans — it hands the
  settled science to the project-lead chat.

### Project-lead chat
- **Responsibility:** own the division of labor across repos; translate science-level features into
  concrete code chunks and assign each to the right repo (per [repo_charters.md](repo_charters.md));
  coordinate cross-repo data formats + integration testing; roll per-repo estimates up into a
  full-phase estimate; the in-the-weeds sequencing + planning.
- **Owns (writes):** the Phase Design Doc as a whole (folding in §1 from research and the estimates
  from the repo chats); the platform `project/` docs (`project_plan.md`, `repo_charters.md`,
  `cross_artifact_linkage_design.md`, the checklists, this doc); and **cross-cutting / project-wide
  memory**.
- **Reads:** every repo's roadmap + architecture, to know capabilities and the division of labor.
- **Does NOT:** write repo source code — it decides *what* and *where*; the repo chats decide *how*.

### Per-repo chats (one per Python repo)
- **Responsibility:** write the code for **their own repo, and only that repo**. Break their slice
  of a phase into an implementation plan with step-level estimates; those estimates flow up to the
  Phase Design Doc.
- **Owns (writes):** their repo's `src/`, tests, `docs/`, `project/architecture.md`, `roadmap.md`,
  `CHANGELOG.md`, and `project/phase_<N>_plan.md`; plus **repo-specific memory**.
- **Reads:** sibling repos as needed to understand a data format or an existing capability; the
  Phase Design Doc for their assignment.
- **Does NOT:** edit another repo, edit the Phase Design Doc directly (they feed estimates + status
  up to the project-lead), or make a decision that affects more than one repo — that escalates.

### Paper-writing chat
- **Responsibility:** know how biomedical / physiology papers are written; turn a phase's findings
  (observations, figures, metrics) into a coherent white-paper narrative across several write/edit
  passes.
- **Owns (writes):** `intracardiac-papers` content.
- **Reads:** the phase manifest with its observations + figures; the scientific objective +
  outcomes from the Phase Design Doc.
- **Does NOT:** drive the science direction or write pipeline code.

### Job-search / application chat
- **Responsibility:** build an understanding of Daniel's background (resume + past experience),
  translate the project's work into a biomedical-industry-targeted resume, then find and track
  suitable openings.
- **Owns (writes):** resume + application materials (kept outside the code repos).
- **Sits outside the phase loop** — it doesn't participate in the phase process; no phase work lives
  here.

## Cross-chat communication

**Memory is the channel.** A convention or decision written to memory by its owning chat is visible
to every other chat automatically — that's how the project-lead's cross-cutting decisions reach the
repo chats without a live conversation. To keep memory clean:

- **Project-lead** writes project-wide / cross-cutting memory (conventions, division of labor,
  cross-repo decisions).
- **Each repo chat** writes only its own repo-specific memory.
- Two chats should never write the same memory entry. If a repo chat discovers something
  cross-cutting, it flags it to the project-lead to record.

## Escalation

- A **repo chat** hitting a decision that touches more than one repo (a new data format, a change to
  a shared interface, where a piece of code belongs) → **project-lead chat**.
- A question about **scientific direction or feasibility** → **research chat**.
- Keep every decision at the lowest level that fully owns it: the project-lead pushes genuinely
  science-level calls back up to research, and genuinely repo-internal calls down to the repo chat.

## Booting a chat

Starting or resuming a chat means reading its charter here plus the durable docs it owns or needs —
the current Phase Design Doc, its repo's `project/` docs (for a repo chat), and memory. That is the
context; a chat should not try to reconstruct the whole project from scratch.
