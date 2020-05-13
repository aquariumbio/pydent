from typing import Iterable
from typing import List
from typing import Union

import networkx as nx

from pydent.exceptions import TridentBaseException
from pydent.models import Collection
from pydent.models import Item
from pydent.models import Plan
from pydent.models import Sample
from pydent.sessionabc import SessionABC


VALID_INVENTORY_TYPES = [Sample, Item, Plan, Collection]
InventoryType = Union[Item, Sample, Collection, Plan]


def to_node(model):
    key = model.id or model._primary_key
    return model.__class__.__name__ + "__" + str(key)


def add_node(graph, m):
    graph.add_node(to_node(m), model=m, model_class=m.__class__.__name__)


def add_edge(graph, m1, m2):
    n1 = to_node(m1)
    if n1 not in graph:
        add_node(graph, m1)
    n2 = to_node(m2)
    if n2 not in graph:
        add_node(graph, m2)
    graph.add_edge(n1, n2)


def is_inventory_type(m):
    for valid_type in VALID_INVENTORY_TYPES:
        if isinstance(m, valid_type):
            return True
    return False


def _handle_sample(
    g: nx.DiGraph, m: InventoryType, to_visit: List[InventoryType], visited: List[str]
):
    if m.is_deserialized("field_values"):
        for fv in m.field_values:
            if fv.is_deserialized("sample"):
                add_edge(g, m, fv.sample)
                if to_node(fv.sample) not in visited:
                    to_visit.append(fv.sample)
    elif m.is_deserialized("items"):
        for item in m.items:
            if to_node(item) not in visited:
                to_visit.append(item)


def _handle_collection(g, m, to_visit):
    for pa in m.part_associations:
        if pa.has_unsaved_sample:
            add_edge(g, m, pa.part.sample)
            to_visit.append(pa.part.sample)


def _handle_item(g, m, to_visit):
    if m.is_deserialized("sample"):
        add_edge(g, m, m.sample)
        to_visit.append(m.sample)
    if m.object_type.rows:
        to_visit.append(m.containing_collection)


def _handle_plan(g, m, to_visit):
    for op in m.operations:
        for fv in op.field_values:
            if fv.sample:
                add_edge(g, m, fv.sample)
                to_visit.append(fv.sample)
            if fv.item:
                item = fv.item
                add_edge(g, m, item)
                to_visit.append(item)


def models_to_graph(session: SessionABC, models: Iterable[InventoryType]) -> nx.DiGraph:
    """Convert an iterable of inventory models (Item, Sample, Collection, or
    Plans), into a DAG.

    :param session: AqSession
    :param models: list of models
    :return: nx.DiGraph
    """

    # check inventory types
    for m in models:
        if not is_inventory_type(m):
            raise TridentBaseException(
                "{} is not a valid inventory type.".format(m.__class__.__name__)
            )

    # create graph
    graph = nx.DiGraph()
    with session.with_cache(using_models=True, timeout=60):
        for m in models:
            add_node(graph, m)

        to_visit = models[:]
        visited = []
        while to_visit:
            m = to_visit.pop()
            if to_node(m) in visited:
                continue
            else:
                visited.append(to_node(m))
            cls = m.__class__.__name__
            if isinstance(m, Item):
                _handle_item(graph, m, to_visit)
            elif isinstance(m, Sample):
                _handle_sample(graph, m, to_visit, visited)
            elif isinstance(m, Collection):
                _handle_collection(graph, m, to_visit)
            elif isinstance(m, Plan):
                _handle_plan(graph, m, to_visit)
            else:
                raise TridentBaseException(
                    "type {} is not a valid inventory type".format(cls)
                )
    return graph


def save_inventory(
    session: SessionABC, inventory: List[InventoryType], merge_samples: bool = False
) -> List[InventoryType]:
    """Saves a list of inventory items to the server.

    :param session: the AqSession instance
    :param inventory: list of inventory items
    :param merge_samples: if True, will merge Samples by name if a sample with
        the same name already exists. See the :method:`merge_sample_by_name` method.
    :return: list of inventory that was saved.
    """
    graph = models_to_graph(session, inventory)
    new_inventory = []
    for n in nx.topological_sort(graph.reverse()):
        model = graph.nodes[n]["model"]
        if not model.id:
            new_inventory.append(model)
            if merge_samples and isinstance(model, Sample):
                model.merge()
            else:
                model.save()
    return new_inventory
