from os import PathLike
from pathlib import Path
from qtpy.QtWidgets import QFileDialog, QLineEdit, QStyle, QWidget
from typing import Optional, Union


class FileLineEdit(QLineEdit):
    def __init__(
        self,
        caption: Optional[str] = None,
        filter: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super(FileLineEdit, self).__init__(parent=parent)
        self.file_dialog = QFileDialog(
            parent=self, caption=caption, filter=filter
        )
        self.file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
        self.browse_action = self.addAction(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogOpenButton
            ),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.browse_action.triggered.connect(self.on_browse_action_triggered)

    def on_browse_action_triggered(self, checked: bool = False):
        if self.path is not None:
            if self.path.parent.is_dir():
                self.file_dialog.setDirectory(str(self.path.parent))
            if self.path.exists():
                self.file_dialog.selectFile(str(self.path))
        if self.file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = self.file_dialog.selectedFiles()
            self.setText(selected_files[0])

    @property
    def path(self) -> Optional[Path]:
        return Path(self.text()) if self.text() else None

    @path.setter
    def path(self, path: Union[str, PathLike]):
        self.setText(str(path) if path is not None else "")
