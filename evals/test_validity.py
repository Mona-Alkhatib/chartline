import pytest

_BAD_SPECS = [
    {"encoding": {"x": {"field": "revenue", "type": "quantitative"}}},  # missing mark
    {"mark": "sankey", "encoding": {"x": {"field": "revenue", "type": "quantitative"}}},  # bad mark
    {"mark": "bar", "encoding": {"x": {"field": "not_a_field", "type": "nominal"}}},  # bad field
    "just a string",  # wrong type
    {"mark": "bar", "transform": [{"field": "no_such_col"}]},  # bad transform field
]

_GOOD_SPECS = [
    {"mark": "bar", "encoding": {"x": {"field": "region", "type": "nominal"},
                                  "y": {"field": "revenue", "type": "quantitative"}}},
    {"mark": "line", "encoding": {"x": {"field": "date", "type": "temporal"},
                                    "y": {"field": "revenue", "type": "quantitative"}}},
    {"mark": "point", "encoding": {"x": {"field": "units", "type": "quantitative"},
                                     "y": {"field": "revenue", "type": "quantitative"}}},
]


@pytest.mark.parametrize("spec", _BAD_SPECS)
def test_validator_rejects_bad(spec, validator, sales_schema):
    result = validator.validate(spec, sales_schema)
    assert not result.valid, f"expected rejection: {spec}"


@pytest.mark.parametrize("spec", _GOOD_SPECS)
def test_validator_accepts_good(spec, validator, sales_schema):
    result = validator.validate(spec, sales_schema)
    assert result.valid, f"expected accept: got error={result.error}"


def test_validity_rate_summary(validator, sales_schema):
    total = len(_BAD_SPECS) + len(_GOOD_SPECS)
    correctly_classified = sum(
        1 for s in _BAD_SPECS if not validator.validate(s, sales_schema).valid
    ) + sum(
        1 for s in _GOOD_SPECS if validator.validate(s, sales_schema).valid
    )
    rate = correctly_classified / total
    assert rate == 1.0, f"Layer 1 classification rate: {rate:.2f}"
