"""
Browser (:mod:`pydent.browser`)
=================================

.. versionadded:: 0.1
    Browser class created

.. currentmodule:: pydent.browser

Browser class for searching and cacheing results.
"""
import re
from collections import OrderedDict
from difflib import get_close_matches
from pprint import pformat
from typing import Callable
from typing import Dict
from typing import List
from typing import Union

import networkx as nx

from pydent import models as pydent_models
from pydent.base import ModelBase
from pydent.exceptions import ForbiddenRequestError
from pydent.exceptions import TridentBaseException
from pydent.interfaces import QueryInterface
from pydent.interfaces import QueryInterfaceABC
from pydent.marshaller import ModelRegistry
from pydent.models import Sample
from pydent.relationships import BaseRelationship
from pydent.sessionabc import SessionABC
from pydent.utils import logger
from pydent.utils.logging_helpers import did_you_mean

# TODO: browser documentation
# TODO: examples in sphinx
# TODO: methods to help pull relevant data from plans (user specifies types of data to
#       pull, and trident should pull and cache in the most efficient way possible)


class BrowserException(TridentBaseException):
    """Generic browser exception."""


class Browser(QueryInterfaceABC):
    """A class for browsing models and Aquarium inventory."""

    # TODO: ability to block model callbacks to enforce cache

    INTERFACE_CLASS = QueryInterface
    ACCEPTED_GET_RELATION_TYPES = [
        "HasOne",
        "HasMany",
        "HasManyThrough",
        "HasManyGeneric",
    ]

    def __init__(self, session: SessionABC, inherit_models: bool = False):
        """Instantiates a new browser from a AqSession instance.

        .. versionchanged:: 0.1.5a7
            'inherit_models' argument will inherit the sessions model_cache
            (default: False)

        :param session: a session instance
        :param inherit_models: if True, the browser will inherit the cache in the
            provided session's browser model_cache
        :type session: SessionABC
        """
        self.session = session
        self._list_models_fxn = self.sample_list
        self.use_cache = True
        self.model = Sample
        self.model_list_cache = {}
        self.model_cache = {}
        self.log = logger(name="Browser@{}".format(session.url))
        if session.browser and inherit_models:
            self.update_cache(session.browser.models)

    @property
    def model_name(self):
        return self.model.__name__

    # TODO: change session interface (find, where, etc.) to use cache IF use_
    #       cache = True
    # TODO: where and find queries can sort through models much more quickly than
    #       Aquarium, but can fallback to Aq

    @property
    def models(self):
        models = []
        for v in self.model_cache.values():
            models += list(v.values())
        return models

    def set_model(self, model_name):
        """Sets the default model of this browser."""
        self.model = ModelRegistry.get_model(model_name)
        if model_name == "Sample":
            self._list_models_fxn = self.sample_list
        else:
            self._list_models_fxn = self._generic_list_models

    def interface(self, model_class=None):
        """Returns a new model query interface.

        :param model_class:
        :type model_class: basestring
        :return: Interface
        :rtype: QueryInterface
        """
        if model_class is None:
            model_class = self.model_name
        return self.session.model_interface(
            model_class, interface_class=self.INTERFACE_CLASS
        )

    def _generic_list_models(self, **query):
        models = self.where(query, self.model_name)
        return ["{}: {}".format(m.id, m.name) for m in models]

    def sample_list(self, sample_type_id=None):
        """Returns a sample list."""
        path = "sample_list"
        if sample_type_id is not None:
            path += "/" + str(sample_type_id)
        return self.session.utils.aqhttp.get(path)

    def clear(self):
        """Clears the model cache."""
        self.model_list_cache = {}
        self.model_cache = {}

    def list_models(self, *args, **kwargs):
        def get_models():
            return self._list_models_fxn(*args, **kwargs)

        if self.use_cache:
            models_cache = self.model_list_cache.get("models", {})
            if self.model_name in models_cache:
                model_list = models_cache[self.model_name]
            else:
                model_list = get_models()
        else:
            model_list = get_models()
        self.model_list_cache.setdefault("models", {})
        self.model_list_cache["models"][self.model_name] = model_list[:]
        return model_list

    def where(
        self,
        query,
        model_class=None,
        primary_key="id",
        sample_type=None,
        methods=None,
        opts: Dict = None,
        page_size: int = None,
        include: Dict = None,
    ):
        """Perform a 'where' query. If models are found in the browser cache,
        those are returned, else new http queries are made to find the models.

        :param query: query as a dictionary
        :param model_class: model class to use (str)
        :param primary_key: which primary key to use (default: 'id')
        :param sample_type: optional sample_type short cut for finding samples
        :param kwargs: other kwargs
        :return: returned model list
        """
        if model_class is None:
            model_class = self.model_name
        if sample_type is not None:
            sample_type_id = self.find_by_name(sample_type, "SampleType").id
            query.update({"sample_type_id": sample_type_id})
        if self.use_cache and not methods and page_size is None:
            return self.cached_where(
                query,
                model_class,
                primary_key=primary_key,
                include=include,
                methods=methods,
                opts=opts,
            )
        else:
            return self.server_where(
                query,
                model_class,
                opts=opts,
                include=include,
                methods=methods,
                page_size=page_size,
            )

    def __query_helper(
        self,
        fname,
        query,
        model_class,
        sample_type=None,
        opts=None,
        params=None,
        as_single=False,
    ):
        """Builds a custom query for the browser.

        :param fname: the function name
        :type fname: basestring
        :param query: the query
        :type query: dict
        :param model_class: the name of the model class (e.g. "Sample")
        :type model_class: basestring
        :param sample_type: optional sample_type name
        :type sample_type: basestring
        :param opts: options to send to the function
        :type opts: dict
        :param params: additionaly keyword arguments to send to the function
        :type params: dict
        :param as_single: if True, will return the first model of the array or None if
            array is empty
        :type as_single: bool
        :return: Aquarium model or list of Aquarium models
        :rtype: ModelBase | list
        """
        if model_class is None:
            model_class = self.model_name
        if query is None:
            query = dict()
        if params is None:
            params = dict()
        if sample_type is not None:
            query.update(
                {"sample_type_id": self.find_by_name(sample_type, "SampleType").id}
            )
        interface = self.interface(model_class)
        fxn = getattr(interface, fname)
        if fname == "all":
            models = fxn(opts=opts, **params)
        else:
            models = fxn(query=query, opts=opts, **params)
        if as_single:
            models = [models]
        return self.update_cache(models).get(model_class, [])

    def one(self, model_class=None, sample_type=None, query=None, opts=None):
        """Finds one instance of a model (or returns None)

        :param model_class: the name of the model class (e.g. "Sample")
        :type model_class: basestring
        :param sample_type: optional sample_type name
        :type sample_type: basestring
        :param query: additional query to filter models
        :type query: dict
        :param opts: additional options
        :type opts: dict
        :return:
        :rtype:
        """
        models = self.__query_helper(
            "one", query, model_class, sample_type, opts=opts, as_single=True
        )
        if not models:
            return None
        return models[0]

    def last(self, num=1, model_class=None, sample_type=None, query=None):
        """Finds last models. Will NOT return cached models.

        :param num: number of models to return
        :type num: int
        :param model_class: the name of the model class (e.g. "Sample")
        :type model_class: basestring
        :param sample_type: optional sample_type name
        :type sample_type: basestring
        :param query: additional query to filter models
        :type query: dict
        :return:
        :rtype:
        """
        return self.__query_helper(
            "last", query, model_class, sample_type, params=dict(num=num)
        )

    def first(self, num=1, model_class=None, sample_type=None, query=None):
        """Finds first models. Will NOT return cached models.

        :param num: number of models to return
        :type num: int
        :param model_class: the name of the model class (e.g. "Sample")
        :type model_class: basestring
        :param sample_type: optional sample_type name
        :type sample_type: basestring
        :param query: additional query to filter models
        :type query: dict
        :return:
        :rtype:
        """
        return self.__query_helper(
            "first", query, model_class, sample_type, params=dict(num=num)
        )

    def find(self, model_id, model_class=None):
        """Finds a model by id. Will returned cached model if possible.

        :param model_id: model_id
        :type model_id: int
        :param model_class: the name of the model class (e.g. "Sample")
        :type model_class: basestring
        :return:
        :rtype:
        """
        if model_class is None:
            model_class = self.model_name
        if self.use_cache:
            return self.cached_find(model_class, model_id)
        return self.interface(model_class).find(model_id)

    def find_by_name(self, name, model_class=None, primary_key="id"):
        """Find model by name. Will return cached model if possible.

        :param name: name of the model
        :param model_class: the name of the model class (e.g. "Sample")
        :type model_class: basestring
        :param primary_key:
        :return:
        """
        models = self.where({"name": name}, model_class, primary_key=primary_key)
        if not models:
            return None
        return models[0]

    def all(self, model_class=None, opts=None):
        """Return all models of a model_class.

        :param model_class: the name of the model class (e.g. "Sample")
        :type model_class: basestring
        :param opts:
        :type opts:
        :return:
        :rtype:
        """
        return self.__query_helper("all", query={}, model_class=model_class, opts=opts)

    @staticmethod
    def _match_query(query, model_dict):
        """Matches a query against a model dictionary.

        :param query: query dictionary
        :type query: dict
        :param model_dict: model dictionary (e.g. model.__dict__)
        :type model_dict: dict
        :return: whether the model matches the query
        :rtype: bool
        """
        for query_key in query:
            if query_key not in model_dict:
                return False
            query_val = query[query_key]
            model_val = model_dict[query_key]
            if isinstance(query_val, list):
                if model_val not in query_val:
                    return False
            elif model_val != query_val:
                return False
        return {k: model_dict[k] for k in query}

    @classmethod
    def _find_matches(cls, query, models):
        found = []
        found_queries = []
        for m in models:
            match = cls._match_query(query, m._get_data())
            if match:
                found.append(m)
                found_queries.append(match)
        return found, found_queries

    def update_cache(
        self,
        models: List[ModelBase],
        recursive: bool = True,
        update_session: bool = False,
    ) -> Dict[str, List[ModelBase]]:
        """Update the browser's model cache from a list of models.

        .. versionchanged:: 0.1.5a8
            Added 'update_session' kwarg which will change the model's
            session to the browser's session.

        .. warning::
            If `update_session=True`, the model's session
            will change and this may have unintended consequences.

        :param models: list of models
        :param recursive: if True, recursively collect all models contained in
            the relationships and use those to update the cache as well.
        :param update_session: if True, attach the browser's session to the models
        :return: the updated dictionary broken down by model class name
        """
        assert isinstance(models, list)
        if recursive:
            memo = {}
            ModelBase._flatten_deserialized_data(models, memo)
            models = list(memo.values())
        if update_session:
            for m in models:
                m._session = self.session
        return self._group_models_and_update_cache(models)

    # TODO: do we really want to simply overwrite the dictionary or update the models?
    def _update_model_cache_helper(
        self, modelname: str, modeldict: Dict
    ) -> List[ModelBase]:
        """Updates the browser's model cache with models from the provided
        model dict."""
        self.log.info(
            "CACHE updated cached with {} {} models".format(len(modeldict), modelname)
        )
        self.model_cache.setdefault(modelname, {})

        model_cache_dict = self.model_cache[modelname]
        for mid in modeldict:
            model = modeldict[mid]
            if mid in model_cache_dict:
                cached_model = model_cache_dict[mid]
                vars(cached_model).update(vars(model))
            else:
                model_cache_dict[mid] = model
        return [model_cache_dict[mid] for mid in modeldict]

    def _group_models_and_update_cache(self, models):
        grouped_by_type = {}
        for model in models:
            classname = model.__class__.__name__
            arr = grouped_by_type.setdefault(classname, [])
            if model is not None:
                arr.append(model)

        result = {}
        for clstype in grouped_by_type:
            result[clstype] = self._update_model_cache_helper(
                clstype, {m._primary_key: m for m in grouped_by_type[clstype]}
            )
        return result

    # TODO: support unsaved models as well
    def cached_find(self, model_class, id):
        if isinstance(id, list):
            return self.cached_where({"id": id}, model_class)
        cached_models = self.model_cache.get(model_class, {})
        found_model = cached_models.get(id, None)
        if found_model is None:
            found_model = self.interface(model_class).find(id)
        else:
            self.log.info(
                "CACHE found {} model with id={} in cache".format(model_class, id)
            )
        if found_model is None:
            return None
        return self._update_model_cache_helper(
            model_class, {found_model.id: found_model}
        )[0]

    def server_where(self, query, model, opts, include, methods, page_size):
        return self.interface(model).where(
            query, opts=opts, methods=methods, include=include, page_size=page_size
        )

    def cached_where(
        self,
        query,
        model,
        primary_key="id",
        methods: Dict = None,
        include: Dict = None,
        opts: Dict = None,
    ):
        if isinstance(query, str):
            server_models = self.server_where(
                query,
                model,
                opts=opts,
                methods=methods,
                include=include,
                page_size=None,
            )
            found_dict = {}
        elif [] in query.values():
            return []
        else:
            cached_models = self.model_cache.get(model, {})
            found, found_queries = self._find_matches(
                query, list(cached_models.values())
            )
            found_dict = {f.id: f for f in found}

            # TODO: this code is broken, remaining query
            remaining_query = dict(query)
            if primary_key in query:
                found_ids = [q[primary_key] for q in found_queries]
                query_id_list = query[primary_key]
                if isinstance(query_id_list, str) or isinstance(query_id_list, int):
                    query_id_list = [query_id_list]
                remaining_ids = list(set(query_id_list).difference(set(found_ids)))
                remaining_query[primary_key] = remaining_ids
            self.log.info(
                "CACHE found {num} {model} models in cache using query {query}".format(
                    num=len(found_dict), model=model, query=self.log.pprint_data(query)
                )
            )

            # TODO: this code may be sketchy... here {'id': []}, really means we found
            #       all of the models..
            if primary_key in remaining_query and not remaining_query[primary_key]:
                return list(found_dict.values())
            server_models = self.interface(model).where(remaining_query, opts=opts)

        models_dict = OrderedDict({s.id: s for s in server_models})
        models_dict.update(found_dict)

        returned = self._update_model_cache_helper(model, models_dict)
        if opts:
            if opts.get("reverse", True) is False:
                returned = returned[::-1]
            if opts.get("limit", None):
                returned = returned[-opts["limit"] :]
        return returned

    def _search_helper(self, pattern, filter_fxn, sample_type=None, **query):
        sample_type_id = None
        if sample_type is not None:
            if isinstance(sample_type, pydent_models.SampleType):
                sample_type_id = sample_type.id
            else:
                sample_type_id = self.find_by_name(sample_type, "SampleType").id

        if sample_type_id is not None:
            query.update({"sample_type_id": sample_type_id})

        model_list = self.list_models()
        self.log.info(
            "SEARCH found {} total models of type {}".format(
                len(model_list), self.model_name
            )
        )
        matches = filter_fxn(pattern, model_list)

        if not matches:
            return []

        if query:
            query.update({"id": matches})
            filtered = self.where(query, self.model_name)
        else:
            filtered = self.interface().find(matches)
        self.log.info(
            "SEARCH filtered to {} total models of type {}".format(
                len(filtered), self.model_name
            )
        )

        if self.use_cache:
            self.update_cache(filtered)
        return filtered

    def search(self, pattern, ignore_case=True, sample_type=None, **query):
        """Performs a regular expression search of Samples.

        :param pattern: regular expression pattern
        :type pattern: basestring
        :param ignore_case: whether to ignore case for regex search (default: True)
        :type ignore_case: bool
        :param sample_type: sample_type_name to filter samples (optional)
        :type sample_type: basestring
        :param query: additional query parameters to filter by
        :type query: dict
        :return: list of samples
        :rtype: list
        """

        def regex_filter(pattern, sample_list):
            matches = []
            for name in sample_list:
                args = []
                if ignore_case:
                    args.append(re.IGNORECASE)
                m = re.search(pattern, name, *args)
                if m is not None:
                    matches.append(name)
            return matches

        return self._search_helper(
            pattern, regex_filter, sample_type=sample_type, **query
        )

    def search_description(
        self, pattern, samples=None, sample_type=None, ignore_case=True
    ):
        """Search samples by their description.

        :param pattern: regex pattern
        :type pattern: basestring
        :param samples: samples to search. If left blank, a search to find samples will
            be performed
        :type samples: list
        :param sample_type: restrict to a particular sample type
        :type sample_type: name
        :param ignore_case: ignore case for regular pattern search (default True)
        :type ignore_case: bool
        :return: list of samples
        :rtype: list
        """
        matches = []
        args = []
        if samples is None:
            samples = self.search(".*", sample_type=sample_type)
        if ignore_case:
            args.append(re.IGNORECASE)
        for sample in samples:
            description = sample.description
            if description is None:
                continue
            if re.search(pattern, sample.description, *args):
                matches.append(sample)
        return matches

    def close_matches(self, pattern, sample_type=None, **query):
        """Finds samples whose names closely match the pattern.

        :param pattern: regular expression pattern
        :type pattern: basestring
        :param sample_type: sample_type_name to filter samples (optional)
        :type sample_type: basestring
        :param query: additional query parameters to filter by
        :type query: dict
        :return: list of samples
        :rtype: list
        """
        return self._search_helper(
            pattern, get_close_matches, sample_type=sample_type, **query
        )

    def list_field_values(self, model_ids, **query):
        """Lists sample field values.

        May supply an additional query to filter :class:`FieldValue`.
        """
        query.update({"parent_class": self.model_name, "parent_id": model_ids})
        return self.where(query, "FieldValue")

    @staticmethod
    def _group_by_attribute(models, attribute):
        """Group models by the given attribute."""
        d = {}
        for s in models:
            arr = d.setdefault(getattr(s, attribute), [])
            arr.append(s)
        return d

    def new_sample(self, sample_type, name, description, project, properties=None):
        st = self.find_by_name(sample_type, "SampleType", primary_key="name")
        if st._get_deserialized_data().get("field_types", None) is None:
            fts = self.where(
                {"parent_class": "SampleType", "parent_id": st.id}, "FieldType"
            )
            st.field_types = fts
        return st.new_sample(name, description, project, properties=properties)

    # TODO: handle not-yet existant samples using rid
    def _retrieve_has_many_or_has_one(
        self, models, relationship_name, relation=None, strict=True
    ):
        """Performs exactly 1 query to fullfill some relationship for a list of
        models."""
        if not models:
            return []
        models = models[:]
        if relation is None:
            relation = models[0].get_relationships()[relationship_name]

        ref = relation.ref  # sample_id
        attr = relation.attr  # id
        model_class2 = relation.nested

        # todo: collect existing fullfilled relationship
        # todo: partition, then collect callback
        # todo: how to handle when model_attr is absent?, or just raise error?

        retrieve_query = relation.build_query(models)
        retrieved_models = self.where(retrieve_query, model_class2)
        self.log.info(
            "RETRIEVE retrieved {num} {cls} models using query {query}".format(
                num=len(retrieved_models),
                cls=model_class2,
                query=self.log.pprint_data(retrieve_query),
            )
        )

        if not retrieved_models:
            return []

        if relation.QUERY_TYPE == "query":
            model_dict = {m1.id: list() for m1 in models}
            for model in retrieved_models:
                model_ref = getattr(model, ref)
                if model_ref is not None:
                    if not strict:
                        model_dict.setdefault(model_ref, []).append(model)
                    else:
                        model_dict[model_ref].append(model)
                else:
                    self.log.error(
                        "RETRIEVE ref: {ref} {model_ref}, attr: {attr}".format(
                            ref=ref, attr=attr, model_ref=model_ref
                        )
                    )
        elif relation.QUERY_TYPE == "by_id":
            retrieved_dict = {getattr(m2, attr): m2 for m2 in retrieved_models}
            model_dict = {m1.id: None for m1 in models}
            missing_models = []
            for model in models:
                model_attr = getattr(model, attr)
                model_ref = getattr(model, ref)
                if model_ref is not None:
                    if model_attr is not None:
                        if model_ref not in retrieved_dict:
                            self.log.info(strict)
                        else:
                            model_dict[model_attr] = retrieved_dict[model_ref]
                    else:
                        self.log.error(
                            "attr: {attr}={model_attr}, ref: {ref}={model_ref}".format(
                                ref=ref,
                                attr=attr,
                                model_attr=model_attr,
                                model_ref=model_ref,
                            )
                        )
                    if model_ref not in retrieved_dict:
                        missing_models.append(model_ref)
            if missing_models:
                self.log.error(
                    "INCONSISTENT AQUARIUM DATABASE - There where {models} missing {cls} "
                    "models "
                    "from the Aquarium database, which were ignored by trident. "
                    "This happens when models are deleted from Aquarium which "
                    "results in an inconsistent server database. Trident was unable "
                    "resolve the following relationships which returned no models "
                    "from the server: "
                    "{cls}.where({attr}={missing})".format(
                        models=len(missing_models),
                        cls=model_class2,
                        missing=missing_models,
                        attr=attr,
                    )
                )
        else:
            raise BrowserException(
                "QUERY_TYPE '{}' for relation '{}' not recognized.".format(
                    relation.QUERY_TYPE, relationship_name
                )
            )
        for model in models:
            found_models = model_dict[getattr(model, attr)]
            setattr(model, relationship_name, found_models)

        return retrieved_models

    def _retrieve_has_many_through(
        self, models: List[ModelBase], relationship_name: str, strict: bool = True
    ):
        """Performs exactly 2 queries to establish a HasManyThrough
        relationship."""
        relation = models[0].get_relationships()[relationship_name]
        association_relation = models[0].get_relationships()[
            relation.through_model_attr
        ]
        attr = relation.attr
        ref = association_relation.ref

        # find other key
        association_class = ModelRegistry.get_model(association_relation.nested)
        association_relationships = association_class.get_relationships()
        other_ref = None
        for r in association_relationships:
            ar = association_relationships[r]
            if ar.nested == relation.nested:
                other_ref = r

        associations = self._retrieve_has_many_or_has_one(
            models, relation.through_model_attr, strict=strict
        )
        self._retrieve_has_many_or_has_one(associations, other_ref, strict=strict)

        associations_by_mid = {}
        for a in associations:
            associations_by_mid.setdefault(getattr(a, ref), []).append(a)

        all_models = []
        for m in models:
            mid = getattr(m, attr)
            if mid in associations_by_mid:
                associations = associations_by_mid[mid]
                _models = [getattr(a, other_ref) for a in associations]
                setattr(m, relationship_name, _models)
                all_models += _models
            else:
                setattr(m, relationship_name, None)
        return list(set(all_models))

    @staticmethod
    def _get_relation_from_model(model, relationship_name, strict):
        relationships = model.get_relationships()
        relation = relationships.get(relationship_name, None)
        if relation is None:
            if strict:
                msg = did_you_mean(relationship_name, list(relationships))
                if not msg:
                    msg = "Available relations: {}".format(pformat(list(relationships)))
                raise BrowserException(
                    "Relation '{}' not found in relationships for {}.\nHint: {}".format(
                        relationship_name, type(model), msg
                    )
                )
        return relation

    def retrieve(
        self,
        models: List[ModelBase],
        relationship_name: str,
        relation: BaseRelationship = None,
        strict: bool = True,
        force_refresh: bool = False,
    ) -> List[ModelBase]:
        """Retrieves a model relationship for the list of models. Compared to a
        `for` loop, `retrieve` is >10X faster for most queries.

        .. code-block:: python

            # FAST code example
            samples = browser.search(".*mCherry.*")
            items = browser.retrieve(samples, 'items')
            for s in samples:
                sample_items = s.items
                # do something with items


        .. code-block:: python

            # very SLOW code example. DO NOT USE.
            samples = browser.search(".*mCherry.*")
            for s in samples:
                sample_items = s.items
                # do something with itmes


        :param models: list of models to retrieve the attribute
        :type models: list
        :param relationship_name: name of the attribute to retrieve
        :type relationship_name: basestring
        :param relation: the relation to retrieve (operational)
        :type relation: pydent.relationships.Relation
        :param strict: wither to ignore database inconsistencies
        :type strict: bool
        :return: list of models retrieved
        :rtype: list
        """
        if not models:
            return []
        self.log.info('RETRIEVE retrieving "{}"'.format(relationship_name))
        model_classes = {m.__class__.__name__ for m in models}
        assert (
            len(model_classes) == 1
        ), "Models must be all of the same BaseModel, but found {}".format(
            model_classes
        )
        if relation is None:
            relation = self._get_relation_from_model(
                models[0], relationship_name, strict
            )
            if relation is None:
                return []
        else:
            if relationship_name in models[0].get_relationships():
                raise BrowserException(
                    'Cannot add new relationship "{}" because it already exists in the '
                    "model definition".format(relationship_name)
                )
        # TODO: add relationship handler for Many and One
        if relation.__class__.__name__ not in self.ACCEPTED_GET_RELATION_TYPES:
            raise BrowserException(
                'retrieve is not supported for the "{}" relationship'.format(
                    relation.__class__.__name__
                )
            )
        self.log.info("RETRIEVE {}: {}".format(relationship_name, relation))

        if not force_refresh:
            needs_refresh = [
                m for m in models if not m.is_deserialized(relationship_name)
            ]
            no_refresh = [m for m in models if m.is_deserialized(relationship_name)]
        else:
            needs_refresh = models
            no_refresh = []

        if needs_refresh:
            if hasattr(relation, "through_model_attr"):
                found_models = self._retrieve_has_many_through(
                    needs_refresh, relationship_name, strict=strict
                )
            else:
                found_models = self._retrieve_has_many_or_has_one(
                    needs_refresh, relationship_name, relation, strict=strict
                )
        else:
            found_models = []

        self.log.info(
            'RETRIEVE retrieved {} for "{}"'.format(
                len(found_models), relationship_name
            )
        )
        for model in no_refresh:
            val = getattr(model, relationship_name)
            if isinstance(val, list):
                found_models += val
            else:
                found_models.append(val)
        return list(set(found_models))

    def recursive_retrieve(
        self,
        models: List[ModelBase],
        relations: Union[str, List[BaseRelationship], Dict],
        strict: bool = True,
        force_refresh: bool = False,
    ):
        """Efficiently retrieve a model relationship recursively from an
        iterable. The relations_dict iterable may be either a list or a
        dictionary. For example, the following will collect all of the
        field_values and their incoming and outgoing wires, the connecting
        field_values, and finally those FieldValues' operations.

        .. code-block::

            relation_dict = {
                "field_values": {
                    "wires_as_dest": {
                        "source": "operation",
                        "destination": "operation"
                    },
                    "wires_as_source": {
                        "source": "operation",
                        "destination": "operation"
                    },
                }
            }
            browser.retrieve(operations, relation_dict)


        :param models: models to retrieve from
        :type models: list
        :param relations: the relation to retrieve. May be a string (by \
            attribute name), a list, or a dict.
        :type relations: list|dict|basestring
        :param strict: wither to ignore database inconsistencies
        :param force_refresh:
        :type force_refresh: bool
        :return: dictionary of all models retrieved grouped by the attribute \
            name that retrieved them.
        :rtype: dictionary
        """
        self.log.info("RETRIEVE recursively retrieving {}".format(relations))
        if isinstance(relations, str):
            self.log.info('RETRIEVE retrieving "{}"'.format(relations))
            return {
                relations: self.retrieve(
                    models, relations, strict=strict, force_refresh=force_refresh
                )
            }
        elif (
            isinstance(relations, list)
            or isinstance(relations, set)
            or isinstance(relations, dict)
            or isinstance(relations, tuple)
        ):
            models_by_attr = {}
            for relation_name in relations:
                models_by_attr.setdefault(relation_name, [])
                new_models = self.retrieve(
                    models, relation_name, strict=strict, force_refresh=force_refresh
                )
                models_by_attr[relation_name] += new_models
                if isinstance(relations, dict):
                    _models_by_attr = self.recursive_retrieve(
                        new_models,
                        dict(relations).pop(relation_name),
                        strict=strict,
                        force_refresh=force_refresh,
                    )
                    for attr in _models_by_attr:
                        _models = _models_by_attr[attr]
                        if attr in models_by_attr:
                            models_by_attr[attr] += _models
                        else:
                            models_by_attr[attr] = _models_by_attr[attr]
            return models_by_attr
        elif not strict:
            return []
        else:
            raise BrowserException(
                "Type {} for is not recognized for recursive_retrieve".format(
                    type(relations)
                )
            )

    @classmethod
    def sample_network(
        cls,
        samples: List[Sample],
        reverse: bool = False,
        g: nx.DiGraph = None,
        get_models: Callable = None,
        cache_func: Callable = None,
        key_func: Callable = None,
    ) -> nx.DiGraph:
        """Build a DAG of :class:`Samples <pydent.models.Sample>` from their.

        :class:`FieldValues <pydent.models.FieldValue>`.

        .. versionadded:: 0.1.5a7
            method added

        .. versionchanged:: 0.1.5a16
            added optional get_models, cache_func, key_func arguments

        :param samples: list of samples
        :param reverse: whether to reverse the edges of the final graph
        :param g: the graph
        :return:
        """

        if not get_models:

            def get_models(model):
                for fv in model.field_values:
                    if fv.sample and issubclass(type(fv.sample), ModelBase):
                        yield fv.sample, {"field_value_name": fv.name}

        if not cache_func:

            def cache_func(models):
                sess = models[0].session
                sess.browser.get(models, {"field_values": "sample"})

        return cls.relationship_network(
            samples,
            get_models=get_models,
            cache_func=cache_func,
            reverse=reverse,
            g=g,
            key_func=key_func,
        )

    @classmethod
    def relationship_network(
        cls,
        models: List[ModelBase],
        get_models: Callable,
        cache_func: Callable = None,
        key_func: Callable = None,
        reverse: bool = False,
        g: nx.DiGraph = None,
        strict_cache: bool = True,
    ):
        """Build a DAG of related models based on some relationships. By
        default are built from a model using (model.__class__.__name__,
        model._primary_key)

        .. versionadded:: 0.1.5a7
            method added

        .. seealso::
            Usage example :meth:`sample_network <pydent.browser.Browser.sample_network>`

        :param models: list of models
        :param get_models: A function that takes in a single instance of a Model
            and returns an iterable of Tuples of (model, data),
            which is used to build edges.
        :param key_func: An optional function that takes in a single instance of
            a Model and returns a key and some node data
        :param cache_func: A function that takes in a list of models and caches
            some results.
        :param g: optional nx.DiGraph
        :param reverse: whether to reverse the edge list
        :param strict_cache: if True, if a request occurs after the cache step,
            a ForbiddenRequestException will be raised.
        :return: the relationship graph
        """

        if key_func is None:

            def key_func(m):
                return (m.__class__.__name__, m._primary_key), {}

        if g is None:
            g = nx.DiGraph()

        models = list(models)

        if not models:
            return g

        for m in models:
            key, ndata = key_func(m)
            g.add_node(key, attr_dict=ndata)

        visited = list(g.nodes)

        if cache_func:
            cache_func(models)

        new_models = []
        new_edges = []

        if strict_cache:
            kwargs = {"using_requests": False, "session_swap": True}
        else:
            kwargs = {}

        with models[0].session(**kwargs):
            try:
                for m1 in models:
                    for m2, data in get_models(m1):
                        if key_func(m2)[0] not in visited:
                            new_models.append(m2)
                        new_edges.append((key_func(m2)[0], key_func(m1)[0], data))
            except ForbiddenRequestError as e:
                msg = (
                    "An exception occurred while strict_cache == True.\n"
                    "This is most likely due to the cache_func not being thorough.\n"
                    "{}".format(str(e))
                )
                raise e.__class__(msg)

        for n1, n2, edata in new_edges:
            if reverse:
                g.add_edge(n2, n1, attr_dict=edata)
            else:
                g.add_edge(n1, n2, attr_dict=edata)

        return cls.relationship_network(
            new_models,
            get_models,
            cache_func,
            key_func=key_func,
            g=g,
            reverse=reverse,
            strict_cache=strict_cache,
        )

    # def relationship_network(self, models, get_models, cache_func, g=None):
    #     """
    #
    #
    #     .. versionadded:: 0.1.5a7
    #
    #
    #     :param models:
    #     :param get_models:
    #     :param g:
    #     :return:
    #     """
    #
    #     def model_to_key(m):
    #         return (m.__class__.__name__, m.id)
    #
    #     if g is None:
    #         g = nx.DiGraph()
    #     for m in models:
    #         g.add_node(model_to_key(m))
    #
    #     cache_func(models)
    #
    #     for m in models:
    #         next_models = get_models(m)

    def get(
        self,
        models: List[ModelBase],
        relations: List[BaseRelationship] = None,
        query: dict = None,
        strict: bool = True,
        force_refresh: bool = False,
    ) -> Union[Dict[str, List[ModelBase]], List[ModelBase]]:
        """

        :param models:
        :param relations:
        :param query:
        :param strict:
        :param force_refresh:
        :return:
        """
        if isinstance(models, ModelBase):
            models = [models]
        elif isinstance(models, str):
            models = list(self.model_cache.get(models, {}).values())
            if query:
                models, _ = self._find_matches(query, models)
        if relations:
            if isinstance(relations, str):
                return self.retrieve(
                    models, relations, strict=strict, force_refresh=force_refresh
                )
            else:
                return self.recursive_retrieve(
                    models, relations, strict=strict, force_refresh=force_refresh
                )
        else:
            return models

    def export_samples_to_csv(self, samples, out):
        """Exports the samples to a csv (for Aquarium import)

        :param samples: list of samples
        :type samples: list
        :param out: output path of csv file
        :type out: basestring
        :return: pandas dataframe used for the csv
        :rtype: pandas.DataFrame
        """
        df = self.samples_to_df(samples)
        df.to_csv(out)
        return df

    def samples_to_rows(self, samples, sample_resolver=None):
        """Return row of dictionaries containing sample information and their
        properties. Can be imported into a pandas DataFrame:

        .. code-block:: python

            import pandas

            df = pandas.DataFrame(samples_to_rows(samples))


        :param samples: samples, all of same sample type
        :type samples: list
        :param sample_resolver: callable to resolve a sample object if the \
            field value property contains a sample. \
            Defaults to return the sample name.
        :type sample_resolver: callable
        :return: list of dictionaries containing sample info and properties
        :rtype: list
        """

        assert (
            len({s.sample_type_id for s in samples}) == 1
        ), "Samples be the of the same SampleType"
        sample_type = samples[0].sample_type

        # self.recursive_retrieve(samples, {
        #     "field_values": "sample",
        #     "sample_type": {
        #         "field_types"
        #     }
        # })
        if sample_resolver is None:

            def default_resolver(sample):
                if isinstance(sample, pydent_models.Sample):
                    return sample.name
                if isinstance(sample, list):
                    resolved_samples = []
                    for s in sample:
                        if isinstance(s, pydent_models.Sample):
                            resolved_samples.append(s.name)
                        else:
                            resolved_samples.append(s)
                    sample = resolved_samples
                return sample

            sample_resolver = default_resolver
        rows = []
        for s in samples:
            row = {
                sample_type.name: s.name,
                "Description": s.description,
                "Project": s.project,
            }
            props = {k: sample_resolver(v) for k, v in s.properties.items()}
            row.update(props)
            rows.append(row)
        return rows

    # TODO: add to change log
    @staticmethod
    def _inspect_header(model, name=None, _id="id"):
        if name is not None:
            name = eval("model.{}".format(name))
        else:
            name = ""
        return "{model_class}: {_id} {name}".format(
            model_class=model.__class__.__name__,
            name=name,
            _id=eval("model.{}".format(_id)),
        )

    # TODO: add to change log
    @staticmethod
    def _inspect_rows(model, attributes, indent=2):
        rows = []
        for attr in attributes:
            rows.append(
                "{attr}: {val}".format(attr=attr, val=eval("model.{}".format(attr)))
            )
        sep = "\n" + " " * indent
        s = sep + sep.join(rows)
        return s

    # TODO: add to change log
    @classmethod
    def inspect(cls, model, header, attributes):
        model_header = cls._inspect_header(model, **header)
        rows = cls._inspect_rows(model, attributes)
        return "{header}{rows}".format(header=model_header, rows=rows)
