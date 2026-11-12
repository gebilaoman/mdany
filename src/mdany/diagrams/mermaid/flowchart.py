"""Flowchart subset parser.

Supported:
  header     flowchart|graph TD|TB|BT|LR|RL
  nodes      A   A[text]   A(text)   A{text}   A((text))   A[(text)]   A["text"]
  edges      -->   -->|label|   -.->   -.label.->   -.->|label|
  chains     A --> B --> C
  comments   %% ...
Everything else raises UnsupportedSyntax.
"""

from __future__ import annotations

import re

from mdany.diagrams.mermaid import Edge, Flowchart, Node, UnsupportedSyntax

_HEADER = re.compile(r"^(?:flowchart|graph)\s+(TD|TB|BT|LR|RL)\s*;?$")
_DIRECTION = {"TD": "TB", "TB": "TB", "BT": "BT", "LR": "LR", "RL": "RL"}

# Order matters: longer delimiters first.
_NODE = re.compile(
    r"""\s*(?P<id>[A-Za-z0-9_]+)
    (?:
        \(\((?P<circle>[^()]*)\)\)
      | \[\((?P<cylinder>[^()\]]*)\)\]
      | \[(?P<box>[^\]]*)\]
      | \{(?P<diamond>[^{}]*)\}
      | \((?P<round>[^()]*)\)
    )?\s*""",
    re.X,
)
_EDGE = re.compile(
    r"""\s*(?:
        -->(?:\s*\|(?P<l1>[^|]*)\|)?
      | -\.->(?:\s*\|(?P<l2>[^|]*)\|)?
      | -\.(?P<l3>[^.>][^>]*?)\.->
    )\s*""",
    re.X,
)
_SHAPES = ("circle", "cylinder", "box", "diamond", "round")


def _label(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        raw = raw[1:-1]
    return raw.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")


def _node(chart: Flowchart, m: re.Match) -> str:
    nid = m.group("id")
    node = chart.nodes.get(nid)
    if node is None:
        node = chart.nodes[nid] = Node(id=nid, label=nid)
    for shape in _SHAPES:
        text = m.group(shape)
        if text is not None:
            node.label = _label(text) or nid
            node.shape = shape
            break
    return nid


def parse(text: str) -> Flowchart:
    chart = Flowchart()
    seen_header = False
    for line_no, line in enumerate(text.splitlines(), 1):
        stmt = line.strip().rstrip(";")
        if not stmt or stmt.startswith("%%"):
            continue
        if not seen_header:
            m = _HEADER.match(stmt)
            if not m:
                raise UnsupportedSyntax(line_no, line, "expected `flowchart <direction>`")
            chart.direction = _DIRECTION[m.group(1)]
            seen_header = True
            continue

        pos = 0
        m = _NODE.match(stmt, pos)
        if not m or m.end() == pos:
            raise UnsupportedSyntax(line_no, line, "unsupported statement")
        prev = _node(chart, m)
        pos = m.end()
        while pos < len(stmt):
            e = _EDGE.match(stmt, pos)
            if not e:
                raise UnsupportedSyntax(line_no, line, "unsupported edge or node syntax")
            n = _NODE.match(stmt, e.end())
            if not n or n.end() == e.end():
                raise UnsupportedSyntax(line_no, line, "edge without target node")
            cur = _node(chart, n)
            label = e.group("l1") or e.group("l2") or e.group("l3") or ""
            style = "solid" if stmt[e.start():e.end()].strip().startswith("-->") else "dotted"
            chart.edges.append(Edge(src=prev, dst=cur, label=label.strip(), style=style))
            prev, pos = cur, n.end()
    if not seen_header:
        raise UnsupportedSyntax(0, "", "empty flowchart")
    return chart
