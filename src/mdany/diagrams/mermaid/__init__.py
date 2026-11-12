"""Mermaid parsers: mermaid text -> intermediate structure (IR).

Only a declared subset is supported. Any other line raises UnsupportedSyntax,
so that a diagram is never drawn with silently missing parts.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class UnsupportedSyntax(Exception):
    def __init__(self, line_no: int, line: str, reason: str):
        super().__init__(f"line {line_no}: {reason}: {line.strip()!r}")
        self.line_no = line_no
        self.line = line
        self.reason = reason


# ---- flowchart IR -----------------------------------------------------------

@dataclass
class Node:
    id: str
    label: str
    shape: str = "box"        # box | round | diamond | circle | cylinder


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    style: str = "solid"      # solid | dotted


@dataclass
class Flowchart:
    direction: str = "TB"     # TB | LR | RL | BT
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)


# ---- sequence IR ------------------------------------------------------------

@dataclass
class Message:
    src: str
    dst: str
    text: str
    dashed: bool = False


@dataclass
class Sequence:
    participants: list[tuple[str, str]] = field(default_factory=list)  # (id, display name)
    messages: list[Message] = field(default_factory=list)


def parse(text: str) -> Flowchart | Sequence:
    """Parse one mermaid block. The first non-empty line selects the diagram type."""
    from mdany.diagrams.mermaid import flowchart, sequence

    for line_no, line in enumerate(text.splitlines(), 1):
        head = line.strip()
        if not head or head.startswith("%%"):
            continue
        if head == "sequenceDiagram":
            return sequence.parse(text)
        if head.split()[0] in ("flowchart", "graph"):
            return flowchart.parse(text)
        raise UnsupportedSyntax(line_no, line, "unsupported diagram type")
    raise UnsupportedSyntax(0, "", "empty diagram")
