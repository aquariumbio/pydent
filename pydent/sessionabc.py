from abc import ABC


class SessionABC(ABC):
    """Session abstract base class."""

    Account = None  #: Account model interface
    AllowableFieldType = None  #: AllowableFieldType model interface
    Budget = None  #: Budget model interface
    Code = None  #: Code model interface
    Collection = None  #: Collection model interface
    DataAssociation = None  #: DataAssociation model interface
    FieldType = None  #: FieldType model interface
    FieldValue = None  #: FieldValue model interface
    Group = None  #: Group model interface
    Invoice = None  #: Invoice model interface
    Item = None  #: Item model interface
    Job = None  #: Job model interface
    JobAssociation = None  #: JobAssociation model interface
    Library = None  #: Library model interface
    Membership = None  #: Membership model interface
    ObjectType = None  #: ObjectType model interface
    Operation = None  #: Operation model interface
    OperationType = None  #: OperationType model interface
    PartAssociation = None  #: PartAssociation model interface
    Plan = None  #: Plan model interface
    PlanAssociation = None  #: PlanAssociation model interface
    Sample = None  #: Sample model interface
    SampleType = None  #: SampleType model interface
    Upload = None  #: Upload model interface
    User = None  #: User model interface
    UserBudgetAssociation = None  #: UserBudgetAssociation model interface
    Wire = None  #: Wire model interface
