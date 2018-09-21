"""
Session interfaces for interacting with Aquarium.

Session interfaces are created by an AqSession instance and use an AqHTTP
instance to make http requests to Aquarium.

Generally, Trident users should be unable to directly access AqHTTP method to
prevent potentially damaging requests or revealing sensitive information.
Session interfaces define a particular way an AqHTTP is used.

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
    # creates samples from a list by calling method CreateInterface.samples
"""

import json

from inflection import pluralize, underscore

from .base import ModelRegistry
from .exceptions import TridentRequestError
from .utils import url_build


class SessionInterface(object):
    """
    Generic session interface.

    Trident users should only be able to make requests through a
    SessionInterface to avoid making arbitrary and potentially damaging
    http requests.
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


class UtilityInterface(SessionInterface):
    """
    Miscellaneous requests for creating, updating, etc.
    """

    # TODO: have ability to save new properties
    def create_samples(self, samples):
        json = [s.dump(include={"field_values"}) for s in samples]
        return self.aqhttp.post('browser/create_samples', {"samples": json})

    def create_items(self, items):
        return [self.aqhttp.get('items/make/{}/{}'.format(
            i.sample.id, i.object_type.id))
            for i in items]

    def create_sample_type(self, sample_type):
        """
        Creates a new sample type
        """
        st_data = sample_type.dump(relations=('field_types'))
        result = self.aqhttp.post('sample_types.json', json_data=st_data)
        sample_type.reload(result)
        return sample_type

    def create_object_type(self, object_type):
        """
        Creates a new object type
        """
        ot_data = object_type.dump()
        result = self.aqhttp.post('object_types.json', json_data=ot_data)
        object_type.reload(result)
        return object_type

    def create_operation_type(self, operation_type):
        """
        Creates a new operation type
        """
        op_data = operation_type.dump(include={
            'field_types': {
                'allowable_field_types': {}
            },
            'protocol': {},
            'cost_model': {},
            'documentation': {},
            'precondition': {}
        })

        # Format 'sample_type' and 'object_type' keys for afts
        for ft_d, ft in zip(
                op_data['field_types'], operation_type.field_types):
            for aft_d, aft in zip(
                    ft_d['allowable_field_types'], ft.allowable_field_types):
                aft_d['sample_type'] = {'name': aft.sample_type.name}
                aft_d['object_type'] = {'name': aft.object_type.name}

        result = self.aqhttp.post('operation_types.json', json_data=op_data)
        operation_type.reload(result)
        return operation_type

    def estimate_plan_cost(self, plan):
        """
        Estimates the plan cost
        """
        result = self.aqhttp.post('launcher/estimate', {'id': plan.id})
        total = 0
        for operation in plan.operations:
            for cost in result['costs']:
                if cost['id'] == operation.id:
                    operation.cost = cost
                    total += (cost['labor'] * cost['labor_rate'] +
                              cost['materials']) * cost['markup_rate']
        return total

    def create_plan(self, plan):
        """
        Saves a plan
        """
        pre_ops = plan.operations
        if pre_ops is None:
            pre_ops = []
        plan_data = plan.to_save_json()
        result = self.aqhttp.post(
            "plans.json?user_id={}".format(self.session.current_user.id),
            json_data=plan_data)
        plan.reload(result)
        post_ops = plan.operations
        for i in range(len(pre_ops)):
            pre_ops[i].reload(post_ops[i])
        return plan

    def save_plan(self, plan):
        plan_data = plan.to_save_json()
        result = self.aqhttp.put(
            "plans/{}.json?user_id={}".format(plan.id,
                                              self.session.current_user.id),
            json_data=plan_data
        )
        plan.reload(result)
        return plan

    def delete_plan(self, plan):
        self.aqhttp.delete('plans/{}'.format(plan.id))

    def delete_wire(self, wire):
        self.aqhttp.delete('wires/{}'.format(wire.id))

    def replan(self, plan_id):
        """
        Copies a plan
        """
        result = self.aqhttp.get(
            'plans/replan/{plan_id}'.format(plan_id=plan_id))
        plan_copy = self.session.Plan.load(result)
        return plan_copy

    def start_job(self, job_id):
        result = self.aqhttp.get(
            'krill/start?job={job_id}'.format(job_id=job_id))
        return result

    def batch_operations(self, operation_ids):
        """
        Batches operations from a list of operation_ids
        """
        self.aqhttp.post('operations/batch', json_data=operation_ids)

    def unbatch_operations(self, operation_ids):
        """
        Unbatches operations from a list of operation_ids
        """
        self.aqhttp.post('operations/batch', json_data=operation_ids)

    def set_operation_status(self, operation_id, status):
        """
        Sets an operation's status
        """
        msg = 'operations/{oid}/status/{status}'.format(
            oid=operation_id,
            status=status)
        self.aqhttp.get(msg)

    def job_debug(self, job_id):
        """
        Runs debug on a job with id=job_id
        """
        self.aqhttp.get('krill/debug/{jid}'.format(jid=job_id))

    def submit_plan(self, plan, user, budget):
        """
        Submits a plan
        """
        user_query = "&user_id=" + str(user.id)
        budget_query = "?budget_id=" + str(budget.id)
        result = self.aqhttp.get('plans/start/' + str(plan.id) +
                                 budget_query + user_query)
        return result

    def update_code(self, code):
        """
        Updates code for a operation_type
        """
        controller = underscore(
            pluralize(code.parent_class))

        code_data = {
            "id": code.parent_id,
            "name": code.name,
            "content": code.content
        }
        result = self.aqhttp.post(url_build(controller, "code"), code_data)
        if "id" in result:
            code.id = result["id"]
            code.parent_id = result["parent_id"]
            code.updated_at = result["updated_at"]
        else:
            raise TridentRequestError(
                "Unable to update code object {}".format(code_data), result)

    def compatible_items(self, sample_id, object_type_id):
        """
        Find items compatible with the field value.
        """
        result = self.aqhttp.post("json/items", {
            "sid": sample_id,
            "oid": object_type_id
        })
        items = []
        for element in result:
            print(element)
        return items

    # TODO: fix delete association
    def delete_data_association(self, association):
        data = {
            "model": {
                "model": "DataAssociation",
                "record_methods": {},
                "record_getters": {}
            },
        }
        data.update(association.dump())
        result = self.aqhttp.post("json/delete", json_data=data)
        return result

    def create_data_association(self, model_inst, key, value, upload=None):
        upload_id = None
        if upload is not None:
            upload_id = upload.id
        data = {
            "model": {
                "model": "DataAssociation",
                "record_methods": {},
                "record_getters": {}
            },
            "parent_id": model_inst.id,
            "key": str(key),
            "object": json.dumps({str(key): value}),
            "parent_class": model_inst.__class__.__name__,
            "upload_id": upload_id
        }
        result = self.aqhttp.post("json/save", json_data=data)
        data_association = model_inst.session.DataAssociation.find(
            result['id'])
        model_inst.data_associations.append(data_association)
        return data_association

    def create_upload(self, upload):
        files = {
            'file': upload.file
        }

        result = self.aqhttp.post(
            "krill/upload?job={}".format(upload.job_id), files=files)
        upload.reload(result)
        return upload


class ModelInterface(SessionInterface):
    """
    Makes requests using AqHTTP that are model specific.
    Establishes a connection between a session object and an Aquarium model.
    """

    def __init__(self, model_name, aqhttp, session):
        super().__init__(aqhttp, session)
        self.model = ModelRegistry.get_model(model_name)

    @property
    def model_name(self):
        """
        Alias for self.model.__name__
        """
        return self.model.__name__

    def _post_json(self, data):
        """
        Posts a json request to session for this interface.
        Attaches raw json and this session instance to the models it retrieves.
        """
        data_dict = {'model': self.model_name}
        data_dict = self._merge_methods(data_dict)
        data_dict.update(data)

        try:
            post_response = self.aqhttp.post(
                'json',
                json_data=data_dict,
            )
        except TridentRequestError as err:
            if err.strerror.status_code == 422:
                return None
            raise err

        if post_response is not None:
            return self.load(post_response)

    def load(self, post_response):
        """
        Loads model instance(s) from data.
        Model instances will be of class defined by self.model.
        If data is a list, will return a list of model instances.
        """
        many = isinstance(post_response, list)
        models = self.model.load(post_response, many=many)
        if many:
            assert len(post_response) == len(models)
            for model in models:
                model.connect_to_session(self.session)
        else:
            models.connect_to_session(self.session)
        return models

    def get(self, path):
        """
        Makes a generic get request
        """
        try:
            response = self.aqhttp.get(path)
        except TridentRequestError as err:
            if err.strerror.status_code == 404:
                return None
            raise err
        return self.load(response)

    def _merge_methods(self, query):
        if hasattr(self.model, 'methods'):
            new_query = dict(query)
            new_query.update({"methods": self.model.methods})
            return new_query
        return query

    def find(self, model_id):
        """
        Finds model by id
        """
        return self._post_json({"id": model_id}, )

    def find_by_name(self, name):
        """
        Finds model by name
        """
        return self._post_json({"method": "find_by_name", "arguments": [name]})

    def array_query(self, method, args, rest, opts=None):
        """
        Finds models based on a query
        """
        if opts is None:
            opts = {}
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        query = {"model": self.model.__name__,
                 "method": method,
                 "arguments": args,
                 "options": options}
        query.update(rest)
        res = self._post_json(query)
        if res is None:
            return []
        return res

    def all(self, rest=None, opts=None):
        """
        Finds all models
        """
        if rest is None:
            rest = {}
        if opts is None:
            opts = {}
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("all", [], rest, options)

    def where(self, criteria, methods=None, opts=None):
        """
        Finds models based on criteria
        """
        rest = {}
        if methods is not None:
            rest = {"methods": methods}
        if opts is None:
            opts = {}
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("where", criteria, rest, options)

    # TODO: implement 'patch' or 'update'? Would this be too dangerous?
    # def patch(self, model_id, json_data):
    #     """
    #     Makes a patch or update from json_data
    #     """
    #     models_name = pluralize(underscore(self.model_name))
    #     result = self.aqhttp.put('{models}/{model_id}'.format(
    #         model_id=model_id, models=models_name), json_data=json_data)
    #     return result

    def new(self, *args, **kwargs):
        """
        Creates a new model instance
        """
        instance = self.model.__new__(self.model)
        instance._session = None
        instance.connect_to_session(self.session)
        instance.__init__(*args, **kwargs)
        return instance
