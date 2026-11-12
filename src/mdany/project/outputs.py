"""Output register and stale-output cleanup (design 5.2).

Each output directory holds .mdany-outputs.json with the names mdany wrote there.
A full build deletes names from the previous register that it did not write again.
mdany never deletes a file that it did not write itself.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

REGISTER = ".mdany-outputs.json"


def read(out_dir: Path) -> set[str]:
    path = out_dir / REGISTER
    if not path.is_file():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")).get("files", []))
    except (json.JSONDecodeError, AttributeError):
        return set()


def write(out_dir: Path, names: set[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / REGISTER).write_text(
        json.dumps({"files": sorted(names)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def finish(out_dir: Path, written: set[str], partial: bool) -> list[str]:
    """Update the register. On a full build, delete stale outputs; return their names."""
    previous = read(out_dir)
    if partial:
        write(out_dir, previous | written)
        return []
    removed = []
    for name in sorted(previous - written):
        target = out_dir / name
        if target.is_dir():
            shutil.rmtree(target)
            removed.append(name)
        elif target.exists():
            target.unlink()
            removed.append(name)
    write(out_dir, written)
    return removed


def copy_item(src: Path, dest: Path) -> None:
    if dest.is_dir():
        shutil.rmtree(dest)
    elif dest.exists():
        dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
