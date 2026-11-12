"""Change relative image paths to absolute paths.

After this step, PDF and DOCX output no longer depend on the current directory,
so intermediate files can live in the temporary directory (design 10.1, items 1 and 5).
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

import panflute as pf

from mdany.core.context import BuildContext
from mdany.core.document import Document

_URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]+:")  # 2+ chars, so "C:" is not a scheme


class ImagePaths:
    name = "image_paths"

    def apply(self, doc: Document, fmt, ctx: BuildContext) -> None:
        def action(elem, _ast):
            if not isinstance(elem, pf.Image) or not elem.url:
                return None
            url = elem.url
            if url.startswith("#") or _URL_SCHEME.match(url):
                return None
            path = Path(unquote(url))
            if not path.is_absolute():
                path = (doc.base_dir / path).resolve()
            if not path.exists():
                ctx.warn(f"{doc.source.name}: image not found: {url}")
            elem.url = str(path)
            return None

        doc.ast.walk(action)
