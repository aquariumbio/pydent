"""
Tests for pickling and unpickling of marshallerbase models
"""

import os
import pickle

from pydent.marshaller import MarshallerBase, add_schema, fields


@add_schema
class MyModel(MarshallerBase):
    fields = dict(
        myrelation=fields.Relation("Anymodelname", callback="test_callback",
                                   params=lambda self: (self.x, self.y))
    )

    def test_callback(self, model_name, _xy):
        x, y = _xy
        return x * y


def test_pickling_marshallerbase_model(tmpdir):
    """We expect to be able to pickle and unpickle a model instance"""
    m = MyModel.load({"x": 4, "y": 5})
    filename = os.path.join(tmpdir, 'mymodel.pkl')

    with open(filename, 'wb') as f:
        pickle.dump(m, f)

    m2 = None
    with open(filename, 'rb') as f:
        m2 = pickle.load(f)

    assert m2.x == m.x
    assert m2.y == m.y
    assert m2.myrelation == m.myrelation
