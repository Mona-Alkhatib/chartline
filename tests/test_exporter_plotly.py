from analyst.exporter import to_plotly
from analyst.models_types import VegaLiteSpec


def test_plotly_bar():
    spec = VegaLiteSpec(spec={
        "mark": "bar",
        "encoding": {
            "x": {"field": "region", "type": "nominal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    })
    code = to_plotly(spec)
    assert "px.bar" in code
    assert "x='region'" in code or 'x="region"' in code


def test_plotly_line():
    spec = VegaLiteSpec(spec={
        "mark": "line",
        "encoding": {
            "x": {"field": "month", "type": "temporal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    })
    code = to_plotly(spec)
    assert "px.line" in code


def test_plotly_code_compiles():
    spec = VegaLiteSpec(spec={
        "mark": "bar",
        "encoding": {"x": {"field": "region", "type": "nominal"}, "y": {"field": "rev", "type": "quantitative"}},
    })
    compile(to_plotly(spec), "<test>", "exec")


def test_plotly_with_color():
    spec = VegaLiteSpec(spec={
        "mark": "bar",
        "encoding": {
            "x": {"field": "region", "type": "nominal"},
            "y": {"field": "revenue", "type": "quantitative"},
            "color": {"field": "product", "type": "nominal"},
        },
    })
    code = to_plotly(spec)
    assert "color=" in code
