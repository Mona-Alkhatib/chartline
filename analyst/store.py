from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Self

from analyst.models_types import SavedSpec, SessionRecord, VegaLiteSpec

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT,
    data_source_ref TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    current_spec_id TEXT
);
CREATE TABLE IF NOT EXISTS specs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    parent_spec_id TEXT,
    user_ask TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    model_used TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_specs_session ON specs(session_id, created_at);
"""


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


class SpecStore:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> Self:
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        return self

    def __exit__(self, *args: object) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SpecStore not opened; use `with SpecStore(...) as store:`")
        return self._conn

    def create_session(self, data_source_ref: str, name: str | None = None) -> SessionRecord:
        now = datetime.utcnow().isoformat()
        sid = _new_id()
        self.conn.execute(
            "INSERT INTO sessions (id, name, data_source_ref, created_at, last_active_at, current_spec_id) "
            "VALUES (?, ?, ?, ?, ?, NULL)",
            (sid, name, data_source_ref, now, now),
        )
        self.conn.commit()
        return SessionRecord(
            id=sid, name=name, data_source_ref=data_source_ref,
            created_at=datetime.fromisoformat(now), last_active_at=datetime.fromisoformat(now),
            current_spec_id=None,
        )

    def get_session(self, session_id: str) -> SessionRecord:
        row = self.conn.execute(
            "SELECT id, name, data_source_ref, created_at, last_active_at, current_spec_id "
            "FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
        if row is None:
            raise KeyError(session_id)
        return SessionRecord(
            id=row[0], name=row[1], data_source_ref=row[2],
            created_at=datetime.fromisoformat(row[3]),
            last_active_at=datetime.fromisoformat(row[4]),
            current_spec_id=row[5],
        )

    def list_sessions(self) -> list[SessionRecord]:
        rows = self.conn.execute(
            "SELECT id, name, data_source_ref, created_at, last_active_at, current_spec_id "
            "FROM sessions ORDER BY last_active_at DESC",
        ).fetchall()
        return [
            SessionRecord(
                id=r[0], name=r[1], data_source_ref=r[2],
                created_at=datetime.fromisoformat(r[3]),
                last_active_at=datetime.fromisoformat(r[4]),
                current_spec_id=r[5],
            )
            for r in rows
        ]

    def update_session(self, session_id: str, current_spec_id: str) -> None:
        self.conn.execute(
            "UPDATE sessions SET current_spec_id = ?, last_active_at = ? WHERE id = ?",
            (current_spec_id, datetime.utcnow().isoformat(), session_id),
        )
        self.conn.commit()

    def touch_session(self, session_id: str) -> None:
        self.conn.execute(
            "UPDATE sessions SET last_active_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), session_id),
        )
        self.conn.commit()

    def save_spec(
        self, session_id: str, user_ask: str, spec: VegaLiteSpec,
        model_used: str, parent_spec_id: str | None,
    ) -> SavedSpec:
        now = datetime.utcnow().isoformat()
        spec_id = _new_id()
        spec_json = json.dumps(spec.spec)
        self.conn.execute(
            "INSERT INTO specs (id, session_id, parent_spec_id, user_ask, spec_json, model_used, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (spec_id, session_id, parent_spec_id, user_ask, spec_json, model_used, now),
        )
        self.conn.commit()
        return SavedSpec(
            id=spec_id, session_id=session_id, parent_spec_id=parent_spec_id,
            user_ask=user_ask, spec_json=spec_json, model_used=model_used,
            created_at=datetime.fromisoformat(now),
        )

    def get_spec(self, spec_id: str) -> SavedSpec:
        row = self.conn.execute(
            "SELECT id, session_id, parent_spec_id, user_ask, spec_json, model_used, created_at "
            "FROM specs WHERE id = ?", (spec_id,),
        ).fetchone()
        if row is None:
            raise KeyError(spec_id)
        return SavedSpec(
            id=row[0], session_id=row[1], parent_spec_id=row[2],
            user_ask=row[3], spec_json=row[4], model_used=row[5],
            created_at=datetime.fromisoformat(row[6]),
        )

    def list_specs(self, session_id: str) -> list[SavedSpec]:
        rows = self.conn.execute(
            "SELECT id, session_id, parent_spec_id, user_ask, spec_json, model_used, created_at "
            "FROM specs WHERE session_id = ? ORDER BY created_at ASC", (session_id,),
        ).fetchall()
        return [
            SavedSpec(
                id=r[0], session_id=r[1], parent_spec_id=r[2],
                user_ask=r[3], spec_json=r[4], model_used=r[5],
                created_at=datetime.fromisoformat(r[6]),
            )
            for r in rows
        ]
