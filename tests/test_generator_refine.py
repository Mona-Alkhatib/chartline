from unittest.mock import MagicMock

from chartline.generator import ChartGenerator
from chartline.models_types import ColumnSummary, SchemaSummary, TableSummary, VegaLiteSpec
from chartline.router import MODEL_SONNET, Router
from chartline.validator import Validator


def _schema() -> SchemaSummary:
    return SchemaSummary(tables=[TableSummary(name="sales", row_count=10, columns=[
        ColumnSummary(name="revenue", dtype="quantitative", null_rate=0.0,
                      distinct_count=10, sample_values=["1", "2"]),
        ColumnSummary(name="region", dtype="nominal", null_rate=0.0,
                      distinct_count=3, sample_values=["NA", "EU"]),
    ])])


def _fake_client(responses: list[str]) -> MagicMock:
    client = MagicMock()
    calls = iter(responses)

    def messages_create(**kwargs):
        body = next(calls)
        msg = MagicMock()
        msg.content = [MagicMock(type="text", text=body)]
        msg.model = kwargs["model"]
        return msg

    client.messages.create = messages_create
    return client


def test_refine_uses_sonnet():
    body = '"mark": "line", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    gen = ChartGenerator(Router(), Validator(), _fake_client([body]))
    prev = VegaLiteSpec(spec={"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}})
    result = gen.refine("make it a line chart", prev, _schema())
    assert result.model_used == MODEL_SONNET
    assert result.spec.spec["mark"] == "line"


def test_refine_retries_on_invalid():
    bad = '"mark": "bar", "encoding": {"x": {"field": "wrong", "type": "nominal"}}}'
    good = '"mark": "line", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    gen = ChartGenerator(Router(), Validator(), _fake_client([bad, good]))
    prev = VegaLiteSpec(spec={"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}})
    result = gen.refine("make it a line chart", prev, _schema())
    assert result.retries == 1
