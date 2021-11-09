from qtpy.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt
from typing import Any, MutableSequence, Optional

from napari_roi._roi import ROIBase


class ROITableModel(QAbstractTableModel):
    def __init__(
        self, rois: MutableSequence[ROIBase], parent: Optional[QObject] = None
    ):
        super(ROITableModel, self).__init__(parent=parent)
        self.rois = rois

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.rois)

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
                return self.rois[index.row()].name
            if index.column() == 1:
                return self.rois[index.row()].x
            if index.column() == 2:
                return self.rois[index.row()].y
            if index.column() == 3:
                return self.rois[index.row()].width
            if index.column() == 4:
                return self.rois[index.row()].height
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
        if (
            0 <= index.row() < self.rowCount()
            and role == Qt.ItemDataRole.EditRole
        ):
            if index.column() == 0:
                self.rois[index.row()].name = str(value)
            elif index.column() == 1:
                try:
                    self.rois[index.row()].x = float(value)
                except ValueError:
                    return False
            elif index.column() == 2:
                try:
                    self.rois[index.row()].y = float(value)
                except ValueError:
                    return False
            elif index.column() == 3:
                try:
                    float_value = float(value)
                except ValueError:
                    return False
                if float_value > 0:
                    self.rois[index.row()].width = float_value
                else:
                    return False
            elif index.column() == 4:
                try:
                    float_value = float(value)
                except ValueError:
                    return False
                if float_value > 0:
                    self.rois[index.row()].height = float_value
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
                self.rois.insert(i, ROIBase())
            self.endInsertRows()
            return True
        return False

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if 0 <= row < row + count <= self.rowCount() and not parent.isValid():
            self.beginRemoveRows(parent, row, row + count - 1)
            for i in range(row, row + count):
                del self.rois[row]
            self.endRemoveRows()
            return True
        return False

    def reset(self):
        self.beginResetModel()
        self.endResetModel()
