# Examples

End-to-end scripts demonstrating cross-component workflows. Each example pulls
from one or more component repos, so the examples become runnable only after
the component repos are tagged + installable from PyPI (or git+https during
pre-1.0 iteration).

## Planned examples

- `reproduce_v1_iafdb.sh` — clone all component repos at the versions used for v1, regenerate banks, train the classifier, eval against IAFDB, render the headline sim-to-real figure. The full end-to-end reproducibility story.
- `train_synthetic_only.sh` — minimal "I just want to train a model on a fresh synthetic bank" path. Demonstrates `synthetic-egm-pipeline` + `egm-classifier`.
- `inspect_predictions.sh` — generate predictions from a checkpoint + open them in `egm-studio`'s inspection tab. Demonstrates the predictions CSV/JSON contract.
- `render_paper_figures.sh` — drive the `egm-figures` CLI for every figure in the white paper. Connected to the `intracardiac-paper` repo's `reproduce.sh`.

## Conventions

- Bash, not Python, for the shell-level orchestration. Each script is short and obvious.
- All paths are relative to the script's directory; no `cd` to surprising places.
- Print every command before running it (`set -x`).
- Fail loudly (`set -euo pipefail`).
- No data files committed here — the scripts download or regenerate everything they need.
