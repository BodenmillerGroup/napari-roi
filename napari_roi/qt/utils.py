from collections.abc import MutableSequence
from typing import TypeVar

from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt

T = TypeVar("T")


class MutableItemModelSequenceWrapper(MutableSequence[T]):
    def __init__(self, data: MutableSequence[T], model: QAbstractItemModel) -> None:
        self._data = data
        self._model = model

    def __getitem__(self, index: int) -> T:
        return self._data[index]

    def __setitem__(self, index: int, item: T) -> None:
        self._data[index] = item
        self._model.dataChanged.emit(
            self._model.createIndex(index, 0),
            self._model.createIndex(index, self._model.columnCount() - 1),
            [Qt.ItemDataRole.EditRole],
        )

    def __delitem__(self, index: int) -> None:
        self._model.beginRemoveRows(QModelIndex(), index, index)
        del self._data[index]
        self._model.endRemoveRows()

    def __len__(self) -> int:
        return len(self._data)

    def insert(self, index: int, item: T) -> None:
        self._model.beginInsertRows(QModelIndex(), index, index)
        self._data.insert(index, item)
        self._model.endInsertRows()

    @property
    def data(self) -> MutableSequence[T]:
        return self._data

    @property
    def model(self) -> QAbstractItemModel:
        return self._model
