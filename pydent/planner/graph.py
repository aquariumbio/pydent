"""PlannerLayout."""
from collections import OrderedDict
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

import networkx as nx

from pydent.models import Operation
from pydent.models import Plan
from pydent.planner.utils import _id_getter
from pydent.planner.utils import get_subgraphs
from pydent.utils import make_async

# custom types
NodeType = Union[str, int]
PlannerGraphType = "PlannerGraph"
PointValue = float
PointType = Tuple[PointValue, PointValue]


class PlannerGraph:
    """Representation of an Aquarium plan as a directed graph.

    Positions :class:`Operations <pydent.models.Operation>` for the
    Aquarium GUI
    """

    def __init__(self, nxgraph: nx.DiGraph = None):
        """Initializes a Plan graph.

        :param nxgraph:
        """
        if nxgraph is None:
            nxgraph = nx.DiGraph()
        self.nxgraph = nxgraph
        self.annotations = []

    @classmethod
    def from_plan(cls, plan: Plan) -> PlannerGraphType:
        """Creates a graph from a :class:`pydent.models.Plan` instance."""
        G = nx.DiGraph()
        planner_graph = cls(G)

        # store reference of operation
        fv_to_op_dict = {}
        if not plan.operations:
            return planner_graph
        for op in plan.operations:
            for fv in op.field_values:
                fv_to_op_dict[fv.rid] = op

        @make_async(10, progress_bar=False)
        def add_wires(wires):
            if not wires:
                return
            missing_operations = []
            for wire in wires:
                # TODO:
                try:
                    from_id = _id_getter(fv_to_op_dict[wire.source.rid])
                    to_id = _id_getter(fv_to_op_dict[wire.destination.rid])
                except KeyError as e:
                    pass
                    raise e
                if from_id is not None and to_id is not None:
                    if from_id not in G:
                        missing_operations.append(from_id)
                    if to_id not in G:
                        missing_operations.append(to_id)
                    if from_id in G and to_id in G:
                        G.add_edge(from_id, to_id, wire=wire)
            return wires

        @make_async(10, progress_bar=False)
        def add_ops(ops: Iterable[Operation]):
            if not ops:
                return
            for op in ops:
                planner_graph._add_operation(op)
            return ops

        add_ops(plan.operations)
        add_wires(plan.wires)

        # fix operation coordinates if None
        for op in planner_graph.operations:
            if op.x is None:
                op.x = 0
            if op.y is None:
                op.y = 0

        return planner_graph

    @property
    def nodes(self):
        return self.nxgraph.nodes

    @property
    def operations(self) -> Generator[Operation, None, None]:
        for node in self.nxgraph.nodes:
            if "operation" in self.nxgraph.nodes[node]:
                yield self.nxgraph.nodes[node]["operation"]

    def iter_operations(
        self,
    ) -> Generator[Tuple[Union[str, int], Operation], None, None]:
        for node in self.nxgraph.nodes:
            if "operation" in self.nxgraph.nodes[node]:
                yield (node, self.nxgraph.nodes[node]["operation"])

    def _add_operation(self, op: Operation):
        """Adds an Operation to the Layout.

        :param op: operation
        :type op: pydent.models.Operation
        :return: None
        :rtype: None
        """
        return self.nxgraph.add_node(_id_getter(op), operation=op)

    def subgraph(self, nodes: List[NodeType]) -> Optional[Type["PlannerGraph"]]:
        """Returns a subgraph layout from a list of node_ids."""
        return self.__class__(nxgraph=self.nxgraph.subgraph(nodes))

    def nodes_to_ops(self, nodes: List[NodeType]):
        """Returns operations from a list of node_ids."""
        return [self.nxgraph.nodes[n]["operation"] for n in nodes]

    def ops_to_nodes(self, ops: List[Operation]):
        """Returns node_ids for each operation."""
        return [_id_getter(op) for op in ops]

    def ops_to_subgraph(self, ops: List[Operation]) -> PlannerGraphType:
        """Returns a sub-layout containing only the operations."""
        return self.subgraph(self.ops_to_nodes(ops))

    def predecessors(self, node: NodeType):
        """Return predecessor nodes.

        :param node: node id
        :type node: basestring
        :return: list of node ids
        :rtype: list
        """
        return self.nxgraph.predecessors(node)

    def successors(self, node: NodeType) -> Generator[NodeType, None, None]:
        """Return successors nodes.

        :param node: node id
        :type node: basestring
        :return: list of node ids
        :rtype: list
        """
        return self.nxgraph.successors(node)

    def predecessor_subgraph(self, subgraph: PlannerGraphType) -> PlannerGraphType:
        n_bunch = self.collect_predecessors(subgraph.roots())
        return self.subgraph(n_bunch)

    def successor_subgraph(self, layout):
        n_bunch = self.collect_successors(layout.leaves())
        return self.subgraph(n_bunch)

    def collect_predecessors(self, nodes: List[NodeType]) -> List[NodeType]:
        """Return all predecessors from a list of nodes.

        :param nodes: list of node ids
        :type nodes: list
        :return: list of node ids
        :rtype: list
        """
        predecessors = []
        for node in nodes:
            predecessors += self.predecessors(node)
        return list(set(predecessors))

    def collect_successors(self, nodes: List[NodeType]) -> List[NodeType]:
        """Return all successors from a list of nodes.

        :param nodes: list of node ids
        :type nodes: list
        :return: list of node ids
        :rtype: list
        """
        successors = []
        for node in nodes:
            successors += self.successors(node)
        return list(set(successors))

    def ops_to_predecessors(self, ops: List[Operation]) -> List[Operation]:
        """Return all predecessor operations from a list of operations.

        :param ops: list of :class:`pydent.models.Operation`
        :type ops: list
        :return: list of node ids
        :rtype: list
        """
        nodes = self.collect_predecessors(self.ops_to_nodes(ops))
        return self.nodes_to_ops(nodes)

    def ops_to_successors(self, ops: List[Operation]) -> List[Operation]:
        """Return all successor operations from a list of operations.

        :param ops: list of :class:`pydent.models.Operation`
        :type ops: list
        :return: list of node ids
        :rtype: list
        """
        nodes = self.collect_successors(self.ops_to_nodes(ops))
        return self.nodes_to_ops(nodes)

    def leaves(self):
        """Returns the leaves of this graph."""
        leaves = []
        for n in self.nodes:
            if len(list(self.successors(n))) == 0:
                leaves.append(n)
        return leaves

    def roots(self):
        """Returns the roots of this graph."""
        roots = []
        for n in self.nodes:
            if len(list(self.predecessors(n))) == 0:
                roots.append(n)
        return roots

    def ops_to_leaves(self):
        return self.nodes_to_ops(self.leaves())

    def ops_to_roots(self):
        return self.nodes_to_ops(self.roots())

    def __len__(self):
        return len(self.nxgraph)


class PlannerLayout(PlannerGraph):
    """Layout module for :class:`Planner <pydent.planner.Planner>`.

    Positions :class:`Operations <pydent.models.Operation>` for the
    Aquarium GUI
    """

    TOP_RIGHT = (100, 100)
    BOX_DELTA_X = 170
    BOX_DELTA_Y = 70
    BOX_WIDTH = 150
    BOX_HEIGHT = 70
    STATUS_COLORS = {
        "waiting": "orange",
        "error": "red",
        "pending": "yellow",
        "running": "green",
        "delayed": "magenta",
        "done": "black",
        "planning": "grey",
    }

    def get_independent_graphs(self):
        """Finds all independent subgraphs.

        :return: list of PlannerLayout
        :rtype: list
        """
        subgraphs = get_subgraphs(self.nxgraph)
        sublayouts = [self.__class__(nxgraph=g) for g in subgraphs]
        return sublayouts

    def _topological_sort(self):
        subgraphs = self.get_independent_graphs()
        for subgraph in subgraphs:
            subgraph._topological_sort_helper()
        self.arrange_layouts(subgraphs)

    def topo_sort_in_place(self):
        cx, cy = self.midpoint()
        self._topological_sort()
        cx2, cy2 = self.midpoint()
        self.translate(cx - cx2, cy - cy2)

    def topo_sort(self):
        """Does a topological sort of the operations in this layout.

        Discovers individual subgraphs and topologically sorts each subgraph,
        and then aligns subgraphs horizontally.

        :return: None
        :rtype: None
        """
        self._topological_sort()
        self.move(*self.TOP_RIGHT)

    def prettify(self):
        return self.topo_sort()

    @classmethod
    def arrange_layouts(cls, layouts):
        x = 0
        y = 0
        for layout in layouts:
            layout.move(x, y)
            x += layout.width + cls.BOX_DELTA_X
            y = layout.y

    def to_grid(
        self, columns: int, axis: int = 1, border_x: int = None, border_y: int = None
    ):
        """Arrange layouts in a grid format.

        :param columns: maximum number of columns (or rows when axis=0)
        :type columns: int
        :param axis: which axis to limit. Default: 1 (columns) or 0 (rows)
        :type axis: int
        :param border_x: (optional) separation between each cell in the grid
        :type border_x: int
        :param border_y: (optional) separation between each cell in the grid
        :type border_y: int
        :return: layout
        :rtype: layout
        """
        layouts = self.get_independent_graphs()
        if len(layouts) == 1:
            self.move(100, 100)
            return self

        # make grid assignments
        assignments = []
        c = 0
        r = 0
        for layout in layouts:
            assignments.append((r, c, layout))
            c += 1
            if c >= columns:
                r += 1
                c = 0

        # find cell height and width
        if border_x is None:
            border_x = self.BOX_DELTA_X * 2
        if border_y is None:
            border_y = self.BOX_DELTA_Y * 2
        grid_cell_height = 0
        grid_cell_width = 0
        for layout in layouts:
            if layout.height > grid_cell_height:
                grid_cell_height = layout.height
            if layout.width > grid_cell_width:
                grid_cell_width = layout.width
        grid_cell_height += border_y
        grid_cell_width += border_x

        for r, c, layout in assignments:
            if axis == 0:
                r, c = c, r
            layout.center(c * grid_cell_width, r * grid_cell_height)
        self.move(100, 100)
        return self

    def align_x_midpoints_to(self, other_layout):
        """Align the midpoint x-coordinate of this layout with that of another.

        :param other_layout: the other canvas layout
        :type other_layout: PlannerLayout
        :return: None
        :rtype: None
        """
        if len(other_layout.nxgraph) == 0:
            return
        other_x, _ = other_layout.midpoint()
        x, _ = self.midpoint()
        deltax = other_x - x
        self.translate(deltax, 0)

    def align_y_midpoints_to(self, other_layout):
        """Align this midpoint y-coordinates of this layout with another
        layout.

        :param other_layout: the other canvas layout
        :type other_layout: PlannerLayout
        :return: None
        :rtype: None
        """
        if len(other_layout.nxgraph) == 0:
            return
        _, other_y = other_layout.midpoint()
        self.y = other_y

    def align_x_of_ops(self, ops1: List[Operation], ops2: List[Operation]):
        """Aligns a set of Operations with another set of Operations within
        this PlannerLayout.

        :param ops1: list of :class:`pydent.models.Operation`
        :type ops1: list
        :param ops2: list of :class:`pydent.models.Operation`
        :type ops2: list
        :return: None
        :rtype: None
        """
        layout1 = self.ops_to_subgraph(ops1)
        layout2 = self.ops_to_subgraph(ops2)
        return layout1.align_x_midpoints_to(layout2)

    @property
    def xy(self) -> PointType:
        return self.bounds()[0]

    @property
    def x(self) -> PointValue:
        return self.xy[0]

    @property
    def y(self) -> PointValue:
        return self.xy[1]

    @x.setter
    def x(self, new_x: PointValue):
        deltax = new_x - self.x
        self.translate(deltax, 0)

    @y.setter
    def y(self, new_y: PointValue):
        delta_y = new_y - self.y
        self.translate(0, delta_y)

    def bounds(self) -> Tuple[PointType, PointType]:
        """Returns the bounding box of the layout as the upper-left and lower-
        right coordinates.

        :return: x,y coordinate
        :rtype: tuple
        """
        x_arr = [op.x for op in self.operations]
        y_arr = [op.y for op in self.operations]
        return (min(x_arr), min(y_arr)), (max(x_arr), max(y_arr))

    def midpoint(self) -> PointType:
        """Returns the midpoint x,y coordinates of the layout.

        :return: x,y coordinate
        :rtype: tuple
        """
        ul, lr = self.bounds()
        x, y = (lr[0] - ul[0]) / 2 + ul[0], (lr[1] - ul[1]) / 2 + ul[1]
        return x, y

    def translate(
        self, delta_x: PointValue, delta_y: PointValue
    ) -> Generator[Operation, None, None]:
        """Translates the layout by the x,y coordinates.

        :param delta_x: delta x
        :type delta_x: int
        :param delta_y: delta y
        :type delta_y: int
        :return: None
        :rtype: None
        """
        for op in self.operations:
            op.x += delta_x
            op.y += delta_y
        return self.operations

    def move(self, x: PointValue, y: PointValue):
        self.x = x
        self.y = y

    def center(self, x: PointValue, y: PointValue):
        self.move(x - self.width / 2, y - self.height / 2)

    @property
    def width(self):
        return self.bounds()[1][0] - self.bounds()[0][0]

    @property
    def height(self) -> PointValue:
        return self.bounds()[1][1] - self.bounds()[0][1]

    def pos(self) -> Dict[NodeType, PointType]:
        pos = {}
        for n, op in self.iter_operations():
            pos[n] = (op.x, -op.y)
        return pos

    def _status_colors(self) -> List[str]:
        node_color = [
            self.STATUS_COLORS.get(op.status, "rosybrown") for op in self.operations
        ]
        return node_color

    # TODO: minimize crossings
    def _topological_sort_helper(self):
        """Attempt a rudimentary topological sort on the plan."""

        _x, _y = self.TOP_RIGHT

        y = _y
        delta_x = self.BOX_DELTA_X
        delta_y = -self.BOX_DELTA_Y

        max_depth = {}
        roots = self.roots()
        for root in roots:
            depths = nx.single_source_shortest_path_length(self.nxgraph, root)
            for n, d in depths.items():
                max_depth[n] = max(max_depth.get(n, d), d)

        # push roots 'up' so they are not stuck on layer one
        for root in roots:
            successors = list(self.successors(root))
            if len(successors) > 0:
                min_depth = min([max_depth[s] for s in successors])
                max_depth[root] = min_depth - 1

        by_depth = OrderedDict()

        for node, depth in max_depth.items():
            by_depth.setdefault(depth, [])
            by_depth[depth].append(node)
        for depth in sorted(by_depth):
            op_ids = by_depth[depth]

            # sort by predecessor_layout
            predecessor_avg_x = []
            x = 0
            for op_id in op_ids:
                predecessors = list(self.predecessors(op_id))
                if len(predecessors) > 0:
                    x, _ = self.subgraph(predecessors).midpoint()
                    predecessor_avg_x.append((x, op_id))
                else:
                    predecessor_avg_x.append((x + 1, op_id))
            sorted_op_ids = [
                op_id for _, op_id in sorted(predecessor_avg_x, key=lambda x: x[0])
            ]

            x = _x
            # sorted_op_ids = sorted(op_ids)
            ops = self.nodes_to_ops(sorted_op_ids)
            for op in ops:
                op.x = x
                op.y = y
                x += delta_x
            layer = self.subgraph(op_ids)
            predecessor_layout = self.predecessor_subgraph(layer)
            layer.align_x_midpoints_to(predecessor_layout)
            y += delta_y

        # readjust
        self.move(_x, _y)

    def align_ops_with_successors(self, ops: List[Operation]):
        """Aligns the Operations to their successors by midpoints.

        Used in topological sorting of plans.

        :param ops: list of :class:`pydent.models.Operation`
        :type ops: list
        :return: None
        :rtype: None
        """
        successors = self.ops_to_successors(ops)
        self.align_x_of_ops(ops, successors)

    def align_ops_with_predecessors(self, ops: List[Operation]):
        """Aligns the Operations to their predecessors by midpoints.

        Used in topological sorting of plans.

        :param ops: list of :class:`pydent.models.Operation`
        :type ops: list
        :return: None
        :rtype: None
        """
        predecessors = self.ops_to_predecessors(ops)
        self.align_x_of_ops(ops, predecessors)

    def draw(self):
        return nx.draw(self.nxgraph, pos=self.pos(), node_color=self._status_colors())
