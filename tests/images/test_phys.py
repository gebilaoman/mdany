import struct

import pytest

from mdany.images import phys


def _phys_chunks(data: bytes) -> list[int]:
    found, i = [], 8
    while i < len(data):
        length = int.from_bytes(data[i:i + 4], "big")
        if data[i + 4:i + 8] == b"pHYs":
            found.append(struct.unpack(">I", data[i + 8:i + 12])[0])
        i += 12 + length
    return found


def test_small_image_keeps_base_dpi():
    assert phys.fit_dpi(400, 300, 12, 9.5, 192) == 192


def test_wide_image_is_limited_by_width():
    dpi = phys.fit_dpi(3000, 300, 12, 9.5, 192)
    assert 3000 * 2.54 / dpi == pytest.approx(12)


def test_tall_image_is_limited_by_height():
    dpi = phys.fit_dpi(300, 4000, 12, 9.5, 192)
    assert 4000 * 2.54 / dpi == pytest.approx(9.5)


def test_fit_writes_exactly_one_phys_chunk(tmp_path, png):
    path = png(tmp_path / "a.png", 2000, 100)
    phys.fit(path, 12, 9.5)
    phys.fit(path, 12, 9.5)                     # running twice must not add a second chunk
    chunks = _phys_chunks(path.read_bytes())
    assert len(chunks) == 1
    width_cm = 2000 / (chunks[0] * 0.0254) * 2.54
    assert 11.98 <= width_cm <= 12
    assert phys.size_px(path.read_bytes()) == (2000, 100)
