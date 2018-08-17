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

    def __init__(self, session, plan_id=None):
        self.plan_id = plan_id
        if self.plan_id is not None:
            self.plan = session.Plan.find(plan_id)
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

    def create_operation_by_name(self, operation_type_name):
        """Adds a new operation to the plan"""
        ots = self.session.OperationType.where({"deployed": True, "name": operation_type_name})
        if ots is None or len(ots) == 0:
            raise Exception("Could not find deployed OperationType \"{}\"".format(operation_type_name))
        return self.create_operation_by_type(ots[0])

    @staticmethod
    def _find_wire(fv1, fv2):
        if fv1.outgoing_wires is not None:
            for wire in fv1.outgoing_wires:
                if wire.to_id == fv2.id:
                    return wire
        if fv2.incoming_wires is not None:
            for wire in fv2.incoming_wires:
                if wire.from_id == fv1.id:
                    return wire

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

    def quick_create_and_wire(self, otname1, otname2, fvnames=None):
        self.create_operation_by_name(otname1)
        self.create_operation_by_name(otname2)
        return self.quick_wire(otname1, otname2)

    def quick_create_chain(self, *otnames):
        prev_name = otnames[0]
        self.create_operation_by_name(prev_name)
        for otname in otnames[1:]:
            self.create_operation_by_name(otname)
            self.quick_wire(prev_name, otname)
            prev_name = otname

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
        wire = self._find_wire(fv1, fv2)
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
        cls.update(field_value)
        if field_value.field_type.ftype == 'sample':
            for fv in fvs:
                fv.sample = field_value.sample
                cls.update(fv)

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
        cls.update(op)
        cls.update(pa)

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

    def networkx(self):
        G = nx.DiGraph()
        edges, nodes = self._rid_adjacency_list()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        return G

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
