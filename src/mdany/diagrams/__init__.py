"""Diagrams: mermaid text -> image file. Knows nothing about output formats;
callers only ask for "svg" or "png"."""

from __future__ import annotations

from pathlib import Path

from mdany.core.deps import Dep, binary
from mdany.diagrams.mermaid import Flowchart, Sequence, UnsupportedSyntax, parse
from mdany.diagrams.render import dot, seqsvg
from mdany.diagrams.style import DiagramStyle

__all__ = ["UnsupportedSyntax", "render", "requires", "DiagramStyle"]

GRAPHVIZ = binary("dot", {
    "macos": "brew install graphviz",
    "debian": "sudo apt-get install -y graphviz",
    "fedora": "sudo dnf install -y graphviz",
    "windows": "choco install graphviz",
})
RSVG = binary("rsvg-convert", {
    "macos": "brew install librsvg",
    "debian": "sudo apt-get install -y librsvg2-bin",
    "fedora": "sudo dnf install -y librsvg2-tools",
    "windows": "choco install rsvg-convert",
})


def requires(image_format: str) -> list[Dep]:
    return [GRAPHVIZ, RSVG] if image_format == "png" else [GRAPHVIZ]


def render(text: str, out_stem: Path, image_format: str, style: DiagramStyle) -> Path:
    """Render one mermaid block to out_stem.svg / out_stem.png. Raises UnsupportedSyntax."""
    ir = parse(text)
    out = out_stem.with_suffix(f".{image_format}")
    if isinstance(ir, Flowchart):
        return dot.render(ir, style, out)
    assert isinstance(ir, Sequence)
    svg = out_stem.with_suffix(".svg")
    svg.write_text(seqsvg.to_svg(ir, style), encoding="utf-8")
    if image_format == "svg":
        return svg
    from mdany.diagrams.raster import svg_to_png

    return svg_to_png(svg, out)
