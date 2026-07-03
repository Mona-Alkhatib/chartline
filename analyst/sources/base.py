from __future__ import annotations

from typing import Protocol, runtime_checkable

from analyst.models_types import SchemaSummary


@runtime_checkable
class DataSource(Protocol):
    @property
    def ref(self) -> str: ...
    def summarize(self) -> SchemaSummary: ...
