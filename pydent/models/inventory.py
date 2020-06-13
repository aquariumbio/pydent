"""Models related to inventory, like Items, Collections, ObjectTypes, and
PartAssociations."""
from abc import abstractmethod
from typing import Any
from typing import Dict
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
from pydent.models.data_associations import DataAssociationSaveContext
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

    def new_item(self, sample: Union[int, Sample]):
        """Create a new item.

        .. versionadded:: 0.1.5a13

        :param sample: the sample id
        :return: the new item
        """
        if isinstance(sample, int):
            sample_id = sample
            sample = self.session.Sample.find(sample_id)
        elif isinstance(sample, Sample):
            sample_id = sample.id
        else:
            raise TypeError(
                "Sample must be either a sample_id (int) or a" " Sample instance."
            )
        return self.session.Item.new(
            sample=sample, sample_id=sample_id, object_type=self, object_type_id=self.id
        )


class ItemLocationMixin(SaveMixin, JSONSaveMixin):
    def move(self, new_location):
        self.session.utils.move_item(self, new_location)

    def store(self):
        self.session.utils.store_item(self)

    def _get_save_json(self):
        data = self.dump()
        if "location" in data:
            del data["location"]
        return data

    def update(self):
        """Updates the item.

        Will update the data associations and its location.
        """
        to_location = self.location
        JSONSaveMixin.save(self, do_reload=True)
        if to_location and to_location != self.location:
            self.move(self.location)
        return self

    def delete(self):
        raise ValueError
        self.move("deleted")

    def mark_as_deleted(self):
        self.location = "deleted"

    def is_deleted(self):
        return self.location == "deleted"

    @abstractmethod
    def create(self):
        pass

    def make(self):
        """Makes the Item on the Aquarium server.

        Requires this Item to be connected to a session.
        """
        if not self.DID_ITEM_WARNING:
            raise DeprecationWarning("This method is depreciated. Use `save()`")
        self.DID_ITEM_WARNING = True
        self.create()


@add_schema
class Item(DataAssociatorMixin, ItemLocationMixin, ModelBase):
    """A physical object in the lab, which a location and unique id."""

    DID_ITEM_WARNING = False

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
        self=None,
        sample_id=None,
        sample=None,
        object_type=None,
        object_type_id=None,
        location=None,
    ):
        if sample_id is None:
            if sample and sample.id:
                sample_id = sample.id

        if object_type_id is None:
            if object_type and object_type.id:
                object_type_id = object_type.id
        super().__init__(
            object_type_id=object_type_id,
            object_type=object_type,
            sample_id=sample_id,
            sample=sample,
            location=location,
        )

    def create(self):
        with DataAssociationSaveContext(self):
            result = self.session.utils.create_items([self])
            self.reload(result[0]["item"])
        return self

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

    def get_sample_id(self) -> Union[None, int]:
        if self.sample_id:
            return self.sample_id
        return self.sample.id

    def has_unsaved_sample(self) -> bool:
        if self.is_deserialized("part") and self.part.is_deserialized("sample"):
            if self.part.sample.id is None:
                return True
        return False

    def is_empty(self) -> bool:
        if self.get_sample_id():
            return True
        return False


@add_schema
class Collection(
    ItemLocationMixin, DataAssociatorMixin, SaveMixin, ControllerMixin, ModelBase
):
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
        """Initialize a new Collection.

        .. versionchanged:: 0.1.5a10
            Advanced indexing added for setting and getting samples and data associations

        **Setting samples using new advanced indexing**

        .. code-block:: python

            object_type = session.ObjectType.one(query='rows > 2 AND columns > 2')
            collection = session.Collection.new(object_type=object_type)

            # assign sample '1' to (0, 0) row=0, column=0
            collection[0, 0] = 1

            # assign sample '2' to (1, 2) row=1, column=2
            collection[1, 2] = 2

            # assign sample '3234' to row 3
            collection[3] = 3234

            # assign sample '444' to column 1
            collection[:, 1] = 444

            # assign sample '6' to the whole collection
            collection[:, :] = 6

            # assign sample using Sample instance
            collection[2, 2] = session.Sample.one()

        **Getting samples using new advanced indexing**

        .. code-block:: python

            # get 2d matrix of sample ids
            print(collection.matrix)  # or collection.sample_id_matrix

            # get 2d matrix of Samples assigned at each location
            print(collection.sample_matrix)

            # get 2d matrix of Parts assigned at each location
            print(collection.part_matrix)

            # get 2d matrix of PartAssociations assigned at each location
            collection.part_associations_matrix

            # get 2d matrix of values of DataAssociations at each location
            collection.data_matrix

            # get 2d matrix of DataAssociations at each location
            collection.data_association_matrix

        **Assigning data to locations**

        To assign data, you can use the advanced indexing on the `data_matrix`

        .. code-block:: python

            collection.data_matrix[0, 0] = {'key': 'value'}

            collection.data_matrix[1] = {'key': 'value2'}

            collection.associate_to('key', 'value3', 3, 3)

        You can delete associations using the following:

        .. code-block:: python

            # delete 3, 3
            collection.delete_association_at('key', 3, 3)

            # delete first three rows at column 3
            collection.delete_association_at('key', slice(None, 3, None), 3)

            # delete all of the 'key' associations
            collection.delete_association_at('key', slice(None, None, None), slice(None, None, None))


        :param object_type:
        :param location:
        :param data_associations:
        :param parts:
        :param part_associations:
        :param kwargs:
        """
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
                if assoc.part.sample_id:
                    return assoc.part.sample_id
                elif assoc.part.sample:
                    return assoc.part.sample.id
                return None

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
                if assoc.part.data_associations:
                    return {a.key: a.value for a in assoc.part.data_associations}
                else:
                    return {}

    @staticmethod
    def _no_setter(x):
        raise ValueError("Setter is not implemented.")

    def _set_sample(
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
        elif sample is None:
            part.sample = None
            part.sample_id = None
        else:
            raise ValueError("{} must be a Sample instance or an int".format(sample))

    def _set_key_values(
        self,
        data: List[List[PartAssociation]],
        r: int,
        c: int,
        data_dict: Dict[str, Any],
    ):
        part = None
        if data[r][c]:
            part = data[r][c].part

        if not part:
            raise ValueError(
                "Cannot set data to ({r},{c}) because "
                "there is no Sample assigned to that location".format(r=r, c=c)
            )
        for k, v in data_dict.items():
            part.associate(k, v)

    @property
    def _mapping(self):
        factory = MatrixMappingFactory(self.__part_association_matrix())
        default_setter = self._no_setter
        factory.new("part_association", setter=default_setter, getter=None)
        factory.new("part", setter=default_setter, getter=self._get_part)
        factory.new("sample_id", setter=self._set_sample, getter=self._get_sample_id)
        factory.new("sample", setter=default_setter, getter=self._get_sample)
        factory.new("data", setter=self._set_key_values, getter=self._get_data_value)
        factory.new(
            "data_association", setter=default_setter, getter=self._get_data_association
        )
        return factory

    @property
    def matrix(self):
        """Returns the matrix of Samples for this Collection.

        (Consider using samples of parts directly.)

        .. versionchanged:: 0.1.5a9
            Refactored using MatrixMapping
        """
        return self.sample_id_matrix

    @property
    def part_matrix(self) -> MatrixMapping[Item]:
        """Return a view of :class:`Item <pydent.models.Item>`

        .. versionadded:: 0.1.5a9

        :return: collection as a view of Items (Parts)
        """
        return self._mapping["part"]

    @property
    def part_association_matrix(self) -> MatrixMapping[PartAssociation]:
        """Return a view of part associations.

        .. versionadded:: 0.1.5a9

        :return: collection as a view of PartAssociations
        """
        return self._mapping["part_association"]

    @property
    def sample_id_matrix(self) -> MatrixMapping[int]:
        """Return a view of sample_ids :class:`Sample<pydent.models.Sample>`

        .. versionadded:: 0.1.5a9

        :return: collection as a view of Sample.ids
        """
        return self._mapping["sample_id"]

    @property
    def sample_matrix(self) -> MatrixMapping[Sample]:
        """Return a view of :class:`Sample<pydent.models.Sample>`

        .. versionadded:: 0.1.5a9

        :return: collection as a view of Samples
        """
        return self._mapping["sample"]

    @property
    def data_matrix(self) -> MatrixMapping[Any]:
        """Return a view of values from the.

        :class:`DataAssociation<pydent.models.DataAssociation>`

        .. versionadded:: 0.1.5a9

        :return: collection as a view of DataAssociation values
        """
        return self._mapping["data"]

    @property
    def data_association_matrix(self) -> MatrixMapping[DataAssociation]:
        """Return a view of.

        :class:`DataAssociation<pydent.models.DataAssociation>`

        .. versionadded:: 0.1.5a9

        :return: collection as a view of DataAssociations
        """
        return self._mapping["data_association"]

    def part(self, row, col) -> Item:
        """Returns the part Item at (row, col) of this Collection (zero-
        based)."""
        return self.part_matrix[row, col]

    def as_item(self):
        """Returns the Item object with the ID of this Collection."""
        return self.session.Item.find(self.id)

    # TODO: implement save and create
    def create(self):
        """Create a new empty collection on the server."""
        result = self.session.utils.model_update(
            "collections", self.object_type_id, self.dump()
        )
        self.id = result["id"]
        self.created_at = result["created_at"]
        self.updated_at = result["updated_at"]
        self.update()
        return self

    def _validate_for_update(self):
        if not self.id:
            raise ValueError(
                "Cannot update part associations since the Collection " "is not saved."
            )
        for association in self.part_associations:
            if association.has_unsaved_sample():
                raise ValueError(
                    "Cannot update. Collection contains Samples ({r},{c})"
                    " that have not yet been saved.".format(
                        r=association.row, c=association.column
                    )
                )

    def update(self):
        self._validate_for_update()
        self.move(self.location)
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

    def associate_to(self, key, value, r: int, c: int):
        self.data_matrix[r, c] = {key: value}

    def delete_association_at(self, key, r: int, c: int):
        part_matrix = self.part_matrix
        for r, c in part_matrix._iter_indices((r, c)):
            part = part_matrix[r, c]
            part.delete_data_associations(key)

    def __getitem__(self, index: IndexType) -> Union[int, List[int], List[List[int]]]:
        """Returns the sample_id of the part at the provided index.

        :param index: either an int (for rows), tuple of ints/slice objs, (row, column),
            or a slice object.
        :return: sample_ids
        """
        return self.matrix[index]

    def __setitem__(self, index: IndexType, sample: Union[int, Sample]):
        """Sets the sample_ids of the collection, creating the PartAssociations
        and parts if needed.

        :param index: either an int (for rows), tuple of ints/slice objs, (row, column),
            or a slice object.
        :param sample: either a Sample with a valid id or sample_id
        :return:
        """
        self.sample_id_matrix[index] = sample

    # TODO: add data associations to matrix
    # TODO: collections test
    # def update(self):
    #     self.as_item().update()
    #
    # def save(self):
    #     self.as_item().save()
