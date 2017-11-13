"""
Marsaller exceptions
"""

class ModelNotFoundError(AttributeError):
    """Could not find model in list of models."""

class CallbackNotFoundError(AttributeError):
    """Could not find callback for the model."""