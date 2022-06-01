from typing import Any, MutableSequence, Optional, Sequence

from qtpy.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

from .. import ROIBase


class ROITableModel(QAbstractTableModel):
    def __init__(
        self, rois: MutableSequence[ROIBase], parent: Optional[QObject] = None
    ) -> None:
        super(ROITableModel, self).__init__(parent=parent)
        self._rois = rois

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rois)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return 5

    def data(
        self,
        index: QModelIndex,
        role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if 0 <= index.row() < self.rowCount() and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
        ):
            if index.column() == 0:
                return self._rois[index.row()].name
            if index.column() == 1:
                return self._rois[index.row()].x
            if index.column() == 2:
                return self._rois[index.row()].y
            if index.column() == 3:
                return self._rois[index.row()].width
            if index.column() == 4:
                return self._rois[index.row()].height
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return ("name", "x", "y", "width", "height")[section]
        return None

    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: Qt.ItemDataRole = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if 0 <= index.row() < self.rowCount() and role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                str_value = str(value).strip()
                if len(str_value) > 0 and not any(
                    roi.name == str_value and i != index.row()
                    for i, roi in enumerate(self._rois)
                ):
                    self._rois[index.row()].name = str_value
                else:
                    return False
            elif index.column() == 1:
                try:
                    self._rois[index.row()].x = float(value)
                except ValueError:
                    return False
            elif index.column() == 2:
                try:
                    self._rois[index.row()].y = float(value)
                except ValueError:
                    return False
            elif index.column() == 3:
                try:
                    float_value = float(value)
                except ValueError:
                    return False
                if float_value > 0:
                    self._rois[index.row()].width = float_value
                else:
                    return False
            elif index.column() == 4:
                try:
                    float_value = float(value)
                except ValueError:
                    return False
                if float_value > 0:
                    self._rois[index.row()].height = float_value
                else:
                    return False
            self.dataChanged.emit(
                self.createIndex(index.row(), index.column()),
                self.createIndex(index.row(), index.column()),
                [Qt.ItemDataRole.EditRole],
            )
            return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if (
            0 <= index.row() < self.rowCount()
            and 0 <= index.column() < self.columnCount()
        ):
            return (
                Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemNeverHasChildren
            )
        return Qt.ItemFlag.NoItemFlags

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if 0 <= row <= self.rowCount() and count > 0 and not parent.isValid():
            self.beginInsertRows(parent, row, row + count - 1)
            for i in range(row, row + count):
                self._rois.insert(i, ROIBase())
            self.endInsertRows()
            return True
        return False

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if 0 <= row < row + count <= self.rowCount() and not parent.isValid():
            self.beginRemoveRows(parent, row, row + count - 1)
            for i in range(row, row + count):
                del self._rois[row]
            self.endRemoveRows()
            return True
        return False

    def refresh_rows(self, row_indices: Sequence[int]) -> None:
        for row_index in row_indices:
            self.dataChanged.emit(
                self.createIndex(row_index, 0),
                self.createIndex(row_index, self.columnCount() - 1),
                [Qt.ItemDataRole.DisplayRole],
            )

    def reset(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    @property
    def rois(self) -> MutableSequence[ROIBase]:
        return self._rois
