"""Processing flow for one document: read -> transforms -> each output format (design 4.4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mdany.core.context import BuildContext
from mdany.core.document import Document
from mdany.formats.base import Format
from mdany.themes import Theme
from mdany.transforms.base import Transform
from mdany.transforms.image_paths import ImagePaths
from mdany.transforms.mermaid import Mermaid
from mdany.transforms.page_break import PageBreak
from mdany.transforms.title import Title


def common_transforms(theme: Theme) -> list[Transform]:
    """Format-independent steps, in order."""
    return [ImagePaths(), Title()]


def format_transforms(theme: Theme) -> list[Transform]:
    """Steps that depend on the target format, in order."""
    return [Mermaid(theme.diagram_style()), PageBreak()]


def convert(
    source: Path,
    targets: list[tuple[Format, Path]],
    theme: Theme,
    ctx: BuildContext,
    options: dict[str, Any] | None = None,
) -> list[Path]:
    """Convert one Markdown file. targets: (format, output path) pairs."""
    doc = Document.load(source, options)
    for step in common_transforms(theme):
        step.apply(doc, None, ctx)

    outputs = []
    for fmt, out in targets:
        fdoc = doc.copy()
        for step in format_transforms(theme):
            step.apply(fdoc, fmt, ctx)
        outputs.append(fmt.build(fdoc, theme, out, ctx))
    return outputs
