"""Plan"""

import aq


class PlanRecord(aq.PlanEquivalence, aq.PlanValidator, aq.Record):

    """Plan: Contains operations and wires"""

    def __init__(self, model, data):
        """Make a new PlanRecord"""
        self.id = None
        self.name = "Untitled Plan"
        self.status = "planning"
        self.layout = {"id": 0, "parent_id": -1, "wires": [], "name": "no name"}
        super(PlanRecord, self).__init__(model, data)
        self.has_many_generic("data_associations", aq.DataAssociation)
        self.has_many(
            "operations", aq.Operation,
            {"through": aq.PlanAssociation, "association": "operation"})
        self.has_many("wires", aq.Wire, opts={"no_getter": True})

    def add_operation(self, operation):
        """Add an operation to the plan"""
        self.append_association("operations", operation)
        return self

    def add_operations(self, operations):
        """Add a list of operations to the plan"""
        for operation in operations:
            self.append_association("operations", operation)
        return self

    def wire(self, source, destination):
        """Add a new wire to the plan"""
        wire = aq.Wire.record({})
        wire.set_association("source", source) \
            .set_association("destination", destination)
        self.append_association("wires", wire)
        return self

    def add_wires(self, pairs):
        """Add a list of wires to the plan"""
        for pair in pairs:
            self.wire(pair[0], pair[1])

    def submit(self, user, budget):
        """Try to run the plan"""
        user_query = "&user_id=" + str(user.id)
        budget_query = "?budget_id=" + str(budget.id)
        aq.http.get('/plans/start/' + str(self.id) + budget_query + user_query)

    def show(self):
        """Print the plan nicely"""
        print(self.name + " id: " + str(self.id))
        for operation in self.operations:
            operation.show(pre="  ")
        for wire in self.wires:
            wire.show(pre="  ")

    def _to_save_json(self):
        """Create just the json needed save the plan, changing the names of
        wire parts to match Aquarium internal model for wires.
        """
        return self.to_json(include=[{
            "wires": ["source", "destination"],
            "operations": ["field_values"]
        }])

    def save(self):
        """Save the plan"""
        if not self.id:
            user_query = "?user_id=" + str(aq.User.current.id)
            result = aq.http.post('/plans.json' + user_query, self._to_save_json())
            if "errors" in result:
                raise Exception("Could not save plan: " + str(result["errors"]))
            new_plan = aq.Plan.record(result)
            self.id = new_plan.id
            self.operations = new_plan.operations
            self.wires = new_plan.wires
        else:
            print("WARNING: Plan " + self.id +
                  " already saved. Cannot save again.")
        return self

    def estimate_cost(self):
        """Estimate the cost of the plan"""
        result = aq.http.post('/launcher/estimate', {"id": self.id})
        for operation in self.operations:
            for cost in result["costs"]:
                if cost["id"] == operation.id:
                    operation.cost = cost

    def field_values(self):
        """Return all field values of all operations in the plan"""
        field_value_list = []
        for operation in self.operations:
            field_value_list = field_value_list + operation.field_values
        return field_value_list

    def to_json(self, include=[], exclude=[]):
        """Convert to json, but remove some interal temporary variables first"""
        j = super(PlanRecord, self).to_json(include=include, exclude=exclude)
        del j["equivalences"]
        return j

    def all_data_associations(self):
        """Return all ata associations of all operations and items associated with the plan"""
        das = self.data_associations
        for operation in self.operations:
            das = das + operation.data_associations
            for field_value in operation.field_values:
                if field_value.item:
                    das = das + field_value.item.data_associations
        return das


class PlanModel(aq.Base):

    """PlanModel class, generates PlanRecords"""

    def __init__(self):
        """Make a new PlanModel"""
        super(PlanModel, self).__init__("Plan")

    def find(self, id):
        """Override find for plans, because the generic method is too minimal"""
        return aq.Plan.record(aq.http.get("/plans/" + str(id) + ".json"))


Plan = PlanModel()
