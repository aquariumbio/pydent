import pytest

from pydent.marshaller.base import SchemaModel


@pytest.fixture(scope="function")
def base():
    class TestBase(SchemaModel):
        pass
    return TestBase
