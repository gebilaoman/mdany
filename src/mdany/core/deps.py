"""External dependencies: modules declare what they need; this module checks it."""

from __future__ import annotations

import platform
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field

from mdany import MdanyError


@dataclass(frozen=True)
class Dep:
    name: str
    check: Callable[[], str | None]          # returns None when OK, else a reason
    install: dict[str, str] = field(default_factory=dict)  # platform key -> command

    def hint(self) -> str:
        key = _platform_key()
        return self.install.get(key) or self.install.get("any") or ""


def _platform_key() -> str:
    system = platform.system()
    if system == "Darwin":
        return "macos"
    if system == "Windows":
        return "windows"
    if shutil.which("apt-get"):
        return "debian"
    if shutil.which("dnf"):
        return "fedora"
    return "linux"


def binary(name: str, install: dict[str, str]) -> Dep:
    def check() -> str | None:
        return None if shutil.which(name) else f"`{name}` not found on PATH"

    return Dep(name=name, check=check, install=install)


def check_all(deps: list[Dep]) -> list[tuple[Dep, str]]:
    """Return (dep, reason) for each missing dependency. Each dep is checked once."""
    seen: set[str] = set()
    missing = []
    for dep in deps:
        if dep.name in seen:
            continue
        seen.add(dep.name)
        reason = dep.check()
        if reason:
            missing.append((dep, reason))
    return missing


def require(deps: list[Dep]) -> None:
    """Stop with exit code 2 when a dependency is missing."""
    missing = check_all(deps)
    if not missing:
        return
    lines = ["missing dependencies:"]
    for dep, reason in missing:
        lines.append(f"  - {dep.name}: {reason}")
        if dep.hint():
            lines.append(f"    install: {dep.hint()}")
    lines.append("Run `mdany doctor` for a full check.")
    raise MdanyError("\n".join(lines), exit_code=2)


# ---- common declarations ---------------------------------------------------

def _check_pandoc() -> str | None:
    from mdany.core import pandoc

    try:
        version = pandoc.pandoc_version()
    except MdanyError as e:
        return str(e)
    if version < pandoc.MIN_VERSION:
        need = ".".join(map(str, pandoc.MIN_VERSION))
        return f"pandoc {'.'.join(map(str, version))} is too old (need >= {need})"
    return None


PANDOC = Dep(
    name="pandoc",
    check=_check_pandoc,
    install={"any": "pip install pypandoc_binary  (bundled with mdany)"},
)
