from pydent import AqSession


def test_instance():

    session = AqSession("vrana", "Mountain5", "http://52.27.43.242/")

    fas = session.OperationType.where({"name": "Fragment Analyzing", "deployed": True})
    fa = fas[0]

    fa.instance()

