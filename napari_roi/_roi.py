from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class ROIBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @name.setter
    @abstractmethod
    def name(self, name: str):
        pass

    @property
    @abstractmethod
    def x(self) -> float:
        raise NotImplementedError()

    @x.setter
    @abstractmethod
    def x(self, x: float):
        pass

    @property
    @abstractmethod
    def y(self) -> float:
        raise NotImplementedError()

    @y.setter
    @abstractmethod
    def y(self, y: float):
        pass

    @property
    @abstractmethod
    def width(self) -> float:
        raise NotImplementedError()

    @width.setter
    @abstractmethod
    def width(self, width: float):
        pass

    @property
    @abstractmethod
    def height(self) -> float:
        raise NotImplementedError()

    @height.setter
    @abstractmethod
    def height(self, height: float):
        pass

    def toROI(
        self,
        name: Optional[str] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> "ROI":
        return ROI(
            name=name or self.name,
            x=x or self.x,
            y=y or self.y,
            width=width or self.width,
            height=height or self.height,
        )


@dataclass
class ROI(ROIBase):
    name: str = "New ROI"
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0
