from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

from chartline.exporter import to_altair, to_plotly
from chartline.generator import ChartGenerator
from chartline.models_types import VegaLiteSpec
from chartline.renderer import render_streamlit
from chartline.router import Router
from chartline.session import Session
from chartline.sources.files import FileSource
from chartline.store import SpecStore
from chartline.validator import Validator

load_dotenv()

_SAMPLE_CSV = Path(__file__).resolve().parents[2] / "evals" / "fixtures" / "datasets" / "sales.csv"

_DEMO_CHARTS: dict[str, VegaLiteSpec] = {
    "Bar: revenue by region": VegaLiteSpec(spec={
        "title": "Revenue by region",
        "mark": "bar",
        "encoding": {
            "x": {
                "field": "region", "type": "nominal", "title": "Region",
                "sort": "-y",
            },
            "y": {
                "aggregate": "sum", "field": "revenue",
                "type": "quantitative", "title": "Total revenue",
            },
        },
    }),
    "Grouped bar: revenue by region and product": VegaLiteSpec(spec={
        "title": "Revenue by region and product",
        "mark": "bar",
        "encoding": {
            "x": {"field": "region", "type": "nominal", "title": "Region"},
            "xOffset": {"field": "product", "type": "nominal"},
            "y": {
                "aggregate": "sum", "field": "revenue",
                "type": "quantitative", "title": "Total revenue",
            },
            "color": {"field": "product", "type": "nominal"},
        },
    }),
    "Line: revenue over time, by product": VegaLiteSpec(spec={
        "title": "Revenue over time",
        "mark": {"type": "line", "point": True},
        "encoding": {
            "x": {"field": "date", "type": "temporal", "title": "Date"},
            "y": {
                "aggregate": "sum", "field": "revenue",
                "type": "quantitative", "title": "Revenue",
            },
            "color": {"field": "product", "type": "nominal"},
        },
    }),
    "Scatter: units vs revenue, colored by region": VegaLiteSpec(spec={
        "title": "Units vs revenue",
        "mark": {"type": "point", "size": 120, "filled": True},
        "encoding": {
            "x": {"field": "units", "type": "quantitative", "title": "Units"},
            "y": {"field": "revenue", "type": "quantitative", "title": "Revenue"},
            "color": {"field": "region", "type": "nominal"},
            "shape": {"field": "product", "type": "nominal"},
        },
    }),
    "Heatmap: revenue by month and region": VegaLiteSpec(spec={
        "title": "Revenue by month and region",
        "mark": "rect",
        "encoding": {
            "x": {
                "field": "date", "type": "ordinal", "timeUnit": "yearmonth",
                "title": "Month",
            },
            "y": {"field": "region", "type": "nominal", "title": "Region"},
            "color": {
                "aggregate": "sum", "field": "revenue",
                "type": "quantitative", "title": "Total revenue",
            },
        },
    }),
}
_DEFAULT_DEMO = "Bar: revenue by region"


def _store_path() -> Path:
    raw = os.environ.get("CHARTLINE_STORE_PATH", "~/.chartline/store.db")
    return Path(raw).expanduser()


def _get_client() -> Anthropic:
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _init_state() -> None:
    st.session_state.setdefault("session_obj", None)
    st.session_state.setdefault("df", None)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("demo_spec", None)
    st.session_state.setdefault("demo_choice", _DEFAULT_DEMO)
    st.session_state.setdefault("is_sample", False)
    st.session_state.setdefault("last_upload_id", None)
    st.session_state.setdefault("bootstrapped", False)
    if not st.session_state.bootstrapped:
        _load_sample()
        st.session_state.bootstrapped = True


def _load_source(uploaded) -> tuple[FileSource, pd.DataFrame]:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name
    source = FileSource(Path(tmp_path))
    return source, source.load()


def _make_session(source: FileSource) -> Session | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    store = SpecStore(_store_path()).__enter__()
    generator = ChartGenerator(Router(), Validator(), _get_client())
    return Session.from_source(source, store, generator, name=source.path.name)


def _load_sample() -> None:
    source = FileSource(_SAMPLE_CSV)
    st.session_state.df = source.load()
    st.session_state.session_obj = _make_session(source)
    st.session_state.demo_spec = _DEMO_CHARTS[_DEFAULT_DEMO]
    st.session_state.demo_choice = _DEFAULT_DEMO
    st.session_state.history = []
    st.session_state.is_sample = True


def main() -> None:
    st.set_page_config(page_title="Chartline", layout="wide")
    _init_state()
    st.title("Chartline")

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if not has_key:
        st.info(
            "**Demo mode.** Sample data is preloaded and chat is disabled. "
            "Pick a chart type from the gallery on the left, or upload your own CSV "
            "to see how Chartline reads a schema and exports code."
        )

    left, center, right = st.columns([1, 2, 1])

    with left:
        if st.session_state.is_sample:
            st.subheader("Demo gallery")
            picked = st.radio(
                "Sample chart types",
                list(_DEMO_CHARTS.keys()),
                index=list(_DEMO_CHARTS.keys()).index(st.session_state.demo_choice),
                key="demo_gallery_pick",
                label_visibility="collapsed",
            )
            if picked != st.session_state.demo_choice:
                st.session_state.demo_choice = picked
                st.session_state.demo_spec = _DEMO_CHARTS[picked]
                st.rerun()
            st.divider()

        st.subheader("Data")
        if st.button("Reset to sample data", use_container_width=True):
            _load_sample()
            st.rerun()
        uploaded = st.file_uploader(
            "or upload your own CSV / Parquet / Excel file",
            type=["csv", "parquet", "xlsx"],
        )
        if uploaded is not None:
            file_id = f"{uploaded.name}-{uploaded.size}"
            if st.session_state.last_upload_id != file_id:
                source, df = _load_source(uploaded)
                st.session_state.session_obj = _make_session(source)
                st.session_state.df = df
                st.session_state.demo_spec = None
                st.session_state.is_sample = False
                st.session_state.last_upload_id = file_id
                st.rerun()
        if st.session_state.df is not None:
            st.write("Preview")
            st.dataframe(st.session_state.df.head(10))

    with center:
        st.subheader("Chart")
        session = st.session_state.session_obj
        demo_spec = st.session_state.demo_spec
        active_spec = None
        if session is not None and session.current_spec is not None:
            active_spec = session.current_spec
        elif demo_spec is not None:
            active_spec = demo_spec

        if active_spec is not None and st.session_state.df is not None:
            render_streamlit(active_spec, st.session_state.df)
        else:
            st.info("Load the sample or upload data to see a chart here.")

    with right:
        session = st.session_state.session_obj
        if has_key:
            st.subheader("Chat")
            for entry in st.session_state.history:
                role = "You" if entry["role"] == "user" else "Chartline"
                st.markdown(f"**{role}:** {entry['text']}")
            prompt = st.chat_input("Describe or refine a chart")
            if prompt and session is not None:
                st.session_state.history.append({"role": "user", "text": prompt})
                if session.current_spec is None:
                    spec = session.ask(prompt)
                else:
                    spec = session.refine(prompt)
                marker = spec.spec.get("mark")
                st.session_state.history.append(
                    {"role": "assistant", "text": f"Updated. mark={marker}"}
                )
                st.rerun()
        else:
            st.subheader("What chat does")
            st.markdown(
                "In the full app, this panel talks to Claude:\n\n"
                "- **Ask** for a new chart: *\"revenue by region as a line chart\"*\n"
                "- **Refine** the current one: *\"log-scale the y-axis\"*, "
                "*\"split by product\"*\n"
                "- **Query a warehouse** in plain English via text-to-SQL "
                "(DuckDB, Postgres, Snowflake, BigQuery)."
            )

        st.divider()
        st.subheader("Export")
        export_spec = None
        if session is not None and session.current_spec is not None:
            export_spec = session.current_spec
        elif st.session_state.demo_spec is not None:
            export_spec = st.session_state.demo_spec

        if export_spec is not None:
            fmt = st.selectbox("Format", ["Vega-Lite JSON", "Altair", "Plotly"])
            if fmt == "Vega-Lite JSON":
                st.code(json.dumps(export_spec.spec, indent=2), language="json")
            elif fmt == "Altair":
                st.code(to_altair(export_spec), language="python")
            else:
                st.code(to_plotly(export_spec), language="python")


if __name__ == "__main__":
    main()
