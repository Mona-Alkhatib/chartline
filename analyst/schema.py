from __future__ import annotations

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from analyst.models_types import ColumnSummary, DType, TableSummary

_CATEGORICAL_CARDINALITY_MAX = 50


def infer_dtype(series: pd.Series) -> DType:
    if isinstance(series.dtype, pd.CategoricalDtype) and series.dtype.ordered:
        return "ordinal"
    if is_datetime64_any_dtype(series):
        return "temporal"
    if is_numeric_dtype(series):
        return "quantitative"
    return "nominal"


def summarize_dataframe(df: pd.DataFrame, name: str | None = None) -> TableSummary:
    columns: list[ColumnSummary] = []
    for col in df.columns:
        s = df[col]
        dtype = infer_dtype(s)
        null_rate = float(s.isna().mean())
        non_null = s.dropna()
        distinct_count = int(non_null.nunique())
        top = non_null.value_counts().head(5).index.tolist()
        sample_values = [str(v) for v in top]
        columns.append(ColumnSummary(
            name=str(col),
            dtype=dtype,
            null_rate=null_rate,
            distinct_count=distinct_count,
            sample_values=sample_values,
        ))
    return TableSummary(name=name, row_count=int(len(df)), columns=columns)
