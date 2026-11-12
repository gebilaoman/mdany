import shutil
import subprocess

import pypdf
import pytest

from mdany import pipeline
from mdany.core.context import BuildContext
from mdany.formats.pdf import PdfFormat, fit
from mdany.themes import Theme


def _pdf(tmp_path, text, **options):
    src = tmp_path / "doc.md"
    src.write_text(text, encoding="utf-8")
    out = tmp_path / "doc.pdf"
    with BuildContext() as ctx:
        pipeline.convert(src, [(PdfFormat(), out)], Theme(), ctx, options)
    return out


def _source_excerpt(pages, lines=50, width=60):
    parts = ["# 源代码", "", "> 说明", ""]
    for p in range(1, pages + 1):
        parts += [f"## 第 {p} 页", "", "```"]
        parts += [f"// 第 {p} 页第 {i:02d} 行 " + "x" * width for i in range(1, lines + 1)]
        parts += ["```", ""]
    return "\n".join(parts)


def test_fit_code_to_page_gives_one_physical_page_per_section(tmp_path):
    out = _pdf(tmp_path, _source_excerpt(3), page_break_before="h2", fit_code_to_page=True,
               header="示例软件 V1.0.0", toc=False)
    reader = pypdf.PdfReader(out)
    assert len(reader.pages) == 3
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        assert "示例软件 V1.0.0" in text                 # running header
        assert f"第 {i} 页第 50 行" in text               # last line is on the same page


def test_without_fit_50_lines_overflow(tmp_path):
    out = _pdf(tmp_path, _source_excerpt(2), page_break_before="h2", toc=False)
    assert len(pypdf.PdfReader(out).pages) > 2


def test_font_size_shrinks_for_long_lines():
    short = "\n".join("x" * 40 for _ in range(50))
    long = "\n".join("x" * 130 for _ in range(50))
    assert fit.font_for(long, 600) < fit.font_for(short, 600)
    assert fit.MIN_PT <= fit.font_for(long, 600) <= fit.MAX_PT


def test_cjk_counts_double_width():
    assert fit.columns("ab") == 2 and fit.columns("中文") == 4


@pytest.mark.skipif(not shutil.which("pdffonts"), reason="poppler pdffonts not installed")
def test_no_tofu_for_cjk_in_code_and_footnotes(tmp_path):
    out = _pdf(tmp_path, "# T\n\n```\n// 第 1 页 源代码\n```\n\n脚注[^a]\n\n[^a]: 内容\n")
    fonts = subprocess.run(["pdffonts", str(out)], capture_output=True, text=True).stdout
    assert "LastResort" not in fonts


def test_section_that_fills_its_page_gives_no_blank_page(tmp_path):
    # Many sections of different lengths: a section that ends exactly at the page
    # bottom must not push the break onto an empty page.
    parts = ["# 源代码", ""]
    for p in range(1, 9):
        parts += [f"## 第 {p} 页", "", "```"] + [f"line {i} " + "y" * (20 + p * 12)
                                                 for i in range(1, 51)] + ["```", ""]
    out = _pdf(tmp_path, "\n".join(parts), page_break_before="h2", fit_code_to_page=True, toc=False)
    pages = pypdf.PdfReader(out).pages
    assert len(pages) == 8
    assert all("页" in page.extract_text() for page in pages)


def _words_beyond_right_margin(pdf):
    """Words whose right edge is past the text area (A4, right margin 16 mm)."""
    import re as _re
    right = (210 - 16) / 25.4 * 72 + 3
    out = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True).stdout
    return [m.group(2) for m in _re.finditer(r'xMax="([\d.]+)"[^>]*>([^<]*)</word>', out)
            if float(m.group(1)) > right]


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="poppler pdftotext not installed")
def test_long_values_do_not_push_table_off_the_page(tmp_path):
    # From itaskid 5.2 task_distributions: the enum type made the 说明 column fall off the page.
    rows = "\n".join(
        f"| downstream_project_id | enum('pending','accepted','rejected','cancelled') | 是 | "
        f"CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | "
        f"下游项目ID，关联 project_task_nodes.project_idfp {i} |"
        for i in range(3)
    )
    head = "| 字段 | 类型 | 可空 | 默认值 | 说明 |\n|---|---|---|---|---|\n"
    out = _pdf(tmp_path, "# T\n\n" + head + rows + "\n")
    assert _words_beyond_right_margin(out) == []
    text = pypdf.PdfReader(out).pages[0].extract_text()
    assert "downstream_project_id" in text          # identifiers are not split
    assert "project_idfp 2" in text.replace("​", "")   # last column is complete


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="poppler pdftotext not installed")
@pytest.mark.parametrize("lang", ["bash", ""])
def test_long_token_in_code_block_wraps(tmp_path, lang):
    token = "upload/{" + ",".join(f"folder{i:02d}" for i in range(20)) + "}"
    out = _pdf(tmp_path, f"# T\n\n```{lang}\n    mkdir -p {token}\n```\n")
    assert _words_beyond_right_margin(out) == []


def test_title_block_shows_file_name_above_h1(tmp_path):
    src = tmp_path / "5.1-系统架构设计文档.md"
    src.write_text("# 系统架构设计文档\n\n正文\n", encoding="utf-8")
    for option, expected in [(["pdf"], True), (["docx"], False), (None, False)]:
        out = tmp_path / "out.pdf"
        with BuildContext() as ctx:
            pipeline.convert(src, [(PdfFormat(), out)], Theme(), ctx, {"title_block": option, "toc": False})
        text = pypdf.PdfReader(out).pages[0].extract_text()
        assert ("5.1-系统架构设计文档" in text) is expected, option
        assert "系统架构设计文档" in text
