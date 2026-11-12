import pytest

from mdany.diagrams.mermaid import Sequence, UnsupportedSyntax, parse


def test_participants_messages_and_self_call():
    seq = parse(
        "sequenceDiagram\n"
        "  participant B as 浏览器\n"
        "  participant S\n"
        "  B->>S: 提交\n"
        "  S->>S: 校验\n"
        "  S-->>B: 返回令牌\n"
        "  S->>D: 查询\n"            # D is not declared: added in order of use
    )
    assert isinstance(seq, Sequence)
    assert seq.participants == [("B", "浏览器"), ("S", "S"), ("D", "D")]
    assert [(m.src, m.dst, m.text, m.dashed) for m in seq.messages] == [
        ("B", "S", "提交", False), ("S", "S", "校验", False),
        ("S", "B", "返回令牌", True), ("S", "D", "查询", False),
    ]


@pytest.mark.parametrize("line", ["Note right of A: x", "loop 每分钟", "A->B: 单箭头", "actor A"])
def test_unsupported_syntax(line):
    with pytest.raises(UnsupportedSyntax) as info:
        parse(f"sequenceDiagram\n  participant A\n  {line}\n")
    assert info.value.line_no == 3
