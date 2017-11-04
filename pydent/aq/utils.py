"""Useful methods that don't fit anywhere else go here"""

import re

class TridentUtilities:

    """Useful methods that don't fit anywhere else go in this class"""    

    def snake(self, name):
        """Turn a camel case name into a snake case name"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def is_record(self, object):
        """Determine if an object is a record:"""
        bases = object.__class__.__bases__
        return len(bases) == 1 and bases[0].__name__ == 'Record'

utils = TridentUtilities()
