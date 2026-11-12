"""Calls to the pandoc binary: Markdown -> syntax tree, syntax tree -> target format."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
from functools import cache
from pathlib import Path

import panflute as pf

from mdany import MdanyError

MIN_VERSION = (3, 1, 2)


@cache
def pandoc_path() -> str:
    """Find pandoc. Order: $MDANY_PANDOC, the binary bundled with pypandoc_binary, PATH."""
    env = os.environ.get("MDANY_PANDOC")
    if env:
        return env
    try:
        import pypandoc

        bundled = Path(pypandoc.__file__).parent / "files" / "pandoc"
        if bundled.is_file():
            return str(bundled)
    except ImportError:
        pass
    found = shutil.which("pandoc")
    if found:
        return found
    raise MdanyError("pandoc not found. Run `mdany doctor`.", exit_code=2)


@cache
def pandoc_version() -> tuple[int, ...]:
    out = subprocess.run(
        [pandoc_path(), "--version"], check=True,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    first = out.stdout.splitlines()[0]  # "pandoc 3.9"
    return tuple(int(x) for x in first.split()[1].split(".") if x.isdigit())


def _run(args: list[str], stdin: str) -> str:
    proc = subprocess.run(
        [pandoc_path(), *args], input=stdin,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise MdanyError(f"pandoc failed ({' '.join(args)}):\n{proc.stderr.strip()}")
    return proc.stdout


def read(source: Path, input_format: str = "gfm") -> pf.Doc:
    """Read a Markdown file into a panflute syntax tree."""
    return read_text(source.read_text(encoding="utf-8"), input_format)


def read_text(text: str, input_format: str = "gfm") -> pf.Doc:
    """Read Markdown text into a panflute syntax tree (bundled pandoc, not the one on PATH)."""
    out = _run(["-f", input_format, "-t", "json"], text)
    return pf.load(io.StringIO(out))


def write(doc: pf.Doc, to: str, output: Path | None = None, extra: list[str] | None = None) -> str:
    """Write a syntax tree to a target format. Returns stdout when output is None."""
    buf = io.StringIO()
    pf.dump(doc, buf)
    args = ["-f", "json", "-t", to, *(extra or [])]
    if output is not None:
        args += ["-o", str(output)]
    return _run(args, buf.getvalue())
