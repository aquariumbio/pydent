from copy import deepcopy

import networkx as nx

# where is this method called?
def arr_to_pairs(arr):
    arr1 = arr[:-1]
    arr2 = arr[1:]
    return list(zip(arr1, arr2))


def _id_getter(model):
    return model._primary_key


def to_undirected(graph):
    """.to_undirected is implemented in networkx out of the box, however, it
    suffers from occasional infinite recursion errors during the deepcopy phase
    (unknown as to why)."""
    undirected = nx.Graph()
    copied = deepcopy(graph)
    for n in copied.nodes:
        ndata = copied.nodes[n]
        undirected.add_node(n, **ndata)
    for n1, n2 in copied.edges:
        edata = copied.edges[n1, n2]
        undirected.add_edge(n1, n2, **edata)
    return undirected


def bfs_tree_subgraph(graph, source):
    """Similar to nx.bfs_tree, but nx.bfs_tree does not maintain edge list."""
    nodes = list(nx.dfs_predecessors(graph, source)) + [source]
    return graph.subgraph(nodes)


def get_subgraphs(graph):
    """Get independent subgraphs."""
    node_list = list(graph.nodes)
    subgraphs = []
    while len(node_list) > 0:
        node = node_list[-1]
        subgraph = nx.bfs_tree(to_undirected(graph), node)
        for n in subgraph.nodes:
            node_list.remove(n)
        subgraphs.append(graph.subgraph(subgraph.nodes))
    return subgraphs
