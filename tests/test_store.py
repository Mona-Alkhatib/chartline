import json
from pathlib import Path

from chartline.models_types import VegaLiteSpec
from chartline.store import SpecStore


def _store(tmp_path: Path) -> SpecStore:
    return SpecStore(tmp_path / "store.db")


def test_create_and_get_session(tmp_path):
    with _store(tmp_path) as store:
        s = store.create_session(data_source_ref="sales.csv", name="July analysis")
        assert s.id
        assert s.current_spec_id is None
        got = store.get_session(s.id)
        assert got.name == "July analysis"


def test_save_and_get_spec(tmp_path):
    with _store(tmp_path) as store:
        sess = store.create_session(data_source_ref="sales.csv")
        spec = VegaLiteSpec(spec={"mark": "bar"})
        saved = store.save_spec(sess.id, "show sales", spec, "claude-opus-4-8", None)
        got = store.get_spec(saved.id)
        assert json.loads(got.spec_json)["mark"] == "bar"
        assert got.model_used == "claude-opus-4-8"


def test_list_specs_in_order(tmp_path):
    with _store(tmp_path) as store:
        sess = store.create_session(data_source_ref="sales.csv")
        first = store.save_spec(sess.id, "a", VegaLiteSpec(spec={"mark": "bar"}), "claude-opus-4-8", None)
        second = store.save_spec(sess.id, "b", VegaLiteSpec(spec={"mark": "line"}), "claude-sonnet-4-6", first.id)
        specs = store.list_specs(sess.id)
        assert [s.id for s in specs] == [first.id, second.id]
        assert specs[1].parent_spec_id == first.id


def test_update_and_touch_session(tmp_path):
    with _store(tmp_path) as store:
        sess = store.create_session(data_source_ref="sales.csv")
        saved = store.save_spec(sess.id, "a", VegaLiteSpec(spec={"mark": "bar"}), "claude-opus-4-8", None)
        store.update_session(sess.id, saved.id)
        assert store.get_session(sess.id).current_spec_id == saved.id


def test_list_sessions_orders_by_recency(tmp_path):
    with _store(tmp_path) as store:
        a = store.create_session(data_source_ref="a.csv")
        b = store.create_session(data_source_ref="b.csv")
        store.touch_session(a.id)
        listed = [s.id for s in store.list_sessions()]
        assert listed[0] == a.id
        assert b.id in listed
