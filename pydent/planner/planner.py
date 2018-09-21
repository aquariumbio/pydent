"""
Planner
"""

from pydent.planner.layout import PlannerLayout
from pydent.planner.utils import arr_to_pairs
from uuid import uuid4
from functools import wraps

from pydent.models import FieldValue, Operation


class PlannerException(Exception):
    """Generic Canvas Exception"""


def plan_verification_wrapper(fxn):
    """
    A wrapper that verifies that all FieldValues or Operations passed
    as arguments exist in the plan.
    """

    @wraps(fxn)
    def wrapper(self, *args, **kwargs):
        if not issubclass(self.__class__, Planner):
            raise PlannerException(
                "Cannot apply 'verify_plan_models' to a non-Canvas instance.")
        for arg in args:
            if issubclass(arg.__class__, FieldValue):
                fv = arg
                if not self._contains_op(fv.operation):
                    fviden = "{} {}".format(fv.role, fv.name)
                    raise PlannerException(
                        "FieldValue \"{}\" not found in Canvas.".format(fviden))
            elif issubclass(arg.__class__, Operation):
                op = arg
                if not self._contains_op(op):
                    opiden = "{}".format(op.operation_type.name)
                    raise PlannerException(
                        "Operation \"{}\" not found in Canvas.".format(opiden))
        return fxn(self, *args, **kwargs)

    return wrapper


class Planner(object):
    """A user-interface for making experimental plans and layouts."""

    def __init__(self, session, plan_id=None):
        self.plan_id = plan_id
        if self.plan_id is not None:
            self.plan = session.Plan.find(plan_id)
            if self.plan is None:
                raise PlannerException(
                    "Could not find plan with id={}".format(plan_id))
        else:
            self.plan = session.Plan.new()
        self.session = session

    @property
    def name(self):
        return self.plan.name

    @name.setter
    def name(self, value):
        self.plan.name = value

    @property
    def url(self):
        return self.session.url + "plans?plan_id={}".format(self.plan.id)

    def create(self):
        """Create the plan on Aquarium"""
        self.plan.create()

    def save(self):
        """Save the plan on Aquarium"""
        self.plan.save()
        return self.plan

    def create_operation_by_type(self, ot, status="planning"):
        op = ot.instance()
        op.status = status
        self.plan.add_operation(op)
        return op

    def create_operation_by_id(self, ot_id):
        ot = self.session.OperationType.find(ot_id)
        return self.create_operation_by_type(ot)

    def create_operation_by_name(self, operation_type_name, category=None):
        """Adds a new operation to the plan"""
        query = {"deployed": True, "name": operation_type_name}
        if category is not None:
            query['category'] = category
        ots = self.session.OperationType.where(query)
        if len(ots) > 1:
            raise PlannerException(
                "Found more than one OperationType for query \"{}\"".format(query))
        if ots is None or len(ots) == 0:
            raise PlannerException(
                "Could not find deployed OperationType \"{}\"".format(operation_type_name))
        return self.create_operation_by_type(ots[0])

    @staticmethod
    def models_are_equal(model1, model2):
        if model1.id is None and model2.id is None:
            if model1.rid == model2.rid:
                return True
        elif model1.id == model2.id:
            return True
        return False

    def get_operation(self, id):
        for op in self.plan.operations:
            if op.id == id:
                return op

    @plan_verification_wrapper
    def get_wire(self, fv1, fv2):
        for wire in self.plan.wires:
            if self.models_are_equal(wire.source, fv1) and self.models_are_equal(wire.destination, fv2):
                return wire

    @plan_verification_wrapper
    def remove_wire(self, fv1, fv2):
        """
        Removes a wire between two field values from a plan
        :param fv1:
        :param fv2:
        :return:
        """
        wire = self.get_wire(fv1, fv2)
        self.plan.wires.remove(wire)

    @plan_verification_wrapper
    def get_outgoing_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self.models_are_equal(wire.source, fv):
                wires.append(wire)
        return wires

    @plan_verification_wrapper
    def get_incoming_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self.models_are_equal(wire.destination, fv):
                wires.append(wire)
        return wires

    def get_fv_successors(self, fv):
        fvs = []
        for wire in self.get_outgoing_wires(fv):
            fvs.append(wire.destination)
        return fvs

    def get_fv_predecessors(self, fv):
        fvs = []
        for wire in self.get_incoming_wires(fv):
            fvs.append(wire.source)
        return fvs

    def get_op_successors(self, op):
        ops = []
        for output in op.outputs:
            ops += [fv.operation for fv in self.get_fv_successors(output)]
        return ops

    def get_op_predecessors(self, op):
        ops = []
        for input in op.inputs:
            ops += [fv.operation for fv in self.get_fv_predecessors(input)]
        return ops

    @classmethod
    def _resolve_source_to_outputs(cls, source):
        """
        Resolves a FieldValue or Operation to its sample output FieldValues
        """
        if isinstance(source, FieldValue):
            if source.role == "output":
                outputs = [source]
            else:
                raise PlannerException("Canvas attempted to find matching allowable_field_types for"
                                       " an output FieldValue but found an input FieldValue")
        elif isinstance(source, Operation):
            outputs = [
                fv for fv in source.outputs if fv.field_type.ftype == 'sample']
        return outputs

    @classmethod
    def _resolve_destination_to_inputs(cls, destination):
        """
        Resolves a FieldValue or Operation to its sample input FieldValues
        """
        if isinstance(destination, FieldValue):
            if destination.role == "input":
                inputs = [destination]
            else:
                raise PlannerException("Canvas attempted to find matching allowable_field_types for"
                                       " an input FieldValue but found an output FieldValue")
        elif isinstance(destination, Operation):
            inputs = [
                fv for fv in destination.inputs if fv.field_type.ftype == 'sample']
        return inputs

    @classmethod
    def _collect_matching_afts(cls, source, destination):
        """Find matching AllowableFieldTypes"""
        inputs = cls._resolve_destination_to_inputs(destination)
        outputs = cls._resolve_source_to_outputs(source)

        matching_afts = []
        matching_inputs = []
        matching_outputs = []
        for output in outputs:
            for input in inputs:
                io_matching_afts = cls._find_matching_afts(output, input)
                if len(io_matching_afts) > 0:
                    if input not in matching_inputs:
                        matching_inputs.append(input)
                    if output not in matching_outputs:
                        matching_outputs.append(output)
                matching_afts += io_matching_afts
        return matching_afts, matching_inputs, matching_outputs

    @staticmethod
    def _find_matching_afts(output, input):
        """Finds matching afts between two FieldValues"""
        afts = []
        output_afts = output.field_type.allowable_field_types
        input_afts = input.field_type.allowable_field_types

        # check whether the field_type handles collections
        input_handles_collections = input.field_type.part is True
        output_handles_collections = input.field_type.part is True
        if input_handles_collections != output_handles_collections:
            return []

        for input_aft in input_afts:
            for output_aft in output_afts:
                out_object_type_id = output_aft.object_type_id
                in_object_type_id = input_aft.object_type_id
                out_sample_type_id = output_aft.sample_type_id
                in_sample_type_id = input_aft.sample_type_id
                if out_object_type_id == in_object_type_id and out_sample_type_id == in_sample_type_id:
                    afts.append((output_aft, input_aft))
        return afts

    def quick_create_operation_by_name(self, otname):
        try:
            return self.create_operation_by_name(*otname)
        except TypeError:
            return self.create_operation_by_name(otname)

    def quick_create_and_wire(self, otname1, otname2, fvnames=None):
        self.quick_create_operation_by_name(otname1)
        self.quick_create_operation_by_name(otname2)
        return self.quick_wire_by_name(otname1, otname2)

    def _contains_op(self, op):
        if op in self.plan.operations:
            return True
        else:
            if op.id is not None and op.id in [x.id for x in self.plan.operations]:
                return True
            else:
                return False

    @plan_verification_wrapper
    def _resolve_op(self, op, category=None):
        if isinstance(op, tuple):
            op = self.create_operation_by_name(op[0], category=op[1])
        if isinstance(op, str):
            # print("Creating operation \"{}\"".format(op))
            op = self.create_operation_by_name(op, category=category)
        return op

    def quick_create_chain(self, *op_or_otnames, category=None):
        """
        Creates a chain of operations by *guessing* wires between operations based on the
        AllowableFieldTypes between the inputs and outputs of each operation type.
        Sample inputs and outputs will be set along the wire if possible.

        e.g.

        .. code::

            # create four new operations based on their OperationType names
            canvas.quick_create_chain("Make PCR Fragment", "Run Gel",
                                      "Extract Gel Slice", "Purify Gel Slice")

            # create four new operations based on their OperationType names by
            # finding OperationTypes only in the "Cloning" category
            canvas.quick_create_chain("Make PCR Fragment", "Run Gel",
                                      "Extract Gel Slice", "Purify Gel Slice", category="Cloning")

            # create four new operations based on their OperationType names by
            # finding OperationTypes only in the "Cloning" category,
            # except find "Make PCR Fragment" in the "Cloning Sandbox" category
            canvas.quick_create_chain(("Make PCR Fragment", "Cloning Sandbox"), "Run Gel",
                                      "Extract Gel Slice", "Purify Gel Slice", category="Cloning")

            # create and wire new operations to an existing operations while
            # routing samples
            pcr_op = canvas.create_operation_by_name("Make PCR Fragment")
            canvas.set_field_value(pcr_op.outputs[0], sample=my_sample)
            new_ops = canvas.quick_create_chain(pcr_op, "Run Gel")
            run_gel = new_ops[1]
            canvas.quick_create_chain("Pour Gel", run_gel)
        """
        ops = [self._resolve_op(n, category=category) for n in op_or_otnames]
        pairs = arr_to_pairs(ops)
        for op1, op2 in pairs:
            self.quick_wire(op1, op2)
        return ops

    @plan_verification_wrapper
    def quick_wire(self, source, destination, strict=True):
        afts, model_inputs, model_outputs = self._collect_matching_afts(
            source, destination)

        # TODO: only if matching FVs are ambiguous raise Exception
        if (len(model_inputs) > 1 or len(model_outputs) > 1) and strict:
            raise PlannerException(
                "Cannot quick wire. Ambiguous wiring between inputs [{}] for {} and outputs [{}] for {}".format(
                    ', '.join([fv.name for fv in model_inputs]),
                    model_inputs[0].operation.operation_type.name,
                    ', '.join([fv.name for fv in model_outputs]),
                    model_outputs[0].operation.operation_type.name))
        elif len(afts) == 0:
            raise PlannerException(
                "Cannot quick wire. No available field types found between {} and {}".format(source.operation_type.name,
                                                                                             destination.operation_type.name))
        for aft1, aft2 in afts:
            o = source.output(aft1.field_type.name)
            i = destination.input(aft2.field_type.name)
            o.allowable_field_type_id = aft1.id
            i.allowable_field_type_id = aft2.id
            return self.add_wire(o, i)

    def quick_wire_by_name(self, otname1, otname2):
        """Wires together the last added operations."""
        op1 = self.find_operations_by_name(otname1)[-1]
        op2 = self.find_operations_by_name(otname2)[-1]
        return self.quick_wire(op1, op2)

    # TODO: resolve afts if already set...
    # TODO: clean up _set_wire
    def _set_wire(self, src_fv, dest_fv, preference="source"):

        # resolve sample
        samples = [src_fv.sample, dest_fv.sample]
        samples = [s for s in samples if s is not None]

        afts = self._collect_matching_afts(src_fv, dest_fv)[0]

        if len(afts) == 0:
            raise PlannerException("Cannot wire \"{}\" to \"{}\". No allowable field types match."
                                   .format(src_fv.name, dest_fv.name))

        selected_aft = afts[0]
        assert selected_aft[0].object_type_id == selected_aft[1].object_type_id

        if len(samples) > 0:
            selected_sample = samples[0]
            if preference == "destination":
                selected_sample = samples[1]

            # filter afts by sample_type_id
            afts = [aft for aft in afts if aft[0].sample_type_id ==
                    selected_sample.sample_type_id]
            selected_aft = afts[0]

            if len(afts) == 0:
                raise PlannerException("No allowable_field_types were found for FieldValues {} & {} for"
                                       " Sample {}".format(src_fv.name, dest_fv.name, selected_sample.name))

            self.set_field_value(src_fv, sample=selected_sample)
            self.set_field_value(dest_fv, sample=selected_sample)

            assert selected_aft[0].sample_type_id == selected_aft[1].sample_type_id
            assert selected_aft[0].sample_type_id == src_fv.sample.sample_type_id
            assert selected_aft[0].sample_type_id == dest_fv.sample.sample_type_id

            # set the sample (and allowable_field_type)
            if src_fv.sample is not None and (dest_fv.sample is None or dest_fv.sample.id != src_fv.sample.id):
                self.set_field_value(
                    dest_fv, sample=src_fv.sample, container=selected_aft[0].object_type)
            elif dest_fv.sample is not None and (src_fv.sample is None or dest_fv.sample.id != src_fv.sample.id):
                self.set_field_value(
                    src_fv, sample=dest_fv.sample, container=selected_aft[0].object_type)

        self.set_field_value(src_fv, container=selected_aft[0].object_type)
        self.set_field_value(dest_fv, container=selected_aft[0].object_type)

    @plan_verification_wrapper
    def add_wire(self, fv1, fv2):
        """Note that fv2.operation will not inherit parent_id of fv1"""
        wire = self.get_wire(fv1, fv2)
        self._set_wire(fv1, fv2)
        if wire is None:
            # wire does not exist, so create it
            self.plan.wire(fv1, fv2)
        return wire

    @staticmethod
    def get_routing_dict(op):
        routing_dict = {}
        for fv in op.field_values:
            routing = fv.field_type.routing
            routing_fvs = routing_dict.get(routing, [])
            routing_fvs.append(fv)
            routing_dict[fv.field_type.routing] = routing_fvs
        return routing_dict

    @plan_verification_wrapper
    def set_field_value(self, field_value, sample=None, item=None, container=None, value=None, row=None, column=None):
        routing = field_value.field_type.routing
        fvs = self.get_routing_dict(field_value.operation)[routing]
        field_value.set_value(
            sample=sample, item=item, container=container, value=value, row=None, column=None)
        # cls._json_update(field_value)
        if field_value.field_type.ftype == 'sample':
            for fv in fvs:
                fv.set_value(sample=sample)
                # cls._json_update(fv)

    @staticmethod
    def _json_update(model, **params):
        """Temporary method to update"""
        aqhttp = model.session._AqSession__aqhttp
        data = {"model": {"model": model.__class__.__name__}}
        data.update(model.dump(**params))
        model_data = aqhttp.post('json/save', json_data=data)
        model.reload(model_data)
        return model

    @classmethod
    def move_operation(cls, op, plan_id):
        pa = op.plan_associations[0]
        pa.plan_id = plan_id
        op.parent_id = 0
        cls._json_update(op)
        cls._json_update(pa)

    def find_operations_by_name(self, operation_type_name):
        return [op for op in self.plan.operations if
                op.operation_type.name == operation_type_name]

    def replan(self):
        """Replan"""
        canvas = self.__class__(self.session)
        canvas.plan = self.plan.replan()
        return canvas

    def annotate(self, markdown, x, y, width, height):
        annotation = {
            "anchor": {"x": width, "y": height},
            "x": x,
            "y": y,
            "markdown": markdown
        }
        self.plan.layout.setdefault('text_boxes', [])
        if self.plan.layout['text_boxes'] is None:
            self.plan.layout['text_boxes'] = []
        if annotation not in self.plan.layout['text_boxes']:
            self.plan.layout['text_boxes'].append(annotation)

    def annotate_above_layout(self, markdown, width, height, layout=None):
        if layout is None:
            layout = self.layout
        x, y = layout.midpoint()
        x += layout.BOX_WIDTH/2
        # x -= width/2
        y -= height
        y -= layout.BOX_DELTAY
        self.annotate(markdown, x, y, width, height)

    @property
    def layout(self):
        return PlannerLayout.from_plan(self.plan)

    @staticmethod
    def _op_to_hash(op):
        """Turns a operation into a hash using the operation_type_id, item_id, and sample_id"""
        ot_id = op.operation_type.id

        field_type_ids = []
        for ft in op.operation_type.field_types:
            if ft.ftype == "sample":
                fv = op.field_value(ft.name, ft.role)

                # none valued Samples are never equivalent
                sid = str(uuid4())
                if fv.sample is not None:
                    sid = "{}{}".format(fv.role, fv.sample.id)

                item_id = "none"
                if fv.item is not None:
                    item_id = "{}{}".format(fv.role, fv.item.id)

                field_type_ids.append("{}:{}:{}:{}".format(
                    ft.name, ft.role, sid, item_id))
        field_type_ids = sorted(field_type_ids)
        return "{}_{}".format(ot_id, "#".join(field_type_ids))

    @classmethod
    def _group_ops_by_hashes(cls, ops):
        hashgroup = {}
        for op in ops:
            h = cls._op_to_hash(op)
            hashgroup.setdefault(h, [])
            hashgroup[h].append(op)
        return hashgroup

    def optimize_plan(self, operations=None, ignore=None):
        """
        Optimizes a plan by removing redundent operations.
        :param canvas:
        :return:
        """
        print("Optimizing Plan")
        if operations is None:
            operations = [
                op for op in self.plan.operations if op.status == 'planning']
        if ignore is not None:
            operations = [
                op for op in operations if op.operation_type.name not in ignore]
        groups = {k: v for k, v in self._group_ops_by_hashes(
            operations).items() if len(v) > 1}

        num_inputs_rewired = 0
        num_outputs_rewired = 0
        ops_to_remove = []
        for gops in groups.values():
            op = gops[0]
            other_ops = gops[1:]
            for other_op in other_ops:
                connected_ops = self.get_op_successors(other_op)
                connected_ops += self.get_op_predecessors(other_op)
                if all([_op.status == "planning" for _op in connected_ops]):
                    # only optimize if ALL connected operations are in planning status
                    for i in other_op.inputs:
                        in_wires = self.get_incoming_wires(i)
                        for w in in_wires:
                            if w.source.operation.status == "planning":
                                self.add_wire(w.source, op.input(i.name))
                                self.remove_wire(w.source, w.destination)
                                num_inputs_rewired += 1
                    for o in other_op.outputs:
                        out_wires = self.get_outgoing_wires(o)
                        for w in out_wires:
                            if w.destination.operation.status == "planning":
                                self.add_wire(op.output(o.name), w.destination)
                                self.remove_wire(w.source, w.destination)
                                num_outputs_rewired += 1
                    ops_to_remove.append(other_op)
        for op in ops_to_remove:
            self.plan.operations.remove(op)
        print("\t{} operations removed".format(len(ops_to_remove)))
        print("\t{} input wires re-wired".format(num_inputs_rewired))
        print("\t{} output wires re-wired".format(num_outputs_rewired))
