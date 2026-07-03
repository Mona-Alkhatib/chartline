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
