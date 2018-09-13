from pydent import models
import requests


def test_login_with_requests(config):

    s = requests.Session()

    s.post(config['aquarium_url'] + "/sessions.json", json={
        "session":
            {
                "login": config['login'],
                "password": config['password']
            }
    })

    user = s.post(config['aquarium_url'] + "/json", json={"model": "User", "id": 66}).json()
    print(user)

def test_login(session, config):
    """Test actually logging into the Aquarium server detailed in the config."""
    # current = session.current_user
    aqhttp = session.User.aqhttp
    res = aqhttp.get("users/current.json")
