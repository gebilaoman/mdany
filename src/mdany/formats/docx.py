"""DOCX format: syntax tree -> DOCX (pandoc, theme reference.docx)."""

from __future__ import annotations

import html
import re
import shutil
import zipfile
from pathlib import Path

import panflute as pf

from mdany import diagrams
from mdany.core import deps, pandoc
from mdany.core.context import BuildContext
from mdany.core.document import Document
from mdany.themes import Theme


class DocxFormat:
    name = "docx"
    ext = ".docx"
    image_format = "png"
    diagram_max_cm = (12.0, 9.5)   # pHYs box for diagrams (design 1.2)

    @property
    def requires(self) -> list[deps.Dep]:
        return [deps.PANDOC, *diagrams.requires(self.image_format)]

    def page_break_before(self, block: pf.Block) -> list[pf.Block]:
        return [pf.RawBlock('<w:p><w:r><w:br w:type="page"/></w:r></w:p>', format="openxml"), block]

    def build(self, doc: Document, theme: Theme, out: Path, ctx: BuildContext) -> Path:
        extra = ["--reference-doc", str(theme.file("reference.docx"))]
        if doc.options.get("toc"):
            extra += ["--toc", f"--toc-depth={doc.options.get('toc_depth', 2)}"]
        if block := doc.title_block(self.name):
            extra += ["--metadata", f"title={block}"]
        out.parent.mkdir(parents=True, exist_ok=True)
        pandoc.write(doc.ast, "docx", out, extra)
        _postprocess(out, doc.title)
        return out


_CNVPR_DESCR = re.compile(r'(<pic:cNvPr\b[^>]*?\bdescr=")([^"]*)(")')
_CORE_TITLE = re.compile(r"<dc:title\s*/>|<dc:title>.*?</dc:title>", re.S)
_TBL_PR = re.compile(r"<w:tblPr>(.*?)</w:tblPr>", re.S)
# Same borders as the "Table" style in themes/default/reference.docx.
_TBL_BORDERS = "<w:tblBorders>" + "".join(
    f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
    for side in ("top", "left", "bottom", "right", "insideH", "insideV")
) + "</w:tblBorders>"
# Elements that must follow tblBorders inside tblPr (OOXML schema order).
_AFTER_BORDERS = re.compile(r"<w:(?:shd|tblLayout|tblCellMar|tblLook|tblCaption|tblDescription)\b")


def _add_table_borders(m: re.Match) -> str:
    """Write the borders on each table directly. Word applies the table style, but
    some viewers (macOS Quick Look, older WPS) ignore table styles."""
    inner = m.group(1)
    if "<w:tblBorders>" in inner:
        return m.group(0)
    pos = _AFTER_BORDERS.search(inner)
    at = pos.start() if pos else len(inner)
    return f"<w:tblPr>{inner[:at]}{_TBL_BORDERS}{inner[at:]}</w:tblPr>"


def _strip_dirs(m: re.Match) -> str:
    """pandoc writes the image source path into pic:cNvPr/@descr. Our paths are
    absolute (transforms.image_paths), so keep only the file name: no local
    directory may end up in a submitted document."""
    value = m.group(2)
    name = re.split(r"[/\\]", value)[-1] if ("/" in value or "\\" in value) else value
    return m.group(1) + name + m.group(3)


def _postprocess(docx: Path, title: str) -> None:
    """Rewrite the DOCX once:
    - the title goes into the document properties only (passing it as pandoc
      metadata would also add a title paragraph above the H1, design 5.4);
    - image descriptions lose their directories;
    - every table gets direct borders.
    """
    tag = f"<dc:title>{html.escape(title, quote=False)}</dc:title>"
    tmp = docx.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item)
            if item.filename == "docProps/core.xml":
                xml = data.decode("utf-8")
                if _CORE_TITLE.search(xml):
                    xml = _CORE_TITLE.sub(tag, xml, count=1)
                else:
                    xml = xml.replace("</cp:coreProperties>", tag + "</cp:coreProperties>")
                data = xml.encode("utf-8")
            elif item.filename == "word/document.xml":
                xml = _CNVPR_DESCR.sub(_strip_dirs, data.decode("utf-8"))
                data = _TBL_PR.sub(_add_table_borders, xml).encode("utf-8")
            dst.writestr(item, data)
    shutil.move(tmp, docx)
