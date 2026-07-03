from __future__ import annotations

import json

from analyst.models_types import VegaLiteSpec

_ALTAIR_MARKS = {
    "bar": "mark_bar", "line": "mark_line", "area": "mark_area",
    "point": "mark_point", "circle": "mark_circle", "square": "mark_square",
    "tick": "mark_tick", "rect": "mark_rect", "rule": "mark_rule",
    "text": "mark_text", "boxplot": "mark_boxplot", "arc": "mark_arc",
}


def to_altair(spec: VegaLiteSpec, dataframe_var: str = "df") -> str:
    s = spec.spec
    mark = s.get("mark")
    mark_type = mark.get("type") if isinstance(mark, dict) else mark
    altair_mark = _ALTAIR_MARKS.get(str(mark_type), "mark_bar")

    encoding = s.get("encoding") or {}
    encoding_kwargs: list[str] = []
    for channel, definition in encoding.items():
        if isinstance(definition, dict):
            encoding_kwargs.append(f"{channel}=alt.{channel.capitalize()}(**{json.dumps(definition)})")

    encoding_str = ", ".join(encoding_kwargs)
    title = s.get("title")
    props: list[str] = []
    if isinstance(title, str):
        props.append(f'title={json.dumps(title)}')

    return "\n".join([
        "import altair as alt",
        "",
        f"chart = (",
        f"    alt.Chart({dataframe_var})",
        f"    .{altair_mark}()",
        f"    .encode({encoding_str})",
        *(f"    .properties({p})" for p in props),
        f")",
    ])


_PLOTLY_FNS = {
    "bar": "bar", "line": "line", "area": "area",
    "point": "scatter", "circle": "scatter", "square": "scatter",
    "boxplot": "box", "arc": "pie", "text": "scatter", "rect": "density_heatmap",
    "tick": "scatter", "rule": "line",
}


def to_plotly(spec: VegaLiteSpec, dataframe_var: str = "df") -> str:
    s = spec.spec
    mark = s.get("mark")
    mark_type = mark.get("type") if isinstance(mark, dict) else mark
    fn = _PLOTLY_FNS.get(str(mark_type), "bar")

    encoding = s.get("encoding") or {}
    kwargs: list[str] = [f"{dataframe_var}"]
    channel_map = {"x": "x", "y": "y", "color": "color", "size": "size", "shape": "symbol"}
    for channel, key in channel_map.items():
        definition = encoding.get(channel)
        if isinstance(definition, dict) and isinstance(definition.get("field"), str):
            kwargs.append(f"{key}={definition['field']!r}")

    title = s.get("title")
    if isinstance(title, str):
        kwargs.append(f"title={title!r}")

    return "\n".join([
        "import plotly.express as px",
        "",
        f"fig = px.{fn}({', '.join(kwargs)})",
    ])
