"""Schema exceptions."""


class SchemaException(Exception):
    pass


class SchemaModelException(Exception):
    pass


"""
Field validation exceptions
"""


class FieldValidationError(Exception):
    pass


class AllowNoneFieldValidationError(FieldValidationError):
    pass


class CallbackValidationError(Exception):
    pass


"""
Model validation exceptions
"""


class ModelValidationError(Exception):
    pass


class ExceptionCollection(Exception):
    """Context dependent exception for capturing multiple exceptions.

    Call `r` to gather exceptions, upon exiting, a single
    ExceptionCollection will be raised with a summary of all the
    internal exceptions.
    """

    def __init__(self, *args, header=''):
        self.args = args
        self.header = header
        self.errors = None

    def r(self, exception):
        self.errors.append(exception)

    def raise_exception_class(self, exception_class):
        """Raise an exception class, if it was collected."""
        errors = self.group_errors.get(exception_class.__name__, [])
        if errors:
            raise exception_class(errors)

    def group_errors(self):
        grouped = {}
        for e in self.errors:
            grouped.setdefault(e.__class__.__name__, []).append(e)
        return grouped

    def __enter__(self):
        self.errors = []
        return self

    def __exit__(self, *args):
        if self.errors:
            # raise MultipleValidation(self.errors)
            try:
                msg = "{}: {}".format(self.__class__.__name__, self.header)
                group_by_exception = self.group_errors()
                for g, errors in group_by_exception.items():
                    msg += "\n {}(s):".format(g)
                    for i, e in enumerate(errors):
                        msg += '\n  ({}): {}'.format(i, e)
                self.args = (msg,)
            except Exception as e:
                raise Exception("There was an error raising exceptions {}\n".format(self.errors, e))
            raise self


class MultipleValidationError(ModelValidationError, ExceptionCollection):
    """Model validation exception."""
    pass
