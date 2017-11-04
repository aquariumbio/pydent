import aq

_verbose = False
_messages = []


def log(msg):
    global _verbose
    if _verbose:
        print(msg)
    _messages.append(msg)


def warning(msg):
    log("WARNING: " + msg)


def messages():
    global _messages
    return _messages


def clear_messages():
    global _messages
    _messages = []


def plan(plan, verbose=False):

    global _verbose
    _verbose = verbose
    clear_messages()

    mark_leaves(plan)

    valid = check_fields(plan) and \
        check_io(plan) and \
        check_wires(plan)

    # check that wires have consistent ends

    log("Plan '" + plan.name + "' is " +
        ("valid" if valid else "not valid."))

    return valid


def check_fields(plan):
    """Check that all fields are defined"""
    valid = True
    for operation in plan.operations:
        for field_type in operation.operation_type.field_types:
            if field_type.array:
                if len(operation.field_value(field_type.name)) == 0:
                    warning(field_type.role + " " + field_type.name +
                            "' of '" + field_type.operation_type.name +
                            "' cannot be an empty array.")
                    valid = False
            else:
                if not operation.field_value(field_type.name, field_type.role):
                    warning(field_type.role + " " + field_type.name +
                            "' of '" + field_type.operation_type.name +
                            "' has not been assigned.")
                    valid = False
    return valid


def mark_leaves(plan):
    """mark all inputs as either a leaf or not"""
    for operation in plan.operations:
        for field_value in operation.outputs:
            field_value.leaf = False
        for field_value in operation.inputs:
            field_value.leaf = True

    for wire in plan.wires:
        wire.destination.leaf = False


def check_io(plan):
    """check all field values for samples, items, and values"""
    valid = True
    for operation in plan.operations:
        for field_value in operation.field_values:
            if field_value.field_type.is_parameter:
                if not field_value.value:
                    warning("Parameter '" + field_value.name +
                            "' of '" + field_value.operation.operation_type.name +
                            "' has not been assigned a value.")
                    valid = False
            elif field_value.leaf:
                if not field_value.child_item_id:
                    warning("Leaf '" + field_value.name +
                            "' of '" + field_value.operation.operation_type.name +
                            "' has not been assigned an item")
                    valid = False
            else:
                if not field_value.child_sample_id and \
                   field_value.allowable_field_type.sample_type:
                    warning(field_value.role +
                            " '" + field_value.name +
                            "' of '" + field_value.operation.operation_type.name +
                            "' has not been assigned a sample")
                    valid = False
    return valid


def check_wires(plan):
    """make sure all wires have have consistent endpoints"""
    valid = True
    for wire in plan.wires:
        stid1 = wire.source.allowable_field_type.sample_type_id
        stid2 = wire.destination.allowable_field_type.sample_type_id
        otid1 = wire.source.allowable_field_type.object_type_id
        otid2 = wire.destination.allowable_field_type.object_type_id
        if stid1 != stid2 or otid1 != otid2:
            valid = False
    return valid
