from unittest.mock import MagicMock

import pandas as pd

from chartline.notebook.widget import NotebookSession


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


def test_notebook_session_ask_returns_widget(tmp_path):
    csv = tmp_path / "sales.csv"
    pd.DataFrame({"revenue": [1.0, 2.0], "region": ["A", "B"]}).to_csv(csv, index=False)
    body = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    client = _fake_client([body])
    ns = NotebookSession.from_file(csv, store_path=tmp_path / "s.db", client=client)
    w = ns.ask("bar of revenue by region")
    assert hasattr(w, "spec_json")


def test_notebook_session_refine_returns_widget(tmp_path):
    csv = tmp_path / "sales.csv"
    pd.DataFrame({"revenue": [1.0, 2.0], "region": ["A", "B"]}).to_csv(csv, index=False)
    body1 = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    body2 = '"mark": "line", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    client = _fake_client([body1, body2])
    ns = NotebookSession.from_file(csv, store_path=tmp_path / "s.db", client=client)
    ns.ask("bar")
    w = ns.refine("make it a line chart")
    assert "line" in w.spec_json
