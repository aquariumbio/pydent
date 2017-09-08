import aq

class InvoiceRecord(aq.Record):
    def __init__(self,model,data):
        super(InvoiceRecord,self).__init__(model,data)

class InvoiceModel(aq.Base):

    def __init__(self):
        super(InvoiceModel,self).__init__("Invoice")

Invoice = InvoiceModel()
