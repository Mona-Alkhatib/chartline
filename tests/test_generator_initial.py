from unittest.mock import MagicMock

from chartline.generator import ChartGenerator
from chartline.models_types import ColumnSummary, SchemaSummary, TableSummary
from chartline.router import MODEL_OPUS, Router
from chartline.validator import Validator


def _schema() -> SchemaSummary:
    return SchemaSummary(tables=[TableSummary(name="sales", row_count=10, columns=[
        ColumnSummary(name="revenue", dtype="quantitative", null_rate=0.0,
                      distinct_count=10, sample_values=["1", "2"]),
        ColumnSummary(name="region", dtype="nominal", null_rate=0.0,
                      distinct_count=3, sample_values=["NA", "EU"]),
    ])])


def _fake_client(responses: list[str]) -> MagicMock:
    """Fake Anthropic client. responses is a list of text bodies (without the leading `{`)."""
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


def test_generate_initial_returns_valid_spec():
    body = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}, "y": {"field": "revenue", "type": "quantitative"}}}'
    gen = ChartGenerator(Router(), Validator(), _fake_client([body]))
    result = gen.generate_initial("bar of revenue by region", _schema())
    assert result.spec.spec["mark"] == "bar"
    assert result.model_used == MODEL_OPUS
    assert result.retries == 0


def test_generate_initial_retries_on_bad_field():
    bad = '"mark": "bar", "encoding": {"x": {"field": "not_a_col", "type": "nominal"}}}'
    good = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    gen = ChartGenerator(Router(), Validator(), _fake_client([bad, good]))
    result = gen.generate_initial("chart", _schema())
    assert result.retries == 1
    assert result.spec.spec["encoding"]["x"]["field"] == "region"


def test_generate_initial_gives_up_after_max_retries():
    bad = '"mark": "bar", "encoding": {"x": {"field": "not_a_col", "type": "nominal"}}}'
    gen = ChartGenerator(Router(), Validator(), _fake_client([bad] * 4), max_retries=3)
    try:
        gen.generate_initial("chart", _schema())
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_generate_initial_recovers_from_bad_json():
    invalid = "this is not JSON at all}"
    good = '"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"}}}'
    gen = ChartGenerator(Router(), Validator(), _fake_client([invalid, good]))
    result = gen.generate_initial("chart", _schema())
    assert result.retries == 1
    assert result.spec.spec["mark"] == "bar"
