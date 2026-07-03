from __future__ import annotations

from typing import Literal

Task = Literal["initial", "refine", "sql"]

MODEL_OPUS = "claude-opus-4-8"
MODEL_SONNET = "claude-sonnet-4-6"

_INITIAL_PROMPT = """You are a data visualization assistant. Given a schema summary
and a user's request, produce a Vega-Lite v5 JSON specification that answers it.

Rules:
- Return ONLY the JSON spec, no prose.
- Use only fields from the schema.
- Prefer simple, standard chart types.
- Encoding types must match the schema (quantitative / ordinal / nominal / temporal).
"""

_REFINE_PROMPT = """You are a data visualization assistant refining an existing Vega-Lite
spec. Given the previous spec and a user's refinement request, produce a new Vega-Lite v5
JSON spec.

Rules:
- Return ONLY the JSON spec, no prose.
- Make the SMALLEST, most surgical change that fulfills the request.
- Do NOT change anything the user didn't ask about.
- Preserve existing encodings, titles, and transforms unless directly overridden.
"""

_SQL_PROMPT = """You are a SQL assistant. Given a warehouse schema and a user's question,
produce a single SELECT statement that answers it.

Rules:
- Return ONLY the SQL, no prose, no code fences.
- Use standard ANSI SQL that DuckDB, Postgres, Snowflake, and BigQuery all accept.
- Prefer explicit column lists over SELECT *.
- Alias aggregated columns with human-friendly names.
"""


class Router:
    def model_for(self, task: Task) -> str:
        match task:
            case "initial" | "sql":
                return MODEL_OPUS
            case "refine":
                return MODEL_SONNET
            case _:
                raise ValueError(f"Unknown task: {task}")

    def system_prompt(self, task: Task) -> str:
        match task:
            case "initial":
                return _INITIAL_PROMPT
            case "refine":
                return _REFINE_PROMPT
            case "sql":
                return _SQL_PROMPT
            case _:
                raise ValueError(f"Unknown task: {task}")

    def system_blocks(self, task: Task) -> list[dict]:
        return [{
            "type": "text",
            "text": self.system_prompt(task),
            "cache_control": {"type": "ephemeral"},
        }]
