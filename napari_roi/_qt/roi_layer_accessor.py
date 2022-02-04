import numpy as np

from collections.abc import MutableSequence
from napari.layers import Shapes
from pathlib import Path
from typing import Optional

from napari_roi._roi import ROIBase, ROIOrigin


class ROILayerAccessor(MutableSequence[ROIBase]):
    NEW_ROI_NAME_METADATA_KEY = "new_roi_name"
    NEW_ROI_WIDTH_METADATA_KEY = "new_roi_width"
    NEW_ROI_HEIGHT_METADATA_KEY = "new_roi_height"
    ROI_ORIGIN_METADATA_KEY = "roi_origin"
    ROI_FILE_METADATA_KEY = "roi_file"

    DEFAULT_NEW_ROI_NAME = "New ROI"
    DEFAULT_NEW_ROI_WIDTH = 100.0
    DEFAULT_NEW_ROI_HEIGHT = 100.0
    DEFAULT_ROI_ORIGIN = ROIOrigin.TOP_LEFT
    DEFAULT_ROI_FILE = ""

    ROI_NAME_PROPERTIES_KEY = "roi_name"

    class Item(ROIBase):
        def __init__(self, parent: "ROILayerAccessor", index: int):
            self._parent = parent
            self._index = index

        def insert(self, roi: ROIBase):
            layer_data = self._parent._layer.data.copy()
            layer_data.insert(self._index, self._create_rectangle_data(roi))
            layer_properties = self._parent._layer.properties.copy()
            for layer_properties_key in layer_properties:
                values = list(layer_properties[layer_properties_key])
                if layer_properties_key == ROILayerAccessor.ROI_NAME_PROPERTIES_KEY:
                    values.insert(self._index, roi.name)
                else:
                    values.insert(self._index, np.nan)
                layer_properties[layer_properties_key] = np.array(values)
            self._parent._layer.properties.clear()
            self._parent._layer.data = layer_data
            self._parent._layer.properties = layer_properties

        def delete(self):
            layer_data = self._parent._layer.data.copy()
            del layer_data[self._index]
            layer_properties = self._parent._layer.properties.copy()
            for layer_properties_key in layer_properties:
                values = list(layer_properties[layer_properties_key])
                del values[self._index]
                layer_properties[layer_properties_key] = np.array(values)
            self._parent._layer.properties.clear()
            self._parent._layer.data = layer_data
            self._parent._layer.properties = layer_properties

        def update(self, roi: ROIBase):
            self.name = roi.name
            self.x = roi.x
            self.y = roi.y
            self.width = roi.width
            self.height = roi.height

        def _create_rectangle_data(self, roi: ROIBase) -> np.ndarray:
            if self._parent.roi_origin == ROIOrigin.TOP_LEFT:
                return np.array(
                    [
                        [roi.y, roi.x],
                        [roi.y, roi.x + roi.width],
                        [roi.y + roi.height, roi.x + roi.width],
                        [roi.y + roi.height, roi.x],
                    ]
                )
            if self._parent.roi_origin == ROIOrigin.TOP_RIGHT:
                return np.array(
                    [
                        [roi.y, roi.x - roi.width],
                        [roi.y, roi.x],
                        [roi.y + roi.height, roi.x],
                        [roi.y + roi.height, roi.x - roi.width],
                    ]
                )
            if self._parent.roi_origin == ROIOrigin.BOTTOM_LEFT:
                return np.array(
                    [
                        [roi.y - roi.height, roi.x],
                        [roi.y - roi.height, roi.x + roi.width],
                        [roi.y, roi.x + roi.width],
                        [roi.y, roi.x],
                    ]
                )
            if self._parent.roi_origin == ROIOrigin.BOTTOM_RIGHT:
                return np.array(
                    [
                        [roi.y - roi.height, roi.x - roi.width],
                        [roi.y - roi.height, roi.x],
                        [roi.y, roi.x],
                        [roi.y, roi.x - roi.width],
                    ]
                )
            raise NotImplementedError()

        @property
        def name(self) -> str:
            return str(
                self._parent._layer.properties[
                    ROILayerAccessor.ROI_NAME_PROPERTIES_KEY
                ][self._index]
            )

        @name.setter
        def name(self, name: str):
            # convert the fixed-length string numpy array to list to allow for
            # longer strings than can be stored in the current numpy array
            roi_names = list(
                self._parent._layer.properties[ROILayerAccessor.ROI_NAME_PROPERTIES_KEY]
            )
            roi_names[self._index] = name
            self._parent._layer.properties[
                ROILayerAccessor.ROI_NAME_PROPERTIES_KEY
            ] = np.array(roi_names)
            self._parent._layer.refresh_text()

        @property
        def data(self) -> np.ndarray:
            return self._parent._layer.data[self._index]

        @data.setter
        def data(self, data: np.ndarray):
            layer_data = self._parent._layer.data.copy()
            layer_data[self._index] = data
            self._parent._layer.data = layer_data

        @property
        def x(self) -> float:
            if self._parent.roi_origin in (
                ROIOrigin.TOP_LEFT,
                ROIOrigin.BOTTOM_LEFT,
            ):
                return float(np.amin(self.data[:, -1]))
            if self._parent.roi_origin in (
                ROIOrigin.TOP_RIGHT,
                ROIOrigin.BOTTOM_RIGHT,
            ):
                return float(np.amax(self.data[:, -1]))
            raise NotImplementedError()

        @x.setter
        def x(self, x: float):
            self.data += np.array([[0.0, x - self.x]])

        @property
        def y(self) -> float:
            if self._parent.roi_origin in (
                ROIOrigin.TOP_LEFT,
                ROIOrigin.TOP_RIGHT,
            ):
                return float(np.amin(self.data[:, -2]))
            if self._parent.roi_origin in (
                ROIOrigin.BOTTOM_LEFT,
                ROIOrigin.BOTTOM_RIGHT,
            ):
                return float(np.amax(self.data[:, -2]))

        @y.setter
        def y(self, y: float):
            self.data += np.array([[y - self.y, 0.0]])

        @property
        def width(self) -> float:
            return float(np.amax(self.data[:, -1]) - np.amin(self.data[:, -1]))

        @width.setter
        def width(self, width: float):
            origin = np.array([[self.y, self.x]])
            scale = np.array([[1.0, width / self.width]])
            self.data = (self.data - origin) * scale + origin

        @property
        def height(self) -> float:
            return float(np.amax(self.data[:, -2]) - np.amin(self.data[:, -2]))

        @height.setter
        def height(self, height: float):
            origin = np.array([[self.y, self.x]])
            scale = np.array([[height / self.height, 1.0]])
            self.data = (self.data - origin) * scale + origin

        @property
        def layer_accessor(self) -> "ROILayerAccessor":
            return self._parent

        @property
        def index(self) -> int:
            return self._index

    def __init__(self, layer: Shapes):
        self._layer = layer
        if self.NEW_ROI_NAME_METADATA_KEY not in layer.metadata:
            layer.metadata[self.NEW_ROI_NAME_METADATA_KEY] = self.DEFAULT_NEW_ROI_NAME
        if self.NEW_ROI_WIDTH_METADATA_KEY not in layer.metadata:
            layer.metadata[self.NEW_ROI_WIDTH_METADATA_KEY] = self.DEFAULT_NEW_ROI_WIDTH
        if self.NEW_ROI_HEIGHT_METADATA_KEY not in layer.metadata:
            layer.metadata[
                self.NEW_ROI_HEIGHT_METADATA_KEY
            ] = self.DEFAULT_NEW_ROI_HEIGHT
        if self.ROI_FILE_METADATA_KEY not in layer.metadata:
            layer.metadata[self.ROI_FILE_METADATA_KEY] = self.DEFAULT_ROI_FILE
        if self.ROI_ORIGIN_METADATA_KEY not in layer.metadata:
            layer.metadata[self.ROI_ORIGIN_METADATA_KEY] = self.DEFAULT_ROI_ORIGIN
        if self.ROI_NAME_PROPERTIES_KEY not in layer.properties:
            layer.properties[self.ROI_NAME_PROPERTIES_KEY] = np.array(
                [""] * len(layer.data)
            )

    def insert(self, index: int, roi: ROIBase):
        ROILayerAccessor.Item(self, index).insert(roi)

    def __getitem__(self, index: int) -> ROIBase:
        if index < 0:
            index = len(self._layer.data) + index
        if index < 0 or index >= len(self._layer.data):
            raise IndexError()
        return ROILayerAccessor.Item(self, index)

    def __setitem__(self, index: int, roi: ROIBase):
        if index < 0:
            index = len(self._layer.data) + index
        if index < 0 or index >= len(self._layer.data):
            raise IndexError()
        ROILayerAccessor.Item(self, index).update(roi)

    def __delitem__(self, index: int):
        if index < 0:
            index = len(self._layer.data) + index
        if index < 0 or index >= len(self._layer.data):
            raise IndexError()
        ROILayerAccessor.Item(self, index).delete()

    def __len__(self):
        return len(self._layer.data)

    @property
    def layer(self) -> Shapes:
        return self._layer

    @property
    def new_roi_name(self) -> str:
        return self._layer.metadata[self.NEW_ROI_NAME_METADATA_KEY]

    @new_roi_name.setter
    def new_roi_name(self, value: str):
        self._layer.metadata[self.NEW_ROI_NAME_METADATA_KEY] = value

    @property
    def new_roi_width(self) -> int:
        return self._layer.metadata[self.NEW_ROI_WIDTH_METADATA_KEY]

    @new_roi_width.setter
    def new_roi_width(self, value: int):
        self._layer.metadata[self.NEW_ROI_WIDTH_METADATA_KEY] = value

    @property
    def new_roi_height(self) -> int:
        return self._layer.metadata[self.NEW_ROI_HEIGHT_METADATA_KEY]

    @new_roi_height.setter
    def new_roi_height(self, value: int):
        self._layer.metadata[self.NEW_ROI_HEIGHT_METADATA_KEY] = value

    @property
    def roi_origin(self) -> ROIOrigin:
        return ROIOrigin(self._layer.metadata[self.ROI_ORIGIN_METADATA_KEY])

    @roi_origin.setter
    def roi_origin(self, value: ROIOrigin):
        self._layer.metadata[self.ROI_ORIGIN_METADATA_KEY] = str(value)

    @property
    def roi_file(self) -> Optional[Path]:
        roi_file_str = self._layer.metadata[self.ROI_FILE_METADATA_KEY]
        if roi_file_str:
            return Path(roi_file_str)
        return None

    @roi_file.setter
    def roi_file(self, value: Optional[Path]):
        self._layer.metadata[self.ROI_FILE_METADATA_KEY] = str(value or "")

    @property
    def current_roi_name(self) -> Optional[str]:
        if (
            self._layer.current_properties is not None
            and self.ROI_NAME_PROPERTIES_KEY in self._layer.current_properties
            and len(self._layer.current_properties[self.ROI_NAME_PROPERTIES_KEY]) == 1
        ):
            return self._layer.current_properties[self.ROI_NAME_PROPERTIES_KEY][0]
        return None

    @current_roi_name.setter
    def current_roi_name(self, value: Optional[str]):
        value = np.array([value]) if value is not None else np.array([])
        self._layer.current_properties[self.ROI_NAME_PROPERTIES_KEY] = value
