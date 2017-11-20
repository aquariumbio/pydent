from pydent.models import User


# TODO: These tests aren't appropriate
def test_login(session, config):
    """Test actually logging into the Aquarium server detailed in the config."""
    current = session.current_user
    assert isinstance(current, User)
    assert current.login == config["login"]
    print(current)
