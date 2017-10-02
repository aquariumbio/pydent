import aq

_plan = None

def equiv(a,b):
    if a.operation == b.operation and a.field_type.routing == b.field_type.routing:
        return True
    for wire in _plan.wires:
        if ( wire.source == a and wire.destination == b ) or \
           ( wire.source == b and wire.destination == a ):
           return True
    return False

def partition_of(sets,a):
    for s in sets:
        if a in s:
            return s
    return None

def join(sets,A,B):
    sets.remove(A)
    sets.remove(B)
    sets.append(A+B)
    return sets

def show(sets):
    for s in sets:
        print([fv.rid for fv in s])

def classes(plan):
    global _plan
    _plan = plan
    fvs = _plan.field_values()
    n = len(fvs)
    sets = [ [fv] for fv in fvs ]
    for i in range(n):
        for j in range(i+1,n):
            A = partition_of(sets,fvs[i])
            B = partition_of(sets,fvs[j])
            if equiv(fvs[i], fvs[j]) and A and B and not A == B:
                print("equiv")
                sets = join(sets,A,B)
    # show(sets)
    return sets
