import pypdf

from mdany import pipeline
from mdany.core.context import BuildContext
from mdany.formats.pdf import PdfFormat
from mdany.themes import Theme


def test_pdf_contains_text_table_and_image(tmp_path, sample_project):
    out = tmp_path / "out" / "文档.pdf"
    with BuildContext() as ctx:
        pipeline.convert(sample_project / "文档.md", [(PdfFormat(), out)], Theme(), ctx)

    reader = pypdf.PdfReader(out)
    text = "".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) >= 1
    assert "测试文档" in text and "中文" in text
    assert sum(len(page.images) for page in reader.pages) >= 1


def test_pandoc_default_css_is_not_used(tmp_path, sample_project):
    with BuildContext(keep_temp=True) as ctx:
        pipeline.convert(
            sample_project / "文档.md", [(PdfFormat(), tmp_path / "a.pdf")], Theme(), ctx
        )
        html = next(ctx.tmp.glob("pdf-*/*.html")).read_text(encoding="utf-8")
    assert "36em" not in html
    assert "themes/default/pdf.css" in html


def test_no_local_paths_in_pdf(tmp_path, sample_project):
    out = tmp_path / "out" / "文档.pdf"
    with BuildContext() as ctx:
        pipeline.convert(sample_project / "文档.md", [(PdfFormat(), out)], Theme(), ctx)
    reader = pypdf.PdfReader(out)
    blobs = [str(reader.metadata or "")]
    for i in range(1, int(reader.trailer["/Size"])):     # every object in the file
        try:
            obj = reader.get_object(i)
        except Exception:
            continue
        if obj is None:
            continue
        blobs.append(str(obj))
        if hasattr(obj, "get_data"):
            try:
                blobs.append(obj.get_data().decode("latin-1"))
            except Exception:
                pass
    text = "\n".join(blobs)
    assert str(sample_project) not in text and "mdany-" not in text
