from collections import Sequence

from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.models.field_value_mixins import FieldValueInterface, FieldTypeInterface
from pydent.relationships import (HasOne, HasMany,
                                  HasManyThrough)
from pydent.models.crud_mixin import SaveMixin

@add_schema
class Sample(FieldValueInterface, SaveMixin, ModelBase):
    """A Sample model"""
    fields = dict(
        # sample relationships
        sample_type=HasOne("SampleType"),
        items=HasMany("Item", ref="sample_id"),
        field_values=HasMany("FieldValue",
                             ref="parent_id",
                             additional_args={"parent_class": "Sample"}),

        # TODO: add new sample relationships to change log
        field_values_as_properties=HasMany("FieldValue",
                                           ref="child_sample_id",
                                           additional_args={
                                               "parent_class": "Sample"
                                           }),
        field_values_as_outputs=HasMany("FieldValue",
                                        ref="child_sample_id",
                                        additional_args={
                                            "parent_class": "Operation",
                                            "role": "output"
                                        }
                                        ),
        field_values_as_inputs=HasMany("FieldValue",
                                       ref="child_sample_id",
                                       additional_args={
                                           "parent_class": "Operation",
                                           "role": "input"
                                       }
                                       ),
        operations_as_outputs=HasManyThrough("Operation", "FieldValuesAsOutput"),
        operations_as_inputs=HasManyThrough("Operation", "FieldValuesAsInput"),
        parent_samples=HasManyThrough("Sample", "FieldValuesAsProperty")
    )

    METATYPE = "sample_type"

    def __init__(self, name=None, project=None, description=None, sample_type=None, sample_type_id=None,
                 properties=None, field_values=None):
        """

        :param name:
        :type name:
        :param project:
        :type project:
        :param description:
        :type description:
        :param sample_type_id:
        :type sample_type_id:
        :param properties:
        :type properties:
        """
        super().__init__(
            name=name,
            project=project,
            description=description,
            sample_type_id=sample_type_id,
            sample_type=sample_type,
            field_values=field_values,
            items=None,
        )
        if properties is not None:
            self.update_properties(properties)

    def postdata_hook(self):
        if self.field_values:
            for fv in self.field_values:
                self.safe_get_field_type(fv)

    @property
    def identifier(self):
        """Return the identifier used by Aquarium in autocompletes"""
        return "{}: {}".format(self.id, self.name)

    def field_value(self, name):
        """
        Returns the :class:`FieldValue` associated with the sample by its name. If the there is more than one FieldValue
        with the same name (as in field_value arrays), it will return the first FieldValue.
        See the :method:`Sample.field_value_array` method.

        :param name: name of the field value
        :type name: str
        :return: the field value
        :rtype: FieldValue
        """
        return self.get_field_value(name, None)

    def field_value_array(self, name):
        return self.get_field_value_array(name, None)

    @staticmethod
    def _property_accessor(fv):
        if fv.field_type:
            if fv.field_type.ftype == 'sample':
                return fv.sample
            else:
                return fv.value

    @property
    def properties(self):
        return self._field_value_dictionary(
            lambda ft: ft.name,
            self._property_accessor
        )

    def update_properties(self, prop_dict):
        """
        Update the FieldValues properties for this sample.

        :param prop_dict: values to update
        :type pro fp_dict: dict
        :return: self
        :rtype: Sample
        """
        ft_dict = {ft.name: ft for ft in self.get_field_types()}
        for name, val in prop_dict.items():
            ft = ft_dict[name]
            if ft.is_parameter():
                key = 'value'
            else:
                key = 'sample'
            if issubclass(type(val), Sequence) and ft.array:
                self.set_field_value_array(name, None, [{key: v} for v in val])
            else:
                self.set_field_value(name, None, {key: val})

    # def _get_create_json(self):
    #     return self.dump(include=('field_values',))
    #
    # def _get_update_json(self):
    #     return self.dump(include=('field_values',))

    def create(self):
        return self.session.utils.create_samples([self])

    def available_items(self, object_type_name=None, object_type_id=None):
        query = {"name": object_type_name, "id": object_type_id}
        query = {k: v for k, v in query.items() if v is not None}
        if query == {}:
            return [i for i in self.items if i.location != 'deleted']
        else:
            object_types = self.session.ObjectType.where(query)
            object_type = object_types[0]
            return [i for i in self.items if i.location != 'deleted' and
                    i.object_type_id == object_type.id]

    def copy(self):
        """Return a copy of this sample."""
        copied = super().copy()
        copied.anonymize()
        return copied

    def __str__(self):
        return self._to_str('id', 'name', 'sample_type')


@add_schema
class SampleType(FieldTypeInterface, SaveMixin, ModelBase):
    """A SampleType model"""
    fields = dict(
        samples=HasMany("Sample", "SampleType"),
        field_types=HasMany("FieldType", ref="parent_id", additional_args={"parent_class": "SampleType"}),

        # TODO: operation_type_afts
        # TODO: property_afts
        # TODO: add relationships description
    )

    def field_type(self, name, role=None):
        return super().field_type(name, role)

    @property
    def properties(self):
        props = {}
        for ft in self.field_types:
            if ft.ftype == 'sample':
                props[ft.name] = [str(aft) for aft in ft.allowable_field_types]
            else:
                props[ft.name] = ft.ftype
        return props

    def new_sample(self, name, description, project, properties=None):
        if properties is None:
            properties = dict()
        sample = self.session.Sample.new(
            name=name,
            sample_type=self,
            description=description,
            project=project,
            properties=properties
        )
        return sample

    def _get_update_json(self):
        return self.dump(include=('field_types',))

    def _get_create_json(self):
        return self.dump(include=('field_types',))

    def __str__(self):
        return self._to_str('id', 'name')
