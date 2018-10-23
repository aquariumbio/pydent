import re
from difflib import get_close_matches

from pydent import ModelRegistry
from pydent import models as pydent_models
from pydent.utils import logger
import pandas as pd

# TODO: browser documentation
# TODO: examples in sphinx
class BrowserException(Exception):
    """Generic browser exception"""


class Browser(logger.Loggable, object):

    def __init__(self, session):
        self.session = session
        self._list_models_fxn = self.sample_list
        self.use_cache = True
        self.model_name = 'Sample'
        self.model_list_cache = {}
        self.model_cache = {}
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

    def interface(self, model_class=None):
        if model_class is None:
            model_class = self.model_name
        return self.session.model_interface(model_class)

    def _generic_list_models(self, **query):
        models = self.where(query, self.model_name)
        return ['{}: {}'.format(m.id, m.name) for m in models]

    def sample_list(self, sample_type_id=None):
        path = 'sample_list'
        if sample_type_id is not None:
            path += "/" + str(sample_type_id)
        return self.session.utils.aqhttp.get(path)

    def reset_cache(self):
        self.model_list_cache = {}
        self.model_cache = {}

    def list_models(self, *args, **kwargs):
        get_models = lambda: self._list_models_fxn(*args, **kwargs)

        if self.use_cache:
            model_list = []
            models_cache = self.model_list_cache.get('models', {})
            if self.model_name in models_cache:
                model_list = models_cache[self.model_name]
            else:
                model_list = get_models()
        else:
            model_list = get_models()
        self.model_list_cache.setdefault('models', {})
        self.model_list_cache['models'][self.model_name] = model_list[:]
        return model_list

    def one(self, model_class=None, sample_type=None):
        pass

    def last(self, num, model_class=None):
        pass

    def first(self, num, model_class=None):
        pass

    def find(self, model_id, model_class=None):
        if model_class is None:
            model_class = self.model_name
        if self.use_cache:
            return self.cached_find(model_class, model_id)
        return self.interface(model_class).find(model_id)

    def where(self, query, model_class=None, primary_key='id', sample_type=None):
        if model_class is None:
            model_class = self.model_name
        if sample_type is not None:
            sample_type_id = self.find_by_name(sample_type, 'SampleType').id
            query.update({"sample_type_id": sample_type_id})
        if self.use_cache:
            return self.cached_where(model_class, query, primary_key=primary_key)
        return self.interface(model_class).where(query)

    def find_by_name(self, name, model_class=None, primary_key='id'):
        models = self.where({'name': name}, model_class, primary_key=primary_key)
        if not models:
            return None
        return models[0]

    # def find(self, model_id):
    #     return self.interface.find(model_id)
    #
    # def find_by_name(self, model_name):
    #     return self.interface.find_by_name(model_name)
    #
    # def where(self, query):
    #     return self.interface().where(query)

    @staticmethod
    def _match_query(query, model_dict):
        """
        Matches a query against a model dictionary

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
            match = cls._match_query(query, m.__dict__)
            if match:
                found.append(m)
                found_queries.append(match)
        return found, found_queries

    def _update_model_cache_helper(self, modelname, modeldict):
        self._info("CACHE updated cached with {} {} models".format(len(modeldict), modelname))
        self.model_cache.setdefault(modelname, {})
        self.model_cache[modelname].update(dict(modeldict))

    def _update_model_cache(self, models):
        grouped_by_type = {}
        for model in models:
            classname = model.__class__.__name__
            arr = grouped_by_type.setdefault(classname, [])
            arr.append(model)

        for clstype in grouped_by_type:
            self._update_model_cache_helper(clstype, {m.id: m for m in grouped_by_type[clstype]})

    # TODO: support unsaved models as well
    def cached_find(self, model_class, id):
        if isinstance(id, list):
            return self.cached_where(model_class, {'id': id})
        cached_models = self.model_cache.get(model_class, {})
        found_model = cached_models.get(id, None)
        if found_model is None:
            found_model = self.interface(model_class).find(id)
        else:
            self._info("CACHE found {} model with id={} in cache".format(model_class, id))
        if found_model is None:
            return None
        self._update_model_cache_helper(model_class, {found_model.id: found_model})
        return found_model

    def cached_where(self, model, query, primary_key='id'):
        cached_models = self.model_cache.get(model, {})
        found, found_queries = self._find_matches(query, list(cached_models.values()))
        found_dict = {f.id: f for f in found}
        remaining_query = dict(query)
        if primary_key in query:
            found_ids = [q[primary_key] for q in found_queries]
            query_id_list = query[primary_key]
            if isinstance(query_id_list, str) or isinstance(query_id_list, int):
                query_id_list = [query_id_list]
            remaining_ids = list(set(query_id_list).difference(set(found_ids)))
            remaining_query[primary_key] = remaining_ids
        self._info("CACHE found {} {} models in cache".format(len(found_dict), model))

        # TODO: this code may be sketchy... here {'id': []}, really means we found all of the models..
        if primary_key in remaining_query and not remaining_query[primary_key]:
            return list(found_dict.values())
        server_models = self.interface(model).where(remaining_query)

        models_dict = {s.id: s for s in server_models}
        models_dict.update(found_dict)
        self._update_model_cache_helper(model, models_dict)

        return list(models_dict.values())

    def _search_helper(self, pattern, filter_fxn, sample_type=None, **query):
        sample_type_id = None
        if sample_type is not None:
            if isinstance(sample_type, pydent_models.SampleType):
                sample_type_id = sample_type.id
            else:
                sample_type_id = self.where({'name': sample_type}, 'SampleType')[0].id

        if sample_type_id is not None:
            query.update({'sample_type_id': sample_type_id})

        model_list = self.list_models(sample_type_id)
        self._info("SEARCH found {} total models of type {}".format(len(model_list), self.model_name))
        matches = filter_fxn(pattern, model_list)

        if not matches:
            return []

        if query:
            query.update({"id": matches})
            filtered = self.where(query, self.model_name)
        else:
            filtered = self.interface().find(matches)
        self._info("SEARCH filtered to {} total models of type {}".format(len(filtered), self.model_name))

        if self.use_cache:
            self._update_model_cache(filtered)

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
        return self.where(query, "FieldValue")

    def _group_by_attribute(self, models, attribute):
        d = {}
        for s in models:
            arr = d.setdefault(getattr(s, attribute), [])
            arr.append(s)
        return d

    def filter_by_data_associations(self, models, associations):
        raise NotImplementedError()

    def filter_by_properties(self, samples, properties):
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
        if self.model_name not in ["Operation", "Sample"]:
            raise BrowserException("Cannot filter_by_properties, model must be either a Operation or Sample")
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
            metatype = self.find(attrid, metatype_name)
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
        return self.interface().find(filtered_model_ids)

    def new_sample(self, sample_type, name, description, project, properties=None):
        st = self.find_by_name(sample_type, "SampleType", primary_key='name')
        if st.__dict__.get('field_types', None) is None:
            fts = self.where({"parent_class": "SampleType", "parent_id": st.id}, "FieldType")
            st.field_types = fts
        return st.new_sample(name, description, project, properties=properties)

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


    def save_sample(self, sample, overwrite_server=False, strict=False):
        """

        :param sample: new Aquarium sample
        :type sample: Sample
        :param overwrite_server: whether to overwrite existing sample (if it exists) properties with the new sample properties
        :type overwrite_server: bool
        :param strict: If False, an exception will be raised if the sample with the same sample name exists
        :type strict: bool
        :return: saved Aquarium sample
        :rtype: Sample
        """
        if not strict:
            existing = self.interface("Sample").find_by_name(sample.name)
            if existing:
                if existing.sample_type_id != sample.sample_type_id:
                    raise BrowserException(
                        "There is an existing sample with name \"{}\", but it is a \"{}\" sample_type, not a \"{}\"".format(
                            sample.name,
                            existing.sample_type.name,
                            sample.sample_type.name
                        ))
                if overwrite_server:
                    existing.update_properties(sample.properties)
                    self.update_sample(existing)
                return existing
        sample.save()
        self._update_model_cache([sample])
        return sample

    @staticmethod
    def _collect_callback_args(models, relation):
        """Combines all of the callback args into a single query"""
        args = {}
        for s in models:
            callback_args = s._get_callback_args(relation)
            if not relation.many:
                args.setdefault(relation.attr, [])
                args[relation.attr] += [x for x in callback_args if x is not None]
            else:
                for cba in callback_args:
                    for k in cba:
                        args.setdefault(k, [])
                        arg_arr = args[k]
                        val = cba[k]
                        if val is not None:
                            if isinstance(val, list):
                                for v in val:
                                    if v not in arg_arr:
                                        arg_arr.append(v)
                            else:
                                arg_arr.append(val)
        return args

    # TODO: handle not-yet existant samples using rid
    def _retrieve_has_many_or_has_one(self, models, relationship_name, relation=None):
        """Performs exactly 1 query to fullfill some relationship for a list of models"""
        if not models:
            return []
        models = models[:]
        if relation is None:
            relation = models[0].relationships[relationship_name]

        ref = relation.ref  # sample_id
        attr = relation.attr  # id
        model_class2 = relation.model
        many = relation.many

        # todo: collect existing fullfilled relationship
        # todo: partition, then collect callback
        # todo: how to handle when model_attr is absent?, or just raise error?

        retrieve_query = self._collect_callback_args(models, relation)
        retrieved_models = self.where(retrieve_query, model_class2)
        self._info("RETRIEVE retrieved {l} {cls} models using query {query}".format(
            l=len(retrieved_models),
            cls=model_class2,
            query=self._pprint_data(retrieve_query)
        ))

        if not retrieved_models:
            return []

        if many:
            model_dict = {m1.id: list() for m1 in models}
            for model in retrieved_models:
                model_ref = getattr(model, ref)
                if model_ref is not None:
                    model_dict[model_ref].append(model)
                else:
                    self._error(
                        "RETRIEVE ref: {ref} {model_ref}, attr: {attr}".format(ref=ref, attr=attr, model_ref=model_ref))
        else:
            retrieved_dict = {getattr(m2, attr): m2 for m2 in retrieved_models}
            model_dict = {m1.id: None for m1 in models}
            missing_models = []
            for model in models:
                model_attr = getattr(model, attr)
                model_ref = getattr(model, ref)
                if model_ref is not None:
                    if model_attr is not None:
                        model_dict[model_attr] = retrieved_dict[model_ref]
                    else:
                        self._error(
                            "attr: {attr}={model_attr}, ref: {ref}={model_ref}".format(m1=model, ref=ref, attr=attr,
                                                                                       model_attr=model_attr,
                                                                                       model_ref=model_ref))
                    if model_ref not in retrieved_dict:
                        missing_models.append(model_ref)
            if missing_models:
                self._error("INCONSISTENT AQUARIUM DATABASE - There where {l} missing {cls} models "
                            "from the Aquarium database, which were ignored by trident. "
                            "This happens when models are deleted from Aquarium which "
                            "results in an inconsistent server database. Trident was unable "
                            "resolve the following relationships which returned no models from the server: "
                            "{cls}.where({attr}={missing})".format(
                    l=len(missing_models),
                    cls=model_class2,
                    missing=missing_models,
                    attr=attr
                ))
        for model in models:
            found_models = model_dict[getattr(model, attr)]
            model.__dict__.update({relationship_name: found_models})

        return retrieved_models

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

    def retrieve(self, models, relationship_name, relation=None):
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
        if not models:
            return []
        self._info('RETRIEVE retrieving "{}"'.format(relationship_name))
        model_classes = set([m.__class__.__name__ for m in models])
        assert len(model_classes) == 1, "Models must be all of the same BaseModel, but found {}".format(model_classes)
        if relation is None:
            relation = models[0].relationships[relationship_name]
        else:
            if relationship_name in models[0].relationships:
                raise BrowserException(
                    'Cannot add new relationship "{}" because it already exists in the model definition'.format(
                        relationship_name))
        accepted_types = ["HasOne", "HasMany", "HasManyThrough", "HasManyGeneric"]
        # TODO: add relationship handler for Many and One
        if relation.__class__.__name__ not in accepted_types:
            raise BrowserException(
                "retrieve is not supported for the \"{}\" relationship".format(relation.__class__.__name__))
        self._info('RETRIEVE {}: {}'.format(relationship_name, relation))
        if hasattr(relation, 'through_model_attr'):
            found_models = self._retrieve_has_many_through(models, relationship_name)
        else:
            found_models = self._retrieve_has_many_or_has_one(models, relationship_name, relation)
        self._info('RETRIEVE retrieved {} for "{}"'.format(len(found_models), relationship_name))
        return found_models

    def recursive_retrieve(self, models, relations):
        """
        Efficiently retrieve a model relationship recursively from an iterable. The relations_dict iterable may be
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
        self._info("RETRIEVE recursively retrieving {}".format(relations))
        if isinstance(relations, str):
            self._info('RETRIEVE retrieving "{}"'.format(relations))
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

    def samples_to_df(self, samples):
        df = pd.DataFrame(self.samples_to_rows(samples))
        df.drop_duplicates(inplace=True)
        st = samples[0].sample_type
        columns = [st.name, 'Description', 'Project'] + [ft.name for ft in st.field_types]
        df = df[columns]
        df = df.set_index(st.name)
        return df

    def export_samples_to_csv(self, samples, out):
        df = self.samples_to_df(samples)
        df.to_csv(out)
        return df

    def samples_to_rows(self, samples, sample_resolver=None):
        """
        Return row of dictionaries containing sample information and their properties. Can be
        imported into a pandas DataFrame:

        .. code-block:: python

            import pandas

            df = pandas.DataFrame(samples_to_rows(samples))


        :param samples: samples, all of same sample type
        :type samples: list
        :param sample_resolver: callable to resolve a sample object if the field value property contains a sample.
        Defaults to return the sample anme
        :type sample_resolver: callable
        :return: list of dictionaries containing sample info and properties
        :rtype: list
        """

        assert len(set([s.sample_type_id for s in samples])) == 1, "Samples be the of the same SampleType"
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
                return sample

            sample_resolver = default_resolver
        rows = []
        for s in samples:
            row = {sample_type.name: s.name, 'Description': s.description, 'Project': s.project}
            props = {k: sample_resolver(v) for k, v in s.properties.items()}
            row.update(props)
            rows.append(row)
        return rows
