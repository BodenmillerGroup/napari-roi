import pandas as pd

from napari.layers import Shapes
from napari.utils.events import Event
from napari.viewer import Viewer
from pathlib import Path
from qtpy.QtCore import QEvent, QItemSelection, QObject, QPoint, Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHeaderView,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableView,
    QWidget,
)
from typing import MutableSequence, Optional, Sequence
from vispy.app.canvas import MouseEvent

from napari_roi._roi import ROI, ROIBase, ROIOrigin
from napari_roi._qt import (
    MutableSequenceWrapper,
    ROILayerAccessor,
    ROITableModel,
)


class ROIWidget(QWidget):
    DEFAULT_COLUMN_WIDTHS = (120, 80, 80, 80, 80)
    ROI_LAYER_TEXT_COLOR = "red"

    def __init__(self, viewer: Viewer):
        super(ROIWidget, self).__init__(parent=viewer.window.qt_viewer)
        self._viewer = viewer
        self._roi_layer: Optional[Shapes] = None
        self._roi_layer_accessor: Optional[ROILayerAccessor] = None
        self._roi_table_model: Optional[ROITableModel] = None

        self.setMinimumHeight(200)
        self.setLayout(QGridLayout())

        self._add_widget = QWidget(parent=self)
        self._add_widget.setLayout(QFormLayout())
        self._add_widget.layout().setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        self._new_roi_name_edit = QLineEdit(parent=self._add_widget)
        self._new_roi_name_edit.textChanged.connect(
            self._on_new_roi_name_edit_text_changed
        )
        self._add_widget.layout().addRow("Name:", self._new_roi_name_edit)
        self._new_roi_width_spinbox = QDoubleSpinBox(parent=self._add_widget)
        self._new_roi_width_spinbox.setRange(0.0, float("inf"))
        self._new_roi_width_spinbox.valueChanged.connect(
            self._on_new_roi_width_spinbox_value_changed
        )
        self._add_widget.layout().addRow("Width:", self._new_roi_width_spinbox)
        self._new_roi_height_spinbox = QDoubleSpinBox(parent=self._add_widget)
        self._new_roi_height_spinbox.setRange(0.0, float("inf"))
        self._new_roi_height_spinbox.valueChanged.connect(
            self._on_new_roi_height_spinbox_value_changed
        )
        self._add_widget.layout().addRow(
            "Height:", self._new_roi_height_spinbox
        )
        self._add_roi_button = QPushButton("Add ROI", parent=self._add_widget)
        self._add_roi_button.clicked.connect(self._on_add_roi_button_clicked)
        self._add_widget.layout().addRow(self._add_roi_button)

        self._roi_table_widget = QWidget(parent=self)
        self._roi_table_widget.setLayout(QFormLayout())
        self._add_widget.layout().setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self._roi_table_view = QTableView(parent=self._roi_table_widget)
        self._roi_table_view.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self._roi_table_view.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._roi_table_view.customContextMenuRequested.connect(
            self._on_roi_table_view_context_menu_requested
        )
        self._roi_table_widget.layout().addRow(self._roi_table_view)
        self._roi_origin_combobox = QComboBox(parent=self._roi_table_widget)
        self._roi_origin_combobox.setFixedWidth(200)
        self._roi_origin_combobox.addItems(
            (
                str(ROIOrigin.TOP_LEFT),
                str(ROIOrigin.TOP_RIGHT),
                str(ROIOrigin.BOTTOM_LEFT),
                str(ROIOrigin.BOTTOM_RIGHT),
            )
        )
        self._roi_origin_combobox.currentTextChanged.connect(
            self._on_roi_origin_combobox_current_text_changed
        )
        self._roi_table_widget.layout().addRow(
            "X/Y origin:", self._roi_origin_combobox
        )

        self._save_widget = QWidget(parent=self)
        self._save_widget.setLayout(QGridLayout())
        self._roi_file_edit = QLineEdit(parent=self)
        self._roi_file_edit.setReadOnly(True)
        self._roi_file_edit.addAction(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogOpenButton
            ),
            QLineEdit.ActionPosition.TrailingPosition,
        ).triggered.connect(self._on_save_file_edit_browse_action_triggered)
        self._save_widget.layout().addWidget(self._roi_file_edit, 0, 0, 1, 2)
        self._autosave_checkbox = QCheckBox(
            "Autosave", parent=self._save_widget
        )
        self._autosave_checkbox.stateChanged.connect(
            self._on_autosave_checkbox_state_changed
        )
        self._save_widget.layout().addWidget(
            self._autosave_checkbox, 1, 0, 1, 1
        )
        self._save_button = QPushButton(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogSaveButton
            ),
            "Save",
            parent=self._save_widget,
        )
        self._save_button.clicked.connect(self._on_save_button_clicked)
        self._save_widget.layout().addWidget(self._save_button, 1, 1, 1, 1)

        self._update_layout(False)
        if isinstance(self._viewer.layers.selection.active, Shapes):
            self._roi_layer = self._viewer.layers.selection.active
        self._on_roi_layer_changed(None)
        self._viewer.layers.selection.events.active.connect(
            self._on_active_viewer_layer_changed
        )
        self.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.Type.ParentChange:
            if isinstance(self.parent(), QDockWidget):
                self.parent().dockLocationChanged.connect(
                    self._on_dock_location_changed
                )
        return super(ROIWidget, self).eventFilter(obj, event)

    def _on_dock_location_changed(self, area: Qt.DockWidgetArea):
        horizontal = area in (
            Qt.DockWidgetArea.TopDockWidgetArea,
            Qt.DockWidgetArea.BottomDockWidgetArea,
        )
        self._update_layout(horizontal)

    def _on_active_viewer_layer_changed(self, event: Event):
        old_roi_layer = self._roi_layer
        if isinstance(event.value, Shapes):
            self._roi_layer = event.value
        else:
            self._roi_layer = None
        self._on_roi_layer_changed(old_roi_layer)

    def _on_roi_layer_changed(self, old_roi_layer: Optional[Shapes]):
        if old_roi_layer is not None:
            old_roi_layer.events.data.disconnect(
                self._on_roi_layer_data_changed
            )
            old_roi_layer.events.properties.disconnect(
                self._on_roi_layer_properties_changed
            )
            old_roi_layer.events.current_properties.disconnect(
                self._on_roi_layer_current_properties_changed
            )
            old_roi_layer.mouse_drag_callbacks.remove(
                self._on_roi_layer_mouse_drag
            )
        if self._roi_layer is not None:
            self._roi_layer_accessor = ROILayerAccessor(self._roi_layer)
            self._roi_table_model = ROITableModel(self._roi_layer_accessor)
            self._roi_layer.events.data.connect(
                self._on_roi_layer_data_changed
            )
            self._roi_layer.events.properties.connect(
                self._on_roi_layer_properties_changed
            )
            self._roi_layer.events.current_properties.connect(
                self._on_roi_layer_current_properties_changed
            )
            self._roi_layer.mouse_drag_callbacks.append(
                self._on_roi_layer_mouse_drag
            )
            self._update_roi_layer_text()
            self.setEnabled(True)
        else:
            self._roi_layer_accessor = None
            self._roi_table_model = None
            self.setEnabled(False)
        update_column_widths = self._roi_table_view.model() is None
        self._roi_table_view.setModel(self._roi_table_model)
        if self._roi_table_model is not None and update_column_widths:
            for column in range(0, self._roi_table_model.columnCount()):
                self._roi_table_view.setColumnWidth(
                    column, self.DEFAULT_COLUMN_WIDTHS[column]
                )
            self._roi_table_view.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Interactive
            )
        selection_model = self._roi_table_view.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(
                self._on_roi_table_view_selection_changed
            )
        self.autosave = False
        self._refresh_add_widget()
        self._refresh_roi_table_widget()
        self._refresh_save_widget()

    def _on_new_roi_name_edit_text_changed(self, text: str):
        self.new_roi_name = text

    def _on_new_roi_width_spinbox_value_changed(self, value: float):
        self.new_roi_width = value

    def _on_new_roi_height_spinbox_value_changed(self, value: float):
        self.new_roi_height = value

    def _on_add_roi_button_clicked(self):
        assert self.new_roi_width is not None
        assert self.new_roi_height is not None
        assert self._roi_layer_accessor is not None
        cy, cx = self._viewer.camera.center[-2:]
        roi = ROI(
            name=self._create_roi_name(),
            x=cx - self.new_roi_width / 2.0,
            y=cy - self.new_roi_height / 2.0,
            width=self.new_roi_width,
            height=self.new_roi_height,
        )
        self._roi_layer_accessor.append(roi)
        self._refresh_roi_table_widget()
        self._update_roi_layer_text()

    def _on_roi_table_view_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ):
        row_indices = set(index.row() for index in selected.indexes())
        self._roi_layer.selected_data = row_indices
        self._roi_layer.refresh()

    def _on_roi_table_view_context_menu_requested(self, pos: QPoint):
        index = self._roi_table_view.indexAt(pos)
        if index.isValid():
            menu = QMenu()
            del_action = menu.addAction(
                self.style().standardIcon(
                    QStyle.StandardPixmap.SP_DialogCloseButton
                ),
                "Delete",
            )
            if menu.exec(self._roi_table_view.mapToGlobal(pos)) == del_action:
                del self._roi_layer_accessor[index.row()]
                self._refresh_roi_table_widget(row_indices=[index.row()])

    def _on_roi_origin_combobox_current_text_changed(self, text: str):
        self.roi_origin = ROIOrigin(text)
        self._refresh_roi_table_widget()
        if self.autosave:
            self.save()

    def _on_save_file_edit_browse_action_triggered(self, checked: bool):
        file_dialog = QFileDialog(
            parent=self,
            caption="Save ROI coordinates as",
            filter="Comma-separated values files (*.csv)",
        )
        if self.roi_file is not None:
            if self.roi_file.parent.is_dir():
                file_dialog.setDirectory(str(self.roi_file.parent))
            if self.roi_file.is_file():
                file_dialog.selectFile(str(self.roi_file))
        else:
            file_dialog.setDirectory(str(Path.home()))
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            path = Path(file_dialog.selectedFiles()[0])
            if path.suffix.lower() != ".csv":
                path = path.with_name(path.name + ".csv")
            self.roi_file = path
            self._refresh_save_widget()
            if self.roi_file.is_file():
                answer = QMessageBox.question(
                    self,
                    "Load existing ROIs",
                    "Do you want to load existing ROIs "
                    "and add them to the current layer?",
                    buttons=QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Yes,
                    defaultButton=QMessageBox.StandardButton.No,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self.load()

    def _on_autosave_checkbox_state_changed(self, state: Qt.CheckState):
        if state == Qt.CheckState.Checked:
            self.save()
        self._refresh_save_widget()

    def _on_save_button_clicked(self, checked: bool):
        self.save()

    def _on_roi_layer_data_changed(self, event: Event):
        if self.autosave:
            self.save()
        self._refresh_roi_table_widget()

    def _on_roi_layer_properties_changed(self, event: Event):
        if self.autosave:
            self.save()
        self._refresh_roi_table_widget()

    def _on_roi_layer_current_properties_changed(self, event: Event):
        self._update_roi_layer_text()

    def _on_roi_layer_mouse_drag(self, roi_layer: Shapes, event: MouseEvent):
        if roi_layer.mode.startswith("add_"):
            self.current_roi_name = self._create_roi_name()
        if roi_layer.mode.startswith("add_") or roi_layer.mode in (
            "select",  # move shape
            "direct",  # move vertex
            "vertex_insert",
            "vertex_remove",
        ):
            yield
            self._refresh_roi_table_widget()
            while event.type == "mouse_move":
                self._refresh_roi_table_widget(
                    row_indices=roi_layer.selected_data
                )
                yield

    def _update_layout(self, horizontal: bool):
        if horizontal:
            self.layout().addWidget(
                self._add_widget,
                0,
                0,
                alignment=Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignTop,
            )
            self.layout().addWidget(
                self._save_widget,
                1,
                0,
                alignment=Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignBottom,
            )
            self.layout().addWidget(self._roi_table_widget, 0, 1, 2, 1)
        else:
            self.layout().addWidget(
                self._add_widget, 0, 0, alignment=Qt.AlignmentFlag.AlignTop
            )
            self.layout().addWidget(self._roi_table_widget, 1, 0)
            self.layout().addWidget(
                self._save_widget, 2, 0, alignment=Qt.AlignmentFlag.AlignBottom
            )

    def _update_roi_layer_text(self):
        if self._roi_layer is not None:
            self._roi_layer.text = ROILayerAccessor.ROI_NAME_PROPERTIES_KEY
            self._roi_layer.text.color = self.ROI_LAYER_TEXT_COLOR

    def _refresh_add_widget(self):
        if self._roi_layer_accessor is not None:
            self._new_roi_name_edit.setText(self.new_roi_name)
            self._new_roi_width_spinbox.setValue(self.new_roi_width)
            self._new_roi_height_spinbox.setValue(self.new_roi_height)

    def _refresh_roi_table_widget(
        self, row_indices: Optional[Sequence[int]] = None
    ):
        if self._roi_table_model is not None:
            if row_indices is not None:
                self._roi_table_model.refresh_rows(row_indices)
            else:
                self._roi_table_model.reset()
        if self._roi_layer_accessor is not None:
            self._roi_origin_combobox.setCurrentText(str(self.roi_origin))

    def _refresh_save_widget(self):
        self._roi_file_edit.setEnabled(not self.autosave)
        self._roi_file_edit.setText(str(self.roi_file or ""))
        self._autosave_checkbox.setEnabled(self.roi_file is not None)
        self._save_button.setEnabled(
            self.roi_file is not None and not self.autosave
        )

    def _create_roi_name(self) -> str:
        assert self._roi_layer_accessor is not None
        desired_roi_name = self.new_roi_name
        existing_roi_names = [roi.name for roi in self._roi_layer_accessor]
        if desired_roi_name not in existing_roi_names:
            return desired_roi_name
        i = 2
        roi_name_fmt = f"{desired_roi_name} ({{:d}})"
        while roi_name_fmt.format(i) in existing_roi_names:
            i += 1
        return roi_name_fmt.format(i)

    def load(self):
        assert self._roi_layer_accessor is not None
        assert self.roi_file is not None
        df = None
        try:
            df = pd.read_csv(self.roi_file)
        except Exception as e:
            QMessageBox.warning(self._viewer.window.qt_viewer, "Error", e)
        if df is not None:
            for i, row in df.iterrows():
                roi = ROI(
                    name=row["Name"],
                    x=row["X"],
                    y=row["Y"],
                    width=row["W"],
                    height=row["H"],
                )
                self._roi_layer_accessor.append(roi)
            self._refresh_roi_table_widget()

    def save(self):
        assert self._roi_layer_accessor is not None
        assert self.roi_file is not None
        df = pd.DataFrame(
            data={
                "Name": [roi.name for roi in self._roi_layer_accessor],
                "X": [roi.x for roi in self._roi_layer_accessor],
                "Y": [roi.y for roi in self._roi_layer_accessor],
                "W": [roi.width for roi in self._roi_layer_accessor],
                "H": [roi.height for roi in self._roi_layer_accessor],
            }
        )
        try:
            df.to_csv(self.roi_file, index=False)
        except Exception as e:
            QMessageBox.warning(self._viewer.window.qt_viewer, "Error", e)

    def get_rois(self) -> MutableSequence[ROIBase]:
        assert self._roi_layer_accessor is not None
        assert self._roi_table_model is not None
        return MutableSequenceWrapper(
            self._roi_layer_accessor, self._roi_table_model
        )

    @property
    def viewer(self) -> Viewer:
        return self._viewer

    @property
    def new_roi_name(self) -> Optional[str]:
        if self._roi_layer_accessor is not None:
            return self._roi_layer_accessor.new_roi_name
        return None

    @new_roi_name.setter
    def new_roi_name(self, value: str):
        assert self._roi_layer_accessor is not None
        self._roi_layer_accessor.new_roi_name = value
        self._new_roi_name_edit.setText(value)

    @property
    def new_roi_width(self) -> Optional[float]:
        if self._roi_layer_accessor is not None:
            return self._roi_layer_accessor.new_roi_width
        return None

    @new_roi_width.setter
    def new_roi_width(self, value: float):
        assert self._roi_layer_accessor is not None
        self._roi_layer_accessor.new_roi_width = value
        self._new_roi_width_spinbox.setValue(value)

    @property
    def new_roi_height(self) -> Optional[float]:
        if self._roi_layer_accessor is not None:
            return self._roi_layer_accessor.new_roi_height
        return None

    @new_roi_height.setter
    def new_roi_height(self, value: float):
        assert self._roi_layer_accessor is not None
        self._roi_layer_accessor.new_roi_height = value
        self._new_roi_height_spinbox.setValue(value)

    @property
    def roi_origin(self) -> Optional[ROIOrigin]:
        if self._roi_layer_accessor is not None:
            return self._roi_layer_accessor.roi_origin
        return None

    @roi_origin.setter
    def roi_origin(self, value: ROIOrigin):
        assert self._roi_layer_accessor is not None
        self._roi_layer_accessor.roi_origin = value
        self._roi_origin_combobox.setCurrentText(str(value))

    @property
    def roi_file(self) -> Optional[Path]:
        if self._roi_layer_accessor is not None:
            return self._roi_layer_accessor.roi_file
        return None

    @roi_file.setter
    def roi_file(self, value: Optional[Path]):
        assert self._roi_layer_accessor is not None
        self._roi_layer_accessor.roi_file = value
        self._roi_file_edit.setText(str(value) if value is not None else None)
        self._refresh_save_widget()

    @property
    def current_roi_name(self) -> Optional[str]:
        if self._roi_layer_accessor is not None:
            return self._roi_layer_accessor.current_roi_name
        return None

    @current_roi_name.setter
    def current_roi_name(self, value: str):
        assert self._roi_layer_accessor is not None
        self._roi_layer_accessor.current_roi_name = value

    @property
    def autosave(self) -> bool:
        return self._autosave_checkbox.isChecked()

    @autosave.setter
    def autosave(self, value: bool) -> bool:
        self._autosave_checkbox.setChecked(value)
        self._refresh_save_widget()
