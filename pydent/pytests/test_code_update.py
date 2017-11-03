import pytest
from pydent.aq import *
import uuid


def test_code_retrieval(load_session):

    ot = OperationType.find_by_name("Test Code API")
    codes = ot.codes
    code = codes[-1]
    code.content = "New code!" + str(uuid.uuid4())
    code.update()
    c = ot.codes[-1]
    assert c.content == code.content
