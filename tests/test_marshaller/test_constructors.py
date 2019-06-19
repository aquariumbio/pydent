import pytest

from pydent.marshaller.base import SchemaModel, ModelRegistry, add_schema
from pydent.marshaller.exceptions import (
    SchemaException,
    ModelValidationError,
    SchemaRegistryError,
)
from pydent.marshaller.fields import Callback, Relationship
from pydent.marshaller.schema import SchemaRegistry


class TestModelConstructors:
    def test_model_base_constructor(self):
        @add_schema
        class TestBase(SchemaModel):
            pass

        assert True, "should pass with no errors"

    def test_model_base_constructor(self):
        with pytest.raises(SchemaException):

            @add_schema
            class TestBase(object):
                pass

    def test_model_registry(self):
        class TestBase(SchemaModel):
            pass

        assert "SchemaModel" not in ModelRegistry.models, (
            "There should be no models for the " "first base class of SchemaModel"
        )

        num = len(ModelRegistry.models)

        class MyFirstModel(TestBase):
            pass

        class MySecondModel(TestBase):
            pass

        assert (
            len(ModelRegistry.models) == num + 2
        ), "There should be 2 models registered"

        assert ModelRegistry.get_model("MyFirstModel") is MyFirstModel
        assert ModelRegistry.get_model("MySecondModel") is MySecondModel


class TestSchemaConstructors:
    @pytest.fixture(scope="function")
    def MyFirstModel(self, base):
        @add_schema
        class MyFirstModel(base):
            pass

        return MyFirstModel

    @pytest.fixture(scope="function")
    def MySecondModel(self, base):
        @add_schema
        class MySecondModel(base):
            pass

        return MySecondModel

    @pytest.fixture(scope="function")
    def MyControlModel(self, base):
        class MyControlModel(base):
            pass

        return MyControlModel

    def test_has_model_schema(self, MyFirstModel, MySecondModel, MyControlModel):
        assert not MyControlModel.model_schema
        assert MyFirstModel.model_schema
        assert MySecondModel.model_schema

    def test_has_model_schema_with_correct_identity(
        self, MyFirstModel, MySecondModel, MyControlModel
    ):
        assert not MyControlModel.model_schema
        assert MyFirstModel.model_schema.__name__ == "MyFirstModelSchema"
        assert MySecondModel.model_schema.__name__ == "MySecondModelSchema"

    def test_get_from_schema_registry(
        self, MyFirstModel, MySecondModel, MyControlModel
    ):
        assert SchemaRegistry.get_model_schema("MyFirstModel")
        assert SchemaRegistry.get_model_schema("MySecondModel")
        with pytest.raises(SchemaRegistryError):
            assert not SchemaRegistry.get_model_schema("MyControlModel")

    def test_different_schemas(self, MyFirstModel, MySecondModel, MyControlModel):
        assert (
            SchemaRegistry.get_model_schema("MyFirstModel") is MyFirstModel.model_schema
        )
        assert (
            SchemaRegistry.get_model_schema("MySecondModel")
            is MySecondModel.model_schema
        )

        assert MyFirstModel.model_schema is not MySecondModel.model_schema


class TestRelationshipConstructors:
    @pytest.fixture(scope="function")
    def base(self):
        SchemaRegistry.schemas = {}
        ModelRegistry.models = {}

        class TestBase(SchemaModel):
            def _set_data(self):
                pass

            def dump(self):
                pass

        yield TestBase
        SchemaRegistry.schemas = {}
        ModelRegistry.models = {}

    def test_standard_relationship_constructor(self, base):
        class MyOtherModel(base):
            pass

        @add_schema
        class MyModel(base):
            fields = dict(
                field1=None, field2=None, field3=Relationship(MyOtherModel, "find")
            )

            def find(self, *args):
                pass

        assert MyModel()


def make_function(num_args, num_kwargs):
    if num_args is None:
        args = ["*args"]
    else:
        args = [chr(i + ord("a")) for i in range(num_args)]
    if num_kwargs is None:
        kwargs = ["**kwargs"]
    else:
        kwargs = [
            "{}=None".format(chr(i + len(args) + ord("a"))) for i in range(num_kwargs)
        ]

    exec(
        """
def foo({args}):
    print(locals())
""".format(
            args=", ".join(args + kwargs).strip()
        )
    )
    print(", ".join(args + kwargs))
    return (eval("foo"), ", ".join(args + kwargs))


def make_function_param(
    num_args,
    num_kwargs,
    num_callback_args,
    num_callback_kwargs,
    result,
    suffix="",
    valid_kwargs=True,
):
    args_to_send = tuple(range(num_callback_args))
    kwarg_offset = ord("a")
    if num_args is not None:
        kwarg_offset += num_args
    if not valid_kwargs:
        kwarg_offset += num_kwargs
    kwargs_to_send = {chr(kwarg_offset + i): None for i in range(num_callback_kwargs)}

    func, signature = make_function(num_args, num_kwargs)
    sent = "{} {}".format(args_to_send, kwargs_to_send)
    return pytest.param(
        func,
        args_to_send,
        kwargs_to_send,
        result,
        id="callback({}) <- {}  {}".format(signature, sent, suffix),
    )


class TestCallback:
    @pytest.mark.parametrize(
        "callback, args, kwargs, expected",
        [
            make_function_param(0, 0, 0, 0, False, suffix="too many args"),
            make_function_param(1, 0, 1, 0, False, suffix="too many args"),
            make_function_param(2, 0, 2, 0, False, suffix="too many args"),
            make_function_param(2, 0, 0, 0, False, suffix="not enough args"),
            make_function_param(3, 0, 1, 0, False, suffix="not enough args"),
            make_function_param(1, 0, 0, 0, True),
            make_function_param(2, 0, 1, 0, True),
            make_function_param(3, 0, 2, 0, True),
            make_function_param(1, 1, 0, 1, True, suffix="with kwargs"),
            make_function_param(2, 2, 1, 2, True, suffix="with kwargs"),
            make_function_param(3, 3, 2, 3, True, suffix="with kwargs"),
            make_function_param(
                1, 1, 0, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(
                2, 1, 1, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(
                3, 1, 2, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(1, 1, 0, 2, False, suffix="too many kwargs"),
            make_function_param(2, 2, 1, 3, False, suffix="too many kwargs"),
            make_function_param(3, 3, 2, 4, False, suffix="too many kwargs"),
            make_function_param(2, 2, 1, 1, True),
            make_function_param(3, 3, 2, 2, True),
            make_function_param(None, 0, 0, 0, True),
            make_function_param(None, 0, 1, 0, True),
            make_function_param(None, 0, 2, 0, True),
            make_function_param(None, 0, 3, 0, True),
            make_function_param(1, None, 0, 0, True),
            make_function_param(2, None, 1, 1, True),
            make_function_param(3, None, 2, 2, True),
        ],
    )
    def test_instance_callback(self, base, callback, args, kwargs, expected):
        def make_model():
            @add_schema
            class MyModel(base):
                fields = dict(
                    field1=None, field2=None, field3=Callback("find", args, kwargs)
                )

                find = callback

            return MyModel

        if expected:
            make_model()
        else:
            with pytest.raises(ModelValidationError):
                make_model()

    @pytest.mark.parametrize(
        "callback, args, kwargs, expected",
        [
            make_function_param(0, 0, 1, 0, False, suffix="too many args"),
            make_function_param(1, 0, 2, 0, False, suffix="too many args"),
            make_function_param(2, 0, 3, 0, False, suffix="too many args"),
            make_function_param(1, 0, 0, 0, False, suffix="not enough args"),
            make_function_param(2, 0, 1, 0, False, suffix="not enough args"),
            make_function_param(0, 0, 0, 0, True),
            make_function_param(1, 0, 1, 0, True),
            make_function_param(2, 0, 2, 0, True),
            make_function_param(0, 1, 0, 1, True, suffix="with kwargs"),
            make_function_param(1, 2, 1, 2, True, suffix="with kwargs"),
            make_function_param(2, 3, 2, 3, True, suffix="with kwargs"),
            make_function_param(
                0, 1, 0, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(
                1, 1, 1, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(
                2, 1, 2, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(0, 1, 0, 2, False, suffix="too many kwargs"),
            make_function_param(1, 2, 1, 3, False, suffix="too many kwargs"),
            make_function_param(2, 3, 2, 4, False, suffix="too many kwargs"),
            make_function_param(1, 2, 1, 1, True),
            make_function_param(2, 3, 2, 2, True),
            make_function_param(None, 0, 0, 0, True),
            make_function_param(None, 0, 1, 0, True),
            make_function_param(None, 0, 2, 0, True),
            make_function_param(None, 0, 3, 0, True),
            make_function_param(0, None, 0, 0, True),
            make_function_param(1, None, 1, 1, True),
            make_function_param(2, None, 2, 2, True),
        ],
    )
    def test_lambda_callback(self, base, callback, args, kwargs, expected):
        def make_model():
            @add_schema
            class MyModel(base):
                fields = dict(
                    field1=None, field2=None, field3=Callback(callback, args, kwargs)
                )

                find = callback

            return MyModel

        if expected:
            make_model()
        else:
            with pytest.raises(ModelValidationError):
                make_model()

    @pytest.mark.parametrize(
        "callback, args, kwargs, expected",
        [
            make_function_param(1, 0, 0, 0, False, suffix="too many args"),
            make_function_param(2, 0, 1, 0, False, suffix="too many args"),
            make_function_param(3, 0, 2, 0, False, suffix="too many args"),
            make_function_param(3, 0, 0, 0, False, suffix="not enough args"),
            make_function_param(4, 0, 1, 0, False, suffix="not enough args"),
            make_function_param(2, 0, 0, 0, True),
            make_function_param(3, 0, 1, 0, True),
            make_function_param(4, 0, 2, 0, True),
            make_function_param(2, 1, 0, 1, True, suffix="with kwargs"),
            make_function_param(3, 2, 1, 2, True, suffix="with kwargs"),
            make_function_param(4, 3, 2, 3, True, suffix="with kwargs"),
            make_function_param(
                2, 1, 0, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(
                3, 1, 1, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(
                4, 1, 2, 1, False, valid_kwargs=False, suffix="invalid kwargs"
            ),
            make_function_param(2, 1, 0, 2, False, suffix="too many kwargs"),
            make_function_param(3, 2, 1, 3, False, suffix="too many kwargs"),
            make_function_param(4, 3, 2, 4, False, suffix="too many kwargs"),
            make_function_param(3, 2, 1, 1, True),
            make_function_param(4, 3, 2, 2, True),
            make_function_param(None, 0, 0, 0, True),
            make_function_param(None, 0, 1, 0, True),
            make_function_param(None, 0, 2, 0, True),
            make_function_param(None, 0, 3, 0, True),
            make_function_param(2, None, 0, 0, True),
            make_function_param(3, None, 1, 1, True),
            make_function_param(4, None, 2, 2, True),
        ],
    )
    def test_instance_relationship(self, base, callback, args, kwargs, expected):
        def make_model():
            @add_schema
            class MyModel(base):
                fields = dict(
                    field1=None,
                    field2=None,
                    field3=Relationship(base, "find", args, kwargs),
                )

                find = callback

            return MyModel

        if expected:
            m = make_model()()
            pass
        else:
            with pytest.raises(ModelValidationError):
                make_model()
