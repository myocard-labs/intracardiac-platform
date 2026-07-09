# Quick start

Get the myocard-labs constellation running on your machine. There are two tracks:

- **User** — install the shipped tools and run them (train a classifier, render figures, open the desktop app). One virtual environment; no source changes.
- **Developer** — modify a package, run its tests, build the papers. One virtual environment **per repo you're working on**.

Both tracks share the same first step (clone the repos). For what each package *is*, see the [platform README](../README.md); to run the pipeline end to end once it's installed, see [`walkthrough.md`](walkthrough.md).

> **Pre-publish note.** The packages aren't on PyPI yet (planned for later — see [`project/project_plan.md`](../project/project_plan.md)). Each pins its siblings by exact git tag, so installing one pulls the others from GitHub automatically. Once published, `pip install myocard-egm-<name>` resolves the same tree from PyPI.

---

## Prerequisites

- **Python 3.10+** — 3.12 is what the project is developed and tested on.
- **git**.
- **A TeX distribution with `latexmk` and `biber`** — *developer track only, and only to build the papers.* See the papers repo's `docs/latex-setup.md`.
- **VS Code** *(recommended, not required)* — most development is done in it, but any editor works. See [Editor setup](#editor-setup-vs-code) below.

---

## 1. Clone the repos (both tracks)

Clone `intracardiac-platform` first — it carries the setup scripts — then run `clone_repos.sh` to fetch the rest as **siblings** (the layout the inter-repo git pins and tooling expect):

```bash
mkdir myocard-labs && cd myocard-labs        # your workspace root
git clone https://github.com/myocard-labs/intracardiac-platform.git
bash intracardiac-platform/scripts/clone_repos.sh          # add --ssh for SSH clones
```

`clone_repos.sh` is idempotent (skips repos already present) and lands everything as siblings:

```
myocard-labs/                     <- workspace root
├── egm-contracts/                foundation: schemas + typed models
├── egm-data/                     foundation: bank/artifact I/O
├── egm-signal/                   foundation: DSP primitives
├── egm-features/                 foundation: per-trace feature extraction
├── iafdb-pipeline/               producer: real EGMs (PhysioNet IAFDB)
├── synthetic-egm-pipeline/       producer: Finitewave synthetic EGMs
├── egm-classifier/               consumer: train / eval / export the CNN
├── egm-studio/                   consumer: desktop GUI + figure renderer
├── intracardiac-platform/        this repo: cross-cutting docs, phases, scripts
└── intracardiac-papers/          the LaTeX papers
```

---

## User track — run the shipped tools

One virtual environment at the workspace root. Install only the **application** repos — the two producers and two consumers. Their foundation dependencies (egm-contracts, egm-data, egm-signal, egm-features) are pulled in automatically from the git pins, so you never install those by hand.

```bash
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip

pip install \
  ./iafdb-pipeline \
  ./synthetic-egm-pipeline \
  "./egm-classifier[onnx]" \
  ./egm-studio
```

Install only the apps you actually need — e.g. drop `egm-classifier`/`egm-studio` if you only want to generate data, or drop the `[onnx]` extra if you won't export models to ONNX. `torch` (classifier), `PySide6` (studio), and `finitewave` (synthetic producer) are the heavy dependencies and only come in with their app.

**Verify the install:**

```bash
# imports resolve (apps pull in the foundation libraries transitively)
python -c "import myocard_iafdb_pipeline, myocard_synthetic_egm_pipeline, \
myocard_egm_classifier, myocard_egm_studio; print('imports ok')"

# console entry points respond
iafdb-inspect --help                # IAFDB producer
synthegm-generate-dataset --help    # synthetic producer
egm-class-train --help              # classifier
egm-studio-render --help            # headless figure renderer
egm-studio                          # launches the desktop app (needs a display)
```

If those respond, you're set — head to [`walkthrough.md`](walkthrough.md) to run the pipeline end to end.

---

## Developer track — modify + test

Work on a repo in **its own virtual environment**. Keeping environments separate (rather than one shared venv) means each repo installs exactly the dependencies declared in its own `pyproject.toml` — no cross-repo interference. Install editable, with the `dev` extra:

```bash
cd egm-classifier                       # the repo you're changing
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"                 # egm-classifier: use ".[dev,onnx]" to include ONNX export
```

That single command pulls the repo's runtime dependencies, its sibling packages (from the git pins), and its dev toolchain (ruff, mypy, pytest, …) — all from the `pyproject.toml`. Use `.[dev,onnx]` for **egm-classifier** if you're touching the export path.

To work on a sibling **at the same time** (say you're changing egm-contracts while developing egm-classifier), install that sibling editable into the same venv to shadow the pinned copy:

```bash
pip install -e ../egm-contracts        # your local egm-contracts now takes precedence
```

### Verify — run the fast tests

CI runs a **fast** set on every push to `development` and the **full** suite on PRs into `release`. The fast set is what you run locally while iterating; `scripts/run_fast_tests.sh` mirrors it (egm-studio's slow Qt-GUI tests are excluded via `-m "not gui"`, and it uses each repo's own `.venv`):

```bash
# from the workspace root, for every repo that has a .venv:
bash intracardiac-platform/scripts/run_fast_tests.sh
# or just the repo you're changing:
bash intracardiac-platform/scripts/run_fast_tests.sh egm-classifier
```

Run the **full** egm-studio suite (including the GUI tests) before opening a PR into `release`:

```bash
cd egm-studio && QT_QPA_PLATFORM=offscreen python -m pytest -q
```

### Before committing

Format, lint, and type-check the repo (a pre-commit hook enforces this):

```bash
ruff format . && ruff check . && mypy src
```

### Working across repos

Each package pins its siblings by exact git tag, so a change to a shared package means: bump its tag, then re-pin and re-test consumers in cascade order — `egm-contracts → egm-data → producers → consumers`. egm-contracts additionally regenerates code from its JSON Schemas; never hand-edit generated files. Each repo's CHANGELOG records the coordinated versions.

### Editor setup (VS Code)

Most development is done in **VS Code**, but it isn't required — any editor works (Neovim, PyCharm, …). The only hard requirements are the per-repo venv and the `ruff`/`mypy`/`pytest` tools installed above. If you use VS Code:

1. **Open the repo as its own folder** (`File ▸ Open Folder`) — one repo per window, matching the venv-per-repo setup.
2. **Select the interpreter**: `Ctrl/Cmd+Shift+P ▸ Python: Select Interpreter ▸ ./.venv/bin/python`. VS Code then uses that venv for running, debugging, and the Testing panel.
3. **Install extensions**: **Python** + **Pylance** (language server and type hints), **Ruff** (formatting + linting), and **LaTeX Workshop** if you build the papers.
4. **Enable format-on-save with Ruff** in your *user* settings (not the repo):

   ```json
   "[python]": {
     "editor.defaultFormatter": "charliermarsh.ruff",
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": { "source.organizeImports": "explicit" }
   },
   "python.testing.pytestEnabled": true
   ```
5. **Run tests** from the Testing panel (it auto-discovers pytest) or the integrated terminal.

Keep all editor config in your user settings. `.vscode/` is gitignored in every repo by design, so nothing here is committed — the setup above is per-developer.

### Build the papers (LaTeX)

The papers build with **make** (the repo's default), which is also the quickest way to confirm your TeX toolchain works:

```bash
cd intracardiac-papers
make                      # builds every paper's main + appendix PDFs
# make papers/phase1-5/   # just one paper
# make clean              # remove aux files (keeps the PDFs)
```

`make` needs a TeX distribution plus `latexmk` and `biber`; setup instructions are in the papers repo's `docs/latex-setup.md`.

---

## Troubleshooting

- **A dependency-resolver conflict when installing** — you shouldn't hit one, because the developer track uses a separate venv per repo. If two repos genuinely pin *conflicting* versions of a shared third-party package, that's a real misalignment: keep the venvs separate to keep working, and open a GitHub issue on the affected repo (org issue tracking to be enabled) so the pins get reconciled. *Dependency alignment across repos is a phase-closeout check* (captured in the project procedures doc).
- **`ModuleNotFoundError: myocard_*`** — the package (or a sibling) isn't installed in the active venv. In the user track, re-run the `pip install ./…` line; in the developer track, confirm you've activated that repo's `.venv` and run `pip install -e ".[dev]"`.
- **Qt: "could not connect to display" / "xcb plugin"** in tests or on a headless box — prefix the command with `QT_QPA_PLATFORM=offscreen`. The GUI (`egm-studio`) needs a real display; the renderer (`egm-studio-render`) is headless and doesn't.
- **`torch` download is huge / slow** — install the CPU wheel: `pip install torch --index-url https://download.pytorch.org/whl/cpu`. The project doesn't require a GPU.
- **A console script fails with a bad shebang after the venv moved** — call the tool as a module instead, e.g. `python -m pytest`.
