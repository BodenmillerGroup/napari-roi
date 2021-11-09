from napari.viewer import Viewer
from qtpy.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QStyle,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from typing import MutableSequence

from napari_roi._roi import ROI, ROIBase
from napari_roi._qt import (
    FileLineEdit,
    MutableSequenceWrapper,
    ROILayerAccessor,
    ROITableModel,
)


class ROIWidget(QWidget):
    DEFAULT_ROI_WIDTH = 100.0
    DEFAULT_ROI_HEIGHT = 100.0
    DEFAULT_ROI_NAME_FMT = "ROI {:d}"
    DEFAULT_ROI_LAYER_NAME = "ROIs"

    # TODO disconnect event handlers
    # TODO delete widget upon deletion of layer

    def __init__(self, viewer: Viewer):
        super(ROIWidget, self).__init__(parent=viewer.window.qt_viewer)
        self.viewer = viewer
        self.next_roi_number = 1

        self.roi_layer = viewer.add_shapes(name=self.DEFAULT_ROI_LAYER_NAME)
        self.roi_layer.events.data.connect(self._on_roi_layer_data_changed)
        self.roi_layer.events.properties.connect(
            self._on_roi_layer_properties_changed
        )
        self.roi_layer.events.current_properties.connect(
            self._on_roi_layer_current_properties_changed
        )
        self.roi_layer.mouse_drag_callbacks.append(
            self._on_roi_layer_mouse_drag
        )
        self.roi_layer_accessor = ROILayerAccessor(self.roi_layer)
        self.roi_layer_accessor.initialize_layer_properties()

        self.setLayout(QVBoxLayout())

        add_widget = QWidget(parent=self)
        add_widget_layout = QFormLayout()
        add_widget.setLayout(add_widget_layout)
        self.width_spin_box = QDoubleSpinBox(parent=add_widget)
        self.width_spin_box.setRange(0.0, float("inf"))
        self.width_spin_box.setValue(self.DEFAULT_ROI_WIDTH)
        add_widget_layout.addRow(
            QLabel("Width:", parent=add_widget), self.width_spin_box
        )
        self.height_spin_box = QDoubleSpinBox(parent=add_widget)
        self.height_spin_box.setRange(0.0, float("inf"))
        self.height_spin_box.setValue(self.DEFAULT_ROI_HEIGHT)
        add_widget_layout.addRow(
            QLabel("Height:", parent=add_widget), self.height_spin_box
        )
        self.add_roi_push_button = QPushButton("Add ROI", parent=add_widget)
        self.add_roi_push_button.clicked.connect(
            self._on_add_roi_push_button_clicked
        )
        add_widget_layout.addRow(self.add_roi_push_button)
        self.layout().addWidget(add_widget)

        self.roi_table_model = ROITableModel(self.roi_layer_accessor)
        self.roi_table_view = QTableView(parent=self)
        self.roi_table_view.setModel(self.roi_table_model)
        self.layout().addWidget(self.roi_table_view)

        save_widget = QWidget(parent=self)
        save_widget_layout = QGridLayout()
        save_widget.setLayout(save_widget_layout)
        self.roi_file_line_edit = FileLineEdit(
            caption="Save ROI coordinates as",
            filter=".csv",
            parent=save_widget,
        )
        self.roi_file_line_edit.setReadOnly(True)
        self.roi_file_line_edit.textChanged.connect(
            self._on_roi_file_line_edit_text_changed
        )
        save_widget_layout.addWidget(self.roi_file_line_edit, 0, 0, 1, 2)
        self.autosave_check_box = QCheckBox("Autosave", parent=save_widget)
        self.autosave_check_box.stateChanged.connect(
            self._on_autosave_check_box_state_changed
        )
        save_widget_layout.addWidget(self.autosave_check_box, 1, 0, 1, 1)
        self.save_push_button = QPushButton(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogSaveButton
            ),
            "Save",
            parent=save_widget,
        )
        self.save_push_button.clicked.connect(
            self._on_save_push_button_clicked
        )
        save_widget_layout.addWidget(self.save_push_button, 1, 1, 1, 1)
        self.layout().addWidget(save_widget)

        self._update_autosave_check_box_enabled()
        self._update_save_push_button_enabled()
        self._update_roi_layer_text()

    def _on_roi_layer_data_changed(self, event):
        self.roi_table_model.reset()

    def _on_roi_layer_properties_changed(self, event):
        self.roi_table_model.reset()

    def _on_roi_layer_current_properties_changed(self, event):
        self._update_roi_layer_text()

    def _on_roi_layer_mouse_drag(self, layer, event):
        # TODO other shapes
        if layer.mode.startswith("add_"):
            self.roi_layer_accessor.update_layer_current_properties(
                self._get_next_roi_name()
            )
        yield
        while event.type == "mouse_move":
            self.roi_table_model.reset()
            yield

    def _on_add_roi_push_button_clicked(self):
        cy, cx = self.viewer.camera.center[-2:]
        width = self.width_spin_box.value()
        height = self.height_spin_box.value()
        roi = ROI(
            name=self._get_next_roi_name(),
            x=cx - width / 2.0,
            y=cy - height / 2.0,
            width=width,
            height=height,
        )
        self.rois.append(roi)

    def _on_roi_file_line_edit_text_changed(self, text):
        # TODO load file if exists
        self._update_autosave_check_box_enabled()
        self._update_save_push_button_enabled()

    def _on_autosave_check_box_state_changed(self, state):
        # TODO autosave
        self._update_roi_file_line_edit_enabled()
        self._update_save_push_button_enabled()

    def _on_save_push_button_clicked(self, checked):
        pass  # TODO save

    def _update_roi_file_line_edit_enabled(self):
        self.roi_file_line_edit.setEnabled(
            not self.autosave_check_box.isChecked()
        )

    def _update_autosave_check_box_enabled(self):
        pass  # TODO only enable if path is valid

    def _update_save_push_button_enabled(self):
        # TODO only enable if path is valid
        self.save_push_button.setEnabled(
            not self.autosave_check_box.isChecked()
        )

    def _update_roi_layer_text(self):
        # TODO text properties
        self.roi_layer.text = ROILayerAccessor.ROI_NAME_PROPERTY

    def _get_next_roi_name(self) -> str:
        next_roi_name = self.DEFAULT_ROI_NAME_FMT.format(self.next_roi_number)
        self.next_roi_number += 1
        return next_roi_name

    @property
    def rois(self) -> MutableSequence[ROIBase]:
        return MutableSequenceWrapper(
            self.roi_layer_accessor, self.roi_table_model
        )
