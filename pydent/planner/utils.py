import networkx as nx


def arr_to_pairs(arr):
    arr1 = arr[:-1]
    arr2 = arr[1:]
    return list(zip(arr1, arr2))


def _id_getter(model):
    id = model.id
    if id is None:
        id = "r{}".format(model.rid)
    return id


def get_subgraphs(graph):
    """Get independent subgraphs"""
    node_list = list(graph.nodes)
    subgraphs = []
    while len(node_list) > 0:
        node = node_list[-1]
        subgraph = nx.bfs_tree(graph.to_undirected(), node)
        for n in subgraph.nodes:
            node_list.remove(n)
        subgraphs.append(graph.subgraph(subgraph.nodes))
    return subgraphs