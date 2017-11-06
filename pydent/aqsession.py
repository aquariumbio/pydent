from pydent.models import AqBase
from pydent.aqhttp import AqHTTP
from pydent.exceptions import TridentModelNotFoundError

class SessionInterface(object):
    """ Interface for making request for specific models. Establishes a connection between a
    session object and an Aquarium model """

    def __init__(self, model_name, session):
        """

        :param model_name: name of the Aquarium model to use
        :type model_name: AqBase
        :param session: Aquarium session instance to use
        :type session: AqHTTP
        """
        self.model = SessionInterface.get_model_by_name(model_name)
        self.session = session

    @staticmethod
    def get_model_by_name(name):
        """
        Gets the model class from its name

        :param name: name of the Aquarium model
        :type name: basestring
        :return: Aquarium model
        :rtype: AqBase
        """
        models = AqBase.models
        if name not in models:
            raise TridentModelNotFoundError("Model \"{0}\" not found."
                                 "Available models: {1}".format(name, ', '.join(AqBase.models.keys())))
        return AqBase.models[name]

    def post_json(self, data):
        """
        Posts a json request to this interface's session. Attaches raw json and this session instance
        to the models it retrieves.
        """
        data_dict = {'model': self.model.__name__}
        data_dict.update(data)
        post_response = self.session.post('json', json_data=data_dict)
        model = self.model.load(post_response)
        if isinstance(model, list):
            for result, model in zip(post_response, model):
                model.raw = result
                model.set_session(self)
        else:
            model.raw = post_response
            model.set_session(self)
        return model

    def find(self, model_id):
        """ Finds model by id """
        return self.post_json({"id": model_id})

    def find_by_name(self, name):
        """ Finds model by name """
        return self.post_json({"method": "find_by_name", "arguments": [name]})

    def array_query(self, method, args, rest, opts=None):
        """ Finds models based on a query """
        if opts is None:
            opts = {}
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        query = {"model": self.model.__name__,
                 "method": method,
                 "arguments": args,
                 "options": options}
        query.update(rest)
        res = self.post_json(query) # type: dict
        if "errors" in res:
            raise Exception(self.model.__name__ + ": " + res["errors"])
        return res

    def all(self, rest=None, opts=None):
        """ Finds all models """
        if rest is None:
            rest = {}
        if opts is None:
            opts = {}
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("all", [], rest, options)

    def where(self, criteria, methods=None, opts=None):
        """ Finds models based on criteria """
        if methods is None:
            methods = {}
        if opts is None:
            opts = {}
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("where", criteria, methods, options)


class AqSession(object):
    """
    Holds a AqHTTP.

    Creates SessionInterface instances when a valid model is used
    as an attribute.

    e.g.
        session1 = AqSession(username, password, aquairum_url)
        session1.User.find(1)
           <User(id=1,...)>
    """

    def __init__(self, login, password, aquarium_url, name=None):
        self.name = name
        self._aqhttp = AqHTTP(login, password, aquarium_url)

    def __getattr__(self, item):
        session = object.__getattribute__(self, "_aqhttp")
        return SessionInterface(item, session)

    def __dir__(self):
        return super().__dir__() + list(AqBase.models.keys())
