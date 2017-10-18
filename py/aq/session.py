from py.aq.aqhttp import AqHTTP
import json

class SessionManagerHook(type):
    """ Hook for confinient calling of different sessions. E.g. Session.Nursery is equivalent to Session.set(
    "Nursery") """

    def __init__(cls, name, bases, clsdict):
        cls.session = None
        cls.sessions = {}
        super(SessionManagerHook, cls).__init__(name, bases, clsdict)

    def __getattr__(cls, item):
        sessions = cls.sessions
        if item in sessions:
            cls.set(item)
        else:
            return getattr(cls, item)


class SessionManager(object, metaclass=SessionManagerHook):
    """ Manages api interface sessions """

    session = None
    sessions = {}

    @classmethod
    def create(cls, api_connector, *args, name=None, **kwargs):
        cls.session = api_connector(*args, **kwargs)
        cls._add_session(cls.session, name)

    @classmethod
    def _add_session(cls, api_connector, name):
        cls.sessions[name] = api_connector

    @classmethod
    def set(cls, name):
        sessions = cls.sessions
        cls.session = sessions[name]

    @classmethod
    def session_name(cls):
        for name, session in cls.sessions.items():
            if cls.session == session:
                return name

    @classmethod
    def close(cls):
        cls.session = None


class Session(SessionManager):
    """ Class for creating sessions """

    @classmethod
    def create(cls, login, password, home, name=None):
        return SessionManager.create(AqHTTP, login, password, home, name=name)

    @classmethod
    def create_from_config(cls, path_to_config, name=None):
        config = json.load(path_to_config)
        cls.create(config["login"], config["password"], config["aquarium_url"], name=name)