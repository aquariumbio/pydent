from pydent.utils import filter_list
from itertools import zip_longest

class FieldTypeInterface(object):

    def field_type(self, name, role):
        if self.field_types:
            fts = filter_list(self.field_types, role=role, name=name)
            if len(fts) > 0:
                return fts[0]


class FieldValueInterface(object):
    """A common interface for things (i.e. Operations and Samples) that have FieldValues and FieldTypes"""

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

    def get_metatype(self):
        metatype = self.METATYPE
        assert issubclass(type(metatype), FieldTypeInterface)
        return metatype

    def get_field_value(self, name, role=None):
        fv_array = self.get_field_value_array(name, role=role)
        if fv_array:
            return fv_array[0]

    def get_field_value_array(self, name, role=None):
        return [fv for fv in self.field_values if fv.name == name and fv.role == role]

    def get_field_types(self):
        return self.get_metatype().field_types

    def _field_value_dictionary(self, ft_func, fv_func):
        data = {}
        ft_dict = {ft.id: ft for ft in self.get_field_types()}

        for ft in ft_dict.values():
            if ft.array:
                val = []
            else:
                val = None
            data[ft_func(ft)] = val

        for fv in self.field_values:
            ft = ft_dict[fv.field_type_id]
            val = fv_func(fv)
            if ft.array:
                data[ft_func(ft)].append(val)
            else:
                data[ft_func(ft)] = val

        return data

    def set_field_value(self, name, role, values):
        fv = self.get_field_value(name, role)
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

    # def properties(self):
    #     """Key-values of the properties"""
    #
    # def empty_properties(self):
    #     """Returns empty list of properties"""
    #
    # def update_properties(self):
    #     """Updates the properties locally"""

    def get_routing(self):
        return self._field_value_dictionary(
            lambda ft: ft.routing,
            lambda fv: fv.sid
        )