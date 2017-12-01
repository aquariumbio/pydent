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

import os

import inflection
from pydent.base import ModelRegistry
from pydent.exceptions import TridentRequestError, TridentJSONDataIncomplete
import warnings


class SessionInterface(object):

    """
    Generic session interface.

    Trident users should only be able to make requests through a SessionInterface to avoid making arbitrary and
    potentially damaging http requests.
    """
    def __init__(self, aqhttp, session):
        """
        Initializer for SessionInterface

        :param aqhttp: aqhttp instance for this interface
        :type aqhttp: AqHTTP
        :param session: session instance for this interface
        :type session: AqSession
        """
        self.aqhttp = aqhttp
        self.session = session

# TODO: do we need this interface???
class UtilityInterface(SessionInterface):
    """
    Misc. requests for creating, updating, etc.
    """
    def create_samples(self, samples):
        json = [s.dump() for s in samples]
        return self.aqhttp.post('browser/create_samples', {"samples": json})

    def create_plan(self, plan):
        user_query = "?user_id=" + str(self.session.current_user.id)
        result = self.aqhttp.post(
            '/plans.json' + user_query, plan.dump())
        return result

    def submit_plan(self, plan, user, budget):
        user_query = "&user_id=" + str(user.id)
        budget_query = "?budget_id=" + str(budget.id)
        self.aqhttp.get('/plans/start/' + str(plan.id) +
                        budget_query + user_query)

    def update_code(self, code):
        controller = inflection.underscore(inflection.pluralize(code.parent_class))

        code_data = {
            "id": code.parent_id,
            "name": code.name,
            "content": code.content
        }
        result = self.aqhttp.post(os.path.join(controller, "code"), code_data)
        if "id" in result:
            code.id = result["id"]
            code.parent_id = result["parent_id"]
            code.updated_at = result["updated_at"]
        else:
            raise TridentRequestError("Unable to update code object {}".format(code_data))

    def compatible_items(self, sample_id, object_type_id):
        """Find items compatible with the field value"""
        result = self.aqhttp.post("json/items", {
            "sid": sample_id,
            "oid": object_type_id
        })
        items = []
        for element in result:
            print(element)
        return items


class ModelInterface(SessionInterface):
    """
    Makes requests using AqHTTP that are model specific. Establishes a connection between a session object and an
    Aquarium model.
    """

    def __init__(self, model_name, aqhttp, session):
        super().__init__(aqhttp, session)
        self.model = ModelRegistry.get_model(model_name)

    def _post_json(self, data, get_from_history_ok=False):
        """
        Posts a json request to this interface's session. Attaches raw json and this session instance
        to the models it retrieves.
        """
        data_dict = {'model': self.model_name}
        data_dict.update(data)

        try:
            post_response = self.aqhttp.post('json', json_data=data_dict, get_from_history_ok=get_from_history_ok)
        except TridentRequestError as e:
            warnings.warn(e.args)
            return None
        except TridentJSONDataIncomplete as e:
            warnings.warn(e.args)
            return None
        many = isinstance(post_response, list)

        models = self.model.load(
            post_response, many=many)
        if many:
            assert len(post_response) == len(models)
            for model in models:
                model.connect_to_session(self.session)
        else:
            models.connect_to_session(self.session)
        return models

    @property
    def model_name(self):
        return self.model.__name__

    def find(self, model_id):
        """ Finds model by id """
        return self._post_json({"id": model_id}, get_from_history_ok=True)

    def find_by_name(self, name):
        """ Finds model by name """
        return self._post_json({"method": "find_by_name", "arguments": [name]}, get_from_history_ok=True)

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
        res = self._post_json(query)  # type: dict
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

    def __call__(self, *args, **kwargs):
        """Creates a new model instance"""
        model = self.model(*args, **kwargs)
        model.connect_to_session(self.session)
        return model
