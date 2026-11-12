"""Build examples/demo end to end (a copy in tmp_path, so the repository stays clean)."""

import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pypdf
import pytest

from mdany.cli import main

DEMO = Path(__file__).resolve().parents[2] / "examples" / "demo"


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


@pytest.fixture
def demo(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "demo"
    shutil.copytree(DEMO, root, ignore=shutil.ignore_patterns("pdf", "word"))
    monkeypatch.chdir(root)
    return root


def test_build_demo(demo):
    before = _snapshot(demo / "md")
    assert main(["build"]) == 0

    expected = {"阶段1-1.1-功能演示", "阶段2-2.5-业务流程图", "阶段6-6.1-源代码摘录"}
    copies = {"阶段6-6.2-项目配置", "阶段6-6.4-数据库脚本.sql"}
    for out_dir, ext in [("pdf", ".pdf"), ("word", ".docx")]:
        names = {p.name for p in (demo / out_dir).iterdir()}
        assert names == {n + ext for n in expected} | copies | {".mdany-outputs.json"}
    assert (demo / "pdf/阶段6-6.2-项目配置/app.json").is_file()

    # skip list: the internal note is not converted
    assert not list(demo.glob("*/*内部说明*"))
    # the source directory is unchanged (design 2.3 item 6)
    assert _snapshot(demo / "md") == before

    # mermaid -> vector images, no mermaid source left in the PDF text
    flow = pypdf.PdfReader(demo / "pdf/阶段2-2.5-业务流程图.pdf")
    text = "".join(p.extract_text() for p in flow.pages)
    assert "flowchart" not in text and "sequenceDiagram" not in text
    assert "注册账号" in text and "同机回环" in text and "返回令牌" in text  # diagram text is real text

    # source excerpt: 3 sections -> 3 pages, each with the running header
    src = pypdf.PdfReader(demo / "pdf/阶段6-6.1-源代码摘录.pdf")
    assert len(src.pages) == 3
    assert all("示例软件 V1.0.0" in p.extract_text() for p in src.pages)

    # docx: 5 diagrams (1 in 1.1, 4 in 2.5) + 2 screenshots, all within the page
    z = zipfile.ZipFile(demo / "word/阶段2-2.5-业务流程图.docx")
    doc = z.read("word/document.xml").decode()
    assert len(re.findall(r"<wp:extent ", doc)) == 5


@pytest.mark.skipif(not shutil.which("pdffonts"), reason="poppler pdffonts not installed")
def test_demo_pdfs_have_no_tofu(demo):
    assert main(["build", "-f", "pdf"]) == 0
    for pdf in (demo / "pdf").glob("*.pdf"):
        fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
        assert "LastResort" not in fonts, pdf.name


def test_rebuild_removes_stale_output(demo):
    assert main(["build", "-f", "pdf"]) == 0
    (demo / "md/阶段2/2.5-业务流程图.md").unlink()
    (demo / "pdf/用户自己的文件.txt").write_text("keep me", encoding="utf-8")
    assert main(["build", "-f", "pdf"]) == 0
    assert not (demo / "pdf/阶段2-2.5-业务流程图.pdf").exists()
    assert (demo / "pdf/用户自己的文件.txt").exists()


def test_single_document_build_does_not_clean(demo):
    assert main(["build", "-f", "pdf"]) == 0
    assert main(["build", "-f", "pdf", "阶段1/1.1-功能演示.md"]) == 0
    assert (demo / "pdf/阶段6-6.1-源代码摘录.pdf").exists()


def test_bad_mermaid_fails_that_document_only(demo, capsys):
    bad = demo / "md/阶段2/2.9-坏图.md"
    bad.write_text("# 坏图\n\n```mermaid\nflowchart TD\n  subgraph X\n```\n", encoding="utf-8")
    assert main(["build", "-f", "pdf"]) == 1
    err = capsys.readouterr().err
    assert "2.9-坏图.md" in err and "subgraph" in err
    assert (demo / "pdf/阶段1-1.1-功能演示.pdf").exists()
