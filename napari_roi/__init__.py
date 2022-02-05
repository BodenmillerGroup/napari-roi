try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from napari_plugin_engine import napari_hook_implementation

from ._roi import ROI, ROIBase, ROIOrigin
from ._roi_widget import ROIWidget


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return ROIWidget, {"name": "regions of interest"}


__all__ = [
    "ROI",
    "ROIBase",
    "ROIOrigin",
    "ROIWidget",
    "napari_experimental_provide_dock_widget",
]
