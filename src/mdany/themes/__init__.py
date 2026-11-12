"""Themes: one directory per theme, one style file per output format."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from mdany import MdanyError

THEMES_DIR = Path(__file__).parent


@dataclass
class Theme:
    name: str = "default"
    overrides: dict[str, Path] = field(default_factory=dict)  # file name -> user file

    def file(self, filename: str) -> Path:
        """Find a style file: user override, then this theme, then the default theme."""
        if filename in self.overrides:
            path = self.overrides[filename]
            if not path.is_file():
                raise MdanyError(f"style file not found: {path}", exit_code=2)
            return path
        for theme in (self.name, "default"):
            path = THEMES_DIR / theme / filename
            if path.is_file():
                return path
        raise MdanyError(f"theme {self.name!r} has no {filename}", exit_code=2)

    def diagram_style(self):
        from mdany.diagrams.style import DiagramStyle

        data = json.loads(self.file("theme.json").read_text(encoding="utf-8"))
        return DiagramStyle.from_dict(data.get("diagram", {}))
