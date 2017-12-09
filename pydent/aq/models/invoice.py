"""Invoices"""

import aq

class InvoiceRecord(aq.Record):

    """InvoiceRecord used to define a set of transactions for given month"""

    def __init__(self, model, data):
        """Make a new InvoiceRecord"""
        super(InvoiceRecord, self).__init__(model, data)


class InvoiceModel(aq.Base):

    """InvoiceModel class, generates InvoiceRecords"""

    def __init__(self):
        """Make a new InvoiceModel"""
        super(InvoiceModel, self).__init__("Invoice")


Invoice = InvoiceModel()
