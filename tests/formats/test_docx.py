import re
import zipfile

from mdany import pipeline
from mdany.core.context import BuildContext
from mdany.formats.docx import DocxFormat
from mdany.themes import Theme

EMU_PER_CM = 360000


def _build(tmp_path, text, **options):
    src = tmp_path / "文档.md"
    src.write_text(text, encoding="utf-8")
    out = tmp_path / "out" / "文档.docx"
    with BuildContext() as ctx:
        pipeline.convert(src, [(DocxFormat(), out)], Theme(), ctx, options)
    return zipfile.ZipFile(out)


def test_table_style_has_borders(tmp_path):
    z = _build(tmp_path, "# T\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    styles = z.read("word/styles.xml").decode()
    table_style = re.search(r'<w:style [^>]*w:styleId="Table"[^>]*>.*?</w:style>', styles, re.S).group(0)
    assert re.search(r'<w:insideV [^>]*w:val="single"', table_style)
    doc = z.read("word/document.xml").decode()
    assert '<w:tblStyle w:val="Table"' in doc
    # direct borders too, in schema order (before tblLook)
    tbl_pr = re.search(r"<w:tblPr>.*?</w:tblPr>", doc, re.S).group(0)
    assert tbl_pr.index("<w:tblBorders>") < tbl_pr.index("<w:tblLook")


def test_title_goes_to_properties_not_body(tmp_path):
    z = _build(tmp_path, "# 设计文档\n\n正文\n")
    assert "<dc:title>设计文档</dc:title>" in z.read("docProps/core.xml").decode()
    body = z.read("word/document.xml").decode()
    assert 'w:val="Title"' not in body
    assert re.findall(r"<w:t[^>]*>([^<]*)</w:t>", body).count("设计文档") == 1   # H1 only


def test_diagram_size_is_within_12_by_9_5_cm(tmp_path):
    tall = "\n".join(f"  N{i}[步骤{i}] --> N{i + 1}[步骤{i + 1}]" for i in range(14))
    z = _build(tmp_path, f"# T\n\n```mermaid\nflowchart TD\n{tall}\n```\n")
    doc = z.read("word/document.xml").decode()
    extents = [(int(cx), int(cy)) for cx, cy in re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"', doc)]
    assert len(extents) == 1
    cx, cy = extents[0]
    assert cx <= 12 * EMU_PER_CM + 1 and cy <= 9.5 * EMU_PER_CM + 1
    assert any(n.startswith("word/media/") for n in z.namelist())


def test_page_break_option(tmp_path):
    z = _build(tmp_path, "# T\n\n## 第 1 页\n\na\n\n## 第 2 页\n\nb\n", page_break_before="h2")
    assert z.read("word/document.xml").decode().count('<w:br w:type="page"/>') == 1


def test_no_local_paths_in_docx(tmp_path, png):
    png(tmp_path / "配图" / "a.png")
    z = _build(tmp_path, "# T\n\n![截图](配图/a.png)\n\n```mermaid\nflowchart TD\n  A --> B\n```\n")
    for name in z.namelist():
        data = z.read(name)
        assert str(tmp_path).encode() not in data, name
        assert b"/var/folders/" not in data and b"mdany-" not in data, name
    assert 'descr="a.png"' in z.read("word/document.xml").decode()


def test_title_block_only_for_listed_formats(tmp_path):
    z = _build(tmp_path, "# 设计文档\n\n正文\n", title_block=["pdf"])
    assert 'w:val="Title"' not in z.read("word/document.xml").decode()
    z = _build(tmp_path, "# 设计文档\n\n正文\n", title_block=True)
    body = z.read("word/document.xml").decode()
    assert 'w:val="Title"' in body and "文档" in body
