# Chartline

Natural-language chart generation and refinement for ad-hoc analysis.

Chartline turns questions like "show me revenue by region" into charts, and lets you refine them iteratively — "log-scale the y-axis," "split by product," "make it a bar chart" — with the LLM producing surgical edits to a canonical Vega-Lite spec each time.

## Features

- **Iterative refinement is the primary interaction** — every ask edits the current chart in place, versioned and rewindable.
- **One library, three surfaces** — Streamlit web app, Jupyter widget, and CLI, all backed by the same Python library.
- **File uploads and warehouse connections** — CSV / Parquet / Excel out of the box; DuckDB, Postgres, Snowflake, BigQuery via SQLAlchemy.
- **Reproducible exports** — every chart can be copied out as Altair or Plotly Python code.
- **Smart model routing** — Opus for first-generation and text-to-SQL, Sonnet for refinements, with prompt caching to keep costs low.

## Quick start

```bash
uv sync
export ANTHROPIC_API_KEY=sk-ant-...
uv run chartline serve
```

Then upload a CSV in the web UI and start asking for charts.

### In a notebook

```python
from notebook.widget import NotebookSession

s = NotebookSession.from_file("sales.csv")
s.ask("show me revenue by month")
s.refine("split by region")
s.refine("log-scale the y-axis")
```

## Configuration

Chartline reads model IDs from environment variables. The defaults track
current Anthropic model names; override them if you need to pin a specific
snapshot or switch to a different tier:

```bash
export CHARTLINE_MODEL_OPUS=claude-opus-4-8       # initial chart + text-to-SQL
export CHARTLINE_MODEL_SONNET=claude-sonnet-4-6   # refinements
```

## Development

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

To run the LLM-backed evals:

```bash
CHARTLINE_RUN_LLM_EVALS=1 uv run pytest evals/test_refinement.py -v -s
CHARTLINE_RUN_SQL_EVALS=1 CHARTLINE_RUN_LLM_EVALS=1 uv run pytest evals/test_sql.py -v -s
```

## Architecture

See `analyst/` for the library, `ui/` for the Streamlit app, `notebook/` for the widget, and `evals/` for the eval harness. Vega-Lite is the canonical chart format — the exporter maps back to Altair and Plotly.
