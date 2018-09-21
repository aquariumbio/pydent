"""Validate Plans"""


class PlanValidator(object):
    """
    Used to validate whether a plan is ready to submit.
    """

    def __init__(self, model, data):
        """
        Creates a PlanValidator for the ?
        """
        self.verbose = False
        self.messages = []
        self.name = ""
        self.operations = []
        self.wires = []
        super(PlanValidator, self).__init__(model, data)

    def log(self, msg):
        """
        Log a message.

        :param msg: the message to be logged
        :type msg: String
        """
        if self.verbose:
            print(msg)
        self.messages.append(msg)

    def warning(self, msg):
        """
        Log a warning.

        :param msg: the warning message to be logged
        :type msg: String
        """
        self.log("WARNING: " + msg)

    def clear_messages(self):
        """
        Clear messages.
        """
        self.messages = []

    def validate(self, verbose=False):
        """
        Check if the plan is valid.
        """
        self.verbose = verbose
        self.clear_messages()
        self.mark_leaves()

        valid = self.check_fields() and \
            self.check_io() and \
            self.check_wires()

        self.log("Plan '" + self.name + "' is " +
                 ("valid" if valid else "not valid."))

        return valid

    def check_fields(self):
        """Check that all fields are defined"""
        valid = True
        for operation in self.operations:
            for field_type in operation.operation_type.field_types:
                if field_type.array:
                    if len(operation.field_value_array(field_type.name, field_type.role)) == 0:
                        self.warning(field_type.role + " " + field_type.name +
                                     "' of '" + field_type.operation_type.name +
                                     "' cannot be an empty array.")
                        valid = False
                else:
                    if not operation.field_value(field_type.name, field_type.role):
                        self.warning(field_type.role + " " + field_type.name +
                                     "' of '" + field_type.operation_type.name +
                                     "' has not been assigned.")
                        valid = False
        return valid

    def mark_leaves(self):
        """mark all inputs as either a leaf or not"""
        for operation in self.operations:
            for field_value in operation.inputs:
                field_value.leaf = False
        for operation in self.operations:
            for field_value in operation.outputs:
                field_value.leaf = False

        for wire in self.all_wires:
            wire.destination.leaf = False

    def check_io(self):
        """check all field values for samples, items, and values"""
        valid = True
        for operation in self.operations:
            for field_value in operation.field_values:
                if field_value.field_type.is_parameter:
                    if not field_value.value:
                        self.warning("Parameter '" + field_value.name +
                                     "' of '" + field_value.operation.operation_type.name +
                                     "' has not been assigned a value.")
                        valid = False
                elif field_value.leaf:
                    if not field_value.child_item_id:
                        self.warning("Leaf '" + field_value.name +
                                     "' of '" + field_value.operation.operation_type.name +
                                     "' has not been assigned an item")
                        valid = False
                else:
                    if not field_value.child_sample_id and \
                       field_value.allowable_field_type.sample_type:
                        self.warning(field_value.role +
                                     " '" + field_value.name +
                                     "' of '" + field_value.operation.operation_type.name +
                                     "' has not been assigned a sample")
                        valid = False
        return valid

    def check_wires(self):
        """make sure all wires have have consistent endpoints"""
        valid = True
        for wire in self.all_wires:
            aft1 = wire.source.allowable_field_type
            aft2 = wire.destination.allowable_field_type
            if aft1 is None or aft2 is None:
                pass
            try:
                stid1 = wire.source.allowable_field_type.sample_type_id
                stid2 = wire.destination.allowable_field_type.sample_type_id
                otid1 = wire.source.allowable_field_type.object_type_id
                otid2 = wire.destination.allowable_field_type.object_type_id
            except:
                pass
            if stid1 != stid2 or otid1 != otid2:
                valid = False
        return valid
