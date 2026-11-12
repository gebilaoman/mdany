"""Add break points to long values in table cells (PDF only).

In automatic table layout, a column is at least as wide as its longest unbreakable
string. A value such as enum('pending','accepted','rejected','cancelled') then
pushes the table past the page edge, and the last column is cut off.

We insert a zero-width space (U+200B) after , ( . / when more text follows, so such
values can wrap there. Identifiers such as downstream_project_id contain none of
these characters and stay whole, so the field column keeps its full width.
"""

from __future__ import annotations

import re

import panflute as pf

ZWSP = "​"
_BREAK_AFTER = re.compile(r"([,(./])(?=[^\s​])")
MIN_LEN = 16      # short values never need a break


def _add(text: str) -> str:
    return _BREAK_AFTER.sub(r"\1" + ZWSP, text) if len(text) >= MIN_LEN else text


def apply(ast: pf.Doc) -> None:
    def in_table(elem) -> bool:
        parent = elem.parent
        while parent is not None:
            if isinstance(parent, pf.TableCell):
                return True
            parent = parent.parent
        return False

    def action(elem, _doc):
        if isinstance(elem, (pf.Str, pf.Code)) and in_table(elem):
            elem.text = _add(elem.text)

    ast.walk(action)
