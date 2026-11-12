import panflute as pf

from mdany.formats.pdf import table_breaks

ZWSP = table_breaks.ZWSP


def _doc(md: str) -> pf.Doc:
    return pf.convert_text(md, input_format="gfm", standalone=True)


def test_breaks_only_inside_table_cells_and_long_values():
    value = "enum('a','b','c','d','e','f')"
    doc = _doc(f"{value}\n\n| t | u |\n|---|---|\n| {value} | x,y |\n")
    table_breaks.apply(doc)
    para, table = doc.content[0], doc.content[1]
    assert ZWSP not in pf.stringify(para)                       # body text unchanged
    cells = [pf.stringify(c) for c in table.content[0].content[0].content]
    assert cells[0] == f"enum(​'a',{ZWSP}'b',{ZWSP}'c',{ZWSP}'d',{ZWSP}'e',{ZWSP}'f')"
    assert cells[1] == "x,y"                                     # short value unchanged


def test_identifiers_keep_underscores_whole():
    assert table_breaks._add("downstream_project_id") == "downstream_project_id"
    assert table_breaks._add("project_task_nodes.project_idfp") == f"project_task_nodes.{ZWSP}project_idfp"
