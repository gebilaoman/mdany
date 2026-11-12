"""PDF format: syntax tree -> HTML (pandoc) -> PDF (engine)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import panflute as pf

from mdany import MdanyError, diagrams
from mdany.core import deps, pandoc
from mdany.core.context import BuildContext
from mdany.core.document import Document
from mdany.formats.pdf import fit, table_breaks
from mdany.formats.pdf import weasyprint as weasyprint_engine
from mdany.themes import Theme

# To add an engine: add a module with REQUIRES, STYLE_FILE and render(), then register it here.
ENGINES: dict[str, Any] = {
    "weasyprint": weasyprint_engine,
}


class PdfFormat:
    name = "pdf"
    ext = ".pdf"
    image_format = "svg"
    diagram_max_cm = None          # SVG; size is limited by the theme CSS

    def __init__(self, engine: str = "weasyprint"):
        if engine not in ENGINES:
            raise MdanyError(
                f"unknown PDF engine {engine!r}; choose from {list(ENGINES)}", exit_code=2
            )
        self.engine = ENGINES[engine]

    @property
    def requires(self) -> list[deps.Dep]:
        return [deps.PANDOC, *self.engine.REQUIRES, *diagrams.requires(self.image_format)]

    def page_break_before(self, block: pf.Block) -> list[pf.Block]:
        # A CSS break on the heading itself. A separate empty block would land on a new
        # page when the previous section fills its page exactly, and give a blank page.
        if isinstance(block, pf.Header):
            block.classes.append("mdany-page-break")
            return [block]
        return [pf.RawBlock('<div class="mdany-page-break"></div>', format="html"), block]

    def build(self, doc: Document, theme: Theme, out: Path, ctx: BuildContext) -> Path:
        work = Path(tempfile.mkdtemp(prefix="pdf-", dir=ctx.tmp))
        html = work / f"{doc.source.stem}.html"
        extra = [
            "--standalone",
            "--metadata", f"pagetitle={doc.title}",
            "--metadata", f"lang={doc.options.get('lang', 'zh-CN')}",   # CJK font fallback
            # Linking the theme CSS also stops pandoc from adding its default CSS
            # (max-width 36em etc.); `-V document-css=false` does not work (design 10.1 item 8).
            "--css", theme.file(self.engine.STYLE_FILE).resolve().as_uri(),
        ]
        if doc.options.get("toc"):
            extra += ["--toc", f"--toc-depth={doc.options.get('toc_depth', 2)}"]
        if block := doc.title_block(self.name):
            extra += ["--metadata", f"title={block}"]
        header = doc.options.get("header")
        if header:
            style = work / "header.html"
            content = json.dumps(str(header), ensure_ascii=False)  # a valid CSS string
            style.write_text(
                f"<style>@page {{ @top-center {{ content: {content}; }} }}</style>\n",
                encoding="utf-8",
            )
            extra += ["--include-in-header", str(style)]
        _file_uris(doc.ast)
        table_breaks.apply(doc.ast)
        if doc.options.get("fit_code_to_page"):
            fit.apply(doc.ast)
        pandoc.write(doc.ast, "html5", html, extra)
        # pandoc's footnote back-link is "↩︎" (U+21A9 U+FE0E). No font has a glyph for the
        # variation selector U+FE0E, so the engine embeds a .LastResort box. Drop it.
        text = html.read_text(encoding="utf-8")
        if "\ufe0e" in text:
            html.write_text(text.replace("\ufe0e", ""), encoding="utf-8")
        out.parent.mkdir(parents=True, exist_ok=True)
        self.engine.render(html, out)
        return out


def _file_uris(ast: pf.Doc) -> None:
    """Write local image paths as file:// URIs.

    The HTML engine reads src as a URL. A Windows path such as C:\\x\\a.png would
    parse as scheme "c"; a file URI is correct on every platform.
    """
    def action(elem, _ast):
        if isinstance(elem, pf.Image) and elem.url and Path(elem.url).is_absolute():
            elem.url = Path(elem.url).as_uri()

    ast.walk(action)
