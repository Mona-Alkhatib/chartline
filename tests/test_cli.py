import json

from typer.testing import CliRunner

from chartline.cli import app
from chartline.models_types import VegaLiteSpec
from chartline.store import SpecStore

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "chartline" in result.stdout.lower()


def test_list_sessions(tmp_path, monkeypatch):
    db = tmp_path / "s.db"
    monkeypatch.setenv("CHARTLINE_STORE_PATH", str(db))
    with SpecStore(db) as store:
        store.create_session(data_source_ref="sales.csv", name="July")
    result = runner.invoke(app, ["list-sessions"])
    assert result.exit_code == 0
    assert "sales.csv" in result.stdout


def test_export_session(tmp_path, monkeypatch):
    db = tmp_path / "s.db"
    monkeypatch.setenv("CHARTLINE_STORE_PATH", str(db))
    with SpecStore(db) as store:
        sess = store.create_session(data_source_ref="sales.csv")
        store.save_spec(sess.id, "a", VegaLiteSpec(spec={"mark": "bar"}), "claude-opus-4-8", None)
    out = tmp_path / "out.json"
    result = runner.invoke(app, ["export", sess.id, "--out", str(out)])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data["session"]["id"] == sess.id
    assert len(data["specs"]) == 1
