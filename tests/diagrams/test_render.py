import shutil
import xml.etree.ElementTree as ET

import pytest

from mdany.diagrams import DiagramStyle, render
from mdany.diagrams.mermaid import parse
from mdany.diagrams.render import dot, seqsvg

FLOW = "flowchart TD\n  A[开始] --> B{判断}\n  B -->|是| C((结束))\n  B -.否.-> D[(库)]\n"
SEQ = "sequenceDiagram\n  participant A as 客户端\n  A->>B: 请求\n  B-->>A: 响应\n  B->>B: 自检\n"


def test_dot_source_has_shapes_styles_and_spline():
    src = dot.to_dot(parse(FLOW), DiagramStyle())
    assert "splines=spline" in src            # ortho breaks edge labels (design 10.1 item 4)
    assert "shape=diamond" in src and "shape=ellipse" in src and "shape=cylinder" in src
    assert 'label="是"' in src and "style=dashed" in src


def test_sequence_svg_is_valid_xml_with_escaped_text():
    svg = seqsvg.to_svg(parse(SEQ.replace("请求", "a<b&c")), DiagramStyle())
    root = ET.fromstring(svg)
    texts = [t.text for t in root.iter("{http://www.w3.org/2000/svg}text")]
    assert "客户端" in texts and "a<b&c" in texts
    assert 'stroke-dasharray="6 4"' in svg     # dashed reply


@pytest.mark.skipif(not shutil.which("dot"), reason="graphviz not installed")
@pytest.mark.parametrize("text", [FLOW, SEQ])
@pytest.mark.parametrize("fmt", ["svg", "png"])
def test_render_files(tmp_path, text, fmt):
    if fmt == "png" and text is SEQ and not shutil.which("rsvg-convert"):
        pytest.skip("rsvg-convert not installed")
    out = render(text, tmp_path / "fig", fmt, DiagramStyle())
    assert out.suffix == f".{fmt}" and out.stat().st_size > 0
    if fmt == "png":
        assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
