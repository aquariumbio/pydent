"""
Models related to inventory, like Items, Collections, ObjectTypes, and PartAssociations
"""

from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.models.crud_mixin import SaveMixin
from pydent.models.data_associations import DataAssociatorMixin
from pydent.relationships import Raw, HasOne, HasMany, HasManyThrough, HasManyGeneric


@add_schema
class Item(DataAssociatorMixin, SaveMixin, ModelBase):
    """
    A physical object in the lab, which a location and unique id.
    """

    fields = dict(
        sample=HasOne("Sample"),
        object_type=HasOne("ObjectType"),
        data_associations=HasManyGeneric(
            "DataAssociation", additional_args={"parent_class": "Item"}
        ),
        data=Raw(),
        ignore=("locator_id",),
        part_associations=HasMany(
            "PartAssociation", ref="part_id"
        ),  # TODO: add to change log
        collections=HasManyThrough(
            "Collection", "PartAssociation"
        ),  # TODO: add to change log
    )
    query_hook = {"methods": ["is_part"]}

    def __init__(
        self=None, sample_id=None, sample=None, object_type=None, object_type_id=None
    ):
        super().__init__(
            object_type_id=object_type_id,
            object_type=object_type,
            sample_id=sample_id,
            sample=sample,
        )

    def make(self):
        """Makes the Item on the Aquarium server. Requires
        this Item to be connected to a session."""
        result = self.session.utils.create_items([self])
        return self.reload(result[0]["item"])

    def save(self):
        """A synonym for `make`"""
        return self.make()

    def is_deleted(self):
        return self.location == "deleted"

    @property
    def containing_collection(self):
        """
        Returns the collection of which this Item is a part.

        Returns the collection object if the Item is a part, otherwise
        returns None.
        """
        if not self.is_part:
            return None

        assoc_list = self.session.PartAssociation.where({"part_id": self.id})
        if not assoc_list:
            return

        if len(assoc_list) != 1:
            return None

        part_assoc = next(iter(assoc_list))
        if not part_assoc:
            return None

        return self.session.Collection.find(part_assoc.collection_id)

    def as_collection(self):
        """
        Returns the Collection object with the ID of this Item, which must be a
        collection.

        Returns None if this Item is not a collection.
        """
        if not self.is_collection:
            return None

        return self.session.Collection.find(self.id)

    @property
    def is_collection(self):
        """
        Returns True if this Item is a collection in a PartAssociation.

        Note: this is not how Aquarium does this test in the `collection?` method.
        """
        assoc_list = self.session.PartAssociation.where({"collection_id": self.id})
        return bool(assoc_list)

    # TODO: add to change log
    @property
    def collection(self):
        return self.collections[0]

    # TODO: add to change log
    @property
    def part_association(self):
        return self.part_associations[0]


@add_schema
class Collection(
    DataAssociatorMixin, ModelBase
):  # pylint: disable=too-few-public-methods
    """A Collection model, such as a 96-well plate, which contains many `parts`, each
    of which can be associated with a different sample."""

    fields = dict(
        object_type=HasOne("ObjectType"),
        data_associations=HasManyGeneric(
            "DataAssociation", additional_args={"parent_class": "Collection"}
        ),
        part_associations=HasMany("PartAssociation", "Collection"),
        parts=HasManyThrough("Item", "PartAssociation", ref="part_id"),
    )
    query_hook = {"methods": ["dimensions"]}

    @property
    def matrix(self):
        """
        Returns the matrix of Samples for this Collection.

        (Consider using samples of parts directly.)
        """
        num_row, num_col = self.dimensions
        sample_matrix = list()
        for row in range(num_row):
            row_list = list()
            for col in range(num_col):
                sample_id = None
                part = self.part(row, col)
                if part:
                    sample_id = part.sample.id
                row_list.append(sample_id)
            sample_matrix.append(row_list)
        return sample_matrix

    def part(self, row, col):
        """
        Returns the part Item at (row, col) of this Collection (zero-based).
        """
        parts = [
            assoc.part
            for assoc in self.part_associations
            if assoc.row == row and assoc.column == col
        ]

        if not parts:
            return None

        return next(iter(parts))

    def as_item(self):
        """
        Returns the Item object with the ID of this Collection
        """
        return self.session.Item.find(self.id)

    def create(self):
        self.as_item().create()

    def update(self):
        self.as_item().update()

    def save(self):
        self.as_item().save()


@add_schema
class ObjectType(SaveMixin, ModelBase):
    """A ObjectType model that represents the type of container an item is."""

    fields = dict(items=HasMany("Item", "ObjectType"), sample_type=HasOne("SampleType"))

    def __str__(self):
        return self._to_str("id", "name")


@add_schema
class PartAssociation(ModelBase):
    """
    Represents a PartAssociation linking a part to a collection. Collections contain
    many `parts`, each of which can refer to a different sample.
    """

    fields = dict(part=HasOne("Item", ref="part_id"), collection=HasOne("Collection"))

    def __init__(self, part_id=None, collection_id=None, row=None, column=None):
        super().__init__(
            part_id=part_id, collection_id=collection_id, row=row, column=column
        )
