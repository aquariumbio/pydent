"""Session interfaces for interacting with Aquarium.

Session interfaces are created by an AqSession instance and use an AqHTTP
instance to make http requests to Aquarium.

Generally, Trident users should be unable to directly access AqHTTP methods to
prevent potentially damaging requests or revealing sensitive information.
Session interfaces define a particular way an AqHTTP is used.

Interfaces are roughly grouped into:

(1) ModelInterface - for finding and retrieving Aquarium models and information
(2) UtilityInterface -- contains methods for creating and updating objects in Aquarium

Example:
    session1 = AqSession(login, password, aquarium_url)
    session1.User
    # => a ModelInterface instance

    session1.User.find(1)
    # use model interface with User to find User(id=1)

    session1.aqhttp.post(...)
    # not allowed

    session1.create
    # => a UtilityInterface

    session1.utils.create_samples(list_of_samples)
    # creates samples from a list by calling method UtilityInterface.samples """
import json
from abc import ABC
from abc import abstractmethod
from typing import Generator
from typing import List
from typing import Union

from inflection import pluralize
from inflection import underscore

from .exceptions import TridentRequestError
from .utils import url_build
from pydent.marshaller.base import SchemaModel
from pydent.marshaller.registry import ModelRegistry


class SessionInterface:
    """Generic session interface.

    Trident users should only be able to make requests through a
    SessionInterface to avoid making arbitrary and potentially damaging
    http requests.
    """

    __slots__ = ["aqhttp", "session"]

    def __init__(self, aqhttp, session):
        """Initializer for SessionInterface.

        :param aqhttp: aqhttp instance for this interface
        :type aqhttp: AqHTTP
        :param session: session instance for this interface
        :type session: AqSession
        """
        self.aqhttp = aqhttp
        self.session = session


class CRUDInterface(SessionInterface):
    """Create, Update, Delete interface.

    Methods for communicating with Aquarium's JSON controller.
    """

    __slots__ = ["aqhttp", "session"]

    # def _validate_model_id(self, model):
    #     if not hasattr(model, 'id') or model.id is None:
    #         raise TridentRequestError("Model {} has no id.".format(model))

    def _model_controller(
        self,
        method: str,
        table: str,
        model_id: Union[str, int, None],
        data: Union[None, dict],
        params=None,
    ) -> dict:
        """Method for creating, updating, and deleting models.

        :param method: Request method name (one of 'put', 'post', 'delete'
        :param table: Table name of model (e.g. 'samples' or 'data_associations')
        :param model_id: Optional model_id (not required for 'post')
        :param data: data
        :param params: controller parameters
        :return: json formatted server response
        :rtype: dict
        """
        if model_id:
            url = "{}/{}.json".format(table, model_id)
        else:
            url = "{}.json".format(table)

        result = self.aqhttp.request(method, url, json=data, params=params)
        return result

    def model_create(self, table, data, params=None):
        return self._model_controller("post", table, None, data, params)

    def model_update(self, table, model_id, data, params=None):
        return self._model_controller("put", table, model_id, data, params)

    def model_delete(self, table, model_id, params=None):
        if model_id is None:
            return
        return self._model_controller("delete", table, model_id, None, params)

    def _json_controller(
        self,
        method,
        model_name,
        model_data,
        record_methods: List[str] = None,
        record_getters: List[str] = None,
    ):
        """Method for creating, updating, and deleting models using Aquarium's
        JSON controller.

        :param method: Method name (e.g. "save", "delete")
        :type method: basestring
        :param model_name: Model name
        :type model_name: basestring
        :param model_data: Additional model and method data
        :type model_data: dict
        :param record_methods: Optional 'record_methods' key
        :type record_methods: dict
        :param record_getters: Optional 'record_getters' key
        :type record_getters: dict
        :return: json formatter response
        :rtype: basestring
        """

        if record_methods is None:
            record_methods = {}
        if record_getters is None:
            record_getters = {}

        data = {
            "model": {
                "model": model_name,
                "record_methods": record_methods,
                "record_getters": record_getters,
            }
        }

        if model_data:
            data.update(model_data)

        if method:
            url = "json/" + method
        else:
            url = "json"

        try:
            post_response = self.aqhttp.post(url, json_data=data)
            return post_response
        except TridentRequestError as err:
            raise err

        # TODO: is this code necessary?
        # result = self.aqhttp.post("json" + method, json_data=data)
        # return result

    def json_delete(
        self,
        model_name,
        model_data,
        record_methods: List[str] = None,
        record_getters: List[str] = None,
    ):
        return self._json_controller(
            "delete", model_name, model_data, record_methods, record_getters
        )

    def json_save(
        self,
        model_name,
        model_data,
        record_methods: List[str] = None,
        record_getters: List[str] = None,
    ) -> dict:
        return self._json_controller(
            "save", model_name, model_data, record_methods, record_getters
        )

    def json_post(
        self,
        model_name,
        model_data,
        record_methods: List[str] = None,
        record_getters: List[str] = None,
    ):
        return self._json_controller(
            None, model_name, model_data, record_methods, record_getters
        )


class UtilityInterface(CRUDInterface):
    """Miscellaneous and specialized requests for creating, updating, etc."""

    __slots__ = ["aqhttp", "session"]

    ##############################
    # Create
    ##############################

    # TODO: have ability to save new properties
    def create_samples(self, samples):
        json_data = [s.dump(include=("field_values",)) for s in samples]

        updated_sample_data = self.aqhttp.post(
            "browser/create_samples", {"samples": json_data}
        )
        updated_samples = updated_sample_data["samples"]
        assert len(samples) == len(updated_samples)
        for s, data in zip(samples, updated_samples):
            s.reload(data)
        return samples

    def create_items(self, items):
        def sid(i):
            if i.sample_id:
                return i.sample_id
            return i.sample.id

        def otid(i):
            if i.object_type_id:
                return i.object_type_id
            return i.object_type.id

        return [
            self.aqhttp.get("items/make/{}/{}".format(sid(i), otid(i))) for i in items
        ]

    def update_operation_type(self, operation_type):
        """Creates a field type for an existing operation type"""
        op_data = operation_type.to_save_json()
        url = "operation_types/{}".format(operation_type.id)
        result = self.aqhttp.put(url, json_data=op_data)
        operation_type.reload(result)
        return operation_type

    def create_operation_type(self, operation_type):
        """Creates a new operation type."""
        op_data = operation_type.to_save_json()
        result = self.aqhttp.post("operation_types.json", json_data=op_data)
        operation_type.reload(result)
        return operation_type

    def create_library(self, library):
        """Creates a new library type."""
        op_data = library.dump(include={"source": {}})
        result = self.aqhttp.post("libraries.json", json_data=op_data)
        library.reload(result)
        return library

    def create_upload(self, upload):
        files = {"file": upload.file}
        result = self.aqhttp.post(
            "krill/upload?job={}".format(upload.job_id), files=files
        )
        upload.reload(result)
        return upload

    def create_data_association(self, model_inst, key, value, upload=None):
        upload_id = None
        if not model_inst.id:
            raise ValueError(
                "Cannot create DataAssociation because model has no id ("
                "it probably is not saved on the server)"
            )
        if upload is not None:
            upload_id = upload.id
        data = {
            "parent_id": model_inst.id,
            "key": str(key),
            "object": json.dumps({str(key): value}),
            "parent_class": model_inst.__class__.__name__,
            "upload_id": upload_id,
        }
        result = self.json_save("DataAssociation", data)

        data_association = model_inst.session.DataAssociation.find(result["id"])
        if data_association.id not in [da.id for da in model_inst.data_associations]:
            model_inst.data_associations.append(data_association)
            return data_association
        else:
            for da in model_inst.data_associations:
                if da.id == data_association.id:
                    return da

    ##############################
    # Save/Update
    ##############################

    def update_code(self, code):
        """Updates code for a operation_type."""
        controller = underscore(pluralize(code.parent_class))

        code_data = {"id": code.parent_id, "name": code.name, "content": code.content}
        result = self.aqhttp.post(url_build(controller, "code"), code_data)
        if "id" in result:
            code.id = result["id"]
            code.parent_id = result["parent_id"]
            code.updated_at = result["updated_at"]
        else:
            raise TridentRequestError(
                "Unable to update code object {}".format(code_data), result
            )

    ##############################
    # Misc
    ##############################

    def move_item(self, item, location):
        assert item.id
        url = "items/move/{item_id}?location={location}".format(
            item_id=item.id, location=location
        )
        result = self.aqhttp.get(url)
        if "error" in result or "errors" in result:
            raise TridentRequestError(str(result), result)
        item.location = location
        return item

    def store_item(self, item):
        assert item.id
        self.aqhttp.get("items/store/{item_id}")
        item.refresh()

    def estimate_plan_cost(self, plan):
        """Estimates the plan cost."""
        result = self.aqhttp.post("launcher/estimate", {"id": plan.id})
        total = 0
        for operation in plan.operations:
            for cost in result["costs"]:
                if cost["id"] == operation.id:
                    operation.cost = cost
                    total += (
                        cost["labor"] * cost["labor_rate"] + cost["materials"]
                    ) * cost["markup_rate"]
        return total

    def step_plan(self, plan_id):
        self.aqhttp.get("operations/step?plan_id={}".format(plan_id))
        return None

    def replan(self, plan_id):
        """Copies a plan."""
        result = self.aqhttp.get("plans/replan/{plan_id}".format(plan_id=plan_id))
        plan_copy = self.session.Plan.load(result)
        return plan_copy

    def start_job(self, job_id):
        result = self.aqhttp.get("krill/start?job={job_id}".format(job_id=job_id))
        return result

    def batch_operations(self, operation_ids):
        """Batches operations from a list of operation_ids."""
        self.aqhttp.post("operations/batch", json_data=operation_ids)

    def unbatch_operations(self, operation_ids):
        """Unbatches operations from a list of operation_ids."""
        self.aqhttp.post("operations/batch", json_data=operation_ids)

    def set_operation_status(self, operation_id, status):
        """Sets an operation's status."""
        msg = "operations/{oid}/status/{status}".format(oid=operation_id, status=status)
        self.aqhttp.get(msg)

    def job_debug(self, job_id):
        """Runs debug on a job with id=job_id."""
        self.aqhttp.get("krill/debug/{jid}".format(jid=job_id))

    def submit_plan(self, plan, user, budget):
        """Submits a plan."""
        user_query = "&user_id=" + str(user.id)
        budget_query = "?budget_id=" + str(budget.id)
        result = self.aqhttp.get(
            "plans/start/" + str(plan.id) + budget_query + user_query
        )
        return result

    def compatible_items(self, sample_id, object_type_id):
        """Find items compatible with the field value."""
        result = self.aqhttp.post(
            "json/items", {"sid": sample_id, "oid": object_type_id}
        )
        items = []
        for element in result:
            print(element)
        return items


class QueryInterfaceABC(ABC):
    """Interface that is used by models to find other models."""

    @abstractmethod
    def find(self, mid):
        pass

    @abstractmethod
    def find_by_name(self, name):
        pass

    @abstractmethod
    def all(self):
        pass

    @abstractmethod
    def where(self, query, **kwargs):
        pass

    @abstractmethod
    def first(self):
        pass

    @abstractmethod
    def last(self):
        pass

    @abstractmethod
    def one(self):
        pass

    @abstractmethod
    def model_name(self):
        """Alias for self.model.__name__"""
        pass


class QueryInterface(SessionInterface, QueryInterfaceABC):
    """Makes requests using AqHTTP that are model specific.

    Establishes a connection between a session object and an Aquarium
    model.
    """

    __slots__ = ["aqhttp", "session", "model", "__dict__"]
    MERGE = "query_hook"
    DEFAULT_OFFSET = -1
    DEFAULT_REVERSE = False
    DEFAULT_LIMIT = -1

    def __init__(self, model_name, aqhttp, session):
        """Instantiates a new model interface. Uses aqhttp to make requests,
        and deserializes response to models.

        :param model_name: Model name (e.g. 'Sample' or 'FieldValue')
        :type model_name: basestring
        :param aqhttp: the AqHTTP instance
        :type aqhttp: AqHTTP
        :param session:
        :type session:
        """
        super().__init__(aqhttp, session)
        self.crud = CRUDInterface(aqhttp, session)
        self.model = ModelRegistry.get_model(model_name)
        self._do_load = True

    @property
    def model_name(self):
        return self.model.__name__

    def _prepost_query_hook(self, query):
        """Method for modifying the query before posting."""

        additional_query = {}
        if hasattr(self.model, self.MERGE):
            additional_query = getattr(self.model, self.MERGE)

        # update and merge
        for k, v in additional_query.items():
            if k not in query:
                query[k] = v
            elif isinstance(query[k], list):
                if isinstance(v, list):
                    query[k] += v
                else:
                    query[k].append(v)
            elif isinstance(query[k], dict):
                if isinstance(v, dict):
                    query[k].update(v)
                else:
                    raise ValueError(
                        "Cannot update query {} with {}:{}".format(query, k, v)
                    )
        return query

    def _post_json(self, data):
        """Posts a json request to session for this interface.

        Attaches raw json and this session instance to the models it
        retrieves.
        """
        data_dict = {"model": self.model_name}
        data_dict = self._prepost_query_hook(data_dict)
        data_dict.update({k: v for k, v in data.items() if v})

        try:
            post_response = self.crud.json_post(self.model_name, data_dict)
        except TridentRequestError as err:
            if err.response.status_code == 422:
                return None
            else:
                raise err

        if post_response is not None and self._do_load:
            return self.load(post_response)
        return post_response

    def load(self, post_response):
        """Loads model instance(s) from data.

        Model instances will be of class defined by self.model. If data
        is a list, will return a list of model instances.
        """
        models = self.model.load_from(post_response, self.session)
        return models

    def get(self, path):
        """Makes a generic get request."""
        try:
            response = self.aqhttp.get(path)
        except TridentRequestError as err:
            if err.response.status_code == 404:
                return None
            raise err
        return self.load(response)

    def find(self, model_id, include=None, opts: dict = None):
        """Finds model by id."""
        if model_id is None:
            raise ValueError("model_id in 'find' cannot be None")
        if model_id == 0:
            return None
        return self._post_json({"id": model_id, "include": include, "options": opts})

    def find_by_name(self, name, include=None, opts: dict = None):
        """Finds model by name."""
        if name is None:
            raise ValueError("name in 'find_by_name' cannot be None")
        if name.strip() == "":
            return None
        return self._post_json(
            {
                "method": "find_by_name",
                "arguments": [name],
                "include": include,
                "options": opts,
            }
        )

    def array_query(self, method, args, rest=None, include=None, opts: dict = None):
        """Finds models based on a query."""
        if opts is None:
            opts = {}
        options = {
            "offset": self.DEFAULT_OFFSET,
            "limit": self.DEFAULT_LIMIT,
            "reverse": self.DEFAULT_REVERSE,
        }
        options.update(opts)
        if options.get("limit", None) == 0:
            return []
        if args is None:
            args = []
        query = {
            "model": self.model.__name__,
            "method": method,
            "arguments": args,
            "include": include,
            "options": options,
        }
        if rest:
            query.update(rest)
        res = self._post_json(query)
        if res is None:
            return []
        return res

    def all(self, methods: List[str] = None, include=None, opts: dict = None):
        """Finds all models.

        :param methods:
        :param include:
        :type include:
        :param opts: additional options ("offset", "limit", "reverse", etc.)
        :type opts: dict
        :return:
        :rtype:
        """

        if opts is None:
            opts = {}
        addopts = opts.pop("opts", dict())
        opts.update(addopts)
        options = {"offset": self.DEFAULT_OFFSET, "reverse": self.DEFAULT_REVERSE}
        options.update(opts)
        return self.array_query(
            method="all", args=None, rest=None, include=include, opts=options
        )

    def where(
        self,
        criteria: dict,
        methods: List[str] = None,
        include: List[str] = None,
        page_size: int = None,
        opts: dict = None,
    ):
        """Performs a query for models.

        :param criteria: query to find models
        :type criteria: dict
        :param methods: server side methods to implement
        :type methods: list
        :param opts: additional options ("offset", "limit", "reverse", etc.)
        :type opts: dict
        :param include:
        :return: list of models
        :rtype: list
        """
        if page_size is not None:
            results = []
            for page in self.pagination(
                criteria,
                page_size=page_size,
                methods=methods,
                include=include,
                opts=opts,
            ):
                results += page
            return results
        if opts is None:
            opts = dict()
        rest = {}
        if methods is not None:
            rest = {"methods": methods}
        return self.array_query(
            method="where", args=criteria, rest=rest, include=include, opts=opts
        )

    # TODO: Refactor 'last' so query is an argument, not part of kwargs
    def last(
        self, num: int = None, query: dict = None, include=None, opts: dict = None
    ):
        """Find the last added models.

        :param num: number of models to return. If not provided, assumes 1
        :type num: int
        :param query: additional query to find models
        :type query: dict
        :param opts: additional options ("offset", "limit", "reverse", etc.)
        :type opts: dict
        :return: list of models
        :rtype: list
        """
        if query is None:
            query = dict()
        if num is None:
            num = 1
        if opts is None:
            opts = dict()
        opts.update(dict(limit=num, reverse=True))
        return self.where(query, include=include, opts=opts)

    # TODO: Refactor 'first' so query is an argument, not part of kwargs
    def first(
        self, num: int = None, query: dict = None, include=None, opts: dict = None
    ):
        """Find the first added models.

        :param num: number of models to return. If not provided, assumes 1
        :type num: int
        :param query: additional query to find models
        :type query: dict
        :param include:
        :param opts: additional options ("offset", "limit", "reverse", etc.)
        :type opts: dict
        :return: list of models
        :rtype: list
        """
        if query is None:
            query = dict()
        if num is None:
            num = 1
        if opts is None:
            opts = dict()
        opts.update(dict(limit=num, reverse=False))
        return self.where(query, include=include, opts=opts)

    # TODO: Refactor 'one' so query is an argument, not part of kwargs
    def one(
        self, query: dict = None, first: bool = False, include=None, opts: dict = None
    ):
        """Return one model. Returns the last model by default. Returns None if
        no model is found.

        :param first: whether to return the first model (default: False
        :type first: bool
        :return: model
        :rtype: ModelBase
        """
        if not first:
            res = self.last(1, query=query, include=include, opts=opts)
        else:
            res = self.first(1, query=query, include=include, opts=opts)
        if not res:
            return None
        else:
            return res[0]

    # TODO: implement 'patch' or 'update'? Would this be too dangerous?
    # def patch(self, model_id, json_data):
    #     """
    #     Makes a patch or update from json_data
    #     """
    #     models_name = pluralize(underscore(self.model_name))
    #     result = self.aqhttp.put('{models}/{model_id}'.format(
    #         model_id=model_id, models=models_name), json_data=json_data)
    #     return result

    def pagination(
        self,
        query: dict,
        page_size: int,
        methods: List[str] = None,
        include: List[str] = None,
        opts: dict = None,
    ) -> Generator[list, None, None]:
        """Return pagination query (as a generator).

        :param interface: SessionInterface
        :param query: query
        :param page_size: number of models to return per page
        :param limit: total number of models to return
        :param opts: additional options
        :return: generator of list of models
        """
        if opts is None:
            opts = {}
        limit = opts.get("limit", -1)
        if limit < page_size and limit >= 0:
            page_size = limit
        n = 0
        if opts:
            _opts = dict(opts)
        else:
            _opts = {}
        while n < limit or limit == -1:
            _opts["limit"] = page_size
            _opts["offset"] = n
            models = self.where(query, methods=methods, include=include, opts=_opts)
            if not models:
                return
            n += len(models)
            yield models

    def new(self, *args, **kwargs):
        """Creates a new model instance.

        Attach a session by calling __new__ with session kwargs.
        """
        instance = self.model.__new__(self.model, *args, session=self.session, **kwargs)
        self.model.__init__(instance, *args, **kwargs)
        return instance

    def __call__(self, *args, **kwargs):
        return self.new(*args, **kwargs)


class BrowserInterface(SessionInterface, QueryInterfaceABC):
    __slots__ = ["aqhttp", "session", "model", "__dict__"]
    MERGE = ["methods"]
    DEFAULT_OFFSET = -1
    DEFAULT_REVERSE = False
    DEFAULT_LIMIT = -1

    # TODO: browser should use standard session
    def __init__(self, model_name, aqhttp, session):
        super().__init__(aqhttp, session)
        self.crud = CRUDInterface(aqhttp, session)
        self.model = ModelRegistry.get_model(model_name)
        self._do_load = True
        self._preload_field_values = None

    @property
    def model_name(self):
        return self.model.__name__

    @property
    def browser(self):
        return self.session.browser

    def find(self, model_id):
        return self.browser.find(model_id, model_class=self.model_name)

    def find_by_name(self, name):
        return self.browser.find_by_name(
            name, model_class=self.model_name, primary_key="name"
        )

    def where(
        self,
        criteria,
        methods: List[str] = None,
        page_size: int = None,
        opts: dict = None,
    ):
        return self.browser.where(
            criteria,
            model_class=self.model_name,
            methods=methods,
            opts=opts,
            page_size=page_size,
        )

    def one(self, query: dict = None, first: bool = False, opts: dict = None):
        return self.browser.one(model_class=self.model_name, query=query, opts=opts)

    def first(self, num: int = 1, query: dict = None, opts: dict = None):
        return self.browser.first(num, model_class=self.model_name, query=query)

    def last(self, num: int = 1, query: dict = None, opts: dict = None):
        return self.browser.last(num, model_class=self.model_name, query=query)

    def new(self, *args, **kwargs):
        instance = self.model.__new__(self.model, *args, session=self.session, **kwargs)
        self.model.__init__(instance, *args, **kwargs)
        self.browser.update_cache([instance])
        return instance

    def all(self, opts: dict = None):
        return self.browser.all(model_class=self.model_name, opts=opts)

    # TODO: load_from using new session
    def load(self, post_response: dict) -> List[SchemaModel]:
        """Loads model instance(s) from data.

        Model instances will be of class defined by self.model. If data
        is a list, will return a list of model instances.
        """
        models = self.model.load_from(post_response, self.session)
        return models
