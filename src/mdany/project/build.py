"""Run a build plan: convert documents, copy items, clean stale outputs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from mdany import MdanyError, pipeline
from mdany.core.context import BuildContext
from mdany.formats.base import Format
from mdany.project import outputs
from mdany.project.plan import Plan
from mdany.themes import Theme


@dataclass
class Result:
    converted: list[Path] = field(default_factory=list)
    copied: list[Path] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)   # (rel, message)


def run(
    plan: Plan, fmts: dict[str, Format], out_dirs: list[Path], theme: Theme, ctx: BuildContext
) -> Result:
    """out_dirs: every output directory of the formats being built (cleanup scope)."""
    result = Result()
    written: dict[Path, set[str]] = {}

    def note(out: Path) -> None:
        written.setdefault(out.parent, set()).add(out.name)

    for msg in plan.warnings:
        ctx.warn(msg)

    total = len(plan.docs)
    for i, job in enumerate(plan.docs, 1):
        targets = [(fmts[name], out) for name, out in job.outputs.items()]
        start = time.monotonic()
        try:
            for out in pipeline.convert(job.source, targets, theme, ctx, job.options):
                result.converted.append(out)
                note(out)
        except MdanyError as e:
            if e.exit_code == 2:         # environment problem: stop the whole build
                raise
            result.failed.append((job.rel, str(e)))
            ctx.info(f"[{i}/{total}] ✗ {job.rel}")
            continue
        ctx.info(f"[{i}/{total}] ✓ {job.rel} ({time.monotonic() - start:.1f}s)")

    for job in plan.copies:
        for dest in job.outputs.values():
            outputs.copy_item(job.source, dest)
            result.copied.append(dest)
            note(dest)
        ctx.info(f"copied {job.rel}")

    # A failed document keeps its old output: do not treat it as stale.
    failed = {rel for rel, _ in result.failed}
    for job in plan.docs:
        if job.rel in failed:
            for out in job.outputs.values():
                note(out)

    for out_dir in sorted(set(out_dirs)):
        result.removed += [
            f"{out_dir.name}/{n}"
            for n in outputs.finish(out_dir, written.get(out_dir, set()), plan.partial)
        ]
    return result
