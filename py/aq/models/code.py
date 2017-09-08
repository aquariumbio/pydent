import aq

class CodeRecord(aq.Record):
    def __init__(self,model,data):
        super(CodeRecord,self).__init__(model,data)

class CodeModel(aq.Base):

    def __init__(self):
        super(CodeModel,self).__init__("Code")

Code = CodeModel()
