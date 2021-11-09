try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from napari_plugin_engine import napari_hook_implementation

from napari_roi._roi import ROIBase
from napari_roi._roi_widget import ROIWidget


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return ROIWidget, {
        "name": "regions of interest",
        "area": "right",
        "allowed_areas": ["left", "right"],
    }


__all__ = ["ROIBase", "ROIWidget", "napari_experimental_provide_dock_widget"]
