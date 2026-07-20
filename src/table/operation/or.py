from src.table.operation.base import ILOp


class OR(ILOp):
    def __init__(self, left: ILOp, right: ILOp):
        self.left = left
        self.right = right

    def execute(self) -> bool:
        return self.left.execute() or self.right.execute()

    def to_string(self) -> str:
        return f"({self.left.to_string()} OR {self.right.to_string()})"
