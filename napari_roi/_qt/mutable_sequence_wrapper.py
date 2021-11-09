from collections.abc import MutableSequence
from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt
from typing import TypeVar

T = TypeVar("T")


class MutableSequenceWrapper(MutableSequence[T]):
    def __init__(self, data: MutableSequence[T], model: QAbstractItemModel):
        self.data = data
        self.model = model

    def __getitem__(self, index: int) -> T:
        return self.data[index]

    def __setitem__(self, index: int, item: T):
        self.data[index] = item
        self.model.dataChanged.emit(
            self.model.createIndex(index, 0),
            self.model.createIndex(index, self.model.columnCount() - 1),
            [Qt.ItemDataRole.EditRole],
        )

    def __delitem__(self, index: int):
        self.model.beginRemoveRows(QModelIndex(), index, index)
        del self.data[index]
        self.model.endRemoveRows()

    def __len__(self):
        return len(self.data)

    def insert(self, index: int, item: T):
        self.model.beginInsertRows(QModelIndex(), index, index)
        self.data.insert(index, item)
        self.model.endInsertRows()
