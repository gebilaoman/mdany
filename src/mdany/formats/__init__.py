"""Format registry. To add a format: implement formats.base.Format and add one line here."""

from __future__ import annotations

from typing import Any

from mdany import MdanyError
from mdany.formats.base import Format
from mdany.formats.docx import DocxFormat
from mdany.formats.pdf import PdfFormat

FORMATS: dict[str, type] = {
    "pdf": PdfFormat,
    "docx": DocxFormat,
}


def names() -> list[str]:
    return list(FORMATS)


def create(name: str, **options: Any) -> Format:
    try:
        cls = FORMATS[name]
    except KeyError:
        raise MdanyError(f"unknown format {name!r}; choose from {names()}", exit_code=2) from None
    return cls(**options)
