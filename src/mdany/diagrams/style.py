"""Diagram style: font and colors. Loaded from the theme's theme.json."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiagramStyle:
    # Pango / CSS font list; the first installed family wins.
    font: str = "PingFang SC,Hiragino Sans GB,Noto Sans CJK SC,Microsoft YaHei,sans-serif"
    ink: str = "#1A202C"          # text
    stroke: str = "#37474F"       # node border, edges
    fill: str = "#F7F8FA"         # node fill
    fill_decision: str = "#EEF2F6"
    lifeline: str = "#90A4AE"

    @classmethod
    def from_dict(cls, data: dict) -> DiagramStyle:
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)
