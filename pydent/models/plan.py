"""Models related to plans, plan associations, and wires."""
import json
from warnings import warn

from pydent.base import ModelBase
from pydent.exceptions import AquariumModelError
from pydent.marshaller import add_schema
from pydent.models.crud_mixin import DeleteMixin
from pydent.models.crud_mixin import SaveMixin
from pydent.models.data_associations import DataAssociatorMixin
from pydent.models.data_associations import Upload
from pydent.models.field_value import FieldValue
from pydent.relationships import HasMany
from pydent.relationships import HasManyGeneric
from pydent.relationships import HasManyThrough
from pydent.relationships import HasOne
from pydent.relationships import JSON
from pydent.relationships import Many
from pydent.relationships import Raw


@add_schema
class Plan(DataAssociatorMixin, SaveMixin, DeleteMixin, ModelBase):
    """A Plan model."""

    fields = dict(
        data_associations=HasManyGeneric(
            "DataAssociation", additional_args={"parent_class": "Plan"}
        ),
        plan_associations=HasMany("PlanAssociation", "Plan"),
        operations=HasManyThrough("Operation", "PlanAssociation"),
        wires=Many("Wire", callback="_get_wires_from_server"),
        layout=JSON(),
        status=Raw(default="planning"),
        user=HasOne("User"),
    )
    query_hook = {"include": ["plan_associations", "operations"]}

    def __init__(self, name="MyPlan", status="planning"):
        super().__init__(
            name=name,
            status=status,
            data_associations=None,
            plan_associations=None,
            layout={
                "id": 0,
                "children": [],
                "documentation": "No documentation of this module",
                "height": 60,
                "input": [],
                "output": [],
                "name": "no_name",
                "parent_id": -1,
                "width": 160,
                "wires": [],
            },
        )

    def add_operation(self, operation):
        """Adds an operation to the Plan.

        :param operation: Operation to add
        :type operation: Operation
        :return: None
        :rtype: None
        """
        self.append_to_many("operations", operation)

    def add_operations(self, operations):
        """Adds multiple operations to the Plan.

        :param operations: list of Operations
        :type operations: list
        :return: None
        :rtype: None
        """
        for operation in operations:
            self.add_operation(operation)

    # TODO: this is not functional or not needed
    # def has_operation(self, op):
    #     if op is None:
    #         return False
    #     return self.operations and op.rid in [_op.rid for _op in self.operations]

    def find_wires(self, src, dest):
        """Retrieves the wire between a source and destination FieldValues.

        :param src: source FieldValue
        :type src: FieldValue
        :param dest: destination FieldValue
        :type dest: FieldValue
        :return: array of wires between src and dest FieldValues (determined by rid)
        :rtype: array of wires
        """

        found = []
        for wire in self.wires:
            if src.rid == wire.source.rid and dest.rid == wire.destination.rid:
                found.append(wire)
        return found

    def wire(self, src, dest):
        """Creates a new wire between src and dest FieldValues. Returns the new
        wire if it does not exist in the plan. If the wire already exists and
        error_if_exists is True, then the existing wire is returned. Else an
        exception is raised.

        :param src: source field value (the input of the wire)
        :type src: FieldValue
        :param dest: destination field value (the output of the wire)
        :type dest: FieldValue
        :param error_if_exists: Raise an error if the Wire already exists in the plan.
        :type error_if_exists: boolean
        :return: Newly created wire or existing wire (if exists and
            error_if_exists == False)
        :rtype: Wire
        """

        # TODO: these checks are unnecessary?
        # if not self.has_operation(src.operation):
        #     raise AquariumModelError(
        #         "Cannot wire because the wire's source FieldValue {} does "
        #         "not exist in the Plan because its Operation '{}' is not in the plan".format(
        #             src, src.operation
        #         )
        #     )
        # if not self.has_operation(dest.operation):
        #     raise AquariumModelError(
        #         "Cannot wire because the wire's destination FieldValue {} does not "
        #         "exist in the Plan because its Operation '{}' is not in the plan.".format(
        #             dest, dest.operation
        #         )
        #     )

        wire = Wire(source=src, destination=dest)
        self.append_to_many("wires", wire)
        return wire

    def _collect_wires(self):
        incoming_wires = []
        outgoing_wires = []
        if self.operations:
            for operation in self.operations:
                if operation.field_values:
                    for field_value in operation.field_values:
                        if field_value.outgoing_wires:
                            outgoing_wires += field_value.outgoing_wires
                        if field_value.incoming_wires:
                            incoming_wires += field_value.incoming_wires
        return incoming_wires, outgoing_wires

    def _get_wire_dict(self, wires):
        """Return all wires in the plan grouped by the wire identifier."""
        wire_dict = {}
        for w in wires:
            wire_dict.setdefault(w.identifier, list())
            if w not in wire_dict[w.identifier]:
                wire_dict[w.identifier].append(w)
        return wire_dict

    def _get_wires_from_server(self, *args):
        fvs = []
        if self.operations:
            for op in self.operations:
                fvs += op.field_values

        fv_ids = [fv.id for fv in fvs if fv.id is not None]
        wires_from_server = []
        if fv_ids:
            wires_from_server = self.session.Wire.where(
                {"from_id": fv_ids, "to_id": fv_ids}
            )
        return wires_from_server

    def submit(self, user, budget):
        """Submits the Plan to the Aquarium server.

        :param user: User to submit the Plan
        :type user: User
        :param budget: Budget to use for the Plan
        :type budget: Budget
        :return: JSON
        :rtype: dict
        """
        result = self.session.utils.submit_plan(self, user, budget)
        return result

    def all_data_associations(self):
        das = self.data_associations
        for operation in self.operations:
            das += operation.data_associations
            for field_value in operation.field_values:
                if field_value.item:
                    das += field_value.item.data_associations
        return das

    @classmethod
    def interface(cls, session):
        # get model interface from Base class
        model_interface = super().interface(session)

        # make a special find method for plans, as generic method is too minimal.
        def new_find(model_id):
            return model_interface.get("plans/{}.json".format(model_id))

        # override the old find method
        model_interface.find = new_find

        return model_interface

    def validate(self, raise_error=True):
        """Validates the plan.

        :param raise_error: If True, raises an AquariumModelException. If false,
            returns the error messages.
        :type raise_error: boolean
        :return: list of error messages
        :rtype: array
        """
        errors = []

        field_values = []
        for op in self.operations:
            for fv in op.field_values:
                field_values.append(fv)
        fv_keys = [fv._primary_key for fv in field_values]
        for wire in self.wires:
            for _fvtype in ["source", "destination"]:
                field_value = getattr(wire, _fvtype)
                if field_value._primary_key not in fv_keys:
                    msg = (
                        "The FieldValue of a wire Wire(rid={}).{} is missing from the "
                        "list of FieldValues in the plan. Did you forget to add an "
                        "operation to the plan?".format(wire._primary_key, _fvtype)
                    )
                    errors.append(msg)
        if raise_error and errors:
            msg = "\n".join(
                ["(ErrNo {}) - {}".format(i, e) for i, e in enumerate(errors)]
            )
            raise AquariumModelError(
                "Plan {} had the following errors:\n{}".format(self, msg)
            )
        return errors

    def to_save_json(self):
        """Returns the json representation of the plan for saving and creating
        Plans on the Aquarium server.

        :return: JSON
        :rtype: dict
        """
        if not self.operations:
            self.operations = []

        if not self.wires:
            self.wires = []

        self.validate(raise_error=True)

        for op in self.operations:
            op.field_values

        json_data = self.dump(
            include={"operations": {"field_values": ["sample", "item"]}}
        )

        # remove redundant wires
        wire_dict = {}
        for wire in self.wires:
            wire_data = wire.to_save_json()
            attributes = [
                wire_data["from_id"],
                wire_data["from"]["rid"],
                wire_data["to_id"],
                wire_data["to"]["rid"],
            ]
            wire_hash = "*&".join([str(a) for a in attributes])
            wire_dict[wire_hash] = wire_data
        json_data["wires"] = list(wire_dict.values())

        # validate
        fv_rids = []
        fv_id_to_rids = {}
        for op in json_data["operations"]:
            for fv in op["field_values"]:
                if fv["id"]:
                    fv_id_to_rids[fv["id"]] = fv["rid"]
                fv_rids.append(fv["rid"])

        # fix json rids and ids
        warnings = []
        for wire_data in json_data["wires"]:
            if wire_data["from_id"] in fv_id_to_rids:
                wire_data["from"]["rid"] = fv_id_to_rids[wire_data["from_id"]]
            if wire_data["to_id"] in fv_id_to_rids:
                wire_data["to"]["rid"] = fv_id_to_rids[wire_data["to_id"]]
            if not wire_data["from"]["rid"] in fv_rids:
                warnings.append(
                    "FieldValue rid={} is missing.".format(wire_data["from"]["rid"])
                )
            if not wire_data["to"]["rid"] in fv_rids:
                warnings.append(
                    "FieldValue rid={} is missing.".format(wire_data["to"]["rid"])
                )
        if warnings:
            print(fv_rids)
            warn(",".join(warnings))

        if json_data["layout"] is not None:
            json_data["layout"] = json.loads(json_data["layout"])
        else:
            del json_data["layout"]

        return json_data

    def _get_create_json(self):
        return self.to_save_json()

    def _get_update_json(self):
        return self.to_save_json()

    def _get_create_params(self):
        return {"user_id": self.session.current_user.id}

    def _get_update_params(self):
        return {"user_id": self.session.current_user.id}

    def estimate_cost(self):
        """Estimates the cost of the plan on the Aquarium server. This is
        necessary before plan submission.

        :return: cost
        :rtype: dict
        """
        return self.session.utils.estimate_plan_cost(self)

    def field_values(self):
        raise NotImplementedError()

    def step(self):
        """Steps a plan."""
        return self.session.utils.step_plan(self.id)

    def show(self):
        """Print the plan nicely."""
        print(self.name + " id: " + str(self.id))
        for operation in self.operations:
            operation.show(pre="  ")
        for wire in self.wires:
            wire.show(pre="  ")

    def replan(self):
        """Copies or replans the plan.

        Returns a plan copy
        """
        return self.session.utils.replan(self.id)

    def download_files(self, outdir=None, overwrite=True):
        """Downloads all uploads associated with the plan. Downloads happen
        ansynchrounously.

        :param outdir: output directory for downloaded files
        :param overwrite: whether to overwrite files if they exist
        :return: None
        """
        uploads = []
        for da in self.data_associations:
            if da.upload is not None:
                uploads.append(da.upload)
        return Upload.async_download(uploads, outdir, overwrite)


@add_schema
class PlanAssociation(ModelBase):
    """A PlanAssociation model."""

    fields = dict(plan=HasOne("Plan"), operation=HasOne("Operation"))

    def __init__(self, plan_id=None, operation_id=None):
        super().__init__(plan_id=plan_id, operation_id=operation_id)


@add_schema
class Wire(DeleteMixin, ModelBase):
    """A Wire model."""

    fields = {
        "source": HasOne("FieldValue", ref="from_id"),
        "destination": HasOne("FieldValue", ref="to_id"),
    }

    WIRABLE_PARENT_CLASSES = ["Operation"]

    def __init__(self, source=None, destination=None):

        self._validate_field_values(source, destination)

        if hasattr(source, "id"):
            from_id = source.id
        else:
            from_id = None

        if hasattr(destination, "id"):
            to_id = destination.id
        else:
            to_id = None

        if (source and not destination) or (destination and not source):
            raise AquariumModelError(
                "Cannot wire. Either source ({}) or destination ({}) is None".format(
                    source, destination
                )
            )

        if source:
            if not source.role:
                raise AquariumModelError(
                    "Cannot wire. FieldValue {} does not have a role".format(
                        source.role
                    )
                )
            elif source.role != "output":
                raise AquariumModelError(
                    "Cannot wire an '{}' FieldValue as a source".format(source.role)
                )

        if destination:
            if not destination.role:
                raise AquariumModelError(
                    "Cannot wire. FieldValue {} does not have a role".format(
                        destination.role
                    )
                )
            elif destination.role != "input":
                raise AquariumModelError(
                    "Cannot wire an '{}' FieldValue as a destination".format(
                        destination.role
                    )
                )

        super().__init__(
            **{
                "source": source,
                "from_id": from_id,
                "destination": destination,
                "to_id": to_id,
            },
            active=True,
        )

    @property
    def identifier(self):

        if not self.source:
            source_id = self.from_id
        else:
            source_id = "r" + str(self.source.rid)

        if not self.destination:
            destination_id = self.to_id
        else:
            destination_id = "r" + str(self.destination.rid)
        return "{}_{}".format(source_id, destination_id)

    @classmethod
    def _validate_field_values(cls, src, dest):
        if src:
            cls._validate_field_value(src, "source")
        if dest:
            cls._validate_field_value(dest, "destination")

        if src and dest and src.rid == dest.rid:
            raise AquariumModelError(
                "Cannot create wire because source and destination are the same "
                "instance."
            )

    @classmethod
    def _validate_field_value(cls, fv, name):
        if not issubclass(type(fv), FieldValue):
            raise AquariumModelError(
                "Cannot create wire because {} FieldValue is {}.".format(
                    name, fv.__class__.__name__
                )
            )

        if fv.parent_class not in cls.WIRABLE_PARENT_CLASSES:
            raise AquariumModelError(
                "Cannot create wire because the {} FieldValue is has '{}' "
                "parent class. Only {} parent classes are wirable".format(
                    name, fv.parent_class, cls.WIRABLE_PARENT_CLASSES
                )
            )

    def validate(self):
        self._validate_field_values(self.source, self.destination)

    def to_save_json(self):
        save_json = {
            "id": self.id,
            "from_id": self.source.id,
            "to_id": self.destination.id,
            "from": {"rid": self.source.rid},
            "to": {"rid": self.destination.rid},
            "active": self.active,
        }
        return save_json

    def delete(self):
        """Permanently deletes the wire instance on the Aquarium server.

        :return:
        :rtype:
        """
        return self.session.utils.delete_wire(self)

    def show(self, pre=""):
        """Show the wire nicely."""
        source = self.source
        dest = self.destination

        from_op_type_name = "None"
        from_name = "None"
        if source:
            from_op_type_name = self.source.operation.operation_type.name
            from_name = source.name

        to_op_type_name = "None"
        to_name = "None"
        if dest:
            to_op_type_name = self.destination.operation.operation_type.name
            to_name = dest.name

        print(
            pre
            + from_op_type_name
            + ":"
            + from_name
            + " --> "
            + to_op_type_name
            + ":"
            + to_name
        )

    def does_wire_to(self, destination):
        if destination and self.destination:
            return destination.rid == self.destination.rid
        return False

    def does_wire_from(self, source):
        if source and self.source:
            return source.rid == self.source.rid
        return False

    def does_wire(self, source, destination):
        """Checks whether this Wire is a wire between the source and
        destination FieldValues.

        If any of the source or destination FieldValues are None,
        returns False.
        """
        if source and destination and self.source and self.destination:
            return (
                source.rid == self.source.rid
                and destination.rid == self.destination.rid
            )
        return False

    # def __eq__(self, other):
    #     """Checks whether this Wire is wired to the same FieldValue instances
    #     of another Wire.
    #
    #     see `does_wire` method.
    #     """
    #     return self.does_wire(other.source, other.destination)
