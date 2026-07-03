from __future__ import annotations

import pandas as pd
import sqlalchemy as sa

from chartline.models_types import SchemaSummary, TableSummary
from chartline.schema import summarize_dataframe

_SAMPLE_ROWS = 500


class WarehouseSource:
    def __init__(self, url: str, name: str, tables: list[str] | None = None) -> None:
        self.url = url
        self.name = name
        self._tables_filter = tables
        self.engine = sa.create_engine(url)

    @property
    def ref(self) -> str:
        return self.name

    def execute(self, sql: str) -> pd.DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql_query(sa.text(sql), conn)

    def summarize(self) -> SchemaSummary:
        inspector = sa.inspect(self.engine)
        table_names = self._tables_filter or inspector.get_table_names()
        summaries: list[TableSummary] = []
        for tname in table_names:
            sample = self.execute(f'SELECT * FROM "{tname}" LIMIT {_SAMPLE_ROWS}')
            row_count = self._count(tname)
            table_summary = summarize_dataframe(sample, name=tname)
            summaries.append(TableSummary(
                name=tname, row_count=row_count, columns=table_summary.columns,
            ))
        return SchemaSummary(tables=summaries)

    def _count(self, table: str) -> int:
        result = self.execute(f'SELECT COUNT(*) AS n FROM "{table}"')
        return int(result.iloc[0]["n"])
