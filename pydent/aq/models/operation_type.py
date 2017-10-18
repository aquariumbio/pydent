from pydent import aq


class OperationTypeRecord(aq.Record):

    def __init__(self,model,data):
        super(OperationTypeRecord,self).__init__(model,data)
        self.has_many("operations", aq.Operation)
        self.has_many_generic("field_types", aq.FieldType)
        self.has_many_generic("codes", aq.Code)

    def code(self,name):
        latest = [ code for code in self.codes
                        if not code.child_id and code.name == name ]
        if len(latest) == 1:
            return latest[0]
        else:
            return None

    def instance(self,x=None,y=None):
        operation = aq.Operation.record({
            "operation_type_id": self.id,
            "status": "planning",
            "x": x,
            "y": y
        })
        operation.operation_type = self
        operation.init_field_values()
        return operation

    def field_type(self,name,role):
        fts = [ ft for ft in self.field_types \
                if ft.name == name and ft.role == role]
        if len(fts) == 0:
            return None
        else:
            return fts[0]

class OperationTypeModel(aq.Base):

    def __init__(self):
        super(OperationTypeModel,self).__init__("OperationType")

OperationType = OperationTypeModel()
