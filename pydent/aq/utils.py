import re


class TridentUtilities:

    def snake(self, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def is_record(self, object):
        bases = object.__class__.__bases__
        return len(bases) == 1 and bases[0].__name__ == 'Record'


utils = TridentUtilities()
