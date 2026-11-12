import pytest

from mdany.diagrams.mermaid import Flowchart, UnsupportedSyntax, parse
from mdany.diagrams.mermaid.flowchart import parse as parse_flowchart


def test_shapes_labels_and_direction():
    chart = parse_flowchart(
        "flowchart LR\n"
        "  A[方框] --> B(圆角)\n"
        "  B --> C{菱形}\n"
        "  C --> D((圆形))\n"
        "  C --> E[(数据库)]\n"
        '  E --> F["带引号"]\n'
    )
    assert chart.direction == "LR"
    shapes = {n.id: (n.shape, n.label) for n in chart.nodes.values()}
    assert shapes == {
        "A": ("box", "方框"), "B": ("round", "圆角"), "C": ("diamond", "菱形"),
        "D": ("circle", "圆形"), "E": ("cylinder", "数据库"), "F": ("box", "带引号"),
    }


def test_td_maps_to_tb_and_bare_nodes_use_id_as_label():
    chart = parse_flowchart("graph TD\nA --> B\n")
    assert chart.direction == "TB"
    assert [n.label for n in chart.nodes.values()] == ["A", "B"]


def test_edges_chain_labels_and_dotted():
    chart = parse_flowchart(
        "flowchart TD\n"
        "  A --> B --> C\n"
        "  C -->|通过| D\n"
        "  C --> |失败| E\n"
        "  D -.同机回环.-> F\n"
        "  E -.-> G\n"
        "  G -.->|异步| A\n"
    )
    edges = [(e.src, e.dst, e.label, e.style) for e in chart.edges]
    assert edges == [
        ("A", "B", "", "solid"), ("B", "C", "", "solid"),
        ("C", "D", "通过", "solid"), ("C", "E", "失败", "solid"),
        ("D", "F", "同机回环", "dotted"), ("E", "G", "", "dotted"),
        ("G", "A", "异步", "dotted"),
    ]


def test_label_defined_later_is_kept():
    chart = parse_flowchart("flowchart TD\nA --> B\nB[第二步]\n")
    assert chart.nodes["B"].label == "第二步"


def test_comments_and_semicolons_are_ignored():
    chart = parse_flowchart("%% top\nflowchart TD;\n  %% note\n  A --> B;\n")
    assert len(chart.edges) == 1


@pytest.mark.parametrize("line", [
    "subgraph 子图",
    "classDef red fill:#f00",
    "A --- B",
    "A ==> B",
    "A --> B & C",
    "click A callback",
    "A -->",
])
def test_unsupported_syntax_is_reported_with_line_number(line):
    with pytest.raises(UnsupportedSyntax) as info:
        parse_flowchart(f"flowchart TD\n  A --> B\n  {line}\n")
    assert info.value.line_no == 3


def test_missing_header_is_reported():
    with pytest.raises(UnsupportedSyntax):
        parse_flowchart("A --> B\n")


def test_dispatch_by_first_line():
    assert isinstance(parse("flowchart TD\nA-->B"), Flowchart)
    with pytest.raises(UnsupportedSyntax, match="unsupported diagram type"):
        parse("pie\n  \"a\": 1")
