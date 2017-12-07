"""
Marsaller exceptions
"""


class MarshallerCallbackNotFoundError(Exception):
    """Could not find callback for the model."""


class MarshallerRelationshipError(AttributeError):
    """Could not fullfill relationship."""
