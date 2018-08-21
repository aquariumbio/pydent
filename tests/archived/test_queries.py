def test_find_returns_none(session):
    """Find queries should return None, if model is not found"""
    x = session.Operation.find(1000000000000)
    assert x is None


def test_where_returns_empty_array(session):
    """Where queries should return an empty array if no models are found (not None)"""
    x = session.Operation.where({"id": 20947983476893498573987})
    assert x == []