from pathlib import Path

import pytest

from analyst.sources.files import FileSource
from analyst.validator import Validator

_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sales_source():
    return FileSource(_FIXTURES / "datasets" / "sales.csv")


@pytest.fixture
def sales_schema(sales_source):
    return sales_source.summarize()


@pytest.fixture
def validator():
    return Validator()
