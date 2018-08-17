from pydent import designer


def test_add_operation_by_name(session):
    plan = session.Plan.find(121080)
    op = designer.create_operation_by_name(plan, "Yeast Transformation")
    print(op.id)


def test_layout(session):
    plan = session.Plan.find(121081)
    layout = plan.layout
    pass


def test_find_layout_inconsistencies(session):
    pass

def test_add_operation_by_id(session):
    pass

def test_remove_operation_by_id(session):
    pass

def test_find_operations_of_type(session):
    pass

# add wire

# remove wire

# validate plan

# update plan

# new plan

# move operation

# create a new layout

# create a new module

# create intra-plan wire

# propogate sample and items along wires