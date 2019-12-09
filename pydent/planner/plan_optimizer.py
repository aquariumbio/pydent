import json
from collections import OrderedDict
from hashlib import sha1
from typing import List
from uuid import uuid4

import networkx as nx

from .graph import PlannerGraph
from pydent.exceptions import PlannerVerificationException
from pydent.models import Operation
from pydent.models import Plan
from pydent.utils import Loggable
from pydent.utils import logger

# TODO: make this independent of planner
# TODO: move get_op and related methods to Plan model


class PlanOptimizer:
    """Class that optimizes a plan."""

    def __init__(self, planner, inherit_logger: Loggable = None):
        self.planner = planner
        self.graph = self.planner.graph
        if inherit_logger:
            self.logger = inherit_logger(self)
        else:
            self.logger = logger(self)

    # TODO: there could be a setting here to merge things with .sample=None
    @staticmethod
    def _fv_to_hash(fv, ft):
        # none valued Samples are never equivalent
        fvhash = OrderedDict(
            {
                "ftype": fv.field_type.ftype,
                "role": fv.role,
                "name": fv.name,
                "array": ft.array,
                "sample": OrderedDict(),
                "item": OrderedDict(),
                "value": None,
            }
        )
        if fv.sample is not None:
            sample_id = fv.child_sample_id or fv.sample.id
            fvhash["sample"]["id"] = sample_id
        elif fv.field_type.ftype != "sample":
            fvhash["value"] = fv.value
        elif fv.allowable_field_type.sample_type_id is None:
            pass
        else:
            # a deterministic hash for field values missing samples
            fvid = fv.id or fv._primary_key
            ftid = ft.id
            hashed = sha1("{}{}".format(fvid, ftid).encode("utf-8"))
            sid = hashed.hexdigest()
            fvhash["sample"] = sid

        if fv.item is not None:
            fvhash["item"]["id"] = fv.item.id
            if ft.part:
                fvhash["item"]["row"] = fv.row
                fvhash["item"]["column"] = fv.column

        return json.dumps(fvhash, indent=2)

    @classmethod
    def _fv_array_to_hash(cls, fv_array, ft, sort=True, sep="*"):
        arr = [cls._fv_to_hash(fv, ft) for fv in fv_array]
        if sort:
            arr.sort()
        return sep.join(arr)

    @classmethod
    def _op_to_hash(cls, op):
        """Turns a operation into a hash using the operation_type_id, item_id,
        and sample_id."""
        ot_id = op.operation_type.id

        field_value_hashes = []
        for ft in op.operation_type.field_types:
            if ft.ftype == "sample":
                if not ft.array:
                    fv = op.field_value(ft.name, ft.role)
                    field_value_hashes.append(cls._fv_to_hash(fv, ft))
                else:
                    fv_array = op.field_value_array(ft.name, ft.role)
                    field_value_hashes.append(cls._fv_array_to_hash(fv_array, ft))

        field_value_hashes = sorted(field_value_hashes)
        return "{}_{}\n{}".format(
            ot_id, op.operation_type.name, "\n".join(field_value_hashes)
        )

    @classmethod
    def _group_ops_by_hashes(cls, ops):
        hashgroup = {}
        for op in ops:
            h = cls._op_to_hash(op)
            hashgroup.setdefault(h, [])
            hashgroup[h].append(op)
        return hashgroup

    def optimize(self, operations: List[Operation] = None, ignore: List[str] = None):
        """Remove redundant operations.

        :param operations: list of operations
        :param ignore: list of operation type names to ignore in optimization
        :return:
        """
        self.logger.info("Optimizing plan...")
        if operations is not None:
            self.logger.info(
                "   only_operations={}".format([op.id for op in operations])
            )
        self.logger.info("   ignore_types={}".format(ignore))

        # only consider operations in the 'planning state'
        if operations is None:
            operations = [
                op for op in self.planner.operations if op.status == "planning"
            ]

        # ignore operation types
        if ignore:
            operations = [
                op for op in operations if op.operation_type.name not in ignore
            ]

        operations = [op for op in operations if op.status == "planning"]
        nxgraph = self.graph.ops_to_subgraph(operations).nxgraph
        op_to_group_id = OrderedDict()
        group_id_to_ops = OrderedDict()

        def opkey(op):
            return op.id or op._primary_key

        group_graph = nx.DiGraph()

        for n in nx.topological_sort(nxgraph):
            op = nxgraph.nodes[n]["operation"]
            op_hash = self._op_to_hash(op)
            sorted_fvs = sorted(
                op.inputs, key=lambda fv: self._fv_to_hash(fv, fv.field_type)
            )
            sorted_in_wires = []
            for fv_input in sorted_fvs:
                sorted_in_wires += self.planner.get_incoming_wires(fv_input)
            sorted_src_ops = [w.source.operation for w in sorted_in_wires]
            predecessor_groups = [op_to_group_id[opkey(_op)] for _op in sorted_src_ops]
            predecessor_hash = "*".join(predecessor_groups)

            final_hash = op_hash + "__" + predecessor_hash
            op_to_group_id[opkey(op)] = final_hash
            group_id_to_ops.setdefault(final_hash, list())
            group_id_to_ops[final_hash].append(op)

            if final_hash not in group_graph:
                group_graph.add_node(final_hash, operations=[])
            group_graph.nodes[final_hash]["operations"].append(op)
            for n2 in predecessor_groups:
                group_graph.add_edge(final_hash, n2)

        wires_to_remove = []
        wires_to_add = set()
        ops_to_remove = []

        wires_to_add_to_array = {}

        groups = {}
        for n1 in group_graph.nodes:
            groups[n1] = group_graph.nodes[n1]["operations"]

        for n1 in group_graph.nodes:
            source_ops = group_graph.nodes[n1]["operations"]

            if len(source_ops) > 1:
                for ft in source_ops[0].operation_type.field_types:
                    if ft.role == "output":
                        source_wires = []
                        for src_op in source_ops:
                            source_wires += self.planner.get_outgoing_wires(
                                src_op.output(ft.name)
                            )
                        source_wires = set(source_wires)
                        for w in source_wires:
                            key = opkey(w.destination.operation)
                            src_fv = source_ops[0].output(w.source.name)
                            dest_group_id = op_to_group_id[key]
                            dest_op = group_id_to_ops[dest_group_id][0]
                            dest_ft = dest_op.operation_type.field_type(
                                name=w.destination.name, role="input"
                            )

                            if dest_ft.array:
                                array_key = (
                                    dest_group_id,
                                    self._fv_to_hash(w.destination, dest_ft),
                                )
                                wires_to_add_to_array.setdefault(
                                    array_key, (src_fv, dest_op, list())
                                )
                                wires_to_add_to_array[array_key][-1].append(dest_ft)
                            else:
                                dest_fv = dest_op.input(w.destination.name)
                                wires_to_add.add((src_fv, dest_fv))

        for dest_ops in group_id_to_ops.values():
            ops_to_remove += dest_ops[1:]
            for op in dest_ops[1:]:
                for fv in op.field_values:
                    if fv.role == "input":
                        wires_to_remove += self.planner.get_incoming_wires(fv)
                    if fv.role == "output":
                        wires_to_remove += self.planner.get_outgoing_wires(fv)

        for w in wires_to_remove:
            self.planner.remove_wire(w.source, w.destination)

        operations_list = self.planner.operations
        for op in ops_to_remove:
            if op in operations_list:
                operations_list.remove(op)

        for w in wires_to_add:
            self.planner.add_wire(*w)

        for (
            (gid, key),
            (fv_src, target_op, target_fts),
        ) in wires_to_add_to_array.items():
            key_to_inputs = {
                self._fv_to_hash(_fv, _fv.field_type): _fv for _fv in target_op.inputs
            }
            if key_to_inputs.get(key, None):
                self.planner.quick_wire(fv_src, key_to_inputs[key])
            else:
                self.planner.quick_wire(fv_src, (target_op, target_fts[0].name))

        self.planner.operations = operations_list
        self.logger.info("\t{} operations removed".format(len(ops_to_remove)))
        self.logger.info("\t{} wires re-wired".format(len(wires_to_remove)))
        self.logger.info("\t{} new wires".format(len(wires_to_add)))
