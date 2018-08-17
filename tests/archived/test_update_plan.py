def new_operation_by_id(plan, ot_id):
    ot = plan.session.OperationType.find(ot_id)
    if ot is None:
        raise Exception("Could not find deployed OperationType \"{}\"".format(operation_type_name))
    op = ot.instance()
    plan.add_operation(op)
    return op


def new_operation(plan, operation_type_name):
    ots = plan.session.OperationType.where({"deployed": True, "name": operation_type_name})
    if len(ots) == 0:
        raise Exception("Could not find deployed OperationType \"{}\"".format(operation_type_name))
    ot = ots[0]
    op = ot.instance()
    plan.add_operation(op)
    return op


# TODO: Operation has this implemented already
def get_routing_dict(op):
    routing_dict = {}
    for fv in op.field_values:
        routing = fv.field_type.routing
        routing_fvs = routing_dict.get(routing, [])
        routing_fvs.append(fv)
        routing_dict[fv.field_type.routing] = routing_fvs
    return routing_dict


def set_field_value(field_value, sample=None, item=None, container=None, value=None):
    routing = field_value.field_type.routing
    fvs = get_routing_dict(field_value.operation)[routing]
    field_value.set_value(sample=sample, item=item, container=container, value=value)
    update(field_value)
    if field_value.field_type.ftype == 'sample':
        for fv in fvs:
            fv.sample = field_value.sample
            update(fv)


def find_wire(fv1, fv2):
    if fv1.outgoing_wires is not None:
        for wire in fv1.outgoing_wires:
            if wire.to_id == fv2.id:
                return wire


def add_wire(plan, fv1, fv2):
    """Note that fv2.operation will not inherit parent_id of fv1"""
    wire = find_wire(fv1, fv2)
    if wire is None:
        print("Creating new wire")
        plan.wire(fv1, fv2)
    # propogate up?
    if fv2.sample is None and fv1.sample is not None:
        set_field_value(fv2, sample=fv1.sample)
    if fv1.sample is None and fv2.sample is not None:
        set_field_value(fv1, sample=fv2.sample)
    if fv1.sample.id != fv2.sample.id:
        set_field_value(fv2, sample=fv1.sample)


def remove_wire(fv1, fv2):
    pass

def test_update_a_plan(session):
    plan = session.Plan.find(121081)
    new_operation(plan, "Yeast Transformation")
    plan.to_save_json()
