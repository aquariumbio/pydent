"""Operation Type"""

import aq


class OperationTypeRecord(aq.Record):

    """ObjectTypeRecord defines the inputs, outputs, and code of a unit
    operation
    """

    def __init__(self, model, data):
        """Make a new OperationTypeRecord"""
        super(OperationTypeRecord, self).__init__(model, data)
        self.has_many("operations", aq.Operation)
        self.has_many_generic("field_types", aq.FieldType)
        self.has_many_generic("codes", aq.Code)

    def code(self, name):
        """Return the code named 'name' associated with the operation type"""
        codes = [code for code in self.codes if code.name == name]
        if len(codes) > 0:
            return codes[len(codes) - 1]
        else:
            return None

    def instance(self, x_pos=None, y_pos=None):
        """Get a new operation whose type is this operation type"""
        operation = aq.Operation.record({
            "operation_type_id": self.id,
            "status": "planning",
            "x": x_pos,
            "y": y_pos
        })
        operation.operation_type = self
        operation.init_field_values()
        return operation

    def field_type(self, name, role):
        """Get the field type named 'name'"""
        fts = [ft for ft in self.field_types
               if ft.name == name and ft.role == role]
        if len(fts) == 0:
            return None
        else:
            return fts[0]


class OperationTypeModel(aq.Base):

    """OperationTypeModel class, generates OperationTypeRecords"""

    def __init__(self):
        """Make a new OperationTypeModel"""
        super(OperationTypeModel, self).__init__("OperationType")


OperationType = OperationTypeModel()
