"""Plan I/O Equivalance Algorithm"""

import aq


class PlanEquivalence:

    """PlanEquivalence class, which should be mixed in with the Plan class. It
    is used to determine which I/O values of the operation in a plan are
    equivalent in the sense that defining one should define the other. for
    example, two I/O connected by a wire, or two I/O with in the same
    operation with the same routing ID are equivalent.
    """

    def equiv(self, a, b):
        """Deterimine if two field values are equivalent"""
        if a.operation == b.operation and a.field_type.routing == b.field_type.routing:
            return True
        for wire in self.wires:
            if (wire.source == a and wire.destination == b) or \
               (wire.source == b and wire.destination == a):
                return True
        return False

    def partition_of(self, sets, a):
        """Return the partition in sets containing a"""
        for s in sets:
            if a in s:
                return s
        return None

    def join(self, sets, A, B):
        """Join the partitions A and B together"""
        sets.remove(A)
        sets.remove(B)
        sets.append(A + B)
        return sets

    def show_classes(self, sets):
        """Show the equivalence classes in sets"""
        for s in sets:
            print([fv.rid for fv in s])

    def classes(self):
        """Find all the equivalence classes of field values"""
        fvs = self.field_values()
        n = len(fvs)
        sets = [[fv] for fv in fvs]
        changed = True
        while changed:
            changed = False
            for i in range(n):
                for j in range(i + 1, n):
                    A = self.partition_of(sets, fvs[i])
                    B = self.partition_of(sets, fvs[j])
                    if self.equiv(fvs[i], fvs[j]) and A and B and A != B:
                        sets = self.join(sets, A, B)
                        changed = True
        self.show_classes(sets)
        return sets

    def set(self, field_value, sample, container):
        """Set a field value and all equivalent field values to the given sample and container"""
        for field_value in self.field_values():
            field_value.marked = False
        aq.algorithms.validate.mark_leaves(self)
        self.__set_aux(field_value, sample, container)
        return self

    def __set_aux(self, field_value, sample, container):
        """Auxilliary method for set"""
        if not self.equivalences:
            self.equivalences = self.classes()
        for fv in self.partition_of(self.equivalences, field_value):
            if not fv.marked:
                fv.marked = True
                fv.set_value(None, sample, container, None)
                if fv.leaf:
                    fv.choose_item()
                self.instantiate_operation(
                    fv.operation, fv.field_type.routing, sample)

    def instantiate_operation(self, operation, routing, sample):
        for ot_field_type in operation.operation_type.field_types:
            if ot_field_type.routing != routing and not ot_field_type.array:
                for st_field_type in sample.sample_type.field_types:
                    if st_field_type.ftype == 'sample' and ot_field_type.name == st_field_type.name:
                        subsample = sample.field_value(
                            st_field_type.name).sample
                        self.__set_aux(operation.field_value(
                            ot_field_type.name, ot_field_type.role), subsample, None)
