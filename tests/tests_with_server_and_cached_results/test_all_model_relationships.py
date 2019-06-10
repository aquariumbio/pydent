import pytest
from pydent.marshaller import ModelRegistry

# skip tests
pytestmark = pytest.mark.skip("These tests utilize a live session with alot of requests."
                              "In the future, we may want to utilize something like pyvrc to avoid"
                              "sending live requests to Aquarium.")

relationship_pairs = []
for model in ModelRegistry.models.values():
    for attr, relationship in model.get_relationships().items():
        relationship_pairs.append((model, attr, relationship))


class TestModelRelationships:
    """
    Tests expected relationship access to Aquarium models.

    For example, a Sample is expected to have access to a SampleType model
    through its 'sample_type' attribute. These tests will check that
    'sample_type' returns a SampleType instance.

    The fixture will attempt to find *some* model, avoiding the use of 'all()'.
    This code isn't ideal, but may be useful in conjunction with request vcr.
    """

    @pytest.mark.parametrize('model_class,attr,relationship', relationship_pairs)
    def test_model_relationships(self, session, model_class, attr, relationship):
        """
        Tries to access nested relationships in an a model
        """
        interface = session.model_interface(model_class.__name__)

        print("\nRelationships:")

        num_models = 1
        tries = 6
        curr = 0
        num_model_increase = 10
        while curr < tries and num_models:
            print(curr)
            curr += 1

            models = interface.last(num_models)
            print(len(models))
            for model_instance in models:
                val = getattr(model_instance, attr)
                nested_model = ModelRegistry.get_model(relationship.nested)
                if relationship.many:
                    if val:
                        assert isinstance(val[0], nested_model), "Value should be a {}, not a {}".format(nested_model, type(val[0]))
                        num_models = 0
                    else:
                        num_models += num_model_increase
                else:
                    if val is not None:
                        assert isinstance(val, nested_model), "Value should be a {}, not a {}".format(nested_model, val)
                        num_models = 0
                    else:
                        num_models += num_model_increase
        if num_models > 0:
            raise Exception("{} is missing an example of the relationship for '{}'".format(model_class, attr))
