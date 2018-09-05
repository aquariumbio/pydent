import networkx as nx


# def get_networkx_predecessors(self, op_id):
#     return self.networkx.predecessors(self._id_getter(op_id))
#
# def get_networkx_successors(self, op_id):
#     return self.networkx.successors(self._id_getter(op_id))


class CanvasLayout(object):

    def __init__(self, G=None):
        if G is None:
            G = nx.DiGraph()
        self.G = G

    @classmethod
    def from_plan(cls, plan):
        """Creates a layout from a :class:`pydent.models.Plan` instance"""
        layout = cls(nx.DiGraph())
        edges = []

        for wire in plan.wires:
            from_id = layout._id_getter(wire.source.operation)
            to_id = layout._id_getter(wire.destination.operation)
            if from_id is not None and to_id is not None:
                edges.append((from_id, to_id))
        for op in plan.operations:
            layout._add_operation(op)
        layout.G.add_edges_from(edges)
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

    def ops_to_subgraph(self, ops):
        """Returns a sub-layout containing only the operations"""
        return self.subgraph(self.ops_to_nodes(ops))

    def get_independent_subgraphs(self):
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

    def topo_sort(self):
        """
        Topologically sorts Operations in the layout. Discovers individual subgraphs and topologically sorts
        each subgraph. Finally, aligns subgraphs horizonatally.

        :return: None
        :rtype: None
        """
        subgraphs = self.get_independent_subgraphs()
        x, y = 100, 100
        for subgraph in subgraphs:
            self.topo_sort_helper(subgraph.G)
            self.align_upper_left_to(x, y)
            x += subgraph.midpoint()[0]

    def topo_sort_helper(self, G):
        """Attempt a rudimentary topological sort on the plan"""
        from collections import OrderedDict

        _x = 100
        _y = 100

        y = _y
        delta_x = 170
        delta_y = -70

        sorted = list(nx.topological_sort(G))[::-1]

        res = nx.single_source_shortest_path_length(G, sorted[-1])
        by_depth = OrderedDict()
        for k, v in res.items():
            by_depth.setdefault(v, [])
            by_depth[v].append(k)
        for depth, op_ids in list(by_depth.items()):
            ops = [G.node[op_id]['operation'] for op_id in op_ids]
            x = _x
            for op in ops:
                op.x = x
                op.y = y
                x += delta_x
            self.align_ops_with_predecessors(ops)
            y += delta_y

        # readjust
        min_x = 0
        min_y = 0
        ops = [G.node[n]['operation'] for n in G.nodes]
        for op in ops:
            if op.x < min_x:
                min_x = op.x
            if op.y < min_y:
                min_y = op.y
        self.align_upper_left_to(_x, _y)

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

    def align_x_with_other(self, other_layout):
        """
        Align this layout'x midpoint x-coordinate with the midpoint x-coordinate of another layout

        :param other_layout: the other canvas layout
        :type other_layout: CanvasLayout
        :return: None
        :rtype: None
        """
        if len(other_layout.G) == 0:
            return
        otherx, othery = other_layout.midpoint()
        x, y = self.midpoint()
        return self.translate(otherx - x, 0)

    def align_y_with_other(self, other_layout):
        """
        Align this layout'x midpoint y-coordinate with the midpoint y-coordinate of another layout

        :param other_layout: the other canvas layout
        :type other_layout: CanvasLayout
        :return: None
        :rtype: None
        """
        if len(other_layout.G) == 0:
            return
        otherx, othery = other_layout.midpoint()
        x, y = self.midpoint()
        return self.translate(0, othery - y)

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
        layout1 = self.ops_to_subgraph(ops1)
        layout2 = self.ops_to_subgraph(ops2)
        return layout1.align_x_with_other(layout2)

    def align_upper_left_to(self, x, y):
        """
        Aligns the upper left corner of the layout to the x,y coordinate

        :param x: x-coor
        :type x: int
        :param y: y-coor
        :type y: int
        :return: None
        :rtype: None
        """
        xb, yb = self.bounds()[0]
        return self.translate(x - xb, y - yb)

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

    def __len__(self):
        return len(self.G)
