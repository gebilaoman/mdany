"""PNG pHYs injection: set the physical size of a PNG without changing its pixels.

graphviz does not write pHYs, so pandoc assumes 96 dpi and a tall diagram fills
a whole DOCX page (design 10.1 item 3). We write a dpi so that the image fits in
max_w_cm x max_h_cm, and never go below base_dpi (resolution only goes up).
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def size_px(data: bytes) -> tuple[int, int]:
    if data[:8] != PNG_SIG:
        raise ValueError("not a PNG file")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def fit_dpi(w_px: int, h_px: int, max_w_cm: float, max_h_cm: float, base_dpi: float) -> float:
    return max(base_dpi, w_px * 2.54 / max_w_cm, h_px * 2.54 / max_h_cm)


def set_dpi(data: bytes, dpi: float) -> bytes:
    """Return PNG bytes with exactly one pHYs chunk (placed before the first IDAT)."""
    d = bytearray(data)
    i, idat = 8, None
    while i < len(d):
        length = int.from_bytes(d[i:i + 4], "big")
        typ = bytes(d[i + 4:i + 8])
        if typ == b"pHYs":
            del d[i:i + 12 + length]
            continue
        if typ == b"IDAT":
            idat = i
            break
        i += 12 + length
    if idat is None:
        raise ValueError("PNG has no IDAT chunk")
    ppm = math.ceil(dpi / 0.0254)   # round up: the physical size never exceeds the box
    payload = b"pHYs" + struct.pack(">IIB", ppm, ppm, 1)
    chunk = struct.pack(">I", 9) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
    d[idat:idat] = chunk
    return bytes(d)


def fit(path: Path, max_w_cm: float, max_h_cm: float, base_dpi: float = 192) -> float:
    """Rewrite path in place so it fits the box. Returns the dpi written."""
    data = path.read_bytes()
    w, h = size_px(data)
    # pandoc truncates the pHYs dpi to an integer (design 10.1 item 11), so write an
    # integer dpi rounded up: the size in the DOCX then never exceeds the box.
    dpi = math.ceil(fit_dpi(w, h, max_w_cm, max_h_cm, base_dpi))
    path.write_bytes(set_dpi(data, dpi))
    return dpi
