import py.aq as aq

class LibraryRecord(aq.Record):

    def __init__(self,model,data):
        super(LibraryRecord,self).__init__(model,data)
        self.has_many("operations", aq.Operation)
        self.has_many_generic("field_types", aq.FieldType)
        self.has_many_generic("codes", aq.Code)

    def code(self,name):
        latest = [ code for code in self.codes if not code.child_id and code.name == name ]
        if len(latest) == 1:
            return latest[0]
        else:
            return None

class LibraryModel(aq.Base):

    def __init__(self):
        super(LibraryModel,self).__init__("Library")

Library = LibraryModel()
