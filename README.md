# mdany

Convert a set of Markdown documents into a PDF / DOCX submission package.

- Mermaid diagrams become vector graphics (graphviz), not code blocks or blurry bitmaps.
- DOCX diagrams fit 12 × 9.5 cm; DOCX tables have borders.
- One `mdany.toml` holds the skip list, copy list and output naming for the whole package.
- Source-code excerpts: one section per page, running header, font sized to fit the page.

Status: in development (target v0.1.0: replace the build scripts of one real project).

## Install

```bash
uv tool install git+https://github.com/gebilaoman/mdany
mdany doctor               # checks pandoc, weasyprint (pango), graphviz, rsvg-convert
```

pandoc comes with the Python package. Install the system parts first:

- macOS: `brew install uv pango graphviz librsvg`
- Debian / Ubuntu: `sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 graphviz librsvg2-bin fonts-noto-cjk`
- Windows (PowerShell):

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

  Open a new PowerShell window after this. CI runs the tests on Windows with the same setup.

## Install (development)

```bash
uv sync
uv run mdany doctor
```

## Use

One file:

```bash
uv run mdany convert report.md              # -> report.pdf next to report.md
uv run mdany convert report.md -f docx      # -> report.docx
uv run mdany convert report.md -f all -o out/
```

A project (directory with `mdany.toml`):

```bash
uv run mdany build                          # all documents, all formats, clean stale outputs
uv run mdany build -f pdf                   # PDF only
uv run mdany build 阶段2/2.5-业务流程图.md   # one document; no cleanup
```

## Demo

`examples/demo/` is a small project with the same layout as a real submission package:
skip list, copy list, an override for a source-code excerpt, and every supported mermaid
form. `tests/e2e/test_demo.py` builds it on every test run.

```bash
cd examples/demo
uv run mdany build          # -> pdf/ and word/
```

## Mermaid subset

- `flowchart` / `graph` with direction TD, TB, BT, LR, RL
  - nodes `A`, `A[box]`, `A(round)`, `A{decision}`, `A((circle))`, `A[(database)]`
  - edges `-->`, `-->|label|`, `-.->`, `-.label.->`, chains `A --> B --> C`
- `sequenceDiagram` with `participant X as Name`, `->>`, `-->>`, self calls

Other syntax stops the build for that document with the file, block number and line.

## DOCX table of contents

The table of contents in a DOCX file is a Word field. Open the file in Word and update
fields (right-click the table of contents, then Update Field) to show it.

## Tests

```bash
uv run pytest
```
