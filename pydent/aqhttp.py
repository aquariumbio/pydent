"""
AqHTTP (:mod:`pydent.aqhttp`)
=============================

.. currentmodule:: pydent.aqhttp

Request class for making raw http requests to Aquarium

This module contains the AqHTTP class, which can make arbitrary post/put/get
requests to Aquarium and returns JSON data.

Generally, Trident users should be unable to make arbitrary requests using this
class.
Users should only access these methods indirectly through a ``Session`` or
``SessionInterface`` instance.
"""
import json
from typing import Dict

import requests
from retry import retry

from pydent.exceptions import ForbiddenRequestError
from pydent.exceptions import TridentJSONDataIncomplete
from pydent.exceptions import TridentLoginError
from pydent.exceptions import TridentRequestError
from pydent.exceptions import TridentTimeoutError
from pydent.utils import logger
from pydent.utils import pprint_data
from pydent.utils import url_build


LOGIN_RETRY_DELAY = 1
LOGIN_RETRY_BACKOFF = 1
LOGIN_RETRY_MAX_DELAY = 2


class AqHTTP:
    """Defines a Python to Aquarium server connection. Makes HTTP requests to
    Aquarium and returns JSON.

    This class should be obscured from Trident users so that they cannot
    make arbitrary requests to an Aquarium server and get sensitive
    information (e.g. User json that is returned contains api_key,
    password_digest, etc.) or make damaging posts. These requests should be made
    by a SessionInterface object instead.
    """

    TIMEOUT = 10

    def __init__(self, login: str, password: str, aquarium_url: str):
        """Initializes an aquarium session with login, password, and server.

        :param login: Aquarium login
        :type login: str
        :param aquarium_url: aquarium url to the server
        :type aquarium_url: str
        """
        self.login = login  #: the user login name
        self.aquarium_url = aquarium_url  #: the aquarium url
        self._requests_session = None  #: the requests session
        self.timeout = self.__class__.TIMEOUT  #: the timeout (s) for requests
        self._login(login, password)
        self.log = logger(name="AqHTTP@{}".format(aquarium_url))  #: the logger
        self._using_requests = True  #: if False, any HTTP requests will throw and error
        self.num_requests = 0  #: number of requests counter

    def on(self):
        """Turn on requests. When requests are off, this causes.

        :class:`ForbiddenRequestError <pydent.exceptions.ForbiddenRequestError>`
        to be raised if a request is made.

        :return: None
        """
        self._using_requests = True

    def off(self):
        """Turn off requests. Will cause.

        :class:`ForbiddenRequestError <pydent.exceptions.ForbiddenRequestError>`
        to be raised if a request is made.

        :return: None
        """
        self._using_requests = False

    @staticmethod
    def _format_response_info(
        response: requests.Response,
        include_text: bool = False,
        include_body: bool = False,
    ) -> str:
        if response is not None:
            if response.status_code >= 400:
                include_text = True
            info = dict(response.request.__dict__)
            info.update({"seconds": response.elapsed.total_seconds()})
            msg = "REQUEST: (t={seconds}s)  {method} {url}".format(**info)
            if include_body:
                body = info["body"]
                try:
                    my_json = body.decode("utf8").replace("'", '"')
                    body = json.loads(my_json)
                    body = pprint_data(body, max_list_len=10)
                except Exception:
                    pass
                msg = msg + "\n" + "BODY: {body}".format(body=body)
            if include_text:
                text = getattr(response, "text", "")
                try:
                    text = json.dumps(json.loads(text), indent=2)
                except Exception:
                    pass
                msg = msg + "\n" + "TEXT: {text}".format(text=text)
            return msg
        return "RESPONSE: NO RESPONSE"

    @staticmethod
    def _format_request_status(response: requests.Response) -> str:
        if response is not None:
            return "STATUS:  {} {}".format(response.status_code, response.reason)
        return "STATUS: NO RESPONSE"

    @property
    def url(self) -> str:
        """An alias of aquarium_url."""
        return self.aquarium_url

    @staticmethod
    def create_session_json(login: str, password: str) -> Dict:
        return {"session": {"login": login, "password": password}}

    @retry(
        TridentLoginError,
        delay=LOGIN_RETRY_DELAY,
        backoff=LOGIN_RETRY_BACKOFF,
        max_delay=LOGIN_RETRY_MAX_DELAY,
        tries=3,
    )
    def _login(self, login: str, password: str):
        """Login to aquarium and saves header as a requests.Session()

        :param login: Aquarium login
        :param password: Aquarium password
        :return: None
        :raises:
            TridentLoginError: If Aquarium authentication fails or server could not
            be contacted
            TridentTimeoutError: If response time exceeds specified timeout
        """
        session_data = self.create_session_json(login, password)
        try:
            res = requests.post(
                url_build(self.aquarium_url, "sessions.json"),
                json=session_data,
                timeout=self.timeout,
            )
            if res is None:
                raise requests.exceptions.ConnectionError
            cookies = dict(res.cookies)

            # Check for remember token
            if not any(["remember_token" in k for k in dict(res.cookies)]):
                raise TridentLoginError(
                    "Authentication error - Cannot connect to Aquarium at {}. "
                    "Please check that your login, password, and url are correct."
                )

            # fix remember token (for some outdated versions of Aquarium)
            for c in dict(cookies):
                if "remember_token" in c:
                    cookies["remember_token"] = cookies[c]
            # TODO: do we remove the session cookie to handle asynchronous requests?
            self.cookies = dict(cookies)
        except requests.exceptions.MissingSchema as error:
            raise TridentLoginError(
                "Aquarium URL {} incorrectly formatted. {}".format(
                    self.aquarium_url, error.args[0]
                )
            )
        except requests.exceptions.ConnectTimeout:
            raise TridentTimeoutError(
                "Either Aquarium took too long to respond during login or your internet"
                " connection is slow. Make sure the url {} is correct."
                " Alternatively, use Session.set_timeout"
                " to increase the request timeout.".format(self.aquarium_url)
            )
        except requests.exceptions.ConnectionError:
            raise TridentLoginError(
                "Could not contact '{}'. Login request returned no response".format(
                    self.aquarium_url
                )
            )

    @staticmethod
    def _serialize_request(url: str, method: str, body: dict) -> str:
        return json.dumps({"url": url, "method": method, "body": body}, sort_keys=True)

    @classmethod
    def _dispatch_response(cls, response):
        if response.status_code == 422:
            pass
        elif response.status_code >= 400:
            response_info = cls._format_response_info(response)
            request_status = cls._format_request_status(response)
            msg = "\n".join(
                [
                    "The Aquarium server returned an error.",
                    request_status,
                    response_info,
                ]
            )
            raise TridentRequestError(msg, response)

    def request(
        self,
        method: str,
        path: str,
        timeout: int = None,
        allow_none: bool = True,
        **kwargs,
    ) -> dict:
        """Performs a http request.

        :param method: request method (e.g. 'put', 'post', 'get', etc.)
        :type method: str
        :param path: url to perform the request
        :type path: str
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param allow_none: if False will raise error when json_data
                contains a None or null value (default: True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """

        url = url_build(self.aquarium_url, path)
        if not self._using_requests:
            raise ForbiddenRequestError(
                "Attempted a request ({} {}) when requests have been turned OFF."
                "\nDATA: {}".format(method.upper(), url, kwargs["json"])
            )

        if timeout is None:
            timeout = self.timeout
        if not allow_none and "json" in kwargs:
            self._disallow_null_in_json(kwargs["json"])

        self.num_requests += 1
        response = requests.request(
            method, url, timeout=timeout, cookies=self.cookies, **kwargs
        )

        self.log.info(self._format_response_info(response))
        self._dispatch_response(response)
        return self._response_to_json(response)

    def _response_to_json(self, response: requests.Response) -> dict:
        """Turns :class:`requests.Request` instance into a json.

        Raises TridentRequestError if an error occurs.
        """

        if response.url == url_build(self.aquarium_url, "signin"):
            msg = (
                "There was an error with authenticating the request. Aquarium "
                + "re-routed to the sign-in page."
            )
            raise TridentRequestError(msg, response)

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            msg = "Response is not JSON formatted"
            msg += "\nMessage:\n" + response.text
            self.log.error(self._format_response_info(response))
            raise TridentRequestError(msg, response)
        if response_json:
            if "errors" in response_json:
                errors = response_json["errors"]
                if isinstance(errors, list):
                    errors = "\n".join(errors)
                msg = "Error response:\n{}".format(errors)
                raise TridentRequestError(msg, response)
        return response_json

    @staticmethod
    def _disallow_null_in_json(json_data: dict):
        """Raises :class:pydent.exceptions.TridentJSONDataIncomplete exception
        if json data being sent contains a null value.

        :raises:
            TridentJSONDataIncomplete: if json data containers a null or None value.
        """
        if None in json_data.values():
            raise TridentJSONDataIncomplete(
                "JSON data {} contains a null value.".format(json_data)
            )

    def post(
        self,
        path: str,
        json_data: dict = None,
        timeout: int = None,
        allow_none: bool = True,
        **kwargs,
    ) -> dict:
        """Make a post request to the session.

        :param path: url
        :type path: str
        :param json_data: json_data to post
        :type json_data: dict
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param allow_none: if False throw error if json_data contains a null
                or None value (default True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request(
            "post",
            path,
            json=json_data,
            timeout=timeout,
            allow_none=allow_none,
            **kwargs,
        )

    def put(
        self,
        path: str,
        json_data: dict = None,
        timeout: int = None,
        allow_none: bool = True,
        **kwargs,
    ) -> dict:
        """Make a put request to the session.

        :param path: url
        :type path: str
        :param json_data: json_data to post
        :type json_data: dict
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param allow_none: if False throw error when json_data contains a null
                or None value (default True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request(
            "put",
            path,
            json=json_data,
            timeout=timeout,
            allow_none=allow_none,
            **kwargs,
        )

    def get(
        self, path: str, timeout: int = None, allow_none: bool = True, **kwargs
    ) -> dict:
        """Make a get request to the session.

        :param path: url
        :type path: str
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param allow_none: if False throw error when json_data contains a null
                or None value (default: True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request(
            "get", path, timeout=timeout, allow_none=allow_none, **kwargs
        )

    def delete(self, path: str, timeout: int = None, **kwargs) -> dict:
        return self.request("delete", path, timeout=timeout, **kwargs)

    def __repr__(self):
        return "<{}(user='{}', url='{}')>".format(
            self.__class__.__name__, self.login, self.aquarium_url
        )

    def __str__(self):
        return self.__repr__()
