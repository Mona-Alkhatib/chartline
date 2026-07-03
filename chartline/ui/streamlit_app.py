from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

from analyst.exporter import to_altair, to_plotly
from analyst.generator import ChartGenerator
from analyst.renderer import render_streamlit
from analyst.router import Router
from analyst.session import Session
from analyst.sources.files import FileSource
from analyst.store import SpecStore
from analyst.validator import Validator

load_dotenv()


def _store_path() -> Path:
    raw = os.environ.get("CHARTLINE_STORE_PATH", "~/.chartline/store.db")
    return Path(raw).expanduser()


def _get_client() -> Anthropic:
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _init_state() -> None:
    st.session_state.setdefault("session_obj", None)
    st.session_state.setdefault("df", None)
    st.session_state.setdefault("history", [])


def _load_source(uploaded) -> tuple[FileSource, pd.DataFrame]:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name
    source = FileSource(Path(tmp_path))
    return source, source.load()


def _make_session(source: FileSource) -> Session:
    store = SpecStore(_store_path()).__enter__()
    generator = ChartGenerator(Router(), Validator(), _get_client())
    return Session.from_source(source, store, generator, name=source.path.name)


def main() -> None:
    st.set_page_config(page_title="Chartline", layout="wide")
    _init_state()
    st.title("Chartline")

    left, center, right = st.columns([1, 2, 1])

    with left:
        st.subheader("Data")
        uploaded = st.file_uploader("Upload a CSV / Parquet / Excel file", type=["csv", "parquet", "xlsx"])
        if uploaded is not None and st.session_state.session_obj is None:
            source, df = _load_source(uploaded)
            st.session_state.session_obj = _make_session(source)
            st.session_state.df = df
        if st.session_state.df is not None:
            st.write("Preview")
            st.dataframe(st.session_state.df.head(10))

    with center:
        st.subheader("Chart")
        session = st.session_state.session_obj
        if session is not None and session.current_spec is not None:
            render_streamlit(session.current_spec, st.session_state.df)
        else:
            st.info("Upload data and ask for a chart to get started.")

    with right:
        st.subheader("Chat")
        session = st.session_state.session_obj
        for entry in st.session_state.history:
            role = "You" if entry["role"] == "user" else "Chartline"
            st.markdown(f"**{role}:** {entry['text']}")
        prompt = st.chat_input("Describe or refine a chart")
        if prompt and session is not None:
            st.session_state.history.append({"role": "user", "text": prompt})
            spec = session.ask(prompt) if session.current_spec is None else session.refine(prompt)
            marker = spec.spec.get("mark")
            st.session_state.history.append(
                {"role": "assistant", "text": f"Updated. mark={marker}"}
            )
            st.rerun()

        st.divider()
        st.subheader("Export")
        if session is not None and session.current_spec is not None:
            fmt = st.selectbox("Format", ["Vega-Lite JSON", "Altair", "Plotly"])
            if fmt == "Vega-Lite JSON":
                st.code(json.dumps(session.current_spec.spec, indent=2), language="json")
            elif fmt == "Altair":
                st.code(to_altair(session.current_spec), language="python")
            else:
                st.code(to_plotly(session.current_spec), language="python")


if __name__ == "__main__":
    main()
