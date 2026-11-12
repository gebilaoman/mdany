from mdany.project import outputs


def test_full_build_removes_only_registered_stale_files(tmp_path):
    out = tmp_path / "pdf"
    out.mkdir()
    for name in ["a.pdf", "b.pdf", "user-notes.txt"]:
        (out / name).write_text("x")
    (out / "dir-item").mkdir()
    outputs.write(out, {"a.pdf", "b.pdf", "dir-item"})

    removed = outputs.finish(out, {"a.pdf"}, partial=False)

    assert sorted(removed) == ["b.pdf", "dir-item"]
    assert (out / "a.pdf").exists() and (out / "user-notes.txt").exists()
    assert outputs.read(out) == {"a.pdf"}


def test_partial_build_only_adds(tmp_path):
    out = tmp_path / "pdf"
    outputs.write(out, {"a.pdf", "b.pdf"})
    assert outputs.finish(out, {"c.pdf"}, partial=True) == []
    assert outputs.read(out) == {"a.pdf", "b.pdf", "c.pdf"}


def test_copy_item_replaces_previous_copy(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "new.json").write_text("{}")
    dest = tmp_path / "out" / "item"
    dest.mkdir(parents=True)
    (dest / "old.json").write_text("{}")
    outputs.copy_item(src, dest)
    assert sorted(p.name for p in dest.iterdir()) == ["new.json"]
