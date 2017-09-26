import aq

_x = 16
_y = 32

def next_position():
    global _x
    global _y
    _x += 176
    if _x > 800:
        _x = 0
        _y += 46
    return [ _x, _y ]

class OperationRecord(aq.Record):

    def __init__(self,model,data):
        self.cost = None
        super(OperationRecord,self).__init__(model,data)
        self.has_many_generic("field_values", aq.FieldValue)
        self.has_many_generic("data_associations", aq.DataAssociation)
        self.has_one("operation_type", aq.OperationType)
        self.has_many("jobs",
            aq.Job,
            { "through": aq.JobAssociation, "association": "job"})

    def set_field_value(self, name, role,
               sample=None, item=None, value=None, container=None):

        field_value = aq.FieldValue.record({
            "name": name,
            "role": role,
            "parent_class": "Operation"
        })
        field_value.operation = self

        self.set_field_type(field_value)
        field_value.set_value(value,sample,container,item)
        self.append_association("field_values", field_value)

        return self

    def set_field_type(self,field_value):
        for field_type in self.operation_type.field_types:
            if field_type.name == field_value.name and \
               field_type.role == field_value.role:
               field_value.field_type = field_type
               return
        raise Exception("Could not find field type of " + field_value.role +
                        " named " + field_value.name +
                        " in operation of type " + self.operation_type.name)

    def set_input(self,name,**kwargs):
        return self.set_field_value(name,'input',**kwargs)

    def set_output(self,name,**kwargs):
        return self.set_field_value(name,'output',**kwargs)

    def field_value(self,name,role):
        fvs = [ fv for fv in self.field_values \
                if fv.name == name and fv.role == role]
        if len(fvs) == 0:
            return None
        elif fvs[0].field_type.array:
            return fvs
        else:
            return fvs[0]

    def input(self,name):
        return self.field_value(name,'input')

    def output(self,name):
        return self.field_value(name,'output')

    @property
    def inputs(self):
        return [ fv for fv in self.field_values if fv.role == 'input' ]

    @property
    def outputs(self):
        return [ fv for fv in self.field_values if fv.role == 'output' ]

    def show(self,pre=""):
        print(pre + self.operation_type.name + " " + str(self.cost))
        for field_value in self.field_values:
            field_value.show(pre=pre+"  ")

    def to_json(self):
        p = next_position()
        return {
            "operation_type_id": self.operation_type_id,
            "field_values": [ fv.to_json() for fv in self.field_values ],
            "status": self.status,
            "routing": {},
            "parent": 0,
            "x": p[0],
            "y": p[1],
            "rid": self.rid
        }

class OperationModel(aq.Base):

    def __init__(self):
        super(OperationModel,self).__init__("Operation")

Operation = OperationModel()
