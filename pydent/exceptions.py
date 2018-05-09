"""
Trident exceptions
"""

from requests.exceptions import RequestException, ConnectTimeout


class TridentRequestError(RequestException):
    """There was an ambiguous exception that occured handling your request."""
    def __init__(self, message, response):
        self.message = message
        self.response = response


class TridentJSONDataIncomplete(RequestException):
    """JSON data contains a null value and may be incomplete."""


class TridentLoginError(RequestException):
    """Trident is not properly connected to the server.
     Verify login credentials are correct."""


class TridentTimeoutError(ConnectTimeout):
    """Trident took too long to respond"""


class TridentModelNotFoundError(AttributeError):
    """Trident could not find model in list of models."""


class AquariumModelError(Exception):
    """An error occured with this Aquarium model"""
