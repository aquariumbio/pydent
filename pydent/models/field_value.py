"""Models related to field values and sample properties."""
import json
from warnings import warn

from pydent.base import ModelBase
from pydent.exceptions import AquariumModelError
from pydent.exceptions import TridentDepreciationWarning
from pydent.marshaller import add_schema
from pydent.models.crud_mixin import JSONDeleteMixin
from pydent.models.crud_mixin import JSONSaveMixin
from pydent.models.field_value_mixins import FieldMixin
from pydent.models.inventory import Collection
from pydent.models.inventory import Item
from pydent.models.inventory import ObjectType
from pydent.models.sample import Sample
from pydent.relationships import fields
from pydent.relationships import Function
from pydent.relationships import HasMany
from pydent.relationships import HasOne
from pydent.relationships import Raw
from pydent.utils import filter_list


class NullType:
    class __NullType:
        def __bool__(self):
            return False

    instance = None

    def __new__(cls):
        if NullType.instance is None:
            NullType.instance = NullType.__NullType()
        return NullType.instance

    def __bool__(self):
        return False


Null = NullType()


@add_schema
class AllowableFieldType(ModelBase):
    """A AllowableFieldType model."""

    fields = dict(
        field_type=HasOne("FieldType"),
        object_type=HasOne("ObjectType"),
        sample_type=HasOne("SampleType"),
    )

    def __init__(self, field_type=None, object_type=None, sample_type=None):
        super().__init__(
            field_type_id=None,
            sample_type_id=None,
            object_type_id=None,
            field_type=field_type,
            object_type=object_type,
            sample_type=sample_type,
        )

    def __str__(self):
        return self._to_str("sample_type", "object_type")


@add_schema
class FieldType(FieldMixin, ModelBase):
    """A FieldType model."""

    fields = dict(
        allowable_field_types=HasMany("AllowableFieldType", "FieldType"),
        operation_type=HasOne(
            "OperationType", callback="find_field_parent", ref="parent_id"
        ),
        sample_type=HasOne("SampleType", callback="find_field_parent", ref="parent_id"),
        field_values=HasMany("FieldValue", "FieldType"),
    )

    def __init__(
        self,
        name=None,
        ftype=None,
        array=None,
        choices=None,
        operation_type=None,
        preferred_field_type_id=None,
        preferred_operation_type_id=None,
        required=None,
        routing=None,
        role=None,
        parent_class=None,
        parent_id=None,
        sample_type=None,
        aft_stype_and_objtype=(),
        allowable_field_types=None,
    ):
        if operation_type and sample_type:
            raise AquariumModelError(
                "Cannot instantiate a FieldType for both a OperationType and SampleType."
            )
        if operation_type:
            parent_class = "OperationType"
        if sample_type:
            parent_class = "SampleType"
        super().__init__(
            name=name,
            ftype=ftype,
            array=array,
            choices=choices,
            role=role,
            preferred_field_type_id=preferred_field_type_id,
            preferred_operation_type_id=preferred_operation_type_id,
            required=required,
            routing=routing,
            parent_class=parent_class,
            parent_id=parent_id,
            sample_type=sample_type,
            operation_type=operation_type,
            allowable_field_types=allowable_field_types,
        )
        self.part = None
        if allowable_field_types is None:
            if aft_stype_and_objtype is not None:
                for smple_type, obj_type in aft_stype_and_objtype:
                    self.create_allowable_field_type(smple_type, obj_type)

    def get_choices(self):
        if self.choices == "":
            return None
        if self.choices is not None:
            return self.choices.split(",")

    def is_parameter(self):
        return self.ftype != "sample"

    def get_allowable_field_types(self, sample_type_id=None, object_type_id=None):
        afts = self.allowable_field_types
        if afts is None or afts == []:
            self.allowable_field_types = None
            afts = self.allowable_field_types
        return filter_list(
            afts, sample_type_id=sample_type_id, object_type_id=object_type_id
        )

    def create_allowable_field_type(self, sample_type=None, object_type=None):
        afts = []
        if self.allowable_field_types:
            afts = self.allowable_field_types
        field_type = self.session.AllowableFieldType.new(
            field_type=self, sample_type=sample_type, object_type=object_type
        )
        afts.append(field_type)
        self.allowable_field_types = afts
        return field_type

    def initialize_field_value(self, field_value=None, parent=None):
        """Updates or initializes a new :class:`FieldValue` from this
        FieldType.

        :param field_value: optional FieldValue to update with this FieldType
        :type field_value: FieldValue
        :return: updated FieldValue
        :rtype: FieldValue
        """

        if not field_value:
            field_value = self.session.FieldValue.new(
                name=self.name, role=self.role, field_type=self
            )
        if self.allowable_field_types:
            field_value.allowable_field_type_id = self.allowable_field_types[0].id
            field_value.allowable_field_type = self.allowable_field_types[0]
        if parent:
            field_value.set_parent(parent)
        return field_value


@add_schema
class FieldValue(FieldMixin, JSONSaveMixin, JSONDeleteMixin, ModelBase):
    """A FieldValue model. One of the more complex models.

    .. versionchanged:: 0.1.2     FieldValues no longer
    have'wires_as_source' or 'wires_as_dest' fields.    Wires may only
    be accessed via plans only or via the FieldValue instance method
    'get_wires,' which accesses the FieldValues operation and its Plan
    to obtain wires.
    """

    fields = dict(
        # FieldValue relationships
        field_type=HasOne("FieldType"),
        allowable_field_type=HasOne("AllowableFieldType"),
        array=fields.Field(),
        # array=Function(lambda fv: fv.array, callback_args=(fields.Callback.SELF,)),
        item=HasOne("Item", ref="child_item_id"),
        sample=HasOne("Sample", ref="child_sample_id"),
        object_type_id=Raw(),
        object_type=HasOne("ObjectType"),
        operation=HasOne("Operation", callback="find_field_parent", ref="parent_id"),
        parent_sample=HasOne("Sample", callback="find_field_parent", ref="parent_id"),
        sid=Function("get_sid"),
        child_sample_name=Function(
            lambda fv: fv.sid, callback_args=(fields.Callback.SELF,)
        ),
        wires_as_source=HasMany("Wire", ref="from_id"),
        wires_as_dest=HasMany("Wire", ref="to_id"),
        # allowable_child_types=Function('get_allowable_child_types'),
    )

    METATYPE = "field_type"

    def __init__(
        self,
        name=None,
        role=None,
        parent_class=None,
        parent_id=None,
        field_type=None,
        sample=None,
        value=None,
        item=None,
        container=None,
    ):
        """

        :param value:
        :type value:
        :param sample:
        :type sample:
        :param container:
        :type container:
        :param item:
        :type item:
        """
        super().__init__(
            name=name,
            role=role,
            parent_class=parent_class,
            parent_id=parent_id,
            field_type_id=None,
            field_type=field_type,
            child_sample_id=None,
            sample=sample,
            value=value,
            child_item_id=None,
            item=item,
            object_type=container,
            allowable_field_type_id=None,
            allowable_field_type=None,
            column=0,
            row=0,
        )

        if field_type is not None:
            self.set_field_type(field_type)

        if any([value, sample, item, container]):
            self._set_helper(
                value=value, sample=sample, item=item, object_type=container
            )

        if self.parent_class == "Operation" and not self.role:
            raise AquariumModelError(
                "FieldValue {} needs a role to be a field value for an operation".format(
                    self
                )
            )

    def get_sid(self):
        """The FieldValues sample identifier."""
        if self.sample is not None:
            return self.sample.identifier

    def get_wires(self):
        if not self.role or self.parent_class != "Operation":
            return None
        elif self.operation and self.operation.plan:
            wires = self.operation.plan.wires
            if self.role == "input":
                return [w for w in wires if w.does_wire_to(self)]
            elif self.role == "output":
                return [w for w in wires if w.does_wire_from(self)]
        return []

    @property
    def incoming_wires(self):
        if self.role == "input":
            self.get_wires()
        return []

    @property
    def outgoing_wires(self):
        if self.role == "output":
            self.get_wires()
        return []

    @property
    def successors(self):
        if self.outgoing_wires:
            return [x.destination for x in self.outgoing_wires]
        return []

    @property
    def predecessors(self):
        if self.incoming_wires:
            return [x.source for x in self.incoming_wires]
        return []

    def show(self, pre=""):
        if self.sample:
            if self.child_item_id:
                item = " item: {}".format(self.child_item_id) + " in {}".format(
                    self.item.object_type.name
                )
            else:
                item = ""
            print(
                "{}{}.{}:{}{}".format(pre, self.role, self.name, self.sample.name, item)
            )
        elif self.value:
            print("{}{}.{}:{}".format(pre, self.role, self.name, self.value))

    def reset(self):
        """Resets the inputs of the field_value."""
        self.value = None
        self.allowable_field_type_id = None
        self.allowable_field_type = None
        self.child_item_id = None
        self.item = None
        self.child_sample_id = None
        self.sample = None
        self.row = None
        self.column = None

    def _validate_types(self, name, x, expected_types):
        if x is not None and not any([issubclass(type(x), e) for e in expected_types]):
            raise AquariumModelError(
                "Cannot set FieldValue.{} with a {}. Expected types {}".format(
                    name, type(x), expected_types
                )
            )

    def _validate_value(self, value):
        if value is not None:
            choices = self.field_type.get_choices()
            if choices is not None:
                if value not in choices and str(value) not in choices:
                    raise AquariumModelError(
                        "Value '{}' not in list of field "
                        "type choices '{}'".format(value, choices)
                    )
        try:
            json.dumps(value)
        except TypeError as e:
            raise AquariumModelError(
                "Cannot set value '{}'. "
                "Value is not json serializable.".format(value)
            ) from e

    def _validate_item_and_container(self, item, container):
        self._validate_types("item", item, [Item, Collection])
        self._validate_types("container", container, [ObjectType])
        if item and container and item.object_type_id != container.id:
            raise AquariumModelError(
                "Item {} is not in container {}".format(item.id, str(container))
            )

    def _validate_sample(self, sample):
        self._validate_types("sample", sample, [Sample])
        if sample is not None and not issubclass(type(sample), Sample):
            raise AquariumModelError(
                "Cannot set sample with a type '{}'".format(type(sample))
            )

    def _validate_sample_and_item(self, sample, item):
        if sample and hasattr(sample, "id") and item:
            if not item.sample_id == sample.id:
                raise AquariumModelError(
                    "Cannot set FieldValue {}. Item {} is not a member of sample {}".format(
                        self, item, sample
                    )
                )

    def _validate_row_or_column(self, dim: int):
        if dim and not isinstance(dim, int):
            raise AquariumModelError("Row and columns must be integers not.")
        if dim is not None:
            if not self.field_type.part:
                raise AquariumModelError(
                    "Cannot set dimensions of a non-part for {} {}".format(
                        self.role, self.name
                    )
                )

    def _validate(self, value, sample, item, object_type, row, column):
        if row is not Null:
            self._validate_row_or_column(row)
        if column is not Null:
            self._validate_row_or_column(column)
        if value is not Null:
            self._validate_value(value)
        if sample is not Null:
            self._validate_sample(sample)

        if sample is Null and item is not Null:
            self._validate_sample_and_item(self.sample, item)
        if sample is not Null and item is not Null:
            self._validate_sample_and_item(sample, item)

        if item is Null and object_type is not Null:
            self._validate_item_and_container(self.item, object_type)
        if item is not Null and object_type is Null:
            self._validate_item_and_container(item, self.object_type)
        if item is not Null and object_type is not Null:
            self._validate_item_and_container(item, object_type)

    def _set_helper(
        self,
        value=Null,
        sample=Null,
        item=Null,
        object_type=Null,
        row=Null,
        column=Null,
    ):
        self._validate(value, sample, item, object_type, row, column)
        if row is not Null:
            self.row = row
        if column is not Null:
            self.column = column

        if value is not Null:
            self.value = value

        if item is not Null:
            self.item = item
            if hasattr(item, "id"):
                self.child_item_id = item.id
            if item and not sample:
                sample = item.sample
        if sample is not Null:
            self.sample = sample
            if hasattr(sample, "id"):
                self.child_sample_id = sample.id
        if object_type is not Null:
            self.object_type = object_type

    def valid_afts(self):
        afts = self.field_type.allowable_field_types
        if self.sample is not None:
            afts = filter_list(afts, sample_type_id=self.sample.sample_type_id)
        if self.object_type is not None:
            afts = filter_list(afts, object_type_id=self.object_type.id)
        if self.item is not None and self.item.object_type_id is not None:
            afts = filter_list(afts, object_type_id=self.item.object_type_id)
        return afts

    def _raise_aft_error(self):
        aft_list = []
        for aft in self.field_type.allowable_field_types:
            st = "none"
            ot = "none"
            if aft.object_type is not None:
                ot = aft.object_type.name
            if aft.sample_type is not None:
                st = aft.sample_type.name
            aft_list.append("{}:{}".format(st, ot))
        sid = "none"
        if self.sample is not None:
            sid = self.sample.sample_type.name
        oid = "none"
        if self.object_type is not None:
            oid = self.object_type.name
        msg = "No allowable field types found for {}:{}:{} using {}:{}."
        msg += " Available afts: {}"
        try:
            otname = self.operation.operation_type.name
        except AttributeError:
            otname = None
        raise AquariumModelError(
            msg.format(otname, self.role, self.name, sid, oid, ", ".join(aft_list))
        )

    def set_aft(self):
        afts = self.valid_afts()
        if len(afts) >= 1:
            self.set_allowable_field_type(afts[0])
        else:
            self._raise_aft_error()

    def set_value(
        self,
        value=Null,
        sample=Null,
        item=Null,
        object_type=Null,
        row=Null,
        column=Null,
        container=Null,
    ):
        if object_type and container:
            raise ValueError(
                "object_type and container (depreciated) cannot be "
                "both defined. Please define 'object_type'."
            )
        if container:
            warn(
                TridentDepreciationWarning(
                    "Use of 'container' is depreciated."
                    " Please use 'object_type' instead"
                )
            )
        if not object_type and container:
            object_type = container

        self._validate(value, sample, item, container, row, column)
        self._set_helper(
            value=value,
            sample=sample,
            item=item,
            object_type=object_type,
            row=row,
            column=column,
        )

        """Sets the value of a """
        if any([sample, object_type, item]):
            self.set_aft()
        return self

    def get_parent_key(self):
        if self.parent_class == "Operation":
            return "operation"
        elif self.parent_class == "Sample":
            return "parent_sample"
        else:
            raise AquariumModelError(
                "Parent class '{}' not recognized as a FieldValue parent.".format(
                    self.parent_class
                )
            )

    def get_parent(self):
        key = self.get_parent_key()
        return getattr(self, key)

    def set_parent(self, model):
        self.parent_id = model.id
        self.parent_class = model.__class__.__name__
        setattr(self, self.get_parent_key(), model)
        return self

    def set_operation(self, operation):
        self.parent_class = "Operation"
        if hasattr(operation, "id"):
            self.parent_id = operation.id
        self.operation = operation

    def set_sample(self, sample):
        self.parent_class = "Sample"
        if hasattr(sample, "id"):
            self.parent_id = sample.id
        self.sample = sample

    def set_field_type(self, field_type):
        """Sets properties from a field_type."""

        self.field_type = field_type
        self.field_type_id = field_type.id

        if field_type.name:
            self.name = field_type.name
        if field_type.parent_class:
            if field_type.parent_class == "OperationType":
                self.parent_class = "Operation"
            elif field_type.parent_class == "SampleType":
                self.parent_class = "Sample"
            else:
                raise AquariumModelError(
                    "FieldType parent_class '{}' not recognized".format(
                        field_type.parent_class
                    )
                )
        if field_type.role:
            self.role = field_type.role

    def set_allowable_field_type(self, allowable_field_type):
        self.allowable_field_type = allowable_field_type
        self.allowable_field_type_id = allowable_field_type.id

    def choose_item(self, first=True):
        """Set the item associated with the field value."""
        index = 0
        if not first:
            index = -1
        items = self.compatible_items()
        if items is not None and len(items) > 0:
            item = items[index]
            self.set_value(item=item)
            return item
        return None

    def compatible_items(self):
        """Find items compatible with the field value."""
        return self.session.utils.compatible_items(
            self.sample.id, self.allowable_field_type.object_type_id
        )

    def __str__(self):
        return self._to_str("id", "name", "role")
