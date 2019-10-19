"""Models related to protocol code, which is associated with operation
types."""
from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.relationships import HasManyGeneric
from pydent.relationships import HasOne
from pydent.relationships import HasOneFromMany
from pydent.relationships import One


@add_schema
class Code(ModelBase):
    """A Code model."""

    fields = dict(
        user=HasOne("User"),
        operation_type=One("OperationType", callback="get_parent", callback_args=None),
        library=One("Library", callback="get_parent", callback_args=None),
    )

    def get_parent(self, parent_class, *args):
        if parent_class != self.parent_class:
            return None
        return self.session.model_interface(self.parent_class).find(self.parent_id)

    def update(self):
        # since they may not always be tied to specific parent
        # controllers
        self.session.utils.update_code(self)


@add_schema
class Library(ModelBase):
    """A Library model."""

    fields = dict(
        codes=HasManyGeneric("Code"),
        source=HasOneFromMany(
            "Code",
            ref="parent_id",
            additional_args={"parent_class": "Library", "name": "source"},
        ),
    )

    def code(self, accessor):
        """Reminant from previous API."""
        # raise DeprecationWarning("This method is depreciated. Use '.source' directly")
        if accessor == "source":
            return self.source
        return None
