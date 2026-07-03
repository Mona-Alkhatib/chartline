from chartline.models_types import VegaLiteSpec
from chartline.renderer import render_html, render_widget


def test_render_html_embeds_spec():
    spec = VegaLiteSpec(spec={"mark": "bar", "encoding": {}})
    html = render_html(spec)
    assert '"mark"' in html and "bar" in html
    assert "vega-lite" in html.lower()
    assert "<script" in html


def test_render_html_custom_id():
    spec = VegaLiteSpec(spec={"mark": "bar"})
    html = render_html(spec, embed_id="custom_vis")
    assert "custom_vis" in html


def test_render_widget_returns_object_with_spec():
    spec = VegaLiteSpec(spec={"mark": "bar"})
    widget = render_widget(spec)
    assert widget is not None
    assert hasattr(widget, "spec_json")
