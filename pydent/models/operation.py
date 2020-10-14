"""Models related to operations and operation types."""
from pydent.base import ModelBase
from pydent.exceptions import AquariumModelError
from pydent.marshaller import add_schema
from pydent.models.crud_mixin import SaveMixin
from pydent.models.data_associations import DataAssociatorMixin
from pydent.models.field_value_mixins import FieldTypeInterface
from pydent.models.field_value_mixins import FieldValueInterface
from pydent.relationships import Function
from pydent.relationships import HasMany
from pydent.relationships import HasManyGeneric
from pydent.relationships import HasManyThrough
from pydent.relationships import HasOne
from pydent.relationships import HasOneFromMany
from pydent.relationships import Raw
from pydent.utils import filter_list


@add_schema
class Operation(FieldValueInterface, DataAssociatorMixin, ModelBase):
    """A Operation model."""

    fields = dict(
        field_values=HasMany(
            "FieldValue", ref="parent_id", additional_args={"parent_class": "Operation"}
        ),
        data_associations=HasManyGeneric(
            "DataAssociation", additional_args={"parent_class": "Operation"}
        ),
        operation_type=HasOne("OperationType"),
        job_associations=HasMany("JobAssociation", "Operation"),
        jobs=HasManyThrough("Job", "JobAssociation"),
        plan_associations=HasMany("PlanAssociation", "Operation"),
        plans=HasManyThrough("Plan", "PlanAssociation"),
        status=Raw(default="planning"),
        routing=Function("get_routing"),
        user=HasOne("User"),
    )

    METATYPE = "operation_type"

    def __init__(
        self, operation_type_id=None, operation_type=None, status=None, x=0, y=0
    ):
        super().__init__(
            operation_type_id=operation_type_id,
            operation_type=operation_type,
            status=status,
            field_values=None,
            x=x,
            y=y,
        )

    def get_routing(self):
        routing_dict = {}
        fvs = self.field_values
        ot = self.operation_type
        if ot is None:
            return routing_dict
        for ft in ot.field_types:
            if ft.routing is not None:
                routing_dict[ft.routing] = None
        if fvs is not None:
            for fv in self.field_values:
                ft = self.safe_get_field_type(fv)
                if ft.routing is not None:
                    routing_dict[ft.routing] = fv.sid
        return routing_dict

    @property
    def successors(self):
        successors = []
        if self.outputs:
            for output in self.outputs:
                for s in output.successors:
                    successors.append(s.operation)
        return successors

    @property
    def predecessors(self):
        predecessors = []
        if self.inputs:
            for inputs in self.inputs:
                for s in inputs.predecessors:
                    predecessors.append(s.operation)
        return predecessors

    def init_field_values(self):
        """Initialize the :class:`FieldValue` from the :class:`FieldType` of
        the parent :class:`Operation` type."""
        self.field_values = []
        for field_type in self.get_metatype().field_types:
            if not field_type.array:
                self.new_field_value_from_field_type(field_type)
        return self

    def field_value_array(self, name, role):
        """Returns :class:`FieldValue` array with name and role."""
        return filter_list(self.get_field_value_array(name, role))

    def field_value(self, name, role):
        """Returns :class:`FieldValue` with name and role.

        Return None if not found.
        """
        if self.field_values:
            fvs = self.field_value_array(name, role)

            if len(fvs) == 0:
                return None

            if len(fvs) == 1:
                return fvs[0]

            msg = "More than one FieldValue found for the field value"
            msg += (
                " of operation {}.(id={}).{}.{}. Are you sure you didn't mean to "
                "call 'field_value_array'?"
            )
            raise AquariumModelError(
                msg.format(self.operation_type, self.id, role, name)
            )

    @property
    def plan(self):
        return self.plans[0]

    def input_array(self, name):
        return self.get_field_value_array(name, "input")

    def output_array(self, name):
        return self.get_field_value_array(name, "output")

    def input(self, name):
        """Returns the input :class:`FieldValue` by name."""
        return self.field_value(name, "input")

    def output(self, name):
        """Returns the output :class:`FieldValue` by name."""
        return self.field_value(name, "output")

    def add_to_input_array(
        self, name, sample=None, item=None, value=None, container=None
    ):
        """Creates and adds a new input :class:`FieldValue`. When setting
        values to items/samples/containers, the item/sample/container must be
        saved.

        :param name: name of the FieldType/FieldValue
        :type name: string
        :param sample: an existing Sample
        :type sample: Sample
        :param item: an existing Item
        :type item: Item
        :param value: a string or number value
        :type value: string|integer
        :param container: an existing ObjectType
        :type container: ObjectType
        :return: the newly created FieldValue
        :rtype: FieldValue
        """
        return self.new_field_value(
            name,
            "input",
            dict(sample=sample, item=item, value=value, container=container),
        )

    def add_to_output_array(
        self, name, sample=None, item=None, value=None, container=None
    ):
        """Creates and adds a new output :class:`FieldValue`. When setting
        values to items/samples/containers, the item/sample/container must be
        saved.

        :param name: name of the FieldType/FieldValue
        :type name: string
        :param sample: an existing Sample
        :type sample: Sample
        :param item: an existing Item
        :type item: Item
        :param value: a string or number value
        :type value: string|integer
        :param container: an existing ObjectType
        :type container: ObjectType
        :return: the newly created FieldValue
        :rtype: FieldValue
        """
        return self.new_field_value(
            name,
            "output",
            dict(sample=sample, item=item, value=value, container=container),
        )

    @property
    def inputs(self):
        """Return a list of all input :class:`FieldValues`"""
        return [fv for fv in self.field_values if fv.role == "input"]

    @property
    def outputs(self):
        """Return a list of all output :class:`FieldValues`"""
        return [fv for fv in self.field_values if fv.role == "output"]

    def set_input(
        self, name, sample=None, item=None, value=None, container=None, object_type=None
    ):
        """Sets a input :class:`FieldValue` to a value. When setting values to
        items/samples/containers, the item/sample/container must be saved.

        :param name: name of the FieldValue/FieldType
        :type name: string
        :param sample: an existing Sample
        :type sample: Sample
        :param item: an existing Item
        :type item: Item
        :param value: a string or number value
        :type value: string|integer
        :param container: an existing ObjectType
        :type container: ObjectType
        :return: the existing FieldValue modified
        :rtype: FieldValue
        """
        if object_type is None and container:
            object_type = container
        return self.set_field_value(
            name,
            "input",
            dict(sample=sample, item=item, value=value, object_type=container),
        )

    def set_output(
        self, name, sample=None, item=None, value=None, container=None, object_type=None
    ):
        """Sets a output :class:`FieldValue` to a value. When setting values to
        items/samples/containers, the item/sample/container must be saved.

        :param name: name of the FieldValue/FieldType
        :type name: string
        :param sample: an existing Sample
        :type sample: Sample
        :param item: an existing Item
        :type item: Item
        :param value: a string or number value
        :type value: string|integer
        :param container: an existing ObjectType
        :type container: ObjectType
        :return: the existing FieldValue modified
        :rtype: FieldValue
        """
        if object_type is None and container:
            object_type = container
        return self.set_field_value(
            name,
            "output",
            dict(sample=sample, item=item, value=value, object_type=object_type),
        )

    def set_input_array(self, name, values):
        """Sets input :class:`FieldValue` array using values. Values should be
        a list of dictionaries containing sample, item, container, or values
        keys. When setting values to items/samples/containers, the
        item/sample/container must be saved.

        :param name: name of the FieldType/FieldValues being modified
        :type name: string
        :param values: list of dictionary of values to set
                (e.g. [{"sample": mysample}, {"item": myitem}])
        :type values: list
        :return: the list of modified FieldValues
        :rtype: list
        """
        return self.set_field_value_array(name, "input", values)

    def set_output_array(self, name, values):
        """Sets output :class:`FieldValue` array using values. Values should be
        a list of dictionaries containing sample, item, container, or values
        keys. When setting values to items/samples/containers, the
        item/sample/container must be saved.

        :param name: name of the FieldType/FieldValues being modified
        :type name: string
        :param values: list of dictionary of values to set
                (e.g. [{"sample": mysample}, {"item": myitem}])
        :type values: list
        :return: the list of modified FieldValues
        :rtype: list
        """
        return self.set_field_value_array(name, "output", values)

    def show(self, pre=""):
        """Print the operation nicely."""
        print(pre + self.operation_type.name + " " + str(self.cost))
        for field_value in self.field_values:
            field_value.show(pre=pre + "  ")

    def __str__(self):
        return self._to_str(operation_type_name=self.operation_type.name)


@add_schema
class OperationType(FieldTypeInterface, SaveMixin, ModelBase):
    """Represents an OperationType, which is the definition of a protocol in
    Aquarium."""

    fields = dict(
        operations=HasMany("Operation", "OperationType"),
        field_types=HasMany(
            "FieldType",
            ref="parent_id",
            additional_args={"parent_class": "OperationType"},
        ),
        codes=HasManyGeneric("Code"),
        cost_model=HasOneFromMany(
            "Code",
            ref="parent_id",
            additional_args={"parent_class": "OperationType", "name": "cost_model"},
        ),
        documentation=HasOneFromMany(
            "Code",
            ref="parent_id",
            additional_args={"parent_class": "OperationType", "name": "documentation"},
        ),
        precondition=HasOneFromMany(
            "Code",
            ref="parent_id",
            additional_args={"parent_class": "OperationType", "name": "precondition"},
        ),
        protocol=HasOneFromMany(
            "Code",
            ref="parent_id",
            additional_args={"parent_class": "OperationType", "name": "protocol"},
        ),
        test=HasOneFromMany(
            "Code",
            ref="parent_id",
            additional_args={"parent_class": "OperationType", "name": "test"},
        ),
    )

    def code(self, accessor):
        if accessor in [
            "protocol",
            "precondition",
            "documentation",
            "cost_model",
            "test",
        ]:
            return getattr(self, accessor)
        return None

    def instance(self, xpos=0, ypos=0):
        operation = self.session.Operation.new(
            operation_type_id=self.id, status="planning", x=xpos, y=ypos
        )
        operation.operation_type = self
        operation.init_field_values()
        return operation

    def field_type(self, name, role):
        if self.field_types:
            fts = filter_list(self.field_types, role=role, name=name)
            if len(fts) > 0:
                return fts[0]

    def sample_type(self):
        sample_types = []
        for field_type in self.field_types:
            for allowable_field_type in field_type.allowable_field_types:
                sample_types.append(allowable_field_type.sample_type)
        return sample_types

    def object_type(self):
        object_types = []
        for field_type in self.field_types:
            for allowable_field_type in field_type.allowable_field_types:
                object_types.append(allowable_field_type.object_type)
        return object_types

    def output(self, name):
        return self.field_type(name, "output")

    def input(self, name):
        return self.field_type(name, "input")

    def save(self):
        """Saves the Operation Type to the Aquarium server.

        Requires this Operation Type to be connected to a session.
        """
        return self.reload(self.session.utils.create_operation_type(self))

    def to_save_json(self):
        op_data = self.dump(
            include={
                "field_types": {"allowable_field_types": {}},
                "protocol": {},
                "cost_model": {},
                "documentation": {},
                "precondition": {},
                "test": {},
            }
        )

        # Format 'sample_type' and 'object_type' keys for afts
        for ft_d, ft in zip(op_data["field_types"], self.field_types):
            for aft_d, aft in zip(
                ft_d["allowable_field_types"], ft.allowable_field_types
            ):
                aft_d["sample_type"] = {"name": aft.sample_type.name}
                aft_d["object_type"] = {"name": aft.object_type.name}
        return op_data

    def _get_create_json(self):
        return self.to_save_json()

    def _get_update_json(self):
        return self.to_save_json()

    def __str__(self):
        return self._to_str("id", "name", "category")
