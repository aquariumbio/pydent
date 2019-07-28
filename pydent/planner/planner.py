"""
Planner
"""

import random
import webbrowser
from collections import defaultdict
from functools import wraps
from uuid import uuid4

import networkx as nx

from pydent.aqsession import AqSession
from pydent.models import FieldValue, Operation, Plan, OperationType
from pydent.planner.layout import PlannerLayout
from pydent.planner.utils import arr_to_pairs, _id_getter, get_subgraphs
from pydent.utils import make_async, Loggable, empty_copy
from copy import deepcopy

import itertools


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
                "Cannot apply 'verify_plan_models' to a non-planner instance."
            )
        for arg in args:
            if issubclass(arg.__class__, FieldValue):
                fv = arg
                if not self._contains_op(fv.operation):
                    fv_ref = "{} {}".format(fv.role, fv.name)
                    msg = 'FieldValue "{}" not found in planner.'
                    raise PlannerException(msg.format(fv_ref))
            elif issubclass(arg.__class__, Operation):
                op = arg
                if not self._contains_op(op):
                    op_ref = "{}".format(op.operation_type.name)
                    msg = 'Operation "{}" not found in planner.'
                    raise PlannerException(msg.format(op_ref))
        return fxn(self, *args, **kwargs)

    return wrapper


class AFTMatcher(object):
    @staticmethod
    def _resolve_to_field_types(model, role=None):
        if isinstance(model, FieldValue):
            if model.role == role:
                return [model.field_type]
            else:
                msg = (
                    "Planner attempted to find matching"
                    " allowable_field_types for"
                    " an input FieldValue but found an output FieldValue"
                )
                raise PlannerException(msg)
        elif isinstance(model, Operation):
            return [ft for ft in model.get_field_types() if ft.role == role]
        else:
            raise PlannerException(
                'Cannot resolve inputs, type must be a FieldValue or Operation, not a "{}"'.format(
                    type(model)
                )
            )

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
        dest_fts = cls._resolve_to_field_types(destination, role="input")
        src_fts = cls._resolve_to_field_types(source, role="output")

        matching_afts = []
        matching_inputs = []
        matching_outputs = []
        for src in src_fts:
            for dest in dest_fts:
                io_matching_afts = cls._find_matching_afts(src, dest)
                if len(io_matching_afts) > 0:
                    if dest not in matching_inputs:
                        matching_inputs.append(dest)
                    if src not in matching_outputs:
                        matching_outputs.append(src)
                matching_afts += io_matching_afts
        return matching_afts, matching_inputs, matching_outputs

    @staticmethod
    def _find_matching_afts(src_ft, dest_ft):
        """Finds matching afts between two FieldTypes"""
        afts = []
        src_afts = src_ft.allowable_field_types
        dest_afts = dest_ft.allowable_field_types

        # check whether the field_type handles collections
        input_handles_collections = dest_ft.part is True
        output_handles_collections = dest_ft.part is True
        if input_handles_collections != output_handles_collections:
            return []

        for dest_aft in dest_afts:
            for src_aft in src_afts:
                out_object_type_id = src_aft.object_type_id
                in_object_type_id = dest_aft.object_type_id
                out_sample_type_id = src_aft.sample_type_id
                in_sample_type_id = dest_aft.sample_type_id
                if (
                    out_object_type_id == in_object_type_id
                    and out_sample_type_id == in_sample_type_id
                ):
                    afts.append((src_aft, dest_aft))
        return afts


class Planner(AFTMatcher, object):
    """A user-interface for making experimental plans and layouts."""

    class ITEM_SELECTION_PREFERENCE:

        ANY = "ANY"  # pick the first item that matches the set field_value
        RESTRICT = "RESTRICT"  # restrict to the currently set allowable_field_type
        PREFERRED = (
            "PREFERRED"
        )  # (default) pick the item that matches the currently set allowable_field_type, else
        # pick ANY item that matches the set field_value
        RESTRICT_TO_ONE = (
            "RESTRICT TO ONE"
        )  # will not select item if its being used in another active operation
        _DEFAULT = PREFERRED
        _CHOICES = [ANY, RESTRICT, PREFERRED, RESTRICT_TO_ONE]

    class ITEM_ORDER_PREFERENCE:

        FIRST = "FIRST"  # select first item
        LAST = "LAST"  # select last item
        RANDOM = "RANDOM"  # select random item
        _DEFAULT = LAST
        _CHOICES = [FIRST, LAST, RANDOM]

    def __init__(self, session_or_plan=None, plan_id=None):
        if issubclass(type(session_or_plan), AqSession):
            # initialize with session
            self.session = session_or_plan

            if plan_id is not None:
                # load an existing plan
                plan = self.browser.find(plan_id, "Plan")
                if plan is None:
                    raise PlannerException(
                        "Could not find plan with id={}".format(plan_id)
                    )
                self.plan = plan
            else:
                # create a new plan
                self.plan = self.session.Plan.new()
        elif issubclass(type(session_or_plan), Plan):
            # initialize with Plan
            plan = session_or_plan
            self.session = plan.session
            self.plan = plan
        self.log = Loggable(self, "Planner@plan_rid={}".format(self.plan.rid))

    @property
    def browser(self):
        return self.session.browser

    @classmethod
    def _check_plans_for_single_session(cls, models):
        session_ids = set([id(m.session) for m in models])
        if len(session_ids) > 1:
            raise PlannerException("Plans have different session ids")
        if models:
            return models[0].session

    @staticmethod
    def _cache_query():
        return {
            "operations": {
                "field_values": {
                    "wires_as_dest": {
                        "source": "operation",
                        "destination": "operation",
                    },
                    "wires_as_source": {
                        "source": "operation",
                        "destination": "operation",
                    },
                    "sample": [],
                    "item": [],
                    "operation": [],
                    "field_type": [],
                },
                "plan_associations": ["plan"],
                "operation_type": {"field_types": []},
            }
        }

    @property
    def plan(self):
        return self._plan

    @plan.setter
    def plan(self, new_plan):
        self._plan = new_plan
        self.cache()

    @classmethod
    def cache_plans(cls, browser, plans):
        browser.recursive_retrieve(plans, cls._cache_query())
        for plan in plans:
            wire_dict = {}
            if plan.operations:
                for op in plan.operations:
                    for fv in op.field_values:
                        for w in fv.wires_as_dest:
                            wire_dict[w._primary_key] = wire_dict.get(w._primary_key, w)
                        for w in fv.wires_as_source:
                            wire_dict[w._primary_key] = wire_dict.get(w._primary_key, w)
            plan.wires = list(wire_dict.values())
        return plans

    def cache(self):
        self.cache_plans(self.browser, [self.plan])

    @property
    def name(self):
        return self.plan.name

    @name.setter
    def name(self, value):
        self.plan.name = value

    @property
    def url(self):
        return self.session.url + "/plans?plan_id={}".format(self.plan.id)

    def open(self):
        webbrowser.open(self.url)

    def create(self):
        """Create the plan on Aquarium"""
        if self.plan.id:
            raise PlannerException(
                "Cannot create plan since it already exists on the server (plan_id={})"
                " Did you mean .{save}() push an update to the server plan? You"
                " can also create a copy of the new plan by calling .{replan}().".format(
                    plan_id=self.plan.id,
                    save=self.save.__name__,
                    replan=self.replan.__name__,
                )
            )

        self.plan.create()

    # TODO: fix this 'set_timeout' to not be global
    def save(self):
        if not self.plan.id:
            self.create()
        else:
            self.update()

    def update(self):
        """Save the plan on Aquarium"""
        self.plan.save()
        return self.plan

    def create_operation_by_type(self, ot, status="planning"):
        op = ot.instance()
        op.status = status
        self.plan.add_operation(op)
        self.log.info("{} created".format(ot.name))
        return op

    def create_operation_by_type_id(self, ot_id):
        # ot = self.browser.find('OperationType', ot_id)
        ot = self.session.OperationType.find(ot_id)
        return self.create_operation_by_type(ot)

    def create_operation_by_name(self, operation_type_name, category=None):
        """Adds a new operation to the plan"""
        query = {"deployed": True, "name": operation_type_name}
        if category is not None:
            query["category"] = category
        ots = self.session.OperationType.where(query)
        if len(ots) > 1:
            msg = 'Found more than one OperationType for query "{}". Have you tried specifying the category?'
            raise PlannerException(msg.format(query))
        if ots is None or len(ots) == 0:
            msg = 'Could not find deployed OperationType "{}".'
            raise PlannerException(msg.format(operation_type_name))
        return self.create_operation_by_type(ots[0])

    def new_op(self, name_id_or_ot):
        if isinstance(name_id_or_ot, str):
            return self.create_operation_by_name(name_id_or_ot)
        elif isinstance(name_id_or_ot, int):
            return self.create_operation_by_type_id(name_id_or_ot)
        elif issubclass(type(name_id_or_ot), OperationType):
            return self.create_operation_by_type(name_id_or_ot)
        else:
            raise PlannerException(
                "Expected a string, integer, or OperationType, "
                "not a {}".format(type(name_id_or_ot))
            )

    @staticmethod
    def _model_are_equal(model1, model2):
        if model1.id is None and model2.id is None:
            if model1._primary_key == model2._primary_key:
                return True
        elif model1.id == model2.id:
            return True
        return False

    def get_op(self, id):
        for op in self.plan.operations:
            if op.id == id:
                return op

    @plan_verification_wrapper
    def get_wire(self, fv1, fv2):
        for wire in self.plan.wires:
            if self._model_are_equal(wire.source, fv1) and self._model_are_equal(
                wire.destination, fv2
            ):
                self.log.info("found wire from {} to {}".format(fv1.name, fv2.name))
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
        wires = list(self.plan.wires)
        if wire:
            self.log.info("removing wire from {} to {}".format(fv1.name, fv2.name))
            wires_as_source = fv1.wires_as_source
            wires_as_dest = fv2.wires_as_dest

            wires_as_source.remove(wire)
            wires_as_dest.remove(wire)

            fv1.wires_as_source = wires_as_source
            fv2.wires_as_dest = wires_as_dest

            wires.remove(wire)
            self.plan.wires = wires
        return wire

    @plan_verification_wrapper
    def get_outgoing_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self._model_are_equal(wire.source, fv):
                wires.append(wire)
        return wires

    @plan_verification_wrapper
    def get_incoming_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self._model_are_equal(wire.destination, fv):
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

    def chain(self, *op_or_otnames, category=None, return_as_dict=False):
        """
        Creates a chain of operations by *guessing* wires between operations
        based on the AllowableFieldTypes between the inputs and outputs of each
        operation type.
        Sample inputs and outputs will be set along the wire if possible.

        e.g.

        .. code::

            # create four new operations based on their OperationType names
            planner.chain("Make PCR Fragment", "Run Gel",
                                      "Extract Gel Slice", "Purify Gel Slice")

            # create four new operations based on their OperationType names by
            # finding OperationTypes only in the "Cloning" category
            planner.chain("Make PCR Fragment", "Run Gel",
                                      "Extract Gel Slice", "Purify Gel Slice",
                                      category="Cloning")

            # create four new operations based on their OperationType names by
            # finding OperationTypes only in the "Cloning" category,
            # except find "Make PCR Fragment" in the "Cloning Sandbox" category
            planner.chain(("Make PCR Fragment", "Cloning Sandbox"),
                                       "Run Gel", "Extract Gel Slice",
                                       "Purify Gel Slice", category="Cloning")

            # create and wire new operations to an existing operations while
            # routing samples
            pcr_op = planner.create_operation_by_name("Make PCR Fragment")
            planner.set_field_value(pcr_op.outputs[0], sample=my_sample)
            new_ops = planner.chain(pcr_op, "Run Gel")
            run_gel = new_ops[1]
            planner.chain("Pour Gel", run_gel)
        """
        self.log.info("QUICK CREATE CHAIN {}".format(op_or_otnames))
        ops = [self._resolve_op(n, category=category) for n in op_or_otnames]
        if any([op for op in ops if op is None]):
            raise Exception("Could not find some operations: {}".format(ops))
        pairs = arr_to_pairs(ops)
        for op1, op2 in pairs:
            self.quick_wire(op1, op2)
        if return_as_dict:
            return_dict = {}
            for op in ops:
                return_dict.setdefault(op.operation_type.name, []).append(op)
            return return_dict
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
        field_type = op.operation_type.field_type(fvname, "input")
        if field_type.array:
            existing_fvs = op.input_array(fvname)
            for fv in existing_fvs:
                if fv.sample is None and not self.get_incoming_wires(fv):
                    return fv
            fv = op.new_field_value(field_type.name, "input")
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
            source, destination
        )

        # TODO: only if matching FVs are ambiguous raise Exception
        # TODO: automatically wire to empty FV if they are equivalent
        if (len(model_inputs) > 1 or len(model_outputs) > 1) and strict:
            raise PlannerException(
                "Cannot quick wire. Ambiguous wiring between inputs [{}] for {} and outputs [{}] for {}\n"
                "Instead, try to use `add_wire` method to wire together two FieldValues.".format(
                    ", ".join([ft.name for ft in model_inputs]),
                    model_inputs[0].operation_type.name,
                    ", ".join([ft.name for ft in model_outputs]),
                    model_outputs[0].operation_type.name,
                )
            )
        elif len(afts) > 0:
            for aft1, aft2 in afts:

                input_ft = aft2.field_type
                output_ft = aft1.field_type

                # input_fv = None
                if input_ft.array:
                    input_fv = self._select_empty_input_array(
                        destination, input_ft.name
                    )
                else:
                    input_fv = destination.input(input_ft.name)
                output_fv = source.output(output_ft.name)

                return self.add_wire(output_fv, input_fv)

        elif len(afts) == 0:
            raise PlannerException(
                "Cannot quick wire. No possible wiring found between inputs {} and {}".format(
                    source, destination
                )
            )

    def quick_wire_by_name(self, otname1, otname2):
        """Wires together the last added operations."""
        op1 = self.get_op_by_name(otname1)[-1]
        op2 = self.get_op_by_name(otname2)[-1]
        return self.quick_wire(op1, op2)

    def clean_wires(self):
        wires_by_id = {}
        for wire in self.plan.wires:
            if wire.source is not None and wire.destination is not None:
                _id = "{}_{}".format(
                    wire.source._primary_key, wire.destination._primary_key
                )
                wires_by_id[_id] = wire
        for op in self.plan.operations:
            for fv in op.field_values:
                wires_as_source = fv.wires_as_source
                wires_as_dest = fv.wires_as_dest

                if wires_as_source is None:
                    wires_as_source = []
                if wires_as_dest is None:
                    wires_as_dest = []

                fv.wires_as_source = list(set(wires_as_source))
                fv.wires_as_dest = list(set(wires_as_dest))
        self.plan.wires = list(wires_by_id.values())

    def remove_operations(self, ops):
        self.clean_wires()
        operations = self.plan.operations
        wires = set(self.plan.wires)
        wires_to_remove = set()

        for op in ops:
            operations.remove(op)
            for fv in op.field_values:
                wires_to_remove = wires_to_remove.union(set(fv.wires_as_source))
                wires_to_remove = wires_to_remove.union(set(fv.wires_as_dest))

        wires = list(wires.difference(wires_to_remove))

        self.plan.operations = operations
        self.plan.wires = wires

    # TODO: resolve afts if already set...
    # TODO: clean up _set_wire
    def _set_wire(self, src_fv, dest_fv, preference="source", setter=None):

        if len(self.get_incoming_wires(dest_fv)) > 0:
            raise PlannerException(
                'Cannot wire because "{}" already has an incoming wire and inputs'
                " can only have one incoming wire. Please remove wire"
                " using 'canvas.remove_wire(src_fv, dest_fv)' before setting.".format(
                    dest_fv.name
                )
            )

        # first collect any matching allowable field types between the field values
        aft_pairs = self._collect_matching_afts(src_fv, dest_fv)[0]

        if len(aft_pairs) == 0:
            raise PlannerException(
                'Cannot wire "{}" to "{}". No allowable field types match.'.format(
                    src_fv.name, dest_fv.name
                )
            )

        # select the first aft
        default_aft_ids = [
            src_fv.allowable_field_type_id,
            dest_fv.allowable_field_type_id,
        ]
        pref_index = 0
        if preference == "destination":
            pref_index = 1
        selected_aft_pair = aft_pairs[0]
        for pair in aft_pairs:
            if pair[pref_index].id == default_aft_ids[pref_index]:
                selected_aft_pair = pair
        assert (
            selected_aft_pair[0].object_type_id == selected_aft_pair[1].object_type_id
        )

        # resolve sample
        samples = [src_fv.sample, dest_fv.sample]
        samples = [s for s in samples if s is not None]

        if setter is None:
            setter = self.set_field_value

        if len(samples) > 0:
            selected_sample = samples[pref_index]

            # filter afts by sample_type_id
            aft_pairs = [
                aft
                for aft in aft_pairs
                if aft[0].sample_type_id == selected_sample.sample_type_id
            ]
            selected_aft_pair = aft_pairs[0]

            if len(aft_pairs) == 0:
                raise PlannerException(
                    "No allowable_field_types were found for FieldValues {} & {} for"
                    " Sample {}".format(src_fv.name, dest_fv.name, selected_sample.name)
                )

            setter(src_fv, sample=selected_sample)
            setter(dest_fv, sample=selected_sample)

            assert (
                selected_aft_pair[0].sample_type_id
                == selected_aft_pair[1].sample_type_id
            )
            assert selected_aft_pair[0].sample_type_id == src_fv.sample.sample_type_id
            assert selected_aft_pair[0].sample_type_id == dest_fv.sample.sample_type_id

            # set the sample (and allowable_field_type)
            if src_fv.sample is not None and (
                dest_fv.sample is None or dest_fv.sample.id != src_fv.sample.id
            ):
                setter(
                    dest_fv,
                    sample=src_fv.sample,
                    container=selected_aft_pair[0].object_type,
                )
            elif dest_fv.sample is not None and (
                src_fv.sample is None or dest_fv.sample.id != src_fv.sample.id
            ):
                setter(
                    src_fv,
                    sample=dest_fv.sample,
                    container=selected_aft_pair[0].object_type,
                )

        setter(src_fv, container=selected_aft_pair[0].object_type)
        setter(dest_fv, container=selected_aft_pair[0].object_type)

    @plan_verification_wrapper
    def add_wire(self, fv1, fv2):
        """Note that fv2.operation will not inherit parent_id of fv1"""
        wire = self.get_wire(fv1, fv2)
        if wire is None:
            # wire does not exist, so create it
            self._set_wire(fv1, fv2)
            wire = self.plan.wire(fv1, fv2)
            self.log.info("wired {} to {}".format(fv1.name, fv2.name))
        return wire

    @classmethod
    def _routing_id(cls, fv):
        routing_id = "{}_{}".format(_id_getter(fv.operation), fv.field_type.routing)
        if fv.field_type.array and fv.role == "input":
            other_fvs = fv.operation.input_array(fv.name)
            for pos, other_fv in enumerate(other_fvs):
                if cls._model_are_equal(other_fv, fv):
                    routing_id += str(pos)
                    return routing_id
        return routing_id

    @staticmethod
    def get_sample_routing_of_operation(op):
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
    def set_field_value(
        self,
        field_value,
        sample=None,
        item=None,
        container=None,
        value=None,
        row=None,
        column=None,
    ):
        self.log.info(
            "setting field_value {} to {} - {} - {} - {}".format(
                field_value.name, sample, item, container, value
            )
        )
        field_value.set_value(
            sample=sample,
            item=item,
            container=container,
            value=value,
            row=None,
            column=None,
        )
        if not field_value.field_type.array:
            routing = field_value.field_type.routing
            fvs = self.get_sample_routing_of_operation(field_value.operation)[routing]
            if field_value.field_type.ftype == "sample":
                for fv in fvs:
                    fv.set_value(sample=sample)
        return field_value

    def set_input_field_value_array(
        self, op, field_value_name, sample=None, item=None, container=None
    ):
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
        return self.set_field_value(
            input_fv, sample=sample, item=item, container=container
        )

    def set_field_value_and_propogate(self, field_value, sample=None):
        # ots = self.browser.where('OperationType', {"id": [op.operation_type_id for op in self.plan.operations]})
        # self.browser.retrieve(ots, 'field_types')
        routing_graph = self._routing_graph()
        routing_id = self._routing_id(field_value)
        subgraph = nx.bfs_tree(routing_graph.to_undirected(), routing_id)
        for node in subgraph:
            n = routing_graph.node[node]
            fv = n["fv"]
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
            raise PlannerException(
                'Item selection preference "{}" not recognized'
                " Please select from one of {}".format(
                    item_preference, ",".join(self.ITEM_SELECTION_PREFERENCE._CHOICES)
                )
            )
        query = {"sample_id": sample.id}

        # restrict allowable_field_types based on preference
        afts = list(field_value.field_type.allowable_field_types)

        if item_preference in [
            self.ITEM_SELECTION_PREFERENCE.RESTRICT,
            self.ITEM_SELECTION_PREFERENCE.RESTRICT_TO_ONE,
        ]:
            afts = [field_value.allowable_field_type]
        # elif item_preference in [self.ITEM_SELECTION_PREFERENCE.ANY, self.ITEM_SELECTION_PREFERENCE.PREFERRED]:
        #     afts = [aft for aft in field_value.field_type.allowable_field_types if aft.sample]
        if item_preference == self.ITEM_SELECTION_PREFERENCE.PREFERRED:
            afts = sorted(
                afts,
                reverse=True,
                key=lambda aft: aft.sample_type_id == sample.sample_type_id,
            )

        query.update({"object_type_id": [aft.object_type_id for aft in afts]})
        return query

    def reserved_items(self, items):
        """Returns a dictionary of item_ids and the array of field_values that use them"""
        browser = self.browser
        item_ids = [i.id for i in items]
        server_fvs = browser.where(
            {"child_item_id": item_ids}, model_class="FieldValue"
        )
        browser.retrieve(server_fvs, "operation")
        server_fvs = [fv for fv in server_fvs if fv.operation.status != "planning"]

        these_fvs = []
        for op in self.plan.operations:
            for fv in op.inputs:
                if fv.child_item_id in item_ids:
                    these_fvs.append(fv)

        fvs = list(set(server_fvs + these_fvs))

        item_id_to_fv = defaultdict(list)
        for fv in fvs:
            item_id_to_fv[fv.child_item_id].append(fv)
        return item_id_to_fv

    @plan_verification_wrapper
    def get_available_items(self, field_value, item_preference):
        sample = field_value.sample
        if not sample:
            return []

        query = self._item_preference_query(sample, field_value, item_preference)
        available_items = self.session.Item.where(query)
        available_items = [i for i in available_items if i.location != "deleted"]

        x = len(available_items)
        if item_preference == self.ITEM_SELECTION_PREFERENCE.RESTRICT_TO_ONE:
            reserved = self.reserved_items(available_items)
            available_items = [i for i in available_items if len(reserved[i.id]) == 0]
            self.log.info("{} items are reserved".format(x - len(available_items)))
        return available_items

    def distribute_items_of_object_type(self, object_type):
        """Distribute items of a particular object_type across non-planning operations across
         existing plans and these operations in this Planner instance. E.g. distributing
         one-shot yeast competent cell aliquots"""
        # collect items of that type used
        items = []
        browser = self.browser
        for op in self.plan.operations:
            for i in op.inputs:
                item = i.item
                if item:
                    if item.object_type_id == object_type.id:
                        items.append(item)

        # find all field_values that use this item
        item_id_to_fv = defaultdict(list)
        item_ids = [i.id for i in items]
        fvs = browser.where({"child_item_id": item_ids}, model_class="FieldValue")
        browser.retrieve(fvs, "operation")

        for fv in fvs:
            item_id_to_fv[fv.child_item_id].append(fv)

        distributed = []

        for item in items:
            fvs = item_id_to_fv[item.id]

            # filter by operations that are submitted
            fvs = [fv for fv in fvs if fv.operation.status != "planning"]
            if len(fvs) > 1:
                available_items = browser.where(
                    {
                        "sample_id": item.sample_id,
                        "object_type_id": item.object_type_id,
                    },
                    model_class="Item",
                )
                available_items = [
                    item for item in available_items if item.location != "deleted"
                ]
                print(
                    "Item {} {} is used in {} inputs. There are {} available items.".format(
                        item.id, item.sample.name, len(fvs), len(available_items)
                    )
                )

                for fv, item in itertools.zip_longest(
                    fvs, available_items, fillvalue="&&&"
                ):
                    if fv != "&&&" and item != "&&&":
                        distributed.append(fv, item)

        for fv, item in distributed:
            fv.set_value(item=item)

    @plan_verification_wrapper
    def set_to_available_item(
        self,
        fv,
        order_preference=ITEM_ORDER_PREFERENCE._DEFAULT,
        filter_func=None,
        item_preference=ITEM_SELECTION_PREFERENCE._DEFAULT,
    ):
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
                selection_index = random.randint(0, len(available_items) - 1)
            item = available_items[selection_index]
            fv.set_value(item=item)
        return item

    @plan_verification_wrapper
    def set_inputs_using_sample_properties(
        self, operation, sample, routing=None, setter=None
    ):
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
    def set_output_sample(self, fv, sample=None, routing=None, setter=None):
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
            raise Exception(
                "Cannot output. FieldValue {} is a/an {}.".format(fv.name, fv.role)
            )
        if setter is None:
            setter = self.set_field_value
        setter(fv, sample=sample)
        op = fv.operation
        self.set_inputs_using_sample_properties(
            op, sample, routing=routing, setter=setter
        )

    @staticmethod
    def _json_update(model, **params):
        """Temporary method to update"""
        aqhttp = model.session._AqSession__aqhttp
        data = {"model": {"model": model.__class__.__name__}}
        data.update(model.dump(**params))
        model_data = aqhttp.create("json/save", json_data=data)
        model.reload(model_data)
        return model

    @classmethod
    def move_op(cls, op, plan_id):
        pa = op.plan_associations[0]
        pa.plan_id = plan_id
        op.parent_id = 0
        cls._json_update(op)
        cls._json_update(pa)

    def get_op_by_name(self, operation_type_name):
        """
        Find operations by their operation_type_name

        :param operation_type_name: The operation type name
        :type operation_type_name: basestring
        :return: list of operations
        :rtype: list
        """
        return [
            op
            for op in self.plan.operations
            if op.operation_type.name == operation_type_name
        ]

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
            "markdown": markdown,
        }
        markdown += "\n<!-- annotated by pydent.planner -->"
        self.plan.layout.setdefault("text_boxes", [])
        if self.plan.layout["text_boxes"] is None:
            self.plan.layout["text_boxes"] = []
        if annotation not in self.plan.layout["text_boxes"]:
            self.plan.layout["text_boxes"].append(annotation)
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

        x = (
            layout.midpoint()[0] + layout.BOX_WIDTH / 2
        )  # adjust so x is midpoint of 'box' on screen
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

    @property
    def graph(self):
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
        fvhash = "{}:{}:{}:{}".format(ft.name, ft.role, sid, item_id)
        if ft.part:
            fvhash += "r{row}:c{column}".format(row=fv.row, column=fv.column)
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
        try:
            from IPython.display import display, HTML

            return display(HTML('<a href="{url}">{url}</a>'.format(url=self.url)))
        except ImportError:
            print("Could not import IPython. This is likely not installed.")

    # TODO: find redundant segments
    # TODO: search functions for plans

    # TODO: procedure should run on topologically sorted operations, if there is the case that
    # two operations have different parents, then these operations are NOT mergable
    def optimize_plan(self, operations=None, ignore=None):
        """
        Optimizes a plan by removing redundent operations.
        :param planner:
        :return:
        """
        self.log.info("Optimizing plan...")
        if operations is not None:
            self.log.info("   only_operations={}".format([op.id for op in operations]))
        self.log.info("   ignore_types={}".format(ignore))
        if operations is None:
            operations = [op for op in self.plan.operations if op.status == "planning"]
        if ignore:
            operations = [
                op for op in operations if op.operation_type.name not in ignore
            ]
        groups = {
            k: v for k, v in self._group_ops_by_hashes(operations).items() if len(v) > 1
        }
        num_inputs_rewired = 0
        num_outputs_rewired = 0
        ops_to_remove = []

        op_graph = PlannerLayout.from_plan(self.plan).G
        sorted_nodes = nx.topological_sort(op_graph)

        visited_groups = []
        for node in sorted_nodes:
            node_data = op_graph.node[node]
            op = node_data["operation"]
            op_hash = self._op_to_hash(op)
            if op_hash in visited_groups or op_hash not in groups:
                continue
            visited_groups.append(op_hash)
            grouped_ops = groups[op_hash]
            op = grouped_ops[0]
            other_ops = grouped_ops[1:]

            # merge wires from other ops into op wires
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

        operations_list = self.plan.operations
        for op in ops_to_remove:
            operations_list.remove(op)
        self.plan.operations = operations_list
        self.log.info("\t{} operations removed".format(len(ops_to_remove)))
        self.log.info("\t{} input wires re-wired".format(num_inputs_rewired))
        self.log.info("\t{} output wires re-wired".format(num_outputs_rewired))

    def roots(self):
        """Get field values that have no predecessors (i.e. are 'roots')"""
        roots = []
        for subgraph in get_subgraphs(self._routing_graph()):
            for n in subgraph:
                node = subgraph.node[n]
                if len(list(subgraph.predecessors(n))) == 0:
                    root = node["fv"]
                    roots.append(root)
        return roots

    def validate(self):
        """
        Validates sample routes in the plan.

        :return: dictionary of each sample route and validation errors
        :rtype: dict
        """

        def fv_info(fv):
            return "{role} {name} for {ot} {opid}".format(
                role=fv.role,
                name=fv.name,
                ot=fv.operation.operation_type.name,
                opid=fv.operation.id,
            )

        routes = {}
        for subgraph in get_subgraphs(self._routing_graph()):
            values = []
            reasons = []
            root = None
            for n in subgraph:
                node = subgraph.node[n]
                fv = node["fv"]
                value = fv.sample
                if value is None and fv.field_type.ftype == "sample":
                    reasons.append("{} has no sample defined".format(fv_info(fv)))
                else:
                    if fv.item:
                        item = fv.item
                        collection = item.as_collection()
                        if collection:
                            item = collection.part(fv.row, fv.column)
                        if item.sample_id != fv.sample.id:
                            reasons.append(
                                "{} has sample_id={} but generated item has sample_id={}".format(
                                    fv_info(fv), fv.sample.id, item.sample_id
                                )
                            )
                    values.append(value)
                if len(list(subgraph.predecessors(n))) == 0:
                    root = fv
            if (
                root.item is None
                and root.role == "input"
                and root.field_type.ftype == "sample"
            ):
                reasons.append("{} has no item defined".format(fv_info(fv)))
            values = list(set(values))
            if len(values) > 1:
                reasons.append("different samples defined in route ({})".format(values))
            root_id = "{} for {} ({})".format(
                root.name, root.operation.operation_type.name, self._routing_id(root)
            )
            routes[root_id] = {
                "root_field_value": root,
                "errors": reasons,
                "valid": len(reasons) == 0,
            }
        errors = {k: v for k, v in routes.items() if v["valid"] != True}
        return errors
        # return routes

    # TODO: implement planner.copy and anonymize the operations and field_values by removing their ids
    def copy(self):
        """Return a copy of this planner, with a new anonymous copy of the plan. Browser cache is copied as well,
        but model_cache in browser are not anonymous"""
        # copy everything execpt plan, which may be large
        copied = empty_copy(self)
        data = self.__dict__.copy()
        data.pop("_plan")
        copied.__dict__ = deepcopy(data)

        # copy over anonymous copy
        copied._plan = self.plan.copy()
        return copied

    def __copy__(self):
        return self.copy()

    @staticmethod
    def combine(plans):
        """
        Merges a list of plans into a single plan by combining operations and wires.

        :param plans: list of Aquarium Plans instances
        :return: new Plan
        """
        copied_plans = [c.copy() for c in plans]

        sessions = set([p.session for p in plans])
        if len(sessions) > 1:
            raise PlannerException(
                "Cannot combine plans, plans must all derive from same session instance"
            )
        session = sessions.pop()

        new_plan = Planner(session)
        new_plan.plan.operations = []
        for p in copied_plans:
            new_plan.plan.operations += p.plan.operations
            new_plan.plan.wires += p.plan.wires
        return new_plan

    def split(self):
        """Split the plan into several distinct plans, if possible. This first convert the plan
         to an operation graph, find subgraphs that are not connected to each other,
         and create new plans based on these subgraphs. This will return anonymous copies of all
        the plans, meaning operations and field_values will be anonymized. Sample and items attached to
        field values will remain to avoid re-creating samples and items."""

        # copy this plan
        copied_plan = self.copy()

        # get independent operation graphs
        layouts = copied_plan.layout.get_independent_layouts()

        # for each independent graph, make a new plan
        new_plans = []
        for layout in layouts:
            new_plan = Planner(self.session)
            new_plans.append(new_plan)

            # copy over the operations
            opids = list(layout.G.nodes)
            ops = [layout.G.nodes[opid]["operation"] for opid in opids]
            wires = []

            # copy over relevant wires
            for wire in copied_plan.plan.wires:
                to_id = wire.destination.operation._primary_key
                from_id = getattr(wire, "source").operation._primary_key
                if to_id in opids or from_id in opids:
                    wires.append(wire)

            new_plan.plan.operations = ops
            new_plan.plan.wires = wires
        return new_plans

    def __add__(self, other):
        return self.combine([self, other])

    def __mul__(self, num):
        return self.combine([self] * num)

    def prettify(self):
        if self.plan.operations:
            self.layout.topo_sort()

    # TODO: implement individual wires and things
    def draw(self):
        layout = self.layout
        edge_colors = []
        for s, e, d in layout.G.edges(data=True):
            color = "black"
            wire = d["wire"]
            if wire.source.sample is None:
                color = "orange"
            elif wire.destination.sample is None:
                color = "orange"
            elif wire.destination.sample != wire.source.sample:
                color = "red"
            edge_colors.append(color)
        nx.draw(self.layout.G, edge_colors=edge_colors, pos=self.layout.pos())
