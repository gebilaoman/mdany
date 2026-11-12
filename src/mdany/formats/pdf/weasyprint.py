"""PDF engine: weasyprint (Python library; needs the system pango library)."""

from __future__ import annotations

from pathlib import Path

from mdany.core.deps import Dep

STYLE_FILE = "pdf.css"


def _check() -> str | None:
    try:
        import weasyprint  # noqa: F401
    except ImportError:
        return "Python package weasyprint is not installed"
    except OSError as e:  # pango / gobject shared libraries not found
        return f"weasyprint cannot load system libraries: {e}"
    return None


REQUIRES = [
    Dep(
        name="weasyprint",
        check=_check,
        install={
            "macos": "brew install pango",
            "debian": "sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0",
            "fedora": "sudo dnf install -y pango",
            "windows": "see https://doc.courtbouillon.org/weasyprint/stable/first_steps.html",
        },
    )
]


def render(html: Path, out: Path) -> None:
    """The HTML links the theme CSS; images have absolute paths (transforms.image_paths)."""
    import weasyprint

    weasyprint.HTML(filename=str(html)).write_pdf(str(out))
