import logging
import re
from difflib import get_close_matches

from pydent import ModelRegistry
from pydent import models as pydent_models
from pydent.utils import logger


# TODO: browser documentation
# TODO: examples in sphinx
class BrowserException(Exception):
    """Generic browser exception"""


class Browser(logger.Loggable, object):

    def __init__(self, session):
        self.session = session
        self._list_models_fxn = self.sample_list
        self.use_cache = False
        self.model_name = 'Sample'
        self.cache = {}
        self.init_logger("Browser@{}".format(session.url))

    # TODO: change session interface (find, where, etc.) to use cache IF use_cache = True
    # TODO: where and find queries can sort through models much more quickly than Aquarium, but can fallback to Aq

    def set_model(self, model_name):
        ModelRegistry.get_model(model_name)
        self.model_name = model_name
        if model_name == "Sample":
            self._list_models_fxn = self.sample_list
        else:
            self._list_models_fxn = self._generic_list_models

    @property
    def interface(self):
        return self.session.model_interface(self.model_name)

    @property
    def item(self):
        return self.session.Item

    @property
    def sample_type(self):
        return self.session.SampleType

    def _generic_list_models(self, opts=None, **query):
        models = self.session.model_interface(self.model_name).where(query, opts=opts)
        return ['{}: {}'.format(m.id, m.name) for m in models]

    def sample_list(self, sample_type_id=None):
        path = 'sample_list'
        if sample_type_id is not None:
            path += "/" + str(sample_type_id)
        return self.session.utils.aqhttp.get(path)

    def reset_cache(self):
        self.cache = {}

    def list_models(self, *args, **kwargs):
        get_models = lambda: self._list_models_fxn(*args, **kwargs)
        model_list = []
        if self.use_cache:
            models_cache = self.cache.get('models', {})
            if self.model_name in models_cache:
                models_list = models_cache[self.model_name]
            else:
                models_list = get_models()
        else:
            model_list = get_models()
        self.cache.setdefault('models', {})
        self.cache['models'][self.model_name] = model_list[:]
        return model_list

    def find(self, model_id):
        return self.interface.find(model_id)

    def find_by_name(self, model_name):
        return self.interface.find_by_name(model_name)

    def where(self, query):
        return self.interface.where(query)

    def find_by_sample_type_name(self, name):
        return self.interface.where({"sample_type_id": self.session.SampleType.find_by_name(name).id})

    def _search_helper(self, pattern, filter_fxn, sample_type=None, **query):
        sample_type_id = None
        if sample_type is not None:
            if isinstance(sample_type, pydent_models.SampleType):
                sample_type_id = sample_type.id
            else:
                sample_type_id = self.session.SampleType.find_by_name(sample_type).id

        if sample_type_id is not None:
            query.update({'sample_type_id': sample_type_id})

        model_list = self.list_models(sample_type_id)
        self._info("found {} total models of type {}".format(len(model_list), self.model_name))
        matches = filter_fxn(pattern, model_list)

        if not matches:
            return []

        if query:
            query.update({"id": matches})
            filtered = self.interface.where(query)
        else:
            filtered = self.interface.find(matches)
        self._info("filtered to {} total models of type {}".format(len(filtered), self.model_name))
        return filtered

    def search(self, pattern, ignore_case=True, sample_type=None, **query):
        """
        Performs a regular expression search of Samples

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

        return self._search_helper(pattern, regex_filter, sample_type=sample_type, **query)

    def close_matches(self, pattern, sample_type=None, **query):
        """
        Finds samples whose names closely match the pattern

        :param pattern: regular expression pattern
        :type pattern: basestring
        :param sample_type: sample_type_name to filter samples (optional)
        :type sample_type: basestring
        :param query: additional query parameters to filter by
        :type query: dict
        :return: list of samples
        :rtype: list
        """
        return self._search_helper(pattern, get_close_matches, sample_type=sample_type, **query)

    def list_field_values(self, model_ids, **query):
        """
        Lists sample field values
        :param models:
        :type models:
        :param query:
        :type query:
        :return:
        :rtype:
        """
        query.update({"parent_class": self.model_name, "parent_id": model_ids})
        return self.session.FieldValue.where(query)

    def _group_by_attribute(self, models, attribute):
        d = {}
        for s in models:
            arr = d.setdefault(getattr(s, attribute), [])
            arr.append(s)
        return d

    def filter_by_data_associations(self, models, associations):
        raise NotImplementedError()

    def filter_by_field_value_properties(self, samples, properties):
        """
        Filters a list of samples by their FieldValue properties. e.g. {"T Anneal": 64}.

        .. code-block::

        # search samples
        browser.filter_samples_by_property(
            browser.search(".*GFP.*", sample_type="Fragment"),
            {"Reverse Primer": browser.find_by_name("eGFP_f")

        :param samples: list of Samples
        :type samples: list
        :param properties: dictionary of properties.
        :type properties: dict
        :return:
        :rtype:
        """

        # TODO: handle metatypes better
        metatype_attribute = "sample_type_id"
        metatype_name = "SampleType"

        if self.model_name == "Operation":
            metatype_attribute = "operation_type_id"
            metatype_name = "OperationType"

        grouped = self._group_by_attribute(samples, metatype_attribute)

        filtered_model_ids = []

        for attrid in grouped:
            models = grouped[attrid]
            model_ids = [s.id for s in models]

            metatype = self.session.model_interface(metatype_name).find(attrid)

            for prop_name in properties:
                field_type = metatype.field_type(prop_name)  # necessary since FieldValues are missing field_type_ids
                if field_type:
                    fv_query = {"name": prop_name}
                    value = properties[prop_name]
                    if value:
                        if field_type.ftype == 'sample':
                            fv_query.update({'child_sample_id': value.id})
                        else:
                            fv_query.update({'value': value})
                    fvs = self.list_field_values(model_ids, **fv_query)
                    fv_parent_sample_ids = set([fv.parent_id for fv in fvs])
                    model_ids = list(set(model_ids).intersection(fv_parent_sample_ids))
            filtered_model_ids += model_ids
        if filtered_model_ids == []:
            return []
        return self.interface.find(filtered_model_ids)

    def new_sample(self, sample_type):
        return self.session.SampleType.find_by_name(sample_type).new_sample

    @staticmethod
    def __json_update(model, **params):
        """This update method is fairly dangerous. Be careful!"""

        aqhttp = model.session._AqSession__aqhttp
        data = {"model": {"model": model.__class__.__name__}}
        data.update(model.dump(**params))
        #         return aqhttp.put("{}")
        return aqhttp.post('json/save', json_data=data)

    # TODO: This method is slow, but 'PUT' sample.json does not work...
    @classmethod
    def update_sample(cls, sample):
        cls.__json_update(sample, include={"field_values": "sample", "sample_type": []})
        for fv in sample.field_values:
            cls.__json_update(fv, include={"sample"})

    #         return cls.__json_update(sample, include={"field_values": "sample"})

    def new_sample(self, sample_type):
        return self.session.SampleType.find_by_name(sample_type).new_sample

    def save_sample(self, sample, overwrite=False, strict=False):
        """

        :param sample: new Aquarium sample
        :type sample: Sample
        :param overwrite: whether to overwrite existing sample (if it exists) properties with the new sample properties
        :type overwrite: bool
        :param strict: If False, an exception will be raised if the sample with the same sample name exists
        :type strict: bool
        :return: saved Aquarium sample
        :rtype: Sample
        """
        if not strict:
            existing = self.find_by_name(sample.name)
            if existing:
                if existing.sample_type_id != sample.sample_type_id:
                    raise BrowserException(
                        "There is an existing sample with nme \"{}\", but it is a \"{}\" sample_type, not a \"{}\"".format(
                            sample.name,
                            existing.sample_type.name,
                            sample.sample_type.name
                        ))
                if overwrite:
                    existing.update_properties(sample.properties)
                    self.update_sample(existing)
                return existing
        return sample.save()

    @staticmethod
    def collect_callback_args(models, relationship_name):
        """Combines all of the callback args into a single query"""
        args = {}
        for s in models:
            relation = s.relationships[relationship_name]
            callback_args = s._get_callback_args(relation)
            for cba in callback_args:
                for k in cba:
                    args.setdefault(k, [])
                    if cba[k] not in args[k]:
                        args[k].append(cba[k])
        return args

    def _retrieve_has_many_or_has_one(self, models, relationship_name):
        """Performs exactly 1 query to fullfill some relationship for a list of models"""
        if not models:
            return []

        relation = models[0].relationships[relationship_name]

        ref = relation.ref  # sample_id
        attr = relation.attr  # id
        model_class2 = relation.model
        many = relation.many

        models1 = models
        if many:
            models2_query = {ref: [getattr(s, attr) for s in models1]}
            # self._info("querying {cls2} using {cls1}.{attr} << {cls2}.{ref}".format(cls1='model', cls2=model_class2, attr=attr, ref=ref))
        else:
            models2_query = {attr: [getattr(s, ref) for s in models1]}
            # self._info("querying {cls2} using {cls1}.{ref} <> {cls2}.{attr}".format(cls1='model', cls2=model_class2, attr=attr, ref=ref))
        models2 = self.session.model_interface(model_class2).where(models2_query)
        # self._info("{} {} models retrieved".format(len(models2), model_class2))
        if not models2:
            return []

        if many:
            model1_attr_dict = {m1.id: list() for m1 in models1}
            for m2 in models2:
                m1id = getattr(m2, ref)
                model1_attr_dict[m1id].append(m2)
        else:
            model2_dict = {getattr(m2, attr): m2 for m2 in models2}
            model1_attr_dict = {m1.id: None for m1 in models1}
            for m1 in models1:
                m1id = getattr(m1, attr)
                model1_attr_dict[m1id] = model2_dict[getattr(m1, ref)]

        for m1 in models1:
            found_models = model1_attr_dict[getattr(m1, attr)]
            m1.__dict__.update({relationship_name: found_models})

        return models2

    def _retrieve_has_many_through(self, models, relationship_name):
        """Performs exactly 2 queries to establish a HasManyThrough relationship"""
        relation = models[0].relationships[relationship_name]
        association_relation = models[0].relationships[relation.through_model_attr]
        attr = relation.attr
        ref = association_relation.ref

        # find other key
        association_class = ModelRegistry.get_model(association_relation.nested)
        association_relationships = association_class.get_schema_class().relationships
        other_ref = None
        for r in association_relationships:
            ar = association_relationships[r]
            if ar.nested == relation.nested:
                other_ref = r

        associations = self._retrieve_has_many_or_has_one(models, relation.through_model_attr)
        self._retrieve_has_many_or_has_one(associations, other_ref)

        associations_by_mid = {}
        for a in associations:
            associations_by_mid.setdefault(getattr(a, ref), []).append(a)

        all_models = []
        for m in models:
            mid = getattr(m, attr)
            if mid in associations_by_mid:
                associations = associations_by_mid[mid]
                _models = [getattr(a, other_ref) for a in associations]
                m.__dict__.update({relationship_name: _models})
                all_models += _models
            else:
                m.__dict__.update({relationship_name: None})
        return list(set(all_models))

    def retrieve(self, models, relationship_name):
        """
        Retrieves a model relationship for the list of models. Compared to a `for` loop,
        `retrieve` is >10X faster for most queries.

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
        :return: list of models retrieved
        :rtype: list
        """
        assert len(set([m.__class__.__name__ for m in models])) == 1, "Models must be all of the same BaseModel"
        relation = models[0].relationships[relationship_name]
        accepted_types = ["HasOne", "HasMany", "HasManyThrough", "HasManyGeneric"]
        # TODO: add relationship handler for Many and One
        if relation.__class__.__name__ not in accepted_types:
            raise BrowserException(
                "retrieve is not supported for the \"{}\" relationship".format(relation.__class__.__name__))
        if hasattr(relation, 'through_model_attr'):
            return self._retrieve_has_many_through(models, relationship_name)
        else:
            return self._retrieve_has_many_or_has_one(models, relationship_name)

    def recursive_retrieve(self, models, relations):
        """
        Retrieve recursively from an iterable. The relations_dict iterable may be
        either a list or a dictionary. For example, the following will collect all of the field_values
        and their incoming and outgoing wires, the connecting field_values, and finally those FieldValues'
        operations.

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
        :param relations: the relation to retrieve. This may either be a string (by attribute name), a list, or a dict.
        :type relations: list|dict|basestring
        :return: dictionary of all models retrieved grouped by the attribute name that retrieved them.
        :rtype: dictionary
        """
        if isinstance(relations, str):
            return {relations: self.retrieve(models, relations)}
        else:
            models_by_attr = {}
            for relation_name in relations:
                models_by_attr.setdefault(relation_name, [])
                new_models = self.retrieve(models, relation_name)
                models_by_attr[relation_name] += new_models
                if isinstance(relations, dict):
                    _models_by_attr = self.recursive_retrieve(new_models, dict(relations).pop(relation_name))
                    for attr in _models_by_attr:
                        _models = _models_by_attr[attr]
                        if attr in models_by_attr:
                            models_by_attr[attr] += _models
                        else:
                            models_by_attr[attr] = _models_by_attr[attr]
            return models_by_attr
