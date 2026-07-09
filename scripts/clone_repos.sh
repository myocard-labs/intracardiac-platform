#!/usr/bin/env bash
#
# Clone every myocard-labs repo as a sibling of intracardiac-platform (i.e. into the workspace
# root). This is the layout the inter-repo git pins and the tooling expect. Safe to re-run:
# repos already present are skipped.
#
# Run it after cloning intracardiac-platform (which carries this script):
#   bash intracardiac-platform/scripts/clone_repos.sh          # HTTPS (default)
#   bash intracardiac-platform/scripts/clone_repos.sh --ssh    # SSH (e.g. private clones)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"          # parent of intracardiac-platform = workspace root

BASE="https://github.com/myocard-labs"
[ "${1:-}" = "--ssh" ] && BASE="git@github.com:myocard-labs"

REPOS=(
  egm-contracts egm-data egm-signal egm-features
  iafdb-pipeline synthetic-egm-pipeline egm-classifier egm-studio
  intracardiac-platform intracardiac-papers
)

echo "Cloning into: $ROOT"
cd "$ROOT"
for r in "${REPOS[@]}"; do
  if [ -d "$r/.git" ]; then
    echo "  skip  $r (already present)"
  else
    echo "  clone $r"
    git clone --quiet "$BASE/$r.git"
  fi
done
echo "Done. Repos are siblings under $ROOT"
