"""Mixins for FieldValues and those objects using FieldValues and
FieldTypes."""
from collections.abc import Sequence
from itertools import zip_longest

from pydent.base import ModelBase
from pydent.utils import filter_list


class FieldMixin:
    """Mixin for finding FieldType and FieldValue relationships."""

    def find_field_parent(self, model_name, model_id):
        """Callback for finding operation_type or sample_type.

        If parent_class does not match the expected nested model name
        (OperationType or SampleType), callback will return None
        """
        if model_name == self.parent_class:
            # weird, but helps with refactoring this mixin
            fxn_name = ModelBase.find_callback.__name__
            fxn = getattr(self, fxn_name)
            return fxn(model_name, model_id)


class FieldTypeInterface:
    """An interface for things that have field types (i.e.

    :class:`pydent.models.OperationType` and :class:`pydent.models.SampleType`).
    """

    def field_type(self, name, role):
        """Returns a :class:`pydent.models.FieldType` by its name and role.

        :param name: its name
        :type name: basestring
        :param role: its role
        :type role: basestring
        :return: the field type or None if not found
        :rtype: FieldType | None
        """
        if self.field_types:
            fts = filter_list(self.field_types, role=role, name=name)
            if len(fts) > 0:
                return fts[0]


class FieldValueInterface:
    """A common interface for things (i.e. Operations and Samples) that have
    FieldValues and FieldTypes."""

    def new_field_value_from_field_type(self, field_type, values_dict=None):
        """Instantiates a new :class:`pydent.models.FieldValue` from a.

        :class:`pydent.models.FieldType`
        instance. Optionally, a values dictionary may be provided with the following
        format:

        ::

            values_dict = {
                "value": None,
                "sample": mysample,
                "item": myitem,
                "object_type": None
            }

        :param field_type: field type to instantiate the field value
        :type field_type: FieldType
        :param values_dict: values to set the new field value
        :type values_dict: dict
        :return: the new field value
        :rtype: FieldValue
        """

        assert field_type in self.get_field_types()
        self.new_field_value(field_type.name, field_type.role, values_dict=values_dict)

    def new_field_value(self, name, role=None, values_dict=None):
        """
        Instantiates a new :class:`pydent.models.FieldValue` from a name and role.
        The should be a field type with the name and role
        in the metatype.
        Optionally, a values dictionary may be provided with the following format:

        ::

            values_dict = {
                "value": None,
                "sample": mysample,
                "item": myitem,
                "object_type": None
            }

        :param name: its name
        :type name: basestring
        :param role: its role
        :type role: basestring
        :param values_dict: values to set the new field value
        :type values_dict: dict
        :return: the new field value
        :rtype: FieldValue
        """

        # retrieve the field_type from the meta_type
        metatype = self.get_metatype()
        ft = metatype.field_type(name, role=role)

        # initialize the field_value
        fv = ft.initialize_field_value(parent=self)
        if values_dict:
            fv.set_value(**values_dict)
        # add new field_value to list of field_values
        if self.field_values is None:
            self.field_values = []

        self.field_values.append(fv)
        return fv

    def safe_get_field_type(self, fv):
        """Safely returns the field value's :class:`pydent.models.FieldType`
        from the model.

        If the field value has no reference to the field type, its
        metatype (e.g. :class:`pydent.models.SampleType` or
        :class:`pydent.models.OperationType`) is used to recover the
        field type.
        """

        def h(f):
            return "{}_%&^_{}".format(f.name, f.role)

        if fv.field_type_id is None:
            fts = self.get_field_types()
            name_role_to_ft = {h(ft): ft for ft in fts}
            ft = name_role_to_ft.get(h(fv), None)
            if ft is not None:
                fv.set_field_type(ft)
        return fv.field_type

    def get_metatype(self):
        """Returns the instance's metatype.

        The metatype is either
        :class:`pydent.models.SampleType` or
        :class:`pydent.models.OperationType`). The metatype class name is
        stored as `METATYPE` in the class definition.

        :return: the metatype
        :rtype: ModelBase
        """

        metatype = getattr(self, self.METATYPE)
        assert issubclass(type(metatype), FieldTypeInterface)
        return metatype

    def get_field_value(self, name, role=None):
        """Returns a :class:`pydent.models.FieldValue` by its name and role.

        :param name: its name
        :type name: basestring
        :param role: its role
        :type role: basestring
        :return: the field value or None if not found
        :rtype: FieldValue | None
        """

        fv_array = self.get_field_value_array(name, role=role)
        if fv_array:
            return fv_array[0]

    def get_field_value_array(self, name, role=None):
        """Returns a list of :class:`pydent.models.FieldValue` by their name
        and role.

        :param name: its name
        :type name: basestring
        :param role: its role
        :type role: basestring
        :return: list of field values
        :rtype: list
        """

        if self.field_values is None:
            return []
        fvs = []
        for fv in self.field_values:
            self.safe_get_field_type(fv)
            if fv.name == name and fv.role == role:
                self.safe_get_field_type(fv)
                fvs.append(fv)
        return fvs

    def get_field_types(self, name=None, role=None):
        """Returns a list of :class:`pydent.models.FieldType` by their name and
        role from the instance's metaclass.

        :param name: its name
        :type name: basestring
        :param role: its role
        :type role: basestring
        :return: list of field types
        :rtype: list
        """

        fts = self.get_metatype().field_types
        if name is not None:
            fts = [ft for ft in fts if ft.name == name]
        if role is not None:
            fts = [ft for ft in fts if ft.name == name]
        return fts

    def get_field_type(self, name, role):
        """Returns a :class:`pydent.models.FieldType` by its name and role from
        the instance's metaclass.

        :param name: its name
        :type name: basestring
        :param role: its role
        :type role: basestring
        :return: metatypes field type or None if not found
        :rtype: FieldType | None
        """

        fts = self.get_field_types(name, role)
        if fts:
            return fts[0]

    def _field_value_dictionary(self, ft_func=None, fv_func=None):

        if ft_func is None:

            def ft_func(ft):
                return ft.name

        if fv_func is None:

            def fv_func(fv):
                return fv

        data = {}
        ft_dict = {ft.id: ft for ft in self.get_field_types()}

        for ft in ft_dict.values():
            if ft.array:
                val = []
            else:
                val = None
            data[ft_func(ft)] = val

        # safely get field_types; field_type_id is sometimes None in Sample field_
        # values; unsure if this used to be a bug in Aquarium that has been since
        # resolved

        fvs = self.field_values
        if fvs:
            for fv in fvs:
                val = fv_func(fv)
                ft = self.safe_get_field_type(fv)
                if ft:
                    if ft.array:
                        data[ft_func(ft)].append(val)
                    else:
                        data[ft_func(ft)] = val

        return data

    def set_field_value(self, name, role, values):
        """
        Sets a field value name and role using a dictionary, as in the following:

        ::

            values = {
                "value": None,
                "sample": mysample,
                "item": myitem,
                "object_type": None
            }
        """

        ft = self.get_field_type(name, role)
        fv = self.get_field_value(name, role)
        if fv is None:
            self.new_field_value_from_field_type(ft, values)
        else:
            fv.set_value(**values)
        return self

    def set_field_value_array(self, name, role, values_array):
        """
        Sets an array of field values by name and role using an array of dictionaries,
        as in the following:

        ::

            values_array = [{
                "value": None,
                "sample": mysample,
                "item": myitem,
                "object_type": None
            }]
        """

        fvs = self.get_field_value_array(name, role)
        to_be_removed = []
        for fv, val in zip_longest(fvs, values_array):
            if fv and val:
                fv.set_value(**val)
            elif fv and not val:
                to_be_removed.append(fv)
            elif not fv and val:
                self.new_field_value(name, role, val)
        for fv in to_be_removed:
            self.field_values.remove(fv)
        return self

    def get_routing(self):
        """Returns the routing dictionary for this instance.

        :return: routing dictionary
        :rtype: dict
        """
        return self._field_value_dictionary(lambda ft: ft.routing, lambda fv: fv.sid)

    def update_field_values(self, value_dict, role=None):
        ft_dict = {ft.name: ft for ft in self.get_field_types()}

        for name, val in value_dict.items():
            ft = ft_dict[name]
            if issubclass(type(val), Sequence) and ft.array:
                self.set_field_value_array(name, role, val)
            else:
                self.set_field_value(name, role, val)
        return self
