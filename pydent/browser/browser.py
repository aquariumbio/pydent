import re
from difflib import get_close_matches

from pydent import models
from pydent import ModelRegistry

# TODO: browser documentation
# TODO: examples in sphinx
class BrowserException(Exception):
    """Generic browser exception"""


class Browser(object):

    model_name = 'Sample'
    cache = {}

    def __init__(self, session):
        self.session = session
        self._list_models_fxn = self.sample_list
        self.use_cache = False

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
            if isinstance(sample_type, models.SampleType):
                sample_type_id = sample_type.id
            else:
                sample_type_id = self.session.SampleType.find_by_name(sample_type).id

        if sample_type_id is not None:
            query.update({'sample_type_id': sample_type_id})

        model_list = self.list_models(sample_type_id)
        matches = filter_fxn(pattern, model_list)

        if not matches:
            return []

        if query:
            query.update({"id": matches})
            return self.interface.where(query)
        return self.interface.find(matches)

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

    def list_sample_field_values(self, samples, **query):
        """
        Lists sample field values
        :param samples:
        :type samples:
        :param query:
        :type query:
        :return:
        :rtype:
        """
        query.update({"parent_class": "Sample", "parent_id": [s.id for s in samples]})
        return self.session.FieldValue.where(query)

    def _group_by_sample_type(self, samples):
        d = {}
        for s in samples:
            arr = d.setdefault(s.sample_type_id, [])
            arr.append(s)
        return d

    def filter_samples_by_property(self, samples, properties):
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
        by_stid = self._group_by_sample_type(samples)

        filtered_sample_ids = []

        for stid in by_stid:
            samps = by_stid[stid]
            sample_ids = [s.id for s in samps]

            st = self.session.SampleType.find(stid)
            for prop_name in properties:
                field_type = st.field_type(prop_name)  # necessary since FieldValues are missing field_type_ids
                if field_type:
                    fv_query = {"name": prop_name}
                    value = properties[prop_name]
                    if value:
                        if field_type.ftype == 'sample':
                            fv_query.update({'child_sample_id': value.id})
                        else:
                            fv_query.update({'value': value})
                    fvs = self.sample_field_values(sample_ids, **fv_query)
                    fv_parent_sample_ids = set([fv.parent_id for fv in fvs])
                    sample_ids = list(set(sample_ids).intersection(fv_parent_sample_ids))
            filtered_sample_ids += sample_ids
        if filtered_sample_ids == []:
            return []
        return self.interface.find(filtered_sample_ids)

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
