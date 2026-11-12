import panflute as pf
import pytest

from mdany import MdanyError
from mdany.core.context import BuildContext
from mdany.core.document import Document
from mdany.formats.docx import DocxFormat
from mdany.formats.pdf import PdfFormat
from mdany.transforms.mermaid import Mermaid
from mdany.transforms.page_break import PageBreak
from mdany.transforms.title import Title


def _doc(tmp_path, text, name="文档.md", **options):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return Document.load(path, options)


# ---- title (design 5.4) ----

def test_title_from_leading_h1(tmp_path):
    doc = _doc(tmp_path, "# 数据库 *设计*\n\n正文\n")
    with BuildContext() as ctx:
        Title().apply(doc, None, ctx)
    assert doc.title == "数据库 设计"


def test_title_falls_back_to_file_name(tmp_path):
    doc = _doc(tmp_path, "正文在前\n\n# 后面的标题\n", name="2.5-业务流程图.md")
    with BuildContext() as ctx:
        Title().apply(doc, None, ctx)
    assert doc.title == "2.5-业务流程图"


def test_title_option_wins(tmp_path):
    doc = _doc(tmp_path, "# H1\n", title="指定标题")
    with BuildContext() as ctx:
        Title().apply(doc, None, ctx)
    assert doc.title == "指定标题"


# ---- page break ----

def _break_targets(doc):
    """Headings that start a new page: after a raw break block, or with the PDF class."""
    blocks = list(doc.ast.content)
    out = []
    for i, b in enumerate(blocks):
        if isinstance(b, pf.RawBlock):
            out.append(pf.stringify(blocks[i + 1]))
        elif isinstance(b, pf.Header) and "mdany-page-break" in b.classes:
            out.append(pf.stringify(b))
    return out


@pytest.mark.parametrize("fmt", [PdfFormat(), DocxFormat()])
def test_break_before_each_h2_except_first(tmp_path, fmt):
    doc = _doc(tmp_path, "# T\n\n## 第 1 页\n\na\n\n## 第 2 页\n\nb\n\n### 小节\n\n## 第 3 页\n",
               page_break_before="h2")
    with BuildContext() as ctx:
        PageBreak().apply(doc, fmt, ctx)
    assert _break_targets(doc) == ["第 2 页", "第 3 页"]


def test_no_option_no_break(tmp_path):
    doc = _doc(tmp_path, "## a\n\n## b\n")
    with BuildContext() as ctx:
        PageBreak().apply(doc, PdfFormat(), ctx)
    assert _break_targets(doc) == []


def test_bad_level_is_a_config_error(tmp_path):
    doc = _doc(tmp_path, "## a\n", page_break_before="h9")
    with BuildContext() as ctx, pytest.raises(MdanyError) as info:
        PageBreak().apply(doc, PdfFormat(), ctx)
    assert info.value.exit_code == 2


# ---- mermaid ----

FLOW = "```mermaid\nflowchart TD\n  A[开始] --> B[结束]\n```\n"


@pytest.mark.parametrize("fmt,suffix", [(PdfFormat(), ".svg"), (DocxFormat(), ".png")])
def test_mermaid_block_becomes_image(tmp_path, fmt, suffix):
    doc = _doc(tmp_path, "# T\n\n" + FLOW + "\n```js\nkeep()\n```\n")
    with BuildContext(keep_temp=True) as ctx:
        Mermaid().apply(doc, fmt, ctx)
        images = []
        doc.ast.walk(lambda e, _d: images.append(e.url) if isinstance(e, pf.Image) else None)
        codes = [b for b in doc.ast.content if isinstance(b, pf.CodeBlock)]
        assert len(images) == 1 and images[0].endswith(suffix)
        assert [c.text for c in codes] == ["keep()"]          # other code blocks stay


def test_unsupported_mermaid_names_file_block_and_line(tmp_path):
    doc = _doc(tmp_path, FLOW + "\n```mermaid\nflowchart TD\n  A --> B\n  subgraph X\n```\n")
    with BuildContext() as ctx, pytest.raises(MdanyError) as info:
        Mermaid().apply(doc, PdfFormat(), ctx)
    message = str(info.value)
    assert "文档.md" in message and "block 2" in message and "line 3" in message
    assert info.value.exit_code == 1
