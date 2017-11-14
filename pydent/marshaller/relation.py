from marshmallow.fields import Nested

class Relation(Nested):
    """Defines a nested relationship with another model.

    Uses "callback" with "params" to find models. Callback is
    applied to the model that is fullfilling this relation. Params may include lambdas
    of the form "lambda self: <do something with self>" which passes in the model
    instance.
    """

    def __init__(self, model, callback, params, *args, **kwargs):
        """Relation initializer.

        :param model: target model
        :type model: basestring
        :param args: positional parameters
        :type args:
        :param callback: function to use in Base to find model
        :type callback: basestring or callable
        :param params: tuple or list of variables (or callables) to use to search for the model. If param is
        a callable, the model instance will be passed in.
        :type params: tuple or list
        :param kwargs: rest of the parameters
        :type kwargs:
        """
        super().__init__(model, *args, load_only=True, **kwargs) #note that "load_only" is important
        self.callback = callback

        # force params to be an iterable
        if not (isinstance(params, list) or isinstance(params, tuple)):
            params = (params,)
        self.params = params

    def __repr__(self):
        return "<Relation (model={}, callback={}, params={})>".format(self.nested, self.callback, self.params)
