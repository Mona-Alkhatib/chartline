from unittest.mock import MagicMock

import pandas as pd

from chartline.generator import ChartGenerator
from chartline.router import Router
from chartline.session import Session
from chartline.sources.files import FileSource
from chartline.store import SpecStore
from chartline.validator import Validator


def _fake_client(responses):
    client = MagicMock()
    calls = iter(responses)

    def messages_create(**kwargs):
        body = next(calls)
        msg = MagicMock()
        msg.content = [MagicMock(type="text", text=body)]
        return msg

    client.messages.create = messages_create
    return client


def _write_csv(tmp_path):
    p = tmp_path / "sales.csv"
    pd.DataFrame({"revenue": [1.0, 2.0], "region": ["A", "B"]}).to_csv(p, index=False)
    return p


def test_session_ask_persists_spec(tmp_path):
    csv = _write_csv(tmp_path)
    body = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    client = _fake_client([body])
    with SpecStore(tmp_path / "s.db") as store:
        gen = ChartGenerator(Router(), Validator(), client)
        session = Session.from_source(FileSource(csv), store, gen)
        spec = session.ask("bar of revenue by region")
        assert spec.spec["mark"] == "bar"
        specs = store.list_specs(session.id)
        assert len(specs) == 1


def test_session_refine_uses_previous(tmp_path):
    csv = _write_csv(tmp_path)
    body1 = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    body2 = '"mark": "line", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    client = _fake_client([body1, body2])
    with SpecStore(tmp_path / "s.db") as store:
        gen = ChartGenerator(Router(), Validator(), client)
        session = Session.from_source(FileSource(csv), store, gen)
        session.ask("bar")
        refined = session.refine("make it a line chart")
        assert refined.spec["mark"] == "line"
        assert len(store.list_specs(session.id)) == 2


def test_session_load_restores_current_spec(tmp_path):
    csv = _write_csv(tmp_path)
    body = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    client = _fake_client([body])
    with SpecStore(tmp_path / "s.db") as store:
        gen = ChartGenerator(Router(), Validator(), client)
        session = Session.from_source(FileSource(csv), store, gen)
        session.ask("bar")
        session_id = session.id
    with SpecStore(tmp_path / "s.db") as store2:
        gen2 = ChartGenerator(Router(), Validator(), _fake_client([]))
        restored = Session.load(session_id, FileSource(csv), store2, gen2)
        assert restored.current_spec is not None
        assert restored.current_spec.spec["mark"] == "bar"
