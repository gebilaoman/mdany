import struct
import zlib
from pathlib import Path

import pytest


def make_png(path: Path, width: int = 4, height: int = 3) -> Path:
    """Write a small valid RGB PNG."""
    def chunk(typ: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data))

    raw = b"".join(b"\x00" + b"\x80\x80\x80" * width for _ in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    return path


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """A source directory with one Markdown file that uses a relative image path."""
    src = tmp_path / "src"
    make_png(src / "配图" / "图 1.png")
    (src / "文档.md").write_text(
        "# 测试文档\n\n"
        "## 表格\n\n| 名称 | 说明 |\n|---|---|\n| 甲 | 中文 |\n\n"
        "## 图片\n\n![截图](配图/图%201.png)\n\n"
        "## 代码\n\n```js\nconsole.log('中文')\n```\n",
        encoding="utf-8",
    )
    return src


@pytest.fixture
def png():
    """Factory fixture: png(path, width, height) writes a small valid PNG."""
    return make_png
