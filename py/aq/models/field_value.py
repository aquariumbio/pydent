import py.aq as aq


class FieldValueRecord(aq.Record):

    def __init__(self,model,data):
        self.value = None
        self.child_item_id = None
        self.child_sample_id = None
        self.row = None
        self.column = None
        self.role = None
        self.field_type = None
        self.allowable_field_type_id = None
        super(FieldValueRecord,self).__init__(model,data)
        self.has_one("field_type", aq.FieldType)
        self.has_one("allowable_field_type", aq.AllowableFieldType)
        self.has_one("item",   aq.Item, opts={"reference": "child_item_id"})
        self.has_one("sample", aq.Sample, opts={"reference": "child_sample_id"})
        self.has_one("operation", aq.Operation, opts={"reference": "parent_id"})
        self.has_one("parent_sample", aq.Sample, opts={"reference": "parent_id"})

    def show(self,pre=""):
        if self.sample:
            if self.child_item_id:
                item = " item: " + str(self.child_item_id) + \
                       " in " + self.item.object_type.name
            else:
                item = ""
            print(pre  + self.role +
                  ". " + self.name +
                  ": " + self.sample.name + item)
        elif self.value:
            print(pre  + self.role +
                  ". " + self.name +
                  ": " + self.value)

    def set_value(self,value,sample,container,item):

        object_type = None

        if value:
            self.value = value

        if sample:
            self.sample = sample
            self.child_sample_id = sample.id

        if item:
            self.item = item
            self.child_item_id = item.id
            object_type = item.object_type

        if container:
            object_type = container

        if item and container and item.object_type_id != container.id:
            raise Exception("Item " + str(item.id) +
                            "is not in container " + container.name)

        for aft in self.field_type.allowable_field_types:
            if object_type and sample:
                if object_type.id == aft.object_type_id and \
                    sample.sample_type_id == aft.sample_type_id:
                    aft.object_type = object_type
                    aft.sample_type = sample.sample_type
                    self.allowable_field_type_id = aft.id
                    self.allowable_field_type = aft
            elif object_type:
                if object_type.id == aft.object_type_id:
                    aft.object_type = object_type
                    self.allowable_field_type_id = aft.id
                    self.allowable_field_type = aft
            elif sample:
                if sample.sample_type_id == aft.sample_type_id:
                    aft.sample_type = sample.sample_type
                    self.allowable_field_type_id = aft.id
                    self.allowable_field_type = aft

        if ( sample or object_type ) and not self.allowable_field_type:
            raise Exception("No allowable field type found for " +
                            self.role + " " + self.name)

        return self

    def choose_item(self):
        items = self.compatible_items()
        if len(items) > 0:
            self.child_item_id = items[0].id
            self.item = items[0]
            return items[0]
        return None

    def compatible_items(self):
        result = aq.http.post("/json/items", {
            "sid": self.sample.id,
            "oid": self.allowable_field_type.object_type_id })
        items = []
        for element in result:
            if "collection" in element:
                items.append(aq.Collection.record(element["collection"]))
            else:
                items.append(aq.Item.record(element))
        return items

class FieldValueModel(aq.Base):

    def __init__(self):
        super(FieldValueModel,self).__init__("FieldValue")

FieldValue = FieldValueModel()
