from marshmallow import Schema, fields
import networkx as nx

class PositionSchema(Schema):
    x = fields.Int()
    y = fields.Int()


class IOSchema(PositionSchema):
    id = fields.Int()
    height = fields.Int()
    width = fields.Int()
    model = fields.Dict()


class LayoutWireSchema(Schema):
    from_module = fields.Dict(allow_none=True)
    to_op = fields.Int()
    to = fields.Dict()
    _from = fields.Dict(data_key="from")


class TextBoxSchema(PositionSchema):
    anchor = fields.Nested(PositionSchema)
    markdown = fields.String()


class LayoutSchema(IOSchema):
    parent_id = fields.Int()
    name = fields.String()
    input = fields.Nested(IOSchema, many=True, allow_none=True)
    output = fields.Nested(IOSchema, many=True, allow_none=True)
    documentation = fields.String()
    children = fields.Nested("LayoutSchema", many=True, allow_none=True)
    wires = fields.Nested(LayoutWireSchema, allow_none=True)
    text_boxes = fields.Nested(TextBoxSchema, many=True, allow_none=True)


class Position(object):
    DEFAULT_X = 160
    DEFAULT_y = 160

    def __init__(self, x=None, y=None):
        if x is None:
            x = self.DEFAULT_X
        if y is None:
            y = self.DEFAULT_Y
        self.x = x
        self.y = y


class IO(Position):
    DEFAULT_WIDTH = 160
    DEFAULT_HEIGHT = 60

    def __init__(self, model, width=None, height=None):
        if width is None:
            width = self.DEFAULT_WIDTH
        if height is None:
            height = self.DEFAULT_HEIGHT
        self.width = width
        self.height = height
        self.model = model


class Module(IO):

    def __init__(self, id, name, documentation):
        self.id = id
        self.name = name
        self.documentation = documentation
        self.parent_id = 0
        self.text_boxes = None
        self.children = None
        self.input = None
        self.output = None
        self.wires = None
        super(IO).__init__("Module")

    def add_wire(self):
        pass

    def add_child(self):
        pass

    def add_input(self):
        pass

    def add_output(self):
        pass

    def add_text(self):
        pass


class Canvas(object):
    """A user-interface for making experimental plans and layouts."""

    def __init__(self, session, plan_id=None):
        self.plan_id = plan_id
        if self.plan_id is not None:
            self.plan = session.Plan.find(plan_id)
            if self.plan is None:
                raise Exception("Could not find plan with id={}".format(plan_id))
        else:
            self.plan = session.Plan.new()
        self.session = session

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
        self.plan.create()

    def save(self):
        """Save the plan on Aquarium"""
        self.plan.save()
        return self.plan

    def create_operation_by_type(self, ot):
        op = ot.instance()
        self.plan.add_operation(op)
        return op

    def create_operation_by_id(self, ot_id):
        ot = self.session.OperationType.find(ot_id)
        return self.create_operation_by_type(ot)

    def create_operation_by_name(self, operation_type_name, category=None):
        """Adds a new operation to the plan"""
        query = {"deployed": True, "name": operation_type_name}
        if category is not None:
            query['category'] = category
        ots = self.session.OperationType.where(query)
        if len(ots) > 1:
            raise Exception("Found more than one OperationType for query \"{}\"".format(query))
        if ots is None or len(ots) == 0:
            raise Exception("Could not find deployed OperationType \"{}\"".format(operation_type_name))
        return self.create_operation_by_type(ots[0])

    @staticmethod
    def eq(m1, m2):
        if m1.id is None and m2.id is None:
            if m1.rid == m2.rid:
                return True
        elif m1.id == m2.id:
            return True
        return False

    # def get_operation_where(self, **params):
    #     ops = []
    #     for op in self.plan.operations:
    #         passes = True
    #         for k, v in params.items():
    #             if getattr(op, k) != v:
    #                 passes = False
    #                 break
    #         ops.append(op)
    #     return ops

    def get_operation(self, id):
        for op in self.plan.operations:
            if op.id == id:
                return op

    def get_wire(self, fv1, fv2):
        for wire in self.plan.wires:
            if self.eq(wire.source, fv1) and self.eq(wire.destination, fv2):
                return wire

    def get_outgoing_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self.eq(wire.source, fv):
                wires.append(wire)
        return wires

    def get_incoming_wires(self, fv):
        wires = []
        for wire in self.plan.wires:
            if self.eq(wire.destination, fv):
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
    def _find_matching_afts_for_ops(cls, op1, op2):
        outputs = [fv for fv in op1.outputs if fv.field_type.ftype == 'sample']
        inputs = [fv for fv in op2.inputs if fv.field_type.ftype == 'sample']

        matching_afts = []
        for output in outputs:
            for input in inputs:
                matching_afts += cls._find_matching_afts(output, input)
        return matching_afts

    @staticmethod
    def _find_matching_afts(output, input):
        afts = []
        output_afts = output.field_type.allowable_field_types
        input_afts = input.field_type.allowable_field_types
        for input_aft in input_afts:
            for output_aft in output_afts:
                if input_aft.sample_type_id == output_aft.sample_type_id and \
                        input_aft.object_type_id == output_aft.object_type_id:
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
        return self.quick_wire(otname1, otname2)

    def quick_create_chain(self, *op_or_otnames, category=None):
        def resolve_op(op):
            if isinstance(op, tuple):
                return self.create_operation_by_name(op[0], category=op[1])
            if isinstance(op, str):
                print("Creating operation \"{}\"".format(op))
                return self.create_operation_by_name(op, category=category)
            return op

        op1 = resolve_op(op_or_otnames[0])
        ops = [op1]
        for op2 in op_or_otnames[1:]:
            op2 = resolve_op(op2)
            ops.append(op2)
            self.quick_wire_ops(op1, op2)
            op1 = op2
        return ops

    def quick_wire_ops(self, op1, op2, fvnames=None):
        if fvnames is not None:
            if len(fvnames) == 2:
                return self.add_wire(op1.output(fvnames[0]), op2.input(fvnames[1]))
            else:
                raise Exception("Field Value names must be a list or tupe of length 2.")

        for aft1, aft2 in self._find_matching_afts_for_ops(op1, op2):
            o = op1.output(aft1.field_type.name)
            i = op2.input(aft2.field_type.name)
            o.allowable_field_type_id = aft1.id
            i.allowable_field_type_id = aft2.id
            return self.add_wire(o, i)

    def quick_wire(self, otname1, otname2, fvnames=None):
        """Wires together the last added operations."""
        op1 = self.find_operations_by_name(otname1)[-1]
        op2 = self.find_operations_by_name(otname2)[-1]
        return self.quick_wire_ops(op1, op2, fvnames=fvnames)

    def add_wire(self, fv1, fv2):
        """Note that fv2.operation will not inherit parent_id of fv1"""
        wire = self.get_wire(fv1, fv2)
        if wire is None:
            # print("Creating new wire")
            self.plan.wire(fv1, fv2)

            # check and set allowable field type
            afts = self._find_matching_afts(fv1, fv2)
            if len(afts) == 0:
                raise Exception("Cannot wire \"{}\" to \"{}\". No allowable field types match."
                                .format(fv1.name, fv2.name))
            fv1.allowable_field_type_id = afts[0][0].id
            fv2.allowable_field_type_id = afts[0][1].id
        # propogate up?
        if fv1.sample is not None and (fv2.sample is None or fv2.sample.id != fv1.sample.id):
            self.set_field_value(fv2, sample=fv1.sample)
        if fv1.sample is None and fv2.sample is not None:
            self.set_field_value(fv1, sample=fv2.sample)

    @staticmethod
    def get_routing_dict(op):
        routing_dict = {}
        for fv in op.field_values:
            routing = fv.field_type.routing
            routing_fvs = routing_dict.get(routing, [])
            routing_fvs.append(fv)
            routing_dict[fv.field_type.routing] = routing_fvs
        return routing_dict

    @classmethod
    def set_field_value(cls, field_value, sample=None, item=None, container=None, value=None):
        routing = field_value.field_type.routing
        fvs = cls.get_routing_dict(field_value.operation)[routing]
        field_value.set_value(sample=sample, item=item, container=container, value=value)
        # cls._json_update(field_value)
        if field_value.field_type.ftype == 'sample':
            for fv in fvs:
                fv.sample = field_value.sample
                # cls._json_update(fv)

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
        return [op for op in self.plan.operations if
                op.operation_type.name == operation_type_name]

    def replan(self):
        """Replan"""
        canvas = self.__class__()
        canvas.plan = self.plan.replan()
        return canvas

    def _adjacency_list_helper(self, id_getter):
        edges = []
        nodes = []
        for wire in self.plan.wires:
            from_id = id_getter(wire.source.operation)
            to_id = id_getter(wire.destination.operation)
            if from_id is not None and to_id is not None:
                edges.append((from_id, to_id))
        for op in self.plan.operations:
            op_id = id_getter(op)
            if op_id is not None:
                nodes.append(op_id)
        return edges, nodes

    def _rid_adjacency_list(self):
        return self._adjacency_list_helper(lambda x: x.rid)

    def _adjacency_list(self):
        def get_id(model):
            id = model.id
            if id is None:
                id = "r{}".format(model.rid)
            return id
        return self._adjacency_list_helper(get_id)

    @staticmethod
    def _id_getter(model):
        id = model.id
        if id is None:
            id = "r{}".format(model.rid)
        return id

    def networkx(self):
        G = nx.DiGraph()
        edges = []
        nodes = []

        for wire in self.plan.wires:
            from_id = self._id_getter(wire.source.operation)
            to_id = self._id_getter(wire.destination.operation)
            if from_id is not None and to_id is not None:
                edges.append((from_id, to_id))
        for op in self.plan.operations:
            op_id = self._id_getter(op)
            if op_id is not None:
                G.add_node(op_id, operation=op)
        G.add_edges_from(edges)

        return G

    def get_networkx_predecessors(self, op_id):
        return self.networkx.predecessors(self._id_getter(op_id))

    def get_networkx_successors(self, op_id):
        return self.networkx.successors(self._id_getter(op_id))

    def topo_sort(self):
        G = self.networkx()
        subgraphs = self.get_subgraphs(G)
        x, y = 100, 100
        for subgraph in subgraphs:
            ops = [G.node[n]['operation'] for n in subgraph.nodes]
            self.topo_sort_helper(subgraph)
            self.adjust_upper_left(ops, x, y)
            x += self.bounds_of_ops(ops)[1][0]

    def topo_sort_helper(self, G):
        """Attempt a rudimentary topological sort on the plan"""
        from collections import OrderedDict

        _x = 100
        _y = 100

        y = _y
        delta_x = 170
        delta_y = 70

        sorted = list(nx.topological_sort(G))[::-1]
        res = nx.single_source_shortest_path_length(G, sorted[-1])
        by_depth = OrderedDict()
        for k, v in res.items():
            by_depth.setdefault(v, [])
            by_depth[v].append(k)
        print(by_depth)
        for depth, op_ids in reversed(list(by_depth.items())):
            ops = [G.node[op_id]['operation'] for op_id in op_ids]
            x = _x
            for op in ops:
                op.x = x
                op.y = y
                x += delta_x
            self.align_x_with_successors(ops)
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
        self.adjust_upper_left(ops, _x, _y)

    @staticmethod
    def get_subgraphs(G):
        node_list = list(G.nodes)
        subgraphs = []
        while len(node_list) > 0:
            node = node_list[-1]
            subgraph = nx.bfs_tree(G.to_undirected(), node)
            for n in subgraph.nodes:
                node_list.remove(n)
            subgraphs.append(G.subgraph(subgraph.nodes))
        return subgraphs

    def align_x_with_successors(self, ops):
        successors = []
        G = self.networkx()
        for op in ops:
            successors += [G.node[x]['operation'] for x in G.successors(self._id_getter(op))]
        x, y = self.midpoint_of_ops(ops)
        px = x
        if len(successors) > 0:
            px, _ = self.midpoint_of_ops(successors)
        self.translate_ops(ops, px - x, 0)
        return ops

    def align_x_with_predecessors(self, ops):
        predecessors = []
        G = self.networkx()
        for op in ops:
            predecessors += [G.node[x]['operation'] for x in G.predecessors(self._id_getter(op))]
        x, y = self.midpoint_of_ops(ops)
        px = x
        if len(predecessors) > 0:
            px, _ = self.midpoint_of_ops(predecessors)
        self.translate_ops(ops, px - x, 0)
        return ops


    @classmethod
    def adjust_upper_left(cls, ops, x, y):
        xb, yb = cls.bounds_of_ops(ops)[0]
        cls.translate_ops(ops, x - xb, y-yb)

    @staticmethod
    def bounds_of_ops(ops):
        """Returns upper-left and lower-right bounding corners of the plan (assuming no modules...)"""
        xarr = [op.x for op in ops]
        yarr = [op.y for op in ops]
        return ((min(xarr), min(yarr)), (max(xarr), max(yarr)))

    @classmethod
    def midpoint_of_ops(cls, ops):
        ul, lr = cls.bounds_of_ops(ops)
        x, y = (lr[0] - ul[0])/2 + ul[0], (lr[1] - ul[1])/2 + ul[1]
        return x, y

    @staticmethod
    def translate_ops(ops, deltax, deltay):
        for op in ops:
            op.x += deltax
            op.y += deltay
        return ops

    # def draw(self):
        # import matplotlib.pyplot as plt
        # pos = {op.id: (op.x, op.y) for op in self.plan.operations}
        # G = self.networkx()
        # nx.draw(G, pos=pos)
        # plt.draw()

    # @staticmethod
    # def is_leaf(op):
    #     wires = []
    #     for input in op.inputs:
    #         _wires = input.incoming_wires
    #         if _wires is not None:
    #             wires += _wires
    #     if len(wires) == 0:
    #         return True
    #     return False

    # def successors(self, fv):
    #     return [w for w in self.plan.wires if w.source == fv]
    #
    # def predecessors(self, fv):
    #     return [w for w in self.plan.wires if w.destination == fv]


    # @staticmethod
    # def is_root(op):
    #     wires = []
    #     for output in op.outputs:
    #         _wires = output.outgoing_wires
    #         if _wires is not None:
    #             wires += _wires
    #     if len(wires) == 0:
    #         return True
    #     return False
    #
    # def leafs(self):
    #     leafs = []
    #     for op in self.plan.operations:
    #         for input in op.inputs:
    #             wires = input.incoming_wires
    #             if wires is None or len(wires) == 0:


# def default_layout():
#     return {'children': None,
#             'documentation': 'No documentation yet for this module.',
#             'height': 60,
#             'id': 0,
#             'input': None,
#             'model': {'model': 'Module'},
#             'name': 'Untitled Module 0',
#             'output': None,
#             'parent_id': -1,
#             'text_boxes': None,
#             'width': 160,
#             'wires': None,
#             'x': 160,
#             'y': 160}


# def destroy_layout(plan, keep_text=True):
#     for op in plan.operations:
#         op.parent_id = 0
#         update(op)
#     new_layout = default_layout()
#     if keep_text:
#         if 'text_boxes' in plan.layout:
#             new_layout['text_boxes'] = plan.layout['text_boxes']
#     plan.layout = new_layout
#     update(plan)
#
# def available_predecessors(operation, field_value_name):
#     input = operation.input(field_value_name)
#     afts = []
#     operation.session.OperationType.where({""})
#
#
# def remove_wire(fv1, fv2):
#     pass
