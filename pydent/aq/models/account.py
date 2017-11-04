"""Accounts"""

import aq

class AccountRecord(aq.Record):

    """AccountRecord: keeps track of user transactions"""

    def __init__(self, model, data):
        """Make a new AccountRecord"""
        super(AccountRecord, self).__init__(model, data)


class AccountModel(aq.Base):

    """AccountModel class, generates AccountRecords"""

    def __init__(self):
        """Make a new AccountModel"""
        super(AccountModel, self).__init__("Account")


Account = AccountModel()
