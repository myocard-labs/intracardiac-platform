"""Self-tests for ``validate_manifest.py`` — throwaway phase fixtures.

Run with myocard-egm-contracts + myocard-egm-data importable, e.g.::

    pytest scripts/test_validate_manifest.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_manifest as vm  # noqa: E402


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _make_valid_phase(phases_dir: Path, phase: str = "1_5") -> dict[str, Any]:
    """Write a complete, internally-consistent phase folder. Returns its ids."""
    pdir = phases_dir / f"phase_{phase}"
    bank_id = f"tbank_synthetic_v{phase}_2026-06-27"
    obs_id = f"obs_high_entropy_p{phase}_2026-06-27"
    fig_id = f"fig_feature_distributions_p{phase}"
    paper_id = f"paper_phase_{phase}"

    (pdir / "banks").mkdir(parents=True, exist_ok=True)
    (pdir / "banks" / "tbank.h5").write_bytes(b"")  # external-style file, but present
    (pdir / "paper").mkdir(exist_ok=True)  # a paper directory the path resolves to
    _write_json(
        pdir / "observations" / f"{obs_id}.json",
        {
            "schema_version": "1",
            "id": obs_id,
            "date": "2026-06-27",
            "title": "t",
            "description": "d",
        },
    )
    _write_json(
        pdir / "figures" / f"{fig_id}.json",
        {
            "schema_version": "1",
            "id": fig_id,
            "description": "d",
            "recipe": "feature-distribution-overlay",
            "output": {"format": "pdf", "path": "x.pdf"},
        },
    )
    manifest = {
        "schema_version": "1",
        "phase": float(phase.replace("_", ".")) if "_" in phase else float(phase),
        "status": "in_progress",
        "egm_banks": [
            {
                "id": bank_id,
                "path": "banks/tbank.h5",
                "produced_by_package": "synthetic-egm-pipeline",
                "produced_by_version": "v0.2.0",
                "download_url": "https://example.com/tbank.h5",
            }
        ],
        "observations": [
            {
                "id": obs_id,
                "path": f"observations/{obs_id}.json",
                "produced_by_package": "egm-studio",
                "produced_by_version": "v0.1.0",
                "usage_tag": "informed_paper",
            }
        ],
        "figures": [
            {
                "id": fig_id,
                "path": f"figures/{fig_id}.json",
                "produced_by_package": "egm-studio",
                "produced_by_version": "v0.1.0",
                "consumes_banks": [bank_id],
                "consumes_observations": [obs_id],
                "usage_tag": "in_paper_main",
            }
        ],
        "papers": [
            {
                "id": paper_id,
                "path": "paper",
                "produced_by_package": "intracardiac-papers",
                "produced_by_version": "latest",
                "figures": [fig_id],
            }
        ],
    }
    _write_json(pdir / "manifest.json", manifest)
    return {
        "pdir": pdir,
        "manifest": manifest,
        "bank_id": bank_id,
        "obs_id": obs_id,
        "fig_id": fig_id,
    }


def _run(
    phases_dir: Path, only: str | None = None, release_gate: bool = False
) -> vm.Report:
    return vm.validate(phases_dir, only, release_gate, False)


def test_valid_phase_is_clean(tmp_path: Path) -> None:
    _make_valid_phase(tmp_path)
    r = _run(tmp_path)
    assert r.errors == [], r.errors
    assert r.warnings == [], r.warnings


def test_schema_invalid_manifest_errors(tmp_path: Path) -> None:
    f = _make_valid_phase(tmp_path)
    m = f["manifest"]
    m["egm_banks"][0]["id"] = "NOT-A-VALID-ID"
    _write_json(f["pdir"] / "manifest.json", m)
    r = _run(tmp_path)
    assert any("[A.6]" in e for e in r.errors), r.errors


def test_duplicate_id_across_phases_errors(tmp_path: Path) -> None:
    a = _make_valid_phase(tmp_path, "1_5")
    b = _make_valid_phase(tmp_path, "2")
    mb = b["manifest"]
    mb["egm_banks"][0]["id"] = a["bank_id"]  # collide with phase 1.5's bank
    mb["figures"][0]["consumes_banks"] = [a["bank_id"]]  # keep phase 2 self-consistent
    _write_json(b["pdir"] / "manifest.json", mb)
    r = _run(tmp_path)
    assert any("[A.2]" in e and a["bank_id"] in e for e in r.errors), r.errors


def test_dangling_in_repo_path_errors(tmp_path: Path) -> None:
    f = _make_valid_phase(tmp_path)
    (f["pdir"] / "observations" / f"{f['obs_id']}.json").unlink()
    r = _run(tmp_path)
    assert any("[A.3]" in e for e in r.errors), r.errors


def test_orphan_file_warns(tmp_path: Path) -> None:
    f = _make_valid_phase(tmp_path)
    _write_json(
        f["pdir"] / "observations" / "obs_orphan_2026-06-27.json",
        {
            "schema_version": "1",
            "id": "obs_orphan_2026-06-27",
            "date": "2026-06-27",
            "title": "t",
            "description": "d",
        },
    )
    r = _run(tmp_path)
    assert any("[A.4]" in w and "orphan" in w for w in r.warnings), r.warnings


def test_unresolved_reference_errors(tmp_path: Path) -> None:
    f = _make_valid_phase(tmp_path)
    m = f["manifest"]
    m["figures"][0]["consumes_banks"] = ["tbank_does_not_exist_2026-01-01"]
    _write_json(f["pdir"] / "manifest.json", m)
    r = _run(tmp_path)
    assert any("[A.5]" in e and "tbank_does_not_exist" in e for e in r.errors), r.errors


def test_missing_usage_tag_is_warning_then_fatal_under_release_gate(
    tmp_path: Path,
) -> None:
    f = _make_valid_phase(tmp_path)
    m = f["manifest"]
    del m["observations"][0]["usage_tag"]
    _write_json(f["pdir"] / "manifest.json", m)
    # Default mode: a warning, not fatal.
    r = _run(tmp_path)
    assert any("usage_tag" in w for w in r.warnings), r.warnings
    assert r.errors == []
    # --release-gate makes it fatal (non-zero exit).
    assert vm.main(["--phases-dir", str(tmp_path), "--release-gate"]) == 1


def test_release_gate_requires_download_url(tmp_path: Path) -> None:
    f = _make_valid_phase(tmp_path)
    m = f["manifest"]
    del m["egm_banks"][0]["download_url"]
    _write_json(f["pdir"] / "manifest.json", m)
    r = _run(tmp_path, release_gate=True)
    assert any("download_url" in w for w in r.warnings), r.warnings


def test_empty_phases_dir_is_clean_warning(tmp_path: Path) -> None:
    r = _run(tmp_path)
    assert r.errors == []
    assert any("nothing to validate" in w for w in r.warnings)
