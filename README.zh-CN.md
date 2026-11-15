<p align="center">
  <img src="assets/logo.png" alt="mdany logo" width="128">
</p>

<h1 align="center">mdany</h1>

<p align="center">
  把一整套 Markdown 文档转成 PDF / DOCX 提交包。
</p>

<p align="center">
  <a href="https://github.com/gebilaoman/mdany/releases"><img alt="release" src="https://img.shields.io/github/v/release/gebilaoman/mdany"></a>
  <a href="https://github.com/gebilaoman/mdany/actions/workflows/ci.yml"><img alt="ci" src="https://github.com/gebilaoman/mdany/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

<p align="center">
  <a href="README.md">English</a> | 简体中文
</p>

---

文档用 Markdown 写，对方要 PDF 或 Word。mdany 用一条命令转完整套文档：

- Mermaid 图经 graphviz 渲染成矢量图，不是代码块，也不是模糊的位图。
- DOCX 里的图缩放到 12 × 9.5 cm 以内，表格带边框。
- 一个 `mdany.toml` 管整套材料：跳过清单、原样复制清单、产物命名。
- 源码摘录：每节一页，带页眉，字号自动缩放到一页放得下。

支持 macOS、Linux、Windows。CI 在三个平台上都跑测试。

## 安装

先装系统依赖：

- **macOS**

  ```bash
  brew install uv pango graphviz librsvg
  ```

- **Debian / Ubuntu**

  ```bash
  sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 graphviz librsvg2-bin fonts-noto-cjk
  # 然后安装 uv：https://docs.astral.sh/uv/getting-started/installation/
  ```

- **Windows（PowerShell）**

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

  执行完后，打开一个新的 PowerShell 窗口。

再安装 mdany，并检查依赖：

```bash
uv tool install git+https://github.com/gebilaoman/mdany@v0.1.0
mdany doctor        # 检查 pandoc、weasyprint（pango）、graphviz、rsvg-convert
```

pandoc 随 Python 包一起安装，不用单独装。

## 快速开始

### 单个文件

```bash
mdany convert report.md              # -> 在 report.md 旁边生成 report.pdf
mdany convert report.md -f docx      # -> report.docx
mdany convert report.md -f all -o out/
```

### 项目

项目是一个带 `mdany.toml` 的目录。mdany 先在当前目录找这个文件，找不到再逐级往上层目录找。

```bash
mdany build                          # 全部文档、全部格式；删除过期产物
mdany build -f pdf                   # 只出 PDF
mdany build 阶段2/2.5-业务流程图.md   # 只转一个文档；不做清理
```

### 示例

`examples/demo/` 是一个小项目，目录结构和真实的提交包相同。里面有跳过清单、复制清单、
一条针对源码摘录的覆盖规则，以及所有支持的 mermaid 写法。

```bash
cd examples/demo
mdany build          # -> pdf/ 和 word/
```

## mdany.toml

```toml
[project]
source  = "md"                        # 源目录，相对 mdany.toml
include = ["阶段*/*.md"]               # glob 模式；默认 ["**/*.md"]
skip    = ["阶段1/内部说明.md"]         # 不转换的文档
copy    = ["阶段6/6.4-数据库脚本.sql"]  # 原样复制的文件或目录
name    = "{parent}-{stem}"            # 产物命名；默认 "{stem}"
# theme = "default"
# css = "my.css"                      # 替换主题的 pdf.css
# reference_doc = "my.docx"           # 替换主题的 reference.docx

[output.pdf]
dir = "pdf"

[output.docx]
dir = "word"

[defaults]                            # 对所有文档生效的选项
toc = true
toc_depth = 2

[[override]]                          # 只对匹配的文档生效的选项
match = "阶段6/6.1-源代码摘录.md"
page_break_before = "h2"
header = "示例软件 V1.0.0"
fit_code_to_page = true
toc = false
```

`name` 可用的字段：

| 字段 | `阶段2/2.5-业务流程图.md` 对应的值 |
|---|---|
| `{parent}` | `阶段2`（顶层文件取源目录名） |
| `{stem}` | `2.5-业务流程图` |
| `{name}` | `2.5-业务流程图.md` |

`[defaults]` 和 `[[override]]` 可用的选项。一个文档匹配多条 override 时，后面的覆盖前面的。

| 选项 | 默认值 | 作用 |
|---|---|---|
| `toc` | `true` | 生成目录。 |
| `toc_depth` | `2` | 目录包含的标题层级。 |
| `title` | 第一个 H1，没有则取文件名 | 文档标题。 |
| `title_block` | `false` | 在正文上方用文件名显示标题块。`true` 表示所有格式，也可以写成列表，例如 `["pdf"]`。 |
| `page_break_before` | 无 | 在这一级标题（`h1` … `h6`）前分页。 |
| `header` | 无 | PDF 每页的页眉文字。 |
| `fit_code_to_page` | `false` | 缩小代码字号，让每个代码块放进一页 PDF。 |
| `lang` | `zh-CN` | PDF 文档语言，决定中日韩文字的字体回退。 |

`mdany.toml` 里有未知的键时，mdany 报错并停止。

## 支持的 Mermaid 语法

- `flowchart` / `graph`，方向 TD、TB、BT、LR、RL
  - 节点 `A`、`A[box]`、`A(round)`、`A{decision}`、`A((circle))`、`A[(database)]`
  - 连线 `-->`、`-->|label|`、`-.->`、`-.label.->`，链式 `A --> B --> C`
- `sequenceDiagram`，支持 `participant X as Name`、`->>`、`-->>`、自调用

遇到其他语法时，该文档停止构建。报错信息给出文件、图块序号和行号。

## DOCX 目录

DOCX 文件里的目录是 Word 域。用 Word 打开文件，右键点目录，选择 **更新域**，目录才会显示。

## 开发

```bash
uv sync
uv run mdany doctor
uv run pytest
uv run ruff check .
```

## 开源协议

mdany 以 [MIT 协议](LICENSE) 发布。

mdany 会调用下面这些程序和库，但不包含它们的源代码。它们各自使用自己的协议：

| 组件 | 协议 | mdany 如何使用 |
|---|---|---|
| [pandoc](https://pandoc.org/)（在 `pypandoc_binary` wheel 中） | GPL-2.0-or-later | 独立程序，以子进程调用 |
| [WeasyPrint](https://weasyprint.org/) | BSD-3-Clause | Python 库，输出 PDF |
| [panflute](https://github.com/sergiocorreia/panflute) | BSD-3-Clause | Python 库，文档过滤 |
| [Graphviz](https://graphviz.org/) | EPL-1.0 | 系统程序，图布局 |
| [librsvg](https://gitlab.gnome.org/GNOME/librsvg)（`rsvg-convert`） | LGPL-2.1-or-later | 系统程序，SVG 转 PNG |
| [Pango](https://gitlab.gnome.org/GNOME/pango) | LGPL-2.1-or-later | 系统库，供 WeasyPrint 使用 |
