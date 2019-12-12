from collections.abc import Mapping
from collections.abc import Sequence
from typing import Callable
from typing import Generator
from typing import Generic
from typing import Iterable
from typing import List
from typing import Tuple
from typing import TypeVar
from typing import Union


IndexType = Union[Tuple[Union[int, slice], Tuple[Union[int, slice]], int, slice]]
T = TypeVar("T")


class MatrixMapping(Sequence, Generic[T]):
    """A 2D matrix that behaves like a numpy matrix more user friendly setters
    and getters."""

    def __init__(
        self,
        data: Iterable[Iterable[T]],
        setter: Callable = None,
        getter: Callable = None,
    ):
        self.data = data
        self.validate()
        self.setter = setter
        if getter is None:
            self.getter = lambda x: x
        else:
            self.getter = getter

    @property
    def dimensions(self) -> Tuple[int, int]:
        return len(self.data), len(self.data[0])

    def set_item(self, r: int, c: int, value: T):
        if self.setter is None:
            self.data[r][c] = value
        else:
            return self.setter(self.data, r, c, value)

    @staticmethod
    def _flatten(arr):
        for a in arr:
            if isinstance(a, list):
                for _a in a:
                    yield _a
            else:
                yield a

    def validate(self):
        if not self._is_rect():
            raise ValueError("Data rows have different lengths")

    def _is_rect(self):
        return len({len(d) for d in self.data}) == 1

    @property
    def _index_matrix(self):
        index_matrix = []
        for r in range(len(self.data)):
            col_indices = list(range(len(self.data[0])))
            tuples = [(r, c) for c in col_indices]
            index_matrix.append(tuples)
        return MatrixMapping(index_matrix)

    @property
    def _index_view(self):
        return self._index_matrix

    def _iter_indices(self, index: IndexType):
        indices = self._index_view[index]

        if isinstance(indices, tuple):
            indices = [[indices]]

        for rc in self._flatten(indices):
            if isinstance(rc, list):
                for r, c in rc:
                    yield r, c
            else:
                yield rc

    def iter_flatten(self) -> Generator[T, None, None]:
        for row in self.data:
            for col in row:
                yield col

    def flatten(self) -> List[T]:
        return list(self.iter_flatten())

    def __len__(self) -> int:
        return len(self.data)

    def __contains__(self, value: T) -> bool:
        for a in self.flatten():
            if a == value:
                return True
        return False

    def __iter__(self) -> Generator[T, None, None]:
        return self.data.__iter__()

    def __setitem__(self, index: IndexType, value: T):
        for r, c in self._iter_indices(index):
            self.set_item(r, c, value)

    #     def __delitem__(self, index: IndexType):
    #         for r, c in self._iter_indices(index):
    #             print(r, c)
    #             print(self.data)
    #             del self.data[r][c]

    def __getitem__(self, index: IndexType) -> Union[T, Iterable[T]]:
        if isinstance(index, slice):
            rows = self.data[index]
            return [[self.getter(d) for d in row] for row in rows]
        elif isinstance(index, tuple):
            if isinstance(index[0], slice):
                rows = self.data[index[0]]
                if isinstance(index[1], slice):
                    return [[self.getter(d) for d in row[index[1]]] for row in rows]
                return [self.getter(row[index[1]]) for row in rows]
            else:
                row = self.data[index[0]]
                if isinstance(index[1], slice):
                    return [self.getter(d) for d in row[index[1]]]
                return self.getter(row[index[1]])
        return [self.getter(d) for d in self.data[index]]

    def get(self, index: IndexType, as_mapping=False):
        if as_mapping:
            return self.__class__(self[index])
        else:
            return self[index]

    def __eq__(self, other):
        return self[:] == other[:]

    def __str__(self):
        return str(self[:])


class MatrixMappingFactory(Mapping):
    """Different ways to view the same set of data."""

    def __init__(self, data):
        self.data = data
        self.views = {}

    def new(self, name, setter: Callable = None, getter: Callable = None):
        self.views[name] = MatrixMapping(self.data, setter=setter, getter=getter)

    def __getitem__(self, key):
        return self.views[key]

    def __iter__(self):
        return self.views.__iter__()

    def __len__(self):
        return len(self.views)


# def set_part(data, r, c, value):
#     if data[r][c] is None:
#         print("NEW!")
#     if value is None:
#         print("deleting")
#
#
# from pydent.models import Collection
#
#
# def _empty(self):
#     nrows, ncols = self.dimensions
#     data = []
#     for r in range(nrows):
#         data.append([None] * ncols)
#     return data
#
#
# @property
# def part_association_matrix(self):
#     data = self._empty()
#     for assoc in self.part_associations:
#         data[assoc.row][assoc.column] = assoc
#     return data
#
#
# @property
# def part_matrix(self):
#     data = self._empty()
#     for r, row in enumerate(self.part_association_matrix):
#         for c, assoc in enumerate(row):
#             if assoc is not None:
#                 data[r][c] = assoc.part
#     return data
#
#
# @property
# def data_association_matrix(self):
#     data = self._empty()
#     for r, row in enumerate(self.part_matrix):
#         for c, assoc in enumerate(row):
#             if assoc is not None:
#                 data[r][c] = assoc.part
#     return data
#
#
# @property
# def matrix(self):
#     data = self._empty()
#     for r, row in enumerate(self.part_association_matrix):
#         for c, assoc in enumerate(row):
#             if assoc is not None:
#                 if assoc.part.sample_id:
#                     data[r][c] = assoc.part.sample_id
#                 else:
#                     data[r][c] = assoc.part.sample.id
#     return data
#
#
# @property
# def part_matrix_view(self):
#     return MatrixMapping(self.part_matrix)
#
#
# @property
# def matrix_view(self):
#     return MatrixMapping(self.matrix, setter=self._set_part)
#
#
# @property
# def part_association_matrix_view(self):
#     return MatrixMapping(self.part_association_matrix)
#
#
# def __getitem__(self, index: IndexType):
#     return self.matrix_view[index]
#
#
# def __setitem__(self, index: IndexType, value: Union[int, Sample]):
#     matrix_view = self.matrix_view[index]
#     matrix_view[index] = value
#
#
# def _set_part(self, data: List[List[int]], r: int, c: int, value: Union[int, Sample]):
#     pass
#
#
# # TODO: versionadded
# # TODO: versionchanged
# # TODO: documentation
# # TODO: better way to
# # TODO: data_association viewer
#
# Collection._empty = _empty
# Collection.part_association_matrix = part_association_matrix
# Collection.part_matrix = part_matrix
# Collection.matrix = matrix
#
# Collection.part_association_matrix_view = part_association_matrix_view
# Collection.part_matrix_view = part_matrix_view
# Collection.matrix_view = matrix_view
#
# Collection.__getitem__ = __getitem__
# Collection.__setitem__ = __setitem__
# Collection._set_part = _set_part
#
# factory = MatrixMappingFactory(collection.part_association_matrix)
#
#
# def part_getter(association):
#     if association is not None:
#         return association.part
#
#
# def value_getter(association):
#     if association is not None:
#         return association.part.sample_id or association.part.sample.id
#
#
# def data_getter(association):
#     if association is not None:
#         return association.part.data_associations
#
#
# factory.new('part', getter=part_getter)
# factory.new('matrix', getter=value_getter)
# factory.new('data', getter=data_getter)
# factory['data'][:4, :3]
#
# # del matrix[:1]
# # matrix.data
# #     def __setitem__(self, index: IndexType, value: Any):
# #         if isinstance(index, int):
# #             for i in range(self.data[index])
#
#
# # def part_association_view(self, index):
# #     associations = []
# #     for row in self.dimensions[0]:
# #         assoc_row = [None] * self.dimensions[1]
# #         for column in self.dimensions[1]:
#
#
# # def __getitem__(self, index):
# #     print(index)
# #     if isinstance(index, int) or isinstance(index, slice):
# #         return self.matrix[index]
# #     elif isinstance(index, tuple):
# #         a = self.matrix[index[0]]
# #         return [_a[index[1]] for _a in a]
# #     else:
# #         raise IndexError("Type '{}' cannot be used as an index".format(type(index)))
#
#
# # def __setitem__(self,
# #                 index: Union[Tuple[Union[int, slice], ...], int, slice],
# #                 value: Union[int, Sample]):
# #     if isinstance(index, int):
# #         p
#
#
# # from pydent.models import Collection
# # Collection.__getitem__ = __getitem__
#
# # collection[0]
