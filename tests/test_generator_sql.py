from unittest.mock import MagicMock

from analyst.generator import ChartGenerator
from analyst.models_types import ColumnSummary, SchemaSummary, TableSummary
from analyst.router import MODEL_OPUS, Router
from analyst.validator import Validator


def _schema() -> SchemaSummary:
    return SchemaSummary(tables=[
        TableSummary(name="orders", row_count=100, columns=[
            ColumnSummary(name="user_id", dtype="quantitative", null_rate=0.0,
                          distinct_count=50, sample_values=["1", "2"]),
            ColumnSummary(name="amount", dtype="quantitative", null_rate=0.0,
                          distinct_count=90, sample_values=["10", "20"]),
        ]),
        TableSummary(name="users", row_count=50, columns=[
            ColumnSummary(name="id", dtype="quantitative", null_rate=0.0,
                          distinct_count=50, sample_values=["1", "2"]),
            ColumnSummary(name="region", dtype="nominal", null_rate=0.0,
                          distinct_count=4, sample_values=["NA", "EU"]),
        ]),
    ])


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


def test_text_to_sql_returns_valid_sql():
    sql = "SELECT SUM(amount) AS total FROM orders WHERE user_id = 1"
    gen = ChartGenerator(Router(), Validator(), _fake_client([sql]))
    result = gen.text_to_sql("total spend for user 1", _schema())
    assert result.strip().upper().startswith("SELECT")


def test_text_to_sql_retries_on_unparseable():
    bad = "not sql at all"
    good = "SELECT COUNT(*) FROM users"
    gen = ChartGenerator(Router(), Validator(), _fake_client([bad, good]))
    result = gen.text_to_sql("how many users", _schema())
    assert "COUNT" in result.upper()


def test_text_to_sql_uses_opus():
    sql = "SELECT 1"
    fake = _fake_client([sql])
    gen = ChartGenerator(Router(), Validator(), fake)
    gen.text_to_sql("q", _schema())
    _ = MODEL_OPUS
