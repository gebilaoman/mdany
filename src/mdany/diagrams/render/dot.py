"""Flowchart IR -> graphviz dot source -> SVG / PNG."""

from __future__ import annotations

import subprocess
from pathlib import Path

from mdany import MdanyError
from mdany.diagrams.mermaid import Flowchart
from mdany.diagrams.style import DiagramStyle

PNG_DPI = 192

_SHAPE_ATTRS = {
    "box": [],
    "round": ['style="rounded,filled"'],
    "diamond": ["shape=diamond"],
    "circle": ["shape=ellipse"],     # a true circle grows too large for CJK labels
    "cylinder": ["shape=cylinder"],
}


def _q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def to_dot(chart: Flowchart, style: DiagramStyle) -> str:
    font = _q(style.font)
    out = [
        "digraph G {",
        f"  rankdir={chart.direction};",
        # ortho does not support edge labels (labels float away) -> spline. Design 10.1 item 4.
        "  splines=spline;",
        "  nodesep=0.35; ranksep=0.5;",
        f"  node [fontname={font} fontsize=14 shape=box style=filled fillcolor={_q(style.fill)}"
        f" color={_q(style.stroke)} penwidth=1.2 margin=\"0.2,0.1\" fontcolor={_q(style.ink)}];",
        f"  edge [fontname={font} fontsize=12 color={_q(style.stroke)}"
        f" fontcolor={_q(style.ink)} arrowsize=0.7];",
    ]
    for node in chart.nodes.values():
        attrs = [f"label={_q(node.label)}", *_SHAPE_ATTRS[node.shape]]
        if node.shape == "diamond":
            attrs.append(f"fillcolor={_q(style.fill_decision)}")
        out.append(f"  {_q(node.id)} [{', '.join(attrs)}];")
    for edge in chart.edges:
        attrs = []
        if edge.label:
            attrs.append(f"label={_q(edge.label)}")
        if edge.style == "dotted":
            attrs.append("style=dashed")
        suffix = f" [{', '.join(attrs)}]" if attrs else ""
        out.append(f"  {_q(edge.src)} -> {_q(edge.dst)}{suffix};")
    out.append("}")
    return "\n".join(out)


def render(chart: Flowchart, style: DiagramStyle, out: Path) -> Path:
    """Write out.svg or out.png (by suffix) with graphviz."""
    fmt = out.suffix.lstrip(".")
    args = ["dot", f"-T{fmt}", "-o", str(out)]
    if fmt == "png":
        args.insert(1, f"-Gdpi={PNG_DPI}")
    try:
        proc = subprocess.run(
            args, input=to_dot(chart, style),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        raise MdanyError("graphviz `dot` not found. Run `mdany doctor`.", exit_code=2) from None
    if proc.returncode != 0:
        raise MdanyError(f"graphviz failed: {proc.stderr.strip()}")
    return out
