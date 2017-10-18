import os
import requests

class AqHTTP(object):

    def __init__(self, login, password, home):
        self.login = login
        self.password = password
        self.home = home
        self.session = None
        self._login()

    def _create_session(self):
        return {
            "session": {
                "login": self.login,
                "password": self.password
            }
        }

    def _login(self):
        """ """
        session_data = self._create_session()
        r = requests.post(os.path.join(self.home, "sessions.json"), json=session_data)
        headers = { "cookie": AqHTTP.__fix_remember_token(r.headers["set-cookie"]) }
        self.session = requests.Session()
        self.session.headers.update(headers)

    @staticmethod
    def __fix_remember_token(h):
        parts = h.split(';')
        rtok = ""
        for c in parts:
            cparts = c.split('=')
            if re.match('remember_token', cparts[0]):
                rtok = cparts[1]
        return "remember_token="+rtok+"; "+h


    def post(self, path, json=None, **kwargs):
        return self.session.post(os.path.join(self.home, path), json=json, **kwargs)

    def put(self, path, json=None, **kwargs):
        return self.session.post(os.path.join(self.home, path), json=json, **kwargs)

    def get(self, path, json=None, **kwargs):
        return self.session.post(os.path.join(self.home, path), json=json, **kwargs)

    def put(self, path, json=None, **kwargs):
        return self.session.post(os.path.join(self.home, path), json=json, **kwargs)