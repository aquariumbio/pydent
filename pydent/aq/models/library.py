"""Libraries"""

import aq


class LibraryRecord(aq.Record):

    """LibraryRecord defines a code library that can be included in
    protocol code
    """

    def __init__(self, model, data):
        """Make a new LibraryRecord"""
        super(LibraryRecord, self).__init__(model, data)
        self.has_many("operations", aq.Operation)
        self.has_many_generic("field_types", aq.FieldType)
        self.has_many_generic("codes", aq.Code)

    def code(self):
        """Get the code named 'name' associated with the library"""
        if len(self.codes) > 0:
            return self.codes[len(self.codes) - 1]
        else:
            return None


class LibraryModel(aq.Base):

    """LibraryModel class, generates LibraryRecords"""

    def __init__(self):
        """Make a new LibraryModel"""
        super(LibraryModel, self).__init__("Library")


Library = LibraryModel()
