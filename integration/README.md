# Integration tests

Cross-repo smoke tests. The single canonical answer to "does the whole pipeline
still work after bumping component versions?"

These tests intentionally live in the meta repo (not in any component repo) because:

- They are the only place where every component is installed side-by-side.
- They protect against contract drift — if `egm-data` ships a breaking change without bumping the major, the integration test breaks before any consumer chat does.
- They are a clean target for CI to wire up later (currently manual + Pi-hosted optional).

## Planned tests

- `smoke.sh` — installs the latest tag of every component, generates a 10-trace synthetic mini-bank, trains a 1-epoch tiny classifier, runs `egm-eval-sim2real` against a 1-patient IAFDB slice, renders one figure. Total runtime target: under 5 minutes on a laptop. If this passes, the dependency DAG is intact.
- `contracts_round_trip.py` — write each `myocard-egm-contracts` schema to a tiny HDF5 / CSV / JSON file, read it back through `myocard-egm-data`, assert byte-equality of every field. Catches dtype / vlen-string regressions at the boundary.

## Not in scope here

- Per-component unit tests — those live in the component repos.
- Performance / timing tests — defer until there's a perf budget to defend.
- GPU tests — none of the components require a GPU for their unit tests; the integration tests follow the same rule (CPU-only) so they run anywhere.
