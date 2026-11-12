from pathlib import Path

import pytest

from mdany import MdanyError
from mdany.project import config, plan

FORMATS = ["pdf", "docx"]


def _project(tmp_path: Path, toml: str) -> Path:
    for rel in ["md/阶段1/1.1-甲.md", "md/阶段1/内部.md", "md/阶段2/2.1-乙.md", "md/阶段6/6.1-代码.md"]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# x\n", encoding="utf-8")
    (tmp_path / "md/阶段6/配置").mkdir()
    (tmp_path / "md/阶段6/配置/a.json").write_text("{}")
    (tmp_path / "md/阶段6/脚本.sql").write_text("--")
    cfg = tmp_path / "mdany.toml"
    cfg.write_text(toml, encoding="utf-8")
    return cfg


FULL = """
[project]
source = "md"
include = ["阶段*/*.md"]
skip = ["阶段1/内部.md", "阶段9/不存在.md"]
copy = ["阶段6/配置", "阶段6/脚本.sql", "阶段6/缺失.csv"]
name = "{parent}-{stem}"
[output.pdf]
dir = "pdf"
[output.docx]
dir = "word"
[defaults]
toc = true
[[override]]
match = "阶段6/*.md"
page_break_before = "h2"
toc = false
"""


def test_load_resolves_paths(tmp_path):
    cfg = config.load(_project(tmp_path, FULL), FORMATS)
    assert cfg.source == (tmp_path / "md").resolve()
    assert cfg.outputs == {"pdf": (tmp_path / "pdf").resolve(), "docx": (tmp_path / "word").resolve()}


@pytest.mark.parametrize("toml,needle", [
    ("[project]\nsorce='md'\n[output.pdf]\n", "unknown key(s) in [project]: sorce"),
    ("[project]\nsource='md'\n", "no [output.<format>]"),
    ("[project]\nsource='md'\n[output.epub]\n", "unknown format"),
    ("[project]\nsource='nope'\n[output.pdf]\n", "source directory not found"),
    ("[project]\nsource='md'\n[output.pdf]\n[defaults]\ntocc=true\n", "[defaults]: tocc"),
    ("[project]\nsource='md'\n[output.pdf]\n[[override]]\ntoc=false\n", "has no `match`"),
    ("[project\n", "invalid TOML"),
])
def test_config_errors_exit_2(tmp_path, toml, needle):
    with pytest.raises(MdanyError) as info:
        config.load(_project(tmp_path, toml), FORMATS)
    assert info.value.exit_code == 2 and needle in str(info.value)


def test_find_searches_parents(tmp_path):
    path = _project(tmp_path, FULL)
    assert config.find(tmp_path / "md" / "阶段1") == path.resolve()


def test_plan_names_skip_copy_and_overrides(tmp_path):
    cfg = config.load(_project(tmp_path, FULL), FORMATS)
    p = plan.make(cfg, {"pdf": ".pdf", "docx": ".docx"})
    assert [d.rel for d in p.docs] == ["阶段1/1.1-甲.md", "阶段2/2.1-乙.md", "阶段6/6.1-代码.md"]
    assert p.docs[0].outputs["pdf"].name == "阶段1-1.1-甲.pdf"
    assert p.docs[0].outputs["docx"].parent.name == "word"
    assert p.docs[0].options == {"toc": True}
    assert p.docs[2].options == {"toc": False, "page_break_before": "h2"}
    assert sorted(c.outputs["pdf"].name for c in p.copies) == ["阶段6-脚本.sql", "阶段6-配置"]
    assert any("阶段9/不存在.md" in w for w in p.warnings)
    assert any("阶段6/缺失.csv" in w for w in p.warnings)


def test_plan_only_selected_documents(tmp_path):
    cfg = config.load(_project(tmp_path, FULL), FORMATS)
    p = plan.make(cfg, {"pdf": ".pdf"}, only=["阶段2/2.1-乙.md"])
    assert [d.rel for d in p.docs] == ["阶段2/2.1-乙.md"]
    assert p.copies == [] and p.partial
    with pytest.raises(MdanyError, match="document not found"):
        plan.make(cfg, {"pdf": ".pdf"}, only=["阶段2/nope.md"])


def test_plan_detects_name_collision(tmp_path):
    toml = FULL.replace('name = "{parent}-{stem}"', 'name = "same"')
    cfg = config.load(_project(tmp_path, toml), FORMATS)
    with pytest.raises(MdanyError, match="same output"):
        plan.make(cfg, {"pdf": ".pdf"})


@pytest.mark.parametrize(
    "value,ok", [("true", True), ('["pdf"]', True), ('["epub"]', False), ('"pdf"', False)]
)
def test_title_block_values(tmp_path, value, ok):
    toml = f"[project]\nsource='md'\n[output.pdf]\n[defaults]\ntitle_block = {value}\n"
    if ok:
        config.load(_project(tmp_path, toml), FORMATS)
    else:
        with pytest.raises(MdanyError, match="title_block"):
            config.load(_project(tmp_path, toml), FORMATS)
