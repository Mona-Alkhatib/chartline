from analyst.exporter import to_altair
from analyst.models_types import VegaLiteSpec


def test_altair_bar_chart_compiles():
    spec = VegaLiteSpec(spec={
        "mark": "bar",
        "encoding": {
            "x": {"field": "region", "type": "nominal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    })
    code = to_altair(spec)
    assert "mark_bar" in code
    assert "region" in code
    assert "revenue" in code


def test_altair_line_chart():
    spec = VegaLiteSpec(spec={
        "mark": "line",
        "encoding": {
            "x": {"field": "month", "type": "temporal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    })
    code = to_altair(spec)
    assert "mark_line" in code


def test_altair_custom_var_name():
    spec = VegaLiteSpec(spec={"mark": "bar", "encoding": {}})
    code = to_altair(spec, dataframe_var="sales_df")
    assert "sales_df" in code


def test_altair_code_is_valid_python():
    spec = VegaLiteSpec(spec={
        "mark": "bar",
        "encoding": {
            "x": {"field": "region", "type": "nominal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    })
    code = to_altair(spec)
    compile(code, "<test>", "exec")


def test_altair_mark_as_dict():
    spec = VegaLiteSpec(spec={
        "mark": {"type": "line", "opacity": 0.5},
        "encoding": {"x": {"field": "month", "type": "temporal"}},
    })
    code = to_altair(spec)
    assert "mark_line" in code


def test_altair_with_title_emits_properties():
    spec = VegaLiteSpec(spec={
        "mark": "bar",
        "encoding": {"x": {"field": "region", "type": "nominal"}},
        "title": "Weekly Revenue",
    })
    code = to_altair(spec)
    assert ".properties(" in code
    assert "Weekly Revenue" in code
