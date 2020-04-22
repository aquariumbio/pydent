import time
from uuid import uuid4

import pytest

from pydent.marshaller.base import add_schema
from pydent.marshaller.base import SchemaModel
from pydent.marshaller.fields import Callback
from pydent.marshaller.fields import Field
from pydent.marshaller.fields import Relationship
from pydent.marshaller.registry import ModelRegistry


@pytest.mark.benchmark
class TestSpeed:
    def EmptyModel(self, base):
        @add_schema
        class EmptyModel(SchemaModel):
            pass

        return EmptyModel

    def WithFields(self, base):
        @add_schema
        class WithFields(SchemaModel):
            fields = dict(field=Field(), field2=Field())

        return WithFields

    def CachedCallback(self, base):
        @add_schema
        class CachedCallback(SchemaModel):
            fields = dict(field=Field(), field2=Callback("find"))

            def find(self):
                time.sleep(0.0001)
                return 5 ** 3

        return CachedCallback

    def NoCacheCallback(self, base):
        @add_schema
        class NoCacheCallback(SchemaModel):
            fields = dict(field=Field(), field2=Callback("find", cache=False))

            def find(self):
                time.sleep(0.0001)
                return 5 ** 3

        return NoCacheCallback

    def ControlModel(self, base):
        class ControlModel:
            @classmethod
            def _set_data(cls, data):
                instance = cls.__new__(cls)
                instance.__dict__.update(data)
                return instance

            def dump(self):
                return self.__dict__

        return ControlModel


    @staticmethod
    def random_data():
        return {
            str(uuid4()): str(uuid4()),
            str(uuid4()): str(uuid4()),
            str(uuid4()): str(uuid4()),
            "field": str(uuid4()),
            "mydata": str(uuid4()),
        }

    def _set_data(self, model, data):
        model._set_data(data)
        assert True

    models = [
        EmptyModel,
        WithFields,
        CachedCallback,
        NoCacheCallback,
        ControlModel
    ]

    @pytest.mark.parametrize("model", models)
    def test_set_data(self, benchmark, base, model):
        data = self.random_data()
        model = model(self, base)
        benchmark(self._set_data, model, data)

    def dump(self, instance):
        instance.dump()
        assert True

    @pytest.mark.parametrize("model", models)
    def test_dump(self, benchmark, base, model):
        data = self.random_data()
        model = model(self, base)
        instance = model._set_data(data)
        benchmark(self.dump, instance)

    def setattr(self, model, k, v):
        setattr(model, k, v)
        assert True

    @pytest.mark.parametrize("model", models)
    def test_set_attribute(self, benchmark, base, model):
        data = self.random_data()
        model = model(self, base)
        instance = model._set_data(data)
        benchmark(self.setattr, instance, "field", 5)

    def access(self, instance, num, *args):
        for i in range(num):
            for arg in args:
                getattr(instance, arg)

    @pytest.mark.parametrize("num", [1, 10, 100, 1000])
    @pytest.mark.parametrize("model", models)
    def test_field_access(self, benchmark, base, model, num):
        instance = model(self, base)._set_data(self.random_data())
        benchmark(self.access, instance, num, "field")

    @pytest.mark.parametrize("num", [1, 10, 100, 1000])
    @pytest.mark.parametrize("model", models)
    def test_data_access(self, benchmark, base, model, num):
        instance = model(self, base)._set_data(self.random_data())
        benchmark(self.access, instance, num, "mydata")

    @pytest.mark.parametrize("num", [1, 10, 100, 1000])
    @pytest.mark.parametrize("model", [CachedCallback, NoCacheCallback])
    def test_access_to_missing(self, benchmark, base, model, num):
        instance = model(self, base)._set_data(self.random_data())
        benchmark(self.access, instance, num, "field", "field2")

    def complex(self, model, data):
        for i in range(5):
            instance = model._set_data(data)
            instance.id = instance.field
            for i in range(1000):
                instance.field
            for i in range(50):
                instance.field = i
                instance.field = instance.field ** 2
            instance.__dict__
            instance.dump()

    @pytest.mark.parametrize("model", models)
    def test_complex(self, benchmark, base, model):
        data = self.random_data()
        model = model(self, base)
        benchmark(self.complex, model, data)

    def test_profile_complex(self, base):
        model = self.CachedCallback(base)
        for i in range(100):
            self.complex(model, self.random_data())


@pytest.mark.benchmark
class TestBenchmarkRelationships:
    @pytest.fixture(scope="function")
    def Company(self, base):
        @add_schema
        class Company(base):
            pass

        return Company

    @pytest.fixture(scope="function")
    def Publisher(self, base):
        @add_schema
        class Publisher(base):
            fields = dict(
                company=Relationship(
                    "Company", "instantiate_model", 6, {"name": "MyCompany"}
                )
            )

            def instantiate_model(self, model_name, model_id, name="Default"):
                return ModelRegistry.get_model(model_name)._set_data(
                    {"id": model_id, "name": name}
                )

        return Publisher

    @pytest.fixture(scope="function")
    def Author(self, base):
        @add_schema
        class Author(base):
            fields = dict(
                publisher=Relationship(
                    "Publisher", "instantiate_model", 4, {"name": "MyPublisher"}
                )
            )

            def instantiate_model(self, model_name, model_id, name="Default"):
                return ModelRegistry.get_model(model_name)._set_data(
                    {"id": model_id, "name": name}
                )

        return Author

    models = [Company, Publisher, Author]

    @pytest.fixture(scope="function")
    def author(self, base, Author, Publisher, Company):
        Author(self, base)
        Publisher(self, base)
        Company(self, base)
        author = Author

    @pytest.mark.parametrize(
        "model,include,expected",
        [
            ("Company", None, {}),
            ("Publisher", None, {}),
            ("Author", None, {}),
            pytest.param(
                "Publisher",
                "company",
                {"company": {"id": 6, "name": "MyCompany"}},
                id="1 layer nested",
            ),
            pytest.param(
                "Author",
                "publisher",
                {"publisher": {"id": 4, "name": "MyPublisher"}},
                id="1 layer nested",
            ),
            pytest.param(
                "Author",
                {"publisher": "company"},
                {
                    "publisher": {
                        "id": 4,
                        "name": "MyPublisher",
                        "company": {"id": 6, "name": "MyCompany"},
                    }
                },
                id="2 layer nested",
            ),
        ],
    )
    def test_nested_dump_benchmark(
        self, base, Author, Publisher, Company, benchmark, model, include, expected
    ):
        instance = ModelRegistry.get_model(model)()
        benchmark(instance.dump, include=include)
        assert instance.dump(include=include) == expected
