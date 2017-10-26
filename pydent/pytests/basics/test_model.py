import pytest
from pydent.aq import *

# TODO: find models from BaseHook.bases.values() and add fixture as argument
def test_models(load_session):
    model = SampleType
    all = model.all()
    for i in [0, -1]:
        # pick first or last
        m = all[i]

        # find_by_name
        assert m == model.find_by_name(m.name)

        # find (by id)
        assert model.find(m.id) == m

        # where
        assert model.where({"id": m.id}) == [m]

def test_library(load_session):

    l = Library.find_by_name("DNA")
    codes = l.codes
    for c in l.codes:
        print(c)
