"""
Planner
"""

from networkx import nx
from pydent.planner.layout import PlannerLayout
from pydent.planner.utils import arr_to_pairs, _id_getter, get_subgraphs
from pydent.utils import make_async
from uuid import uuid4
from functools import wraps

from pydent.models import FieldValue, Operation


class PlannerException(Exception):
    """Generic planner Exception"""


def plan_verification_wrapper(fxn):
    """
    A wrapper that verifies that all FieldValues or Operations passed
    as arguments exist in the plan.
    """

    @wraps(fxn)
    def wrapper(self, *args, **kwargs):
        if not issubclass(self.__class__, Planner):
            raise PlannerException(
                "Cannot apply 'verify_plan_models' to a non-planner instance.")
        for arg in args:
            if issubclass(arg.__class__, FieldValue):
                fv = arg
                if not self._contains_op(fv.operation):
                    fv_ref = "{} {}".format(fv.role, fv.name)
                    msg = "FieldValue \"{}\" not found in planner."
                    raise PlannerException(msg.format(fv_ref))
            elif issubclass(arg.__class__, Operation):
                op = arg
                if not self._contains_op(op):
                    op_ref = "{}".format(op.operation_type.name)
                    msg = "Operation \"{}\" not found in planner."
                    raise PlannerException(msg.format(op_ref))
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
            msg = "Found more than one OperationType for query \"{}\". Have you tried specifying the category?"
            raise PlannerException(msg.format(query))
        if ots is None or len(ots) == 0:
            msg = "Could not find deployed OperationType \"{}\"."
            raise PlannerException(msg.format(operation_type_name))
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
            if (self.models_are_equal(wire.source, fv1)
                    and self.models_are_equal(wire.destination, fv2)):
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
                msg = "Planner attempted to find matching" \
                    " allowable_field_types for an output FieldValue but" \
                    " found an input FieldValue"
                raise PlannerException(msg)
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
                return [destination]
            else:
                msg = "Planner attempted to find matching" \
                    " allowable_field_types for" \
                    " an input FieldValue but found an output FieldValue"
                raise PlannerException(msg)
        elif isinstance(destination, Operation):
            inputs = [fv for fv in destination.inputs
                      if fv.field_type.ftype == 'sample']
            return inputs
        else:
            raise PlannerException("Cannot resolve inputs, type must be a FieldValue or Operation, not a \"{}\"".format(type(destination)))

    @classmethod
    def _collect_matching_afts(cls, source, destination):
        """

        :param source: a field value or operation source
        :type source: FieldValue|Operation
        :param destination: a field value or operation destination
        :type destination: FieldValue|Operation
        :return: tuple of matching allowable_field_type (aft) pairs, matching field_value inputs and matching field_value outputs
        :rtype: tuple
        """
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
                if (out_object_type_id == in_object_type_id
                        and out_sample_type_id == in_sample_type_id):
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
            plan_operation_ids = [x.id for x in self.plan.operations]
            return op.id is not None and op.id in plan_operation_ids

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
        Creates a chain of operations by *guessing* wires between operations
        based on the AllowableFieldTypes between the inputs and outputs of each
        operation type.
        Sample inputs and outputs will be set along the wire if possible.

        e.g.

        .. code::

            # create four new operations based on their OperationType names
            planner.quick_create_chain("Make PCR Fragment", "Run Gel",
                                      "Extract Gel Slice", "Purify Gel Slice")

            # create four new operations based on their OperationType names by
            # finding OperationTypes only in the "Cloning" category
            planner.quick_create_chain("Make PCR Fragment", "Run Gel",
                                      "Extract Gel Slice", "Purify Gel Slice",
                                      category="Cloning")

            # create four new operations based on their OperationType names by
            # finding OperationTypes only in the "Cloning" category,
            # except find "Make PCR Fragment" in the "Cloning Sandbox" category
            planner.quick_create_chain(("Make PCR Fragment", "Cloning Sandbox"),
                                       "Run Gel", "Extract Gel Slice",
                                       "Purify Gel Slice", category="Cloning")

            # create and wire new operations to an existing operations while
            # routing samples
            pcr_op = planner.create_operation_by_name("Make PCR Fragment")
            planner.set_field_value(pcr_op.outputs[0], sample=my_sample)
            new_ops = planner.quick_create_chain(pcr_op, "Run Gel")
            run_gel = new_ops[1]
            planner.quick_create_chain("Pour Gel", run_gel)
        """
        ops = [self._resolve_op(n, category=category) for n in op_or_otnames]
        if any([op for op in ops if op is None]):
            raise Exception("Could not find some operations: {}".format(ops))
        pairs = arr_to_pairs(ops)
        for op1, op2 in pairs:
            self.quick_wire(op1, op2)
        return ops

    # TODO: way to select preference for afts in quick_wire?
    @plan_verification_wrapper
    def quick_wire(self, source, destination, strict=False):
        """

        :param source: field_value or operation source
        :type source: FieldValue|Operation
        :param destination: field_value or operation destination
        :type destination: FieldValue|Operation
        :param strict: will raise error if there is is ambiguous wiring between the source and destination
        :type strict: bool
        :return: created wire
        :rtype: Wire
        """
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
        elif len(afts) > 0:
            for aft1, aft2 in afts:

                input_ft = aft2.field_type
                output_ft = aft1.field_type

                i = destination.input(input_ft.name)
                o = source.output(output_ft.name)
                if input_ft.array:
                    if len(self.get_incoming_wires(i)) == 0:
                        i = o.operation.add_to_field_value_array(input_ft.name, "input")
                return self.add_wire(o, i)
        elif len(afts) == 0:
            "Cannot quick wire. No possible wiring found between inputs [{}] for {} and outputs [{}] for {}".format(
                ', '.join([fv.name for fv in model_inputs]),
                model_inputs[0].operation.operation_type.name,
                ', '.join([fv.name for fv in model_outputs]),
                model_outputs[0].operation.operation_type.name)

    def quick_wire_by_name(self, otname1, otname2):
        """Wires together the last added operations."""
        op1 = self.find_operations_by_name(otname1)[-1]
        op2 = self.find_operations_by_name(otname2)[-1]
        return self.quick_wire(op1, op2)

    # TODO: resolve afts if already set...
    # TODO: clean up _set_wire
    def _set_wire(self, src_fv, dest_fv, preference="source", setter=None):

        if len(self.get_incoming_wires(dest_fv)) > 0:
            raise PlannerException("Cannot wire because \"{}\" already has an incoming wire and inputs"
                                   " can only have one incoming wire. Please remove wire"
                                   " using 'canvas.remove_wire(src_fv, dest_fv)' before setting.".format(dest_fv.name))

        # first collect any matching allowable field types between the field values
        aft_pairs = self._collect_matching_afts(src_fv, dest_fv)[0]

        if len(aft_pairs) == 0:
            raise PlannerException("Cannot wire \"{}\" to \"{}\". No allowable field types match."
                                   .format(src_fv.name, dest_fv.name))

        # select the first aft
        default_aft_ids = [src_fv.allowable_field_type_id, dest_fv.allowable_field_type_id]
        pref_index = 0
        if preference == "destination":
            pref_index = 1
        selected_aft_pair = aft_pairs[0]
        for pair in aft_pairs:
            if pair[pref_index].id == default_aft_ids[pref_index]:
                selected_aft_pair = pair
        assert selected_aft_pair[0].object_type_id == selected_aft_pair[1].object_type_id

        # resolve sample
        samples = [src_fv.sample, dest_fv.sample]
        samples = [s for s in samples if s is not None]

        if setter is None:
            setter = self.set_field_value

        if len(samples) > 0:
            selected_sample = samples[pref_index]

            # filter afts by sample_type_id
            aft_pairs = [aft for aft in aft_pairs if aft[0].sample_type_id ==
                    selected_sample.sample_type_id]
            selected_aft_pair = aft_pairs[0]

            if len(aft_pairs) == 0:
                raise PlannerException("No allowable_field_types were found for FieldValues {} & {} for"
                                       " Sample {}".format(src_fv.name, dest_fv.name, selected_sample.name))

            setter(src_fv, sample=selected_sample)
            setter(dest_fv, sample=selected_sample)

            assert selected_aft_pair[0].sample_type_id == selected_aft_pair[1].sample_type_id
            assert selected_aft_pair[0].sample_type_id == src_fv.sample.sample_type_id
            assert selected_aft_pair[0].sample_type_id == dest_fv.sample.sample_type_id

            # set the sample (and allowable_field_type)
            if src_fv.sample is not None and (dest_fv.sample is None or dest_fv.sample.id != src_fv.sample.id):
                setter(
                    dest_fv, sample=src_fv.sample, container=selected_aft_pair[0].object_type)
            elif dest_fv.sample is not None and (src_fv.sample is None or dest_fv.sample.id != src_fv.sample.id):
                setter(
                    src_fv, sample=dest_fv.sample, container=selected_aft_pair[0].object_type)

        setter(src_fv, container=selected_aft_pair[0].object_type)
        setter(dest_fv, container=selected_aft_pair[0].object_type)

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
    def _routing_id(fv):
        return "{}_{}".format(_id_getter(fv.operation), fv.field_type.routing)

    @staticmethod
    def get_routing_dict(op):
        routing_dict = {}
        for fv in op.field_values:
            routing = fv.field_type.routing
            routing_fvs = routing_dict.get(routing, [])
            routing_fvs.append(fv)
            routing_dict[fv.field_type.routing] = routing_fvs
        return routing_dict

    def _routing_graph(self):
        """Get sample routing graph. A property of a valid plan is that any two routing nodes
        that are connected by an edge must have the same sample. Edges are treated as 'sample wires'"""
        G = nx.DiGraph()

        for op in self.plan.operations:
            for fv in op.field_values:
                G.add_node(self._routing_id(fv), fv=fv)

        for w in self.plan.wires:
            src_id = self._routing_id(w.source)
            dest_id = self._routing_id(w.destination)

            G.add_node(src_id, fv=w.source)
            G.add_node(dest_id, fv=w.destination)

            G.add_edge(src_id, dest_id, wire=w)
        return G

    def _cache(self):
        @make_async(10, progress_bar=False)
        def _cache_ops(ops):
            for op in ops:
                for fv in op.field_values:
                    fv.sample
                    fv.allowable_field_type
                    fv.field_type
            return ops
        _cache_ops(self.plan.operations)

    # TODO: verify all routing graphs have the same sample
    # TODO: verify all leaves have an item or a wire
    def validate(self):
        routing_subgraphs = self._routing_graph()
        for rsg in routing_subgraphs:
            for n in rsg.nodes:
                n.field_value

    # TODO: Support for row and column
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

    def set_field_value_and_propogate(self, field_value, sample=None):
        routing_graph = self._routing_graph()
        routing_id = self._routing_id(field_value)
        subgraph = nx.bfs_tree(routing_graph.to_undirected(), routing_id)
        for node in subgraph:
            n = routing_graph.node[node]
            self.set_field_value(n['fv'], sample=sample)

    @staticmethod
    @make_async
    def _filter_by_lambdas(models, lambda_arr):
        """Filters models by a array of lambdas."""
        arr = models[:]
        _arr = []
        while arr:
            m = arr.pop()
            for fxn in lambda_arr:
                try:
                    if fxn(m):
                        _arr.append(m)
                except TypeError or ValueError:
                    continue
        return _arr

    @plan_verification_wrapper
    def set_to_available_item(self, fv, recent=True, lambda_arr=None):
        """
        Sets the item of the field value to the next available item. Setting recent=False will select
        the oldest item.

        :param fv: The field value to set.
        :type fv: FieldValue
        :param recent: whether to select the most recent item (recent=True is default)
        :type recent: bool
        :param lambda_arr: array of lambda to filter items by. E.g. 'lambda_arr=[lambda x: x.get("concentration") > 10]'
        :type lambda_arr: list
        :return: the selected item
        :rtype: Item
        """
        sample = fv.sample
        item = None
        if sample is not None:
            allowable_field_type = fv.allowable_field_type
            available_items = sample.available_items(object_type_id=allowable_field_type.object_type_id)
            available_items = sorted(available_items, key=lambda x: x.created_at)
            if lambda_arr is not None:
                available_items = self._filter_by_lambdas(available_items, lambda_arr)
            if recent:
                item = available_items[-1]
            else:
                item = available_items[0]
        if item is not None:
            fv.set_value(item=item)
        return item

    @plan_verification_wrapper
    def set_inputs_with_sample(self, operation, sample, routing=None, setter=None):
        """Map the sample field values to the operation inputs. Optionally, a routing dictionary may
        be passed to indicate the mapping between the sample field values and operation inputs.

        For example, the following would map the "Integrant" sample field value to the "Template"
        operation input, and so on...:

        .. code:: python

            routing={
                "Integrant": "Template",
                "QC_Primer1": "Forward Primer",
                "QC_Primer2": "Reverse Primer"
            }
        """
        if routing is None:
            routing = {ft.name: ft.name for ft in sample.sample_type.field_types}

        if setter is None:
            setter = self.set_field_value
        for sfv, ofv in routing.items():
            operation_input = operation.input(ofv)
            sample_property = sample.properties.get(sfv, None)
            # set operation input to the property sample
            if operation_input is not None and sample_property is not None:
                setter(operation_input, sample=sample_property)

    @plan_verification_wrapper
    def set_output(self, fv, sample=None, routing=None, setter=None):
        """
        Sets the output of the field value to the sample. If the field_value names between the Sample and
        the field_value's operation inputs, these will be set as well. Optionally, a routing dictionary may
        be passed to indicate the mapping between the sample field values and the operation field values.

        :param fv: the output field value
        :type fv:
        :param sample:
        :type sample:
        :param routing:
        :type routing:
        :return:
        :rtype:
        """
        if fv.role != "output":
            raise Exception("Cannot output. FieldValue {} is a/an {}.".format(fv.name, fv.role))
        if setter is None:
            setter = self.set_field_value
        setter(fv, sample=sample)
        op = fv.operation
        self.set_inputs_with_sample(op, sample, routing=routing, setter=setter)

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
        """
        Find operations by their operation_type_name

        :param operation_type_name: The operation type name
        :type operation_type_name: basestring
        :return: list of operations
        :rtype: list
        """
        return [op for op in self.plan.operations if
                op.operation_type.name == operation_type_name]

    def replan(self):
        """Replan the plan, by 'copying' the plan using the Aquarium server."""
        planner = self.__class__(self.session)
        planner.plan = self.plan.replan()
        return planner

    def annotate(self, markdown, x, y, width, height):
        """
        Annotates the plan with Markdown text.

        :param markdown: text to annotate (in markdown format)
        :type markdown: basestring
        :param x: x-position
        :type x: int
        :param y: y-position
        :type y: int
        :param width: width of the text box
        :type width: int
        :param height: height of the text box
        :type height: int
        :return: None
        :rtype: None
        """
        annotation = {
            "anchor": {"x": width, "y": height},
            "x": x,
            "y": y,
            "markdown": markdown
        }
        markdown += "\n<!-- annotated by pydent.planner -->"
        self.plan.layout.setdefault('text_boxes', [])
        if self.plan.layout['text_boxes'] is None:
            self.plan.layout['text_boxes'] = []
        if annotation not in self.plan.layout['text_boxes']:
            self.plan.layout['text_boxes'].append(annotation)
        return annotation

    def annotate_operations(self, ops, markdown, width, height):
        """Annotates above the operations. Estimates the x-midpoint and y and makes a
        text annotation at that location."""
        layout = self.layout.ops_to_layout(ops)
        return self.annotate_above_layout(markdown, width, height, layout=layout)

    def annotate_above_layout(self, markdown, width, height, layout=None):
        """Annotates text directly above a layout"""
        if layout is None:
            layout = self.layout

        x = layout.midpoint()[0] + layout.BOX_WIDTH/2  # adjust so x is midpoint of 'box' on screen
        y = layout.y

        # center the annotation
        x -= width/2
        y -= height

        # give some space between annotation and operation
        y -= layout.BOX_DELTA_Y/2

        return self.annotate(markdown, x, y, width, height)

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

    def ipython_link(self):
        from IPython.display import display, HTML
        return display(HTML("<a href=\"{url}\">{url}</a>".format(url=self.url)))

    def optimize_plan(self, operations=None, ignore=None):
        """
        Optimizes a plan by removing redundent operations.
        :param planner:
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

    def roots(self):
        """Get field values that have no predecessors (i.e. are 'roots')"""
        roots = []
        for subgraph in get_subgraphs(self._routing_graph()):
            for n in subgraph:
                node = subgraph.node[n]
                if len(list(subgraph.predecessors(n))) == 0:
                    root = node['fv']
                    roots.append(root)
        return roots

    def validate(self):
        """
        Validates sample routes in the plan.

        :return: dictionary of each sample route and validation errors
        :rtype: dict
        """
        routes = {}
        for subgraph in get_subgraphs(self._routing_graph()):
            values = []
            reasons = []
            root = None
            for n in subgraph:
                node = subgraph.node[n]
                fv = node['fv']
                value = fv.sample
                if value is None and fv.field_type.ftype == 'sample':
                    reasons.append("{} {} for {} has no sample defined".format(fv.role, fv.name, fv.operation.operation_type.name))
                else:
                    values.append(value)
                if len(list(subgraph.predecessors(n))) == 0:
                    root = fv
            if root.item is None and root.role == "input" and root.field_type.ftype == 'sample':
                reasons.append("{} {} for {} has no item defined".format(fv.role, fv.name, fv.operation.operation_type.name))
            values = list(set(values))
            if len(values) > 1:
                reasons.append("different samples defined in route ({})".format(values))
            root_id = "{} for {} ({})".format(root.name, root.operation.operation_type.name, self._routing_id(root))
            routes[root_id] = {
                "root_field_value": root,
                "errors": reasons,
                "valid": len(reasons) == 0
            }
        return routes

    # TODO: implement individual wires and things
    def draw(self):
        layout = self.layout
        edge_colors = []
        for s, e, d in layout.G.edges(data=True):
            color = "black"
            wire = d['wire']
            if wire.source.sample is None:
                color = "orange"
            elif wire.destination.sample is None:
                color = "orange"
            elif wire.destination.sample != wire.source.sample:
                color = "red"
            edge_colors.append(color)
        nx.draw(self.layout.G, edge_colors=edge_colors, pos=self.layout.pos())