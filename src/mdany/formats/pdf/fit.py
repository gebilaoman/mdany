"""Fit each code block on one PDF page (option fit_code_to_page).

Used for source-code excerpts where each "page N" section must be one physical
page (for example 50 lines per page). For each code block, choose the largest
font size in [MIN_PT, MAX_PT] so that its lines, after wrapping, fit the page.

The page geometry matches themes/default/pdf.css (A4, margins 20 mm x 16 mm).
"""

from __future__ import annotations

import math
import unicodedata

import panflute as pf

CONTENT_W_PT = (210 - 2 * 16) / 25.4 * 72      # 504.6
CONTENT_H_PT = (297 - 2 * 20) / 25.4 * 72      # 728.5
# Horizontal space inside the content box that code text cannot use (pre padding,
# border, rounding). Calibrated with weasyprint 70 + Menlo: 6/7/8/9 pt give
# 132/113/99/88 columns, and this value reproduces them.
PRE_PAD_PT = 26
HEADING_PT = 70        # h2 with margins and rule, plus pre margins
FIRST_PAGE_EXTRA_PT = 150   # title (h1), intro paragraph above the first section
SAFETY_PT = 30
# A wrapped line breaks at word boundaries, so its continuation lines hold fewer
# characters than a full line. Count only this part of a line as usable.
WRAP_FILL = 0.85

MAX_PT, MIN_PT, STEP_PT = 9.0, 6.0, 0.25
LINE_HEIGHT = 1.3
MONO_ADVANCE = 0.602   # Menlo / DejaVu Sans Mono glyph width in em; CJK glyphs are 2 columns


def columns(line: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in line.expandtabs(4)
    )


def visual_lines(text: str, font_pt: float) -> int:
    cols = max(1, int((CONTENT_W_PT - PRE_PAD_PT) / (MONO_ADVANCE * font_pt)))
    total = 0
    for line in text.split("\n"):
        width = columns(line)
        total += 1 if width <= cols else math.ceil(width / (cols * WRAP_FILL))
    return total


def font_for(text: str, budget_pt: float) -> float:
    size = MAX_PT
    while size > MIN_PT:
        if visual_lines(text, size) * size * LINE_HEIGHT <= budget_pt:
            return size
        size -= STEP_PT
    return MIN_PT


def apply(ast: pf.Doc) -> None:
    """Set a font size on every top-level code block."""
    budget = CONTENT_H_PT - HEADING_PT - SAFETY_PT
    first = True
    for block in ast.content:
        if not isinstance(block, pf.CodeBlock) or "mermaid" in block.classes:
            continue
        size = font_for(block.text, budget - (FIRST_PAGE_EXTRA_PT if first else 0))
        first = False
        block.classes.append("mdany-fit")
        block.attributes["style"] = f"font-size:{size:g}pt;line-height:{LINE_HEIGHT}"
