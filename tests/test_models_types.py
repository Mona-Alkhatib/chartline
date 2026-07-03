from datetime import datetime

import pytest
from pydantic import ValidationError

from chartline.models_types import (
    ColumnSummary,
    GenerationResult,
    SavedSpec,
    SchemaSummary,
    SessionRecord,
    TableSummary,
    ValidationResult,
    VegaLiteSpec,
)


def test_column_summary_dtype_enum():
    c = ColumnSummary(
        name="revenue", dtype="quantitative", null_rate=0.0,
        distinct_count=100, sample_values=["1.0", "2.0"],
    )
    assert c.dtype == "quantitative"
    with pytest.raises(ValidationError):
        ColumnSummary(name="x", dtype="numeric", null_rate=0.0, distinct_count=1, sample_values=[])


def test_schema_summary_prompt_text_lists_columns():
    schema = SchemaSummary(tables=[
        TableSummary(name="sales", row_count=100, columns=[
            ColumnSummary(name="revenue", dtype="quantitative", null_rate=0.0,
                          distinct_count=100, sample_values=["1.0", "2.0"]),
            ColumnSummary(name="region", dtype="nominal", null_rate=0.01,
                          distinct_count=4, sample_values=["NA", "EU", "APAC"]),
        ])
    ])
    text = schema.to_prompt_text()
    assert "sales" in text
    assert "revenue" in text and "quantitative" in text
    assert "region" in text and "nominal" in text


def test_vega_lite_spec_wraps_dict():
    v = VegaLiteSpec(spec={"mark": "bar", "encoding": {"x": {"field": "a"}}})
    assert v.spec["mark"] == "bar"


def test_generation_result_fields():
    v = VegaLiteSpec(spec={"mark": "bar"})
    r = GenerationResult(spec=v, model_used="claude-sonnet-4-6", retries=1)
    assert r.retries == 1


def test_validation_result_defaults():
    r = ValidationResult(valid=True)
    assert r.error is None


def test_saved_spec_roundtrip():
    s = SavedSpec(
        id="01H", session_id="sess1", parent_spec_id=None,
        user_ask="show revenue by month", spec_json='{"mark":"line"}',
        model_used="claude-opus-4-8", created_at=datetime(2026, 7, 2, 10, 0, 0),
    )
    assert s.parent_spec_id is None


def test_session_record_current_spec_optional():
    s = SessionRecord(
        id="sess1", name=None, data_source_ref="sales.csv",
        created_at=datetime.now(), last_active_at=datetime.now(),
        current_spec_id=None,
    )
    assert s.current_spec_id is None
