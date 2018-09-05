import networkx as nx
from networkx import DiGraph

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
        self.G.add_node(self._id_getter(op), operation=op)

    def subgraph(self, nodes):
        return self.__class__(G=self.G.subgraph(nodes))

    def nodes_to_ops(self, nodes):
        return [self.G.node[n]['operation'] for n in nodes]

    def ops_to_nodes(self, ops):
        return [self._id_getter(op) for op in ops]

    def ops_to_subgraph(self, ops):
        return self.subgraph(self.ops_to_nodes(ops))

    def get_independent_subgraphs(self):
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
        subgraphs = self.get_independent_subgraphs()
        x, y = 100, 100
        for subgraph in subgraphs:
            self.topo_sort_helper(subgraph.G)
            self.adjust_upper_left(x, y)
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
        self.adjust_upper_left(_x, _y)

    def align_ops_with_predecessors(self, ops):
        successors = self.ops_to_successors(ops)
        self.align_x_of_ops(ops, successors)

    def align_ops_with_predecessors(self, ops):
        predecessors = self.ops_to_predecessors(ops)
        self.align_x_of_ops(ops, predecessors)

    def predecessors(self, node):
        return self.G.predecessors(node)

    def successors(self, node):
        return self.G.successors(node)

    def collect_predecessors(self, nodes):
        preds = []
        for node in nodes:
            preds += self.predecessors(node)
        return list(set(preds))

    def collect_successors(self, nodes):
        successors = []
        for node in nodes:
            successors += self.successors(node)
        return list(set(successors))

    def ops_to_predecessors(self, ops):
        nodes = self.collect_predecessors(self.ops_to_nodes(ops))
        return self.nodes_to_ops(nodes)

    def ops_to_successors(self, ops):
        nodes = self.collect_successors(self.ops_to_nodes(ops))
        return self.nodes_to_ops(nodes)

    def align_x_with_other(self, other_layout):
        if len(other_layout.G) == 0:
            return
        otherx, othery = other_layout.midpoint()
        x, y = self.midpoint()
        return self.translate(otherx - x, 0)

    def align_y_with_other(self, other_layout):
        if len(other_layout.G) == 0:
            return
        otherx, othery = other_layout.midpoint()
        x, y = self.midpoint()
        return self.translate(0, othery - y)

    def align_x_of_ops(self, ops1, ops2):
        layout1 = self.ops_to_subgraph(ops1)
        layout2 = self.ops_to_subgraph(ops2)
        return layout1.align_x_with_other(layout2)

    def adjust_upper_left(self, x, y):
        xb, yb = self.bounds()[0]
        return self.translate(x - xb, y - yb)

    def bounds(self):
        """Returns upper-left and lower-right bounding corners of the plan (assuming no modules...)"""
        xarr = [op.x for op in self.operations]
        yarr = [op.y for op in self.operations]
        return ((min(xarr), min(yarr)), (max(xarr), max(yarr)))

    def midpoint(self):
        ul, lr = self.bounds()
        x, y = (lr[0] - ul[0]) / 2 + ul[0], (lr[1] - ul[1]) / 2 + ul[1]
        return x, y

    def translate(self, deltax, deltay):
        for op in self.operations:
            op.x += deltax
            op.y += deltay