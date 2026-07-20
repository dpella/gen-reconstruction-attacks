from abc import ABC, abstractmethod
from typing import List


class ILOp(ABC):
    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the operation.
        """
        pass

    @abstractmethod
    def to_string(self) -> str:
        """
        Return a string representation of the operation.
        """
        pass


class OpComposite(ILOp):
    def __init__(self):
        self._operands: List[ILOp] = []

    def add(self, op: ILOp) -> None:
        self._operands.append(op)

    def remove(self, op: ILOp) -> None:
        self._operands.remove(op)

    @property
    def operands(self) -> List[ILOp]:
        return self._operands

    def execute(self) -> bool:
        for op in self._operands:
            if not op.execute():
                return False
        return True

    def to_string(self) -> str:
        return " ".join(op.to_string() for op in self._operands)
