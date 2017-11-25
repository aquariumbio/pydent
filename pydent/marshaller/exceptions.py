"""
Marsaller exceptions
"""

class MarshallerCallbackNotFoundError(Exception):
    """Could not find callback for the model."""


class MarshallerRelationshipError(Exception):
    """Could not fullfill relationship."""