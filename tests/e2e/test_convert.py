from mdany.cli import main


def _snapshot(directory):
    return sorted(p.relative_to(directory) for p in directory.rglob("*"))


def test_convert_writes_pdf_and_leaves_source_dir_clean(tmp_path, sample_project):
    before = _snapshot(sample_project)
    assert main(["convert", str(sample_project / "文档.md"), "-o", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "文档.pdf").stat().st_size > 0
    assert _snapshot(sample_project) == before


def test_missing_source_exits_2(tmp_path):
    assert main(["convert", str(tmp_path / "nope.md")]) == 2


def test_doctor_passes(capsys):
    assert main(["doctor"]) == 0
    assert "pandoc" in capsys.readouterr().out
