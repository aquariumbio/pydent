from collections import Sequence
from itertools import zip_longest

from pydent.base import ModelBase
from pydent.utils import filter_list


class FieldMixin:
    """
    Mixin for finding FieldType and FieldValue relationships
    """

    def find_field_parent(self, model_name, model_id):
        """
        Callback for finding operation_type or sample_type.
        If parent_class does not match the expected nested model name
        (OperationType or SampleType), callback will return None
        """
        if model_name == self.parent_class:
            # weird, but helps with refactoring this mixin
            fxn_name = ModelBase.find_callback.__name__
            fxn = getattr(self, fxn_name)
            return fxn(model_name, model_id)


class FieldTypeInterface(object):

    def field_type(self, name, role):
        if self.field_types:
            fts = filter_list(self.field_types, role=role, name=name)
            if len(fts) > 0:
                return fts[0]


class FieldValueInterface(object):
    """A common interface for things (i.e. Operations and Samples) that have FieldValues and FieldTypes"""

    def new_field_value_from_field_type(self, field_type, values=None):
        assert field_type in self.get_field_types()
        self.new_field_value(field_type.name, field_type.role, values=values)

    def new_field_value(self, name, role=None, values=None):
        # retrieve the field_type from the meta_type
        metatype = self.get_metatype()
        ft = metatype.field_type(name, role=role)

        # initialize the field_value
        fv = ft.initialize_field_value(parent=self)
        if values:
            fv.set_value(**values)
        # add new field_value to list of field_values
        if self.field_values is None:
            self.field_values = []

        self.field_values.append(fv)
        return fv

    def safe_get_field_type(self, fv):
        if fv.field_type_id is None:
            fts = self.get_field_types()
            h = lambda f: '{}_%&^_{}'.format(f.name, f.role)
            name_role_to_ft = {h(ft): ft for ft in fts}
            ft = name_role_to_ft.get(h(fv), None)
            if ft is not None:
                fv.set_field_type(ft)
        return fv.field_type

    def get_metatype(self):
        metatype = getattr(self, self.METATYPE)
        assert issubclass(type(metatype), FieldTypeInterface)
        return metatype

    def get_field_value(self, name, role=None):
        fv_array = self.get_field_value_array(name, role=role)
        if fv_array:
            return fv_array[0]

    def get_field_value_array(self, name, role=None):
        if self.field_values is None:
            return []
        return [fv for fv in self.field_values if fv.name == name and fv.role == role]

    def get_field_types(self, name=None, role=None):
        fts = self.get_metatype().field_types
        if name is not None:
            fts = [ft for ft in fts if ft.name == name]
        if role is not None:
            fts = [ft for ft in fts if ft.name == name]
        return fts

    def get_field_type(self, name, role):
        fts = self.get_field_types(name, role)
        if fts:
            return fts[0]

    def _field_value_dictionary(self, ft_func=None, fv_func=None):

        if ft_func is None:
            ft_func = lambda ft: ft.name
        if fv_func is None:
            fv_func = lambda fv: fv

        data = {}
        ft_dict = {ft.id: ft for ft in self.get_field_types()}

        for ft in ft_dict.values():
            if ft.array:
                val = []
            else:
                val = None
            data[ft_func(ft)] = val

        # safely get field_types; field_type_id is sometimes None in Sample field_values;
        # unsure if this used to be a bug in Aquarium that has been since resolved

        for fv in self.field_values:
            val = fv_func(fv)
            ft = self.safe_get_field_type(fv)
            if ft:
                if ft.array:
                    data[ft_func(ft)].append(val)
                else:
                    data[ft_func(ft)] = val

        return data

    def set_field_value(self, name, role, values):
        ft = self.get_field_type(name, role)
        fv = self.get_field_value(name, role)
        if fv is None:
            self.new_field_value_from_field_type(ft, values)
        else:
            fv.set_value(**values)
        return self

    def set_field_value_array(self, name, role, values_array):
        fvs = self.get_field_value_array(name, role)
        to_be_removed = []
        for fv, val in zip_longest(fvs, values_array):
            if fv and val:
                fv.set_value(val)
            elif fv and not val:
                to_be_removed.append(fv)
            elif not fv and val:
                self.new_field_value(name, role, val)
        for fv in to_be_removed:
            self.field_values.remove(fv)
        return self

    def get_routing(self):
        return self._field_value_dictionary(
            lambda ft: ft.routing,
            lambda fv: fv.sid
        )

    def update_field_values(self, value_dict, role=None):
        ft_dict = {ft.name: ft for ft in self.get_field_types()}

        for name, val in value_dict.items():
            ft = ft_dict[name]
            if issubclass(type(val), Sequence) and ft.array:
                self.set_field_value_array(name, role, val)
            else:
                self.set_field_value(name, role, val)
        return self
