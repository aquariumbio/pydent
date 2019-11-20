"""
Exceptions (:mod:`pydent.exceptions`)
=====================================

.. currentmodule:: pydent.exceptions

Trident exceptions
"""


class TridentBaseException(Exception):
    """Base exception for all trident errors."""


class TridentRequestError(TridentBaseException):
    """There was an ambiguous exception that occurred handling your request."""

    def __init__(self, msg, response):
        super().__init__(msg)
        self.response = response


class AquariumError(TridentBaseException):
    """Aquarium raised an error."""


class AquariumModelNotFound(TridentBaseException):
    """Returned when Aquarium could not find a given model."""


class ForbiddenRequestError(TridentBaseException):
    """Raised when Trident attempts to make a request after requests have been
    explicitly turned off."""


class TridentJSONDataIncomplete(TridentBaseException):
    """JSON data contains a null value and may be incomplete."""


class TridentLoginError(TridentBaseException):
    """Trident is not properly connected to the server.

    Verify login credentials are correct.
    """


class TridentTimeoutError(TridentBaseException):
    """Trident took too long to respond."""


class TridentModelNotFoundError(TridentBaseException):
    """Trident could not find model in list of models."""


class AquariumModelError(TridentBaseException):
    """An error occurred with this Aquarium model."""


class NoSessionError(TridentBaseException):
    """There was no session attached to the model, but one is required."""


class SessionAlreadySet(TridentBaseException):
    """Cannot set session to models with a session already set."""
