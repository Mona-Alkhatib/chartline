# Chartline

Natural-language chart generation and refinement for ad-hoc analysis.

Chartline turns questions like "show me revenue by region" into charts, and lets you refine them iteratively ("log-scale the y-axis," "split by product," "make it a bar chart") with the LLM producing surgical edits to a canonical Vega-Lite spec each time.

## Features

- **Iterative refinement as the primary interaction.** Every ask edits the current chart in place, versioned and rewindable.
- **One library, three surfaces.** Streamlit web app, Jupyter widget, and CLI, all backed by the same Python library.
- **File uploads and warehouse connections.** CSV, Parquet, and Excel out of the box; DuckDB, Postgres, Snowflake, and BigQuery via SQLAlchemy.
- **Reproducible exports.** Every chart can be copied out as Altair or Plotly Python code.
- **Smart model routing.** Opus for first-generation and text-to-SQL, Sonnet for refinements, with prompt caching to keep costs low.

## Preview without an API key

If you just want to see what Chartline renders (no LLM calls, no cost):

```bash
uv sync
uv run streamlit run chartline/ui/streamlit_app.py
```

Open http://localhost:8501, click **"Try the sample sales.csv"**, then pick from the **Demo gallery** dropdown to flip between bar, stacked bar, line, scatter, and heatmap views of the sample dataset. The right-hand panel also shows the corresponding Vega-Lite JSON, Altair, and Plotly code for whichever chart is on screen.

The chat panel still needs `ANTHROPIC_API_KEY` for new asks and refinements, but the demo gallery and code export work offline.

## Quick start (with LLM)

```bash
uv sync
export ANTHROPIC_API_KEY=sk-ant-...
uv run chartline serve
```

Upload a CSV in the web UI and start asking for charts.

### In a notebook

```python
from chartline.notebook.widget import NotebookSession

s = NotebookSession.from_file("sales.csv")
s.ask("show me revenue by month")
s.refine("split by region")
s.refine("log-scale the y-axis")
```

## Configuration

Chartline reads model IDs from environment variables. The defaults track current Anthropic model names; override them if you need to pin a specific snapshot or switch to a different tier:

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

Everything lives under a single `chartline/` package: the core library at the top level (`chartline.session`, `chartline.generator`, `chartline.store`, and friends), the Streamlit app at `chartline.ui.streamlit_app`, and the Jupyter widget at `chartline.notebook.widget`. The eval harness lives at `evals/`, and unit tests at `tests/`. Vega-Lite is the canonical chart format, and the exporter maps back to Altair and Plotly.
