import pytest

from chartline.router import MODEL_OPUS, MODEL_SONNET, Router


def test_model_for_initial_is_opus():
    assert Router().model_for("initial") == MODEL_OPUS


def test_model_for_refine_is_sonnet():
    assert Router().model_for("refine") == MODEL_SONNET


def test_model_for_sql_is_opus():
    assert Router().model_for("sql") == MODEL_OPUS


def test_model_for_unknown_raises():
    with pytest.raises(ValueError):
        Router().model_for("whatever")  # type: ignore[arg-type]


def test_system_prompt_initial_mentions_vega_lite():
    p = Router().system_prompt("initial")
    assert "Vega-Lite" in p


def test_system_prompt_refine_mentions_surgical():
    p = Router().system_prompt("refine")
    assert "surgical" in p.lower() or "minimal" in p.lower()


def test_system_prompt_sql_mentions_sql():
    p = Router().system_prompt("sql")
    assert "SQL" in p


def test_system_blocks_have_cache_control():
    blocks = Router().system_blocks("initial")
    assert isinstance(blocks, list)
    assert any(b.get("cache_control") == {"type": "ephemeral"} for b in blocks)
