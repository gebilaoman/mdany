"""Build plan: which documents to convert, where each output goes, what to copy."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any

from mdany import MdanyError
from mdany.project.config import Config


@dataclass
class DocJob:
    source: Path
    rel: str                                   # path relative to the source directory
    options: dict[str, Any]
    outputs: dict[str, Path] = field(default_factory=dict)   # format -> output file


@dataclass
class CopyJob:
    source: Path
    rel: str
    outputs: dict[str, Path] = field(default_factory=dict)   # format -> destination


@dataclass
class Plan:
    docs: list[DocJob]
    copies: list[CopyJob]
    partial: bool                              # only some documents were asked for
    warnings: list[str] = field(default_factory=list)


def _name(template: str, rel: str, stem: str, filename: str, source_root: Path) -> str:
    p = PurePosixPath(rel)
    parent = p.parent.name if str(p.parent) != "." else source_root.name
    try:
        return template.format(parent=parent, stem=stem, name=filename)
    except (KeyError, IndexError) as e:
        raise MdanyError(
            f"name template {template!r}: unknown field {e}; use {{parent}} {{stem}} {{name}}",
            exit_code=2,
        ) from None


def _options(cfg: Config, rel: str) -> dict[str, Any]:
    opts = dict(cfg.defaults)
    for ov in cfg.overrides:
        if fnmatchcase(rel, ov.match):
            opts.update(ov.options)
    return opts


def _rel(cfg: Config, path: Path) -> str:
    return path.resolve().relative_to(cfg.source).as_posix()


def make(cfg: Config, formats: dict[str, str], only: list[str] | None = None) -> Plan:
    """formats: format name -> file extension, for the formats to build."""
    warnings: list[str] = []
    skip = set(cfg.skip)

    found: dict[str, Path] = {}
    for pattern in cfg.include:
        for path in sorted(cfg.source.glob(pattern)):
            if path.is_file():
                found.setdefault(_rel(cfg, path), path)
    for item in sorted(skip - set(found)):
        warnings.append(f"skip item matches no included file: {item}")

    if only:
        selected = {}
        for item in only:
            path = Path(item)
            candidates = [cfg.source / item] + ([path] if path.exists() else [])
            hit = next((c for c in candidates if c.is_file()), None)
            if hit is None:
                raise MdanyError(f"document not found: {item}", exit_code=2)
            rel = _rel(cfg, hit)
            selected[rel] = hit.resolve()
        found = selected
    else:
        found = {rel: p for rel, p in found.items() if rel not in skip}

    used: dict[Path, str] = {}

    def claim(out: Path, rel: str) -> Path:
        if out in used and used[out] != rel:
            raise MdanyError(
                f"two items write the same output {out.name}: {used[out]} and {rel}", exit_code=2
            )
        used[out] = rel
        return out

    docs = []
    for rel, path in sorted(found.items()):
        job = DocJob(source=path, rel=rel, options=_options(cfg, rel))
        base = _name(cfg.name, rel, path.stem, path.name, cfg.source)
        for fmt, ext in formats.items():
            job.outputs[fmt] = claim(cfg.outputs[fmt] / f"{base}{ext}", rel)
        docs.append(job)

    copies = []
    if not only:
        for rel in cfg.copy:
            src = cfg.source / rel
            if not src.exists():
                warnings.append(f"copy item not found: {rel}")
                continue
            job = CopyJob(source=src, rel=rel)
            base = _name(cfg.name, rel, src.name, src.name, cfg.source)
            for fmt in formats:
                job.outputs[fmt] = claim(cfg.outputs[fmt] / base, rel)
            copies.append(job)

    return Plan(docs=docs, copies=copies, partial=bool(only), warnings=warnings)
