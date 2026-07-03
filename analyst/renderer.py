from __future__ import annotations

import json
from string import Template

import anywidget
import traitlets

from analyst.models_types import VegaLiteSpec

_HTML_TEMPLATE = Template("""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
</head>
<body>
  <div id="$embed_id"></div>
  <script>
    vegaEmbed("#$embed_id", $spec_json, { actions: false });
  </script>
</body>
</html>
""")


def render_html(spec: VegaLiteSpec, embed_id: str = "vis") -> str:
    return _HTML_TEMPLATE.substitute(embed_id=embed_id, spec_json=json.dumps(spec.spec))


_WIDGET_ESM = """
import vegaEmbed from "https://cdn.jsdelivr.net/npm/vega-embed@6/+esm";

async function render({ model, el }) {
  el.innerHTML = "";
  const div = document.createElement("div");
  el.appendChild(div);
  const spec = JSON.parse(model.get("spec_json"));
  await vegaEmbed(div, spec, { actions: false });
  model.on("change:spec_json", async () => {
    div.innerHTML = "";
    const nextSpec = JSON.parse(model.get("spec_json"));
    await vegaEmbed(div, nextSpec, { actions: false });
  });
}

export default { render };
"""


class _ChartWidget(anywidget.AnyWidget):
    _esm = _WIDGET_ESM
    spec_json = traitlets.Unicode("").tag(sync=True)


def render_widget(spec: VegaLiteSpec) -> _ChartWidget:
    return _ChartWidget(spec_json=json.dumps(spec.spec))


def render_streamlit(spec: VegaLiteSpec, df) -> None:
    import streamlit as st

    st.vega_lite_chart(df, spec.spec, use_container_width=True)
