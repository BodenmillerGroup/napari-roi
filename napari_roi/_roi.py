from abc import ABC, abstractmethod
from dataclasses import dataclass

from napari.utils.misc import StringEnum


class ROIBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @name.setter
    @abstractmethod
    def name(self, name: str) -> None:
        pass

    @property
    @abstractmethod
    def x(self) -> float:
        raise NotImplementedError()

    @x.setter
    @abstractmethod
    def x(self, x: float) -> None:
        pass

    @property
    @abstractmethod
    def y(self) -> float:
        raise NotImplementedError()

    @y.setter
    @abstractmethod
    def y(self, y: float) -> None:
        pass

    @property
    @abstractmethod
    def width(self) -> float:
        raise NotImplementedError()

    @width.setter
    @abstractmethod
    def width(self, width: float) -> None:
        pass

    @property
    @abstractmethod
    def height(self) -> float:
        raise NotImplementedError()

    @height.setter
    @abstractmethod
    def height(self, height: float) -> None:
        pass


@dataclass
class ROI(ROIBase):
    name: str = "New ROI"
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0


class ROIOrigin(StringEnum):
    CENTER = "center"
    TOP_LEFT = "top left"
    TOP_RIGHT = "top right"
    BOTTOM_LEFT = "bottom left"
    BOTTOM_RIGHT = "bottom right"
