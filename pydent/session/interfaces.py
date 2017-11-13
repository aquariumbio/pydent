"""interface.py

This module contains session interfaces for interacting with an Aquarium server. Session interfaces
are created by an AqSession instance and use an AqHTTP instance to make http requests to Aquarium.

Generally, Trident users should be unable to directly access AqHTTP method to prevent potentially
damaging requests or revealing sensitive information. Session interfaces define a particular way
an AqHTTP is used.

Interfaces are roughly grouped into:

(1) ModelInterface - for finding and retrieving Aquarium models and information
(2) CreateInterface - for creating new objects (e.g. new Samples) in Aquarium
(3) UpdateInterface - for updating objects in Aquarium

Example:
    session1 = AqSession(login, password, aquarium_url)
    session1.User
    # => a ModelInterface instance

    session1.User.find(1)
    # use model interface with User to find User(id=1)

    session1.aqhttp.post(...)
    # not allowed

    session1.create
    # => a CreateInterface

    session1.create.samples(list_of_samples)
    # creates samples from a list of samples by calling method "samples" in CreateInterface
"""

import inflection
import os
from pydent.marshaller import ModelRegistry


class SessionInterface(object):
    def __init__(self, aqhttp, session):
        self.aqhttp = aqhttp
        self.session = session


class CreateInterface(SessionInterface):

    def samples(self, samples):
        json = [s.dump() for s in samples]
        return self.aqhttp.post('browser/create_samples', {"samples": json})

    def plan(self, plan):
        user_query = "?user_id=" + str(self.session.current_user.id)
        result = self.aqhttp.post(
            '/plans.json' + user_query, plan.dump())
        return result

    def submit_plan(self, plan, user, budget):
        user_query = "&user_id=" + str(user.id)
        budget_query = "?budget_id=" + str(budget.id)
        self.aqhttp.get('/plans/start/' + str(self.id) +
                        budget_query + user_query)


class UpdateInterface(SessionInterface):

    def code(self, parent_class):
        class_name = parent_class.__class__.__name__
        controller = inflection.underscore(class_name)
        controller = inflection.pluralize(controller)

        result = self.aqhttp.post(os.path.join(
            controller, "code"), parent_class.dump(only=("id", "name", "content")))
        if "id" in result:
            self.id = result["id"]
            self.parent_id = result["parent_id"]
            self.updated_at = result["updated_at"]


class ModelInterface(SessionInterface):
    """
    Makes requests using AqHTTP that are model specific. Establishes a connection between a session object and an
    Aquarium model.

    Trident users should only be able to make requests through a SessionInterface to avoid making arbitrary and
    potentially damaging http requests.
    """

    def __init__(self, model_name, aqhttp, session):
        super().__init__(aqhttp, session)
        self.model = ModelRegistry.get_model(model_name)

    # TODO: for self.model.load, require that a session be passed in...
    def post_json(self, data):
        """
        Posts a json request to this interface's session. Attaches raw json and this session instance
        to the models it retrieves.
        """
        data_dict = {'model': self.model.__name__}
        data_dict.update(data)
        post_response = self.aqhttp.post('json', json_data=data_dict)

        many = isinstance(post_response, list)

        models = self.model.load(
            post_response, many=many)

        if many:
            for result, model in zip(post_response, models):
                model.connect_to_session(self.session)
        else:
            models.connect_to_session(self.session)
        return models

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
        res = self.post_json(query)  # type: dict
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
