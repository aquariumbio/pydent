
def test_find_returns_none(session):

    x = session.Operation.find(1000000000000)
    assert x is None


def test_where_returns_empty_array(session):

    x = session.Operation.where({"id": 20947983476893498573987})
    assert x == []