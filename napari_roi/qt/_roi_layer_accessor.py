from collections.abc import MutableSequence
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from napari.layers import Shapes
from napari.layers.utils.layer_utils import features_to_pandas_dataframe

from .. import ROIBase, ROIOrigin


class ROILayerAccessor(MutableSequence[ROIBase]):
    ROI_NAME_FEATURES_KEY = "roi_name"

    NEW_ROI_NAME_METADATA_KEY = "new_roi_name"
    NEW_ROI_WIDTH_METADATA_KEY = "new_roi_width"
    NEW_ROI_HEIGHT_METADATA_KEY = "new_roi_height"
    ROI_ORIGIN_METADATA_KEY = "roi_origin"
    ROI_FILE_METADATA_KEY = "roi_file"
    AUTOSAVE_ROI_FILE_METADATA_KEY = "autosave_roi_file"

    DEFAULT_NEW_ROI_NAME = "New ROI"
    DEFAULT_NEW_ROI_WIDTH = 100.0
    DEFAULT_NEW_ROI_HEIGHT = 100.0
    DEFAULT_ROI_ORIGIN = ROIOrigin.CENTER
    DEFAULT_ROI_FILE = ""
    DEFAULT_AUTOSAVE_ROI_FILE = False

    class ItemAccessor(ROIBase):
        def __init__(self, parent: "ROILayerAccessor", index: int) -> None:
            self._parent = parent
            self._index = index

        def insert(self, roi: ROIBase) -> None:
            layer_data = self._parent._layer.data.copy()
            layer_data.insert(self._index, self._create_rectangle_data(roi))
            self._parent._layer.data = layer_data  # appends a row to features
            layer_features = features_to_pandas_dataframe(self._parent._layer.features)
            layer_features: pd.DataFrame = pd.concat(
                (
                    layer_features.iloc[: self._index],
                    layer_features.iloc[[-1]],
                    layer_features.iloc[self._index : -1],
                ),
                ignore_index=True,
            )  # move appended row to desired index
            layer_features[ROILayerAccessor.ROI_NAME_FEATURES_KEY].iloc[
                self._index
            ] = roi.name
            self._parent._layer.features = layer_features

        def delete(self) -> None:
            layer_features = features_to_pandas_dataframe(self._parent._layer.features)
            layer_features: pd.DataFrame = pd.concat(
                (
                    layer_features.iloc[: self._index],
                    layer_features.iloc[self._index + 1 :],
                    layer_features.iloc[[self._index]],
                ),
                ignore_index=True,
            )  # move deleted row to the end
            self._parent._layer.features = layer_features
            layer_data = self._parent._layer.data.copy()
            del layer_data[self._index]
            self._parent._layer.data = layer_data  # removes last row from features

        def update(self, roi: ROIBase) -> None:
            self.name = roi.name
            self.x = roi.x
            self.y = roi.y
            self.width = roi.width
            self.height = roi.height

        @property
        def parent(self) -> "ROILayerAccessor":
            return self._parent

        @property
        def index(self) -> int:
            return self._index

        @property
        def data(self) -> np.ndarray:
            return self._parent._layer.data[self._index]

        @data.setter
        def data(self, data: np.ndarray) -> None:
            layer_data = self._parent._layer.data.copy()
            layer_data[self._index] = data
            self._parent._layer.data = layer_data

        @property
        def features(self) -> pd.Series:
            layer_features = features_to_pandas_dataframe(self._parent._layer.features)
            return layer_features.iloc[self._index]

        @features.setter
        def features(self, features: pd.Series) -> None:
            layer_features = features_to_pandas_dataframe(self._parent._layer.features)
            layer_features = layer_features.copy()
            layer_features.iloc[self._index] = features
            self._parent._layer.features = layer_features

        @property
        def name(self) -> str:
            return str(self.features[ROILayerAccessor.ROI_NAME_FEATURES_KEY])

        @name.setter
        def name(self, name: str) -> None:
            features = self.features.copy()
            features[ROILayerAccessor.ROI_NAME_FEATURES_KEY] = name
            self.features = features

        @property
        def x(self) -> float:
            if self._parent.roi_origin == ROIOrigin.CENTER:
                return 0.5 * (
                    float(np.amin(self.data[:, -1])) + float(np.amax(self.data[:, -1]))
                )
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
        def x(self, x: float) -> None:
            self.data += np.array([[0.0, x - self.x]])

        @property
        def y(self) -> float:
            if self._parent.roi_origin == ROIOrigin.CENTER:
                return 0.5 * (
                    float(np.amin(self.data[:, -2])) + float(np.amax(self.data[:, -2]))
                )
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
            return NotImplementedError()

        @y.setter
        def y(self, y: float) -> None:
            self.data += np.array([[y - self.y, 0.0]])

        @property
        def width(self) -> float:
            return float(np.amax(self.data[:, -1]) - np.amin(self.data[:, -1]))

        @width.setter
        def width(self, width: float) -> None:
            origin = np.array([[self.y, self.x]])
            scale = np.array([[1.0, width / self.width]])
            self.data = (self.data - origin) * scale + origin

        @property
        def height(self) -> float:
            return float(np.amax(self.data[:, -2]) - np.amin(self.data[:, -2]))

        @height.setter
        def height(self, height: float) -> None:
            origin = np.array([[self.y, self.x]])
            scale = np.array([[height / self.height, 1.0]])
            self.data = (self.data - origin) * scale + origin

        def _create_rectangle_data(self, roi: ROIBase) -> np.ndarray:
            if self._parent.roi_origin == ROIOrigin.CENTER:
                return np.array(
                    [
                        [roi.y - roi.height / 2.0, roi.x - roi.width / 2.0],
                        [roi.y - roi.height / 2.0, roi.x + roi.width / 2.0],
                        [roi.y + roi.height / 2.0, roi.x + roi.width / 2.0],
                        [roi.y + roi.height / 2.0, roi.x - roi.width / 2.0],
                    ]
                )
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

    def __init__(self, layer: Shapes) -> None:
        self._layer = layer
        if self.ROI_NAME_FEATURES_KEY not in layer.features:
            layer.features[self.ROI_NAME_FEATURES_KEY] = ""
        if self.ROI_NAME_FEATURES_KEY not in layer.feature_defaults:
            layer.feature_defaults[self.ROI_NAME_FEATURES_KEY] = ""
        if self.NEW_ROI_NAME_METADATA_KEY not in layer.metadata:
            layer.metadata[self.NEW_ROI_NAME_METADATA_KEY] = self.DEFAULT_NEW_ROI_NAME
        if self.NEW_ROI_WIDTH_METADATA_KEY not in layer.metadata:
            layer.metadata[self.NEW_ROI_WIDTH_METADATA_KEY] = self.DEFAULT_NEW_ROI_WIDTH
        if self.NEW_ROI_HEIGHT_METADATA_KEY not in layer.metadata:
            layer.metadata[
                self.NEW_ROI_HEIGHT_METADATA_KEY
            ] = self.DEFAULT_NEW_ROI_HEIGHT
        if self.ROI_ORIGIN_METADATA_KEY not in layer.metadata:
            layer.metadata[self.ROI_ORIGIN_METADATA_KEY] = self.DEFAULT_ROI_ORIGIN
        if self.ROI_FILE_METADATA_KEY not in layer.metadata:
            layer.metadata[self.ROI_FILE_METADATA_KEY] = self.DEFAULT_ROI_FILE
        if self.AUTOSAVE_ROI_FILE_METADATA_KEY not in layer.metadata:
            layer.metadata[
                self.AUTOSAVE_ROI_FILE_METADATA_KEY
            ] = self.DEFAULT_AUTOSAVE_ROI_FILE

    def insert(self, index: int, roi: ROIBase) -> None:
        ROILayerAccessor.ItemAccessor(self, index).insert(roi)

    def __getitem__(self, index: int) -> ROIBase:
        if index < 0:
            index = len(self._layer.data) + index
        if index < 0 or index >= len(self._layer.data):
            raise IndexError()
        return ROILayerAccessor.ItemAccessor(self, index)

    def __setitem__(self, index: int, roi: ROIBase) -> None:
        if index < 0:
            index = len(self._layer.data) + index
        if index < 0 or index >= len(self._layer.data):
            raise IndexError()
        ROILayerAccessor.ItemAccessor(self, index).update(roi)

    def __delitem__(self, index: int) -> None:
        if index < 0:
            index = len(self._layer.data) + index
        if index < 0 or index >= len(self._layer.data):
            raise IndexError()
        ROILayerAccessor.ItemAccessor(self, index).delete()

    def __len__(self) -> int:
        return len(self._layer.data)

    @property
    def layer(self) -> Shapes:
        return self._layer

    @property
    def new_roi_name(self) -> str:
        return self._layer.metadata[self.NEW_ROI_NAME_METADATA_KEY]

    @new_roi_name.setter
    def new_roi_name(self, new_roi_name: str) -> None:
        self._layer.metadata[self.NEW_ROI_NAME_METADATA_KEY] = new_roi_name

    @property
    def new_roi_width(self) -> int:
        return self._layer.metadata[self.NEW_ROI_WIDTH_METADATA_KEY]

    @new_roi_width.setter
    def new_roi_width(self, new_roi_width: int) -> None:
        self._layer.metadata[self.NEW_ROI_WIDTH_METADATA_KEY] = new_roi_width

    @property
    def new_roi_height(self) -> int:
        return self._layer.metadata[self.NEW_ROI_HEIGHT_METADATA_KEY]

    @new_roi_height.setter
    def new_roi_height(self, new_roi_height: int) -> None:
        self._layer.metadata[self.NEW_ROI_HEIGHT_METADATA_KEY] = new_roi_height

    @property
    def roi_origin(self) -> ROIOrigin:
        return ROIOrigin(self._layer.metadata[self.ROI_ORIGIN_METADATA_KEY])

    @roi_origin.setter
    def roi_origin(self, roi_origin: ROIOrigin) -> None:
        self._layer.metadata[self.ROI_ORIGIN_METADATA_KEY] = str(roi_origin)

    @property
    def roi_file(self) -> Optional[Path]:
        roi_file_str = self._layer.metadata[self.ROI_FILE_METADATA_KEY]
        return Path(roi_file_str) if roi_file_str else None

    @roi_file.setter
    def roi_file(self, roi_file: Optional[Path]) -> None:
        self._layer.metadata[self.ROI_FILE_METADATA_KEY] = str(roi_file or "")

    @property
    def autosave_roi_file(self) -> bool:
        return self._layer.metadata[self.AUTOSAVE_ROI_FILE_METADATA_KEY]

    @autosave_roi_file.setter
    def autosave_roi_file(self, autosave_roi_file: bool) -> None:
        self._layer.metadata[self.AUTOSAVE_ROI_FILE_METADATA_KEY] = autosave_roi_file

    @property
    def current_roi_name(self) -> Optional[str]:
        if (
            self._layer.current_properties is not None
            and self.ROI_NAME_FEATURES_KEY in self._layer.current_properties
            and len(self._layer.current_properties[self.ROI_NAME_FEATURES_KEY]) == 1
        ):
            return self._layer.current_properties[self.ROI_NAME_FEATURES_KEY][0]
        return None

    @current_roi_name.setter
    def current_roi_name(self, current_roi_name: Optional[str]) -> None:
        layer_current_properties = self._layer.current_properties.copy()
        layer_current_properties[self.ROI_NAME_FEATURES_KEY] = np.array(
            [current_roi_name] if current_roi_name is not None else []
        )
        self._layer.current_properties = layer_current_properties
