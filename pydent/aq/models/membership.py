from pydent import aq


class MembershipRecord(aq.Record):
    def __init__(self,model,data):
        super(MembershipRecord,self).__init__(model,data)

class MembershipModel(aq.Base):

    def __init__(self):
        super(MembershipModel,self).__init__("Membership")

Membership = MembershipModel()
