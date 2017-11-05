"""Useful methods that don't fit anywhere else go here"""

import re

def snake(name):
    """Turn a camel case name into a snake case name"""
    temp = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', temp).lower()

def is_record(obj):
    """Determine if an object is a record:"""
    bases = obj.__class__.__bases__
    return len(bases) == 1 and bases[0].__name__ == 'Record'
