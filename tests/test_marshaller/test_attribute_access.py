import pytest
from pydent.marshaller.base import add_schema
from pydent.marshaller.fields import Callback, Relationship, Field
from pydent.marshaller.exceptions import ModelValidationError
from uuid import uuid4


class TestAttributeAccess:
    @pytest.mark.parametrize(
        "data",
        [
            {"id": 5},
            {"id": 5, "name": 4},
            {"id": 3, "model": "mymodel", "name": "myname"},
        ],
    )
    def test_load(self, base, data):
        @add_schema
        class MyModel(base):
            pass

        mymodel = MyModel._set_data(data)
        for k, v in data.items():
            assert hasattr(mymodel, k)

        for k, v in data.items():
            assert getattr(mymodel, k) == v

        with pytest.raises(AttributeError):
            getattr(mymodel, str(uuid4()))

        mymodel.id = 10
        assert mymodel.id == 10


class TestCallbackAccess:
    class Functions:
        def any(self, *args):
            pass

        def multiply(self, a, b, c, d=1):
            return (a * 2 + b ** 2 + 3 * c) * d

        def kwarg_name(self, model_name, name=5):
            pass

        def kwarg_name2(self, model_name, a, b, name=5):
            pass

        def multiple_kwargs(self, model_name, a, b, c=4, d=6):
            pass

    @pytest.mark.parametrize(
        "callback,args,kwargs,expected",
        [
            (
                Functions().multiply,
                (1, 2, 3),
                dict(d=1),
                Functions().multiply(1, 2, 3, d=1),
            ),
            (
                Functions().multiply,
                (3, 5, 7),
                dict(d=4),
                Functions().multiply(3, 5, 7, d=4),
            ),
        ],
    )
    def test_callback_results(self, base, callback, args, kwargs, expected):
        @add_schema
        class MyModel(base):
            fields = dict(
                field1=None, field2=None, field3=Callback("find", args, kwargs)
            )

            find = callback

        model = MyModel()

        assert model.field3 == expected

    def test_callback_results_using_lambda(self, base):
        @add_schema
        class MyModel(base):
            fields = dict(field1=Callback(lambda a, b: a * b, (3, 4), {}))

        model = MyModel()
        assert model.field1 == 12
        model.field1 = 3
        assert model.field1 == 3
        del model.field1
        assert model.field1 == 12

    def test_callback_results_using_lambda_passing_self(self, base):
        @add_schema
        class MyModel(base):
            fields = dict(field1=Callback(lambda a, b: a.x * b, (Callback.SELF, 4), {}))

        model = MyModel._set_data({"x": 5})
        assert model.field1 == 20
        model.x = 6
        assert model.field1 == 24

    def test_callback_results_using_lambda_args(self, base):
        @add_schema
        class MyModel(base):
            fields = dict(
                field1=Callback(lambda a, b: a * b, (lambda slf: slf.x * slf.x, 5), {})
            )

        model = MyModel._set_data({"x": 5})
        assert model.field1 == 5 ** 3
        model.x = 6
        assert model.x == 6
        assert model.field1 == 6 ** 2 * 5

    def test_callback_results_using_lambda_kwargs(self, base):
        @add_schema
        class MyModel(base):
            fields = dict(
                field1=Callback(
                    "func", (2,), {"instance": Callback.SELF, "b": lambda x: x.b}
                )
            )

            def func(self, a, instance=None, b=1):
                return a * b * instance.x

        model = MyModel._set_data({"x": 7, "b": 10})
        assert model.field1 == 2 * 7 * 10
        model.x = 8
        model.b = 11
        assert model.field1 == 2 * 8 * 11
        model.field1 = 5
        assert model.field1 == 5

    def test_wrong_nested_model_raises_error(self, base):
        with pytest.raises(ModelValidationError):

            @add_schema
            class MyModel(base):
                fields = dict(
                    field1=None, field2=None, field3=Relationship("", None, None, None)
                )

    def test_no_callback_raises_error(self, base):
        with pytest.raises(ModelValidationError):

            @add_schema
            class MyModel(base):
                fields = dict(
                    field1=None,
                    field2=None,
                    field3=Relationship(base, None, None, None),
                )

                def find(self, *args):
                    pass

    @pytest.mark.parametrize(
        "data,expected",
        [
            ({"id": 5}, {"id": 5, "model": "default"}),
            ({"model": "override", "id": 6}, {"id": 6, "model": "override"}),
        ],
    )
    def test_callback_override_while_loading(self, base, data, expected):
        @add_schema
        class MyModel(base):
            fields = dict(model=Callback("find"))

            def find(self):
                return "default"

        mymodel = MyModel(data)
        for k, v in expected.items():
            assert hasattr(mymodel, k)

        for k, v in expected.items():
            assert getattr(mymodel, k) == v

    @pytest.fixture(scope="function")
    def cached_model(self, base):
        @add_schema
        class MyModel(base):
            fields = dict(
                cached=Callback("find", cache=True),
                nocache=Callback("find", cache=False),
            )

            def __init__(self, x):
                self.x = x
                super().__init__()

            def find(self):
                return self.x

        return MyModel

    def test_callback_cache_vs_nocache(self, cached_model):

        mymodel = cached_model(5)
        assert mymodel.cached == 5
        assert mymodel.nocache == 5
        mymodel.x = 6
        assert mymodel.cached == 5
        assert mymodel.nocache == 6
        mymodel.x = 7
        assert mymodel.nocache == 7

    def test_callback_del_cache_resets(self, cached_model):
        mymodel = cached_model(5)
        assert mymodel.cached == 5
        assert mymodel.nocache == 5

        # change underlying data
        mymodel.x = 7
        assert mymodel.nocache == 7
        assert mymodel.cached == 5, "cache should not change with underlying data"

        del mymodel.cached
        assert mymodel.nocache == 7
        assert mymodel.cached == 7, "cache should call underlying data"

        # change underlying data
        mymodel.x = 9
        assert mymodel.nocache == 9
        assert mymodel.cached == 7, "cache should not change with underlying data"

        # change underlying data, set cached
        mymodel.x = 9
        mymodel.cached = 6
        assert mymodel.cached == 6
        assert mymodel.nocache == 9
        del mymodel.cached
        assert mymodel.cached == 9
        assert mymodel.nocache == 9

    def test_initialize_callback(self, base):
        @add_schema
        class MyModel(base):
            fields = dict(field=Callback("find"))

            def find(self):
                return 5

        m = MyModel({"field": 6})
        assert m.dump(include={"field"}) == {"field": 6}
