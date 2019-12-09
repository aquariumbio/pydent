"""Models related to inventory, like Items, Collections, ObjectTypes, and
PartAssociations."""
from typing import Any
from typing import List
from typing import Tuple
from typing import Union

from .data_associations import DataAssociation
from .sample import Sample
from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.models.controller_mixin import ControllerMixin
from pydent.models.crud_mixin import JSONSaveMixin
from pydent.models.crud_mixin import SaveMixin
from pydent.models.data_associations import DataAssociatorMixin
from pydent.relationships import HasMany
from pydent.relationships import HasManyGeneric
from pydent.relationships import HasManyThrough
from pydent.relationships import HasOne
from pydent.relationships import Raw
from pydent.utils.matrix_mapper import IndexType
from pydent.utils.matrix_mapper import MatrixMapping
from pydent.utils.matrix_mapper import MatrixMappingFactory


@add_schema
class ObjectType(SaveMixin, ModelBase):
    """A ObjectType model that represents the type of container an item is."""

    fields = dict(items=HasMany("Item", "ObjectType"), sample_type=HasOne("SampleType"))

    def __str__(self):
        return self._to_str("id", "name")


@add_schema
class Item(DataAssociatorMixin, SaveMixin, ModelBase):
    """A physical object in the lab, which a location and unique id."""

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
        """Makes the Item on the Aquarium server.

        Requires this Item to be connected to a session.
        """
        result = self.session.utils.create_items([self])
        return self.reload(result[0]["item"])

    def save(self):
        """A synonym for `make`"""
        return self.make()

    def is_deleted(self):
        return self.location == "deleted"

    @property
    def containing_collection(self):
        """Returns the collection of which this Item is a part.

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
        """Returns the Collection object with the ID of this Item, which must
        be a collection.

        Returns None if this Item is not a collection.
        """
        if not self.is_collection:
            return None

        return self.session.Collection.find(self.id)

    @property
    def is_collection(self):
        """Returns True if this Item is a collection in a PartAssociation.

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
class PartAssociation(JSONSaveMixin, ModelBase):
    """Represents a PartAssociation linking a part to a collection.

    Collections contain many `parts`, each of which can refer to a
    different sample.
    """

    fields = dict(part=HasOne("Item", ref="part_id"), collection=HasOne("Collection"))

    def __init__(self, part_id=None, collection_id=None, row=None, column=None):
        super().__init__(
            part_id=part_id, collection_id=collection_id, row=row, column=column
        )


@add_schema
class Collection(
    DataAssociatorMixin, SaveMixin, ControllerMixin, ModelBase
):  # pylint: disable=too-few-public-methods
    """A Collection model, such as a 96-well plate, which contains many
    `parts`, each of which can be associated with a different sample."""

    fields = dict(
        object_type=HasOne("ObjectType"),
        data_associations=HasManyGeneric(
            "DataAssociation", additional_args={"parent_class": "Collection"}
        ),
        part_associations=HasMany("PartAssociation", "Collection"),
        parts=HasManyThrough("Item", "PartAssociation", ref="part_id"),
    )
    query_hook = {"methods": ["dimensions"]}

    # TODO: validate dimensions is returning the same dimensions as that in the object_type
    # TODO: init should establish dimensions

    def __init__(
        self,
        object_type: ObjectType = None,
        location: str = None,
        data_associations: List = None,
        parts: List = None,
        part_associations: List = None,
        **kwargs,
    ):
        if isinstance(object_type, ObjectType):
            object_type = object_type
            object_type_id = object_type.id
            dims = object_type.rows, object_type.columns
        else:
            object_type_id = None
            dims = None

        super().__init__(
            object_type=object_type,
            object_type_id=object_type_id,
            location=location,
            dimensions=dims,
            data_associations=data_associations,
            part_associations=part_associations,
            parts=parts,
            **kwargs,
        )

        print(self)

        if self.part_associations is None:
            self.part_associations = []
        if self.data_associations is None:
            self.data_associations = []

    def _empty(self):
        nrows, ncols = self.dimensions
        data = []
        for r in range(nrows):
            data.append([None] * ncols)
        return data

    def __part_association_matrix(self):
        data = self._empty()
        if self.part_associations:
            for assoc in self.part_associations:
                data[assoc.row][assoc.column] = assoc
        return data

    @staticmethod
    def _get_part(assoc):
        if assoc is not None:
            return assoc.part

    @staticmethod
    def _get_sample_id(assoc):
        if assoc is not None:
            if assoc.part:
                return assoc.part.sample_id or assoc.part.sample.id

    @staticmethod
    def _get_sample(assoc):
        if assoc is not None:
            if assoc.part:
                return assoc.part.sample

    @staticmethod
    def _get_data_association(assoc):
        if assoc is not None:
            if assoc.part:
                if assoc.data_associations:
                    return {a.key: a for a in assoc.part.data_associations}
                else:
                    return {}

    @staticmethod
    def _get_data_value(assoc):
        if assoc is not None:
            if assoc.part:
                if assoc.data_associations:
                    return {a.key: a.value for a in assoc.part.data_associations}
                else:
                    return {}

    @staticmethod
    def _no_setter(x):
        raise ValueError("Setter is not implemented.")

    def _set_sample_id(
        self,
        data: List[List[PartAssociation]],
        r: int,
        c: int,
        sample: Union[int, Sample],
    ):
        if data[r][c]:
            part = data[r][c].part
        else:
            part = self.session.Item.new(
                object_type_id=self.session.ObjectType.find_by_name("__Part").id
            )
            association = self.session.PartAssociation.new(
                part_id=part.id, collection_id=self.id, row=r, column=c
            )
            association.part = part
            self.append_to_many("part_associations", association)
        if isinstance(sample, int):
            part.sample_id = sample
            part.reset_field("sample")
        elif isinstance(sample, Sample):
            part.sample = sample
            part.sample_id = sample.id
        else:
            raise ValueError("{} must be a Sample instance".format(sample))

    @property
    def _mapping(self):
        factory = MatrixMappingFactory(self.__part_association_matrix())
        default_setter = self._no_setter
        factory.new("part_association", setter=default_setter, getter=None)
        factory.new("part", setter=default_setter, getter=self._get_part)
        factory.new("sample_id", setter=self._set_sample_id, getter=self._get_sample_id)
        factory.new("sample", setter=default_setter, getter=self._get_sample)
        factory.new("data", setter=default_setter, getter=self._get_data_value)
        factory.new(
            "data_association", setter=default_setter, getter=self._get_data_association
        )
        return factory

    @property
    def matrix(self):
        """Returns the matrix of Samples for this Collection.

        (Consider using samples of parts directly.)
        """
        return self.sample_id_matrix

    @property
    def parts_matrix(self) -> MatrixMapping[Item]:
        return self._mapping["part"]

    @property
    def part_association_matrix(self) -> MatrixMapping[PartAssociation]:
        return self._mapping["part_association"]

    @property
    def sample_id_matrix(self) -> MatrixMapping[int]:
        return self._mapping["sample_id"]

    @property
    def sample_matrix(self) -> MatrixMapping[Sample]:
        return self._mapping["sample"]

    @property
    def data_matrix(self) -> MatrixMapping[Any]:
        return self._mapping["data"]

    @property
    def data_association_matrix(self) -> MatrixMapping[DataAssociation]:
        return self._mapping["data_association"]

    def part(self, row, col) -> Item:
        """Returns the part Item at (row, col) of this Collection (zero-
        based)."""
        return self.parts_matrix[row, col]

    def as_item(self):
        """Returns the Item object with the ID of this Collection."""
        return self.session.Item.find(self.id)

    # TODO: implement save and create
    def create(self):
        """Create a new empty collection on the server."""
        result = self.session.utils.model_update(
            "collections", self.object_type_id, self.dump()
        )
        self.reload(result)
        self.id = result["id"]
        for association in self.part_associations:
            if not association.collection_id:
                association.collection_id = self.id
            association.part.save()
            association.part_id = association.part.id
            association.save()
        self.refresh()

    def update(self):
        result = self.session.utils.model_update(
            "collections", self.object_type_id, self.dump()
        )
        self.id = result["id"]
        for association in self.part_associations:
            if not association.collection_id:
                association.collection_id = self.id
            association.part.save()
            association.part_id = association.part.id
            association.save()
        self.refresh()

    def assign_sample(self, sample_id: int, pairs: List[Tuple[int, int]]):
        """Assign sample id to the (row, column) pairs for the collection.

        :param sample_id: the sample id to assign
        :param pairs: list of (row, column) tuples
        :return: self
        """
        self.controller_method(
            "assign_sample",
            self.get_tableized_name(),
            self.id,
            data={"sample_id": sample_id, "pairs": pairs},
        )
        self.refresh()
        return self

    def remove_sample(self, pairs: List[Tuple[int, int]]):
        """Clear the sample_id assigment in the (row, column) pairs for the
        collection.

        :param pairs: list of (row, column) tuples
        :return: self
        """
        self.controller_method(
            "delete_selection",
            self.get_tableized_name(),
            self.id,
            data={"pairs": pairs},
        )
        self.refresh()
        return self

    def __getitem__(self, index: IndexType) -> Union[int, List[int], List[List[int]]]:
        return self.matrix[index]

    def __setitem__(self, index: IndexType, sample: Union[int, Sample]):
        self.sample_id_matrix[index] = sample

    # TODO: add data associations to matrix
    # TODO: collections test
    # def update(self):
    #     self.as_item().update()
    #
    # def save(self):
    #     self.as_item().save()
