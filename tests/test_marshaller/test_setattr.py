import pytest
from pydent.marshaller import MarshallerBase, add_schema, Relation

def test_setattr():
    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation("SomeModel", callback="test_callback", params=[])
        )

        def __init__(self, other_id=None):
            self.other_id = other_id
            super().__init__()

        def test_callback(self, model_name):
            return self.other_id


    m = MyModel.load({"other_id": 5})

    assert hasattr(m, "myrelation")
    assert m.myrelation == 5
    assert hasattr(m, "myrelation")

    # when underlying parameters used in callback change, myrelation should change as well
    m.other_id = 6
    assert m.myrelation == 6