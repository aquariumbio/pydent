"""
Planner
"""

from functools import wraps
from uuid import uuid4

from networkx import nx
from pydent.browser import Browser
from pydent.models import FieldValue, Operation
from pydent.planner.layout import PlannerLayout
from pydent.planner.utils import arr_to_pairs, _id_getter, get_subgraphs
from pydent.utils import filter_list, make_async, logger

import random

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


class Planner(logger.Loggable, object):
    """A user-interface for making experimental plans and layouts."""

    class ITEM_SELECTION_PREFERENCE:

        ANY = "ANY"  # pick the first item that matches the set field_value
        RESTRICT = "RESTRICT"  # restrict to the currently set allowable_field_type
        PREFERRED = "PREFERRED"  # (default) pick the item that matches the currently set allowable_field_type, else
        # pick ANY item that matches the set field_value
        _DEFAULT = PREFERRED
        _CHOICES = [ANY, RESTRICT, PREFERRED]

    class ITEM_ORDER_PREFERENCE:

        FIRST = "FIRST" # select first item
        LAST = "LAST" # select last item
        RANDOM = "RANDOM" # select random item
        _DEFAULT = LAST
        _CHOICES = [FIRST, LAST, RANDOM]

    def __init__(self, session, plan_id=None):
        self.session = session
        self._browser = Browser(session)
        self.plan_id = plan_id
        if self.plan_id is not None:
            self.plan = self._browser.find(self.plan_id, 'Plan')
            if self.plan is None:
                raise PlannerException(
                    "Could not find plan with id={}".format(plan_id))
            self.cache()
        else:
            self.plan = session.Plan.new()
        self.init_logger("Planner@plan_rid={}".format(self.plan.rid))

    def cache(self):
        # ots = self.browser.where('OperationType', {'deployed': True})
        # self.browser.retrieve(ots, 'field_types')
        results = self._browser.recursive_retrieve([self.plan], {
            "operations": {
                "field_values": {
                    "wires_as_dest": ["source", "destination"],
                    "wires_as_source": ["source", "destination"],
                    "sample": [],
                    "item": [],
                    "operation": [],
                    "field_type": []
                },
                "operation_type": {
                    "field_types": []
                }
            }
        })
        wires = results['wires_as_dest'] + results['wires_as_source']
        self.plan.wires = wires

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
        if self.plan.id:
            raise PlannerException("Cannot create plan since it already exists on the server (plan_id={})"
                                   " Did you mean .{save}() push an update to the server plan? You"
                                   " can also create a copy of the new plan by calling .{replan}().".format(
                plan_id=self.plan.id,
                save=self.save.__name__,
                replan=self.replan.__name__
            ))
        self.plan.create()

    def save(self):
        """Save the plan on Aquarium"""
        self.plan.save()
        return self.plan

    def create_operation_by_type(self, ot, status="planning"):
        op = ot.instance()
        op.status = status
        self.plan.add_operation(op)
        self._info("{} created".format(ot.name))
        return op

    def create_operation_by_id(self, ot_id):
        # ot = self.browser.find('OperationType', ot_id)
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
            if model1._primary_key == model2._primary_key:
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
                self._info("found wire from {} to {}".format(fv1.name, fv2.name))
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
        if wire:
            self._info("removing wire from {} to {}".format(fv1.name, fv2.name))
            fv1.wires_as_source.remove(wire)
            fv2.wires_as_dest.remove(wire)
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
            raise PlannerException(
                "Cannot resolve inputs, type must be a FieldValue or Operation, not a \"{}\"".format(type(destination)))

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
        self._info("QUICK CREATE CHAIN {}".format(op_or_otnames))
        ops = [self._resolve_op(n, category=category) for n in op_or_otnames]
        # self.browser.recursive_retrieve(
        #     ops, {
        #         'operation_type': {
        #             "field_types": "allowable_field_types"
        #         }
        #     }
        # )
        if any([op for op in ops if op is None]):
            raise Exception("Could not find some operations: {}".format(ops))
        pairs = arr_to_pairs(ops)
        for op1, op2 in pairs:
            self.quick_wire(op1, op2)
        return ops

    def _select_empty_input_array(self, op, fvname):
        """
        Selects the first 'empty' (i.e. field_values with no Sample set)
        field value in the :class:`FieldValue` array.
        Returns None if the FieldType is not an array. If there are no current
        'empty' field values, a new one is instantiated and returned.

        :param op: Operation
        :param fvname: FieldType/FieldValue name of the array
        :return:
        """
        field_type = op.operation_type.field_type(fvname, 'input')
        if field_type.array:
            existing_fvs = op.input_array(fvname)
            for fv in existing_fvs:
                if fv.sample is None and not self.get_incoming_wires(fv):
                    return fv
            fv = op.add_to_field_value_array(field_type.name, "input")
            return fv

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
        # TODO: automatically wire to empty FV if they are equivalent
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

                # input_fv = None
                if input_ft.array:
                    input_fv = self._select_empty_input_array(destination, input_ft.name)
                else:
                    input_fv = destination.input(input_ft.name)
                output_fv = source.output(output_ft.name)
                return self.add_wire(output_fv, input_fv)

        elif len(afts) == 0:
            raise PlannerException(
                "Cannot quick wire. No possible wiring found between inputs [{}] for {} and outputs [{}] for {}".format(
                    ', '.join([fv.name for fv in model_inputs]),
                    model_inputs[0].operation.operation_type.name,
                    ', '.join([fv.name for fv in model_outputs]),
                    model_outputs[0].operation.operation_type.name))

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
        if wire is None:
            # wire does not exist, so create it
            self._set_wire(fv1, fv2)
            self.plan.wire(fv1, fv2)
            self._info("wired {} to {}".format(fv1.name, fv2.name))
        return wire

    @classmethod
    def _routing_id(cls, fv):
        routing_id = "{}_{}".format(_id_getter(fv.operation), fv.field_type.routing)
        if fv.field_type.array and fv.role == "input":
            other_fvs = fv.operation.input_array(fv.name)
            for pos, other_fv in enumerate(other_fvs):
                if cls.models_are_equal(other_fv, fv):
                    routing_id += str(pos)
                    return routing_id
        return routing_id

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

    # TODO: Support for row and column
    # TODO: routing dict does not work with input arrays (it groups them ALL together)
    @plan_verification_wrapper
    def set_field_value(self, field_value, sample=None, item=None, container=None, value=None, row=None, column=None):
        self._info("setting field_value {}".format(field_value.name))
        field_value.set_value(
            sample=sample, item=item, container=container, value=value, row=None, column=None)
        if not field_value.field_type.array:
            routing = field_value.field_type.routing
            fvs = self.get_routing_dict(field_value.operation)[routing]
            if field_value.field_type.ftype == 'sample':
                for fv in fvs:
                    fv.set_value(sample=sample)
        return field_value

    def set_input_field_value_array(self, op, field_value_name, sample=None, item=None, container=None):
        """
        Finds the first 'empty' (no incoming wires and no sample set) field value and set the field value.
        If there are no empty field values in the array, create a new field value and set that one.

        :param op: operation
        :type op: Operation
        :param field_value_name: field value name
        :type field_value_name: basestring
        :param sample: the sample to set
        :type sample: Sample
        :param item: the item to set
        :type item: Item
        :param container: the container type to set
        :type container: ObjectType
        :return: the set field value
        :rtype: FieldValue
        """
        input_fv = self._select_empty_input_array(op, field_value_name)
        return self.set_field_value(input_fv, sample=sample, item=item, container=container)

    def set_field_value_and_propogate(self, field_value, sample=None):
        # ots = self.browser.where('OperationType', {"id": [op.operation_type_id for op in self.plan.operations]})
        # self.browser.retrieve(ots, 'field_types')
        routing_graph = self._routing_graph()
        routing_id = self._routing_id(field_value)
        subgraph = nx.bfs_tree(routing_graph.to_undirected(), routing_id)
        for node in subgraph:
            n = routing_graph.node[node]
            fv = n['fv']
            self.set_field_value(fv, sample=sample)
        return field_value

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

    def _item_preference_query(self, sample, field_value, item_preference):
        if item_preference not in self.ITEM_SELECTION_PREFERENCE._CHOICES:
            raise PlannerException("Item selection preference \"{}\" not recognized"
                                   " Please select from one of {}".format(item_preference, ','.join(
                self.ITEM_SELECTION_PREFERENCE._CHOICES)))
        query = {"sample_id": sample.id}

        # restrict allowable_field_types based on preference
        afts = list(field_value.field_type.allowable_field_types)

        if item_preference == self.ITEM_SELECTION_PREFERENCE.RESTRICT:
            afts = [field_value.allowable_field_type]
        elif item_preference in [self.ITEM_SELECTION_PREFERENCE.ANY, self.ITEM_SELECTION_PREFERENCE.PREFERRED]:
            afts = [aft for aft in field_value.field_types if aft.sample]
        if item_preference == self.ITEM_SELECTION_PREFERENCE.PREFERRED:
            afts = sorted(afts, reverse=True, key=lambda aft: aft.sample_type_id==sample.sample_type_id)

        query.update({"object_type_id": [aft.object_type_id for aft in afts]})
        return query

    @plan_verification_wrapper
    def get_available_items(self, field_value, item_preference):
        sample = field_value.sample
        if not sample:
            return []

        if item_preference not in self.ITEM_SELECTION_PREFERENCE._CHOICES:
            raise PlannerException("Item selection preference \"{}\" not recognized"
                                   " Please select from one of {}".format(item_preference, ','.join(
                self.ITEM_SELECTION_PREFERENCE._CHOICES)))
        query = {"sample_id": sample.id}

        # restrict allowable_field_types based on preference
        afts = list(field_value.field_type.allowable_field_types)

        if item_preference == self.ITEM_SELECTION_PREFERENCE.RESTRICT:
            afts = [field_value.allowable_field_type]
        elif item_preference in [self.ITEM_SELECTION_PREFERENCE.ANY, self.ITEM_SELECTION_PREFERENCE.PREFERRED]:
            afts = filter_list(afts, sample_type_id=sample.sample_type_id)

        if item_preference == self.ITEM_SELECTION_PREFERENCE.PREFERRED:
            afts = sorted(afts, reverse=True, key=lambda aft: aft.sample_type_id == sample.sample_type_id)

        if not afts:
            return []

        query.update({"object_type_id": [aft.object_type_id for aft in afts]})

        available_items = self.session.Item.where(query)
        available_items = [i for i in available_items if i.location != 'deleted']
        return available_items

    @plan_verification_wrapper
    def set_to_available_item(self, fv, order_preference=ITEM_ORDER_PREFERENCE._DEFAULT, filter_func=None,
                              item_preference=ITEM_SELECTION_PREFERENCE._DEFAULT):
        """
        Sets the item of the field value to the next available item. Setting recent=False will select
        the oldest item.

        :param fv: The field value to set.
        :type fv: FieldValue
        :param recent: whether to select the most recent item (recent=True is default)
        :type recent: bool
        :param filter_func: array of lambda to filter items by. E.g. 'lambda_arr=[lambda x: x.get("concentration") > 10]'
        :type filter_func: list
        :param order_preference: The item order preference. Select from "LAST" (default), "FIRST", or "RANDOM". Selections
                                also available in :class:`Planner.ITEM_ORDER_PREFERENCE`. Random will choose a random item
                                from the available items found after all preferences and filters
        :type order_preference: basestring
        :param item_preference: The item selection preference. Select from items in :class:`Planner.ITEM_SELECTION_PREFERENCE`
                                If "PREFERRED" (default), will select item that matches the allowable_field_value that is
                                already set for the field_value, else select any item that matches the :class:`Sample` set :class:`FieldValue`. If
                                "RESTRICT", will restrict selected item only to those that matches the current allowable_field_value
                                that is set for the :class:`FieldValue`. If "ANY", will select any items that matches the :class:`Sample`.
                                set for the field_value
        :type item_preference: basestring
        :return: The selected item (or None if no item set)
        :rtype: Item or None
        """
        sample = fv.sample
        item = None

        if sample is not None:
            available_items = self.get_available_items(fv, item_preference)
            if filter_func is not None:
                if not isinstance(filter_func, list):
                    filter_func = [filter_func]
                available_items = self._filter_by_lambdas(available_items, filter_func)

            if not available_items:
                return None

            available_items = sorted(available_items, key=lambda x: x.created_at)

            selection_index = -1
            if order_preference == self.ITEM_ORDER_PREFERENCE.FIRST:
                selection_index = 0
            elif order_preference == self.ITEM_ORDER_PREFERENCE.LAST:
                selection_index = -1
            elif order_preference == self.ITEM_ORDER_PREFERENCE.RANDOM:
                selection_index = random.randint(0, len(available_items)-1)
            item = available_items[selection_index]
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

    def find_operation(self, opid):
        for op in self.plan.operations:
            if op._primary_key == opid:
                return op

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

        x = layout.midpoint()[0] + layout.BOX_WIDTH / 2  # adjust so x is midpoint of 'box' on screen
        y = layout.y

        # center the annotation
        x -= width / 2
        y -= height

        # give some space between annotation and operation
        y -= layout.BOX_DELTA_Y / 2

        return self.annotate(markdown, x, y, width, height)

    @property
    def layout(self):
        return PlannerLayout.from_plan(self.plan)

    @staticmethod
    def _fv_to_hash(fv, ft):
        # none valued Samples are never equivalent
        sid = str(uuid4())
        if fv.sample is not None:
            sid = "{}{}".format(fv.role, fv.sample.id)

        item_id = "none"
        if fv.item is not None:
            item_id = "{}{}".format(fv.role, fv.item.id)
        fvhash = "{}:{}:{}:{}".format(
            ft.name, ft.role, sid, item_id)
        if ft.part:
            fvhash += "r{row}:c{column}".format(
                row=fv.row,
                column=fv.column,
            )
        return fvhash

    @classmethod
    def _fv_array_to_hash(cls, fv_array, ft):
        return "*".join([cls._fv_to_hash(fv, ft) for fv in fv_array])

    @classmethod
    def _op_to_hash(cls, op):
        """Turns a operation into a hash using the operation_type_id, item_id, and sample_id"""
        ot_id = op.operation_type.id

        field_type_ids = []
        for ft in op.operation_type.field_types:
            if ft.ftype == "sample":
                if not ft.array:
                    fv = op.field_value(ft.name, ft.role)
                    field_type_ids.append(cls._fv_to_hash(fv, ft))
                else:
                    fv_array = op.field_value_array(ft.name, ft.role)
                    field_type_ids.append(cls._fv_array_to_hash(fv_array, ft))

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
        self._info("Optimizing plan...")
        if operations is not None:
            self._info("   only_operations={}".format([op.id for op in operations]))
        self._info("   ignore_types={}".format(ignore))
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
                                self.remove_wire(w.source, w.destination)
                                self.add_wire(w.source, op.input(i.name))
                                num_inputs_rewired += 1
                    for o in other_op.outputs:
                        out_wires = self.get_outgoing_wires(o)
                        for w in out_wires:
                            if w.destination.operation.status == "planning":
                                self.remove_wire(w.source, w.destination)
                                self.add_wire(op.output(o.name), w.destination)
                                num_outputs_rewired += 1
                    ops_to_remove.append(other_op)
        for op in ops_to_remove:
            self.plan.operations.remove(op)
        self._info("\t{} operations removed".format(len(ops_to_remove)))
        self._info("\t{} input wires re-wired".format(num_inputs_rewired))
        self._info("\t{} output wires re-wired".format(num_outputs_rewired))

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
                    reasons.append(
                        "{} {} for {} has no sample defined".format(fv.role, fv.name, fv.operation.operation_type.name))
                else:
                    values.append(value)
                if len(list(subgraph.predecessors(n))) == 0:
                    root = fv
            if root.item is None and root.role == "input" and root.field_type.ftype == 'sample':
                reasons.append(
                    "{} {} for {} has no item defined".format(fv.role, fv.name, fv.operation.operation_type.name))
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
