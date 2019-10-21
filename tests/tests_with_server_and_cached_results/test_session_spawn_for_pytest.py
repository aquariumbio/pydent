KEY = "AGGLKJDLFJ"


class TestSessionSpawn:
    """test to unsure fixure is not alterable by other tests."""

    def test1(self, session):
        setattr(session, KEY, 1)

    def test2(self, session):
        assert not hasattr(session, KEY)
