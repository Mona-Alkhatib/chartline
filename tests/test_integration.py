import json
from unittest.mock import MagicMock

import pandas as pd

from analyst.exporter import to_altair, to_plotly
from analyst.generator import ChartGenerator
from analyst.router import Router
from analyst.session import Session
from analyst.sources.files import FileSource
from analyst.store import SpecStore
from analyst.validator import Validator


def _fake_client(bodies):
    client = MagicMock()
    calls = iter(bodies)

    def messages_create(**kwargs):
        body = next(calls)
        msg = MagicMock()
        msg.content = [MagicMock(type="text", text=body)]
        return msg

    client.messages.create = messages_create
    return client


def test_end_to_end_upload_ask_refine_export_replay(tmp_path):
    csv = tmp_path / "sales.csv"
    pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01"]),
        "region": ["NA", "EU", "APAC"],
        "revenue": [100.0, 200.0, 300.0],
    }).to_csv(csv, index=False)

    initial = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}, "y": {"field": "revenue", "type": "quantitative"}}}'
    refined = '"mark": "line", "encoding": {"x": {"field": "date", "type": "temporal"}, "y": {"field": "revenue", "type": "quantitative"}}}'
    client = _fake_client([initial, refined])

    db = tmp_path / "s.db"
    with SpecStore(db) as store:
        gen = ChartGenerator(Router(), Validator(), client)
        session = Session.from_source(FileSource(csv), store, gen, name="sales.csv")
        s1 = session.ask("bar of revenue by region")
        assert s1.spec["mark"] == "bar"
        s2 = session.refine("switch to a line chart over time")
        assert s2.spec["mark"] == "line"

        altair_code = to_altair(s2)
        assert "mark_line" in altair_code
        plotly_code = to_plotly(s2)
        assert "px.line" in plotly_code

        session_id = session.id

    with SpecStore(db) as store2:
        specs = store2.list_specs(session_id)
        assert len(specs) == 2
        session_record = store2.get_session(session_id)
        assert session_record.current_spec_id == specs[-1].id
        latest_spec = json.loads(specs[-1].spec_json)
        assert latest_spec["mark"] == "line"
