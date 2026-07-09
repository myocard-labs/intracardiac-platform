#!/usr/bin/env python3
"""Scan-and-validate the per-phase manifests in intracardiac-platform.

Each science phase keeps a manifest at ``phases/phase_X/manifest.json``
that indexes every artifact the phase produced (the egm-contracts
cross-artifact-linkage design). egm-studio is the canonical curator; this
script is the scan-and-validate safety net that catches drift, and is the
release gate before any phase that ships a paper is declared done.

Checks (see ``project/cross_artifact_linkage_design.md`` section 8):

  A. Orphan / integrity  (always run; failures are fatal)
     A.1  stable-id format — enforced via A.6 (the regex lives in the schema)
     A.2  no duplicate artifact id across the whole project
     A.3  every manifest entry's ``path`` resolves to a real file
          (in-repo observation/figure files = error; external bank / model /
          paper targets = warning)
     A.4  no file under phase_X/observations|figures is missing from
          the manifest (orphan detection)
     A.5  every relationship pointer resolves to a known artifact id
     A.6  schema validity of every manifest / observation / figure_spec file
          (this is what enforces A.1)

  B. Load-bearing coverage  (warning by default; fatal under --release-gate)
     B.7/B.8  every observation / figure entry carries a usage_tag
     B.9      in-paper consistency: figures tagged in_paper_* are listed by a
              paper; observations tagged informed_paper are consumed by some
              figure

  C. Distribution URLs  (only under --release-gate)
     C.10/C.11  every bank / model entry has a download_url
     C.12       (with --check-urls) each download_url answers an HTTP HEAD

Exit code is non-zero when any *fatal* issue is found: errors are always
fatal; warnings are fatal only under ``--release-gate``.

Requires ``myocard-egm-contracts`` and ``myocard-egm-data`` importable.

Usage::

    python scripts/validate_manifest.py                 # all phases, warnings non-fatal
    python scripts/validate_manifest.py --phase 1_5     # one phase
    python scripts/validate_manifest.py --release-gate  # B + C become fatal
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib import error as _urlerror
from urllib import request as _urlrequest

from myocard_egm_contracts.validators import (
    validate_figure_spec,
    validate_observation,
    validate_phase_manifest,
)
from myocard_egm_data.phases import PhaseManifest, load_phase_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PHASES_DIR = REPO_ROOT / "phases"

IN_PAPER_TAGS = {"in_paper_main", "in_paper_supplementary"}

# Relationship fields per manifest section: which entry attributes point at
# OTHER artifact ids. Scalar = single id-or-None; list = list of ids. Field
# names mirror the future provenance-graph edge types (design section 3).
_SCALAR_REFS: dict[str, tuple[str, ...]] = {
    "egm_banks": ("model", "source_bank"),
    "training_runs": ("trained_on_bank", "produced_model"),
    "models": ("trained_from_run",),
}
_LIST_REFS: dict[str, tuple[str, ...]] = {
    "figures": ("consumes_banks", "consumes_models", "consumes_observations"),
    "papers": ("figures",),
}
_ALL_SECTIONS = (
    "egm_banks",
    "noise_banks",
    "training_runs",
    "models",
    "observations",
    "figures",
    "papers",
)
# Sections whose `path` points inside this repo (so a dangling path is an
# error). Banks / models / papers point at possibly-external artifacts (a
# producer's HDF5, the sibling intracardiac-papers repo), so a missing path
# there is only a warning.
_IN_REPO_SECTIONS = {"observations", "figures"}


@dataclass
class Report:
    """Accumulates issues, split by severity."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def merge(self, other: Report) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def _idstr(value: Any) -> str:
    """Normalize a contracts id field to a plain string.

    datamodel-code-generator emits ArtifactId / FigureId / PaperId as RootModel
    subclasses (the value lives in ``.root`` and the instances are unhashable),
    so every id must be unwrapped before it is hashed or compared.
    """
    return value.root if hasattr(value, "root") else str(value)


def _sections(manifest: PhaseManifest) -> dict[str, list[Any]]:
    """Return ``{section_name: [entries]}`` with None lists normalized to []."""
    return {name: list(getattr(manifest, name) or []) for name in _ALL_SECTIONS}


def _iter_defined_ids(
    manifest: PhaseManifest, phase_label: str
) -> list[tuple[str, str, str]]:
    """Every artifact id this manifest *defines*, as (id, section, phase)."""
    out: list[tuple[str, str, str]] = []
    for section, entries in _sections(manifest).items():
        for entry in entries:
            out.append((_idstr(entry.id), section, phase_label))
    return out


def _iter_references(
    manifest: PhaseManifest, phase_label: str
) -> list[tuple[str, str, str, str]]:
    """Every relationship pointer, as (referrer_id, field, target_id, phase)."""
    out: list[tuple[str, str, str, str]] = []
    sections = _sections(manifest)
    for section, fields in _SCALAR_REFS.items():
        for entry in sections[section]:
            for fname in fields:
                target = getattr(entry, fname, None)
                if target is not None:
                    out.append((_idstr(entry.id), fname, _idstr(target), phase_label))
    for section, fields in _LIST_REFS.items():
        for entry in sections[section]:
            for fname in fields:
                for target in getattr(entry, fname, None) or []:
                    out.append((_idstr(entry.id), fname, _idstr(target), phase_label))
    return out


def _resolve(path_str: str, manifest_path: Path) -> Path:
    """Resolve an entry path relative to the manifest's directory."""
    p = Path(path_str)
    return p if p.is_absolute() else (manifest_path.parent / p)


# ---------------------------------------------------------------------------
# Per-phase collection (Check A.6 schema validity happens here; because the
# stable-id regex lives in the schema, A.6 also subsumes A.1 id-format).
# ---------------------------------------------------------------------------


@dataclass
class PhaseData:
    label: str
    manifest_path: Path
    manifest: PhaseManifest | None  # None if it failed schema validation


def collect_phase(phase_dir: Path, report: Report) -> PhaseData:
    """Validate + load one phase's manifest and its referenced sub-files."""
    label = phase_dir.name.removeprefix("phase_")
    manifest_path = phase_dir / "manifest.json"
    if not manifest_path.is_file():
        report.error(f"[A.6] {phase_dir.name}: no manifest.json")
        return PhaseData(label, manifest_path, None)

    # A.6 schema validity of the manifest (also enforces the A.1 id-pattern regexes).
    result = validate_phase_manifest(manifest_path)
    if not result.ok:
        for issue in result.issues:
            report.error(f"[A.6] {manifest_path}: {issue}")
        return PhaseData(label, manifest_path, None)

    manifest = load_phase_manifest(manifest_path)

    # A.6 schema validity of every referenced observation / figure_spec file.
    for obs_entry in list(manifest.observations or []):
        fpath = _resolve(obs_entry.path, manifest_path)
        if fpath.is_file():
            r = validate_observation(fpath)
            for issue in r.issues:
                report.error(f"[A.6] {fpath}: {issue}")
    for fig_entry in list(manifest.figures or []):
        fpath = _resolve(fig_entry.path, manifest_path)
        if fpath.is_file():
            r = validate_figure_spec(fpath)
            for issue in r.issues:
                report.error(f"[A.6] {fpath}: {issue}")

    return PhaseData(label, manifest_path, manifest)


# ---------------------------------------------------------------------------
# Check A.3 — path validity
# ---------------------------------------------------------------------------


def check_paths(phase: PhaseData, report: Report) -> None:
    assert phase.manifest is not None
    for section, entries in _sections(phase.manifest).items():
        for entry in entries:
            fpath = _resolve(entry.path, phase.manifest_path)
            # exists(): file for banks/models/observations/figures, directory
            # for a paper entry.
            if fpath.exists():
                continue
            msg = f"[A.3] phase {phase.label}: {section} '{_idstr(entry.id)}' path does not resolve: {entry.path}"
            if section in _IN_REPO_SECTIONS:
                report.error(msg)
            else:
                report.warn(msg + " (external producer artifact?)")


# ---------------------------------------------------------------------------
# Check A.4 — orphan files under observations/ and figure_specs/
# ---------------------------------------------------------------------------


def check_orphans(phase: PhaseData, report: Report) -> None:
    assert phase.manifest is not None
    phase_dir = phase.manifest_path.parent
    indexed = {
        _resolve(entry.path, phase.manifest_path).resolve()
        for entry in (
            list(phase.manifest.observations or []) + list(phase.manifest.figures or [])
        )
    }
    for sub in ("observations", "figures"):
        subdir = phase_dir / sub
        if not subdir.is_dir():
            continue
        for fpath in sorted(subdir.glob("*.json")):
            if fpath.resolve() not in indexed:
                report.warn(
                    f"[A.4] phase {phase.label}: {sub}/{fpath.name} is on disk "
                    "but not referenced by the manifest (orphan)"
                )


# ---------------------------------------------------------------------------
# Check B — usage-tag coverage + in-paper consistency
# ---------------------------------------------------------------------------


def check_usage(phase: PhaseData, report: Report) -> None:
    assert phase.manifest is not None
    sections = _sections(phase.manifest)

    # B.7 (observations) / B.8 (figures) — every entry carries a usage_tag.
    for section, code in (("observations", "B.7"), ("figures", "B.8")):
        for entry in sections[section]:
            if getattr(entry, "usage_tag", None) is None:
                report.warn(
                    f"[{code}] phase {phase.label}: {section} '{_idstr(entry.id)}' has no usage_tag"
                )

    # B.9 — in-paper consistency.
    paper_figures = {
        _idstr(fig) for paper in sections["papers"] for fig in (paper.figures or [])
    }
    for fig in sections["figures"]:
        tag = getattr(fig.usage_tag, "value", fig.usage_tag)
        if tag in IN_PAPER_TAGS and _idstr(fig.id) not in paper_figures:
            report.warn(
                f"[B.9] phase {phase.label}: figure '{_idstr(fig.id)}' is tagged "
                f"'{tag}' but no paper lists it"
            )

    consumed_obs = {
        _idstr(obs)
        for fig in sections["figures"]
        for obs in (fig.consumes_observations or [])
    }
    for obs in sections["observations"]:
        tag = getattr(obs.usage_tag, "value", obs.usage_tag)
        if tag == "informed_paper" and _idstr(obs.id) not in consumed_obs:
            report.warn(
                f"[B.9] phase {phase.label}: observation '{_idstr(obs.id)}' is tagged "
                "'informed_paper' but no figure consumes it"
            )


# ---------------------------------------------------------------------------
# Check C — distribution URLs (release-gate only)
# ---------------------------------------------------------------------------


def check_distribution(phase: PhaseData, report: Report, check_urls: bool) -> None:
    assert phase.manifest is not None
    sections = _sections(phase.manifest)
    # C.10 covers both bank kinds (egm + noise); C.11 covers models.
    for section, code in (
        ("egm_banks", "C.10"),
        ("noise_banks", "C.10"),
        ("models", "C.11"),
    ):
        for entry in sections[section]:
            url = getattr(entry, "download_url", None)
            if url is None:
                report.warn(
                    f"[{code}] phase {phase.label}: {section} '{_idstr(entry.id)}' has no "
                    "download_url (needed to reproduce a shipped paper)"
                )
            elif check_urls and not _head_ok(str(url)):
                report.warn(
                    f"[C.12] phase {phase.label}: {_idstr(entry.id)} download_url unreachable: {url}"
                )


def _head_ok(url: str) -> bool:
    req = _urlrequest.Request(url, method="HEAD")
    try:
        with _urlrequest.urlopen(req, timeout=10) as resp:  # noqa: S310 - explicit https expected
            return 200 <= resp.status < 400
    except (_urlerror.URLError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def validate(
    phases_dir: Path, only_phase: str | None, release_gate: bool, check_urls: bool
) -> Report:
    report = Report()
    phase_dirs = sorted(d for d in phases_dir.glob("phase_*") if d.is_dir())
    if only_phase is not None:
        wanted = f"phase_{only_phase}"
        phase_dirs = [d for d in phase_dirs if d.name == wanted]
        if not phase_dirs:
            report.error(f"no phase folder named {wanted!r} under {phases_dir}")
            return report
    if not phase_dirs:
        report.warn(
            f"no phase_* folders found under {phases_dir} (nothing to validate)"
        )
        return report

    phases = [collect_phase(d, report) for d in phase_dirs]
    loaded = [p for p in phases if p.manifest is not None]

    # A.2 — duplicate ids across the whole project.
    all_ids: list[tuple[str, str, str]] = []
    for p in loaded:
        assert p.manifest is not None  # filtered above; narrows for the id helpers
        all_ids.extend(_iter_defined_ids(p.manifest, p.label))
    counts = Counter(art_id for art_id, _section, _phase in all_ids)
    for art_id, n in counts.items():
        if n > 1:
            where = ", ".join(
                f"{phase}/{section}" for aid, section, phase in all_ids if aid == art_id
            )
            report.error(
                f"[A.2] duplicate artifact id {art_id!r} defined {n}x ({where})"
            )

    defined = {art_id for art_id, _s, _p in all_ids}

    for p in loaded:
        assert p.manifest is not None
        check_paths(p, report)
        check_orphans(p, report)
        # A.5 — cross-reference integrity.
        for referrer, fname, target, phase_label in _iter_references(
            p.manifest, p.label
        ):
            if target not in defined:
                report.error(
                    f"[A.5] phase {phase_label}: {referrer!r}.{fname} -> {target!r} "
                    "does not resolve to any known artifact id"
                )
        check_usage(p, report)
        if release_gate:
            check_distribution(p, report, check_urls)

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--phase", default=None, help="limit to one phase (folder suffix, e.g. 1_5)"
    )
    parser.add_argument(
        "--release-gate",
        action="store_true",
        help="treat usage-coverage (B) and distribution-url (C) issues as fatal",
    )
    parser.add_argument(
        "--check-urls",
        action="store_true",
        help="under --release-gate, HEAD-request each download_url (slow; needs network)",
    )
    parser.add_argument(
        "--phases-dir",
        type=Path,
        default=DEFAULT_PHASES_DIR,
        help=f"override the phases directory (default: {DEFAULT_PHASES_DIR})",
    )
    args = parser.parse_args(argv)

    report = validate(args.phases_dir, args.phase, args.release_gate, args.check_urls)

    for w in report.warnings:
        print(f"WARNING  {w}")
    for e in report.errors:
        print(f"ERROR    {e}")

    fatal = len(report.errors) + (len(report.warnings) if args.release_gate else 0)
    print(
        f"\n{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
        f"{' — warnings are fatal under --release-gate' if args.release_gate else ''}."
    )
    if fatal:
        print("FAILED")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
