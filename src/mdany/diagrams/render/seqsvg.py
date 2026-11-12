"""Sequence IR -> SVG (own renderer; graphviz has no lifelines).

Ported from itaskid mermaid2dot.py seq_svg(), which was checked on the submission material.
"""

from __future__ import annotations

import html

from mdany.diagrams.mermaid import Sequence
from mdany.diagrams.style import DiagramStyle

PITCH, BOX_W, BOX_H = 185, 168, 34
TOP, STEP = 12, 40


def to_svg(seq: Sequence, style: DiagramStyle) -> str:
    n = len(seq.participants)
    width = max(n * PITCH + 40, 320)
    height = TOP + BOX_H + STEP * len(seq.messages) + 28
    xs = {pid: 20 + BOX_W / 2 + i * PITCH for i, (pid, _) in enumerate(seq.participants)}
    font = html.escape(style.font, quote=True)

    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{font}">',
        '<defs><marker id="ah" markerWidth="9" markerHeight="8" refX="8" refY="4" '
        f'orient="auto"><path d="M0,0 L9,4 L0,8 z" fill="{style.stroke}"/></marker></defs>',
    ]
    box = f'fill="{style.fill}" stroke="{style.stroke}" stroke-width="1.2"'
    for pid, name in seq.participants:
        x = xs[pid]
        o.append(f'<rect x="{x - BOX_W / 2:.0f}" y="{TOP}" width="{BOX_W}" height="{BOX_H}" {box}/>')
        o.append(f'<text x="{x:.0f}" y="{TOP + 22}" text-anchor="middle" font-size="14" '
                 f'fill="{style.ink}">{html.escape(name)}</text>')
        o.append(f'<line x1="{x:.0f}" y1="{TOP + BOX_H}" x2="{x:.0f}" y2="{height - 16}" '
                 f'stroke="{style.lifeline}" stroke-width="1" stroke-dasharray="5 4"/>')

    y = TOP + BOX_H + STEP // 2
    for msg in seq.messages:
        xa, xb = xs[msg.src], xs[msg.dst]
        text = html.escape(msg.text)
        if msg.src == msg.dst:
            x0 = xa + 4
            o.append(f'<path d="M {x0:.0f},{y - 6} h 60 v 16 h -60" fill="none" '
                     f'stroke="{style.stroke}" stroke-width="1.3" marker-end="url(#ah)"/>')
            o.append(f'<text x="{x0 + 70:.0f}" y="{y + 6}" font-size="13" '
                     f'fill="{style.ink}">{text}</text>')
        else:
            dash = ' stroke-dasharray="6 4"' if msg.dashed else ""
            o.append(f'<line x1="{xa:.0f}" y1="{y}" x2="{xb:.0f}" y2="{y}" '
                     f'stroke="{style.stroke}" stroke-width="1.3"{dash} marker-end="url(#ah)"/>')
            o.append(f'<text x="{(xa + xb) / 2:.0f}" y="{y - 7}" text-anchor="middle" '
                     f'font-size="13" fill="{style.ink}">{text}</text>')
        y += STEP
    o.append("</svg>")
    return "\n".join(o)
