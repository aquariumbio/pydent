import pytest
from pydent import *

def test_sample_type_all(load_session):
    g = globals()
    s = SampleType
    SampleType.all()