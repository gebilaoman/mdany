"""BuildContext: temporary directory and messages for one build."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


class BuildContext:
    """Owns the temporary directory of one build.

    The directory is removed when the build succeeds, and kept when it fails
    (or when keep_temp is set), so that the user can inspect the files.
    """

    def __init__(self, keep_temp: bool = False):
        self.keep_temp = keep_temp
        self.tmp = Path(tempfile.mkdtemp(prefix="mdany-"))
        self.warnings: list[str] = []

    def tmpdir(self, name: str) -> Path:
        d = self.tmp / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"warning: {message}", file=sys.stderr)

    def info(self, message: str) -> None:
        print(message, file=sys.stderr)

    def __enter__(self) -> BuildContext:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None and not self.keep_temp:
            shutil.rmtree(self.tmp, ignore_errors=True)
        else:
            print(f"temporary files kept: {self.tmp}", file=sys.stderr)
