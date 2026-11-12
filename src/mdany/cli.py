"""Command line: mdany convert / build / doctor (design 6)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mdany import MdanyError, __version__, formats, pipeline
from mdany.core import deps
from mdany.core.context import BuildContext
from mdany.formats.pdf import ENGINES as PDF_ENGINES
from mdany.project import build as project_build
from mdany.project import config as project_config
from mdany.project import plan as project_plan
from mdany.themes import Theme


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("-f", "--format", choices=[*formats.names(), "all"])
    p.add_argument("--pdf-engine", default="weasyprint", choices=list(PDF_ENGINES))
    p.add_argument("--css", type=Path, help="replace the theme's pdf.css")
    p.add_argument("--reference-doc", type=Path, help="replace the theme's reference.docx")
    p.add_argument("--keep-temp", action="store_true", help="keep temporary files on success")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mdany", description="Markdown -> PDF / DOCX")
    p.add_argument("--version", action="version", version=f"mdany {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("convert", help="convert one Markdown file")
    c.add_argument("source", type=Path)
    c.add_argument("-o", "--output-dir", type=Path,
                   help="output directory (default: the directory of the source file)")
    _common(c)

    b = sub.add_parser("build", help="build a project from mdany.toml")
    b.add_argument("documents", nargs="*",
                   help="build only these documents (relative to the source directory); "
                        "no stale-output cleanup")
    b.add_argument("-c", "--config", type=Path,
                   help="path to mdany.toml (default: search from the current directory up)")
    _common(b)

    sub.add_parser("doctor", help="check external dependencies")
    return p


def _create_formats(names: list[str], args: argparse.Namespace) -> dict:
    out = {}
    for name in names:
        opts = {"engine": args.pdf_engine} if name == "pdf" else {}
        out[name] = formats.create(name, **opts)
    return out


def _theme(name: str, css: Path | None, reference_doc: Path | None) -> Theme:
    overrides = {}
    if css:
        overrides["pdf.css"] = css
    if reference_doc:
        overrides["reference.docx"] = reference_doc
    return Theme(name=name, overrides=overrides)


def cmd_convert(args: argparse.Namespace) -> int:
    source: Path = args.source
    if not source.is_file():
        raise MdanyError(f"file not found: {source}", exit_code=2)
    choice = args.format or "pdf"
    names = formats.names() if choice == "all" else [choice]
    fmts = _create_formats(names, args)
    deps.require([d for f in fmts.values() for d in f.requires])

    out_dir = (args.output_dir or source.parent).resolve()
    theme = _theme("default", args.css, args.reference_doc)
    targets = [(f, out_dir / f"{source.stem}{f.ext}") for f in fmts.values()]

    with BuildContext(keep_temp=args.keep_temp) as ctx:
        for out in pipeline.convert(source, targets, theme, ctx):
            print(out)
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    cfg_path = args.config or project_config.find(Path.cwd())
    cfg = project_config.load(cfg_path, formats.names())

    if args.format in (None, "all"):
        names = list(cfg.outputs)
    else:
        if args.format not in cfg.outputs:
            raise MdanyError(f"format {args.format!r} has no [output.{args.format}] in "
                             f"{cfg_path}", exit_code=2)
        names = [args.format]
    fmts = _create_formats(names, args)
    deps.require([d for f in fmts.values() for d in f.requires])

    plan = project_plan.make(cfg, {n: f.ext for n, f in fmts.items()}, args.documents or None)
    theme = _theme(cfg.theme, args.css or cfg.css, args.reference_doc or cfg.reference_doc)
    out_dirs = [cfg.outputs[n] for n in names]

    with BuildContext(keep_temp=args.keep_temp) as ctx:
        result = project_build.run(plan, fmts, out_dirs, theme, ctx)
        if result.failed:
            ctx.keep_temp = True    # keep intermediate files for the failed documents

    print(f"documents: {len(plan.docs) - len(result.failed)}/{len(plan.docs)} converted, "
          f"{len(result.converted)} files; copied {len(plan.copies)} items")
    for name in result.removed:
        print(f"removed stale output: {name}")
    for rel, message in result.failed:
        print(f"FAILED {rel}:\n  {message}", file=sys.stderr)
    for d in out_dirs:
        print(f"output: {d}")
    return 1 if result.failed else 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    all_deps = []
    for name in formats.names():
        all_deps += formats.create(name).requires
    for engine in PDF_ENGINES.values():   # all engines, not only the default one
        all_deps += engine.REQUIRES
    missing = {d.name: reason for d, reason in deps.check_all(all_deps)}
    seen = set()
    for dep in all_deps:
        if dep.name in seen:
            continue
        seen.add(dep.name)
        if dep.name in missing:
            print(f"  ✗ {dep.name}: {missing[dep.name]}")
            if dep.hint():
                print(f"      install: {dep.hint()}")
        else:
            print(f"  ✓ {dep.name}")
    return 2 if missing else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "convert":
            return cmd_convert(args)
        if args.command == "build":
            return cmd_build(args)
        if args.command == "doctor":
            return cmd_doctor(args)
    except MdanyError as e:
        print(f"error: {e}", file=sys.stderr)
        return e.exit_code
    return 1


if __name__ == "__main__":
    sys.exit(main())
