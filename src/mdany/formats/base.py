"""Format interface: one output format."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import panflute as pf

    from mdany.core.context import BuildContext
    from mdany.core.deps import Dep
    from mdany.core.document import Document
    from mdany.themes import Theme


class Format(Protocol):
    name: str               # value of -f
    ext: str                # ".pdf"
    image_format: str       # "svg" or "png": what diagrams must produce for this format
    diagram_max_cm: tuple[float, float] | None   # PNG diagram box (pHYs); None = no limit

    @property
    def requires(self) -> list[Dep]: ...

    def page_break_before(self, block: pf.Block) -> list[pf.Block]:
        """Return the blocks that replace `block` so that it starts a new page."""
        ...

    def build(self, doc: Document, theme: Theme, out: Path, ctx: BuildContext) -> Path: ...
