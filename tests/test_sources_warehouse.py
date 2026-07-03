import duckdb
import pandas
import pytest

from analyst.sources.warehouse import WarehouseSource


@pytest.fixture
def warehouse(tmp_path):
    db = tmp_path / "wh.duckdb"
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE users AS SELECT * FROM (VALUES (1,'A'),(2,'B'),(3,'A')) AS t(id, region)")
    con.execute("CREATE TABLE orders AS SELECT * FROM (VALUES (1,10.0),(2,20.0),(3,30.0)) AS t(user_id, amount)")
    con.close()
    return WarehouseSource(f"duckdb:///{db}", name="wh")


def test_warehouse_execute(warehouse):
    df = warehouse.execute("SELECT * FROM users ORDER BY id")
    assert len(df) == 3
    assert list(df.columns) == ["id", "region"]


def test_warehouse_summarize_lists_tables(warehouse):
    schema = warehouse.summarize()
    table_names = {t.name for t in schema.tables}
    assert table_names == {"users", "orders"}


def test_warehouse_summarize_columns_have_dtypes(warehouse):
    schema = warehouse.summarize()
    users = next(t for t in schema.tables if t.name == "users")
    by_name = {c.name: c for c in users.columns}
    assert by_name["id"].dtype == "quantitative"
    assert by_name["region"].dtype == "nominal"


def test_warehouse_ref_is_name(warehouse):
    assert warehouse.ref == "wh"


def test_warehouse_execute_invalid_sql(warehouse):
    with pytest.raises(pandas.errors.DatabaseError):
        warehouse.execute("SELECT * FROM nowhere")
