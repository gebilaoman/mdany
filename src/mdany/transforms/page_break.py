"""Insert a page break before each heading of a given level (option page_break_before).

Rule: break before every heading of that level except the first one, so the
first section shares the page with the title. Format-dependent: the format
decides how a heading starts a new page.
"""

from __future__ import annotations

import panflute as pf

from mdany import MdanyError
from mdany.core.context import BuildContext
from mdany.core.document import Document


def parse_level(value) -> int | None:
    if value in (None, "", False):
        return None
    text = str(value).lower().removeprefix("h")
    if not text.isdigit() or not 1 <= int(text) <= 6:
        raise MdanyError(f"page_break_before must be h1..h6, got {value!r}", exit_code=2)
    return int(text)


class PageBreak:
    name = "page_break"

    def apply(self, doc: Document, fmt, ctx: BuildContext) -> None:
        level = parse_level(doc.options.get("page_break_before"))
        if level is None:
            return
        out, seen = [], False
        for block in doc.ast.content:
            if isinstance(block, pf.Header) and block.level == level:
                if seen:
                    out.extend(fmt.page_break_before(block))
                    continue
                seen = True
            out.append(block)
        doc.ast.content = out
