"""
Canvas
"""

from pydent.user_interfaces.designer.layout import CanvasLayout
from pydent.user_interfaces.designer.utils import arr_to_pairs
from uuid import uuid4
from functools import wraps

from pydent.models import FieldValue, Operation


class CanvasException(Exception):
    """Generic Canvas Exception"""


def verify_plan_models(fxn):
    """Will do a check to verify if any FieldValues or Operations passed as arguments
    exist in the plan."""

    @wraps(fxn)
    def wrapper(self, *args, **kwargs):
        if not issubclass(self.__class__, Canvas):
            raise CanvasException("Cannot apply 'verify_plan_models' to a non-Canvas instance.")
        for arg in args:
            if issubclass(arg.__class__, FieldValue):
                fv = arg
                if not self._contains_op(fv.operation):
                    fviden = "{} {}".format(fv.role, fv.name)
                    raise CanvasException("FieldValue \"{}\" not found in Canvas.".format(fviden))
            elif issubclass(arg.__class__, Operation):
                op = arg
                if not self._contains_op(op):
                    opiden = "{}".format(op.operation_type.name)
                    raise CanvasException("Operation \"{}\" not found in Canvas.".format(opiden))
        return fxn(self, *args, **kwargs)

    return wrapper


class PlanOptimizer(object):

    @staticmethod
    def _op_to_hash(op):
        ot_id = op.operation_type.id

        ftids = []

        for ft in op.operation_type.field_types:
            if ft.ftype == "sample":
                fv = op.field_value(ft.name, ft.role)

                # none valued Samples are never equivaent
                sid = str(uuid4())
                if fv.sample is not None:
                    sid = "{}{}".format(fv.role, fv.sample.id)

                itemid = "none"
                if fv.item is not None:
                    itemid = "{}{}".format(fv.role, fv.item.id)

                ftids.append("{}:{}:{}:{}".format(ft.name, ft.role, sid, itemid))
        ftids = sorted(ftids)
        return "{}_{}".format(ot_id, "#".join(ftids))

    @classmethod
    def _group_ops_by_hashes(cls, ops):
        hashgroup = {}
        for op in ops:
            h = cls._op_to_hash(op)
            hashgroup.setdefault(h, [])
            hashgroup[h].append(op)
        return hashgroup

    def optimize_plan(self, operations=None):
        """
        Optimizes a plan by removing redundent operations.
        :param canvas:
        :return:
        """
        print("Optimizing Plan")
        if operations is None:
            operations = [op for op in self.plan.operations if op.status == 'planning']
        groups = {k: v for k, v in self._group_ops_by_hashes(operations).items() if len(v) > 1}

        num_inputs_rewired = 0
        num_outputs_rewired = 0
        ops_to_remove = []
        for k, gops in groups.items():
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


class Canvas(PlanOptimizer):
    """A user-interface for making experimental plans and layouts."""

    def __init__(self, session, plan_id=None):
        self.plan_id = plan_id
        if self.plan_id is not None:
            self.plan = session.Plan.find(plan_id)
            if self.plan is None:
                raise CanvasException("Could not find plan with id={}".format(plan_id))
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
            raise CanvasException("Found more than one OperationType for query \"{}\"".format(query))
        if ots is None or len(ots) == 0:
            raise CanvasException("Could not find deployed OperationType \"{}\"".format(operation_type_name))
        return self.create_operation_by_type(ots[0])

    @staticmethod
    def eq(m1, m2):
        if m1.id is None and m2.id is None:
            if m1.rid == m2.rid:
                return True
        elif m1.id == m2.id:
            return True
        return False

    def get_operation(self, id):
        for op in self.plan.operations:
            if op.id == id:
                return op

    @verify_plan_models
    def get_wire(self, fv1, fv2):
        for wire in self.plan.wires:
            if self.eq(wire.source, fv1) and self.eq(wire.destination, fv2):
                return wire

    @verify_plan_models
    def remove_wire(self, fv1, fv2):
        """
        Removes a wire between two field values from a plan
        :param fv1:
        :param fv2:
        :return:
        """
        wire = self.get_wire(fv1, fv2)
        self.plan.wires.remove(wire)

    @verify_plan_models
    def get_outgoing_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self.eq(wire.source, fv):
                wires.append(wire)
        return wires

    @verify_plan_models
    def get_incoming_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self.eq(wire.destination, fv):
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
        """Resolves a FieldValue or Operation to its sample output FieldValues"""
        if isinstance(source, FieldValue):
            if source.role == "output":
                outputs = [source]
            else:
                raise CanvasException("Canvas attempted to find matching allowable_field_types for"
                                      " an output FieldValue but found an input FieldValue")
        elif isinstance(source, Operation):
            outputs = [fv for fv in source.outputs if fv.field_type.ftype == 'sample']
        return outputs

    @classmethod
    def _resolve_destination_to_inputs(cls, destination):
        """Resolves a FieldValue or Operation to its sample input FieldValues"""
        if isinstance(destination, FieldValue):
            if destination.role == "input":
                inputs = [destination]
            else:
                raise CanvasException("Canvas attempted to find matching allowable_field_types for"
                                      " an input FieldValue but found an output FieldValue")
        elif isinstance(destination, Operation):
            inputs = [fv for fv in destination.inputs if fv.field_type.ftype == 'sample']
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
            opart = output.field_type.part == True
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
        input_part = input.field_type.part == True
        output_part = input.field_type.part == True
        if input_part != output_part:
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
        return op in self.plan.operations

    @verify_plan_models
    def _resolve_op(self, op, category=None):
        if isinstance(op, tuple):
            op = self.create_operation_by_name(op[0], category=op[1])
        if isinstance(op, str):
            # print("Creating operation \"{}\"".format(op))
            op = self.create_operation_by_name(op, category=category)
        return op

    def quick_create_chain(self, *op_or_otnames, category=None):
        ops = [self._resolve_op(n, category=category) for n in op_or_otnames]
        pairs = arr_to_pairs(ops)
        for op1, op2 in pairs:
            self.quick_wire(op1, op2)
        return ops

    @verify_plan_models
    def quick_wire(self, source, destination, strict=True):
        afts, minputs, moutputs = self._collect_matching_afts(source, destination)

        # TODO: only if matching FVs are ambiquous raise Exception
        if (len(minputs) > 1 or len(moutputs) > 1) and strict:
            raise CanvasException(
                "Cannot quick wire. Ambiguous wiring between inputs [{}] for {} and outputs [{}] for {}".format(
                    ', '.join([fv.name for fv in minputs]),
                    minputs[0].operation.operation_type.name,
                    ', '.join([fv.name for fv in moutputs]),
                    moutputs[0].operation.operation_type.name))
        elif len(afts) == 0:
            raise CanvasException(
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

    def _set_wire(self, src_fv, dest_fv, preference="source"):

        # resolve sample
        samples = [src_fv.sample, dest_fv.sample]
        samples = [s for s in samples if s is not None]

        afts = self._collect_matching_afts(src_fv, dest_fv)[0]

        if len(afts) == 0:
            raise CanvasException("Cannot wire \"{}\" to \"{}\". No allowable field types match."
                                  .format(src_fv.name, dest_fv.name))

        if len(samples) > 0:
            selected_sample = samples[0]
            if preference == "destination":
                selected_sample = samples[1]

            # filter afts by sample_type_id
            afts = [aft for aft in afts if aft[0].sample_type_id == selected_sample.sample_type_id]

            if len(afts) == 0:
                raise CanvasException("No allowable_field_types were found for FieldValues {} & {} for"
                                      " Sample {}".format(src_fv.name, dest_fv.name, selected_sample.name))

            self.set_field_value(src_fv, sample=selected_sample)
            self.set_field_value(dest_fv, sample=selected_sample)

            # set the sample (and allowable_field_type)
            if src_fv.sample is not None and (dest_fv.sample is None or dest_fv.sample.id != src_fv.sample.id):
                self.set_field_value(dest_fv, sample=src_fv.sample)
            if dest_fv.sample is not None and (src_fv.sample is None or dest_fv.sample.id != src_fv.sample.id):
                self.set_field_value(src_fv, sample=dest_fv.sample)
        else:
            # no samples set, so just set the allowable_field_type
            aft = afts[0]
            src_fv.allowable_field_type_id = aft[0].id
            dest_fv.allowable_field_type_id = aft[1].id

    @verify_plan_models
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

    @verify_plan_models
    def set_field_value(self, field_value, sample=None, item=None, container=None, value=None, row=None, column=None):
        routing = field_value.field_type.routing
        fvs = self.get_routing_dict(field_value.operation)[routing]
        field_value.set_value(sample=sample, item=item, container=container, value=value, row=None, column=None)
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
        canvas = self.__class__()
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


    # @staticmethod
    # def _id_getter(model):
    #     id = model.id
    #     if id is None:
    #         id = "r{}".format(model.rid)
    #     return id
    #
    # def _adjacency_list_helper(self, id_getter):
    #     edges = []
    #     nodes = []
    #     for wire in self.plan.wires:
    #         from_id = id_getter(wire.source.operation)
    #         to_id = id_getter(wire.destination.operation)
    #         if from_id is not None and to_id is not None:
    #             edges.append((from_id, to_id))
    #     for op in self.plan.operations:
    #         op_id = id_getter(op)
    #         if op_id is not None:
    #             nodes.append(op_id)
    #     return edges, nodes
    #
    # def _rid_adjacency_list(self):
    #     return self._adjacency_list_helper(lambda x: x.rid)
    #
    # def _adjacency_list(self):
    #     return self._adjacency_list_helper(self._id_getter)

    @property
    def layout(self):
        return CanvasLayout.from_plan(self.plan)

    # def draw(self):
    # import matplotlib.pyplot as plt
    # pos = {op.id: (op.x, op.y) for op in self.plan.operations}
    # G = self.networkx()
    # nx.draw(G, pos=pos)
    # plt.draw()

    # @staticmethod
    # def is_leaf(op):
    #     wires = []
    #     for input in op.inputs:
    #         _wires = input.incoming_wires
    #         if _wires is not None:
    #             wires += _wires
    #     if len(wires) == 0:
    #         return True
    #     return False

    # def successors(self, fv):
    #     return [w for w in self.plan.wires if w.source == fv]
    #
    # def predecessors(self, fv):
    #     return [w for w in self.plan.wires if w.destination == fv]

    # @staticmethod
    # def is_root(op):
    #     wires = []
    #     for output in op.outputs:
    #         _wires = output.outgoing_wires
    #         if _wires is not None:
    #             wires += _wires
    #     if len(wires) == 0:
    #         return True
    #     return False
    #
    # def leafs(self):
    #     leafs = []
    #     for op in self.plan.operations:
    #         for input in op.inputs:
    #             wires = input.incoming_wires
    #             if wires is None or len(wires) == 0:

# def default_layout():
#     return {'children': None,
#             'documentation': 'No documentation yet for this module.',
#             'height': 60,
#             'id': 0,
#             'input': None,
#             'model': {'model': 'Module'},
#             'name': 'Untitled Module 0',
#             'output': None,
#             'parent_id': -1,
#             'text_boxes': None,
#             'width': 160,
#             'wires': None,
#             'x': 160,
#             'y': 160}


# def destroy_layout(plan, keep_text=True):
#     for op in plan.operations:
#         op.parent_id = 0
#         update(op)
#     new_layout = default_layout()
#     if keep_text:
#         if 'text_boxes' in plan.layout:
#             new_layout['text_boxes'] = plan.layout['text_boxes']
#     plan.layout = new_layout
#     update(plan)
#
# def available_predecessors(operation, field_value_name):
#     input = operation.input(field_value_name)
#     afts = []
#     operation.session.OperationType.where({""})
#
#
# def remove_wire(fv1, fv2):
#     pass
