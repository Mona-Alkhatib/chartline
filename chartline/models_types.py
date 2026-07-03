from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

DType = Literal["quantitative", "ordinal", "nominal", "temporal"]


class ColumnSummary(BaseModel):
    name: str
    dtype: DType
    null_rate: float
    distinct_count: int
    sample_values: list[str]


class TableSummary(BaseModel):
    name: str | None
    row_count: int
    columns: list[ColumnSummary]


class SchemaSummary(BaseModel):
    tables: list[TableSummary]

    def to_prompt_text(self) -> str:
        lines: list[str] = []
        for t in self.tables:
            table_name = t.name or "<unnamed>"
            lines.append(f"Table: {table_name} ({t.row_count} rows)")
            for c in t.columns:
                samples = ", ".join(c.sample_values[:5])
                lines.append(
                    f"  - {c.name} [{c.dtype}] "
                    f"null_rate={c.null_rate:.2f} distinct={c.distinct_count} samples=[{samples}]"
                )
        return "\n".join(lines)


class VegaLiteSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    spec: dict[str, Any]


class GenerationResult(BaseModel):
    spec: VegaLiteSpec
    model_used: str
    retries: int


class ValidationResult(BaseModel):
    valid: bool
    error: str | None = None


class SavedSpec(BaseModel):
    id: str
    session_id: str
    parent_spec_id: str | None
    user_ask: str
    spec_json: str
    model_used: str
    created_at: datetime


class SessionRecord(BaseModel):
    id: str
    name: str | None
    data_source_ref: str
    created_at: datetime
    last_active_at: datetime
    current_spec_id: str | None
