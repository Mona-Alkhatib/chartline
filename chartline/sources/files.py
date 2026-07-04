from __future__ import annotations

from pathlib import Path

import pandas as pd

from chartline.models_types import SchemaSummary
from chartline.schema import summarize_dataframe


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


_LOADERS: dict[str, callable] = {
    ".csv": _read_csv,
    ".parquet": pd.read_parquet,
    ".xlsx": pd.read_excel,
    ".xls": pd.read_excel,
}


class FileSource:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    @property
    def ref(self) -> str:
        return str(self.path)

    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        loader = _LOADERS.get(self.path.suffix.lower())
        if loader is None:
            raise ValueError(f"Unsupported file extension: {self.path.suffix}")
        return loader(self.path)

    def summarize(self) -> SchemaSummary:
        df = self.load()
        return SchemaSummary(tables=[summarize_dataframe(df, name=self.path.stem)])
