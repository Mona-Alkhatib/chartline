from __future__ import annotations

import json
from typing import Self

import pandas as pd

from analyst.generator import ChartGenerator
from analyst.models_types import SchemaSummary, VegaLiteSpec
from analyst.sources.base import DataSource
from analyst.store import SpecStore


class Session:
    def __init__(
        self, id: str, source: DataSource, store: SpecStore, generator: ChartGenerator,
        current_spec: VegaLiteSpec | None = None,
    ) -> None:
        self.id = id
        self.source = source
        self.store = store
        self.generator = generator
        self._schema: SchemaSummary | None = None
        self._current_spec = current_spec

    @property
    def current_spec(self) -> VegaLiteSpec | None:
        return self._current_spec

    @property
    def schema(self) -> SchemaSummary:
        if self._schema is None:
            self._schema = self.source.summarize()
        return self._schema

    def ask(self, user_ask: str) -> VegaLiteSpec:
        result = self.generator.generate_initial(user_ask, self.schema)
        saved = self.store.save_spec(
            self.id, user_ask, result.spec, result.model_used, parent_spec_id=None,
        )
        self.store.update_session(self.id, saved.id)
        self._current_spec = result.spec
        return result.spec

    def refine(self, user_ask: str) -> VegaLiteSpec:
        if self._current_spec is None:
            raise RuntimeError("No current spec to refine. Call `ask()` first.")
        parent = self.store.get_session(self.id).current_spec_id
        result = self.generator.refine(user_ask, self._current_spec, self.schema)
        saved = self.store.save_spec(
            self.id, user_ask, result.spec, result.model_used, parent_spec_id=parent,
        )
        self.store.update_session(self.id, saved.id)
        self._current_spec = result.spec
        return result.spec

    @classmethod
    def from_source(
        cls, source: DataSource, store: SpecStore, generator: ChartGenerator,
        name: str | None = None,
    ) -> Self:
        record = store.create_session(data_source_ref=source.ref, name=name)
        return cls(id=record.id, source=source, store=store, generator=generator)

    @classmethod
    def from_df(
        cls, df: pd.DataFrame, store: SpecStore, generator: ChartGenerator,
        name: str | None = None,
    ) -> Self:
        raise NotImplementedError("Use from_source with a FileSource for now; from_df in phase 2.")

    @classmethod
    def load(
        cls, session_id: str, source: DataSource, store: SpecStore, generator: ChartGenerator,
    ) -> Self:
        record = store.get_session(session_id)
        current: VegaLiteSpec | None = None
        if record.current_spec_id is not None:
            saved = store.get_spec(record.current_spec_id)
            current = VegaLiteSpec(spec=json.loads(saved.spec_json))
        store.touch_session(session_id)
        return cls(
            id=session_id, source=source, store=store, generator=generator, current_spec=current,
        )
