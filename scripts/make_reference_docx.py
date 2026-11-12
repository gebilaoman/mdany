"""Build themes/default/reference.docx from pandoc's default reference.docx.

Changes (design 1.1 item 4):
  - table style "Table": single borders on all cells, grey header row;
  - body text: 10.5 pt, East Asian font Microsoft YaHei (Word falls back on macOS).
Run: uv run python scripts/make_reference_docx.py
"""

import re
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mdany.core.pandoc import pandoc_path  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "src/mdany/themes/default/reference.docx"

BORDERS = (
    "<w:tblBorders>"
    + "".join(
        f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        for side in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    + "</w:tblBorders>"
)
HEADER_ROW = (
    '<w:tblStylePr w:type="firstRow"><w:rPr><w:b/></w:rPr><w:tcPr>'
    '<w:shd w:val="clear" w:color="auto" w:fill="F0F0F0"/></w:tcPr></w:tblStylePr>'
)


def patch_styles(xml: str) -> str:
    # Table style: borders + header row.
    m = re.search(r'<w:style w:type="table" w:default="1" w:styleId="Table">.*?</w:style>', xml, re.S)
    assert m, "Table style not found"
    style = m.group(0)
    # Schema order inside tblPr: ... tblInd, tblBorders, shd, tblLayout, tblCellMar ...
    style, n = re.subn(r"(<w:tblInd [^>]*/>)", r"\1" + BORDERS, style, count=1)
    assert n == 1, "tblInd not found"
    style = re.sub(r'<w:tblStylePr w:type="firstRow">.*?</w:tblStylePr>', HEADER_ROW, style, flags=re.S)
    xml = xml.replace(m.group(0), style)
    # Body defaults: East Asian font and 10.5 pt.
    xml = xml.replace('w:eastAsiaTheme="minorEastAsia"', 'w:eastAsia="Microsoft YaHei"', 1)
    xml = re.sub(r'(<w:rPrDefault>.*?)<w:sz w:val="24" />\s*<w:szCs w:val="24" />',
                 r'\1<w:sz w:val="21" /><w:szCs w:val="21" />', xml, count=1, flags=re.S)
    return xml


def main() -> None:
    raw = subprocess.run([pandoc_path(), "--print-default-data-file", "reference.docx"],
                         capture_output=True, check=True).stdout
    tmp = OUT.with_suffix(".src.docx")
    tmp.write_bytes(raw)
    with zipfile.ZipFile(tmp) as src, zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item)
            if item.filename == "word/styles.xml":
                data = patch_styles(data.decode("utf-8")).encode("utf-8")
            dst.writestr(item, data)
    tmp.unlink()
    print(f"written {OUT}")


if __name__ == "__main__":
    main()
