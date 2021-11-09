import numpy as np

from collections.abc import MutableSequence
from napari.layers import Shapes

from napari_roi._roi import ROIBase


class ROILayerAccessor(MutableSequence[ROIBase]):
    ROI_NAME_PROPERTY = "roi_name"

    class ROIAccessor(ROIBase):
        def __init__(self, layer: Shapes, index: int):
            self.layer = layer
            self.index = index

        def insert(self, roi: ROIBase):
            new_layer_data = self.layer.data.copy()
            new_layer_data.insert(self.index, self._create_data(roi))
            new_layer_properties = self.layer.properties.copy()
            new_roi_names = new_layer_properties[
                ROILayerAccessor.ROI_NAME_PROPERTY
            ].tolist()
            new_roi_names.insert(self.index, roi.name)
            new_layer_properties[
                ROILayerAccessor.ROI_NAME_PROPERTY
            ] = np.array(new_roi_names)
            self.layer.properties.clear()
            self.layer.data = new_layer_data
            self.layer.properties = new_layer_properties

        def delete(self):
            new_layer_data = self.layer.data.copy()
            del new_layer_data[self.index]
            new_layer_properties = self.layer.properties.copy()
            new_roi_names = new_layer_properties[
                ROILayerAccessor.ROI_NAME_PROPERTY
            ].tolist()
            del new_roi_names[self.index]
            new_layer_properties[
                ROILayerAccessor.ROI_NAME_PROPERTY
            ] = np.array(new_roi_names)
            self.layer.properties.clear()
            self.layer.data = new_layer_data
            self.layer.properties = new_layer_properties

        def update(self, roi: ROIBase):
            self.name = roi.name
            self.data = self._create_data(roi)

        @staticmethod
        def _create_data(roi: ROIBase) -> np.ndarray:
            return np.array(
                [
                    [roi.y, roi.x],
                    [roi.y, roi.x + roi.width],
                    [roi.y + roi.height, roi.x + roi.width],
                    [roi.y + roi.height, roi.x],
                ]
            )

        @property
        def name(self) -> str:
            return str(
                self.layer.properties[ROILayerAccessor.ROI_NAME_PROPERTY][
                    self.index
                ]
            )

        @name.setter
        def name(self, name: str):
            self.layer.properties[ROILayerAccessor.ROI_NAME_PROPERTY][
                self.index
            ] = name
            self.layer.refresh_text()

        @property
        def data(self) -> np.ndarray:
            return self.layer.data[self.index]

        @data.setter
        def data(self, data: np.ndarray):
            new_layer_data = self.layer.data.copy()
            new_layer_data[self.index] = data
            self.layer.data = new_layer_data

        @property
        def x(self) -> float:
            return float(np.amin(self.data[:, -1]))

        @x.setter
        def x(self, x: float):
            self.data = self._create_data(self.toROI(x=x))

        @property
        def y(self) -> float:
            return float(np.amin(self.data[:, -2]))

        @y.setter
        def y(self, y: float):
            self.data = self._create_data(self.toROI(y=y))

        @property
        def width(self) -> float:
            return float(np.amax(self.data[:, -1]) - np.amin(self.data[:, -1]))

        @width.setter
        def width(self, width: float):
            self.data = self._create_data(self.toROI(width=width))

        @property
        def height(self) -> float:
            return float(np.amax(self.data[:, -2]) - np.amin(self.data[:, -2]))

        @height.setter
        def height(self, height: float):
            self.data = self._create_data(self.toROI(height=height))

    def __init__(self, layer: Shapes):
        self.layer = layer

    def initialize_layer_properties(self):
        if self.ROI_NAME_PROPERTY not in self.layer.properties:
            self.layer.properties[self.ROI_NAME_PROPERTY] = np.array([])

    def update_layer_current_properties(self, roi_name: str):
        self.layer.current_properties[self.ROI_NAME_PROPERTY] = np.array(
            [roi_name]
        )

    def insert(self, index: int, roi: ROIBase):
        ROILayerAccessor.ROIAccessor(self.layer, index).insert(roi)

    def __getitem__(self, index: int) -> ROIBase:
        return ROILayerAccessor.ROIAccessor(self.layer, index)

    def __setitem__(self, index: int, roi: ROIBase):
        ROILayerAccessor.ROIAccessor(self.layer, index).update(roi)

    def __delitem__(self, index: int):
        ROILayerAccessor.ROIAccessor(self.layer, index).delete()

    def __len__(self):
        return len(self.layer.data)
