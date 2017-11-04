"""Membership"""

import aq


class MembershipRecord(aq.Record):

    """MembershipRecord is a join table that associates users and groups"""

    def __init__(self, model, data):
        """Make a new MembershipRecord"""
        super(MembershipRecord, self).__init__(model, data)
        self.has_one("user", aq.User)
        self.has_one("group", aq.Group)

class MembershipModel(aq.Base):

    """MembershipModel class, generates MembershipRecords"""

    def __init__(self):
        """Make a new MembershipModel"""
        super(MembershipModel, self).__init__("Membership")

Membership = MembershipModel()
