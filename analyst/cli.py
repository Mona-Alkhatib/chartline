from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import typer

import analyst
from analyst.store import SpecStore

app = typer.Typer(add_completion=False, help="Chartline — natural-language chart generation.")


def _store_path() -> Path:
    raw = os.environ.get("CHARTLINE_STORE_PATH", "~/.chartline/store.db")
    return Path(raw).expanduser()


@app.command()
def version() -> None:
    """Print the Chartline version."""
    typer.echo(f"chartline {analyst.__version__}")


@app.command("list-sessions")
def list_sessions() -> None:
    """List saved sessions, most recent first."""
    with SpecStore(_store_path()) as store:
        for s in store.list_sessions():
            name = s.name or "(unnamed)"
            typer.echo(f"{s.id}  {name}  data={s.data_source_ref}  active={s.last_active_at}")


@app.command()
def export(session_id: str, out: Path = typer.Option(..., "--out")) -> None:
    """Export a session (metadata + all specs) to a JSON file."""
    with SpecStore(_store_path()) as store:
        sess = store.get_session(session_id)
        specs = store.list_specs(session_id)
        payload = {
            "session": sess.model_dump(mode="json"),
            "specs": [s.model_dump(mode="json") for s in specs],
        }
    out.write_text(json.dumps(payload, indent=2, default=str))
    typer.echo(f"Wrote {len(specs)} specs to {out}")


@app.command()
def serve(port: int = 8501) -> None:
    """Launch the Streamlit web app."""
    entry = Path(__file__).parent.parent / "ui" / "streamlit_app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(entry), "--server.port", str(port)],
        check=False,
    )


if __name__ == "__main__":
    app()
