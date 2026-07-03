from __future__ import annotations

import atexit
import contextlib
import os
from pathlib import Path
from typing import Any, Self

from chartline.generator import ChartGenerator
from chartline.renderer import render_widget
from chartline.router import Router
from chartline.session import Session
from chartline.sources.files import FileSource
from chartline.sources.warehouse import WarehouseSource
from chartline.store import SpecStore
from chartline.validator import Validator


def _default_store_path() -> Path:
    raw = os.environ.get("CHARTLINE_STORE_PATH", "~/.chartline/store.db")
    return Path(raw).expanduser()


def _default_client() -> Any:
    from anthropic import Anthropic
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


class NotebookSession:
    def __init__(self, session: Session, store: SpecStore) -> None:
        self.session = session
        self._store = store
        self._closed = False
        atexit.register(self.close)

    @classmethod
    def from_file(
        cls, path: Path | str, store_path: Path | str | None = None,
        client: Any | None = None,
    ) -> Self:
        source = FileSource(path)
        store = SpecStore(Path(store_path) if store_path else _default_store_path())
        store.__enter__()
        generator = ChartGenerator(Router(), Validator(), client or _default_client())
        session = Session.from_source(source, store, generator, name=source.path.name)
        return cls(session, store)

    @classmethod
    def from_warehouse(
        cls, url: str, name: str, store_path: Path | str | None = None,
        client: Any | None = None,
    ) -> Self:
        source = WarehouseSource(url, name=name)
        store = SpecStore(Path(store_path) if store_path else _default_store_path())
        store.__enter__()
        generator = ChartGenerator(Router(), Validator(), client or _default_client())
        session = Session.from_source(source, store, generator, name=name)
        return cls(session, store)

    def ask(self, user_ask: str):
        spec = self.session.ask(user_ask)
        return render_widget(spec)

    def refine(self, user_ask: str):
        spec = self.session.refine(user_ask)
        return render_widget(spec)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        with contextlib.suppress(Exception):
            self._store.__exit__(None, None, None)
