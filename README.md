<p align="center">
  <img src="assets/logo.png" alt="mdany logo" width="128">
</p>

<h1 align="center">mdany</h1>

<p align="center">
  Convert a set of Markdown documents into a PDF / DOCX submission package.
</p>

<p align="center">
  <a href="https://github.com/gebilaoman/mdany/releases"><img alt="release" src="https://img.shields.io/github/v/release/gebilaoman/mdany"></a>
  <a href="https://github.com/gebilaoman/mdany/actions/workflows/ci.yml"><img alt="ci" src="https://github.com/gebilaoman/mdany/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

---

You write documents in Markdown. The receiver wants PDF or Word files. mdany converts
the full set with one command:

- Mermaid diagrams become vector graphics (through graphviz). They are not code blocks or blurry bitmaps.
- In DOCX files, diagrams fit 12 × 9.5 cm and tables have borders.
- One `mdany.toml` file holds the skip list, the copy list and the output names for the full package.
- Source-code excerpts: one section per page, a running header, and a font size that fits the page.

macOS, Linux and Windows are supported. CI runs the tests on all three.

## Install

Install the system parts first:

- **macOS**

  ```bash
  brew install uv pango graphviz librsvg
  ```

- **Debian / Ubuntu**

  ```bash
  sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 graphviz librsvg2-bin fonts-noto-cjk
  # then install uv: https://docs.astral.sh/uv/getting-started/installation/
  ```

- **Windows (PowerShell)**

  ```powershell
  winget install --id=astral-sh.uv -e
  winget install --id=Git.Git -e
  winget install --id=MSYS2.MSYS2 -e
  C:\msys64\usr\bin\bash.exe -lc "pacman -S --needed --noconfirm mingw-w64-x86_64-pango mingw-w64-x86_64-graphviz mingw-w64-x86_64-librsvg"
  $bin = "C:\msys64\mingw64\bin"
  [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$bin", "User")
  [Environment]::SetEnvironmentVariable("WEASYPRINT_DLL_DIRECTORIES", $bin, "User")
  [Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
  ```

  Open a new PowerShell window after these commands.

Then install mdany and check the dependencies:

```bash
uv tool install git+https://github.com/gebilaoman/mdany@v0.1.0
mdany doctor        # checks pandoc, weasyprint (pango), graphviz, rsvg-convert
```

pandoc comes with the Python package. You do not install it separately.

## Quick start

### One file

```bash
mdany convert report.md              # -> report.pdf next to report.md
mdany convert report.md -f docx      # -> report.docx
mdany convert report.md -f all -o out/
```

### A project

A project is a directory with a `mdany.toml` file. mdany searches for this file in the
current directory and then in its parent directories.

```bash
mdany build                          # all documents, all formats; removes stale outputs
mdany build -f pdf                   # PDF only
mdany build 阶段2/2.5-业务流程图.md   # one document; no cleanup
```

### Demo

`examples/demo/` is a small project with the same layout as a real submission package. It
has a skip list, a copy list, an override for a source-code excerpt, and all supported
mermaid forms.

```bash
cd examples/demo
mdany build          # -> pdf/ and word/
```

## mdany.toml

```toml
[project]
source  = "md"                        # source directory, relative to mdany.toml
include = ["阶段*/*.md"]               # glob patterns; default ["**/*.md"]
skip    = ["阶段1/内部说明.md"]         # documents to leave out
copy    = ["阶段6/6.4-数据库脚本.sql"]  # files or directories to copy as-is
name    = "{parent}-{stem}"            # output name; default "{stem}"
# theme = "default"
# css = "my.css"                      # replaces the theme's pdf.css
# reference_doc = "my.docx"           # replaces the theme's reference.docx

[output.pdf]
dir = "pdf"

[output.docx]
dir = "word"

[defaults]                            # options for all documents
toc = true
toc_depth = 2

[[override]]                          # options for the documents that match
match = "阶段6/6.1-源代码摘录.md"
page_break_before = "h2"
header = "示例软件 V1.0.0"
fit_code_to_page = true
toc = false
```

Fields for `name`:

| Field | Value for `阶段2/2.5-业务流程图.md` |
|---|---|
| `{parent}` | `阶段2` (for a top-level file: the name of the source directory) |
| `{stem}` | `2.5-业务流程图` |
| `{name}` | `2.5-业务流程图.md` |

Options for `[defaults]` and `[[override]]`. When more than one override matches a
document, the last one wins.

| Option | Default | Meaning |
|---|---|---|
| `toc` | `true` | Add a table of contents. |
| `toc_depth` | `2` | Heading levels in the table of contents. |
| `title` | first H1, else the file name | Document title. |
| `title_block` | `false` | Show the file name as a title block above the body. `true` for all formats, or a list such as `["pdf"]`. |
| `page_break_before` | none | Start a new page before each heading of this level (`h1` … `h6`). |
| `header` | none | Running header text on each PDF page. |
| `fit_code_to_page` | `false` | Make the code font smaller so that each code block fits one PDF page. |
| `lang` | `zh-CN` | PDF document language. It controls the font fallback for CJK text. |

mdany stops with an error when `mdany.toml` has an unknown key.

## Mermaid subset

- `flowchart` / `graph` with direction TD, TB, BT, LR, RL
  - nodes `A`, `A[box]`, `A(round)`, `A{decision}`, `A((circle))`, `A[(database)]`
  - edges `-->`, `-->|label|`, `-.->`, `-.label.->`, chains `A --> B --> C`
- `sequenceDiagram` with `participant X as Name`, `->>`, `-->>`, self calls

For other syntax, the build of that document stops. The error gives the file, the block
number and the line.

## DOCX table of contents

The table of contents in a DOCX file is a Word field. To show it, open the file in Word,
right-click the table of contents, and select **Update Field**.

## Development

```bash
uv sync
uv run mdany doctor
uv run pytest
uv run ruff check .
```

## License

mdany is released under the [MIT License](LICENSE).

mdany calls the programs and libraries below. It does not include their source code.
Each one has its own license:

| Component | License | How mdany uses it |
|---|---|---|
| [pandoc](https://pandoc.org/) (in the `pypandoc_binary` wheel) | GPL-2.0-or-later | Separate program, called as a subprocess |
| [WeasyPrint](https://weasyprint.org/) | BSD-3-Clause | Python library, PDF output |
| [panflute](https://github.com/sergiocorreia/panflute) | BSD-3-Clause | Python library, document filters |
| [Graphviz](https://graphviz.org/) | EPL-1.0 | System program, diagram layout |
| [librsvg](https://gitlab.gnome.org/GNOME/librsvg) (`rsvg-convert`) | LGPL-2.1-or-later | System program, SVG to PNG |
| [Pango](https://gitlab.gnome.org/GNOME/pango) | LGPL-2.1-or-later | System library, used by WeasyPrint |
