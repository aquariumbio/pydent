from pydent import AqSession
from pydent.browser.browser_interface import BrowserInterface
from pydent.browser import Browser


class BrowserSession(AqSession):

    INTERFACE_CLASS = BrowserInterface

    def __init__(self, login, password, aquarium_url, name=None):
        super().__init__(login, password, aquarium_url, name=name)
        self.browser = Browser(self)

    @classmethod
    def from_session(cls, session):
        instance = cls.__new__(cls)
        instance._aqhttp = session._aqhttp
        instance._current_user = session._current_user
        instance.initialize_interface()
        instance.browser = Browser(instance)
        return instance

    def clear(self):
        """
        Clears the browser cache.

        :return: None
        :rtype: None
        """
        self.browser.clear()