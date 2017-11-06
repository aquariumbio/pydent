from requests.exceptions import RequestException

class TridentRequestError(RequestException):
    """There was an ambiguous exception that occured handling your request."""


class TridentLoginError(RequestException):
    """Trident is not properly connected to the server.
     Verify login credentials are correct."""


class TridentModelNotFoundError(AttributeError):
    """Trident could not find model in list of models."""
