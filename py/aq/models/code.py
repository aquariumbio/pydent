import aq

class CodeRecord(aq.Record):

    def __init__(self,model,data):
        super(CodeRecord,self).__init__(model,data)

    def update(self):
        # Todo: make server side controller for code objects
        # since they may not always be tied to specific parent
        # controllers
        if self.parent_class == "OperationType":
            controller = "operation_types"
        elif self.parent_class == "Library":
            controller = "libraries"
        else:
            raise Exception("No code update controller available.")
        result = aq.http.post("/" + controller + "/code", {
            "id": self.parent_id,
            "name": self.name,
            "content": self.content
        })
        if "id" in result:
            self.id = result["id"]
        else:
            raise Exception("Unable to update code object.")

class CodeModel(aq.Base):

    def __init__(self):
        super(CodeModel,self).__init__("Code")

Code = CodeModel()
