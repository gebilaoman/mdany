"""Transform interface: one step of the syntax-tree processing chain."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from mdany.core.context import BuildContext
    from mdany.core.document import Document
    from mdany.formats.base import Format


class Transform(Protocol):
    name: str

    def apply(self, doc: Document, fmt: Format | None, ctx: BuildContext) -> None:
        """Change doc.ast in place. fmt is None for format-independent steps."""
        ...
