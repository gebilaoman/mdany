"""Document: one Markdown source file and its syntax tree."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import panflute as pf

from mdany.core import pandoc

DEFAULT_OPTIONS: dict[str, Any] = {
    "toc": True,
    "toc_depth": 2,
}


@dataclass
class Document:
    source: Path                     # absolute path of the .md file
    ast: pf.Doc
    options: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_OPTIONS))
    title: str = ""                  # set by transforms; formats use it as document title

    @property
    def base_dir(self) -> Path:
        """Directory that relative paths in the document resolve against."""
        return self.source.parent

    @classmethod
    def load(cls, source: Path, options: dict[str, Any] | None = None) -> Document:
        source = source.resolve()
        opts = dict(DEFAULT_OPTIONS)
        opts.update(options or {})
        return cls(source=source, ast=pandoc.read(source), options=opts, title=source.stem)

    def title_block(self, fmt_name: str) -> str | None:
        """Text of the title block above the body, or None (option title_block, design 5.4).

        title_block = true shows it in every format; a list such as ["pdf"] limits it
        to those formats. The text is the file name without extension.
        """
        value = self.options.get("title_block")
        if value is True or (isinstance(value, list) and fmt_name in value):
            return self.source.stem
        return None

    def copy(self) -> Document:
        return Document(
            source=self.source,
            ast=copy.deepcopy(self.ast),
            options=dict(self.options),
            title=self.title,
        )
