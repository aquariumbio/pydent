"""Code"""

import aq

class CodeRecord(aq.Record):

    """CodeRecord used to store versions of code for protocols, preconditions,
     etc.
     """

    def __init__(self, model, data):
        """Make a new CodeRecord"""
        self.parent_id = None
        self.updated_at = None
        super(CodeRecord, self).__init__(model, data)
        self.has_one("user", aq.User)

    def update(self):
        """Update a code object by sending new content to Aquarium"""
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
            self.parent_id = result["parent_id"]
            self.updated_at = result["updated_at"]
        else:
            raise Exception("Unable to update code object.")


class CodeModel(aq.Base):

    """CodeModel class, generates CodeRecords"""

    def __init__(self):
        """Make a new CodeModel"""
        super(CodeModel, self).__init__("Code")


Code = CodeModel()
