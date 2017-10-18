import py.aq as aq


class AccountRecord(aq.Record):
    def __init__(self, model, data):
        super(AccountRecord, self).__init__(model, data)


class AccountModel(aq.Base):
    def __init__(self):
        super(AccountModel, self).__init__("Account")


Account = AccountModel()
