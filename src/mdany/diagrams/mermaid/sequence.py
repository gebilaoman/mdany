"""sequenceDiagram subset parser.

Supported:
  participant X            participant X as Display name
  X->>Y: text              X-->>Y: text (dashed)       X->>X: text (self call)
  comments %% ...
Participants used in messages without a declaration are added in order of use.
Everything else raises UnsupportedSyntax.
"""

from __future__ import annotations

import re

from mdany.diagrams.mermaid import Message, Sequence, UnsupportedSyntax

_PARTICIPANT = re.compile(r"^participant\s+([A-Za-z0-9_]+)(?:\s+as\s+(.+))?$")
_MESSAGE = re.compile(r"^([A-Za-z0-9_]+)\s*(-->>|->>)\s*([A-Za-z0-9_]+)\s*:\s*(.*)$")


def parse(text: str) -> Sequence:
    seq = Sequence()
    known: set[str] = set()

    def add(pid: str, name: str | None = None) -> None:
        if pid not in known:
            known.add(pid)
            seq.participants.append((pid, (name or pid).strip()))

    seen_header = False
    for line_no, line in enumerate(text.splitlines(), 1):
        stmt = line.strip()
        if not stmt or stmt.startswith("%%"):
            continue
        if not seen_header:
            if stmt != "sequenceDiagram":
                raise UnsupportedSyntax(line_no, line, "expected `sequenceDiagram`")
            seen_header = True
            continue
        m = _PARTICIPANT.match(stmt)
        if m:
            add(m.group(1), m.group(2))
            continue
        m = _MESSAGE.match(stmt)
        if m:
            src, arrow, dst, msg = m.groups()
            add(src)
            add(dst)
            seq.messages.append(Message(src, dst, msg.strip(), dashed=arrow == "-->>"))
            continue
        raise UnsupportedSyntax(line_no, line, "unsupported statement")
    return seq
