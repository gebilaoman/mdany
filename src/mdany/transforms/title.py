"""Decide the document title (design 5.4).

1. option `title` when set;
2. else the text of the first block when it is an H1 (the H1 stays in the body);
3. else the file name without extension.
"""

from __future__ import annotations

import panflute as pf

from mdany.core.context import BuildContext
from mdany.core.document import Document


class Title:
    name = "title"

    def apply(self, doc: Document, fmt, ctx: BuildContext) -> None:
        if doc.options.get("title"):
            doc.title = str(doc.options["title"])
            return
        blocks = doc.ast.content
        first = blocks[0] if len(blocks) else None
        if isinstance(first, pf.Header) and first.level == 1:
            doc.title = pf.stringify(first).strip() or doc.source.stem
        else:
            doc.title = doc.source.stem
