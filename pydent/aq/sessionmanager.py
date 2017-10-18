
class SessionManagerHook(type):
    """ Hook for confinient calling of different sessions. E.g. Session.Nursery is equivalent to Session.set(
    "Nursery") """

    def __init__(cls, name, bases, clsdict):
        cls.session = None
        cls.sessions = {}
        super(SessionManagerHook, cls).__init__(name, bases, clsdict)

    def __getattr__(cls, item):
        sessions = object.__getattribute__(cls, "sessions")
        if item in sessions:
            cls.set(item)
        else:
            try:
                return object.__getattribute__(cls, item)
            except AttributeError:
                raise AttributeError("Session {0} not found. Select from {1}".format(item, sessions.keys()))

class SessionManager(object, metaclass=SessionManagerHook):
    """ Manages api interface sessions """

    session = None
    sessions = {}

    @classmethod
    def create_session(cls, api_connector, *args, name=None, **kwargs):
        cls.session = api_connector(*args, **kwargs)
        cls._add_session(cls.session, name)
        return cls

    @classmethod
    def _add_session(cls, api_connector, name):
        cls.sessions[name] = api_connector
        print(cls.sessions)

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
