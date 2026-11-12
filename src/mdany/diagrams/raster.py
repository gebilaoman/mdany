"""SVG -> PNG. Uses rsvg-convert (design 10.2 item 3: a pip-installable option is not checked yet)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from mdany import MdanyError

ZOOM = 2  # matches graphviz PNG_DPI 192 = 2 x 96


def svg_to_png(svg: Path, png: Path) -> Path:
    try:
        proc = subprocess.run(
            ["rsvg-convert", "-z", str(ZOOM), "-o", str(png), str(svg)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        raise MdanyError("`rsvg-convert` not found. Run `mdany doctor`.", exit_code=2) from None
    if proc.returncode != 0:
        raise MdanyError(f"rsvg-convert failed: {proc.stderr.strip()}")
    return png
