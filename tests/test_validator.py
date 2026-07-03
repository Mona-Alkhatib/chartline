from analyst.models_types import ColumnSummary, SchemaSummary, TableSummary
from analyst.validator import Validator


def _schema() -> SchemaSummary:
    return SchemaSummary(tables=[TableSummary(name="sales", row_count=10, columns=[
        ColumnSummary(name="revenue", dtype="quantitative", null_rate=0.0,
                      distinct_count=10, sample_values=["1", "2"]),
        ColumnSummary(name="month", dtype="temporal", null_rate=0.0,
                      distinct_count=5, sample_values=["2026-01", "2026-02"]),
        ColumnSummary(name="region", dtype="nominal", null_rate=0.0,
                      distinct_count=3, sample_values=["NA", "EU"]),
    ])])


def test_valid_bar_chart():
    v = Validator()
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "mark": "bar",
        "encoding": {
            "x": {"field": "region", "type": "nominal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    }
    r = v.validate(spec, _schema())
    assert r.valid, r.error


def test_rejects_hallucinated_field():
    v = Validator()
    spec = {
        "mark": "bar",
        "encoding": {"x": {"field": "not_a_column", "type": "nominal"}},
    }
    r = v.validate(spec, _schema())
    assert not r.valid
    assert "not_a_column" in r.error


def test_rejects_missing_mark():
    v = Validator()
    spec = {"encoding": {"x": {"field": "region", "type": "nominal"}}}
    r = v.validate(spec, _schema())
    assert not r.valid
    assert r.error is not None
    assert "mark" in r.error


def test_rejects_unsupported_mark():
    v = Validator()
    spec = {
        "mark": "sankey",
        "encoding": {"x": {"field": "region", "type": "nominal"}},
    }
    r = v.validate(spec, _schema())
    assert not r.valid
    assert "Unsupported mark" in r.error


def test_rejects_non_dict():
    v = Validator()
    r = v.validate("not a spec", _schema())  # type: ignore[arg-type]
    assert not r.valid


def test_accepts_line_with_temporal():
    v = Validator()
    spec = {
        "mark": "line",
        "encoding": {
            "x": {"field": "month", "type": "temporal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    }
    r = v.validate(spec, _schema())
    assert r.valid, r.error
