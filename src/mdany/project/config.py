"""Read and check mdany.toml (design 5.1)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mdany import MdanyError

CONFIG_NAME = "mdany.toml"

# Per-document options: [defaults] and [[override]].
OPTION_KEYS = {"toc", "toc_depth", "title", "page_break_before", "header", "fit_code_to_page", "lang",
               "title_block"}
_PROJECT_KEYS = {"source", "include", "skip", "copy", "name", "theme", "css", "reference_doc"}
_OUTPUT_KEYS = {"dir"}


@dataclass
class Override:
    match: str                       # glob, relative to the source directory
    options: dict[str, Any]


@dataclass
class Config:
    root: Path                       # directory of mdany.toml
    source: Path
    include: list[str]
    skip: list[str]
    copy: list[str]
    name: str
    outputs: dict[str, Path]         # format name -> output directory
    defaults: dict[str, Any] = field(default_factory=dict)
    overrides: list[Override] = field(default_factory=list)
    theme: str = "default"
    css: Path | None = None
    reference_doc: Path | None = None


def _err(path: Path, message: str) -> MdanyError:
    return MdanyError(f"{path}: {message}", exit_code=2)


def _unknown(path: Path, where: str, data: dict, allowed: set[str]) -> None:
    extra = sorted(set(data) - allowed)
    if extra:
        raise _err(path, f"unknown key(s) in {where}: {', '.join(extra)}")


def _str_list(path: Path, where: str, value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise _err(path, f"{where} must be a list of strings")
    return value


def _check_title_block(path: Path, where: str, opts: dict, known_formats: list[str]) -> None:
    value = opts.get("title_block")
    if value is None or isinstance(value, bool):
        return
    if not isinstance(value, list) or not all(v in known_formats for v in value):
        raise _err(path, f"{where}: title_block must be true, false or a list of {known_formats}")


def find(start: Path) -> Path:
    """Find mdany.toml in start or its parents."""
    start = start.resolve()
    for d in (start, *start.parents):
        candidate = d / CONFIG_NAME
        if candidate.is_file():
            return candidate
    raise MdanyError(f"{CONFIG_NAME} not found in {start} or its parents", exit_code=2)


def load(path: Path, known_formats: list[str]) -> Config:
    path = path.resolve()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise _err(path, f"invalid TOML: {e}") from None
    _unknown(path, "top level", data, {"project", "output", "defaults", "override"})
    root = path.parent

    project = data.get("project", {})
    _unknown(path, "[project]", project, _PROJECT_KEYS)
    source = (root / project.get("source", ".")).resolve()
    if not source.is_dir():
        raise _err(path, f"source directory not found: {source}")

    outputs: dict[str, Path] = {}
    for fmt, conf in data.get("output", {}).items():
        if fmt not in known_formats:
            raise _err(path, f"[output.{fmt}]: unknown format; choose from {known_formats}")
        _unknown(path, f"[output.{fmt}]", conf, _OUTPUT_KEYS)
        outputs[fmt] = (root / conf.get("dir", fmt)).resolve()
    if not outputs:
        raise _err(path, "no [output.<format>] section")

    defaults = data.get("defaults", {})
    _unknown(path, "[defaults]", defaults, OPTION_KEYS)
    _check_title_block(path, "[defaults]", defaults, known_formats)

    overrides = []
    for i, item in enumerate(data.get("override", []), 1):
        if "match" not in item:
            raise _err(path, f"[[override]] #{i} has no `match`")
        opts = {k: v for k, v in item.items() if k != "match"}
        _unknown(path, f"[[override]] #{i}", opts, OPTION_KEYS)
        _check_title_block(path, f"[[override]] #{i}", opts, known_formats)
        overrides.append(Override(match=item["match"], options=opts))

    def opt_path(key: str) -> Path | None:
        return (root / project[key]).resolve() if project.get(key) else None

    return Config(
        root=root,
        source=source,
        include=_str_list(path, "include", project.get("include", ["**/*.md"])),
        skip=_str_list(path, "skip", project.get("skip")),
        copy=_str_list(path, "copy", project.get("copy")),
        name=project.get("name", "{stem}"),
        outputs=outputs,
        defaults=defaults,
        overrides=overrides,
        theme=project.get("theme", "default"),
        css=opt_path("css"),
        reference_doc=opt_path("reference_doc"),
    )
