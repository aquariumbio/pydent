import pytest
from marshmallow import pprint
from pydent import models, ModelRegistry
from pydent.exceptions import TridentRequestError

# # skip tests
# pytestmark = pytest.mark.skip("These tests utilize a live session with alot of requests."
#                               "In the future, we may want to utilize something like pyvrc to avoid"
#                               "sending live requests to Aquarium.")


class TestModelRelationships:
    """
    Tests expected relationship access to Aquarium models.

    For example, a Sample is expected to have access to a SampleType model
    through its 'sample_type' attribute. These tests will check that
    'sample_type' returns a SampleType instance.

    The fixture will attempt to find *some* model, avoiding the use of 'all()'.
    This code isn't ideal, but may be useful in conjunction with request vcr.
    """

    # @pytest.fixture(params=ModelRegistry.models.values())
    @pytest.mark.parametrize('model_class', ModelRegistry.models.values())
    def test_model_relationships(self, session, request, model_class):
        """
        Tries to access nested relationships in an a model

        :param session: pytest fixture that has returned a live trident session
        :type session: AqSession
        :param request: parameter from the fixture
        :type request: dict
        :return: None
        :rtype: None
        """

        # Try to find a live model
        model_class_name = model_class.__name__  # e.g. "FieldType"
        model_instance = None
        for iden in [1, 100, 1000, 5000, 10000, 54069, 130000, 200000, 76858][::-1]:
            try:
                print("Finding '{}' model with {}".format(model_class_name,
                                                          iden))
                interface = getattr(session, model_class_name)

                model_instance = interface.find(iden)
            except TridentRequestError as e:
                print(e)
            if model_instance:
                break
        if model_instance is None:
            raise Exception("Could not find a {}".format(model_class))

        # Get the model class
        print(model_instance)
        pprint(model_instance.raw)

        # Discover and access model relationships
        relationships = model_class.get_relationships()

        print("\nRelationships:")
        pprint(relationships)
        for attr, relationship in relationships.items():
            print("\tGetting attribute '{}'".format(attr))
            val = getattr(model_instance, attr)
            nested_model = ModelRegistry.get_model(relationship.nested)
            print('model: {}, attr: {}, val: {}'.format(nested_model,
                                                        attr,
                                                        val))
            if relationship.many:
                if val is not None:
                    if len(val) > 0:
                        assert isinstance(val[0], nested_model)
            else:
                nested_model = ModelRegistry.get_model(relationship.nested)
                if val is not None:
                    assert isinstance(val, nested_model)
