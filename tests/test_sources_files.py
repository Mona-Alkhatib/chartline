from pathlib import Path

import pandas as pd
import pytest

from analyst.sources.files import FileSource


def _write_csv(tmp_path: Path) -> Path:
    p = tmp_path / "sales.csv"
    pd.DataFrame({"revenue": [1, 2, 3], "region": ["A", "B", "A"]}).to_csv(p, index=False)
    return p


def test_file_source_loads_csv(tmp_path):
    p = _write_csv(tmp_path)
    src = FileSource(p)
    df = src.load()
    assert len(df) == 3
    assert list(df.columns) == ["revenue", "region"]


def test_file_source_summarize(tmp_path):
    p = _write_csv(tmp_path)
    src = FileSource(p)
    schema = src.summarize()
    assert len(schema.tables) == 1
    assert schema.tables[0].name == "sales"
    assert {c.name for c in schema.tables[0].columns} == {"revenue", "region"}


def test_file_source_ref_is_filename(tmp_path):
    p = _write_csv(tmp_path)
    assert FileSource(p).ref.endswith("sales.csv")


def test_file_source_parquet(tmp_path):
    p = tmp_path / "data.parquet"
    pd.DataFrame({"x": [1, 2]}).to_parquet(p)
    src = FileSource(p)
    assert len(src.load()) == 2


def test_file_source_unsupported_extension(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("nothing")
    with pytest.raises(ValueError, match="Unsupported"):
        FileSource(p).load()


def test_file_source_missing_path(tmp_path):
    p = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        FileSource(p).load()
