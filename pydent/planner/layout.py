"""
PlannerLayout
"""

import networkx as nx
from collections import OrderedDict
from pydent.utils import make_async


class PlannerLayout(object):

    TOP_RIGHT = (100, 100)
    BOX_DELTAX = 170
    BOX_DELTAY = 70
    BOX_WIDTH = 100
    BOX_HEIGHT = 70
    STATUS_COLORS = {
        "waiting": "orange",
        "error": "red",
        "pending": "yellow",
        "running": "green",
        "delayed": "magenta",
        "done": "black",
        "planning": "grey"
    }

    def __init__(self, G=None):
        if G is None:
            G = nx.DiGraph()
        self.G = G
        self.annotations = []

    @classmethod
    def from_plan(cls, plan):
        """Creates a layout from a :class:`pydent.models.Plan` instance"""
        layout = cls(nx.DiGraph())
        edges = []

        @make_async(10, progress_bar=False)
        def add_wires(wires):
            for wire in wires:
                from_id = layout._id_getter(wire.source.operation)
                to_id = layout._id_getter(wire.destination.operation)
                if from_id is not None and to_id is not None:
                    edges.append((from_id, to_id))
            return wires

        @make_async(10, progress_bar=False)
        def add_ops(ops):
            for op in ops:
                layout._add_operation(op)
            return ops

        add_wires(plan.wires)
        add_ops(plan.operations)
        layout.G.add_edges_from(edges)

        # fix operation coordinates if None
        for op in layout.operations:
            if op.x is None:
                op.x = 0
            if op.y is None:
                op.y = 0

        return layout

    @staticmethod
    def _id_getter(model):
        id = model.id
        if id is None:
            id = "r{}".format(model.rid)
        return id

    @property
    def nodes(self):
        return self.G.nodes

    @property
    def operations(self):
        for node in self.G.nodes:
            yield self.G.node[node]['operation']

    def _add_operation(self, op):
        """
        Adds an Operation to the Layout

        :param op: operation
        :type op: pydent.models.Operation
        :return: None
        :rtype: None
        """
        return self.G.add_node(self._id_getter(op), operation=op)

    def subgraph(self, nodes):
        """Returns a subgraph layout from a list of node_ids"""
        return self.__class__(G=self.G.subgraph(nodes))

    def nodes_to_ops(self, nodes):
        """Returns operations from a list of node_ids"""
        return [self.G.node[n]['operation'] for n in nodes]

    def ops_to_nodes(self, ops):
        """Returns node_ids for each operation"""
        return [self._id_getter(op) for op in ops]

    def ops_to_layout(self, ops):
        """Returns a sub-layout containing only the operations"""
        return self.subgraph(self.ops_to_nodes(ops))

    def get_independent_layouts(self):
        """
        Finds all independent subgraphs.

        :return: list of CanvasLayout
        :rtype: list
        """
        node_list = list(self.G.nodes)
        subgraphs = []
        while len(node_list) > 0:
            node = node_list[-1]
            subgraph = nx.bfs_tree(self.G.to_undirected(), node)
            for n in subgraph.nodes:
                node_list.remove(n)
            nxsubgraph = self.G.subgraph(subgraph.nodes)
            sublayout = self.__class__(G=nxsubgraph)
            subgraphs.append(sublayout)
        return subgraphs

    def _topo_sort(self):
        subgraphs = self.get_independent_layouts()
        for subgraph in subgraphs:
            subgraph._topo_sort_helper()
        self.arrange_layouts(subgraphs)

    def topo_sort_in_place(self):
        cx, cy = self.midpoint()
        self._topo_sort()
        cx2, cy2 = self.midpoint()
        self.translate(cx - cx2, cy - cy2)

    def topo_sort(self):
        """
        Topologically sorts Operations in the layout. Discovers individual subgraphs and topologically sorts
        each subgraph. Finally, aligns subgraphs horizonatally.

        :return: None
        :rtype: None
        """
        self._topo_sort()
        self.move(*self.TOP_RIGHT)

    @classmethod
    def arrange_layouts(cls, layouts):
        x = 0
        y = 0
        for layout in layouts:
            layout.move(x, y)
            x += layout.width + cls.BOX_DELTAX
            y = layout.y

    def to_grid(self, columns, axis=1, borderx=None, bordery=None):
        """
        Arrange layouts in a grid format.

        :param columns: maximum number of columns (or rows when axis=0)
        :type columns: int
        :param axis: which axis to limi. Default: 1 (columns) or 0 (rows)
        :type axis: int
        :param borderx: (optional) separation between each cell in the grid
        :type borderx: int
        :param bordery: (optional) separation between each cell in the grid
        :type bordery: int
        :return: layout
        :rtype: layout
        """
        layouts = self.get_independent_layouts()
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
        if borderx is None:
            borderx = self.BOX_DELTAX * 2
        if bordery is None:
            bordery = self.BOX_DELTAY * 2
        grid_cell_height = 0
        grid_cell_width = 0
        for layout in layouts:
            if layout.height > grid_cell_height:
                grid_cell_height = layout.height
            if layout.width > grid_cell_width:
                grid_cell_width = layout.width
        grid_cell_height += bordery
        grid_cell_width += borderx

        for r, c, layout in assignments:
            if axis == 0:
                r, c = c, r
            layout.center(c * grid_cell_width, r * grid_cell_height)
        self.move(100, 100)
        return self

    # TODO: minimize crossings
    def _topo_sort_helper(self):
        """Attempt a rudimentary topological sort on the plan"""

        _x, _y = self.TOP_RIGHT

        y = _y
        delta_x = self.BOX_DELTAX
        delta_y = -self.BOX_DELTAY

        max_depth = {}
        roots = self.roots()
        for root in roots:
            depths = nx.single_source_shortest_path_length(self.G, root)
            for n, d in depths.items():
                max_depth[n] = max(max_depth.get(n, d), d)

        # push roots 'up' so they are not stuck on layer one
        for root in self.roots():
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
            pred_avg_x = []
            x = 0
            for op_id in op_ids:
                preds = list(self.predecessors(op_id))
                if len(preds) > 0:
                    x, _ = self.subgraph(preds).midpoint()
                    pred_avg_x.append((x, op_id))
                else:
                    pred_avg_x.append((x+1, op_id))
            sorted_op_ids = [op_id for _, op_id in sorted(
                pred_avg_x, key=lambda x: x[0])]

            x = _x
            # sorted_op_ids = sorted(op_ids)
            ops = self.nodes_to_ops(sorted_op_ids)
            for op in ops:
                op.x = x
                op.y = y
                x += delta_x
            layer = self.subgraph(op_ids)
            pred_layout = self.predecessor_layout(layer)
            layer.align_x_midpoints(pred_layout)
            y += delta_y

        # readjust
        self.move(_x, _y)

    def align_ops_with_successors(self, ops):
        """
        Aligns the Operations to their successors by midpoints. Used in topological sorting of plans.

        :param ops: list of :class:`pydent.models.Operation`
        :type ops: list
        :return: None
        :rtype: None
        """
        successors = self.ops_to_successors(ops)
        self.align_x_of_ops(ops, successors)

    def align_ops_with_predecessors(self, ops):
        """
        Aligns the Operations to their predecessors by midpoints. Used in topological sorting of plans.

        :param ops: list of :class:`pydent.models.Operation`
        :type ops: list
        :return: None
        :rtype: None
        """
        predecessors = self.ops_to_predecessors(ops)
        self.align_x_of_ops(ops, predecessors)

    def predecessors(self, node):
        """
        Return predecessor nodes

        :param node: node id
        :type node: basestring
        :return: list of node ids
        :rtype: list
        """
        return self.G.predecessors(node)

    def successors(self, node):
        """
        Return successors nodes

        :param node: node id
        :type node: basestring
        :return: list of node ids
        :rtype: list
        """
        return self.G.successors(node)

    def predecessor_layout(self, layout):
        nbunch = self.collect_predecessors(layout.roots())
        return self.subgraph(nbunch)

    def successor_layout(self, layout):
        nbunch = self.collect_successors(layout.leaves())
        return self.subgraph(nbunch)

    def collect_predecessors(self, nodes):
        """
        Return all predecessors from a list of nodes

        :param nodes: list of node ids
        :type nodes: list
        :return: list of node ids
        :rtype: list
        """
        preds = []
        for node in nodes:
            preds += self.predecessors(node)
        return list(set(preds))

    def collect_successors(self, nodes):
        """
        Return all successors from a list of nodes

        :param nodes: list of node ids
        :type nodes: list
        :return: list of node ids
        :rtype: list
        """
        successors = []
        for node in nodes:
            successors += self.successors(node)
        return list(set(successors))

    def ops_to_predecessors(self, ops):
        """
        Return all predecessor operations from a list of operations

        :param nodes: list of :class:`pydent.models.Operation`
        :type nodes: list
        :return: list of node ids
        :rtype: list
        """
        nodes = self.collect_predecessors(self.ops_to_nodes(ops))
        return self.nodes_to_ops(nodes)

    def ops_to_successors(self, ops):
        """
        Return all successor operations from a list of operations

        :param nodes: list of :class:`pydent.models.Operation`
        :type nodes: list
        :return: list of node ids
        :rtype: list
        """
        nodes = self.collect_successors(self.ops_to_nodes(ops))
        return self.nodes_to_ops(nodes)

    def leaves(self):
        """Returns the leaves of this layout"""
        leaves = []
        for n in self.nodes:
            if len(list(self.successors(n))) == 0:
                leaves.append(n)
        return leaves

    def roots(self):
        """Returns the roots of this layout"""
        roots = []
        for n in self.nodes:
            if len(list(self.predecessors(n))) == 0:
                roots.append(n)
        return roots

    def ops_to_leaves(self):
        return self.nodes_to_ops(self.leaves())

    def ops_to_roots(self):
        return self.nodes_to_ops(self.roots())

    def align_x_midpoints(self, other_layout):
        """
        Align this layout'x midpoint x-coordinate with the midpoint x-coordinate of another layout

        :param other_layout: the other canvas layout
        :type other_layout: PlannerLayout
        :return: None
        :rtype: None
        """
        if len(other_layout.G) == 0:
            return
        other_x, _ = other_layout.midpoint()
        x, _ = self.midpoint()
        self.translate(other_x - x, 0)

    def align_y_midpoints(self, other_layout):
        """
        Align this midpoint y-coordinates of this layout with another layout

        :param other_layout: the other canvas layout
        :type other_layout: PlannerLayout
        :return: None
        :rtype: None
        """
        if len(other_layout.G) == 0:
            return
        _, other_y = other_layout.midpoint()
        self.y = other_y

    def align_x_of_ops(self, ops1, ops2):
        """
        Aligns a set of Operations with another set of Operations within the CanvasLayout

        :param ops1: list of :class:`pydent.models.Operation`
        :type ops1: list
        :param ops2: list of :class:`pydent.models.Operation`
        :type ops2: list
        :return: None
        :rtype: None
        """
        layout1 = self.ops_to_layout(ops1)
        layout2 = self.ops_to_layout(ops2)
        return layout1.align_x_midpoints(layout2)

    @property
    def xy(self):
        return self.bounds()[0]

    @property
    def x(self):
        return self.xy[0]

    @property
    def y(self):
        return self.xy[1]

    @x.setter
    def x(self, new_x):
        deltax = new_x - self.x
        self.translate(deltax, 0)

    @y.setter
    def y(self, new_y):
        deltay = new_y - self.y
        self.translate(0, deltay)

    def bounds(self):
        """
        Returns the upper-left and lower-right bounding box coordinates of the layout

        :return: x,y coordinate
        :rtype: tuple
        """
        xarr = [op.x for op in self.operations]
        yarr = [op.y for op in self.operations]
        return ((min(xarr), min(yarr)), (max(xarr), max(yarr)))

    def midpoint(self):
        """
        Returns the midpoint x,y coordinates of the layout

        :return: x,y coordinate
        :rtype: tuple
        """
        ul, lr = self.bounds()
        x, y = (lr[0] - ul[0]) / 2 + ul[0], (lr[1] - ul[1]) / 2 + ul[1]
        return x, y

    def translate(self, deltax, deltay):
        """
        Translates the layout by the x,y coordinates

        :param deltax: delta x
        :type deltax: int
        :param deltay: delta y
        :type deltay: int
        :return: None
        :rtype: None
        """
        for op in self.operations:
            op.x += deltax
            op.y += deltay

    def move(self, x, y):
        self.x = x
        self.y = y

    def center(self, x, y):
        self.move(x - self.width/2, y - self.height/2)

    @property
    def width(self):
        return self.bounds()[1][0] - self.bounds()[0][0]

    @property
    def height(self):
        return self.bounds()[1][1] - self.bounds()[0][1]

    def draw(self):
        pos = {}
        for n in self.nodes:
            op = self.G.node[n]['operation']
            pos[n] = (op.x, -op.y)

        node_color = [self.STATUS_COLORS.get(
            op.status, "rosybrown") for op in self.operations]

        return nx.draw(self.G, pos=pos, node_color=node_color)

    def __len__(self):
        return len(self.G)
