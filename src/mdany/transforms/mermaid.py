"""Replace ```mermaid code blocks with image paragraphs.

Format-dependent: the format decides svg or png, and an optional maximum size
for PNG diagrams (pHYs, design 1.2).
"""

from __future__ import annotations

import hashlib

import panflute as pf

from mdany import MdanyError
from mdany.core.context import BuildContext
from mdany.core.document import Document
from mdany.diagrams import DiagramStyle, UnsupportedSyntax, render
from mdany.images import phys


class Mermaid:
    name = "mermaid"

    def __init__(self, style: DiagramStyle | None = None):
        self.style = style or DiagramStyle()

    def apply(self, doc: Document, fmt, ctx: BuildContext) -> None:
        out_dir = ctx.tmpdir("diagrams")
        index = 0

        def action(elem, _ast):
            nonlocal index
            if not isinstance(elem, pf.CodeBlock) or "mermaid" not in elem.classes:
                return None
            index += 1
            key = hashlib.sha1(
                f"{fmt.image_format}|{self.style}|{elem.text}".encode()
            ).hexdigest()[:16]
            stem = out_dir / key
            path = stem.with_suffix(f".{fmt.image_format}")
            if not path.exists():
                try:
                    render(elem.text, stem, fmt.image_format, self.style)
                except UnsupportedSyntax as e:
                    raise MdanyError(
                        f"{doc.source}: mermaid block {index}, {e}\n"
                        "Supported: flowchart (nodes [] () {} (()) [()], edges --> -.->, "
                        "labels) and sequenceDiagram (participant, ->>, -->>). "
                        "Simplify the diagram or use an image."
                    ) from None
                box = getattr(fmt, "diagram_max_cm", None)
                if fmt.image_format == "png" and box:
                    phys.fit(path, *box)
            return pf.Para(pf.Image(url=str(path)))

        doc.ast.walk(action)
