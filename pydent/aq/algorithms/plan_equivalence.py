"""Plan I/O Equivalance Algorithm"""

def equivalence_class_of(partition, field_value):
    """Return the partition in sets containing a"""
    for equivalence_class in partition:
        if field_value in equivalence_class:
            return equivalence_class
    return None

def join(sets, partition_1, partition_2):
    """Join the partitions together"""
    sets.remove(partition_1)
    sets.remove(partition_2)
    sets.append(partition_1 + partition_2)
    return sets

def show_classes(partition):
    """Show the equivalence classes in sets"""
    for equivalence_class in partition:
        print([fv.rid for fv in equivalence_class])

class PlanEquivalence:

    """PlanEquivalence class, which should be mixed in with the Plan class. It
    is used to determine which I/O values of the operation in a plan are
    equivalent in the sense that defining one should define the other. for
    example, two I/O connected by a wire, or two I/O with in the same
    operation with the same routing ID are equivalent.
    """

    def __init__(self, model, data):
        """Initialize Plan Equivalance attributes"""
        self.operations = []
        self.wires = []
        # self.field_values = []
        self.equivalences = None
        super(PlanEquivalence, self).__init__(model, data)


    def equiv(self, field_value_1, field_value_2):
        """Deterimine if two field values are equivalent"""
        if field_value_1.operation == field_value_2.operation and \
           field_value_1.field_type.routing == field_value_2.field_type.routing:
            return True
        for wire in self.wires:
            if (wire.source == field_value_1 and wire.destination == field_value_2) or \
               (wire.source == field_value_2 and wire.destination == field_value_1):
                return True
        return False

    def classes(self):
        """Find all the equivalence classes of field values"""
        fvs = self.field_values()
        num = len(fvs)
        sets = [[fv] for fv in fvs]
        changed = True
        while changed:
            changed = False
            for i in range(num):
                for j in range(i + 1, num):
                    class_i = equivalence_class_of(sets, fvs[i])
                    class_j = equivalence_class_of(sets, fvs[j])
                    if self.equiv(fvs[i], fvs[j]) and class_i and class_j and class_i != class_j:
                        sets = join(sets, class_i, class_j)
                        changed = True
        return sets

    def set(self, field_value, sample, container):
        """Set a field value and all equivalent field values to the given sample and container"""
        for field_value in self.field_values():
            field_value.marked = False
        self.mark_leaves()
        self.__set_aux(field_value, sample, container)
        return self

    def __set_aux(self, field_value, sample, container):
        """Auxilliary method for set"""
        if self.equivalences is None:
            self.equivalences = self.classes()
        for other_field_value in equivalence_class_of(self.equivalences, field_value):
            if not other_field_value.marked:
                other_field_value.marked = True
                other_field_value.set_value(None, sample, container, None)
                if other_field_value.leaf:
                    other_field_value.choose_item()
                self.instantiate_operation(
                    other_field_value.operation, other_field_value.field_type.routing, sample)

    def instantiate_operation(self, operation, routing, sample):
        """Set all of the field values in the operation with routing id 'routing' to the sample"""
        for ot_field_type in operation.operation_type.field_types:
            if ot_field_type.routing != routing and not ot_field_type.array:
                for st_field_type in sample.sample_type.field_types:
                    if st_field_type.ftype == 'sample' and ot_field_type.name == st_field_type.name:
                        subsample = sample.field_value(st_field_type.name).sample
                        self.__set_aux(operation.field_value(
                            ot_field_type.name, ot_field_type.role), subsample, None)
