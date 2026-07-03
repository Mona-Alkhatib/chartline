import json
import os
from pathlib import Path

import pytest
from anthropic import Anthropic
from dotenv import load_dotenv

from chartline.generator import ChartGenerator
from chartline.router import Router
from chartline.sources.warehouse import WarehouseSource
from chartline.validator import Validator

load_dotenv()

_PAIRS_PATH = Path(__file__).parent / "fixtures" / "warehouse" / "sql_pairs.json"
_DB_PATH = Path(__file__).parent / "fixtures" / "warehouse" / "wh.duckdb"
_PASS_THRESHOLD = 0.80


def _load_pairs() -> list[dict]:
    return json.loads(_PAIRS_PATH.read_text())


def _ensure_warehouse() -> None:
    if not _DB_PATH.exists():
        from evals.fixtures.warehouse import build
        build.build(_DB_PATH)


@pytest.fixture
def warehouse():
    _ensure_warehouse()
    return WarehouseSource(f"duckdb:///{_DB_PATH}", name="wh")


@pytest.mark.sql_eval
@pytest.mark.skipif(
    os.environ.get("CHARTLINE_RUN_SQL_EVALS") != "1",
    reason="Set CHARTLINE_RUN_SQL_EVALS=1 to run live SQL evals.",
)
def test_sql_correctness(warehouse):
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    generator = ChartGenerator(Router(), Validator(), client)
    schema = warehouse.summarize()
    pairs = _load_pairs()
    passes = 0
    failures: list[dict] = []
    for pair in pairs:
        try:
            sql = generator.text_to_sql(pair["question"], schema)
            df = warehouse.execute(sql)
        except Exception as e:
            failures.append({"id": pair["id"], "error": str(e)})
            continue
        cols_ok = df.shape[1] == pair["expected_columns"]
        rows_ok = pair["min_rows"] <= df.shape[0] <= pair["max_rows"]
        if cols_ok and rows_ok:
            passes += 1
        else:
            failures.append({
                "id": pair["id"], "sql": sql,
                "got_shape": df.shape,
                "wanted_columns": pair["expected_columns"],
                "wanted_rows": [pair["min_rows"], pair["max_rows"]],
            })
    rate = passes / len(pairs)
    print(f"\nLayer 3 pass rate: {rate:.2%} ({passes}/{len(pairs)})")
    for f in failures:
        print(f"  FAIL {f['id']}: {f}")
    assert rate >= _PASS_THRESHOLD, f"Layer 3 pass rate {rate:.2%} below {_PASS_THRESHOLD:.0%}"
