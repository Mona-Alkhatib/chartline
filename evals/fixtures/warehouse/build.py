"""Build the fixture DuckDB warehouse used by Layer 3 evals."""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

DEFAULT_DB = Path(__file__).parent / "wh.duckdb"


def build(db_path: Path = DEFAULT_DB) -> None:
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    con.execute("""
        CREATE TABLE users AS SELECT * FROM (VALUES
            (1, 'alice', 'NA'),
            (2, 'bob', 'EU'),
            (3, 'carol', 'NA'),
            (4, 'dan', 'APAC'),
            (5, 'eve', 'EU')
        ) AS t(id, name, region);
    """)
    con.execute("""
        CREATE TABLE products AS SELECT * FROM (VALUES
            (10, 'Widget', 'Hardware'),
            (11, 'Gadget', 'Hardware'),
            (12, 'Doodad', 'Software')
        ) AS t(id, name, category);
    """)
    con.execute("""
        CREATE TABLE orders AS SELECT * FROM (VALUES
            (100, 1, 10, 100.0, DATE '2026-01-05'),
            (101, 2, 11, 200.0, DATE '2026-01-06'),
            (102, 1, 12, 50.0, DATE '2026-01-07'),
            (103, 3, 10, 150.0, DATE '2026-02-01'),
            (104, 4, 11, 300.0, DATE '2026-02-15'),
            (105, 5, 12, 75.0, DATE '2026-03-01'),
            (106, 2, 10, 100.0, DATE '2026-03-05'),
            (107, 3, 11, 250.0, DATE '2026-03-20')
        ) AS t(id, user_id, product_id, amount, order_date);
    """)
    con.close()
    print(f"Wrote fixture warehouse to {db_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=DEFAULT_DB)
    args = p.parse_args()
    build(args.out)
