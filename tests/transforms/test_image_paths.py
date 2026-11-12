import panflute as pf

from mdany.core.context import BuildContext
from mdany.core.document import Document
from mdany.transforms.image_paths import ImagePaths


def _urls(doc: Document) -> list[str]:
    urls = []
    doc.ast.walk(lambda e, _d: urls.append(e.url) if isinstance(e, pf.Image) else None)
    return urls


def test_relative_paths_become_absolute(tmp_path, sample_project):
    md = sample_project / "文档.md"
    md.write_text(
        md.read_text(encoding="utf-8")
        + "\n![远程](https://example.com/a.png)\n![缺失](missing.png)\n",
        encoding="utf-8",
    )
    doc = Document.load(md)
    with BuildContext() as ctx:
        ImagePaths().apply(doc, None, ctx)
        warnings = list(ctx.warnings)

    urls = _urls(doc)
    assert urls[0] == str((sample_project / "配图" / "图 1.png").resolve())
    assert urls[1] == "https://example.com/a.png"
    assert urls[2] == str((sample_project / "missing.png").resolve())
    assert len(warnings) == 1 and "missing.png" in warnings[0]
