"""
Exceptions (:mod:`pydent.exceptions`)
=====================================

.. currentmodule:: pydent.exceptions

Trident exceptions
"""
from typing import Type
from warnings import warn


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


class PlannerException(TridentBaseException):
    """Generic planner Exception."""


class PlannerVerificationException(TridentBaseException):
    """Raised when object is not in plan but is required."""


class TridentDepreciationWarning(DeprecationWarning):
    """Raised when a feature or api is depreciated."""


class AquariumQueryLanguageValidationError(TridentBaseException):
    """Raised when aql is provided with an invalide query."""


# class WarningLimit(object):
#
#     _limits = {}
#
#     def __init__(self, msg: str, limit: int = 1, warning_class: Type = TridentDepreciationWarning):
#         self.msg = msg
#         self.warning_class = warning_class
#         self._limits[msg] = (0, limit)
#
#     def warn(self):
#         a, b = self._limits[self.msg]
#         if a < b:
#             warn(self.warning_class(self.msg))
#             self._limits[self.msg] = (a + 1, b)
#         else:
#             return
#
# def warn_with_limits(msg: str, limit: int):
#     WarningLimit(msg, limit).warn()
