import pandas as pd

from chartline.schema import infer_dtype, summarize_dataframe


def test_infer_dtype_numeric():
    s = pd.Series([1.0, 2.0, 3.0])
    assert infer_dtype(s) == "quantitative"


def test_infer_dtype_datetime():
    s = pd.to_datetime(pd.Series(["2026-01-01", "2026-02-01"]))
    assert infer_dtype(s) == "temporal"


def test_infer_dtype_categorical_low_cardinality():
    s = pd.Series(["A", "B", "A", "C", "A"])
    assert infer_dtype(s) == "nominal"


def test_infer_dtype_ordinal_when_ordered_category():
    s = pd.Categorical(["low", "medium", "high"], categories=["low", "medium", "high"], ordered=True)
    assert infer_dtype(pd.Series(s)) == "ordinal"


def test_summarize_dataframe_basic():
    df = pd.DataFrame({
        "revenue": [100.0, 200.0, None, 300.0],
        "region": ["NA", "EU", "APAC", "NA"],
        "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]),
    })
    t = summarize_dataframe(df, name="sales")
    assert t.name == "sales"
    assert t.row_count == 4
    by_name = {c.name: c for c in t.columns}
    assert by_name["revenue"].dtype == "quantitative"
    assert by_name["revenue"].null_rate == 0.25
    assert by_name["region"].dtype == "nominal"
    assert by_name["region"].distinct_count == 3
    assert set(by_name["region"].sample_values) <= {"NA", "EU", "APAC"}
    assert by_name["date"].dtype == "temporal"


def test_summarize_dataframe_sample_values_are_strings():
    df = pd.DataFrame({"x": [1, 2, 3]})
    t = summarize_dataframe(df, name="t")
    col = t.columns[0]
    assert all(isinstance(v, str) for v in col.sample_values)
